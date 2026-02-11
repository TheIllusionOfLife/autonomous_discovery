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
