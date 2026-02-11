"""Evaluation helpers for Phase 1 gap detector metrics."""

from __future__ import annotations

from autonomous_discovery.gap_detector.analogical import GapCandidate


def compute_topk_precision(labels: list[bool]) -> float:
    """Compute precision over top-k labels."""
    if not labels:
        return 0.0
    return sum(1 for label in labels if label) / len(labels)


def compute_detection_rate(*, non_trivial_count: int, total_candidates: int) -> float:
    """Compute non-trivial detection rate among scored candidates."""
    if total_candidates == 0:
        return 0.0
    return non_trivial_count / total_candidates


def build_topk_label_template_rows(candidates: list[GapCandidate]) -> list[dict[str, str]]:
    """Build CSV rows for manual top-k labeling."""
    return [
        {
            "missing_decl": c.missing_decl,
            "source_decl": c.source_decl,
            "target_family": c.target_family,
            "score": f"{c.score:.6f}",
            "label_non_trivial": "",
            "notes": "",
        }
        for c in candidates
    ]
