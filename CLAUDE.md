# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Autonomous mathematical discovery system that identifies knowledge gaps in Mathlib4, generates conjectures to fill them, proves conjectures via formal verification, and iterates — driven by intrinsic curiosity with no human-specified objective. Targeting NeurIPS 2026 (May 15 deadline) with ICLR 2027 fallback.

**Current state**: Planning phase. No code yet — only specification documents.

## Document Chain

Three documents form a sequential chain (read in order):

1. `autonomous-math-discovery-project-brief.md` — Original vision: architecture, gap taxonomy (5 types), experimental plan
2. `unified-review.md` — Critical review identifying 11 issues (P0-P3), partially in Japanese
3. `project-spec.md` — **Authoritative spec** addressing all review issues. Contains final architecture, timeline, and design decisions. When documents conflict, this one wins.

## Planned Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Formal verification | Lean 4 + Mathlib4 | Algebra subset (groups, rings, modules) |
| Orchestration | Python | Bridges to Lean 4 via subprocess/lake |
| Knowledge graph | NetworkX DiGraph | ~210K nodes in-memory, not Neo4j |
| Embeddings | LLM embeddings of theorem statements | For semantic similarity in gap detection |
| Proof engine | Local 7B model + API fallback | DeepSeek-Prover-V2-7B candidates; API for complex proofs |
| Conjecture generation | Frontier LLM API (Claude/GPT-4/Gemini) | Creative math reasoning |
| Compute | Mac Mini M2 Pro (local) + API (heavy inference) | 671B model impossible locally |

## Architecture (Discovery Loop)

```text
Knowledge Base → Gap Detector → Conjecture Generator → Counter-Example Filter
     ↑                                                         ↓
Novelty Checker ← Verifier (Lean 4) ← Self-Repair Loop ← Proof Engine

Meta-Evaluator (CUSUM + Mann-Whitney) → [CONTINUE or ALERT HUMAN]
```

Key subsystems:
- **Curiosity scorer**: 3 formulations compared via ablation (linear combination, information gain, compression progress)
- **Novelty checker**: 4-layer pipeline (normalize → defEq → bi-implication → LLM comparison)
- **Self-repair loop**: 3 local retries with Lean error feedback → 1 API escalation
- **Staleness detection**: CUSUM change-point + Mann-Whitney with autocorrelation handling and Holm-Bonferroni correction

## Claim-Safety Language Policy

All documents and the paper MUST follow these rules:
- Novelty claims prefixed with "to our knowledge"
- "Autonomous" always qualified: "autonomous with respect to problem selection"
- "Discovery" reserved for results classified Novel AND verified by Lean; otherwise use "results" or "rediscoveries"
- Never use "first" in isolation; always "first [specific scope] to our knowledge, as of [date]"
- Never use "fully autonomous" (hyperparameters are human-set)

## Timeline (14 weeks from Feb 10, 2026)

- **Phase 1 (Weeks 1-5)**: Foundation + Go/No-Go — Lean 4 setup, graph extraction, gap detector, pilots
- **Phase 2 (Weeks 6-9)**: Core Loop — conjecture generator, proof engine, full loop integration
- **Phase 3 (Weeks 10-12)**: Evaluation — curiosity ablations, rediscovery experiment, novel discovery
- **Phase 4 (Weeks 13-14)**: Paper writing and submission

## Contribution Ladder

| Level | What's needed | Venue |
|-------|--------------|-------|
| L1 (minimum) | System runs end-to-end | Workshop paper |
| L2 (solid) | Curiosity-driven > random (p < 0.05) | NeurIPS/ICLR main |
| L3 (strong) | L2 + novel theorem submitted to Mathlib | Strong accept |
| L4 (exceptional) | Multiple novel theorems + 1K+ cycle dynamics | Best paper candidate |

## Key Design Decisions

- **Analogical gaps in algebra** as MVP gap type (strongest novelty claim + rich Mathlib coverage)
- **Cutoff-based theorem selection** for data leakage mitigation (post-2024-08 Mathlib commits)
- **20-trial Wilson CI memorization test** before rediscovery experiments
- **Normalized go/no-go metrics**: detection rate >= 5%, top-20 precision >= 60%, minimum 20 non-trivial gaps
- **Reproducibility tiers**: Tier 1 (fully local/deterministic), Tier 2 (same API access), Tier 3 (aggregate stats comparable)
