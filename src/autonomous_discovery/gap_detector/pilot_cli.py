"""CLI for running the Phase 1 gap-detector pilot harness."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from autonomous_discovery.config import ProjectConfig
from autonomous_discovery.gap_detector.pilot import run_phase1_pilot


def build_parser() -> argparse.ArgumentParser:
    config = ProjectConfig()
    parser = argparse.ArgumentParser(
        description="Run Phase 1 gap detector pilot artifact generation."
    )
    parser.add_argument("--premises-path", type=Path, default=config.premises_path)
    parser.add_argument("--decl-types-path", type=Path, default=config.decl_types_path)
    parser.add_argument("--output-dir", type=Path, default=config.data_processed_dir)
    parser.add_argument("--top-k", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_phase1_pilot(
            premises_path=args.premises_path,
            decl_types_path=args.decl_types_path,
            output_dir=args.output_dir,
            top_k=args.top_k,
        )
    except FileNotFoundError as exc:
        print(f"Input file not found: {exc.filename}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
