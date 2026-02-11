"""Deterministic counterexample pre-filter for conjectures."""

from __future__ import annotations

from dataclasses import dataclass

from autonomous_discovery.conjecture_generator.models import ConjectureCandidate


@dataclass(frozen=True, slots=True)
class FilterDecision:
    """Result of filtering a conjecture before proof attempts."""

    accepted: bool
    reason: str


@dataclass(frozen=True, slots=True)
class BasicCounterexampleFilter:
    """Cheap string-based guardrails before expensive verification."""

    def evaluate(self, conjecture: ConjectureCandidate) -> FilterDecision:
        statement = conjecture.lean_statement.lower()
        if " : false" in statement:
            return FilterDecision(accepted=False, reason="contains_false_literal")
        if "1 = 0" in statement or "0 = 1" in statement:
            return FilterDecision(accepted=False, reason="contains_obvious_contradiction")
        return FilterDecision(accepted=True, reason="passed_basic_checks")
