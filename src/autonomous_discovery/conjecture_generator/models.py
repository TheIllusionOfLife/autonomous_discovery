"""Data models for conjecture generation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ConjectureCandidate:
    """A conjecture candidate generated for a detected gap."""

    gap_missing_decl: str
    lean_statement: str
    rationale: str
    model_id: str
    temperature: float
    metadata: dict[str, str] = field(default_factory=dict)
