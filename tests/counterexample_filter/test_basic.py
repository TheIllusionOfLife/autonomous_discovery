from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.counterexample_filter.basic import (
    BasicCounterexampleFilter,
    FilterDecision,
)


def _candidate(statement: str) -> ConjectureCandidate:
    return ConjectureCandidate(
        gap_missing_decl="Group.one_mul",
        lean_statement=statement,
        rationale="test",
        model_id="test",
        temperature=0.0,
    )


def test_counterexample_filter_rejects_false_marker() -> None:
    f = BasicCounterexampleFilter()

    decision = f.evaluate(_candidate("theorem bad : False"))

    assert decision == FilterDecision(accepted=False, reason="contains_false_literal")


def test_counterexample_filter_rejects_obvious_contradiction() -> None:
    f = BasicCounterexampleFilter()

    decision = f.evaluate(_candidate("theorem bad : 1 = 0"))

    assert decision == FilterDecision(accepted=False, reason="contains_obvious_contradiction")


def test_counterexample_filter_allows_simple_true_statement() -> None:
    f = BasicCounterexampleFilter()

    decision = f.evaluate(_candidate("theorem ok : True"))

    assert decision == FilterDecision(accepted=True, reason="passed_basic_checks")
