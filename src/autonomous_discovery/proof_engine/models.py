"""Data models for proof attempts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProofAttempt:
    """A single generated proof attempt for a conjecture."""

    statement: str
    proof_script: str
    engine: str
    attempt_index: int
