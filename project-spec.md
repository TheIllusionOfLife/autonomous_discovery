# Project Specification: Autonomous Mathematical Discovery
## Addressing Unified Review Issues

> **Document 3 of 3** | Role: **Actionable Specification**
>
> This spec was created after considering both the original proposition and the unified review. It incorporates real-world constraints (hardware, team composition, timeline) gathered through a structured interview, and provides concrete resolutions for every P0-P3 issue raised in the review.
>
> **Previous**: [autonomous-math-discovery-project-brief.md](autonomous-math-discovery-project-brief.md) — Original vision and architecture.
> **Previous**: [unified-review.md](unified-review.md) — Issues this spec addresses.

Generated from interview on 2026-02-10.

---

## 1. Project Constraints (Interview Results)

| Dimension | Decision | Impact |
|-----------|----------|--------|
| Primary deliverable | Paper + working system (both important) | System needs production-quality, not just prototype |
| Compute | Mac Mini M2 Pro (local) + API (heavy inference) | 671B model impossible locally; hybrid strategy required |
| Team | CS-focused, no mathematician | Go/no-go must rely on automated metrics, not human math judgment |
| Lean 4 experience | Intermediate | Phase 1 feasible but expect learning curve on Mathlib internals |
| Proof Engine | Hybrid: local small models + API for complex proofs | Cost-conscious; most operations local, API only when needed |
| Go/No-Go evaluation | Automated metrics (no math expert access) | Must design quantitative criteria that don't require mathematical expertise |
| Timeline | Now (Feb 2026), full-time | NeurIPS 2026 target (~May deadline), fallback ICLR 2027 (~Sep) |
| MVP gap type | Analogical Gap (algebra domain) | Focus on group/ring/module structure analogies in Mathlib |
| Curiosity function | Multiple formulations compared via ablation | Linear combination, information gain, compression progress |
| Data leakage mitigation | Cutoff-based theorem selection | Use only theorems added after LLM training data cutoff |
| Implementation | Lean 4 (proofs/verification) + Python (orchestration) | Bridge needed between Python orchestrator and Lean 4 |
| Paper contribution focus | Discovery results themselves | System is a means; quality of discovered theorems is the measure |
| Math domain | Algebra (groups, rings, modules, etc.) | Rich structural similarity; deep Mathlib coverage |
| Fallback | ICLR 2027 if NeurIPS deadline missed | Allows scope adjustment without panic |
| Openness | Fully open-source (code, data, experiment scripts) | Reproducibility is first-class — see Reproducibility Policy below |

---

## 2. Addressing P0 Issues (Must Resolve Before Starting)

### P0-1: Operational Definitions of Core Claims

**Problem**: "first", "fully autonomous", "divergent" lack testable definitions.

**Resolution**:

- **Autonomous**: Define as "human intervention frequency." Metric: number of human decisions per 100 discovery cycles. Target: 0 during normal operation (human intervenes only on staleness alerts).
- **Divergent**: Define as "objective-free exploration." The system selects its own targets from a curiosity function — no human-specified research question. Note: hyperparameters (α,β,γ) are meta-parameters of the exploration strategy, not research objectives. Analogous to how ε in ε-greedy is not a task specification.
- **First**: Scope the claim precisely: "first system combining autonomous problem-finding with formal verification in mathematics." Acknowledge partial autonomy in Kosmos, AI Scientist. The differentiator is the closed loop: gap detection → conjecture → proof → verification → knowledge base update, all without human-specified objectives.
- **Comparison table**: Add citation for each cell. Replace subjective Yes/No with measurable properties. Add a row for "human decisions per discovery cycle."

### P0-2: Rediscovery Experiment — Data Leakage

**Problem**: LLMs may have memorized Mathlib theorems during pre-training.

**Resolution**:

