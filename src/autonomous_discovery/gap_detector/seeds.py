"""Seed-source helpers for initial gap inventory candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SeedHint:
    """A TODO/sorry annotation that may indicate a useful gap seed."""

    file_path: str
    line_number: int
    kind: str
    content: str


def scan_seed_annotations(paths: list[Path]) -> list[SeedHint]:
    """Scan Lean files for TODO/sorry markers."""
    hints: list[SeedHint] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for index, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            lowered = stripped.lower()
            if "todo" in lowered:
                hints.append(
                    SeedHint(
                        file_path=str(path),
                        line_number=index,
                        kind="todo",
                        content=stripped,
                    )
                )
            elif lowered == "sorry" or lowered.startswith("sorry "):
                hints.append(
                    SeedHint(
                        file_path=str(path),
                        line_number=index,
                        kind="sorry",
                        content=stripped,
                    )
                )
    return hints
