# Experiment: Initial Validation (2026-02-13)

## Executive Summary

**Overall verdict: NO_GO** (conditional — two fixable bottlenecks identified)

The pipeline is fully functional end-to-end. The LLM (gpt-oss:20b) generated **mathematically meaningful** Lean 4 conjectures for Jacobson radical theory, module ranks, and substructure membership — but **none verified** due to a weak proof engine. Phase 1 gap quality does not meet the absolute non-trivial count threshold (9/20 vs 20 needed). The post-cutoff theorem supply is abundant (28,991 vs 30 needed), confirming the mathematical domain is viable.

**Two bottlenecks**: (1) Gap filtering lets trivial declarations through, diluting the candidate pool; (2) The proof engine (`exact?`/`aesop`/`simp`) cannot handle non-trivial proofs. Both are engineering problems, not fundamental viability issues.

## Go/No-Go Gate Results

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| Non-trivial gaps | >= 20 | 9 | FAIL |
| Detection rate | >= 5% | 50% | PASS |
| Top-20 precision | >= 60% | 45% | FAIL |
| Post-cutoff theorems | >= 30 | 28,991 | PASS |

Decision rule: GO if `non_trivial_count >= 20` AND (`detection_rate >= 5%` OR `precision >= 60%`).
Result: **NO_GO** — non_trivial_count (9) < 20.

## Phase 1: Gap Detection Quality

- **20 candidates** evaluated from analogical gap detector
- **9/20 non-trivial** (45% precision) — Jacobson radical analogs, extensionality, characterization theorems
- **11/20 trivial** — coercion injectivity lemmas, simp tags, instance derivations, inhabited instances
- **Detection rate**: 50% of evaluated module proxies contain non-trivial gaps (2/4 modules)
- Non-trivial gaps cluster in Jacobson radical theory (Ring ↔ Module analogs)

### Why NO_GO on Phase 1

The absolute count gate (>= 20 non-trivial) requires expanding the candidate pool. Current top-20 is dominated by mechanical declarations that the type-aware filtering scores highly because they share structural analogy patterns with substantive theorems.

## Phase 2: Template Baseline

- **20 gaps** → **20 conjectures** → **19 defeq duplicates** → **1 novel** → **1 verified** (100%)
- Template generator produces trivial `theorem X : True` conjectures by design
- 19/20 conjectures flagged as defeq duplicates by novelty checker — system correctly identifies them
- The 1 novel conjecture verified successfully, confirming Lean bridge works end-to-end
- Cycle duration: ~204s

## Phase 2: Ollama LLM (gpt-oss:20b)

- **20 gaps** → **14 conjectures** (6 gaps produced no parseable Lean output) → **14 novel** → **0 verified** (0%)
- Model: `gpt-oss:20b` (20.9B params, MXFP4 quantization, local GPU)
- Cycle duration: ~110 min (~5 min/candidate with 3 retries)
- Failure breakdown: 13 Lean verification timeouts, 29 verification failures
- Proof engine limited to `exact?`, `aesop`, `simp` — insufficient for non-trivial proofs

### Conjecture Quality Assessment

The LLM produced **mathematically meaningful** Lean 4 statements for several gaps:

| Conjecture | Assessment |
|------------|------------|
| `Ring.map_jacobson_of_bijective` | Jacobson radical preservation under bijective ring maps — plausible theorem |
| `Ring.jacobson_pi_le` | Product inequality for Jacobson radical — structurally correct |
| `Ring.jacobson_eq_bot_of_injective` | Vanishing under injection — likely needs stronger hypotheses |
| `Ring.comap_jacobson_of_ker_le` | Preimage of Jacobson radical — well-formed |
| `Module.rank_le_domain` | Module rank bound under linear maps — meaningful |
| `Ring.ofIsUnitOrEqZero` | Field dichotomy (IsUnit or zero) — known result |
| `Subgroup.single_mem_pi` / `Submodule.single_mem_pi` | Pi membership — correct pattern |
| `Submodule.pi_span` | Span commutes with pi — plausible |

However, 5/14 conjectures were nonsensical `Coe SpecialLinearGroup GeneralLinearGroup` instances — the LLM hallucinated the same coercion pattern across different family prefixes due to garbage gap inputs.

### Why 0% Verification

Two distinct failure modes:
1. **Bad statements** (5/14): Coercion instance hallucinations that Lean can't even type-check efficiently (timeout)
2. **Good statements, weak proofs** (9/14): Mathematically plausible conjectures where `exact?`/`aesop`/`simp` are too weak — these theorems require multi-step proofs with imports and lemma chains

## Post-Cutoff Validation

- **18,150** total algebra theorems in current Mathlib snapshot
- **28,991** approximate theorem additions after 2024-08-01 cutoff
- Threshold: >= 30 → **GO** (exceeded by ~966x)
- The algebra domain has abundant post-cutoff activity for rediscovery experiments

## Recommendations

1. **Improve gap filtering** (Phase 1 bottleneck): Add heuristics to deprioritize coercion injectivity (`_injective` suffix on type-cast declarations), instance derivations (`addCommGroup`, `addCommMonoid`, `inhabited`), and mechanical simp lemmas (`congr_simp`). This alone could push precision above 60% and remove garbage inputs that cause LLM hallucinations.

2. **Expand candidate pool**: Increase `top_k` beyond 20 or broaden family prefixes to surface more non-trivial candidates and meet the absolute count threshold.

3. **Strengthen proof engine** (Phase 2 bottleneck): The current engine only tries 3 generic tactics (`exact?`, `aesop`, `simp`). The Jacobson radical conjectures and module rank bounds are plausible but require multi-step proofs. Consider: (a) LLM-generated proof sketches alongside conjectures, (b) tactic chains with intermediate `have` steps, (c) targeted `apply` with known lemmas from the dependency graph.

4. **Weighted scoring refinement**: The current dependency-weighted scoring ranks trivial declarations highly. Consider penalizing candidates whose source declarations are auto-generated (instance, coercion, simp).

5. **Evaluate with a stronger model**: The `gpt-oss:20b` model produced 5/14 hallucinated coercion instances. A larger or more math-specialized model may improve both statement quality and could generate proof hints.
