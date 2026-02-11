# LeanExtract

Project-local Lean package used by `autonomous_discovery` for Lean-side extraction and bridge utilities.

## From Repository Root

```bash
git submodule update --init --recursive
lake -d lean/LeanExtract update
lake -d lean/LeanExtract build
```

## Notes

- Keep `LeanExtract` changes scoped to project needs.
- Do not commit build artifacts (`.lake/`, `build/`, `*.olean`).
