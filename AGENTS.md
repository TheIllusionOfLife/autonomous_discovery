# AGENTS.md

Repository-specific instructions for coding agents working in `autonomous_discovery`.

## Scope and Intent

- Keep changes small, deterministic, and test-backed.
- Prefer improving existing modules over introducing new abstractions.
- Do not introduce new runtime dependencies unless explicitly requested.

## Commands Agents Should Know

Use these exact commands (all from repository root):

```bash
uv sync --dev
git submodule update --init --recursive
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest -q
uv run pytest -m integration -q
uv run python -m autonomous_discovery.gap_detector.cli --top-k 20
uv run python -m autonomous_discovery.gap_detector.pilot_cli --top-k 20
uv run python -m autonomous_discovery.phase2_cli --top-k 20 --proof-retry-budget 3
```

Phase 2 trusted local mode is intentionally explicit:

```bash
uv run python -m autonomous_discovery.phase2_cli --trusted-local-run --i-understand-unsafe
```

## Code Style and Implementation Rules

- Python 3.12+, 4-space indent, max line length 99.
- Lint config is Ruff (`E,F,I,N,W,UP`) in `pyproject.toml`.
- Use type hints on public functions and dataclasses.
- Keep domain modules cohesive (`gap_detector`, `pipeline`, `verifier`, etc.).
- Avoid hidden side effects at import time.

## Testing and Validation

- Unit tests live under `tests/` mirroring source modules.
- Integration tests are marked with `@pytest.mark.integration` and run separately.
- For behavior changes, add or update tests in the same PR/branch.
- Minimum local validation before proposing merge:
  - `uv run ruff check src tests`
  - `uv run ruff format --check src tests`
  - `uv run pytest -q`

## Branches, Commits, and PR Etiquette

- Never push directly to `main`.
- Branch naming: `feat/<short-topic>`, `fix/<short-topic>`, `chore/<short-topic>`, `test/<short-topic>`.
- Commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Keep each commit logically scoped and include test evidence in PR description.

## Architecture-Specific Decisions

- `run_phase2_cycle` in `src/autonomous_discovery/pipeline/phase2.py` is the orchestration entrypoint.
- Lean verification is sandbox-first by default; trusted local mode exists for controlled environments.
- Data artifacts are written to `data/processed/` and are not committed.
- `ProjectConfig` in `src/autonomous_discovery/config.py` is the canonical location for project paths and thresholds.

## Environment and Tooling Quirks

- Lean verification expects `lean` and `lake` on `PATH` for real verification.
- Sandboxed verifier mode defaults to `nsjail` command prefix; missing sandbox marks runtime as not ready.
- Use `uv` for dependency/runtime execution; do not install packages globally.

## Common Gotchas

- Phase 2 with `--trusted-local-run` requires `--i-understand-unsafe`; missing ack exits with code 1.
- CI validates lint, format, unit tests, and integration tests; run the same commands locally before opening a PR.
- Large planning/spec docs are archived in `docs/archive/` and should not be treated as current implementation docs.
