"""MathlibGraph: NetworkX DiGraph wrapper for Mathlib theorem dependencies."""

from __future__ import annotations

from typing import Any

import networkx as nx

from autonomous_discovery.knowledge_base.parser import DeclarationEntry, PremisesEntry


class MathlibGraph:
    """Wrapper around nx.DiGraph for Mathlib theorem dependency analysis.

    Nodes are declaration names. An edge from A to B means A depends on B.
    """

    def __init__(self, graph: nx.DiGraph) -> None:
        self._graph = graph

    @classmethod
    def from_raw_data(
        cls,
        premises: list[PremisesEntry],
        declarations: list[DeclarationEntry],
    ) -> MathlibGraph:
        """Build a graph from parsed premises and declaration_types data."""
        g = nx.DiGraph()

        # Index declarations by name for attribute lookup
        decl_index: dict[str, DeclarationEntry] = {d.name: d for d in declarations}

        # Add ALL declaration nodes first (including those with no premises)
        for decl in declarations:
            g.add_node(decl.name, kind=decl.kind, type_signature=decl.type_signature)

        # Add premise entries and edges
        for entry in premises:
            if not g.has_node(entry.name):
                node_attrs: dict[str, Any] = {}
                if entry.name in decl_index:
                    decl = decl_index[entry.name]
                    node_attrs["kind"] = decl.kind
                    node_attrs["type_signature"] = decl.type_signature
                g.add_node(entry.name, **node_attrs)

            # Add edges to dependencies
            for dep in entry.dependencies:
                if not g.has_node(dep.name):
                    g.add_node(dep.name)
                g.add_edge(entry.name, dep.name, is_explicit=dep.is_explicit, is_simp=dep.is_simp)

        return cls(g)

    # --- Query methods ---

    @property
    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    def has_node(self, name: str) -> bool:
        return self._graph.has_node(name)

    def has_edge(self, source: str, target: str) -> bool:
        return self._graph.has_edge(source, target)

    def get_node_attrs(self, name: str) -> dict[str, Any]:
        return dict(self._graph.nodes[name])

    def get_edge_attrs(self, source: str, target: str) -> dict[str, Any]:
        return dict(self._graph.edges[source, target])

    # --- Analysis methods ---

    def filter_by_module_prefix(self, prefix: str) -> MathlibGraph:
        """Return a new MathlibGraph containing only nodes matching the module prefix."""
        matching = [n for n in self._graph.nodes if n.startswith(prefix)]
        subgraph = self._graph.subgraph(matching).copy()
        return MathlibGraph(subgraph)

    def filter_by_name_prefixes(self, prefixes: list[str]) -> MathlibGraph:
        """Return a new MathlibGraph containing only nodes whose name starts with any prefix.

        Declaration names in Mathlib use short prefixes (e.g. 'Algebra.', 'Group.')
        rather than full module paths.
        """
        matching = [n for n in self._graph.nodes if any(n.startswith(p) for p in prefixes)]
        subgraph = self._graph.subgraph(matching).copy()
        return MathlibGraph(subgraph)

    def get_statistics(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "density": nx.density(self._graph),
        }

    def descendants_count(self, node: str) -> int:
        """Count transitive dependencies (descendants in the dependency graph)."""
        return len(nx.descendants(self._graph, node))

    def pagerank(self) -> dict[str, float]:
        return nx.pagerank(self._graph)
