"""TDD tests for LeanRunner (Python→Lean subprocess bridge)."""

from unittest.mock import patch

import pytest

from autonomous_discovery.lean_bridge.runner import LeanResult, LeanRunner


class TestLeanResult:
    def test_dataclass_fields(self) -> None:
        result = LeanResult(stdout="ok", stderr="", returncode=0, timed_out=False)
        assert result.stdout == "ok"
        assert result.returncode == 0
        assert result.timed_out is False

    def test_success_property(self) -> None:
        ok = LeanResult(stdout="", stderr="", returncode=0, timed_out=False)
        assert ok.success is True

        fail = LeanResult(stdout="", stderr="error", returncode=1, timed_out=False)
        assert fail.success is False

        timeout = LeanResult(stdout="", stderr="", returncode=0, timed_out=True)
        assert timeout.success is False


class TestLeanRunnerUnit:
    """Unit tests that mock subprocess — no Lean installation required."""

    def test_check_lean_available_true(self) -> None:
        runner = LeanRunner()
        with patch("autonomous_discovery.lean_bridge.runner.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "leanprover/lean4:v4.16.0"
            assert runner.check_lean_available() is True

    def test_check_lean_available_false(self) -> None:
        runner = LeanRunner()
        with patch(
            "autonomous_discovery.lean_bridge.runner.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            assert runner.check_lean_available() is False

    def test_run_command_success(self) -> None:
        runner = LeanRunner()
        with patch("autonomous_discovery.lean_bridge.runner.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "#check Nat.add_comm : ok"
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0
            result = runner.run_command(["lean", "--run", "test.lean"])
            assert result.success is True
            assert "Nat.add_comm" in result.stdout

    def test_run_command_timeout(self) -> None:
        import subprocess

        runner = LeanRunner(timeout=1)
        with patch(
            "autonomous_discovery.lean_bridge.runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="lean", timeout=1),
        ):
            result = runner.run_command(["lean", "--run", "test.lean"])
            assert result.timed_out is True
            assert result.success is False

    def test_run_command_missing_executable(self) -> None:
        runner = LeanRunner()
        with patch(
            "autonomous_discovery.lean_bridge.runner.subprocess.run",
            side_effect=FileNotFoundError("No such file: 'nonexistent'"),
        ):
            result = runner.run_command(["nonexistent"])
            assert result.success is False
            assert not result.timed_out
            assert "No such file" in result.stderr

    def test_run_command_error(self) -> None:
        runner = LeanRunner()
        with patch("autonomous_discovery.lean_bridge.runner.subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "unknown identifier 'foo'"
            mock_run.return_value.returncode = 1
            result = runner.run_command(["lean", "--run", "test.lean"])
            assert result.success is False
            assert "unknown identifier" in result.stderr

    def test_run_lake_delegates_to_run_command(self) -> None:
        runner = LeanRunner(project_dir="/tmp/fake")
        with patch.object(runner, "run_command") as mock_cmd:
            mock_cmd.return_value = LeanResult("", "", 0, False)
            result = runner.run_lake("build")
            assert result.success is True
            # Verify lake was called with project_dir as cwd
            call_args = mock_cmd.call_args
            assert call_args[0][0] == ["lake", "build"]
            assert call_args[1].get("cwd") == "/tmp/fake"

    def test_default_timeout(self) -> None:
        runner = LeanRunner()
        assert runner.timeout == 300  # 5 minutes default

    def test_custom_timeout(self) -> None:
        runner = LeanRunner(timeout=60)
        assert runner.timeout == 60


# --- Integration tests (require Lean installed) ---


@pytest.mark.integration
class TestLeanRunnerIntegration:
    def test_lean_version_check(self) -> None:
        runner = LeanRunner()
        assert runner.check_lean_available() is True

    def test_lean_eval(self) -> None:
        runner = LeanRunner()
        result = runner.run_command(["lean", "--version"])
        assert result.success is True
        assert "leanprover" in result.stdout.lower() or "lean" in result.stdout.lower()
