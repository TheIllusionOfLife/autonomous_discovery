import csv
import json
from pathlib import Path

from autonomous_discovery.gap_detector.evaluate_cli import main


def _write_metrics(path: Path, top_k: int = 5) -> None:
    path.write_text(
        json.dumps(
            {
                "candidate_count": top_k,
                "top_k": top_k,
                "output_dir": str(path.parent),
                "candidates_path": str(path.parent / "gap_candidates.jsonl"),
                "labels_path": str(path.parent / f"top{top_k}_label_template.csv"),
                "metrics_path": str(path),
                "topk_precision": None,
                "detection_rate": None,
                "non_trivial_count": None,
                "go_no_go_status": "pending",
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_labels(path: Path, labels: list[str], source_decls: list[str] | None = None) -> None:
    fieldnames = [
        "missing_decl",
        "source_decl",
        "target_family",
        "score",
        "label_non_trivial",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, label in enumerate(labels, start=1):
            source_decl = (
                source_decls[idx - 1] if source_decls is not None else f"Group.M{idx}.gap_{idx}"
            )
            writer.writerow(
                {
                    "missing_decl": f"Ring.gap_{idx}",
                    "source_decl": source_decl,
                    "target_family": "Ring.",
                    "score": "0.5",
                    "label_non_trivial": label,
                    "notes": "",
                }
            )


def test_evaluate_cli_updates_metrics(tmp_path: Path) -> None:
    metrics_path = tmp_path / "phase1_metrics.json"
    labels_path = tmp_path / "top5_label_template.csv"
    _write_metrics(metrics_path, top_k=5)
    _write_labels(labels_path, labels=["yes", "1", "", "no", "false"])

    code = main(
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
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "top20_precision" not in metrics
    assert metrics["topk_precision"] == 0.4
    assert metrics["detection_rate"] == 0.4
    assert metrics["detection_rate_basis"] == "evaluated_module_proxy_rate"
    assert metrics["non_trivial_candidate_rate"] == 0.4
    assert metrics["non_trivial_count"] == 2
    assert metrics["evaluated_module_count"] == 5
    assert metrics["modules_with_non_trivial_gaps_count"] == 2
    assert metrics["go_no_go_status"] == "no_go"


def test_evaluate_cli_marks_go_when_primary_or_secondary_and_absolute_pass(tmp_path: Path) -> None:
    metrics_path = tmp_path / "phase1_metrics.json"
    labels_path = tmp_path / "top60_label_template.csv"
    _write_metrics(metrics_path, top_k=60)
    labels = ["yes"] * 40 + ["no"] * 20
    # Keep all positive labels in one module so detection_rate fails but precision passes.
    source_decls = (
        ["Group.Core.same_module"] * 24
        + ["Group.Core.same_module" for _ in range(16)]
        + [f"Group.M{i}.gap_{i}" for i in range(20)]
    )
    _write_labels(labels_path, labels=labels, source_decls=source_decls)

    code = main(
        [
            "--metrics-path",
            str(metrics_path),
            "--labels-csv",
            str(labels_path),
            "--top-k",
            "60",
        ]
    )
    assert code == 0
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["topk_precision"] == (40 / 60)
    assert metrics["non_trivial_count"] == 40
    assert metrics["detection_rate"] < 0.05
    assert metrics["go_no_go_checks"]["primary_detection_rate_ok"] is False
    assert metrics["go_no_go_checks"]["secondary_topk_precision_ok"] is True
    assert metrics["go_no_go_checks"]["minimum_non_trivial_count_ok"] is True
    assert metrics["go_no_go_status"] == "go"


def test_evaluate_cli_populates_top20_precision_for_top20_runs(tmp_path: Path) -> None:
    metrics_path = tmp_path / "phase1_metrics.json"
    labels_path = tmp_path / "top20_label_template.csv"
    _write_metrics(metrics_path, top_k=20)
    _write_labels(labels_path, labels=["yes"] * 20)

    code = main(
        [
            "--metrics-path",
            str(metrics_path),
            "--labels-csv",
            str(labels_path),
            "--top-k",
            "20",
        ]
    )
    assert code == 0
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["top20_precision"] == 1.0
    assert metrics["topk_precision"] == 1.0


def test_evaluate_cli_reports_invalid_metrics_json(tmp_path: Path, capsys) -> None:
    metrics_path = tmp_path / "phase1_metrics.json"
    labels_path = tmp_path / "top5_label_template.csv"
    metrics_path.write_text("{invalid json", encoding="utf-8")
    _write_labels(labels_path, labels=["yes"])

    code = main(
        [
            "--metrics-path",
            str(metrics_path),
            "--labels-csv",
            str(labels_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "invalid json" in captured.err.lower()


def test_evaluate_cli_reports_missing_required_csv_column(tmp_path: Path, capsys) -> None:
    metrics_path = tmp_path / "phase1_metrics.json"
    labels_path = tmp_path / "top5_label_template.csv"
    _write_metrics(metrics_path, top_k=5)
    labels_path.write_text(
        "missing_decl,source_decl,target_family,score,notes\n"
        "Ring.gap_1,Group.M1.gap_1,Ring.,0.5,\n",
        encoding="utf-8",
    )

    code = main(
        [
            "--metrics-path",
            str(metrics_path),
            "--labels-csv",
            str(labels_path),
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "label_non_trivial" in captured.err