1. **Cutoff-based selection**: Only remove theorems added to Mathlib AFTER the training data cutoff of the LLM used. For DeepSeek-Prover-V2, identify its training data cutoff date and select theorems merged into Mathlib after that date.
2. **Memorization pre-test**: Before the experiment, directly prompt the LLM with the theorem statement and ask it to prove it. Run 20 attempts per theorem. Classify as "potentially memorized" if the 95% Wilson confidence interval for the pass rate has a lower bound >50%. This avoids the instability of small-sample thresholds (the previous 5-trial / 80% criterion was effectively 5/5 and statistically fragile).
3. **Contamination analysis**: Report memorization test results as part of the paper. Show the distribution of "memorized" vs "non-memorized" theorems and their rediscovery rates separately.
4. **Limitation**: Explicitly acknowledge that complete decontamination is impossible. Frame the experiment as "rediscovery in the presence of potential prior exposure" and argue that the curiosity function's value is in *directing* the search, not in the LLM's raw ability to prove.

### P0-3: Curiosity Function — Multiple Formulations

**Problem**: Single linear combination lacks theoretical justification.

**Resolution**: Implement and compare three formulations:

1. **Linear combination** (baseline): `curiosity(g) = α·novelty + β·tractability + γ·significance`
2. **Information gain**: `curiosity(g) = H(KB) - E[H(KB | prove(g))]` — expected reduction in knowledge base entropy if gap g is filled. Approximated via graph-theoretic measures (how many other gaps become tractable if g is proven).
3. **Compression progress**: `curiosity(g) = Δ_compress(KB, g)` — estimated reduction in total proof length across the knowledge base if g is proven. Measured by: can existing proofs be shortened using g as a lemma?

Ablation study compares all three + random baseline. This becomes a key technical contribution.

### P0-4: Go/No-Go Quantitative Criteria (Without Mathematician)

**Problem**: No mathematician available for "non-trivial" judgment.

**Resolution**: Define automated non-triviality criteria:

1. **Proof complexity**: Gap's expected proof is >N tactic steps (N calibrated against Mathlib median proof length in algebra)
2. **Dependency impact**: Proving the gap would add ≥K new edges to the dependency graph (the theorem is used by other theorems)
3. **Structural novelty**: Embedding distance from nearest existing theorem is above the Pth percentile of inter-theorem distances in the target domain
4. **Not a direct instantiation**: The gap cannot be closed by `apply` or `exact` with a single existing lemma

**Go criteria** (normalized — not dependent on absolute count):

- **Primary metric**: Detection rate ≥ 5% of scanned Mathlib algebra modules contain at least one non-trivial gap satisfying all 4 criteria above.
- **Secondary metric**: Top-20 precision ≥ 60% — of the 20 highest-scored gaps, at least 12 pass all 4 non-triviality criteria when verified independently (re-run with different random seed).
- **Minimum absolute count**: ≥20 non-trivial gaps (lower bound to ensure sufficient experimental sample size).

If primary OR secondary metric fails after 2 iterations on gap detection heuristics, pivot to Formalization Gaps as fallback.

---

## 3. Addressing P1 Issues (Phase 1-2)

### P1-1: Novelty Judgment — defEq Layer

Add a multi-layered equivalence check (defEq alone is too strict and produces false negatives for mathematically equivalent but syntactically different theorems):

1. **Layer 1 — Normalization**: Before comparison, normalize theorem statements by: canonicalizing type variable names, sorting symmetric arguments, and unfolding top-level definitions. This reduces syntactic variation that defeats defEq.
2. **Layer 2 — defEq**: Attempt `Lean.Meta.isDefEq` on normalized statements against existing theorems in the relevant Mathlib module. If match → Duplicate.
3. **Layer 3 — Semantic near-match**: If not defEq but embedding similarity >0.90 → attempt to prove `T_new ↔ T_existing` (or `T_new → T_existing ∧ T_existing → T_new`) using automated tactics (aesop, simp). If bi-implication proven → Duplicate (isomorphic result).
4. **Layer 4 — LLM comparison**: For remaining high-similarity pairs (>0.85), use LLM to assess whether theorems are equivalent up to renaming, reordering, or trivial reformulation.
5. **Triviality**: Replace line-count heuristic with composite score: {tactic_count, max_tactic_depth, unique_lemmas_used, proof_term_size}

