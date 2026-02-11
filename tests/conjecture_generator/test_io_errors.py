from pathlib import Path

import pytest

from autonomous_discovery.conjecture_generator.io import read_conjectures


def test_read_conjectures_rejects_non_dict_metadata(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(
        '{"gap_missing_decl":"X","lean_statement":"theorem X : Prop","rationale":"r","model_id":"m","temperature":0.0,"metadata":[]}'
        "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="metadata"):
        read_conjectures(path)
