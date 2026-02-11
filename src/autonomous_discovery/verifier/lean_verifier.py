"""Lean-backed verifier implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from autonomous_discovery.lean_bridge.runner import LeanRunner
from autonomous_discovery.verifier.models import VerificationResult


@dataclass(slots=True)
class LeanVerifier:
    """Verify conjectures by compiling temporary Lean files."""

    runner: LeanRunner = field(default_factory=LeanRunner)
    timeout: int = 30

    def verify(self, statement: str, proof_script: str) -> VerificationResult:
        if not self.runner.check_lean_available():
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=False,
                stderr="Lean executable is not available on PATH.",
                timed_out=False,
            )

        with TemporaryDirectory(prefix="autonomous_discovery_lean_") as tmp_dir:
            lean_path = Path(tmp_dir) / "Candidate.lean"
            lean_path.write_text(
                f"{statement} :=\n{proof_script}\n",
                encoding="utf-8",
            )

            result = self.runner.run_command(["lean", str(lean_path)], timeout=self.timeout)
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=result.success,
                stderr=result.stderr,
                timed_out=result.timed_out,
            )
