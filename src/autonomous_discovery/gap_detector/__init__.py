"""Gap detector: identifies knowledge gaps in the Mathlib dependency graph (Week 3-4)."""

from autonomous_discovery.gap_detector.analogical import (
    AnalogicalGapDetector,
    GapCandidate,
    GapDetectorConfig,
)
from autonomous_discovery.gap_detector.evaluate_cli import main as evaluate_metrics_cli_main
from autonomous_discovery.gap_detector.evaluation import (
    build_topk_label_template_rows,
    compute_detection_rate,
    compute_topk_precision,
)
from autonomous_discovery.gap_detector.pilot import run_phase1_pilot
from autonomous_discovery.gap_detector.report import read_gap_report, write_gap_report
from autonomous_discovery.gap_detector.seeds import SeedHint, scan_seed_annotations

__all__ = [
    "AnalogicalGapDetector",
    "GapCandidate",
    "GapDetectorConfig",
    "SeedHint",
    "build_topk_label_template_rows",
    "compute_detection_rate",
    "compute_topk_precision",
    "evaluate_metrics_cli_main",
    "read_gap_report",
    "run_phase1_pilot",
    "scan_seed_annotations",
    "write_gap_report",
]
