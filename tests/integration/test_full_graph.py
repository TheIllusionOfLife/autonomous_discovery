"""Integration tests: load full Mathlib graph from real lean-training-data output."""

import pytest

from autonomous_discovery.config import ProjectConfig
from autonomous_discovery.knowledge_base.graph import MathlibGraph
from autonomous_discovery.knowledge_base.parser import parse_declaration_types, parse_premises


@pytest.mark.integration
class TestFullGraph:
    @pytest.fixture
    def config(self) -> ProjectConfig:
        return ProjectConfig()

    @pytest.fixture
    def full_graph(self, config: ProjectConfig) -> MathlibGraph:
        premises_text = config.premises_path.read_text()
        decl_types_text = config.decl_types_path.read_text()
        premises = parse_premises(premises_text)
        declarations = parse_declaration_types(decl_types_text)
        return MathlibGraph.from_raw_data(premises, declarations)

    def test_graph_scale(self, full_graph: MathlibGraph) -> None:
        """Full Mathlib graph should have >150K nodes, >500K edges."""
        stats = full_graph.get_statistics()
        print(f"\nFull graph: {stats}")
        assert stats["node_count"] > 150_000, f"Expected >150K nodes, got {stats['node_count']}"
        assert stats["edge_count"] > 500_000, f"Expected >500K edges, got {stats['edge_count']}"

    def test_algebra_subgraph(self, full_graph: MathlibGraph, config: ProjectConfig) -> None:
        """Algebra subgraph should have substantial size."""
        algebra = full_graph.filter_by_name_prefixes(list(config.algebra_name_prefixes))
        stats = algebra.get_statistics()
        print(f"\nAlgebra subgraph: {stats}")
        assert stats["node_count"] > 1000, f"Expected >1K algebra nodes, got {stats['node_count']}"


@pytest.mark.integration
class TestPostCutoffCount:
    """Critical early gate: count post-2024-08 algebra theorems in Mathlib."""

    def test_post_cutoff_algebra_theorem_count(self) -> None:
        """Verify sufficient post-cutoff algebra theorems exist for the experiment.

        This test requires the Mathlib4 git repo to be available at
        lean/LeanExtract/.lake/packages/mathlib/. It counts commits
        touching Mathlib/Algebra/ since the cutoff date.

        Threshold: >=30 theorems (per project spec go/no-go criteria).
        """
        import subprocess

        config = ProjectConfig()
        mathlib_dir = config.lean_project_dir / ".lake" / "packages" / "mathlib"

        if not mathlib_dir.exists():
            pytest.skip(f"Mathlib repo not found at {mathlib_dir}")

        # Count commits touching algebra files since cutoff
        result = subprocess.run(
            [
                "git",
                "log",
                f"--since={config.cutoff_date.isoformat()}",
                "--oneline",
                "--",
                "Mathlib/Algebra/",
            ],
            capture_output=True,
            text=True,
            cwd=mathlib_dir,
        )

        commit_count = len([line for line in result.stdout.strip().split("\n") if line])
        print(f"\nPost-cutoff algebra commits: {commit_count}")
        print(f"Threshold: >= {config.min_post_cutoff_theorems}")

        if commit_count < config.min_post_cutoff_theorems:
            pytest.fail(
                f"EARLY GATE FAILURE: Only {commit_count} post-cutoff algebra commits "
                f"(need >= {config.min_post_cutoff_theorems}). "
                f"Consider expanding domain or adjusting cutoff date."
            )
