import json
from pathlib import Path

import pytest

from autonomous_discovery.gap_detector.cli import main


@pytest.mark.integration
def test_gap_detector_cli_smoke(tmp_path: Path) -> None:
    premises_path = tmp_path / "premises.txt"
    decl_types_path = tmp_path / "decl_types.txt"
    output_path = tmp_path / "gap_candidates.jsonl"

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
            "--output-path",
            str(output_path),
            "--top-k",
            "5",
        ]
    )

    assert code == 0
    assert output_path.exists()
    records = [json.loads(line) for line in output_path.read_text().splitlines() if line]
    assert records
    assert any(r["missing_decl"] == "Ring.one_mul" for r in records)


def test_gap_detector_cli_reports_missing_input(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "--premises-path",
            "does-not-exist-premises.txt",
            "--decl-types-path",
            "does-not-exist-decls.txt",
        ]
    )
    captured = capsys.readouterr()
    assert code != 0
    assert "not found" in captured.err.lower()
