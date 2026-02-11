# autonomous_discovery

Autonomous mathematical discovery system targeting Lean 4 + Mathlib.

## Quick start

```bash
uv sync
```

## Quality checks

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest -q
uv run pytest -m integration -q
```

## Gap detector (Phase 1)

Generate top-k analogical gap candidates:

```bash
uv run python -m autonomous_discovery.gap_detector.cli --top-k 20
```

Run the pilot harness and emit review artifacts:

```bash
uv run python -m autonomous_discovery.gap_detector.pilot_cli --top-k 20
```

Artifacts are written under `data/processed/`:
- `gap_candidates.jsonl`
- `top20_label_template.csv`
- `phase1_metrics.json`
