from autonomous_discovery.gap_detector.seeds import scan_seed_annotations


def test_scan_seed_annotations_finds_todo_and_sorry(tmp_path) -> None:
    lean_file = tmp_path / "Mathlib" / "Algebra" / "Sample.lean"
    lean_file.parent.mkdir(parents=True)
    lean_file.write_text(
        """\
theorem foo : True := by
  -- TODO: strengthen hypothesis
  sorry

def bar : Nat := by
  -- keep this note
  exact 0
"""
    )

    hints = scan_seed_annotations([lean_file])

    assert len(hints) == 2
    kinds = {hint.kind for hint in hints}
    assert kinds == {"todo", "sorry"}

    todo = next(h for h in hints if h.kind == "todo")
    assert "strengthen hypothesis" in todo.content


def test_scan_seed_annotations_ignores_todo_substring_inside_identifier(tmp_path) -> None:
    lean_file = tmp_path / "Mathlib" / "Algebra" / "Identifier.lean"
    lean_file.parent.mkdir(parents=True)
    lean_file.write_text(
        """\
def pseudoTopologicalGroupTodoCounter : Nat := 1
def done : Nat := 2
"""
    )

    hints = scan_seed_annotations([lean_file])
    assert hints == []
