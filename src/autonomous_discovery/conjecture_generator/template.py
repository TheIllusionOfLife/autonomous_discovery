"""Template-based deterministic conjecture generator."""

from __future__ import annotations

import re
from dataclasses import dataclass

from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.gap_detector.analogical import GapCandidate


@dataclass(frozen=True, slots=True)
class TemplateConjectureGenerator:
    """Generate deterministic conjectures from gap candidates."""

    model_id: str = "template-v1"
    temperature: float = 0.0

    def generate(
        self,
        gaps: list[GapCandidate],
        *,
        max_candidates: int,
    ) -> list[ConjectureCandidate]:
        if max_candidates <= 0:
            return []

        ranked = sorted(
            gaps,
            key=lambda gap: (-gap.score, gap.missing_decl, gap.source_decl, gap.target_family),
        )

        candidates: list[ConjectureCandidate] = []
        for gap in ranked[:max_candidates]:
            theorem_name = self._safe_theorem_name(gap.missing_decl)
            rationale = (
                f"Analogical transfer from {gap.source_decl} to {gap.target_family} "
                f"for missing declaration {gap.missing_decl}."
            )
            metadata: dict[str, str] = {
                "source_decl": gap.source_decl,
                "target_family": gap.target_family,
                "score": f"{gap.score:.6f}",
            }
            for signal_name, signal_value in sorted(gap.signals.items()):
                metadata[f"signal_{signal_name}"] = f"{signal_value:.6f}"

            candidates.append(
                ConjectureCandidate(
                    gap_missing_decl=gap.missing_decl,
                    lean_statement=f"theorem {theorem_name} : True",
                    rationale=rationale,
                    model_id=self.model_id,
                    temperature=self.temperature,
                    metadata=metadata,
                )
            )

        return candidates

    def _safe_theorem_name(self, missing_decl: str) -> str:
        if "\n" in missing_decl or "\r" in missing_decl:
            raise ValueError("missing_decl contains newline characters")
        normalized = missing_decl.replace(".", "_")
        normalized = re.sub(r"[^A-Za-z0-9_]", "_", normalized)
        if not normalized:
            raise ValueError("missing_decl produced empty theorem name")
        if not re.match(r"^[A-Za-z_]", normalized):
            normalized = f"T_{normalized}"
        return normalized
