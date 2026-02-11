"""Lean-backed verifier implementation."""

from __future__ import annotations

import re
import shutil
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
    require_sandbox: bool = True
    sandbox_command_prefix: tuple[str, ...] = ("nsjail",)

    _disallowed_patterns: tuple[re.Pattern[str], ...] = (
        re.compile(r"\brun_cmd\b", re.IGNORECASE),
        re.compile(r"\bunsafe\b", re.IGNORECASE),
        re.compile(r"#eval\b", re.IGNORECASE),
        re.compile(r"#print\b", re.IGNORECASE),
        re.compile(r"(?<![A-Za-z0-9_])IO\.", re.IGNORECASE),
        re.compile(r"\bopen\s+IO\b", re.IGNORECASE),
    )
    _statement_pattern: re.Pattern[str] = re.compile(
        r"^\s*theorem\s+[A-Za-z_][A-Za-z0-9_]*\s*:\s*True\s*$"
    )
    _proof_pattern: re.Pattern[str] = re.compile(
        r"^\s*by\s*\n\s*(exact\?|aesop|simp|trivial)\s*$",
        re.IGNORECASE,
    )

    def is_available(self) -> bool:
        return self.runner.check_lean_available()

    def runtime_status(self) -> dict[str, bool]:
        lean_available = self.is_available()
        sandbox_available = self._sandbox_available()
        runtime_ready = lean_available and (sandbox_available or not self.require_sandbox)
        return {
            "lean_available": lean_available,
            "sandbox_available": sandbox_available,
            "runtime_ready": runtime_ready,
        }

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
        if not self._is_supported_input_shape(statement, proof_script):
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=False,
                stderr=(
                    "Verifier only accepts constrained theorem/proof shapes for safety. "
                    "Use trusted mode with a separate sandboxed backend for arbitrary code."
                ),
                timed_out=False,
            )
        if self.require_sandbox and not self._sandbox_available():
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=False,
                stderr=(
                    "Sandbox runtime is required for Lean verification but was not found. "
                    "Configure sandbox_command_prefix or disable require_sandbox "
                    "for trusted-only runs."
                ),
                timed_out=False,
            )

        with TemporaryDirectory(prefix="autonomous_discovery_lean_") as tmp_dir:
            lean_path = Path(tmp_dir) / "Candidate.lean"
            content = f"import Mathlib\n\n{statement} :=\n{proof_script}\n"
            lean_path.write_text(
                content,
                encoding="utf-8",
            )

            lean_cmd = ["lake", "env", "lean", str(lean_path)]
            cmd = [*self.sandbox_command_prefix, *lean_cmd] if self.require_sandbox else lean_cmd
            result = self.runner.run_command(
                cmd,
                timeout=self.timeout,
            )
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=result.success,
                stderr=self._sanitize_stderr(result.stderr, tmp_dir),
                timed_out=result.timed_out,
            )

    def _contains_disallowed_content(self, statement: str, proof_script: str) -> bool:
        payload = f"{statement}\n{proof_script}"
        return any(pattern.search(payload) for pattern in self._disallowed_patterns)

    def _sanitize_stderr(self, stderr: str, tmp_dir: str) -> str:
        redacted = stderr.replace(tmp_dir, "<tmpdir>")
        if len(redacted) <= self.max_stderr_chars:
            return redacted
        return redacted[: self.max_stderr_chars] + "...<truncated>"

    def _sandbox_available(self) -> bool:
        if not self.sandbox_command_prefix:
            return False
        return shutil.which(self.sandbox_command_prefix[0]) is not None

    def _is_supported_input_shape(self, statement: str, proof_script: str) -> bool:
        return bool(self._statement_pattern.match(statement)) and bool(
            self._proof_pattern.match(proof_script)
        )
