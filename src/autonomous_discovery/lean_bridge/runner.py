"""LeanRunner: Python→Lean 4 subprocess bridge with timeout handling."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 300  # 5 minutes


@dataclass(frozen=True, slots=True)
class LeanResult:
    """Result of running a Lean/Lake command."""

    stdout: str
    stderr: str
    returncode: int
    timed_out: bool

    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out


class LeanRunner:
    """Subprocess bridge to Lean 4 and Lake build system."""

    def __init__(
        self,
        project_dir: str | Path | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.project_dir = str(project_dir) if project_dir else None
        self.timeout = timeout

    def check_lean_available(self) -> bool:
        """Check if `lean` is on PATH and responds."""
        try:
            result = subprocess.run(
                ["lean", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run_command(
        self,
        cmd: list[str],
        *,
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> LeanResult:
        """Run an arbitrary command and capture output."""
        effective_timeout = timeout if timeout is not None else self.timeout
        effective_cwd = cwd if cwd is not None else self.project_dir
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=effective_cwd,
            )
            return LeanResult(
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as e:
            return LeanResult(
                stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
                stderr=e.stderr or "" if isinstance(e.stderr, str) else "",
                returncode=-1,
                timed_out=True,
            )
        except (FileNotFoundError, OSError) as e:
            return LeanResult(stdout="", stderr=str(e), returncode=-1, timed_out=False)

    def run_lake(self, *args: str, timeout: int | None = None) -> LeanResult:
        """Run a `lake` command in the project directory."""
        return self.run_command(["lake", *args], timeout=timeout, cwd=self.project_dir)
