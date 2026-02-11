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
from autonomous_discovery.counterexample_filter.basic import (
    BasicCounterexampleFilter,
    FilterDecision,
)
from autonomous_discovery.gap_detector.analogical import AnalogicalGapDetector, GapDetectorConfig
from autonomous_discovery.knowledge_base.graph import MathlibGraph
from autonomous_discovery.knowledge_base.parser import parse_declaration_types, parse_premises
from autonomous_discovery.lean_bridge.runner import LeanRunner
from autonomous_discovery.novelty_checker.basic import BasicNoveltyChecker, NoveltyDecision
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

    def runtime_status(self) -> dict[str, bool]: ...


class CounterexampleFilter(Protocol):
    """Protocol for fast conjecture rejection filters."""

    def evaluate(self, conjecture: ConjectureCandidate) -> FilterDecision: ...


class NoveltyChecker(Protocol):
    """Protocol for novelty/duplicate detection."""

    def is_novel(self, statement: str) -> NoveltyDecision: ...


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


def _runtime_status(verifier: Verifier) -> dict[str, bool]:
    if hasattr(verifier, "runtime_status"):
        status = verifier.runtime_status()
        return {
            "lean_available": bool(status.get("lean_available", False)),
            "sandbox_available": bool(status.get("sandbox_available", False)),
            "runtime_ready": bool(status.get("runtime_ready", False)),
        }

    lean_available = verifier.is_available()
    return {
        "lean_available": lean_available,
        "sandbox_available": True,
        "runtime_ready": lean_available,
    }


def _build_default_verifier(
    config: ProjectConfig, *, trusted_local_run: bool, sandbox_command_prefix: tuple[str, ...]
) -> Verifier:
    runner = LeanRunner(project_dir=config.lean_project_dir)
    try:
        return LeanVerifier(
            runner=runner,
            require_sandbox=not trusted_local_run,
            sandbox_command_prefix=sandbox_command_prefix,
        )
    except TypeError:
        # Backward-compatible fallback for test doubles with legacy constructor signatures.
        return LeanVerifier(runner=runner)


def run_phase2_cycle(
    *,
    premises_path: Path,
    decl_types_path: Path,
    output_dir: Path,
    top_k: int = 20,
    proof_retry_budget: int = 3,
    trusted_local_run: bool = False,
    sandbox_command_prefix: tuple[str, ...] = ("nsjail",),
    generator: ConjectureGenerator | None = None,
    conjecture_filter: CounterexampleFilter | None = None,
    novelty_checker: NoveltyChecker | None = None,
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

    effective_filter = conjecture_filter or BasicCounterexampleFilter()
    effective_novelty_checker = novelty_checker or BasicNoveltyChecker()
    effective_proof_engine = proof_engine or SimpleProofEngine()
    effective_verifier = verifier or _build_default_verifier(
        config,
        trusted_local_run=trusted_local_run,
        sandbox_command_prefix=sandbox_command_prefix,
    )
    runtime_status = _runtime_status(effective_verifier)
    verification_mode = "trusted_local" if trusted_local_run else "sandboxed"

    output_dir.mkdir(parents=True, exist_ok=True)
    attempts_path = output_dir / "phase2_attempts.jsonl"
    metrics_path = output_dir / "phase2_cycle_metrics.json"

    filtered_out_count = 0
    filter_pass_count = 0
    filter_reject_reasons: dict[str, int] = {}
    duplicate_count = 0
    novel_count = 0
    novelty_unknown_count = 0
    success_count = 0
    failure_counts: dict[str, int] = {}
    skipped_reason: str | None = None
    verifiable_conjectures: list[ConjectureCandidate] = []
    for conjecture in conjectures:
        filter_decision = effective_filter.evaluate(conjecture)
        if not filter_decision.accepted:
            filtered_out_count += 1
            filter_reject_reasons[filter_decision.reason] = (
                filter_reject_reasons.get(filter_decision.reason, 0) + 1
            )
            continue
        filter_pass_count += 1

        novelty_decision = effective_novelty_checker.is_novel(conjecture.lean_statement)
        if novelty_decision.is_novel:
            novel_count += 1
            verifiable_conjectures.append(conjecture)
        elif novelty_decision.reason:
            duplicate_count += 1
        else:
            novelty_unknown_count += 1

    with attempts_path.open("w", encoding="utf-8"):
        pass
    if not runtime_status["runtime_ready"]:
        if runtime_status["lean_available"] and not runtime_status["sandbox_available"]:
            skipped_reason = (
                "Sandbox runtime is required for Lean verification but was not found. "
                "Configure sandbox_command_prefix or use trusted local mode."
            )
        elif not runtime_status["lean_available"]:
            skipped_reason = "Lean executable is not available on PATH."
        else:
            skipped_reason = "Verifier runtime is not ready."
    else:
        with attempts_path.open("w", encoding="utf-8") as f:
            for conjecture in verifiable_conjectures:
                attempts = effective_proof_engine.build_attempts(
                    conjecture,
                    max_attempts=proof_retry_budget,
                )
                conjecture_succeeded = False
                for attempt in attempts:
                    attempt_started_ns = time.perf_counter_ns()
                    verification = effective_verifier.verify(
                        attempt.statement, attempt.proof_script
                    )
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

    success_rate = success_count / len(verifiable_conjectures) if verifiable_conjectures else 0.0
    cycle_duration_ms = (time.perf_counter_ns() - cycle_started_ns) / 1_000_000
    metrics: dict[str, Any] = {
        "gap_count": len(gaps),
        "conjecture_count": len(conjectures),
        "filtered_out_count": filtered_out_count,
        "filter_pass_count": filter_pass_count,
        "filter_reject_reasons": dict(sorted(filter_reject_reasons.items())),
        "duplicate_count": duplicate_count,
        "novel_count": novel_count,
        "novelty_unknown_count": novelty_unknown_count,
        "verification_success_count": success_count,
        "success_rate": success_rate,
        "cycle_duration_ms": round(cycle_duration_ms, 3),
        "graph_cache_hit": graph_cache_hit,
        "verifier_available": runtime_status["lean_available"],
        "verification_mode": verification_mode,
        "lean_available": runtime_status["lean_available"],
        "sandbox_available": runtime_status["sandbox_available"],
        "runtime_ready": runtime_status["runtime_ready"],
        "skipped_reason": skipped_reason,
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
