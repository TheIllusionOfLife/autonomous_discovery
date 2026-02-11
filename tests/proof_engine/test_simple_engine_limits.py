import pytest

from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.proof_engine.simple_engine import SimpleProofEngine


def _sample_conjecture() -> ConjectureCandidate:
    return ConjectureCandidate(
        gap_missing_decl="Ring.one_mul",
        lean_statement="theorem Ring_one_mul : Prop",
        rationale="",
        model_id="template-v1",
        temperature=0.0,
        metadata={},
    )


def test_simple_proof_engine_rejects_excessive_retry_budget() -> None:
    engine = SimpleProofEngine()

    with pytest.raises(ValueError, match="supported"):
        engine.build_attempts(_sample_conjecture(), max_attempts=4)
