"""Integration tests: load full Mathlib graph from real lean-training-data output."""

import shutil
import subprocess

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
        if not config.premises_path.exists():
            pytest.skip(f"Data file not found: {config.premises_path}")
        if not config.decl_types_path.exists():
            pytest.skip(f"Data file not found: {config.decl_types_path}")
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

    def test_post_cutoff_algebra_activity(self) -> None:
        """Verify sufficient post-cutoff algebra development activity in Mathlib.

        This is a coarse proxy: counts git commits touching Mathlib/Algebra/
        since the cutoff date. A commit may add, modify, or remove multiple
        theorems, so this is a lower bound on activity, not an exact theorem count.

        A more precise count (diffing declaration names) is deferred to the
        gap detector module where we compare declaration sets across versions.

        Threshold: >=30 commits (proxy for spec's go/no-go theorem threshold).
        """
        if not shutil.which("git"):
            pytest.skip("git not found on PATH")

        config = ProjectConfig()
        mathlib_dir = config.lean_project_dir / ".lake" / "packages" / "mathlib"

        if not mathlib_dir.exists():
            pytest.skip(f"Mathlib repo not found at {mathlib_dir}")

        # Count commits touching algebra files since cutoff
        try:
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
                timeout=30,
                check=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            pytest.fail(f"git log failed: {e}")

        commit_count = len([line for line in result.stdout.strip().split("\n") if line])
        print(f"\nPost-cutoff algebra commits (proxy for activity): {commit_count}")
        print(f"Threshold: >= {config.min_post_cutoff_theorems} commits")

        if commit_count < config.min_post_cutoff_theorems:
            pytest.fail(
                f"EARLY GATE WARNING: Only {commit_count} post-cutoff algebra commits "
                f"(need >= {config.min_post_cutoff_theorems}). "
                f"Consider expanding domain or adjusting cutoff date."
            )
