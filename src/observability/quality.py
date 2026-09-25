from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


MIN_ROW_COUNT = 5
MAX_ROW_COUNT = 5_000
MIN_SUMMARY_LENGTH = 30
MAX_STALE_RATIO = 0.25


def _quality_report_path(settings: Settings, report_name: str) -> Path:
    """Resolve the configured artifact path for a quality report."""
    normalized_name = report_name.strip().lower()
    if "baseline" in normalized_name:
        return settings.paths.baseline_quality_report
    if "corrupt" in normalized_name:
        return settings.paths.corrupted_quality_report
    return settings.paths.quality_dir / f"{safe_slug(report_name)}_quality_report.json"


def _validation_result_payload(expectation, validation_result) -> dict[str, Any]:
    """Keep the useful, JSON-safe part of a GX validation result."""
    raw_result = validation_result.to_json_dict()
    return {
        "expectation_type": expectation.__class__.__name__,
        "column": getattr(expectation, "column", None),
        "success": bool(raw_result["success"]),
        "result": raw_result.get("result", {}),
    }


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Validate a cleaned papers dataframe with the required GX 1.x checks."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")
    if not report_name.strip():
        raise ValueError("report_name must not be empty.")

    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    expectation_specs = [
        (
            gxe.ExpectTableRowCountToBeBetween(
                min_value=MIN_ROW_COUNT,
                max_value=MAX_ROW_COUNT,
            ),
            None,
        ),
        (gxe.ExpectColumnValuesToNotBeNull(column="paper_id"), "paper_id"),
        (gxe.ExpectColumnValuesToNotBeNull(column="title"), "title"),
        (gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"), "text_for_embedding"),
        (gxe.ExpectColumnValuesToBeUnique(column="paper_id"), "paper_id"),
        (
            gxe.ExpectColumnValueLengthsToBeBetween(
                column="summary",
                min_value=MIN_SUMMARY_LENGTH,
            ),
            "summary",
        ),
    ]

    results: list[dict[str, Any]] = []
    for expectation, required_column in expectation_specs:
        if required_column is not None and required_column not in df.columns:
            results.append(
                {
                    "expectation_type": expectation.__class__.__name__,
                    "column": required_column,
                    "success": False,
                    "result": {"missing_column": required_column},
                }
            )
            continue

        try:
            validation_result = batch.validate(expectation)
            results.append(_validation_result_payload(expectation, validation_result))
        except Exception as exc:  # GX should fail the gate instead of crashing the pipeline.
            results.append(
                {
                    "expectation_type": expectation.__class__.__name__,
                    "column": required_column,
                    "success": False,
                    "result": {"exception": f"{type(exc).__name__}: {exc}"},
                }
            )

    failed_count = sum(not result["success"] for result in results)
    report = {
        "report_name": report_name,
        "success": failed_count == 0,
        "row_count": int(len(df)),
        "expectation_count": len(results),
        "failed_expectation_count": failed_count,
        "results": results,
    }
    write_json(_quality_report_path(settings, report_name), report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build and persist the freshness SLA report for a papers dataframe."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    total_rows = int(len(df))
    published = (
        pd.to_datetime(df["published"], errors="coerce", utc=True)
        if "published" in df.columns
        else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]")
    )
    age_days = (
        pd.to_numeric(df["age_days"], errors="coerce")
        if "age_days" in df.columns
        else pd.Series(float("nan"), index=df.index, dtype="float64")
    )

    valid_published = published.dropna()
    valid_age_rows = int(age_days.notna().sum())
    stale_rows = int(age_days.gt(settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows if total_rows else 0.0
    is_fresh = total_rows > 0 and valid_age_rows == total_rows and stale_ratio <= MAX_STALE_RATIO

    report = {
        "latest_published": (
            valid_published.max().date().isoformat() if not valid_published.empty else None
        ),
        "oldest_published": (
            valid_published.min().date().isoformat() if not valid_published.empty else None
        ),
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": MAX_STALE_RATIO,
        "is_fresh": is_fresh,
    }
    write_json(Path(report_path), report)
    return report
