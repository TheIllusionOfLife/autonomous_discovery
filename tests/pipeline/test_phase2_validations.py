from pathlib import Path

import pytest

from autonomous_discovery.pipeline.phase2 import run_phase2_cycle


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
