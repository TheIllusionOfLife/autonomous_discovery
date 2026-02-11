"""CLI for the Phase 2 core loop vertical slice."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from autonomous_discovery.config import ProjectConfig
from autonomous_discovery.pipeline.phase2 import run_phase2_cycle


def build_parser() -> argparse.ArgumentParser:
    config = ProjectConfig()
    parser = argparse.ArgumentParser(description="Run a Phase 2 discovery cycle.")
    parser.add_argument("--premises-path", type=Path, default=config.premises_path)
    parser.add_argument("--decl-types-path", type=Path, default=config.decl_types_path)
    parser.add_argument("--output-dir", type=Path, default=config.data_processed_dir)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--proof-retry-budget", type=int, default=3)
    parser.add_argument(
        "--trusted-local-run",
        action="store_true",
        help="Allow unsandboxed verification for trusted local runs.",
    )
    parser.add_argument(
        "--sandbox-command-prefix",
        type=str,
        default="nsjail",
        help="Shell-like command prefix for sandboxing Lean verification.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run_phase2_cycle(
            premises_path=args.premises_path,
            decl_types_path=args.decl_types_path,
            output_dir=args.output_dir,
            top_k=args.top_k,
            proof_retry_budget=args.proof_retry_budget,
            trusted_local_run=args.trusted_local_run,
            sandbox_command_prefix=tuple(shlex.split(args.sandbox_command_prefix)),
        )
    except FileNotFoundError as exc:
        print(f"Input file not found: {exc.filename}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not summary["runtime_ready"] and summary["skipped_reason"]:
        print(summary["skipped_reason"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
