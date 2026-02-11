import csv
import json
from pathlib import Path

import pytest

from autonomous_discovery.gap_detector.pilot import run_phase1_pilot


@pytest.mark.integration
def test_phase1_pilot_writes_artifacts(tmp_path: Path) -> None:
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

    summary = run_phase1_pilot(
        premises_path=premises_path,
        decl_types_path=decl_types_path,
        output_dir=output_dir,
        top_k=5,
    )

    candidates_path = output_dir / "gap_candidates.jsonl"
    labels_path = output_dir / "top20_label_template.csv"
    metrics_path = output_dir / "phase1_metrics.json"

    assert summary["candidate_count"] >= 1
    assert candidates_path.exists()
    assert labels_path.exists()
    assert metrics_path.exists()

    with metrics_path.open() as f:
        metrics = json.load(f)
    assert "candidate_count" in metrics
    assert "top_k" in metrics

    with labels_path.open() as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert {"missing_decl", "source_decl", "target_family", "label_non_trivial", "notes"} <= set(
        rows[0].keys()
    )
