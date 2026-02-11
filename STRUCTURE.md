# STRUCTURE.md

## Top-Level Layout

- `src/autonomous_discovery/`: main Python package
- `tests/`: unit + integration tests
- `data/raw/`: source text inputs (`premises.txt`, `decl_types.txt`)
- `data/processed/`: generated runtime artifacts (gitignored)
- `lean/`: Lean projects and extraction/training tooling (`lean-training-data` is a submodule)
- `.github/workflows/`: CI and automation workflows
- `docs/archive/`: legacy planning/review/spec documents

## Source Package Organization

- `gap_detector/`: gap detection, pilot harness, evaluation CLIs
- `pipeline/`: phase orchestration (`run_phase2_cycle`)
- `conjecture_generator/`: candidate generation models/protocols
- `proof_engine/`: proof attempt generation
- `verifier/`: Lean-backed verification
- `lean_bridge/`: subprocess bridge for Lean/Lake execution
- `knowledge_base/`: parsing and graph construction
- `counterexample_filter/`, `novelty_checker/`: gating layers

## Testing Layout

- Mirror source modules under `tests/<module>/`
- Keep integration coverage in `tests/integration/`
- Use behavior-oriented names: `test_<behavior>.py`

## Import and Dependency Conventions

- Absolute imports rooted at `autonomous_discovery`.
- `config.py` is the source of truth for repository paths and thresholds.
- Prefer protocol-driven seams for pipeline components (generator, verifier, filter, novelty checker).

## File and Naming Conventions

- Modules/functions: `snake_case`
- Classes/dataclasses: `PascalCase`
- Keep module scope focused; avoid monolithic files unless orchestration requires it.

## Documentation Placement

- Human onboarding and commands: `README.md`
- Agent operating rules: `AGENTS.md`
- Product intent: `PRODUCT.md`
- Technical decisions/constraints: `TECH.md`
- Historical context: `docs/archive/`
