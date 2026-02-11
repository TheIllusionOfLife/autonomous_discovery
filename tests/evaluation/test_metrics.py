from autonomous_discovery.gap_detector.evaluation import (
    build_topk_label_template_rows,
    compute_detection_rate,
    compute_topk_precision,
)
from autonomous_discovery.gap_detector.report import read_gap_report, write_gap_report
from autonomous_discovery.gap_detector.analogical import GapCandidate


def test_compute_topk_precision() -> None:
    labels = [True, False, True, True]
    assert compute_topk_precision(labels) == 0.75
    assert compute_topk_precision([]) == 0.0


def test_compute_detection_rate() -> None:
    assert compute_detection_rate(non_trivial_count=4, total_candidates=20) == 0.2
    assert compute_detection_rate(non_trivial_count=0, total_candidates=0) == 0.0


def test_build_topk_label_template_rows() -> None:
    candidates = [
        GapCandidate(
            source_decl="Group.one_mul",
            target_family="Ring.",
            missing_decl="Ring.one_mul",
            score=0.5,
            signals={"dependency_overlap": 1.0},
        )
    ]
    rows = build_topk_label_template_rows(candidates)

    assert rows[0]["missing_decl"] == "Ring.one_mul"
    assert rows[0]["label_non_trivial"] == ""
    assert rows[0]["notes"] == ""


def test_report_roundtrip_from_evaluation_fixture(tmp_path) -> None:
    candidates = [
        GapCandidate(
            source_decl="A.x",
            target_family="B.",
            missing_decl="B.x",
            score=0.1,
            signals={"dependency_overlap": 0.0},
        )
    ]
    report_path = tmp_path / "gaps.jsonl"
    write_gap_report(candidates, report_path)
    loaded = read_gap_report(report_path)
    assert loaded == candidates
