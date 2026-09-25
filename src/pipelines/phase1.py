from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def _load_or_fetch_records(settings):
    """Prefer the preserved snapshot unless an explicit source refresh is requested."""
    raw_records_path = settings.paths.raw_records_json
    if settings.refresh_source or not raw_records_path.exists():
        return fetch_source_records(settings)
    return load_raw_records(raw_records_path)


def _load_or_build_test_set(df: pd.DataFrame, settings) -> list[dict]:
    """Reuse a fixed benchmark set unless refresh was requested or it is missing."""
    test_set_path = settings.paths.eval_testset
    if not settings.refresh_test_set and test_set_path.exists():
        try:
            test_set = read_json(test_set_path)
        except (OSError, ValueError):
            test_set = None
        if isinstance(test_set, list) and test_set:
            return test_set
    return build_test_set(df, test_set_path)


def main() -> None:
    """Run the clean-data baseline pipeline and write its artifacts."""
    settings = load_settings()
    run_date = datetime.now(UTC)

    records = _load_or_fetch_records(settings)
    if not records:
        raise RuntimeError("No Crossref records are available for the baseline pipeline.")

    df = build_clean_dataframe(records, run_date)
    if df.empty:
        raise RuntimeError("Cleaning produced no usable paper records.")

    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))

    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    if not quality.get("success", False):
        raise RuntimeError(
            "Baseline data quality gate failed; refusing to build the vector index. "
            f"See {settings.paths.baseline_quality_report}."
        )

    test_set = _load_or_build_test_set(df, settings)
    if not test_set:
        raise RuntimeError("Evaluation test set is empty; cannot measure the baseline.")

    index = LocalEmbeddingIndex.build(df, settings)
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    source_summary = {
        "source": settings.source_api,
        "records_loaded": len(records),
        "records_cleaned": len(df),
        "raw_response_path": str(settings.paths.raw_api_response),
        "raw_records_path": str(settings.paths.raw_records_json),
        "run_date": run_date.isoformat(),
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        evaluation.summary,
        quality,
        freshness,
    )

    print("Baseline pipeline completed.")
    print(f"Records: {len(records)} raw -> {len(df)} clean")
    print(f"Quality gate: {'PASS' if quality.get('success') else 'FAIL'}")
    print(f"Retrieval hit rate: {evaluation.summary['retrieval_hit_rate']:.3f}")
    print(f"Mean token F1: {evaluation.summary['mean_token_f1']:.3f}")
    print(f"Clean data: {settings.paths.clean_csv}")
    print(f"Metrics: {settings.paths.baseline_metrics}")
    print(f"Report: {settings.paths.baseline_report}")
