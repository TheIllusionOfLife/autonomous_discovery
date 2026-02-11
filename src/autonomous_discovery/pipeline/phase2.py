"""Phase 2 orchestration: gap -> conjecture -> proof attempts -> verification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from autonomous_discovery.config import ProjectConfig
from autonomous_discovery.conjecture_generator.protocol import ConjectureGenerator
from autonomous_discovery.conjecture_generator.template import TemplateConjectureGenerator
from autonomous_discovery.gap_detector.analogical import AnalogicalGapDetector, GapDetectorConfig
from autonomous_discovery.knowledge_base.graph import MathlibGraph
from autonomous_discovery.knowledge_base.parser import parse_declaration_types, parse_premises
from autonomous_discovery.proof_engine.models import ProofAttempt
from autonomous_discovery.proof_engine.simple_engine import SimpleProofEngine
from autonomous_discovery.verifier.lean_verifier import LeanVerifier
from autonomous_discovery.verifier.models import VerificationResult


class ProofEngine(Protocol):
    """Protocol for proof attempt generators."""

    def build_attempts(self, conjecture: Any, *, max_attempts: int = 3) -> list[ProofAttempt]: ...


class Verifier(Protocol):
    """Protocol for proof verification backends."""

    def verify(self, statement: str, proof_script: str) -> VerificationResult: ...


def run_phase2_cycle(
    *,
    premises_path: Path,
    decl_types_path: Path,
    output_dir: Path,
    top_k: int = 20,
    proof_retry_budget: int = 3,
    generator: ConjectureGenerator | None = None,
    proof_engine: ProofEngine | None = None,
    verifier: Verifier | None = None,
) -> dict[str, Any]:
    """Execute one deterministic discovery cycle for Phase 2."""
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    if proof_retry_budget <= 0:
        raise ValueError("proof_retry_budget must be a positive integer")

    config = ProjectConfig()
    premises = parse_premises(premises_path.read_text(encoding="utf-8"))
    declarations = parse_declaration_types(decl_types_path.read_text(encoding="utf-8"))
    graph = MathlibGraph.from_raw_data(premises, declarations)

    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=config.algebra_name_prefixes,
            top_k=top_k,
        )
    )
    gaps = detector.detect(graph, top_k=top_k)

    effective_generator = generator or TemplateConjectureGenerator()
    conjectures = effective_generator.generate(gaps, max_candidates=top_k)

    effective_proof_engine = proof_engine or SimpleProofEngine()
    effective_verifier = verifier or LeanVerifier()

    output_dir.mkdir(parents=True, exist_ok=True)
    attempts_path = output_dir / "phase2_attempts.jsonl"
    metrics_path = output_dir / "phase2_cycle_metrics.json"

    success_count = 0
    with attempts_path.open("w", encoding="utf-8") as f:
        for conjecture in conjectures:
            attempts = effective_proof_engine.build_attempts(
                conjecture,
                max_attempts=proof_retry_budget,
            )
            conjecture_succeeded = False
            for attempt in attempts:
                verification = effective_verifier.verify(attempt.statement, attempt.proof_script)
                row = {
                    "gap_missing_decl": conjecture.gap_missing_decl,
                    "statement": attempt.statement,
                    "proof_script": attempt.proof_script,
                    "engine": attempt.engine,
                    "attempt_index": attempt.attempt_index,
                    "success": verification.success,
                    "stderr": verification.stderr,
                    "timed_out": verification.timed_out,
                }
                f.write(json.dumps(row, sort_keys=True) + "\n")
                if verification.success:
                    conjecture_succeeded = True
                    break
            if conjecture_succeeded:
                success_count += 1

    success_rate = success_count / len(conjectures) if conjectures else 0.0
    metrics: dict[str, Any] = {
        "gap_count": len(gaps),
        "conjecture_count": len(conjectures),
        "verification_success_count": success_count,
        "success_rate": success_rate,
        "top_k": top_k,
        "proof_retry_budget": proof_retry_budget,
        "artifacts": {
            "attempts_path": str(attempts_path),
            "metrics_path": str(metrics_path),
        },
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics
