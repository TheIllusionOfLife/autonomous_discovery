# Experiment: Initial Validation (2026-02-13)

## Executive Summary

**Overall verdict: NO_GO**

The pipeline infrastructure is fully functional end-to-end, but Phase 1 gap quality does not meet the absolute non-trivial count threshold. The post-cutoff theorem supply is abundant (28,991 vs 30 needed), confirming the mathematical domain is viable. The bottleneck is gap candidate quality — too many mechanical/trivial gaps dilute the top-20.

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

## Phase 2: Ollama LLM

- **Ollama service unavailable** (HTTP 404 on localhost:11434)
- All 20 gap candidates failed after 3 retry attempts each
- **0 conjectures generated, 0 verified**
- This step requires a running Ollama instance with a suitable model (e.g., `codellama`)

## Post-Cutoff Validation

- **18,150** total algebra theorems in current Mathlib snapshot
- **28,991** approximate theorem additions after 2024-08-01 cutoff
- Threshold: >= 30 → **GO** (exceeded by ~966x)
- The algebra domain has abundant post-cutoff activity for rediscovery experiments

## Recommendations

1. **Improve gap filtering**: Add heuristics to deprioritize coercion injectivity (`_injective` suffix on type-cast declarations), instance derivations (`addCommGroup`, `addCommMonoid`, `inhabited`), and mechanical simp lemmas (`congr_simp`). This alone could push precision above 60%.

2. **Expand candidate pool**: Increase `top_k` beyond 20 or broaden family prefixes to surface more non-trivial candidates and meet the absolute count threshold.

3. **Re-run with Ollama**: Set up Ollama with a code-capable model to evaluate LLM-generated conjectures. The template baseline confirms the pipeline works; real conjectures are needed to assess discovery potential.

4. **Weighted scoring refinement**: The current dependency-weighted scoring ranks trivial declarations highly. Consider penalizing candidates whose source declarations are auto-generated (instance, coercion, simp).
