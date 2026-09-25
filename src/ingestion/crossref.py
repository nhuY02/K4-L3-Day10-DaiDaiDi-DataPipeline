from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
import re
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


CROSSREF_WORKS_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Convert a Crossref ``works`` response into the pipeline's raw schema."""

    def clean_text(value: Any) -> str:
        if value is None:
            return ""
        # Crossref abstracts commonly contain JATS elements. Replacing tags with
        # spaces also keeps adjacent paragraphs from being accidentally joined.
        without_tags = re.sub(r"<[^>]*>", " ", unescape(str(value)))
        return normalize_whitespace(without_tags)

    def first_text(value: Any) -> str:
        if isinstance(value, list):
            return clean_text(value[0]) if value else ""
        return clean_text(value)

    def text_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [text for item in value if (text := clean_text(item))]

    def crossref_date(value: Any) -> str:
        if not isinstance(value, dict):
            return ""
        date_parts = value.get("date-parts")
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list):
            try:
                parts = [int(part) for part in date_parts[0][:3]]
                if parts:
                    year = parts[0]
                    month = parts[1] if len(parts) > 1 else 1
                    day = parts[2] if len(parts) > 2 else 1
                    return datetime(year, month, day).date().isoformat()
            except (TypeError, ValueError, OverflowError):
                pass

        date_time = clean_text(value.get("date-time"))
        if date_time:
            try:
                return datetime.fromisoformat(date_time.replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                return ""
        return ""

    def timestamp(item: dict[str, Any]) -> str:
        # ``created`` is closest to the source record timestamp requested by the
        # lab. The remaining fields make the parser robust to Crossref variants.
        for key in ("created", "updated", "deposited", "indexed"):
            value = item.get(key)
            if isinstance(value, dict):
                candidate = clean_text(value.get("date-time"))
                if candidate:
                    return candidate
                raw_timestamp = value.get("timestamp")
                if isinstance(raw_timestamp, (int, float)):
                    try:
                        # Crossref timestamps are normally milliseconds since epoch.
                        seconds = raw_timestamp / 1000 if raw_timestamp > 10_000_000_000 else raw_timestamp
                        return datetime.fromtimestamp(seconds, tz=UTC).isoformat().replace("+00:00", "Z")
                    except (OSError, OverflowError, ValueError):
                        pass
        return ""

    def pdf_link(item: dict[str, Any]) -> str:
        links = item.get("link")
        if not isinstance(links, list):
            return ""
        for link in links:
            if not isinstance(link, dict):
                continue
            url = clean_text(link.get("URL") or link.get("url"))
            content_type = clean_text(link.get("content-type")).lower()
            if url and (content_type == "application/pdf" or url.lower().split("?", 1)[0].endswith(".pdf")):
                return url
        return ""

    message = payload.get("message", {}) if isinstance(payload, dict) else {}
    items = message.get("items", []) if isinstance(message, dict) else []
    if not isinstance(items, list):
        return []

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        paper_id = clean_text(item.get("DOI"))
        title = first_text(item.get("title"))
        if not paper_id or not title:
            continue

        authors: list[str] = []
        raw_authors = item.get("author", [])
        if isinstance(raw_authors, list):
            for author in raw_authors:
                if not isinstance(author, dict):
                    continue
                name = normalize_whitespace(
                    " ".join(
                        part
                        for part in (clean_text(author.get("given")), clean_text(author.get("family")))
                        if part
                    )
                )
                if name:
                    authors.append(name)

        categories = text_list(item.get("subject"))
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=clean_text(item.get("abstract")),
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=crossref_date(item.get("published")),
                updated=timestamp(item),
                abs_url=clean_text(item.get("URL")),
                pdf_url=pdf_link(item),
                comment="",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref records, using the preserved snapshot when appropriate."""

    snapshot_path = settings.paths.raw_api_response
    payload: dict[str, Any] | None = None
    records: list[PaperRecord] | None = None

    # The default lab mode is intentionally reproducible and network-independent.
    if not settings.refresh_source and snapshot_path.exists():
        local_payload = read_json(snapshot_path)
        if isinstance(local_payload, dict):
            payload = local_payload
    else:
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        params: dict[str, Any] = {
            "query": settings.source_query,
            "rows": settings.max_results,
        }
        if settings.source_filter:
            params["filter"] = settings.source_filter
        try:
            response = session.get(
                CROSSREF_WORKS_URL,
                params=params,
                headers={"User-Agent": "Day10-DataPipeline-Lab/1.0"},
                timeout=(5, 30),
            )
            response.raise_for_status()
            live_payload = response.json()
            if not isinstance(live_payload, dict):
                raise ValueError("Crossref returned a non-object JSON payload.")
            live_records = parse_crossref_payload(live_payload)
            if not live_records:
                raise ValueError("Crossref returned no usable records.")
            # Validate and parse completely before replacing a known-good snapshot.
            payload = live_payload
            records = live_records
            write_json(snapshot_path, payload)
        except (requests.RequestException, ValueError):
            if not snapshot_path.exists():
                raise RuntimeError("Crossref API failed and no local snapshot is available.") from None
            local_payload = read_json(snapshot_path)
            if not isinstance(local_payload, dict):
                raise RuntimeError("The local Crossref snapshot is not a JSON object.") from None
            payload = local_payload
        finally:
            session.close()

    if payload is None:
        raise RuntimeError("No Crossref payload is available.")

    if records is None:
        records = parse_crossref_payload(payload)
    if not records:
        raise RuntimeError("The available Crossref payload contains no usable records.")
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load the serialized output produced by :func:`fetch_source_records`."""

    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list of raw records in {path}.")

    field_names = {field.name for field in fields(PaperRecord)}
    records: list[PaperRecord] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        values = {name: item.get(name, [] if name in {"authors", "categories"} else "") for name in field_names}
        for name in ("authors", "categories"):
            value = values[name]
            if isinstance(value, list):
                values[name] = [str(entry) for entry in value if entry is not None]
            elif value is None or value == "":
                values[name] = []
            else:
                values[name] = [str(value)]
        records.append(PaperRecord(**values))
    return records
