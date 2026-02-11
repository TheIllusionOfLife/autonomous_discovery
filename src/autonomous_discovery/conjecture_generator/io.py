"""JSONL IO helpers for conjecture candidates."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from autonomous_discovery.conjecture_generator.models import ConjectureCandidate


def write_conjectures(conjectures: list[ConjectureCandidate], path: Path) -> None:
    """Write conjecture candidates to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for conjecture in conjectures:
            row = asdict(conjecture)
            f.write(json.dumps(row, sort_keys=True) + "\n")


def read_conjectures(path: Path) -> list[ConjectureCandidate]:
    """Read conjecture candidates from JSONL."""
    items: list[ConjectureCandidate] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            metadata_raw = row.get("metadata", {})
            if not isinstance(metadata_raw, dict):
                raise ValueError("metadata must be a JSON object")
            try:
                items.append(
                    ConjectureCandidate(
                        gap_missing_decl=str(row["gap_missing_decl"]),
                        lean_statement=str(row["lean_statement"]),
                        rationale=str(row["rationale"]),
                        model_id=str(row["model_id"]),
                        temperature=float(row["temperature"]),
                        metadata={str(k): str(v) for k, v in metadata_raw.items()},
                    )
                )
            except KeyError as exc:
                raise ValueError(f"Missing required field in JSONL line: {exc}") from exc
    return items
