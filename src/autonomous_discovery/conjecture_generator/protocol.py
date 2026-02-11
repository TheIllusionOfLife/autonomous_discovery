"""Protocols for conjecture generation implementations."""

from __future__ import annotations

from typing import Protocol

from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.gap_detector.analogical import GapCandidate


class ConjectureGenerator(Protocol):
    """Protocol for deterministic or model-backed conjecture generators."""

    def generate(
        self,
        gaps: list[GapCandidate],
        *,
        max_candidates: int,
    ) -> list[ConjectureCandidate]: ...
