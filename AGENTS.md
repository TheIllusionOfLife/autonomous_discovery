# Repository Guidelines

## Project Structure & Module Organization
- Core Python package lives in `src/autonomous_discovery/` with domain modules such as `gap_detector/`, `pipeline/`, `proof_engine/`, and `verifier/`.
- Tests mirror source structure under `tests/` (for example, `tests/gap_detector/` for `src/autonomous_discovery/gap_detector/`).
- Integration tests are in `tests/integration/` and are marked `integration`.
- Runtime artifacts and generated outputs are written to `data/processed/`.
- Lean-related code and tooling are under `lean/`.

## Build, Test, and Development Commands
- `uv sync`: install and lock project dependencies.
- `uv run ruff check src tests`: run lint checks.
- `uv run ruff format --check src tests`: verify formatting.
- `uv run pytest -q`: run default test suite (`-m 'not integration'`).
- `uv run pytest -m integration -q`: run integration tests.
- `uv run python -m autonomous_discovery.phase2_cli --top-k 20 --proof-retry-budget 3`: run one deterministic Phase 2 cycle.

## Coding Style & Naming Conventions
- Python 3.12+, 4-space indentation, max line length 99 (Ruff enforced).
- Follow Ruff rule sets configured in `pyproject.toml` (`E,F,I,N,W,UP`).
- Use `snake_case` for functions/modules, `PascalCase` for classes, and descriptive test names like `test_runner_rejects_unsafe_path`.
- Keep modules focused; prefer small, composable functions.

## Testing Guidelines
- Framework: `pytest` with markers configured in `pyproject.toml`.
- Place unit tests next to corresponding domain area; keep integration coverage in `tests/integration/`.
- Name tests as `test_<behavior>.py` and assert observable behavior, not implementation details.
- Run lint + format + tests before opening a PR.

## Commit & Pull Request Guidelines
- Follow conventional-style commit prefixes seen in history: `feat:`, `fix:`, `test:`.
- Keep commits scoped to one logical change and include tests for behavior changes.
- Open PRs from a feature branch (never push directly to `main`).
- PRs should include: concise summary, rationale, test evidence (commands run), and linked issue/context when available.
