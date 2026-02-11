import json

from autonomous_discovery.gap_detector.analogical import GapCandidate
from autonomous_discovery.gap_detector.report import read_gap_report, write_gap_report


def test_write_and_read_gap_report_roundtrip(tmp_path) -> None:
    candidates = [
        GapCandidate(
            source_decl="Group.one_mul",
            target_family="Ring.",
            missing_decl="Ring.one_mul",
            score=0.75,
            signals={"dependency_overlap": 0.5, "source_pagerank": 0.2},
        ),
        GapCandidate(
            source_decl="Ring.zero_mul",
            target_family="Module.",
            missing_decl="Module.zero_smul",
            score=0.66,
            signals={"dependency_overlap": 0.4, "source_pagerank": 0.1},
        ),
    ]
    out_path = tmp_path / "gap_candidates.jsonl"

    write_gap_report(candidates, out_path)

    lines = out_path.read_text().strip().splitlines()
    assert len(lines) == 2
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["missing_decl"] == "Ring.one_mul"

    loaded = read_gap_report(out_path)
    assert loaded == candidates
