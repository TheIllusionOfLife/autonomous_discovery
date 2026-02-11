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
- `top{K}_label_template.csv` (for example `top20_label_template.csv`)
- `phase1_metrics.json`

After labeling `label_non_trivial` in the CSV, compute go/no-go metrics:

```bash
uv run python -m autonomous_discovery.gap_detector.evaluate_cli \
  --metrics-path data/processed/phase1_metrics.json \
  --labels-csv data/processed/top20_label_template.csv \
  --top-k 20
```

This updates `phase1_metrics.json` with `topk_precision`, `detection_rate`,
`non_trivial_count`, and `go_no_go_status`. For `--top-k 20`, a compatibility
key `top20_precision` is also populated.
