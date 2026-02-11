from pathlib import Path

from autonomous_discovery.conjecture_generator.io import read_conjectures, write_conjectures
from autonomous_discovery.conjecture_generator.models import ConjectureCandidate


def test_write_and_read_conjectures_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "conjectures.jsonl"
    expected = [
        ConjectureCandidate(
            gap_missing_decl="Ring.one_mul",
            lean_statement="theorem Ring_one_mul : Prop",
            rationale="Analogy from Group.one_mul",
            model_id="template-v1",
            temperature=0.0,
            metadata={"source_decl": "Group.one_mul"},
        )
    ]

    write_conjectures(expected, path)
    actual = read_conjectures(path)

    assert actual == expected
