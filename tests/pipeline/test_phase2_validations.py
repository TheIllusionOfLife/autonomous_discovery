from pathlib import Path

import pytest

from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.lean_bridge.runner import LeanRunner
from autonomous_discovery.pipeline.phase2 import run_phase2_cycle
from autonomous_discovery.proof_engine.models import ProofAttempt
from autonomous_discovery.verifier.models import VerificationResult


def _write_minimal_data(tmp_path: Path) -> tuple[Path, Path]:
    premises_path = tmp_path / "premises.txt"
    decl_types_path = tmp_path / "decl_types.txt"
    premises_path.write_text("---\nGroup.one_mul\n  * Group.one\n", encoding="utf-8")
    decl_types_path.write_text(
        (
            "---\n"
            "theorem\n"
            "Group.one_mul\n"
            "Group.one_mul : Prop\n"
            "---\n"
            "theorem\n"
            "Group.one\n"
            "Group.one : Prop\n"
        ),
        encoding="utf-8",
    )
    return premises_path, decl_types_path


def test_phase2_rejects_non_positive_top_k(tmp_path: Path) -> None:
    premises_path, decl_types_path = _write_minimal_data(tmp_path)

    with pytest.raises(ValueError, match="top_k"):
        run_phase2_cycle(
            premises_path=premises_path,
            decl_types_path=decl_types_path,
            output_dir=tmp_path / "out",
            top_k=0,
        )


def test_phase2_rejects_non_positive_retry_budget(tmp_path: Path) -> None:
    premises_path, decl_types_path = _write_minimal_data(tmp_path)

    with pytest.raises(ValueError, match="proof_retry_budget"):
        run_phase2_cycle(
            premises_path=premises_path,
            decl_types_path=decl_types_path,
            output_dir=tmp_path / "out",
            proof_retry_budget=0,
        )


def test_phase2_emits_observability_fields_and_cache_signal(tmp_path: Path) -> None:
    premises_path, decl_types_path = _write_minimal_data(tmp_path)
    output_dir = tmp_path / "out"

    first = run_phase2_cycle(
        premises_path=premises_path,
        decl_types_path=decl_types_path,
        output_dir=output_dir,
        top_k=1,
    )
    second = run_phase2_cycle(
        premises_path=premises_path,
        decl_types_path=decl_types_path,
        output_dir=output_dir,
        top_k=1,
    )

    assert "cycle_duration_ms" in first
    assert "verifier_available" in first
    assert "failure_counts" in first
    assert second["graph_cache_hit"] is True


def test_phase2_builds_default_verifier_with_project_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    premises_path, decl_types_path = _write_minimal_data(tmp_path)
    output_dir = tmp_path / "out"
    captured: dict[str, str | None] = {"project_dir": None}

    class FakeVerifier:
        def __init__(self, runner: LeanRunner) -> None:
            captured["project_dir"] = runner.project_dir

        def is_available(self) -> bool:
            return False

        def verify(self, statement: str, proof_script: str) -> VerificationResult:
            return VerificationResult(
                statement=statement,
                proof_script=proof_script,
                success=False,
                stderr="Lean executable is not available on PATH.",
                timed_out=False,
            )

    monkeypatch.setattr("autonomous_discovery.pipeline.phase2.LeanVerifier", FakeVerifier)
    run_phase2_cycle(
        premises_path=premises_path,
        decl_types_path=decl_types_path,
        output_dir=output_dir,
        top_k=1,
    )
    assert captured["project_dir"] is not None


def test_graph_cache_is_bounded(tmp_path: Path) -> None:
    import autonomous_discovery.pipeline.phase2 as phase2

    phase2._GRAPH_CACHE.clear()

    for i in range(phase2._MAX_CACHE_SIZE + 2):
        run_dir = tmp_path / f"case_{i}"
        run_dir.mkdir(parents=True, exist_ok=True)
        premises_path, decl_types_path = _write_minimal_data(run_dir)
        out_dir = run_dir / "out"
        run_phase2_cycle(
            premises_path=premises_path,
            decl_types_path=decl_types_path,
            output_dir=out_dir,
            top_k=1,
        )

    assert len(phase2._GRAPH_CACHE) == phase2._MAX_CACHE_SIZE


