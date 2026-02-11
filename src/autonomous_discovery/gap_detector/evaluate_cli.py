"""CLI for computing Phase 1 go/no-go metrics from labeled top-k gaps."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from autonomous_discovery.config import ProjectConfig
from autonomous_discovery.gap_detector.evaluation import (
    compute_detection_rate,
    compute_topk_precision,
)

POSITIVE_LABELS = {"1", "true", "yes", "y"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate labeled top-k gap candidates.")
    parser.add_argument("--metrics-path", type=Path, required=True)
    parser.add_argument("--labels-csv", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=None)
    return parser


def _is_non_trivial(label_value: str) -> bool:
    return label_value.strip().lower() in POSITIVE_LABELS


def _module_proxy(decl_name: str) -> str:
    parts = [part for part in decl_name.split(".") if part]
    if len(parts) >= 3:
        return ".".join(parts[:2])
    if parts:
        return parts[0]
    return "<unknown>"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = ProjectConfig()

    try:
        metrics = json.loads(args.metrics_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Input file not found: {args.metrics_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in metrics file: {exc}", file=sys.stderr)
        return 1

    try:
        with args.labels_csv.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"Input file not found: {args.labels_csv}", file=sys.stderr)
        return 1

    if rows and "label_non_trivial" not in rows[0]:
        print("Labels CSV must include 'label_non_trivial' column", file=sys.stderr)
        return 1
    if rows and "source_decl" not in rows[0]:
        print("Labels CSV must include 'source_decl' column", file=sys.stderr)
        return 1

    try:
        requested_top_k = args.top_k if args.top_k is not None else int(metrics.get("top_k", 20))
    except (TypeError, ValueError):
        print("Invalid top_k value in metrics file", file=sys.stderr)
        return 1
    if requested_top_k <= 0:
        print("top_k must be a positive integer", file=sys.stderr)
        return 1

    top_rows = rows[:requested_top_k]
    labels = [_is_non_trivial(row.get("label_non_trivial") or "") for row in top_rows]
    non_trivial_count = sum(1 for label in labels if label)
    topk_precision = compute_topk_precision(labels)

    evaluated_modules = {_module_proxy(row.get("source_decl") or "") for row in top_rows}
    non_trivial_modules = {
        _module_proxy(row.get("source_decl") or "")
        for row, is_non_trivial in zip(top_rows, labels, strict=True)
        if is_non_trivial
    }
    evaluated_module_count = len(evaluated_modules)
    modules_with_non_trivial_gaps_count = len(non_trivial_modules)
    detection_rate = compute_detection_rate(
        non_trivial_count=modules_with_non_trivial_gaps_count,
        total_candidates=evaluated_module_count,
    )
    non_trivial_candidate_rate = compute_detection_rate(
        non_trivial_count=non_trivial_count,
        total_candidates=len(top_rows),
    )

    primary_ok = detection_rate >= config.min_detection_rate
    secondary_ok = topk_precision >= config.min_top20_precision
    absolute_ok = non_trivial_count >= config.min_nontrivial_gaps
    go_no_go_status = "go" if absolute_ok and (primary_ok or secondary_ok) else "no_go"

    if requested_top_k == 20:
        metrics["top20_precision"] = topk_precision
    else:
        metrics.pop("top20_precision", None)
    metrics["topk_precision"] = topk_precision
    metrics["detection_rate"] = detection_rate
    metrics["detection_rate_basis"] = "evaluated_module_proxy_rate"
    metrics["non_trivial_candidate_rate"] = non_trivial_candidate_rate
    metrics["non_trivial_count"] = non_trivial_count
    metrics["evaluated_module_count"] = evaluated_module_count
    metrics["modules_with_non_trivial_gaps_count"] = modules_with_non_trivial_gaps_count
    metrics["go_no_go_checks"] = {
        "primary_detection_rate_ok": primary_ok,
        "secondary_topk_precision_ok": secondary_ok,
        "minimum_non_trivial_count_ok": absolute_ok,
    }
    metrics["go_no_go_status"] = go_no_go_status
    args.metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
