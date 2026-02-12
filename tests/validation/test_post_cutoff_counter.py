"""Tests for post-cutoff theorem counting logic."""

from __future__ import annotations

from autonomous_discovery.knowledge_base.parser import DeclarationEntry
from autonomous_discovery.validation.post_cutoff_counter import filter_algebra_theorems


def test_filters_only_algebra_theorems() -> None:
    declarations = [
        DeclarationEntry(kind="theorem", name="Algebra.foo", type_signature="T"),
        DeclarationEntry(kind="theorem", name="Ring.bar", type_signature="T"),
        DeclarationEntry(kind="definition", name="Algebra.baz", type_signature="T"),
        DeclarationEntry(kind="theorem", name="Nat.succ_pos", type_signature="T"),
        DeclarationEntry(kind="theorem", name="Group.mul_one", type_signature="T"),
    ]
    result = filter_algebra_theorems(declarations, ("Algebra.", "Ring.", "Group."))
    assert [d.name for d in result] == ["Algebra.foo", "Ring.bar", "Group.mul_one"]


def test_empty_declarations_returns_empty() -> None:
    result = filter_algebra_theorems([], ("Algebra.",))
    assert result == []


def test_no_matching_prefix_returns_empty() -> None:
    declarations = [
        DeclarationEntry(kind="theorem", name="Nat.succ", type_signature="T"),
    ]
    result = filter_algebra_theorems(declarations, ("Algebra.", "Ring."))
    assert result == []


def test_excludes_non_theorem_kinds() -> None:
    declarations = [
        DeclarationEntry(kind="definition", name="Ring.foo", type_signature="T"),
        DeclarationEntry(kind="inductive", name="Ring.bar", type_signature="T"),
        DeclarationEntry(kind="instance", name="Ring.baz", type_signature="T"),
    ]
    result = filter_algebra_theorems(declarations, ("Ring.",))
    assert result == []