### P1-2: Staleness Detection — Statistical Rigor

Replace "3/4 indicators declining for N cycles" with:
1. **CUSUM (Cumulative Sum)** change point detection on novelty rate time series
2. **Sliding window** significance test: compare last W cycles against the preceding W cycles using Mann-Whitney U test
3. **Autocorrelation handling**: Compute lag-1 autocorrelation of novelty rate series. If significant (p < 0.05), apply block bootstrap (block size = estimated autocorrelation length) instead of standard Mann-Whitney to preserve temporal dependence structure.
4. **Multiple testing correction**: Apply Holm-Bonferroni correction across the 4 staleness indicators to control family-wise error rate at α = 0.05.
5. Staleness declared when CUSUM detects a shift AND the corrected significance test rejects H0 (no decline).
6. N is not a fixed hyperparameter — it emerges from the statistical test.
7. **Expected false alarm rate**: Validate via simulation on synthetic novelty curves (constant, linear decline, step decline) before deployment. Target: false positive rate < 5% on constant curves, detection power > 80% on step declines of ≥30%.

### P1-3: Compute Cost Pilot

Run in Phase 1 (week 2-3):
1. Select 10 representative gaps from Mathlib algebra
2. For each gap: measure wall-clock time, API token usage, and cost for conjecture generation + proof attempt
3. Extrapolate to 1K and 10K iterations
4. Decision: If projected 10K iteration cost exceeds $5K API, reduce scope (fewer iterations, simpler model, or narrower domain)

### P1-4: Auto-formalization Pilot

Run in Phase 1 (week 3-4):
1. Take 20 known Mathlib theorems in algebra
2. Express each in natural language
3. Ask LLM to formalize back to Lean 4
4. Measure: type-check pass rate, semantic equivalence rate (via defEq)
5. Decision: If pass rate <60%, invest in fine-tuning or switch to direct Lean generation (skip natural language intermediate)

---

## 4. Addressing P2-P3 Issues (Phase 2-3)

### P2-1: Success Criteria — Statistical Design

- **Rediscovery**: Use Fisher's exact test comparing curiosity-driven vs random baseline rediscovery rates. Pre-register sample size based on power analysis (target: 80% power to detect 20% difference in rediscovery rate).
- **Novel discovery**: Report count + automated non-triviality score distribution. Since no mathematician is available, submit top results to Mathlib as PRs — community acceptance serves as external validation.
- **Effect size**: Report Cohen's h for proportion comparisons.

### P2-2: Comparison Table

- Add citations for each claim about each system
- Replace binary Yes/No with quantitative metrics where possible
- Add a "Design Goal" row acknowledging systems target different objectives

### P3-1: Language

- "stales" → "stagnates" throughout
- General English proofreading pass before submission

---

## 5. Revised Architecture (Constraint-Adapted)

