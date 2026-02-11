"""TDD tests for lean-training-data output parsers."""

from pathlib import Path

import pytest

from autonomous_discovery.knowledge_base.parser import (
    DeclarationEntry,
    Dependency,
    parse_declaration_types,
    parse_premises,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def premises_text() -> str:
    return (FIXTURES / "sample_premises.txt").read_text()


@pytest.fixture
def decl_types_text() -> str:
    return (FIXTURES / "sample_decl_types.txt").read_text()


# --- parse_premises tests ---


class TestParsePremises:
    def test_single_block(self) -> None:
        text = """\
---
Nat.add_comm
  * Nat.rec
  * Nat.add
  Nat.add_succ
  Nat.succ_add
"""
        result = parse_premises(text)
        assert len(result) == 1

        entry = result[0]
        assert entry.name == "Nat.add_comm"
        assert len(entry.dependencies) == 4

        explicit = [d for d in entry.dependencies if d.is_explicit]
        assert len(explicit) == 2
        assert {d.name for d in explicit} == {"Nat.rec", "Nat.add"}

    def test_multiple_blocks(self, premises_text: str) -> None:
        result = parse_premises(premises_text)
        assert len(result) == 3

        names = [e.name for e in result]
        assert names == [
            "List.toFinset.ext_iff",
            "Nat.add_comm",
            "Group.inv_mul_cancel",
        ]

    def test_simp_flag(self) -> None:
        text = """\
---
List.toFinset.ext_iff
s List.mem_toFinset
  * congrArg
"""
        result = parse_premises(text)
        assert len(result) == 1

        simp_deps = [d for d in result[0].dependencies if d.is_simp]
        assert len(simp_deps) == 1
        assert simp_deps[0].name == "List.mem_toFinset"

    def test_empty_input(self) -> None:
        assert parse_premises("") == []
        assert parse_premises("   \n\n  ") == []

    def test_dependency_dataclass(self) -> None:
        dep = Dependency(name="Nat.add", is_explicit=True, is_simp=False)
        assert dep.name == "Nat.add"
        assert dep.is_explicit is True
        assert dep.is_simp is False


# --- parse_declaration_types tests ---


class TestParseDeclarationTypes:
    def test_single_block(self) -> None:
        text = """\
---
theorem
Nat.add_comm
∀ (n m : Nat), n + m = m + n
"""
        result = parse_declaration_types(text)
        assert len(result) == 1

        entry = result[0]
        assert entry.kind == "theorem"
        assert entry.name == "Nat.add_comm"
        assert entry.type_signature == "∀ (n m : Nat), n + m = m + n"

    def test_multiple_blocks(self, decl_types_text: str) -> None:
        result = parse_declaration_types(decl_types_text)
        assert len(result) == 3

        assert result[0].kind == "theorem"
        assert result[0].name == "Nat.add_comm"

        assert result[1].kind == "definition"
        assert result[1].name == "List.toFinset"

        assert result[2].kind == "theorem"
        assert result[2].name == "TopologicalSpace.OpenNhds.map_id_obj"

    def test_multiline_signature(self, decl_types_text: str) -> None:
        result = parse_declaration_types(decl_types_text)
        # The third entry has a multi-line type signature
        sig = result[2].type_signature
        assert "TopologicalSpace.OpenNhds.map" in sig
        assert "\n" in sig  # Must preserve multi-line structure

    def test_empty_input(self) -> None:
        assert parse_declaration_types("") == []
        assert parse_declaration_types("   \n\n  ") == []

    def test_declaration_entry_dataclass(self) -> None:
        entry = DeclarationEntry(
            kind="theorem",
            name="Nat.add_comm",
            type_signature="∀ (n m : Nat), n + m = m + n",
        )
        assert entry.kind == "theorem"