def test_phase2_secure_mode_reports_runtime_not_ready(tmp_path: Path) -> None:
    premises_path, decl_types_path = _write_minimal_data(tmp_path)

    summary = run_phase2_cycle(
        premises_path=premises_path,
        decl_types_path=decl_types_path,
        output_dir=tmp_path / "out",
        top_k=1,
        sandbox_command_prefix=("definitely-not-installed-sandbox",),
    )

    assert summary["verification_mode"] == "sandboxed"
    assert summary["runtime_ready"] is False
    assert summary["skipped_reason"] is not None
    attempts_path = Path(summary["artifacts"]["attempts_path"])
    assert attempts_path.exists()
    assert attempts_path.read_text(encoding="utf-8") == ""


def test_phase2_trusted_mode_runs_without_sandbox(tmp_path: Path) -> None:
    premises_path, decl_types_path = _write_minimal_data(tmp_path)

    summary = run_phase2_cycle(
        premises_path=premises_path,
        decl_types_path=decl_types_path,
        output_dir=tmp_path / "out",
        top_k=1,
        trusted_local_run=True,
        sandbox_command_prefix=("definitely-not-installed-sandbox",),
    )

    assert summary["verification_mode"] == "trusted_local"
    assert summary["runtime_ready"] is True
    assert summary["skipped_reason"] is None


def test_phase2_applies_filter_and_novelty_metrics(tmp_path: Path) -> None:
    premises_path, decl_types_path = _write_minimal_data(tmp_path)

    class FakeGenerator:
        def generate(
            self, gaps: list[object], *, max_candidates: int
        ) -> list[ConjectureCandidate]:
            _ = (gaps, max_candidates)
            return [
                ConjectureCandidate(
                    gap_missing_decl="A",
                    lean_statement="theorem A : True",
                    rationale="a",
                    model_id="m",
                    temperature=0.0,
                ),
                ConjectureCandidate(
                    gap_missing_decl="B",
                    lean_statement="theorem B : True",
                    rationale="b",
                    model_id="m",
                    temperature=0.0,
                ),
            ]

    class FakeFilter:
        def evaluate(self, conjecture: ConjectureCandidate) -> object:
            class Decision:
                def __init__(self, accepted: bool, reason: str) -> None:
                    self.accepted = accepted
                    self.reason = reason

            if conjecture.gap_missing_decl == "B":
                return Decision(False, "rejected_in_test")
            return Decision(True, "ok")

    class FakeNoveltyChecker:
        def is_novel(self, statement: str) -> object:
            class Decision:
                def __init__(self, is_novel: bool, reason: str) -> None:
                    self.is_novel = is_novel
                    self.reason = reason

            if statement == "theorem A : True":
                return Decision(False, "exact_duplicate")
            return Decision(True, "novel")

    class FakeProofEngine:
        def build_attempts(
            self, conjecture: ConjectureCandidate, *, max_attempts: int = 3
        ) -> list[ProofAttempt]:
            _ = max_attempts
            return [
                ProofAttempt(
                    statement=conjecture.lean_statement,
                    proof_script="by\n  trivial",
                    engine="fake",
                    attempt_index=1,
                )
            ]

    class FakeVerifier:
        def is_available(self) -> bool:
            return True

        def runtime_status(self) -> dict[str, bool]:
            return {"lean_available": True, "sandbox_available": True, "runtime_ready": True}

        def verify(self, statement: str, proof_script: str) -> VerificationResult:
            _ = (statement, proof_script)
            return VerificationResult(
                statement="theorem T : True",
                proof_script="by\n  trivial",
                success=True,
                stderr="",
                timed_out=False,
            )

    summary = run_phase2_cycle(
        premises_path=premises_path,
        decl_types_path=decl_types_path,
        output_dir=tmp_path / "out",
        top_k=2,
        trusted_local_run=True,
        generator=FakeGenerator(),
        conjecture_filter=FakeFilter(),
        novelty_checker=FakeNoveltyChecker(),
        proof_engine=FakeProofEngine(),
        verifier=FakeVerifier(),
    )

    assert summary["conjecture_count"] == 2
    assert summary["filtered_out_count"] == 1
    assert summary["filter_pass_count"] == 1
    assert summary["duplicate_count"] == 1
    assert summary["novel_count"] == 0
