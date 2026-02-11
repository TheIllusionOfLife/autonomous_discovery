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
    max_stderr_chars: int = 2000

    _disallowed_tokens: tuple[str, ...] = (
        "run_cmd",
        "unsafe",
        "#eval",
        "#print",
        "IO.",
        "open IO",
    )

    def is_available(self) -> bool:
        return self.runner.check_lean_available()

    def verify(self, statement: str, proof_script: str) -> VerificationResult:
        if not self.is_available():
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=False,
                stderr="Lean executable is not available on PATH.",
                timed_out=False,
            )

        if self._contains_disallowed_content(statement, proof_script):
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=False,
                stderr="Unsafe Lean directives are not permitted in verifier inputs.",
                timed_out=False,
            )

        with TemporaryDirectory(prefix="autonomous_discovery_lean_") as tmp_dir:
            lean_path = Path(tmp_dir) / "Candidate.lean"
            lean_path.write_text(
                f"{statement} :=\n{proof_script}\n",
                encoding="utf-8",
            )

            result = self.runner.run_command(
                ["lean", str(lean_path)],
                timeout=self.timeout,
                cwd=tmp_dir,
            )
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=result.success,
                stderr=self._sanitize_stderr(result.stderr, tmp_dir),
                timed_out=result.timed_out,
            )

    def _contains_disallowed_content(self, statement: str, proof_script: str) -> bool:
        payload = f"{statement}\n{proof_script}".lower()
        return any(token.lower() in payload for token in self._disallowed_tokens)

    def _sanitize_stderr(self, stderr: str, tmp_dir: str) -> str:
        redacted = stderr.replace(tmp_dir, "<tmpdir>")
        if len(redacted) <= self.max_stderr_chars:
            return redacted
        return redacted[: self.max_stderr_chars] + "...<truncated>"