```
┌─────────────────────────────────────────────────────────────────┐
│                   AUTONOMOUS DISCOVERY LOOP                      │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │  KNOWLEDGE   │──→│  ANALOGICAL  │──→│  CONJECTURE  │        │
│  │  BASE        │   │  GAP         │   │  GENERATOR   │        │
│  │  (Mathlib4   │   │  DETECTOR    │   │  (Claude/    │        │
│  │   Algebra    │   │  (NetworkX   │   │   GPT-4 API) │        │
│  │   dep graph  │   │   dep graph  │   │              │        │
│  │   + embed)   │   │   + embed)   │   └──────┬───────┘        │
│  └──────┬───────┘   └──────────────┘          │                │
│         │                                      ↓                │
│         │                              ┌──────────────┐        │
│         │                              │  COUNTER-    │        │
│         │           ┌──────────────┐   │  EXAMPLE     │        │
│         │           │  CURIOSITY   │   │  FILTER      │        │
│         │           │  SCORER      │   │  (small-case │        │
│         │           │  (3 variants │   │   test)      │        │
│         │           │   compared)  │   └──────┬───────┘        │
│         │           └──────────────┘          │                │
│         │                  ↑           pass?  ↓                │
│         │                  │           ┌──────────────┐        │
│  ┌──────────────┐          │           │  PROOF       │        │
│  │  NOVELTY     │          │           │  ENGINE      │        │
│  │  CHECKER     │          │           │  (Local 7B + │        │
│  │  (normalize  │          │           │   API heavy) │        │
│  │  +defEq+emb) │          │           └──────┬───────┘        │
│  └──────┬───────┘          │                  │                │
│         ↑                  │           fail?  ↓ ok?            │
│         │                  │           ┌──────────────┐        │
│         │                  │           │  SELF-REPAIR │        │
│         │                  │           │  (Lean error │        │
│         │                  │           │   → LLM fix  │        │
│         │                  │           │   → retry)   │        │
│         │                  │           └──────┬───────┘        │
│         │                  │                  │                │
│         └──────────────────┼──────── VERIFIER (Lean 4)         │
│                            │                                    │
│  ┌─────────────────────────┴──────────────────────────────── ┐  │
│  │       META-EVALUATOR (CUSUM + Corrected Stat Tests)        │  │
│  └────────────────────────────────────────────────────────── ┘  │
│                         │                                       │
│                         ↓                                       │
│                 [CONTINUE or ALERT HUMAN]                       │
└─────────────────────────────────────────────────────────────────┘

Infra: Python orchestrator ←→ Lean 4 (subprocess/lake)
Local: Mac Mini M2 Pro (orchestration, small model inference, Lean)
API:   DeepSeek / Claude / GPT-4 (conjecture gen, heavy proof attempts)
Graph: NetworkX in-memory (Mathlib dependency graph, ~210K nodes)
```

### 5.1 Knowledge Graph (NetworkX)

The Mathlib dependency graph is the primary structural backbone for gap detection, not just an auxiliary view.

