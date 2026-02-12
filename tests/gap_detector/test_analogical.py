import networkx as nx

from autonomous_discovery.gap_detector.analogical import AnalogicalGapDetector, GapDetectorConfig
from autonomous_discovery.knowledge_base.graph import MathlibGraph
from autonomous_discovery.knowledge_base.parser import parse_declaration_types, parse_premises


def _build_graph() -> MathlibGraph:
    premises_text = """\
---
Group.mul_assoc
  * Group.mul
---
Ring.mul_assoc
  * Ring.mul
---
Group.one_mul
  * Group.one
  * HMul.hMul
---
Module.add_zero
  * Module.add
"""
    decl_text = """\
---
theorem
Group.mul_assoc
Group.mul_assoc : Prop
---
theorem
Ring.mul_assoc
Ring.mul_assoc : Prop
---
theorem
Group.one_mul
Group.one_mul : Prop
---
theorem
Module.add_zero
Module.add_zero : Prop
---
theorem
Group.mul
Group.mul : Prop
---
theorem
Ring.mul
Ring.mul : Prop
---
theorem
Group.one
Group.one : Prop
---
theorem
HMul.hMul
HMul.hMul : Prop
---
theorem
Module.add
Module.add : Prop
"""
    premises = parse_premises(premises_text)
    declarations = parse_declaration_types(decl_text)
    return MathlibGraph.from_raw_data(premises, declarations)


def test_detects_missing_analogical_counterpart() -> None:
    graph = _build_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
        )
    )

    gaps = detector.detect(graph)
    missing_names = {g.missing_decl for g in gaps}

    assert "Ring.one_mul" in missing_names


def test_respects_score_threshold() -> None:
    graph = _build_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
            min_score=1.01,
        )
    )
    assert detector.detect(graph) == []


def test_returns_ranked_results_with_expected_signals() -> None:
    graph = _build_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            top_k=2,
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
        )
    )
    gaps = detector.detect(graph)

    assert len(gaps) == 2
    assert gaps[0].score >= gaps[1].score
    assert "dependency_overlap" in gaps[0].signals
    assert "source_pagerank" in gaps[0].signals
    assert "source_descendants" in gaps[0].signals
    assert "cross_family_hits" in gaps[0].signals
    assert "cross_family_total" in gaps[0].signals
    assert "cross_family_overlap" in gaps[0].signals
    assert "namespace_stem_match" in gaps[0].signals


def test_filters_namespace_stem_mismatch_candidates() -> None:
    premises_text = """\
---
Module.Basis.subset_extend
  * Module.Basis.mk
---
Module.Basis.mk
  * Module.add
---
Group.mul_assoc
  * Group.mul
---
Group.mul
  * HMul.hMul
---
Ring.mul_assoc
  * Ring.mul
---
Ring.mul
  * HMul.hMul
---
Module.add
  * HAdd.hAdd
"""
    decl_text = """\
---
theorem
Module.Basis.subset_extend
Module.Basis.subset_extend : Prop
---
theorem
Module.Basis.mk
Module.Basis.mk : Prop
---
theorem
Group.mul_assoc
Group.mul_assoc : Prop
---
theorem
Group.mul
Group.mul : Prop
---
theorem
Ring.mul_assoc
Ring.mul_assoc : Prop
---
theorem
Ring.mul
Ring.mul : Prop
---
theorem
Module.add
Module.add : Prop
---
theorem
HMul.hMul
HMul.hMul : Prop
---
theorem
HAdd.hAdd
HAdd.hAdd : Prop
"""
    graph = MathlibGraph.from_raw_data(
        parse_premises(premises_text),
        parse_declaration_types(decl_text),
    )
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_cross_family_hits=1,
            min_cross_family_overlap=0.0,
            require_namespace_stem_match=True,
            min_score=0.0,
        )
    )

    gaps = detector.detect(graph)
    missing_names = {g.missing_decl for g in gaps}

    assert "Group.Basis.subset_extend" not in missing_names
    assert "Ring.Basis.subset_extend" not in missing_names


def test_detect_supports_backward_compatible_top_k_argument() -> None:
    graph = _build_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            top_k=5,
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
        )
    )

    gaps = detector.detect(graph, top_k=1)
    assert len(gaps) == 1


# --- Type class filter tests ---


def _build_typed_graph() -> MathlibGraph:
    """Build a graph with realistic type signatures containing type class instances."""
    g = nx.DiGraph()
    # Module declarations — require [Module R M] instance
    g.add_node(
        "Module.rank",
        kind="theorem",
        type_signature="∀ {R : Type u_1} {M : Type u_2} [inst : CommRing R] [Module R M], ...",
    )
    g.add_node("Module.sub", kind="theorem", type_signature="Module.sub : Prop")
    # Group declarations
    g.add_node(
        "Group.order",
        kind="theorem",
        type_signature="∀ {G : Type u_1} [inst : Group G], ...",
    )
    g.add_node("Group.sub", kind="theorem", type_signature="Group.sub : Prop")
    # Ring declarations
    g.add_node(
        "Ring.rank",
        kind="theorem",
        type_signature="∀ {R : Type u_1} [inst : Ring R], ...",
    )
    g.add_node("Ring.sub", kind="theorem", type_signature="Ring.sub : Prop")
    # Shared deps
    g.add_node("Nat.succ", kind="def", type_signature="Nat.succ : Nat → Nat")
    # Edges: Module.rank depends on Module.sub and Nat.succ
    g.add_edge("Module.rank", "Module.sub")
    g.add_edge("Module.rank", "Nat.succ")
    # Edges: Group.order depends on Group.sub and Nat.succ
    g.add_edge("Group.order", "Group.sub")
    g.add_edge("Group.order", "Nat.succ")
    return MathlibGraph(g)


