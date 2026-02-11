import json
import shutil
from pathlib import Path

import pytest

from autonomous_discovery.phase2_cli import main


@pytest.mark.integration
def test_phase2_cli_smoke(tmp_path: Path) -> None:
    premises_path = tmp_path / "premises.txt"
    decl_types_path = tmp_path / "decl_types.txt"
    output_dir = tmp_path / "processed"

    premises_path.write_text(
        """\
---
Group.one_mul
  * Group.one
---
Ring.one
  * OfNat.ofNat
"""
    )
    decl_types_path.write_text(
        """\
---
theorem
Group.one_mul
Group.one_mul : Prop
---
theorem
Group.one
Group.one : Prop
---
theorem
Ring.one
Ring.one : Prop
---
theorem
OfNat.ofNat
OfNat.ofNat : Prop
"""
    )

    code = main(
        [
            "--premises-path",
            str(premises_path),
            "--decl-types-path",
            str(decl_types_path),
            "--output-dir",
            str(output_dir),
            "--top-k",
            "5",
            "--trusted-local-run",
            "--i-understand-unsafe",
        ]
    )

    assert code == 0
    metrics_path = output_dir / "phase2_cycle_metrics.json"
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "success_rate" in metrics


def test_phase2_cli_reports_missing_input(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        ["--premises-path", "missing-premises.txt", "--decl-types-path", "missing-decls.txt"]
    )

    captured = capsys.readouterr()
    assert code == 1
    assert "not found" in captured.err.lower()


@pytest.mark.integration
def test_phase2_cli_secure_mode_reports_missing_sandbox(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    premises_path = tmp_path / "premises.txt"
    decl_types_path = tmp_path / "decl_types.txt"
    output_dir = tmp_path / "processed"

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

    code = main(
        [
            "--premises-path",
            str(premises_path),
            "--decl-types-path",
            str(decl_types_path),
            "--output-dir",
            str(output_dir),
            "--sandbox-command-prefix",
            "definitely-not-installed-sandbox",
        ]
    )

    captured = capsys.readouterr()
    assert code == 1
    if shutil.which("lean"):
        assert "sandbox runtime is required" in captured.err.lower()
    else:
        assert "lean executable is not available" in captured.err.lower()


@pytest.mark.integration
def test_phase2_cli_trusted_local_run_allows_missing_sandbox(tmp_path: Path) -> None:
    premises_path = tmp_path / "premises.txt"
    decl_types_path = tmp_path / "decl_types.txt"
    output_dir = tmp_path / "processed"

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

    code = main(
        [
            "--premises-path",
            str(premises_path),
            "--decl-types-path",
            str(decl_types_path),
            "--output-dir",
            str(output_dir),
            "--trusted-local-run",
            "--i-understand-unsafe",
            "--sandbox-command-prefix",
            "definitely-not-installed-sandbox",
        ]
    )

    if shutil.which("lean"):
        assert code == 0
    else:
        assert code == 1


@pytest.mark.integration
def test_phase2_cli_trusted_local_run_requires_explicit_ack(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    premises_path = tmp_path / "premises.txt"
    decl_types_path = tmp_path / "decl_types.txt"
    output_dir = tmp_path / "processed"

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

    code = main(
        [
            "--premises-path",
            str(premises_path),
            "--decl-types-path",
            str(decl_types_path),
            "--output-dir",
            str(output_dir),
            "--trusted-local-run",
        ]
    )

    captured = capsys.readouterr()
    assert code == 1
    assert "i-understand-unsafe" in captured.err
