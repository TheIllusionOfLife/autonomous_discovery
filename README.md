# autonomous_discovery

Autonomous mathematical discovery system for Lean 4 + Mathlib.

The repository currently implements:
- Phase 1: analogical gap detection and pilot artifact generation.
- Phase 2: deterministic discovery loop (gap -> conjecture -> filter/novelty -> proof attempts -> Lean verification).

## Quick Start

```bash
uv sync --dev
git submodule update --init --recursive
```

## Run Commands

Generate Phase 1 gap candidates:

```bash
uv run python -m autonomous_discovery.gap_detector.cli --top-k 20
```

Generate pilot artifacts for manual review:

```bash
uv run python -m autonomous_discovery.gap_detector.pilot_cli --top-k 20
```

Evaluate labeled top-k pilot outputs:

```bash
uv run python -m autonomous_discovery.gap_detector.evaluate_cli \
  --metrics-path data/processed/phase1_metrics.json \
  --labels-csv data/processed/top20_label_template.csv \
  --top-k 20
```

Run one Phase 2 cycle (sandboxed verifier mode):

```bash
uv run python -m autonomous_discovery.phase2_cli --top-k 20 --proof-retry-budget 3
```

Trusted local mode (unsandboxed; explicit acknowledgment required):

```bash
uv run python -m autonomous_discovery.phase2_cli \
  --trusted-local-run \
  --i-understand-unsafe \
  --top-k 20 \
  --proof-retry-budget 3
```

## Data and Artifacts

- Inputs: `data/raw/premises.txt`, `data/raw/decl_types.txt`
- Generated outputs: `data/processed/`
- Main Phase 2 artifacts:
  - `phase2_attempts.jsonl`
  - `phase2_cycle_metrics.json`

## Quality Checks

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest -q
uv run pytest -m integration -q
```

## Documentation Map

- Developer instructions: `AGENTS.md`
- Product goals: `PRODUCT.md`
- Technology decisions: `TECH.md`
- Codebase layout and conventions: `STRUCTURE.md`
- Legacy planning/spec documents: `docs/archive/`
