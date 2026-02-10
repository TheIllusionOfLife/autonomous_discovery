# Autonomous Mathematical Discovery via Knowledge-Gap-Driven Curiosity

## Project Brief — February 2026

> **Document 1 of 3** | Role: **Initial Proposition**
>
> This is the original project brief proposing the research direction, system architecture, experimental plan, and timeline. It serves as the foundational vision document.
>
> **Next**: [unified-review.md](unified-review.md) — Research review identifying issues and risks in this brief.

---

## Thesis

All existing AI-for-science systems — AI Scientist v2, Kosmos, AlphaEvolve, AlphaProof, A-Lab — are **convergent**: they optimize toward human-specified goals. We propose the first **divergent** scientific discovery system: one that autonomously identifies mathematical knowledge gaps, formulates conjectures to fill them, proves or refutes those conjectures via formal verification, and iterates — with no human-specified objective. The system is driven by **intrinsic curiosity** defined as the pursuit of knowledge gaps in a formal mathematical knowledge base.

**Core claim**: By shifting from problem-solving to problem-finding, we remove the human bottleneck in AI-driven scientific discovery. The system runs autonomously until it stales — at which point principled staleness detection triggers human review.

---

## 1. The Problem: AI Science Has a Problem-Finding Problem

### The bottleneck in current AI-for-science

Every deployed AI discovery system requires a human to specify what to work on:

| System | Year | What Human Must Provide | What AI Does |
|--------|------|------------------------|--------------|
| AI Scientist v2 (Sakana) | 2025 | Research direction + templates | Generates hypotheses, runs experiments, writes papers |
| Kosmos (FutureHouse) | 2025 | Research objective + dataset | Autonomous exploration within given scope |
| AlphaEvolve (DeepMind) | 2025 | Specific problem to optimize | Evolves algorithms via LLM + evaluation |
| AlphaProof (DeepMind) | 2024 | Competition problems to prove | RL-based theorem proving in Lean |
| AI-Researcher (HKU) | 2025 | Domain specification | End-to-end paper generation |
| A-Lab (Berkeley) | 2025 | Materials property targets | Closed-loop synthesis + characterization |
| Robot Scientist (Adam/Eve) | 2004-present | Biological domain constraints | Automated hypothesis testing |

**The pattern**: Humans ask, AI answers. This is powerful but fundamentally bounded by human bandwidth, imagination, and domain knowledge. No system asks its own questions.

### What we propose

A system that:
1. **Identifies** knowledge gaps in a formal mathematical knowledge base (Mathlib4, 210K+ theorems)
2. **Generates** conjectures to fill those gaps, ranked by a curiosity function
3. **Proves** (or refutes) conjectures using state-of-the-art neural theorem provers
4. **Verifies** results via independent formal verification (Lean 4 type-checker)
5. **Evaluates** its own novelty production rate and detects staleness
6. **Iterates** indefinitely until staleness is detected or humans intervene

This is the first system where the AI decides **what questions to ask**, not just how to answer them.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS DISCOVERY LOOP                 │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  KNOWLEDGE   │───→│    GAP       │───→│  CONJECTURE  │  │
│  │  BASE        │    │  DETECTOR    │    │  GENERATOR   │  │
│  │  (Mathlib4 + │    │  (Curiosity  │    │  (LLM-based) │  │
│  │   own work)  │    │   Function)  │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ↑                                       │           │
│         │                                       ↓           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   NOVELTY    │←───│   VERIFIER   │←───│    PROOF     │  │
│  │   CHECKER    │    │  (Lean 4     │    │   ENGINE     │  │
│  │  (Mathlib +  │    │   type-check)│    │  (DeepSeek/  │  │
│  │   arXiv)     │    │              │    │   APOLLO)    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                                    │
│         ↓                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              META-EVALUATOR (Staleness Detection)     │   │
│  │  Monitors: novelty rate, compression progress,        │   │
│  │  surprise decay, repetition patterns                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ↓                                   │
│                  [CONTINUE or ALERT HUMAN]                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Knowledge Base

**Foundation**: Mathlib4 (210K+ formalized theorems, 100K+ definitions, 8K modules)

