# TECH.md

## Language and Runtime

- Python 3.12+
- Package manager and task runner: `uv`

## Core Libraries

- `networkx` for knowledge graph representation
- `numpy` / `scipy` for numerical and scoring utilities
- `pytest` for tests
- `ruff` for linting and formatting

## Project Tooling

- Build backend: `uv_build`
- Lint rules: Ruff `E,F,I,N,W,UP`
- Line length: 99
- Tests default to non-integration (`-m 'not integration'` via `pyproject.toml`)

## External Toolchain

- Lean 4 and Lake for theorem verification workflows
- Optional sandbox runtime in verifier mode (default prefix: `nsjail`)
- Git submodules for pinned Lean external dependencies (`lean/lean-training-data`)

## Technical Constraints

- Verification path must preserve safe defaults; trusted-local bypass requires explicit CLI acknowledgment.
- Data artifacts are filesystem-based and written to `data/processed/`.
- The orchestration loop is deterministic by design for repeatable experiments.

## CI and Automation

- GitHub Actions workflow `python-ci.yml` runs:
  - `uv sync --dev`
  - `uv run ruff check src tests`
  - `uv run ruff format --check src tests`
  - `uv run pytest -q -m "not integration"`
  - `uv run pytest -q -m integration`
