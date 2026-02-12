"""Ollama-backed LLM conjecture generator."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import httpx

from autonomous_discovery.config import LLMConfig
from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.gap_detector.analogical import GapCandidate

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a mathematical conjecture generator for Lean 4 and Mathlib.
Given a gap between algebraic families, produce a precise Lean 4 theorem or lemma
statement that would fill the gap. Output ONLY valid Lean 4 code.
Do NOT include import statements. Include the proof using `sorry` as placeholder.
"""

# Matches theorem/lemma declarations up to `:=` or `where` keyword.
# Limitation: _DECL_RE terminates at the first `:=` or `where`, which may
# falsely truncate declarations whose type signatures contain a literal `:=`
# (e.g., inside a `let` binding or default value in the return type) or an
# embedded `where` keyword.  A full Lean 4 parser would be needed to handle
# these edge cases; the regex is sufficient for typical LLM-generated output.
_DECL_RE = re.compile(
    r"((?:theorem|lemma)\s+\S+.*?)(?:\s*:=|\s+where\b)",
    re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class OllamaConjectureGenerator:
    """Generate conjectures via Ollama LLM inference."""

    config: LLMConfig = field(default_factory=LLMConfig)

    def generate(
        self,
        gaps: list[GapCandidate],
        *,
        max_candidates: int,
    ) -> list[ConjectureCandidate]:
        if max_candidates <= 0 or not gaps:
            return []

        ranked = sorted(
            gaps,
            key=lambda g: (-g.score, g.missing_decl, g.source_decl, g.target_family),
        )

        candidates: list[ConjectureCandidate] = []
        for gap in ranked:
            if len(candidates) >= max_candidates:
                break
            candidate = self._generate_for_gap(gap)
            if candidate is not None:
                candidates.append(candidate)
        return candidates

    def _generate_for_gap(self, gap: GapCandidate) -> ConjectureCandidate | None:
        messages = self._build_messages(gap)
        attempts = 1 + self.config.parse_retries

        for attempt_idx in range(attempts):
            try:
                content = self._call_ollama(messages)
            except Exception as exc:
                logger.warning(
                    "Ollama request failed for %s (attempt %d/%d): %s",
                    gap.missing_decl,
                    attempt_idx + 1,
                    attempts,
                    exc,
                )
                continue

            statements = self._parse_lean_statements(content)
            if statements:
                return ConjectureCandidate(
                    gap_missing_decl=gap.missing_decl,
                    lean_statement=statements[0],
                    rationale=(
                        f"LLM-generated conjecture for {gap.missing_decl} "
                        f"via analogy from {gap.source_decl} to {gap.target_family}."
                    ),
                    model_id=self.config.model_name,
                    temperature=self.config.temperature,
                    metadata={
                        "source_decl": gap.source_decl,
                        "target_family": gap.target_family,
                        "score": f"{gap.score:.6f}",
                    },
                )

            # Append failed response and repair prompt for retry
            logger.info(
                "No parseable Lean statement for %s (attempt %d/%d), retrying",
                gap.missing_decl,
                attempt_idx + 1,
                attempts,
            )
            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your response did not contain a valid Lean 4 theorem or lemma "
                        "declaration. Please output ONLY a single theorem/lemma "
                        "statement with `:= by sorry` proof."
                    ),
                }
            )

        logger.warning(
            "Failed to generate conjecture for %s after %d attempts",
            gap.missing_decl,
            attempts,
        )
        return None

    def _build_messages(self, gap: GapCandidate) -> list[dict[str, str]]:
        user_content = (
            f"Generate a Lean 4 theorem statement for the missing declaration: "
            f"{gap.missing_decl}\n"
            f"\n"
            f"Context:\n"
            f"- Source declaration: {gap.source_decl}\n"
            f"- Target family: {gap.target_family}\n"
            f"- Gap score: {gap.score:.4f}\n"
            f"- Signals: {gap.signals}\n"
            f"\n"
            f"The source declaration {gap.source_decl} exists but {gap.missing_decl} "
            f"does not. Write a plausible Lean 4 theorem or lemma that would fill this gap, "
            f"using appropriate type class assumptions for the {gap.target_family} family."
        )
        return [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def _call_ollama(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }
        response = httpx.post(
            f"{self.config.ollama_base_url}/api/chat",
            json=payload,
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        data = response.json()
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Unexpected Ollama response format: {exc}") from exc

    def _parse_lean_statements(self, raw: str) -> list[str]:
        """Extract theorem/lemma statement declarations from LLM output."""
        statements: list[str] = []
        for match in _DECL_RE.finditer(raw):
            stmt = match.group(1).strip()
            if stmt:
                statements.append(stmt)
        return statements
