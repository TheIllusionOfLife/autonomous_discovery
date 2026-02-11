import json
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
        ]
    )

    assert code == 0
    metrics_path = output_dir / "phase2_cycle_metrics.json"
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "success_rate" in metrics


def test_phase2_cli_reports_missing_input(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--premises-path", "missing-premises.txt", "--decl-types-path", "missing-decls.txt"])

    captured = capsys.readouterr()
    assert code == 1
    assert "not found" in captured.err.lower()
