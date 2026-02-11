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
        config=GapDetectorConfig(family_prefixes=("Group.", "Ring.", "Module."))
    )

    gaps = detector.detect(graph, top_k=20)
    missing_names = {g.missing_decl for g in gaps}

    assert "Ring.one_mul" in missing_names


def test_respects_score_threshold() -> None:
    graph = _build_graph()
    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=("Group.", "Ring.", "Module."),
            min_score=1.01,
        )
    )
    assert detector.detect(graph, top_k=20) == []


def test_returns_ranked_results_with_expected_signals() -> None:
    graph = _build_graph()
    detector = AnalogicalGapDetector()
    gaps = detector.detect(graph, top_k=2)

    assert len(gaps) == 2
    assert gaps[0].score >= gaps[1].score
    assert "dependency_overlap" in gaps[0].signals
    assert "source_pagerank" in gaps[0].signals
    assert "source_descendants" in gaps[0].signals
