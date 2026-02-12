"""TDD tests for MathlibGraph (NetworkX DiGraph wrapper)."""

from pathlib import Path

import pytest

from autonomous_discovery.knowledge_base.graph import MathlibGraph
from autonomous_discovery.knowledge_base.parser import parse_declaration_types, parse_premises

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def premises():
    return parse_premises((FIXTURES / "sample_premises.txt").read_text())


@pytest.fixture
def declarations():
    return parse_declaration_types((FIXTURES / "sample_decl_types.txt").read_text())


@pytest.fixture
def graph(premises, declarations) -> MathlibGraph:
    return MathlibGraph.from_raw_data(premises, declarations)


class TestBuildGraph:
    def test_build_graph_from_premises(self, graph: MathlibGraph) -> None:
        # 3 declarations + their unique dependencies as nodes
        assert graph.node_count > 3
        assert graph.edge_count > 0

    def test_declaration_nodes_present(self, graph: MathlibGraph) -> None:
        assert graph.has_node("Nat.add_comm")
        assert graph.has_node("List.toFinset.ext_iff")
        assert graph.has_node("Group.inv_mul_cancel")

    def test_dependency_edges(self, graph: MathlibGraph) -> None:
        # Nat.add_comm depends on Nat.rec (explicit)
        assert graph.has_edge("Nat.add_comm", "Nat.rec")
        assert graph.has_edge("Nat.add_comm", "Nat.add_succ")

    def test_node_attributes(self, graph: MathlibGraph) -> None:
        attrs = graph.get_node_attrs("Nat.add_comm")
        assert attrs["kind"] == "theorem"
        assert "type_signature" in attrs
        assert "∀ (n m : Nat)" in attrs["type_signature"]

    def test_isolated_declarations_included(self) -> None:
        """Declarations with no premises should still appear as graph nodes."""
        from autonomous_discovery.knowledge_base.parser import DeclarationEntry, PremisesEntry

        premises = [PremisesEntry(name="A", dependencies=[])]
        declarations = [
            DeclarationEntry(kind="theorem", name="A", type_signature="A : Prop"),
            DeclarationEntry(kind="theorem", name="B", type_signature="B : Prop"),
        ]
        graph = MathlibGraph.from_raw_data(premises, declarations)
        assert graph.has_node("A")
        assert graph.has_node("B")  # B has no premises but should still be in graph
        assert graph.get_node_attrs("B")["kind"] == "theorem"

    def test_edge_attributes(self, graph: MathlibGraph) -> None:
        # Nat.add_comm -> Nat.rec is explicit
        edge_attrs = graph.get_edge_attrs("Nat.add_comm", "Nat.rec")
        assert edge_attrs["is_explicit"] is True
        assert edge_attrs["is_simp"] is False

        # List.toFinset.ext_iff -> List.mem_toFinset is simp
        edge_attrs = graph.get_edge_attrs("List.toFinset.ext_iff", "List.mem_toFinset")
        assert edge_attrs["is_simp"] is True
        assert edge_attrs["is_explicit"] is False


class TestFilterSubgraph:
    def test_filter_algebra_subgraph(self, premises, declarations) -> None:
        """Filter to Mathlib.Algebra.* prefix — fixture has Group.* which simulates algebra."""
        # Add a premises entry with algebra-like module prefix
        extra_premises_text = """\
---
Mathlib.Algebra.Group.Basic.mul_one
  * Group.mul
  One.one
---
Mathlib.Topology.Basic.continuous_id
  * TopologicalSpace
"""
        extra_premises = parse_premises(extra_premises_text)
        all_premises = list(premises) + extra_premises

        graph = MathlibGraph.from_raw_data(all_premises, declarations)
        subgraph = graph.filter_by_module_prefix("Mathlib.Algebra")

        assert subgraph.has_node("Mathlib.Algebra.Group.Basic.mul_one")
        assert not subgraph.has_node("Mathlib.Topology.Basic.continuous_id")

    def test_filter_empty_prefix(self, graph: MathlibGraph) -> None:
        subgraph = graph.filter_by_module_prefix("NonExistent.Module")
        assert subgraph.node_count == 0

    def test_filter_by_name_prefixes(self, graph: MathlibGraph) -> None:
        """Filter by declaration name prefixes (how real Mathlib names work)."""
        subgraph = graph.filter_by_name_prefixes(["Group.", "Nat."])
        assert subgraph.has_node("Nat.add_comm")
        assert subgraph.has_node("Group.inv_mul_cancel")
        assert not subgraph.has_node("List.toFinset.ext_iff")

    def test_filter_by_name_prefixes_empty(self, graph: MathlibGraph) -> None:
        subgraph = graph.filter_by_name_prefixes(["ZZZ."])
        assert subgraph.node_count == 0


class TestGraphStatistics:
    def test_statistics_keys(self, graph: MathlibGraph) -> None:
        stats = graph.get_statistics()
        assert "node_count" in stats
        assert "edge_count" in stats
        assert "density" in stats
        assert stats["node_count"] == graph.node_count
        assert stats["edge_count"] == graph.edge_count

    def test_descendants_count(self, graph: MathlibGraph) -> None:
        # Leaf dependency nodes should have 0 descendants
        count = graph.descendants_count("Nat.add_succ")
        assert count == 0

    def test_pagerank_runs(self, graph: MathlibGraph) -> None:
        pr = graph.pagerank()
        assert isinstance(pr, dict)
        assert len(pr) > 0
        # All values should be positive floats
        assert all(v > 0 for v in pr.values())

    def test_type_signature_of_returns_signature(self, graph: MathlibGraph) -> None:
        sig = graph.type_signature_of("Nat.add_comm")
        assert sig is not None
        assert "∀ (n m : Nat)" in sig

    def test_type_signature_of_missing_node(self, graph: MathlibGraph) -> None:
        assert graph.type_signature_of("NonExistent.Decl") is None

    def test_type_signature_of_node_without_signature(self) -> None:
        """Dependency-only nodes may lack a type_signature attribute."""
        import networkx as nx

        g = nx.DiGraph()
        g.add_node("bare_node")  # no type_signature attr
        graph = MathlibGraph(g)
        assert graph.type_signature_of("bare_node") is None
