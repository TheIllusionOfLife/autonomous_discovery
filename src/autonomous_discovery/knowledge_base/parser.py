"""Parsers for lean-training-data output files (premises, declaration_types)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Dependency:
    """A single dependency of a declaration."""

    name: str
    is_explicit: bool
    is_simp: bool


@dataclass(frozen=True, slots=True)
class PremisesEntry:
    """A declaration and its dependencies, parsed from `lake exe premises` output."""

    name: str
    dependencies: list[Dependency]


@dataclass(frozen=True, slots=True)
class DeclarationEntry:
    """A declaration with its kind and type signature, from `lake exe declaration_types`."""

    kind: str
    name: str
    type_signature: str


def parse_premises(text: str) -> list[PremisesEntry]:
    """Parse the output of `lake exe premises Mathlib`.

    Format: blocks separated by `---`, each block has:
      - Line 1: declaration name
      - Subsequent lines: dependencies, optionally prefixed with `*` (explicit) or `s` (simp)
    """
    entries: list[PremisesEntry] = []
    blocks = text.split("---")

    for block in blocks:
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        name = lines[0].strip()
        deps: list[Dependency] = []

        for line in lines[1:]:
            stripped = line.strip()
            if not stripped:
                continue

            is_explicit = False
            is_simp = False

            if stripped.startswith("* "):
                is_explicit = True
                stripped = stripped[2:].strip()
            elif stripped.startswith("s "):
                # lean-training-data prefixes simp dependencies with "s ".
                # This is unambiguous: Lean declaration names follow Namespace.Name
                # convention and never start with a lowercase letter followed by space.
                is_simp = True
                stripped = stripped[2:].strip()

            deps.append(Dependency(name=stripped, is_explicit=is_explicit, is_simp=is_simp))

        entries.append(PremisesEntry(name=name, dependencies=deps))

    return entries


def parse_declaration_types(text: str) -> list[DeclarationEntry]:
    """Parse the output of `lake exe declaration_types Mathlib`.

    Format: blocks separated by `---`, each block has:
      - Line 1: kind (theorem, definition, inductive, etc.)
      - Line 2: declaration name
      - Remaining lines: type signature (may be multi-line)
    """
    entries: list[DeclarationEntry] = []
    blocks = text.split("---")

    for block in blocks:
        lines = block.split("\n")
        # Strip only fully empty leading/trailing lines, preserve internal structure
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) < 3:
            continue

        # Find the first non-empty line (kind), second (name), rest (signature)
        found_lines: list[str] = []
        sig_start_idx = 0
        for i, line in enumerate(lines):
            if line.strip():
                found_lines.append(line.strip())
                if len(found_lines) == 2:
                    sig_start_idx = i + 1
                    break

        if len(found_lines) < 2:
            continue

        kind = found_lines[0]
        name = found_lines[1]

        # Signature is everything after name line, stripped of leading/trailing blank lines
        sig_lines = lines[sig_start_idx:]
        # Strip trailing empty lines
        end = len(sig_lines)
        while end > 0 and not sig_lines[end - 1].strip():
            end -= 1
        # Strip leading empty lines
        start = 0
        while start < end and not sig_lines[start].strip():
            start += 1

        type_signature = "\n".join(sig_lines[start:end])

        entries.append(DeclarationEntry(kind=kind, name=name, type_signature=type_signature))

    return entries
