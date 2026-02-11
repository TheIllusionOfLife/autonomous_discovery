from autonomous_discovery.novelty_checker.basic import (
    BasicNoveltyChecker,
    NoveltyDecision,
)


def test_basic_novelty_checker_flags_exact_duplicate() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem x : True"})

    decision = checker.is_novel("theorem x : True")

    assert decision == NoveltyDecision(is_novel=False, reason="exact_duplicate")


def test_basic_novelty_checker_flags_normalized_duplicate() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem foo  :   True"})

    decision = checker.is_novel("theorem foo : True")

    assert decision == NoveltyDecision(is_novel=False, reason="normalized_duplicate")


def test_basic_novelty_checker_accepts_new_statement() -> None:
    checker = BasicNoveltyChecker(existing_statements={"theorem x : True"})

    decision = checker.is_novel("theorem y : True")

    assert decision == NoveltyDecision(is_novel=True, reason="novel")
