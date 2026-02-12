"""Count algebra theorems added to Mathlib after the data-leakage cutoff date.

Validates the go/no-go gate: at least ``min_post_cutoff_theorems`` algebra
theorems must exist after the cutoff for the rediscovery experiment.
"""

from __future__ import annotations

import logging
import re
import subprocess
from datetime import date
from pathlib import Path

from autonomous_discovery.config import ProjectConfig
from autonomous_discovery.knowledge_base.parser import DeclarationEntry, parse_declaration_types

logger = logging.getLogger(__name__)

# Lean 4 theorem/protected theorem declaration at start of added line.
_THEOREM_LINE_RE = re.compile(r"^\+\s*(?:protected\s+)?(?:theorem|lemma)\s+(\S+)")

# Mathlib subdirectories corresponding to algebra name prefixes.
_ALGEBRA_GIT_PATHS: tuple[str, ...] = (
    "Mathlib/Algebra/",
    "Mathlib/FieldTheory/",
    "Mathlib/GroupTheory/",
    "Mathlib/LinearAlgebra/",
    "Mathlib/RingTheory/",
)


def filter_algebra_theorems(
    declarations: list[DeclarationEntry],
    prefixes: tuple[str, ...],
) -> list[DeclarationEntry]:
    """Return declarations that are theorems matching any algebra prefix."""
    return [
        d
        for d in declarations
        if d.kind == "theorem" and any(d.name.startswith(p) for p in prefixes)
    ]


def count_post_cutoff_from_git(
    mathlib_repo: Path,
    cutoff_date: date,
) -> int:
    """Count new theorem lines added after cutoff_date via git diff.

    This is an approximate count — it counts added ``theorem``/``lemma``
    lines in algebra-related directories, which may include renamed or
    moved theorems. Sufficient for a go/no-go estimate.
    """
    # Find last commit on or before cutoff
    cutoff_str = cutoff_date.isoformat() + "T23:59:59Z"
    result = subprocess.run(
        ["git", "log", f"--before={cutoff_str}", "--format=%H", "-1"],
        cwd=mathlib_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    cutoff_hash = result.stdout.strip()
    if not cutoff_hash:
        logger.warning("No Mathlib commit found before %s", cutoff_date)
        return 0

    logger.info("Cutoff commit: %s", cutoff_hash)

    # Diff from cutoff to HEAD for algebra paths
    diff_result = subprocess.run(
        [
            "git",
            "diff",
            f"{cutoff_hash}..HEAD",
            "--",
            *_ALGEBRA_GIT_PATHS,
        ],
        cwd=mathlib_repo,
        capture_output=True,
        text=True,
        check=True,
    )

    count = 0
    for line in diff_result.stdout.splitlines():
        if _THEOREM_LINE_RE.match(line):
            count += 1
    return count


def main() -> int:
    """Run post-cutoff theorem counting and report results."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = ProjectConfig()

    # Step 1: Count total algebra theorems from current snapshot
    logger.info("Parsing declaration types from %s ...", config.decl_types_path)
    text = config.decl_types_path.read_text(encoding="utf-8")
    declarations = parse_declaration_types(text)
    algebra_theorems = filter_algebra_theorems(declarations, config.algebra_name_prefixes)
    logger.info("Total algebra theorems in current snapshot: %d", len(algebra_theorems))

    # Step 2: Estimate post-cutoff count via git
    mathlib_repo = (
        config.lean_project_dir.parent / "lean-training-data" / ".lake" / "packages" / "mathlib"
    )
    if not (mathlib_repo / ".git").exists():
        logger.warning("Mathlib git repo not found at %s — skipping git count", mathlib_repo)
        return 1

    post_cutoff = count_post_cutoff_from_git(mathlib_repo, config.cutoff_date)
    logger.info(
        "Approximate post-cutoff (%s) algebra theorem additions: %d",
        config.cutoff_date,
        post_cutoff,
    )

    # Go/no-go decision
    threshold = config.min_post_cutoff_theorems
    if post_cutoff >= threshold:
        logger.info("GO: %d >= %d threshold", post_cutoff, threshold)
        return 0
    else:
        logger.warning(
            "NO-GO: %d < %d threshold — consider expanding domain",
            post_cutoff,
            threshold,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
