from pathlib import Path

import pytest

from autonomous_discovery.conjecture_generator.io import read_conjectures


def test_read_conjectures_rejects_non_dict_metadata(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(
        (
            '{"gap_missing_decl":"X","lean_statement":"theorem X : Prop",'
            '"rationale":"r","model_id":"m","temperature":0.0,"metadata":[]}\n'
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="metadata"):
        read_conjectures(path)


def test_read_conjectures_rejects_missing_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"
    path.write_text(
        '{"gap_missing_decl":"X","rationale":"r","model_id":"m","temperature":0.0}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required field"):
        read_conjectures(path)


def test_read_conjectures_coerces_core_fields_to_strings(tmp_path: Path) -> None:
    path = tmp_path / "typed.jsonl"
    path.write_text(
        '{"gap_missing_decl":123,"lean_statement":456,"rationale":789,"model_id":0,"temperature":1.5,"metadata":{}}\n',
        encoding="utf-8",
    )

    [item] = read_conjectures(path)
    assert item.gap_missing_decl == "123"
    assert item.lean_statement == "456"
    assert item.rationale == "789"
    assert item.model_id == "0"
