# Lean Workspace

This directory is tracked and contains Lean-related components used by this project.

## Layout

- `LeanExtract/`: project-local Lean extraction utilities and glue code used by this repository.
- `lean-training-data/`: pinned third-party dependency managed as a git submodule.

## Source of Truth Policy

- `LeanExtract/` is maintained in this repository.
- `lean-training-data/` is upstream-owned (`https://github.com/kim-em/lean-training-data.git`) and should not be treated as project-local source.
- If you need behavior changes in `lean-training-data/`, prefer upstream contributions or explicitly document a fork.

## Bootstrap

From repository root:

```bash
git submodule update --init --recursive
```

## Build / Smoke Commands

Build `LeanExtract`:

```bash
lake -d lean/LeanExtract update
lake -d lean/LeanExtract build
```

Run extraction scripts from `lean-training-data`:

```bash
lake -d lean/lean-training-data update
lake -d lean/lean-training-data exe cache get
lake -d lean/lean-training-data exe declaration_types Mathlib
lake -d lean/lean-training-data exe premises Mathlib
```

## Notes

- Lean build outputs (`.lake/`, `build/`, `*.olean`) are ignored and should not be committed.
- Keep generated data artifacts outside this folder (for example under `data/raw/` or `data/processed/`).