**Representation**: The knowledge base maintains three views:
- **Graph view**: Dependency graph of theorems, definitions, and lemmas (from Mathlib's importGraph)
- **Embedding view**: Vector embeddings of theorem statements for semantic similarity
- **Structural view**: Categorized by mathematical domain (algebra, analysis, topology, combinatorics, etc.)

**Updates**: When the system proves a new theorem, all three views are updated. The new theorem becomes part of the knowledge base for future gap detection.

### 2.2 Gap Detector (The Curiosity Engine)

This is the core innovation. The Gap Detector identifies regions of the knowledge base where understanding is incomplete. It uses five gap-detection heuristics:

#### Gap Type 1: Analogical Gaps
**Definition**: Theorem T exists for mathematical structure A. Structure B is "analogous" to A (e.g., Ring and Module, ℝ and ℂ, finite and infinite). No analogue of T exists for B.

**Detection algorithm**:
1. Embed all mathematical structures (types/classes) in Mathlib
2. For each pair (A, B) with high structural similarity
3. For each theorem about A, check if an analogous theorem about B exists
4. Missing analogues are gaps

**Example**: A commutativity theorem exists for addition on ℕ but no formalized analogue exists for some algebraic structure with similar properties.

#### Gap Type 2: Completeness Gaps
**Definition**: A family of theorems covers cases C₁, C₂, ..., Cₖ. Case Cₖ₊₁ is a natural extension but is missing.

**Detection algorithm**:
1. Identify parametric families of theorems (theorems with similar structure but different parameters)
2. Extract the parameter space (e.g., dimensions, cardinalities, algebraic properties)
3. Check for missing parameter values

**Example**: A property is proven for groups of specific orders but not for the next natural case.

#### Gap Type 3: Connection Gaps
**Definition**: Two subfields of Mathlib share structural patterns but have no formal bridge theorems connecting them.

**Detection algorithm**:
1. Compute cross-domain embedding similarity for theorems in different Mathlib modules
2. Identify pairs of theorems from different domains with high semantic similarity
3. Check if any formal dependency (bridge theorem) connects them
4. High similarity + no dependency = potential connection gap

**Example**: An algebraic identity and a combinatorial identity that look structurally similar but have no formal relationship in Mathlib.

#### Gap Type 4: Generalization Gaps
**Definition**: Theorem T holds for a specific type (e.g., ℝ², Fin n, a particular group). It may generalize to a broader type.

**Detection algorithm**:
1. Identify theorems with "overly specific" type signatures
2. Check if the proof techniques would extend to more general types
3. Score by the breadth of the potential generalization

**Example**: A theorem about ℝ² that likely holds in arbitrary inner product spaces.

#### Gap Type 5: Formalization Gaps
**Definition**: Known mathematical results (from arXiv, textbooks, OEIS) that aren't yet formalized in Mathlib.

**Detection algorithm**:
1. Compare Mathlib's theorem inventory against external mathematical databases
2. Use LLM to identify well-known results that should be in Mathlib but aren't
3. Prioritize results that would serve as useful lemmas for other gaps

### 2.3 Curiosity Scoring Function

Each detected gap receives a curiosity score:

```
curiosity(gap) = α · novelty(gap) + β · tractability(gap) + γ · significance(gap)
```

Where:
- **novelty(gap)**: Embedding distance from nearest existing theorem. Higher = more novel.
- **tractability(gap)**: Estimated probability of successful proof, based on:
  - Proof complexity of structurally similar theorems
  - Availability of relevant tactics and lemmas
  - LLM confidence in generating a proof sketch
- **significance(gap)**: Structural importance, measured by:
  - Number of other gaps that depend on this one
  - Centrality in the knowledge graph
  - Breadth of potential generalization

**Initial weights**: α = β = γ = 1/3 (equal). Can be tuned via ablation study.

**Selection strategy**: Prioritize gaps in the "sweet spot" — novel enough to be interesting, tractable enough to be provable, significant enough to matter. Avoid trivial gaps (low novelty) and impossible gaps (low tractability).

### 2.4 Conjecture Generator

**Input**: A knowledge gap with its context (surrounding theorems, relevant definitions, gap type)

**Process**:
1. LLM receives the gap description + relevant Mathlib context
2. Generates candidate conjecture in natural language
3. Translates conjecture to Lean 4 statement
4. Lean compiler checks that the statement is well-typed (syntactically valid)
5. Quick counterexample search (test on small cases) to filter obviously false conjectures

**Output**: A well-typed Lean 4 theorem statement ready for proof attempt

**LLM choice**: A frontier model (Claude, GPT-4, Gemini) for conjecture generation, as this requires creative mathematical reasoning. Can also fine-tune on Mathlib theorem statement patterns.

### 2.5 Proof Engine

**Primary**: DeepSeek-Prover-V2-671B (88.9% on miniF2F, 49/658 on PutnamBench)
**Secondary**: APOLLO framework for iterative repair (84.9% on miniF2F with sub-8B models)
**Fallback**: Lean 4 automated tactics (aesop, omega, simp, decide)

**Pipeline**:
1. DeepSeek-Prover-V2 generates initial proof attempt
2. If type-check fails → APOLLO iterative repair loop (LLM + Lean compiler feedback)
3. If still failing → decompose into subgoals, attempt each separately
4. If all approaches fail within compute budget → mark conjecture as "unresolved" and move on

**Compute budget**: Each conjecture gets a fixed token/time budget. Prevents infinite loops on intractable conjectures.

### 2.6 Verifier (External, Independent)

**The prover-verifier separation principle**: The system that generates proofs (LLM) must be architecturally independent from the system that verifies them (Lean 4 type-checker).

This is the key safety property. Lean 4's type-checker is deterministic and correct by construction. If a proof type-checks, it is mathematically valid. No LLM hallucination can bypass this.

**Verification pipeline**:
1. Lean 4 type-checker verifies the complete proof
2. All imported lemmas must themselves be verified
3. No `sorry` or `admit` placeholders allowed
4. Proof is compiled to a Lean `.olean` file for reproducibility

### 2.7 Novelty Checker

After verification, the system checks whether the result is genuinely new:

1. **Mathlib check**: Is this theorem (or a trivially equivalent one) already in Mathlib?
2. **Own-work check**: Has the system already proven this or something equivalent?
3. **External check**: Search arXiv for related results (using LLM to compare)
4. **Triviality check**: Is the proof shorter than N lines using only basic tactics? (If so, likely trivial)

Results classified as: **Novel** (not in any database), **Rediscovery** (known but independently derived), **Trivial** (direct application of existing results), **Duplicate** (already in knowledge base).

### 2.8 Meta-Evaluator (Staleness Detection)

The system monitors four staleness indicators:

1. **Novelty rate**: Number of Novel results per unit time. Tracked as a moving average.
2. **Compression progress**: Does adding new results improve the system's ability to compress its knowledge? (Measured by: can existing proofs be shortened using new lemmas?)
3. **Surprise decay**: How often do proof attempts succeed on the first try? If success rate approaches 100%, the system is only attempting trivial gaps.
4. **Repetition index**: Semantic similarity between recent outputs. If new results cluster tightly with previous results, the system is stuck in a local region.

**Staleness threshold**: If 3 of 4 indicators are declining for N consecutive cycles, the system alerts a human reviewer.

**Recovery strategies** (attempted before alerting):
- Switch to a different gap type (e.g., from analogical gaps to connection gaps)
- Increase the novelty weight in the curiosity function
- Expand the knowledge base scope (import additional Mathlib modules)

---

## 3. The Key Differentiator: A Comparison

| Dimension | AI Scientist v2 | Kosmos | AlphaProof | AlphaEvolve | **This System** |
|-----------|-----------------|--------|------------|-------------|-----------------|
| Problem finding | No | Partial | No | No | **Yes (core contribution)** |
| Problem solving | Yes | Yes | Yes | Yes | Yes |
| Verification | Peer review (noisy) | Human validation | Lean (formal) | Evaluation function | **Lean (formal)** |
| Domain | ML research | Cross-domain | Math competition | Algorithms | **Formal math (extensible)** |
| Autonomy level | Needs research direction | Needs objective | Needs problems | Needs problems | **Fully autonomous** |
| Runs indefinitely | No (single paper) | No (12hr runs) | No (per-problem) | No (per-problem) | **Yes (until staleness)** |
| Staleness detection | N/A | N/A | N/A | N/A | **Yes (novel contribution)** |
| Curiosity function | N/A | N/A | N/A | N/A | **Yes (novel contribution)** |

---

## 4. Experimental Plan

### Experiment 1: Rediscovery (Validation)
**Goal**: Demonstrate the system can independently rediscover known results.

**Protocol**:
1. Remove N theorems from Mathlib (selected from diverse subfields)
2. Run the system with the modified knowledge base
3. Measure how many removed theorems the system independently rediscovers
4. Compare: curiosity-driven exploration vs. random gap exploration

**Success criteria**: Rediscovery rate significantly above random baseline.

**Why this works**: This is a controlled experiment. We know the ground truth (the removed theorems exist), so we can objectively measure the system's ability to find and fill knowledge gaps.

### Experiment 2: Novel Discovery (Stretch Goal)
**Goal**: Demonstrate the system can discover theorems NOT currently in Mathlib.

**Protocol**:
1. Run the system on the full Mathlib knowledge base
2. Collect all verified results classified as "Novel"
3. Have human mathematicians evaluate novelty and significance
4. Submit non-trivial results to Mathlib as PRs (ultimate validation)

**Success criteria**: At least one non-trivial, human-validated novel theorem.

### Experiment 3: Ablation Studies
**Goal**: Validate design choices.

**Ablations**:
- **No curiosity function** (random gap selection): Does curiosity improve discovery quality?
- **Single gap type only** (e.g., only analogical gaps): Does multi-type gap detection help?
- **No staleness detection**: Does the system degrade without meta-evaluation?
- **Curiosity weight variations** (α, β, γ): Which component matters most?

### Experiment 4: Staleness Analysis
**Goal**: Characterize the system's discovery dynamics over time.

**Protocol**:
1. Run the system for an extended period (e.g., 10K+ iterations)
2. Plot novelty rate, compression progress, surprise, and repetition over time
3. Identify when staleness occurs and what triggers it
4. Evaluate whether recovery strategies (gap type switching, etc.) extend productive runtime

### Baselines
1. **Random exploration**: Select gaps uniformly at random
2. **Human-guided**: Human mathematician selects gaps (upper bound on quality)
3. **AlphaProof-style**: Given a fixed set of conjectures, prove them (no gap detection)
4. **Conjecture-only**: Generate conjectures without gap detection (no curiosity structure)

---

## 5. Risk Assessment

### Critical Risk: The Curiosity Function May Not Find Non-Trivial Gaps
**Risk level**: HIGH (3-4/5)
**Time to test**: 2-3 months
**Mitigation**: Test the gap detector in isolation first. Give it access to Mathlib, ask it to identify gaps, and have a mathematician evaluate whether the identified gaps are interesting. This is the go/no-go experiment.
**If it fails**: Simplify the gap taxonomy. Start with only formalization gaps (known results not yet in Mathlib — these are guaranteed to be real gaps).

### High Risk: LLM Proof Generation May Not Scale to Novel Conjectures
**Risk level**: MEDIUM-HIGH (3/5)
**Time to test**: 3-4 months
**Mitigation**: Start with conjectures that are "near" known results (small generalizations, analogues). Use APOLLO's iterative repair to maximize proof success rate. Leverage DeepSeek-Prover-V2-671B for maximum capability.
**If it fails**: Reduce conjecture ambition. Focus on lemma-level discoveries (useful intermediate results) rather than major theorems.

### Medium Risk: Novelty Checker May Miss Duplicates
**Risk level**: MEDIUM (2-3/5)
**Time to test**: 1-2 months
**Mitigation**: Use multiple novelty-checking strategies (exact match, semantic similarity, LLM comparison). Accept some false positives initially; human review catches them.

### Medium Risk: Staleness Detection Thresholds
**Risk level**: MEDIUM (2-3/5)
**Time to test**: 4-6 months (needs extended runs)
**Mitigation**: Track multiple metrics. Conservative thresholds initially (alert early rather than late).

### Low Risk: Verification Correctness
**Risk level**: LOW (1/5)
**Mitigation**: Lean 4 type-checker is deterministic. This component is reliable by construction.

### Go/No-Go Decision Point
**Month 2-3**: Run the gap detector on Mathlib. If it identifies gaps that a mathematician judges as "interesting and non-trivial," proceed. If all identified gaps are trivial or nonsensical, pivot to a simpler gap taxonomy or change domains.

---

## 6. Component Selection

| Component | Tool | Rationale |
|-----------|------|-----------|
| Knowledge Base | Mathlib4 (Lean 4) | 210K+ theorems, formal, actively maintained |
| Embeddings | LLM embeddings of theorem statements | Enables semantic similarity for gap detection |
| Gap Detection | Custom (LLM + graph analysis) | Novel contribution — no existing tool |
| Conjecture Generation | Frontier LLM (Claude/GPT-4/Gemini) | Requires creative mathematical reasoning |
| Auto-formalization | DeepSeek-Prover-V2 or custom fine-tune | Translates natural language to Lean 4 |
| Proof Engine | DeepSeek-Prover-V2-671B + APOLLO | Best available neural theorem provers |
| Verification | Lean 4 type-checker | Deterministic, correct by construction |
| Novelty Check | Mathlib search + arXiv search + LLM | Multi-layered novelty validation |
| Staleness Detection | Custom metrics pipeline | Novel contribution — no existing tool |
| Orchestration | LLM-based agent (the "brain") | Coordinates all components |

---

## 7. Paper Outline

**Target venue**: NeurIPS 2026 or ICLR 2027

### Proposed Structure

1. **Introduction** (1.5 pages)
   - The problem-finding gap in AI-for-science
   - Our contribution: autonomous, curiosity-driven mathematical discovery
   - Key results preview

2. **Related Work** (1.5 pages)
   - AI for scientific discovery (AI Scientist, Kosmos, AlphaEvolve, etc.)
   - Neural theorem proving (AlphaProof, DeepSeek-Prover, APOLLO)
   - Intrinsic motivation and artificial curiosity (Schmidhuber, Stanley, etc.)
   - Position: we bridge AI-for-science and intrinsic motivation

3. **System Architecture** (2 pages)
   - Full pipeline overview
   - Knowledge base representation
   - The autonomous discovery loop

4. **Knowledge-Gap-Driven Curiosity** (2 pages)
   - Gap taxonomy (5 types)
   - Gap detection algorithms
   - Curiosity scoring function
   - Theoretical motivation (connection to compression progress)

5. **Staleness Detection** (1 page)
   - Metrics: novelty rate, compression progress, surprise, repetition
   - Recovery strategies
   - When to alert humans

6. **Experiments** (3 pages)
   - Rediscovery experiment + results
   - Novel discovery results
   - Ablation studies
   - Staleness dynamics analysis
   - Baselines comparison

7. **Discussion** (1 page)
   - Implications for autonomous science
   - Limitations and future directions (cross-domain, non-mathematical)
   - The path from math to general scientific discovery

8. **Conclusion** (0.5 pages)

### Estimated length: ~13 pages + appendix

---

## 8. Development Timeline

### Phase 1: Foundation (Months 1-2)
- Set up Lean 4 + Mathlib4 development environment
- Implement knowledge base representation (graph + embeddings)
- Build basic gap detector (start with analogical gaps only)
- **Go/no-go milestone**: Gap detector identifies non-trivial gaps

### Phase 2: Core Loop (Months 3-4)
- Implement conjecture generator (LLM + Lean formalization)
- Integrate proof engine (DeepSeek-Prover-V2 + APOLLO)
- Build verification pipeline
- Implement novelty checker
- **Milestone**: System completes one full discovery cycle

### Phase 3: Full System (Months 5-6)
- Implement all 5 gap types
- Build curiosity scoring function
- Implement staleness detection
- Run rediscovery experiment
- **Milestone**: Rediscovery results validate the approach

### Phase 4: Evaluation & Paper (Months 7-8)
- Extended runs for novel discovery
- Ablation studies
- Staleness dynamics analysis
- Write paper
- **Milestone**: Paper submission

### Total estimated timeline: 8 months

---

## 9. Open Questions

1. **System name**: TBD — should reflect autonomous curiosity-driven discovery
2. **LLM selection for conjecture generation**: Need to evaluate Claude vs. GPT-4 vs. Gemini vs. open-source on mathematical creativity tasks
3. **Compute budget**: How much compute per conjecture? Need to balance exploration breadth vs. proof depth
4. **Cross-domain potential**: After math, which domain next? (Candidates: formal verification of code, computational physics, automated chemistry)
5. **Curiosity weight tuning**: Should α, β, γ be fixed or adaptive?
6. **Scalability**: How does the system behave as the knowledge base grows? Does gap detection become harder or easier?

---

## 10. Why This Matters

If this system works — even partially — it demonstrates something profound: that the scientific process of *asking questions* can be automated, not just the process of *answering them*.

Current AI systems accelerate science linearly: one human asks, AI answers faster. An autonomous problem-finding system could accelerate science exponentially: the AI both asks and answers, exploring territory no human thought to explore.

The constraint to formally verifiable domains (starting with mathematics) is both a practical necessity and a philosophical feature. In domains where truth is decidable, we can trust the system's outputs completely. The Lean type-checker doesn't care whether the proof was generated by a human or an AI — it either type-checks or it doesn't.

Starting with mathematics, the system can later extend to any domain with formal verification: software correctness, protocol verification, computational physics, and eventually — as verification methods improve — to broader scientific domains.

The vision is simple: **an AI that is curious about the world, pursues understanding autonomously, and produces formally verified knowledge as output.** Not because a human told it to, but because knowledge gaps exist and filling them is what the system does.
