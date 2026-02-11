"""Report helpers for gap detector artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from autonomous_discovery.gap_detector.analogical import GapCandidate


def write_gap_report(candidates: list[GapCandidate], output_path: Path) -> None:
    """Write candidates as newline-delimited JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for candidate in candidates:
            f.write(
                json.dumps(
                    {
                        "source_decl": candidate.source_decl,
                        "target_family": candidate.target_family,
                        "missing_decl": candidate.missing_decl,
                        "score": candidate.score,
                        "signals": candidate.signals,
                    },
                    sort_keys=True,
                )
            )
            f.write("\n")


def read_gap_report(path: Path) -> list[GapCandidate]:
    """Load candidates from newline-delimited JSON."""
    candidates: list[GapCandidate] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            candidates.append(
                GapCandidate(
                    source_decl=record["source_decl"],
                    target_family=record["target_family"],
                    missing_decl=record["missing_decl"],
                    score=float(record["score"]),
                    signals={k: float(v) for k, v in record["signals"].items()},
                )
            )
    return candidates