- **Extraction**: Parse Mathlib4's `import` graph and `@[simp]`/`@[ext]` tactic annotations via `lake env printPaths` + Lean metaprogramming to extract theorem-level dependencies.
- **Storage**: NetworkX `DiGraph` in-memory. Nodes = theorems/definitions/lemmas (with attributes: module, type signature, embedding vector). Edges = `uses` (theorem A's proof references lemma B).
- **Queries for gap detection**:
  - Analogical gaps: "For each theorem about `Group`, find structurally similar theorems about `Ring`/`Module` by comparing neighborhood topology + embedding similarity."
  - Significance scoring: PageRank / betweenness centrality as proxy for theorem importance.
  - Dependency impact: `len(nx.descendants(G, node))` estimates how many theorems a new result could unblock.
- **Why not Neo4j**: ~210K nodes fits comfortably in memory. NetworkX avoids external service dependency, simplifies reproducibility (Tier 1), and is sufficient for the graph algorithms needed.

### 5.2 Counter-Example Filter

Before investing API compute on proof attempts, filter out likely-false conjectures:

1. **Small-case instantiation**: For conjectures involving parametric types (e.g., groups of order n), test on small concrete instances (n = 1..10) using Lean's `#eval` or `decide`.
2. **Type-specific checks**: For algebraic conjectures, test on known small structures (ℤ/2ℤ, ℤ/3ℤ, S₃, Klein four-group, etc.).
3. **Quick tactic attempt**: Run `aesop` / `omega` / `simp` with a 5-second timeout. If it finds a counterexample or disproves the goal, discard.
4. **Pass rate target**: Filter should eliminate ≥30% of generated conjectures to justify its compute cost. Measure in Phase 2 pilot.

### 5.3 Self-Repair Loop (Proof Failure → Feedback)

When a proof attempt fails, Lean 4 returns structured error messages. These are valuable signal, not just noise:

1. **Error extraction**: Parse Lean compiler output for: unsolved goals, type mismatches, unknown identifiers, tactic failures.
2. **Feedback to LLM**: Construct a repair prompt: original conjecture + attempted proof + Lean error messages + relevant Mathlib context.
3. **Retry budget**: Up to 3 repair iterations per conjecture. Each iteration feeds the previous error back to the LLM.
4. **Escalation**: If local 7B model fails all 3 iterations, escalate to API model for one final attempt before marking as "unresolved."
5. **Rationale**: APOLLO (2025) demonstrated that iterative LLM + compiler feedback achieves 84.9% on miniF2F with sub-8B models. This loop is the core mechanism.

### Reproducibility Policy

Fully open-source intent creates tension with closed API dependency. To address this:

1. **Model version pinning**: All API calls log the exact model version used (e.g., `deepseek-prover-v2-0131`, `claude-3-opus-20240229`). Pin versions for the duration of each experiment run.
2. **Full request/response logging**: Every LLM API call is logged with: timestamp, model version, full prompt, full response, token counts, temperature, and any other parameters. Logs are published as part of the open-source release.
3. **Determinism where possible**: Set temperature=0 for all proof generation calls. For conjecture generation (where diversity matters), fix seed when the API supports it, and log the seed otherwise.
4. **Reproducibility tiers**: Document clearly in the paper:
   - **Tier 1 (fully reproducible)**: Lean 4 verification, gap detection, novelty checking, staleness detection — all local, deterministic.
   - **Tier 2 (reproducible with same API access)**: Conjecture generation, proof attempts — reproducible given same model version + logged parameters.
   - **Tier 3 (results reproducible, not exact outputs)**: If API versions are deprecated, results may vary but aggregate statistics (rediscovery rate, novelty rate) should be comparable.
5. **Cached inference artifacts**: Publish all generated conjectures, proof attempts, and intermediate results so that downstream analysis can be reproduced without re-running API calls.

---

## 6. Revised Timeline (NeurIPS 2026 Target)

### Phase 1: Foundation + Go/No-Go (Weeks 1-6, Feb-mid Mar 2026)

- **Week 1-2**: Setup Lean 4 + Mathlib4 algebra subset; Python orchestrator skeleton; Mathlib graph + embedding extraction
- **Week 3-4**: Implement Analogical Gap detector for algebra (group ↔ ring ↔ module analogies)
- **Week 4-5**: Compute cost pilot (10 gaps) + auto-formalization pilot (20 theorems)
- **Week 5-6**: Go/no-go evaluation against normalized criteria (detection rate, top-20 precision)
  - **Go** → Phase 2
  - **No-go** → Pivot to Formalization Gaps, re-evaluate in 2 weeks

**Buffer**: 1 week added vs. original. Lean/Mathlib setup and embedding extraction are the highest-uncertainty tasks in the project; underestimating them would cascade into every subsequent phase.

### Phase 2: Core Loop (Weeks 7-11, mid Mar-mid Apr 2026)

- **Week 7-8**: Conjecture generator (LLM → Lean 4 statement); proof engine (local 7B + API fallback)
- **Week 8-9**: Verification pipeline (Lean 4 type-check, no sorry/admit); novelty checker (multi-layer)
- **Week 10-11**: Full loop integration; first end-to-end discovery cycles
- **Milestone**: System completes 10+ successful discovery cycles autonomously

**Buffer**: 1 week added. Integration of Python ↔ Lean bridge + API orchestration has high coupling risk.

### Phase 3: Curiosity + Evaluation (Weeks 12-16, mid Apr-mid May 2026)

- **Week 12-13**: Implement 3 curiosity formulations + staleness detection (CUSUM with autocorrelation handling)
- **Week 13-14**: Rediscovery experiment (cutoff-based, with memorization pre-test)
- **Week 14-15**: Ablation studies; novel discovery extended run
- **Week 15-16**: Results analysis, statistical validation, reproducibility artifact packaging
- **Milestone**: Experimental results sufficient for paper

**Buffer**: 1 week added. Statistical validation (power analysis, effect sizes, multiple testing correction) requires dedicated time separate from running experiments.

### Phase 4: Paper (Weeks 17-19, mid May-early Jun 2026)

- **Week 17**: Figures, tables, architecture diagrams
- **Week 18**: Paper draft (full)
- **Week 19**: Revision, internal review, submission to NeurIPS 2026

**Note**: Total timeline expanded from 16 to 19 weeks (+3 weeks buffer). This is more realistic for a project combining Lean/Mathlib development, LLM integration, and rigorous statistical evaluation. If NeurIPS deadline is earlier than expected, Phase 4 can compress by parallelizing draft writing with late Phase 3 experiments.

### Fallback: If NeurIPS deadline missed → continue to ICLR 2027

- Add Generalization Gaps (second gap type)
- Extended novel discovery runs
- Deeper ablation analysis
- Staleness simulation validation study
- Submit by Sep 2026

---

## 7. Key Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Knowledge graph | NetworkX in-memory (not Neo4j) | ~210K nodes fits in RAM; no external dependency; Tier 1 reproducible |
| Counter-example filter | Small-case + quick tactic before proof | Saves API cost by filtering likely-false conjectures early |
| Self-repair loop | 3 iterations local → 1 API escalation | APOLLO-style compiler feedback; maximizes local compute before API spend |
| MVP gap type | Analogical (algebra) | Strongest novelty claim + rich structure in Mathlib |
| Proof engine | Hybrid (local 7B + API) | M2 Pro constraint; cost-controlled |
| Curiosity | 3-way comparison | Strongest paper contribution |
| Go/no-go | Normalized metrics (detection rate, top-20 precision) | Domain-size independent; avoids arbitrary absolute thresholds |
| Data leakage | Cutoff-based + 20-trial Wilson CI memorization test | Statistically robust contamination detection |
| Staleness | CUSUM + Mann-Whitney + autocorrelation + Holm-Bonferroni | Handles temporal dependence and multiple testing |
| Novelty check | Normalize → defEq → bi-implication → LLM (4 layers) | Reduces false negatives from defEq-only approach |
| Contribution emphasis | Discovery results | System is means, discoveries are the measure |
| Open source | Full (code + data + scripts) + reproducibility tiers | API dependence managed via version pinning, logging, cached artifacts |

---

## 8. Risk Registry (Updated)

| Risk | Severity | Mitigation | Fallback |
|------|----------|------------|----------|
| Gap detector finds only trivial gaps | Critical | Automated non-triviality criteria; calibrate against Mathlib stats | Pivot to Formalization Gaps |
| API costs exceed budget | High | Pilot study in Phase 1; aggressive local model usage | Reduce iteration count; narrower domain |
| Auto-formalization accuracy too low | High | Pilot in Phase 1; fallback to direct Lean generation | Skip NL intermediate step |
| Proof success rate too low for novel conjectures | High | Counter-example filter + self-repair loop (3 local + 1 API) + near-known analogues | Focus on lemma-level discoveries |
| NeurIPS deadline missed | Medium | ICLR 2027 fallback; workshop paper option | 19-week timeline with buffers accounts for this |
| API reproducibility gap | Medium | Version pinning, full logging, cached artifacts, 3-tier policy | Tier 3 fallback if API versions deprecated |
| Lean 4 / Mathlib learning curve | Medium | Intermediate experience; Lean Zulip community | Budget extra time in Phase 1 |
| Discovered theorems are trivial | Medium | Composite triviality score; Mathlib PR validation | Reframe as "gap detection" contribution |

---

## 9. Open Items

1. Identify DeepSeek-Prover-V2 training data cutoff date (needed for P0-2)
2. Select specific local 7B model for proof attempts (candidates: DeepSeek-Prover-V2-7B, Llemma-7B)
3. Determine LLM for conjecture generation (Claude vs GPT-4 vs Gemini — evaluate on math creativity)
4. Set up Mathlib4 algebra module dependency graph extraction tooling
5. Establish API budget ceiling (monthly)
