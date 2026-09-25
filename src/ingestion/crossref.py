from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from core.config import Settings
from core.utils import normalize_whitespace, write_json


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
    """Parse Crossref API payload thanh list PaperRecord."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = item.get("DOI", "").strip()
        if not doi:
            continue

        # Title
        title_list = item.get("title", [])
        title = normalize_whitespace(title_list[0]) if title_list else ""
        if not title:
            continue

        # Abstract
        abstract = normalize_whitespace(item.get("abstract", "") or "")

        # Authors
        author_list = item.get("author", [])
        authors: list[str] = []
        for a in author_list:
            given = a.get("given", "")
            family = a.get("family", "")
            full = f"{given} {family}".strip()
            if full:
                authors.append(full)

        # Categories / subjects
        categories = [s for s in item.get("subject", []) if s]
        primary_category = categories[0] if categories else ""

        # Dates — prefer published-print, then published-online, then created
        def extract_date(date_obj: dict | None) -> str:
            if not date_obj:
                return ""
            parts = date_obj.get("date-parts", [[]])[0]
            if not parts:
                return ""
            year = parts[0] if len(parts) > 0 else 0
            month = parts[1] if len(parts) > 1 else 1
            day = parts[2] if len(parts) > 2 else 1
            return f"{year:04d}-{month:02d}-{day:02d}"

        published = (
            extract_date(item.get("published-print"))
            or extract_date(item.get("published-online"))
            or extract_date(item.get("created"))
        )
        updated = extract_date(item.get("deposited")) or published

        # URLs
        abs_url = f"https://doi.org/{doi}"
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break

        comment = normalize_whitespace(item.get("subtitle", [""])[0] if item.get("subtitle") else "")

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=abstract,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi Crossref REST API, luu raw response, parse thanh records."""
    base_url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": "DOI,title,abstract,author,subject,published-print,published-online,created,deposited,link,subtitle",
    }

    retryable = {429, 500, 502, 503, 504}
    max_retries = 5
    response = None

    for attempt in range(max_retries):
        try:
            response = requests.get(base_url, params=params, timeout=30)
            if response.status_code in retryable:
                wait = 2 ** attempt
                time.sleep(wait)
                continue
            response.raise_for_status()
            break
        except requests.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

    if response is None or not response.ok:
        raise RuntimeError("Failed to fetch records from Crossref API.")

    payload = response.json()
    write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)

    raw_dicts = [
        {
            "paper_id": r.paper_id,
            "title": r.title,
            "summary": r.summary,
            "authors": r.authors,
            "categories": r.categories,
            "primary_category": r.primary_category,
            "published": r.published,
            "updated": r.updated,
            "abs_url": r.abs_url,
            "pdf_url": r.pdf_url,
            "comment": r.comment,
        }
        for r in records
    ]
    write_json(settings.paths.raw_records_json, raw_dicts)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh list PaperRecord."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    records: list[PaperRecord] = []
    for item in raw:
        records.append(
            PaperRecord(
                paper_id=item.get("paper_id", ""),
                title=item.get("title", ""),
                summary=item.get("summary", ""),
                authors=item.get("authors", []),
                categories=item.get("categories", []),
                primary_category=item.get("primary_category", ""),
                published=item.get("published", ""),
                updated=item.get("updated", ""),
                abs_url=item.get("abs_url", ""),
                pdf_url=item.get("pdf_url", ""),
                comment=item.get("comment", ""),
            )
        )
    return records
