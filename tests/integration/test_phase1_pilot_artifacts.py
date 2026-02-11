import csv
import json
from pathlib import Path

import pytest

from autonomous_discovery.gap_detector.evaluate_cli import main as evaluate_main
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
    labels_path = output_dir / "top5_label_template.csv"
    metrics_path = output_dir / "phase1_metrics.json"

    assert summary["candidate_count"] >= 1
    assert candidates_path.exists()
    assert labels_path.exists()
    assert metrics_path.exists()
    lines = [line for line in candidates_path.read_text().splitlines() if line.strip()]
    assert lines
    for line in lines:
        json.loads(line)

    with metrics_path.open() as f:
        metrics = json.load(f)
    assert "candidate_count" in metrics
    assert "top_k" in metrics
    assert "topk_precision" in metrics
    assert "detection_rate" in metrics
    assert "non_trivial_count" in metrics
    assert metrics["go_no_go_status"] == "pending"

    with labels_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert {"missing_decl", "source_decl", "target_family", "label_non_trivial", "notes"} <= set(
        rows[0].keys()
    )

    rows[0]["label_non_trivial"] = "yes"
    with labels_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    code = evaluate_main(
        [
            "--metrics-path",
            str(metrics_path),
            "--labels-csv",
            str(labels_path),
            "--top-k",
            "5",
        ]
    )
    assert code == 0

    updated = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "top20_precision" not in updated
    assert updated["topk_precision"] > 0.0
    assert updated["detection_rate"] > 0.0
    assert updated["non_trivial_count"] >= 1
    assert updated["go_no_go_status"] in {"go", "no_go"}
