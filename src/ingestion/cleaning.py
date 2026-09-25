from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    rows: list[dict] = []

    for rec in records:
        # 1. Normalize title, summary
        title = normalize_whitespace(rec.title)
        summary = normalize_whitespace(rec.summary)
        if not title or not rec.paper_id:
            continue

        # 2. Normalize authors & categories
        authors = [normalize_whitespace(a) for a in rec.authors if a and a.strip()]
        categories = [normalize_whitespace(c) for c in rec.categories if c and c.strip()]

        # 3. Parse published date
        published_str = rec.published or ""
        try:
            if len(published_str) >= 10:
                published_dt = datetime.strptime(published_str[:10], "%Y-%m-%d")
            else:
                published_dt = None
        except ValueError:
            published_dt = None

        # 4. Tinh age_days
        if published_dt:
            run_dt = run_date.replace(tzinfo=None) if run_date.tzinfo else run_date
            age_days = (run_dt - published_dt).days
        else:
            age_days = -1

        # 5. Helper columns
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)
        summary_chars = len(summary)

        # text_for_embedding: combine title + summary + authors + categories
        text_parts = [title, summary]
        if authors_joined:
            text_parts.append(f"Authors: {authors_joined}")
        if categories_joined:
            text_parts.append(f"Categories: {categories_joined}")
        text_for_embedding = " | ".join(p for p in text_parts if p)

        rows.append(
            {
                "paper_id": rec.paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": rec.primary_category,
                "published": published_str,
                "updated": rec.updated,
                "abs_url": rec.abs_url,
                "pdf_url": rec.pdf_url,
                "comment": rec.comment,
                "age_days": age_days,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "text_for_embedding": text_for_embedding,
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # 6. Drop duplicates & filter bad rows
    df = df.drop_duplicates(subset=["paper_id"])
    df = df[df["title"].str.strip().ne("")]
    df = df[df["text_for_embedding"].str.strip().ne("")]

    # 7. Sort by published date desc
    df = df.sort_values("published", ascending=False).reset_index(drop=True)

    return df
