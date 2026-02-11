import json
from pathlib import Path

import pytest

from autonomous_discovery.pipeline.phase2 import run_phase2_cycle


@pytest.mark.integration
def test_phase2_cycle_smoke_writes_artifacts(tmp_path: Path) -> None:
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

    summary = run_phase2_cycle(
        premises_path=premises_path,
        decl_types_path=decl_types_path,
        output_dir=output_dir,
        top_k=5,
    )

    metrics_path = output_dir / "phase2_cycle_metrics.json"
    attempts_path = output_dir / "phase2_attempts.jsonl"

    assert metrics_path.exists()
    assert attempts_path.exists()
    assert summary["gap_count"] >= 1
    assert summary["conjecture_count"] >= 1
    assert summary["verification_success_count"] >= 0
    assert 0.0 <= summary["success_rate"] <= 1.0

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["artifacts"]["attempts_path"] == str(attempts_path)

    lines = [line for line in attempts_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    json.loads(lines[0])
