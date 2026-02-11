"""Deterministic novelty checker with layered duplicate detection.

Layers are evaluated in order:
1. exact string duplicate
2. normalized duplicate (comments + whitespace)
3. lightweight defEq-style duplicate via binder alpha-normalization
4. bi-implication duplicate (P ↔ Q)

Optional semantic comparison can be plugged in as a final duplicate check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SemanticComparison:
    """Comparator result for optional semantic equivalence checks."""

    equivalent: bool
    confidence: float
    reason: str = ""


class SemanticComparator(Protocol):
    """Interface for optional semantic equivalence backends."""

    def compare(self, left: str, right: str) -> SemanticComparison: ...


@dataclass(frozen=True, slots=True)
class NoveltyDecision:
    """Decision returned by novelty checker backends."""

    is_novel: bool
    reason: str
    layer: str | None = None
    confidence: float | None = None


@dataclass(slots=True)
class BasicNoveltyChecker:
    """Layered novelty checker with deterministic defaults.

    This checker is stateful: novel statements are added to ``existing_statements``.
    Normalization strips line comments only (not nested Lean block comments).
    """

    existing_statements: set[str] = field(default_factory=set)
    semantic_comparator: SemanticComparator | None = None
    semantic_compare_limit: int = 20
    semantic_confidence_threshold: float = 0.9

    _normalized_existing: set[str] = field(init=False, default_factory=set)
    _defeq_existing: set[str] = field(init=False, default_factory=set)
    _bi_implication_existing: set[tuple[str, str]] = field(init=False, default_factory=set)
    _seen_order: list[str] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        for statement in self.existing_statements:
            self._index_statement(statement)

    def is_novel(self, statement: str) -> NoveltyDecision:
        if statement in self.existing_statements:
            return NoveltyDecision(is_novel=False, reason="exact_duplicate")

        normalized = self._normalize(statement)
        if normalized in self._normalized_existing:
            return NoveltyDecision(is_novel=False, reason="normalized_duplicate")

        defeq_key = self._defeq_key(statement)
        if defeq_key in self._defeq_existing:
            return NoveltyDecision(is_novel=False, reason="defeq_duplicate")

        bi_implication_key = self._bi_implication_key(statement)
        if bi_implication_key is not None and bi_implication_key in self._bi_implication_existing:
            return NoveltyDecision(is_novel=False, reason="bi_implication_duplicate")

        semantic = self._semantic_decision(statement)
        if semantic is not None:
            return semantic

        self._index_statement(statement)
        return NoveltyDecision(is_novel=True, reason="novel")

    def _index_statement(self, statement: str) -> None:
        self.existing_statements.add(statement)
        self._seen_order.append(statement)
        self._normalized_existing.add(self._normalize(statement))
        self._defeq_existing.add(self._defeq_key(statement))
        bi_key = self._bi_implication_key(statement)
        if bi_key is not None:
            self._bi_implication_existing.add(bi_key)

    def _semantic_decision(self, statement: str) -> NoveltyDecision | None:
        if self.semantic_comparator is None or not self._seen_order:
            return None

        best_low_confidence: float | None = None
        compare_scope = self._seen_order[-self.semantic_compare_limit :]
        for previous in reversed(compare_scope):
            try:
                comparison = self.semantic_comparator.compare(statement, previous)
            except Exception:
                continue
            if not comparison.equivalent:
                continue
            if comparison.confidence >= self.semantic_confidence_threshold:
                return NoveltyDecision(
                    is_novel=False,
                    reason="semantic_duplicate",
                    layer="semantic",
                    confidence=comparison.confidence,
                )
            if best_low_confidence is None or comparison.confidence > best_low_confidence:
                best_low_confidence = comparison.confidence

        if best_low_confidence is not None:
            return NoveltyDecision(
                is_novel=False,
                reason="unknown",
                layer="semantic",
                confidence=best_low_confidence,
            )

        return None

    def _normalize(self, statement: str) -> str:
        without_line_comments = re.sub(r"--.*$", "", statement, flags=re.MULTILINE)
        return re.sub(r"\s+", " ", without_line_comments).strip()

    def _defeq_key(self, statement: str) -> str:
        body = self._statement_body(statement)
        return self._alpha_normalize_binders(body)

    def _statement_body(self, statement: str) -> str:
        normalized = self._normalize(statement)
        theorem_prefix = re.match(r"^\s*theorem\s+[A-Za-z_][A-Za-z0-9_']*\s*:\s*(.+)$", normalized)
        if theorem_prefix:
            return theorem_prefix.group(1).strip()
        parts = normalized.split(":", maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip()
        return normalized

    def _alpha_normalize_binders(self, expr: str) -> str:
        binder_names: list[str] = []
        pattern = (
            r"(?:∀|forall)\s*(?:\(\s*([A-Za-z_][A-Za-z0-9_']*)\s*:|"
            r"([A-Za-z_][A-Za-z0-9_']*)\s*:)"
        )
        for match in re.finditer(pattern, expr):
            name = match.group(1) or match.group(2)
            if name:
                binder_names.append(name)

        mapping: dict[str, str] = {}
        for name in binder_names:
            if name not in mapping:
                mapping[name] = f"v{len(mapping) + 1}"

        normalized = expr
        for original, canonical in mapping.items():
            normalized = re.sub(rf"\b{re.escape(original)}\b", canonical, normalized)
        normalized = re.sub(r"\bforall\b", "∀", normalized)
        normalized = re.sub(
            r"∀\s*\(\s*([A-Za-z_][A-Za-z0-9_']*)\s*:\s*([^)]+?)\s*\)",
            r"∀ \1 : \2",
            normalized,
        )
        return re.sub(r"\s+", " ", normalized).strip()

    def _bi_implication_key(self, statement: str) -> tuple[str, str] | None:
        body = self._statement_body(statement)
        if "↔" in body:
            left, right = body.split("↔", maxsplit=1)
            return self._canonical_relation_pair(left, right)

        return None

    def _canonical_relation_pair(self, left: str, right: str) -> tuple[str, str] | None:
        left_norm = self._strip_wrapping_parens(self._normalize(left))
        right_norm = self._strip_wrapping_parens(self._normalize(right))
        if not left_norm or not right_norm:
            return None
        return tuple(sorted((left_norm, right_norm)))

    def _strip_wrapping_parens(self, text: str) -> str:
        candidate = text.strip()
        while self._is_fully_wrapped(candidate):
            inner = candidate[1:-1].strip()
            if not inner:
                break
            candidate = inner
        return candidate

    def _is_fully_wrapped(self, text: str) -> bool:
        if len(text) < 2 or text[0] != "(" or text[-1] != ")":
            return False

        depth = 0
        for index, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    return False
                if depth == 0 and index != len(text) - 1:
                    return False
        return depth == 0
