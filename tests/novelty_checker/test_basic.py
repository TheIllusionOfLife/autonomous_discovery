from autonomous_discovery.novelty_checker.basic import (
    BasicNoveltyChecker,
    NoveltyDecision,
    SemanticComparison,
)


def test_basic_novelty_checker_flags_exact_duplicate() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem x : True"})

    decision = checker.is_novel("theorem x : True")

    assert decision == NoveltyDecision(is_novel=False, reason="exact_duplicate")


def test_basic_novelty_checker_flags_normalized_duplicate() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem foo  :   True"})

    decision = checker.is_novel("theorem foo : True")

    assert decision == NoveltyDecision(is_novel=False, reason="normalized_duplicate")


def test_basic_novelty_checker_flags_defeq_duplicate_with_alpha_renaming() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem foo : ∀ n : Nat, n = n"})

    decision = checker.is_novel("theorem foo : ∀ m : Nat, m = m")

    assert decision == NoveltyDecision(is_novel=False, reason="defeq_duplicate")


def test_basic_novelty_checker_flags_bi_implication_duplicate() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem foo : P -> Q"})

    decision = checker.is_novel("theorem foo : Q -> P")

    assert decision == NoveltyDecision(is_novel=False, reason="bi_implication_duplicate")


def test_basic_novelty_checker_flags_semantic_duplicate_when_comparator_matches() -> None:
    class AlwaysEquivalentComparator:
        def compare(self, left: str, right: str) -> SemanticComparison:
            _ = (left, right)
            return SemanticComparison(equivalent=True, confidence=0.95, reason="semantic_match")

    checker = BasicNoveltyChecker(
        existing_statements={"theorem x : Nat.succ n = n + 1"},
        semantic_comparator=AlwaysEquivalentComparator(),
    )

    decision = checker.is_novel("theorem y : n + 1 = Nat.succ n")

    assert decision == NoveltyDecision(
        is_novel=False,
        reason="semantic_duplicate",
        layer="semantic",
        confidence=0.95,
    )


def test_basic_novelty_checker_reports_unknown_when_semantic_confidence_is_low() -> None:
    class LowConfidenceComparator:
        def compare(self, left: str, right: str) -> SemanticComparison:
            _ = (left, right)
            return SemanticComparison(equivalent=True, confidence=0.4, reason="low_confidence")

    checker = BasicNoveltyChecker(
        existing_statements={"theorem x : Nat.succ n = n + 1"},
        semantic_comparator=LowConfidenceComparator(),
        semantic_confidence_threshold=0.9,
    )

    decision = checker.is_novel("theorem y : n + 1 = Nat.succ n")

    assert decision == NoveltyDecision(
        is_novel=False,
        reason="unknown",
        layer="semantic",
        confidence=0.4,
    )


def test_basic_novelty_checker_accepts_new_statement() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem x : True"})

    decision = checker.is_novel("theorem y : False")

    assert decision == NoveltyDecision(is_novel=True, reason="novel")


def test_basic_novelty_checker_ignores_line_comments_in_normalization() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem x : True -- baseline"})

    decision = checker.is_novel("theorem x : True")

    assert decision == NoveltyDecision(is_novel=False, reason="normalized_duplicate")
