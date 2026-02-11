"""Data models for Lean verification outcomes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Outcome of verifying a statement and proof script in Lean."""

    statement: str
    proof_script: str
    success: bool
    stderr: str
    timed_out: bool
