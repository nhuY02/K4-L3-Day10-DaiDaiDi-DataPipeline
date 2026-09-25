from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors",
    "categories",
    "primary_category",
    "published",
    "updated",
    "abs_url",
    "pdf_url",
    "comment",
    "authors_joined",
    "categories_joined",
    "summary_chars",
    "age_days",
    "text_for_embedding",
]


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Build a deterministic, retrieval-ready dataframe from raw records."""

    def clean_text(value: Any) -> str:
        return normalize_whitespace(str(value)) if value is not None else ""

    def clean_list(value: Any) -> list[str]:
        if isinstance(value, (list, tuple)):
            values = value
        elif value is None or value == "":
            values = []
        else:
            values = [value]
        return [text for item in values if (text := clean_text(item))]

    run_timestamp = pd.Timestamp(run_date)
    if run_timestamp.tzinfo is None:
        run_timestamp = run_timestamp.tz_localize("UTC")
    else:
        run_timestamp = run_timestamp.tz_convert("UTC")

    rows: list[dict[str, Any]] = []
    for record in records:
        paper_id = clean_text(record.paper_id)
        title = clean_text(record.title)
        summary = clean_text(record.summary)
        authors = clean_list(record.authors)
        categories = clean_list(record.categories)
        primary_category = clean_text(record.primary_category) or (categories[0] if categories else "")

        published_timestamp = pd.to_datetime(record.published, errors="coerce", utc=True)
        if not paper_id or not title or pd.isna(published_timestamp):
            continue
        updated_timestamp = pd.to_datetime(record.updated, errors="coerce", utc=True)

        published = published_timestamp.strftime("%Y-%m-%d")
        updated = "" if pd.isna(updated_timestamp) else updated_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)
        age_days = max(0, int((run_timestamp - published_timestamp).days))
        text_for_embedding = "\n".join(
            [
                f"Title: {title}",
                f"Authors: {authors_joined}",
                f"Published: {published}",
                f"Categories: {categories_joined}",
                f"Summary: {summary}",
            ]
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "abs_url": clean_text(record.abs_url),
                "pdf_url": clean_text(record.pdf_url),
                "comment": clean_text(record.comment),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
                "_paper_id_key": paper_id.casefold(),
            }
        )

    if not rows:
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    dataframe = pd.DataFrame(rows)
    dataframe = dataframe.drop_duplicates(subset="_paper_id_key", keep="first")
    dataframe = dataframe.sort_values(["_paper_id_key", "title"], kind="stable")
    dataframe = dataframe.drop(columns="_paper_id_key")
    return dataframe[CLEAN_COLUMNS].reset_index(drop=True)
