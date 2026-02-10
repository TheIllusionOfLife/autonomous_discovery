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
| Openness | Fully open-source (code, data, experiment scripts) | Reproducibility is first-class |

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
2. **Memorization pre-test**: Before the experiment, directly prompt the LLM with the theorem statement and ask it to prove it. If it succeeds with high confidence (>80% pass rate across 5 attempts), classify as "potentially memorized" and exclude or flag.
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

**Go criteria**: Gap detector identifies ≥50 gaps in the algebra domain that satisfy all 4 criteria above. If <50, iterate on gap detection heuristics. If after 2 iterations still <50, pivot to Formalization Gaps as fallback.

---

## 3. Addressing P1 Issues (Phase 1-2)

### P1-1: Novelty Judgment — defEq Layer

Add a Lean 4-based equivalence check:
1. For each verified theorem T_new, attempt `Lean.Meta.isDefEq` against all existing theorems in the relevant Mathlib module
2. If defEq with any existing theorem → classify as Duplicate
3. If not defEq but embedding similarity >0.95 → flag for manual review (or LLM-based deeper comparison)
4. Triviality: Replace line-count heuristic with composite score: {tactic_count, max_tactic_depth, unique_lemmas_used, proof_term_size}

### P1-2: Staleness Detection — Statistical Rigor

Replace "3/4 indicators declining for N cycles" with:
1. **CUSUM (Cumulative Sum)** change point detection on novelty rate time series
2. **Sliding window** significance test: compare last W cycles against the preceding W cycles using Mann-Whitney U test
3. Staleness declared when CUSUM detects a shift AND the significance test rejects H0 (no decline) at p < 0.05
4. N is not a fixed hyperparameter — it emerges from the statistical test

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
┌──────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS DISCOVERY LOOP                      │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │  KNOWLEDGE   │───→│  ANALOGICAL  │───→│  CONJECTURE  │        │
│  │  BASE        │    │  GAP         │    │  GENERATOR   │        │
│  │  (Mathlib4   │    │  DETECTOR    │    │  (Claude/    │        │
│  │   Algebra +  │    │  (Embedding  │    │   GPT-4 API) │        │
│  │   own work)  │    │   + Graph)   │    │              │        │
│  └──────────────┘    └──────────────┘    └──────────────┘        │
│         ↑                                       │                 │
│         │            ┌──────────────┐           ↓                 │
│  ┌──────────────┐    │  CURIOSITY   │    ┌──────────────┐        │
│  │   NOVELTY    │    │  SCORER      │    │    PROOF     │        │
│  │   CHECKER    │    │  (3 variants │    │   ENGINE     │        │
│  │  (defEq +   │    │   compared)  │    │  (Local 7B + │        │
│  │   embedding) │    └──────────────┘    │   API heavy) │        │
│  └──────────────┘           ↑            └──────────────┘        │
│         ↑                   │                   │                 │
│         │                   │                   ↓                 │
│         └───────────────────┼────────── VERIFIER (Lean 4)        │
│                             │                                     │
│  ┌──────────────────────────┴─────────────────────────────────┐  │
│  │         META-EVALUATOR (CUSUM + Statistical Tests)          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                          │                                        │
│                          ↓                                        │
│                  [CONTINUE or ALERT HUMAN]                        │
└──────────────────────────────────────────────────────────────────┘