def test_type_class_filter_rejects_incompatible_transfer() -> None:
    """Module.rank requires [Module R M]; Group cannot provide Module → rejected."""
    graph = _build_typed_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
            min_score=0.0,
            enable_type_class_filter=True,
        )
    )
    gaps = detector.detect(graph)
    missing_names = {g.missing_decl for g in gaps}
    # Module.rank → Group.rank should be rejected (Group can't provide Module)
    assert "Group.rank" not in missing_names


def test_type_class_filter_allows_compatible_transfer() -> None:
    """Group.order requires [Group G]; Ring can provide Group → allowed."""
    graph = _build_typed_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
            min_score=0.0,
            enable_type_class_filter=True,
        )
    )
    gaps = detector.detect(graph)
    missing_names = {g.missing_decl for g in gaps}
    # Group.order → Ring.order should be allowed (Ring provides Group)
    assert "Ring.order" in missing_names


def test_type_class_filter_disabled_preserves_old_behavior() -> None:
    """With filter disabled, incompatible transfers are kept."""
    graph = _build_typed_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
            min_score=0.0,
            enable_type_class_filter=False,
        )
    )
    gaps = detector.detect(graph)
    missing_names = {g.missing_decl for g in gaps}
    # With filter off, Module→Group transfer should pass through
    assert "Group.rank" in missing_names


def test_type_class_satisfaction_signal_present() -> None:
    """Candidates should include type_class_satisfaction in signals when filter is enabled."""
    graph = _build_typed_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
            min_score=0.0,
            enable_type_class_filter=True,
        )
    )
    gaps = detector.detect(graph)
    assert len(gaps) > 0
    for gap in gaps:
        assert "type_class_satisfaction" in gap.signals


def test_existing_tests_pass_with_prop_signatures() -> None:
    """Prop type signatures have no type class instances → filter passes them through."""
    graph = _build_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
            enable_type_class_filter=True,
        )
    )
    gaps = detector.detect(graph)
    missing_names = {g.missing_decl for g in gaps}
    # Same assertion as the original test — Prop sigs have no instances, so filter is a no-op
    assert "Ring.one_mul" in missing_names


# --- Weighted dependency scoring tests ---


def test_weighted_dependencies_score_discrimination() -> None:
    """Family-specific deps should contribute more weight than universal deps.

    When a family dep misses (Group.helper → Ring.helper not in graph) but a
    universal dep hits (Nat.zero → Nat.zero in graph), weighted scoring
    down-weights the universal hit, producing a different dep_overlap than
    uniform scoring.
    """
    g = nx.DiGraph()
    # Source: depends on a family-specific dep and a universal dep
    g.add_node("Group.thm_a", kind="theorem", type_signature="∀ {G : Type} [inst : Group G], ...")
    g.add_node("Group.helper", kind="theorem", type_signature="Group.helper : Prop")
    g.add_node("Nat.zero", kind="def", type_signature="Nat.zero : Nat")
    g.add_edge("Group.thm_a", "Group.helper")
    g.add_edge("Group.thm_a", "Nat.zero")
    # Target family exists but does NOT have Ring.helper (so the family dep misses)
    g.add_node("Ring.other", kind="theorem", type_signature="Ring.other : Prop")

    graph = MathlibGraph(g)

    detector_weighted = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
            min_score=0.0,
            enable_type_class_filter=True,
            enable_weighted_dependencies=True,
        )
    )
    detector_uniform = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring."),
            min_cross_family_hits=0,
            min_cross_family_overlap=0.0,
            min_score=0.0,
            enable_type_class_filter=True,
            enable_weighted_dependencies=False,
        )
    )

    gaps_w = detector_weighted.detect(graph)
    gaps_u = detector_uniform.detect(graph)

    # Both should find Ring.thm_a as a gap
    assert any(g.missing_decl == "Ring.thm_a" for g in gaps_w)
    assert any(g.missing_decl == "Ring.thm_a" for g in gaps_u)

    # Weighted dep_overlap should differ from uniform dep_overlap:
    # Uniform: total=2, hits=1 (Nat.zero), dep_overlap=0.5
    # Weighted: family dep (weight=1.0) misses, universal dep (weight≈0.05) hits
    #           → dep_overlap much lower than 0.5
    w_gap = next(g for g in gaps_w if g.missing_decl == "Ring.thm_a")
    u_gap = next(g for g in gaps_u if g.missing_decl == "Ring.thm_a")
    assert w_gap.signals["dependency_overlap"] != u_gap.signals["dependency_overlap"]
