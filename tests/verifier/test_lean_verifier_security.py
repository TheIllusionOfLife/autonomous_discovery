from autonomous_discovery.lean_bridge.runner import LeanResult
from autonomous_discovery.verifier.lean_verifier import LeanVerifier


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def check_lean_available(self) -> bool:
        return True

    def run_command(
        self, cmd: list[str], *, timeout: int | None = None, cwd: str | None = None
    ) -> LeanResult:
        self.commands.append(cmd)
        return LeanResult(stdout="", stderr="", returncode=0, timed_out=False)


def test_verifier_blocks_unsafe_lean_directives() -> None:
    verifier = LeanVerifier(runner=FakeRunner(), require_sandbox=False)

    result = verifier.verify("theorem T : True", 'by\n  run_cmd IO.println "x"')

    assert result.success is False
    assert "unsafe" in result.stderr.lower()


def test_verifier_truncates_stderr_payload() -> None:
    class NoisyRunner(FakeRunner):
        def run_command(
            self, cmd: list[str], *, timeout: int | None = None, cwd: str | None = None
        ) -> LeanResult:
            _ = (cmd, timeout, cwd)
            return LeanResult(stdout="", stderr="x" * 5000, returncode=1, timed_out=False)

    verifier = LeanVerifier(runner=NoisyRunner(), max_stderr_chars=200, require_sandbox=False)
    result = verifier.verify("theorem T : True", "by\n  trivial")

    assert result.success is False
    assert len(result.stderr) <= 220


def test_verifier_allows_identifiers_containing_io_substring() -> None:
    verifier = LeanVerifier(runner=FakeRunner(), require_sandbox=False)

    result = verifier.verify("theorem AIOfoo : True", "by\n  trivial")

    assert result.success is True


def test_verifier_requires_sandbox_runtime_by_default() -> None:
    verifier = LeanVerifier(
        runner=FakeRunner(),
        require_sandbox=True,
        sandbox_command_prefix=("definitely-not-installed-sandbox",),
    )

    result = verifier.verify("theorem T : True", "by\n  trivial")
    assert result.success is False
    assert "sandbox runtime is required" in result.stderr.lower()


def test_verifier_rejects_unsupported_statement_shape() -> None:
    verifier = LeanVerifier(runner=FakeRunner(), require_sandbox=False)
    result = verifier.verify("theorem X : Nat", "by\n  trivial")

    assert result.success is False
    assert "constrained theorem/proof shapes" in result.stderr.lower()
