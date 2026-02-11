from autonomous_discovery.lean_bridge.runner import LeanResult
from autonomous_discovery.verifier.lean_verifier import LeanVerifier


class FakeRunner:
    def __init__(self, *, available: bool, result: LeanResult) -> None:
        self.available = available
        self.result = result
        self.commands: list[list[str]] = []

    def check_lean_available(self) -> bool:
        return self.available

    def run_command(
        self, cmd: list[str], *, timeout: int | None = None, cwd: str | None = None
    ) -> LeanResult:
        self.commands.append(cmd)
        return self.result


def test_lean_verifier_returns_unavailable_result_when_lean_missing() -> None:
    verifier = LeanVerifier(
        runner=FakeRunner(available=False, result=LeanResult("", "", 0, False))
    )

    result = verifier.verify("theorem T : True", "by\n  trivial")

    assert result.success is False
    assert "not available" in result.stderr.lower()


def test_lean_verifier_executes_runner_and_maps_success() -> None:
    runner = FakeRunner(available=True, result=LeanResult("", "", 0, False))
    verifier = LeanVerifier(runner=runner)

    result = verifier.verify("theorem T : True", "by\n  trivial")

    assert result.success is True
    assert runner.commands
    assert runner.commands[0][0] == "lean"
