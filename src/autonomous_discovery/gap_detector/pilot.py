"""Phase 1 pilot harness for gap detector artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from autonomous_discovery.gap_detector.analogical import (
    AnalogicalGapDetector,
    GapCandidate,
    GapDetectorConfig,
)
from autonomous_discovery.gap_detector.evaluation import build_topk_label_template_rows
from autonomous_discovery.gap_detector.report import write_gap_report
from autonomous_discovery.knowledge_base.graph import MathlibGraph
from autonomous_discovery.knowledge_base.parser import parse_declaration_types, parse_premises


def run_phase1_pilot(
    *,
    premises_path: Path,
    decl_types_path: Path,
    output_dir: Path,
    top_k: int = 20,
) -> dict[str, Any]:
    """Run analogical gap detection and emit pilot-ready artifacts."""
    premises = parse_premises(premises_path.read_text(encoding="utf-8"))
    declarations = parse_declaration_types(decl_types_path.read_text(encoding="utf-8"))
    graph = MathlibGraph.from_raw_data(premises, declarations)

    detector = AnalogicalGapDetector(config=GapDetectorConfig(top_k=top_k))
    candidates = detector.detect(graph)

    output_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = output_dir / "gap_candidates.jsonl"
    labels_path = output_dir / f"top{top_k}_label_template.csv"
    metrics_path = output_dir / "phase1_metrics.json"

    write_gap_report(candidates, candidates_path)
    _write_label_template(labels_path, candidates)

    summary = {
        "candidate_count": len(candidates),
        "top_k": top_k,
        "output_dir": str(output_dir),
        "candidates_path": str(candidates_path),
        "labels_path": str(labels_path),
        "metrics_path": str(metrics_path),
        "topk_precision": None,
        "detection_rate": None,
        "non_trivial_count": None,
        "go_no_go_status": "pending",
    }
    if top_k == 20:
        summary["top20_precision"] = None
    metrics_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _write_label_template(path: Path, candidates: list[GapCandidate]) -> None:
    rows = build_topk_label_template_rows(candidates)
    fieldnames = [
        "missing_decl",
        "source_decl",
        "target_family",
        "score",
        "label_non_trivial",
        "notes",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
