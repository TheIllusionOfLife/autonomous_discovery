"""Deterministic novelty checker baseline."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class NoveltyDecision:
    """Decision returned by novelty checker backends."""

    is_novel: bool
    reason: str


@dataclass(slots=True)
class BasicNoveltyChecker:
    """Baseline duplicate detector using exact and normalized matching."""

    existing_statements: set[str] = field(default_factory=set)
    _normalized_existing: set[str] = field(init=False, default_factory=set)

    def __post_init__(self) -> None:
        self._normalized_existing = {self._normalize(s) for s in self.existing_statements}

    def is_novel(self, statement: str) -> NoveltyDecision:
        if statement in self.existing_statements:
            return NoveltyDecision(is_novel=False, reason="exact_duplicate")

        normalized = self._normalize(statement)
        if normalized in self._normalized_existing:
            return NoveltyDecision(is_novel=False, reason="normalized_duplicate")

        self.existing_statements.add(statement)
        self._normalized_existing.add(normalized)
        return NoveltyDecision(is_novel=True, reason="novel")

    def _normalize(self, statement: str) -> str:
        return re.sub(r"\s+", " ", statement).strip()