Infra: Python orchestrator ←→ Lean 4 (subprocess/lake)
Local: Mac Mini M2 Pro (orchestration, small model inference, Lean)
API:   DeepSeek / Claude / GPT-4 (conjecture gen, heavy proof attempts)
```

---

## 6. Revised Timeline (NeurIPS 2026 Target)

### Phase 1: Foundation + Go/No-Go (Weeks 1-5, Feb-Mar 2026)

- **Week 1-2**: Setup Lean 4 + Mathlib4 algebra subset; Python orchestrator skeleton; Mathlib graph + embedding extraction
- **Week 2-3**: Implement Analogical Gap detector for algebra (group ↔ ring ↔ module analogies)
- **Week 3-4**: Compute cost pilot (10 gaps) + auto-formalization pilot (20 theorems)
- **Week 4-5**: Go/no-go evaluation: ≥50 non-trivial gaps found?
  - **Go** → Phase 2
  - **No-go** → Pivot to Formalization Gaps, re-evaluate in 2 weeks

### Phase 2: Core Loop (Weeks 6-9, Mar-Apr 2026)

- **Week 6-7**: Conjecture generator (LLM → Lean 4 statement); proof engine (local 7B + API fallback)
- **Week 7-8**: Verification pipeline (Lean 4 type-check, no sorry/admit); novelty checker (defEq + embedding)
- **Week 8-9**: Full loop integration; first end-to-end discovery cycle
- **Milestone**: System completes 10+ successful discovery cycles autonomously

### Phase 3: Curiosity + Evaluation (Weeks 10-13, Apr-May 2026)

- **Week 10-11**: Implement 3 curiosity formulations + staleness detection (CUSUM)
- **Week 11-12**: Rediscovery experiment (cutoff-based, with memorization pre-test)
- **Week 12-13**: Ablation studies; novel discovery extended run
- **Milestone**: Experimental results sufficient for paper

### Phase 4: Paper (Weeks 14-16, May 2026)

- **Week 14**: Results analysis, figures, tables
- **Week 15**: Paper draft
- **Week 16**: Revision, submission to NeurIPS 2026

### Fallback: If NeurIPS deadline missed → continue to ICLR 2027

- Add Generalization Gaps (second gap type)
- Extended novel discovery runs
- Deeper ablation analysis
- Submit by Sep 2026

---

## 7. Key Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MVP gap type | Analogical (algebra) | Strongest novelty claim + rich structure in Mathlib |
| Proof engine | Hybrid (local 7B + API) | M2 Pro constraint; cost-controlled |
| Curiosity | 3-way comparison | Strongest paper contribution |
| Go/no-go | Automated metrics (4 criteria) | No mathematician; quantitative and reproducible |
| Data leakage | Cutoff-based + memorization test | Most rigorous feasible approach |
| Staleness | CUSUM + Mann-Whitney | Statistically principled |
| Novelty check | defEq + embedding + composite triviality | Addresses mathematical equivalence |
| Contribution emphasis | Discovery results | System is means, discoveries are the measure |
| Open source | Full (code + data + scripts) | Reproducibility; community validation via Mathlib PRs |

---

## 8. Risk Registry (Updated)

| Risk | Severity | Mitigation | Fallback |
|------|----------|------------|----------|
| Gap detector finds only trivial gaps | Critical | Automated non-triviality criteria; calibrate against Mathlib stats | Pivot to Formalization Gaps |
| API costs exceed budget | High | Pilot study in Phase 1; aggressive local model usage | Reduce iteration count; narrower domain |
| Auto-formalization accuracy too low | High | Pilot in Phase 1; fallback to direct Lean generation | Skip NL intermediate step |
| Proof success rate too low for novel conjectures | High | Start with near-known analogues; APOLLO repair loop | Focus on lemma-level discoveries |
| NeurIPS deadline missed | Medium | ICLR 2027 fallback; workshop paper option | Timeline above accounts for this |
| Lean 4 / Mathlib learning curve | Medium | Intermediate experience; Lean Zulip community | Budget extra time in Phase 1 |
| Discovered theorems are trivial | Medium | Composite triviality score; Mathlib PR validation | Reframe as "gap detection" contribution |

---

## 9. Open Items

1. Identify DeepSeek-Prover-V2 training data cutoff date (needed for P0-2)
2. Select specific local 7B model for proof attempts (candidates: DeepSeek-Prover-V2-7B, Llemma-7B)
3. Determine LLM for conjecture generation (Claude vs GPT-4 vs Gemini — evaluate on math creativity)
4. Set up Mathlib4 algebra module dependency graph extraction tooling
5. Establish API budget ceiling (monthly)
