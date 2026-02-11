from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.proof_engine.simple_engine import SimpleProofEngine


def test_simple_proof_engine_generates_three_attempts() -> None:
    conjecture = ConjectureCandidate(
        gap_missing_decl="Ring.one_mul",
        lean_statement="theorem Ring_one_mul : Prop",
        rationale="",
        model_id="template-v1",
        temperature=0.0,
        metadata={},
    )

    engine = SimpleProofEngine()
    attempts = engine.build_attempts(conjecture, max_attempts=3)

    assert [attempt.attempt_index for attempt in attempts] == [1, 2, 3]
    assert attempts[0].proof_script == "by\n  exact?"
    assert attempts[1].proof_script == "by\n  aesop"
    assert attempts[2].proof_script == "by\n  simp"
