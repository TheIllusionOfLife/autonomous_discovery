"""JSONL IO helpers for conjecture candidates."""

from __future__ import annotations

import json
from pathlib import Path

from autonomous_discovery.conjecture_generator.models import ConjectureCandidate


def write_conjectures(conjectures: list[ConjectureCandidate], path: Path) -> None:
    """Write conjecture candidates to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for conjecture in conjectures:
            row = {
                "gap_missing_decl": conjecture.gap_missing_decl,
                "lean_statement": conjecture.lean_statement,
                "rationale": conjecture.rationale,
                "model_id": conjecture.model_id,
                "temperature": conjecture.temperature,
                "metadata": conjecture.metadata,
            }
            f.write(json.dumps(row, sort_keys=True) + "\n")


def read_conjectures(path: Path) -> list[ConjectureCandidate]:
    """Read conjecture candidates from JSONL."""
    items: list[ConjectureCandidate] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            items.append(
                ConjectureCandidate(
                    gap_missing_decl=row["gap_missing_decl"],
                    lean_statement=row["lean_statement"],
                    rationale=row["rationale"],
                    model_id=row["model_id"],
                    temperature=float(row["temperature"]),
                    metadata={str(k): str(v) for k, v in row.get("metadata", {}).items()},
                )
            )
    return items
