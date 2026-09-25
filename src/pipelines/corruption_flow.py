from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def _evaluate_dataset(df: pd.DataFrame, settings, embeddings_path, metrics_path, answers_path):
    index = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=embeddings_path)
    return evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=metrics_path,
        answers_output_path=answers_path,
    )


def _print_comparison(baseline: dict, corrupted: dict, repaired: dict) -> None:
    metric_names = (
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    print("\nBaseline vs. corrupted vs. repaired")
    print(f"{'Metric':<24} {'Baseline':>10} {'Corrupted':>10} {'Repaired':>10}")
    for name in metric_names:
        print(
            f"{name:<24} {baseline.get(name, float('nan')):>10.3f} "
            f"{corrupted.get(name, float('nan')):>10.3f} "
            f"{repaired.get(name, float('nan')):>10.3f}"
        )


def main() -> None:
    """Measure corruption impact and verify repair from preserved raw records."""
    settings = load_settings()
    paths = settings.paths
    required_paths = (paths.baseline_metrics, paths.clean_json, paths.eval_testset, paths.raw_records_json)
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Run the baseline pipeline first; required artifacts are missing: " + ", ".join(missing)
        )

    baseline_metrics = read_json(paths.baseline_metrics)
    baseline_df = pd.read_json(paths.clean_json)
    if baseline_df.empty:
        raise RuntimeError("Baseline clean dataset is empty; corruption flow cannot continue.")

    corrupted_df = corrupt_clean_dataframe(baseline_df.copy(deep=True), paths.corruption_log)
    if corrupted_df.empty:
        raise RuntimeError("Corruption produced an empty dataset; cannot evaluate its impact.")
    write_csv(corrupted_df, paths.corrupted_clean_csv)
    write_json(paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))

    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, paths.freshness_report
    )
    corrupted_evaluation = _evaluate_dataset(
        corrupted_df,
        settings,
        paths.corrupted_embeddings_json,
        paths.corrupted_metrics,
        paths.corrupted_answers,
    )

    raw_records = load_raw_records(paths.raw_records_json)
    if not raw_records:
        raise RuntimeError("Raw snapshot contains no records; cannot repair the dataset.")
    repaired_df = build_clean_dataframe(raw_records, datetime.now(UTC))
    if repaired_df.empty:
        raise RuntimeError("Rebuilding from raw records produced no usable papers.")
    write_csv(repaired_df, paths.repaired_clean_csv)
    write_json(paths.repaired_clean_json, repaired_df.to_dict(orient="records"))

    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, paths.freshness_report
    )
    repaired_evaluation = _evaluate_dataset(
        repaired_df,
        settings,
        paths.repaired_embeddings_json,
        paths.repaired_metrics,
        paths.repaired_answers,
    )

    generate_corruption_report(
        paths.comparison_report,
        baseline_metrics,
        corrupted_evaluation.summary,
        repaired_evaluation.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    _print_comparison(
        baseline_metrics,
        corrupted_evaluation.summary,
        repaired_evaluation.summary,
    )
    print(f"Corruption log: {paths.corruption_log}")
    print(f"Comparison report: {paths.comparison_report}")
