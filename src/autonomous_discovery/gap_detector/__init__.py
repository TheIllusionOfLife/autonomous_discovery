"""Gap detector: identifies knowledge gaps in the Mathlib dependency graph (Week 3-4)."""

from autonomous_discovery.gap_detector.analogical import (
    AnalogicalGapDetector,
    GapCandidate,
    GapDetectorConfig,
)
from autonomous_discovery.gap_detector.report import read_gap_report, write_gap_report
from autonomous_discovery.gap_detector.seeds import SeedHint, scan_seed_annotations

__all__ = [
    "AnalogicalGapDetector",
    "GapCandidate",
    "GapDetectorConfig",
    "SeedHint",
    "read_gap_report",
    "scan_seed_annotations",
    "write_gap_report",
]
