"""Type class extraction and family compatibility for Lean 4 type signatures."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Matches bracket-delimited type class instances in Lean 4 signatures:
#   [inst : ClassName args...]  → named instance
#   [ClassName args...]          → anonymous instance
# Does NOT match implicit type vars like {R : Type u_1}.
_INSTANCE_RE = re.compile(
    r"\["
    r"(?:\w+\s*:\s*)?"  # optional instance name + colon
    r"((?:[A-Z]\w*\.)*[A-Z]\w*)"  # class name (possibly dotted, starts with uppercase)
    r"(?:\s[^\]]*?)?"  # optional arguments
    r"\]"
)


def extract_type_classes(type_signature: str) -> frozenset[str]:
    """Extract type class names from a Lean 4 type signature.

    Returns a frozenset of class names found in instance brackets.
    Implicit type variables ({R : Type u_1}) are not matched.
    """
    if not type_signature:
        return frozenset()
    return frozenset(_INSTANCE_RE.findall(type_signature))


UNIVERSAL_CLASSES: frozenset[str] = frozenset(
    {
        "DecidableEq",
        "Fintype",
        "Inhabited",
        "Repr",
        "ToString",
        "BEq",
        "Hashable",
        "Nonempty",
        "Decidable",
    }
)

# Maps family prefix → set of type classes that family's structures can provide.
# Based on Mathlib's algebraic hierarchy.
DEFAULT_PROVIDED: dict[str, frozenset[str]] = {
    "Group.": frozenset(
        {
            "Group",
            "Monoid",
            "Semigroup",
            "MulOneClass",
            "AddGroup",
            "AddMonoid",
            "AddSemigroup",
            "AddCommGroup",
            "CommGroup",
            "Inv",
            "Neg",
        }
    ),
    "Ring.": frozenset(
        {
            "Ring",
            "CommRing",
            "Semiring",
            "CommSemiring",
            "Group",
            "CommGroup",
            "Monoid",
            "Semigroup",
            "MulOneClass",
            "AddGroup",
            "AddMonoid",
            "AddSemigroup",
            "AddCommGroup",
            "AddCommMonoid",
            "Module",  # Ring is a Module over itself
            "Algebra",
            "Inv",
            "Neg",
        }
    ),
    "Module.": frozenset(
        {
            "Module",
            "Semiring",
            "CommSemiring",
            "Ring",
            "CommRing",
            "AddCommMonoid",
            "AddCommGroup",
            "AddMonoid",
            "AddSemigroup",
        }
    ),
}


@dataclass(frozen=True, slots=True)
class FamilyCompatibility:
    """Checks whether a target family can satisfy type class requirements."""

    provided_classes: dict[str, frozenset[str]]

    def can_satisfy(
        self,
        *,
        required_classes: frozenset[str],
        target_family: str,
    ) -> tuple[bool, float]:
        """Check if target_family can satisfy the required type classes.

        Universal classes (DecidableEq, Fintype, etc.) are ignored.

        Returns:
            (all_satisfied, satisfaction_ratio) where ratio is fraction of
            non-universal requirements met. Empty requirements → (True, 1.0).
            Unknown family → (False, 0.0).
        """
        relevant = required_classes - UNIVERSAL_CLASSES
        if not relevant:
            return True, 1.0

        provided = self.provided_classes.get(target_family)
        if provided is None:
            return False, 0.0

        satisfied = sum(1 for cls in relevant if cls in provided)
        ratio = satisfied / len(relevant)
        return satisfied == len(relevant), ratio
