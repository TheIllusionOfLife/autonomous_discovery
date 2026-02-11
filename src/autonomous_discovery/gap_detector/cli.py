"""CLI for analogical gap detection."""

from __future__ import annotations

import argparse
from pathlib import Path

from autonomous_discovery.config import ProjectConfig
from autonomous_discovery.gap_detector.analogical import AnalogicalGapDetector, GapDetectorConfig
from autonomous_discovery.gap_detector.report import write_gap_report
from autonomous_discovery.knowledge_base.graph import MathlibGraph
from autonomous_discovery.knowledge_base.parser import parse_declaration_types, parse_premises


def build_parser() -> argparse.ArgumentParser:
    config = ProjectConfig()
    parser = argparse.ArgumentParser(description="Detect analogical gaps in Mathlib declarations.")
    parser.add_argument("--premises-path", type=Path, default=config.premises_path)
    parser.add_argument("--decl-types-path", type=Path, default=config.decl_types_path)
    parser.add_argument(
        "--output-path",
        type=Path,
        default=config.data_processed_dir / "gap_candidates.jsonl",
    )
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--min-score", type=float, default=0.2)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    premises = parse_premises(args.premises_path.read_text(encoding="utf-8"))
    declarations = parse_declaration_types(args.decl_types_path.read_text(encoding="utf-8"))
    graph = MathlibGraph.from_raw_data(premises, declarations)

    detector = AnalogicalGapDetector(
        config=GapDetectorConfig(
            family_prefixes=ProjectConfig().algebra_name_prefixes,
            min_score=args.min_score,
            top_k=args.top_k,
        )
    )
    candidates = detector.detect(graph, top_k=args.top_k)
    write_gap_report(candidates, args.output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
