"""Phase 2 orchestration: gap -> conjecture -> proof attempts -> verification."""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Protocol

from autonomous_discovery.config import ProjectConfig
from autonomous_discovery.conjecture_generator.models import ConjectureCandidate
from autonomous_discovery.conjecture_generator.protocol import ConjectureGenerator
from autonomous_discovery.conjecture_generator.template import TemplateConjectureGenerator
from autonomous_discovery.gap_detector.analogical import AnalogicalGapDetector, GapDetectorConfig
from autonomous_discovery.knowledge_base.graph import MathlibGraph
from autonomous_discovery.knowledge_base.parser import parse_declaration_types, parse_premises
from autonomous_discovery.lean_bridge.runner import LeanRunner
from autonomous_discovery.proof_engine.models import ProofAttempt
from autonomous_discovery.proof_engine.simple_engine import SimpleProofEngine
from autonomous_discovery.verifier.lean_verifier import LeanVerifier
from autonomous_discovery.verifier.models import VerificationResult

_MAX_CACHE_SIZE = 5
_GRAPH_CACHE: OrderedDict[tuple[str, int, int, str, int, int], MathlibGraph] = OrderedDict()


class ProofEngine(Protocol):
    """Protocol for proof attempt generators."""

    def build_attempts(
        self, conjecture: ConjectureCandidate, *, max_attempts: int = 3
    ) -> list[ProofAttempt]: ...


class Verifier(Protocol):
    """Protocol for proof verification backends."""

    def verify(self, statement: str, proof_script: str) -> VerificationResult: ...

    def is_available(self) -> bool: ...


def _file_signature(path: Path) -> tuple[str, int, int]:
    stat = path.stat()
    return (str(path.resolve()), stat.st_mtime_ns, stat.st_size)


def _load_graph_cached(premises_path: Path, decl_types_path: Path) -> tuple[MathlibGraph, bool]:
    key = (*_file_signature(premises_path), *_file_signature(decl_types_path))
    if key in _GRAPH_CACHE:
        _GRAPH_CACHE.move_to_end(key)
        return _GRAPH_CACHE[key], True

    premises = parse_premises(premises_path.read_text(encoding="utf-8"))
    declarations = parse_declaration_types(decl_types_path.read_text(encoding="utf-8"))
    graph = MathlibGraph.from_raw_data(premises, declarations)
    _GRAPH_CACHE[key] = graph
    while len(_GRAPH_CACHE) > _MAX_CACHE_SIZE:
        _GRAPH_CACHE.popitem(last=False)
    return graph, False


def _failure_kind(result: VerificationResult) -> str:
    if result.timed_out:
        return "timeout"
    if result.success:
        return "none"
    lowered = result.stderr.lower()
    if "not available" in lowered:
        return "unavailable"
    if "unsafe" in lowered:
        return "unsafe_input"
    if "error" in lowered:
        return "compile_error"
    return "verification_failed"


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

    cycle_started_ns = time.perf_counter_ns()
    config = ProjectConfig()
    graph, graph_cache_hit = _load_graph_cached(premises_path, decl_types_path)

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
    effective_verifier = verifier or LeanVerifier(
        runner=LeanRunner(project_dir=config.lean_project_dir)
    )
    verifier_available = effective_verifier.is_available()

    output_dir.mkdir(parents=True, exist_ok=True)
    attempts_path = output_dir / "phase2_attempts.jsonl"
    metrics_path = output_dir / "phase2_cycle_metrics.json"

    success_count = 0
    failure_counts: dict[str, int] = {}
    with attempts_path.open("w", encoding="utf-8") as f:
        for conjecture in conjectures:
            attempts = effective_proof_engine.build_attempts(
                conjecture,
                max_attempts=proof_retry_budget,
            )
            conjecture_succeeded = False
            for attempt in attempts:
                attempt_started_ns = time.perf_counter_ns()
                verification = effective_verifier.verify(attempt.statement, attempt.proof_script)
                duration_ms = (time.perf_counter_ns() - attempt_started_ns) / 1_000_000
                failure_kind = _failure_kind(verification)
                if failure_kind != "none":
                    failure_counts[failure_kind] = failure_counts.get(failure_kind, 0) + 1
                row = {
                    "gap_missing_decl": conjecture.gap_missing_decl,
                    "statement": attempt.statement,
                    "proof_script": attempt.proof_script,
                    "engine": attempt.engine,
                    "attempt_index": attempt.attempt_index,
                    "success": verification.success,
                    "stderr": verification.stderr,
                    "timed_out": verification.timed_out,
                    "duration_ms": round(duration_ms, 3),
                    "failure_kind": failure_kind,
                }
                f.write(json.dumps(row, sort_keys=True) + "\n")
                if verification.success:
                    conjecture_succeeded = True
                    break
            if conjecture_succeeded:
                success_count += 1

    success_rate = success_count / len(conjectures) if conjectures else 0.0
    cycle_duration_ms = (time.perf_counter_ns() - cycle_started_ns) / 1_000_000
    metrics: dict[str, Any] = {
        "gap_count": len(gaps),
        "conjecture_count": len(conjectures),
        "verification_success_count": success_count,
        "success_rate": success_rate,
        "cycle_duration_ms": round(cycle_duration_ms, 3),
        "graph_cache_hit": graph_cache_hit,
        "verifier_available": verifier_available,
        "failure_counts": dict(sorted(failure_counts.items())),
        "top_k": top_k,
        "proof_retry_budget": proof_retry_budget,
        "artifacts": {
            "attempts_path": str(attempts_path),
            "metrics_path": str(metrics_path),
        },
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics
