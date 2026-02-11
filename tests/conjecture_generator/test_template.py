import pytest

from autonomous_discovery.conjecture_generator.template import TemplateConjectureGenerator
from autonomous_discovery.gap_detector.analogical import GapCandidate


def test_template_generator_returns_deterministic_top_k_candidates() -> None:
    gaps = [
        GapCandidate(
            source_decl="Group.mul_assoc",
            target_family="Ring.",
            missing_decl="Ring.mul_assoc",
            score=0.81,
            signals={"dependency_overlap": 0.7},
        ),
        GapCandidate(
            source_decl="Group.one_mul",
            target_family="Ring.",
            missing_decl="Ring.one_mul",
            score=0.91,
            signals={"dependency_overlap": 0.9},
        ),
    ]

    generator = TemplateConjectureGenerator()
    candidates = generator.generate(gaps, max_candidates=1)

    assert len(candidates) == 1
    assert candidates[0].gap_missing_decl == "Ring.one_mul"
    assert candidates[0].lean_statement == "theorem Ring_one_mul : True"
    assert candidates[0].model_id == "template-v1"
    assert candidates[0].temperature == 0.0


def test_template_generator_includes_signal_metadata() -> None:
    gap = GapCandidate(
        source_decl="Group.inv_mul_cancel",
        target_family="Ring.",
        missing_decl="Ring.inv_mul_cancel",
        score=0.55,
        signals={"cross_family_overlap": 0.25},
    )

    generator = TemplateConjectureGenerator()
    [candidate] = generator.generate([gap], max_candidates=3)

    assert candidate.metadata["source_decl"] == "Group.inv_mul_cancel"
    assert candidate.metadata["target_family"] == "Ring."
    assert candidate.metadata["score"] == "0.550000"
    assert candidate.metadata["signal_cross_family_overlap"] == "0.250000"


def test_template_generator_rejects_newline_in_missing_decl() -> None:
    gap = GapCandidate(
        source_decl="Group.inv_mul_cancel",
        target_family="Ring.",
        missing_decl='Ring.inv_mul_cancel\n#eval IO.println "x"',
        score=0.55,
        signals={"cross_family_overlap": 0.25},
    )
    generator = TemplateConjectureGenerator()

    with pytest.raises(ValueError, match="newline"):
        generator.generate([gap], max_candidates=1)
