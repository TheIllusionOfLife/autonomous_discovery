"""Simple deterministic proof attempt generator."""

from __future__ import annotations

from dataclasses import dataclass

from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.proof_engine.models import ProofAttempt


@dataclass(frozen=True, slots=True)
class SimpleProofEngine:
    """Build a small sequence of baseline proof attempts."""

    engine_name: str = "simple-proof-engine"

    def build_attempts(
        self,
        conjecture: ConjectureCandidate,
        *,
        max_attempts: int = 3,
    ) -> list[ProofAttempt]:
        if max_attempts <= 0:
            return []

        scripts = [
            "by\n  exact?",
            "by\n  aesop",
            "by\n  simp",
        ]
        capped = scripts[:max_attempts]
        return [
            ProofAttempt(
                statement=conjecture.lean_statement,
                proof_script=script,
                engine=self.engine_name,
                attempt_index=index,
            )
            for index, script in enumerate(capped, start=1)
        ]
