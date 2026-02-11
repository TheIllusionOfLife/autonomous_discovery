# PRODUCT.md

## Purpose

`autonomous_discovery` is a research product that automates mathematical problem-finding and theorem validation in Lean/Mathlib. It is designed to discover promising gaps, generate candidate conjectures, and verify them in a repeatable loop.

## Target Users

- ML + formal methods researchers
- Engineers building autonomous theorem discovery workflows
- Teams preparing reproducible research artifacts for publication

## Core User Value

- Reduce manual theorem candidate hunting.
- Produce machine-readable outputs for auditing and evaluation.
- Run deterministic discovery cycles with explicit safety modes.

## Key Features

- Phase 1 analogical gap detector with ranking and pilot artifact generation.
- Phase 1 evaluation CLI for top-k precision and go/no-go style metrics.
- Phase 2 orchestrated pipeline with:
  - template conjecture generation
  - counterexample filtering
  - novelty checks
  - retry-bounded proof attempts
  - Lean-based verification with sandbox-first policy
- Structured JSON/JSONL artifacts for downstream analysis.

## Product Objectives

- Reliability: stable, deterministic CLI runs and artifacts.
- Safety: sandboxed verification by default.
- Reproducibility: local commands and CI checks based on `uv` + `pytest` + `ruff`.
- Research throughput: support fast iteration across gap-detection and verification heuristics.

## Non-Goals (Current Scope)

- Full autonomous paper-writing pipeline.
- Production serving infrastructure.
- Generic multi-domain theorem discovery beyond current algebra-focused configuration.
