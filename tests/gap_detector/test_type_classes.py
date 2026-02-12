"""TDD tests for type class extraction and family compatibility."""

from autonomous_discovery.gap_detector.type_classes import (
    DEFAULT_PROVIDED,
    FamilyCompatibility,
    extract_type_classes,
)


class TestExtractTypeClasses:
    def test_named_instance(self) -> None:
        sig = "∀ {R : Type u_1} [inst : Semiring R] (x : R), x * 1 = x"
        assert extract_type_classes(sig) == frozenset({"Semiring"})

    def test_anonymous_instance(self) -> None:
        sig = "∀ {R : Type u_1} {M : Type u_2} [Module R M] (m : M), ..."
        assert extract_type_classes(sig) == frozenset({"Module"})

    def test_mixed_patterns(self) -> None:
        sig = "∀ {R : Type u_1} {M : Type u_2} [inst : Semiring R] [Module R M], ..."
        assert extract_type_classes(sig) == frozenset({"Semiring", "Module"})

    def test_empty_signature(self) -> None:
        assert extract_type_classes("") == frozenset()

    def test_no_instance_signature(self) -> None:
        sig = "∀ (n m : Nat), n + m = m + n"
        assert extract_type_classes(sig) == frozenset()

    def test_dotted_class_name(self) -> None:
        sig = "∀ {C : Type u_1} [inst : CategoryTheory.Category C], ..."
        assert extract_type_classes(sig) == frozenset({"CategoryTheory.Category"})

    def test_implicit_type_vars_not_matched(self) -> None:
        sig = "∀ {R : Type u_1} {M : Type u_2}, ..."
        assert extract_type_classes(sig) == frozenset()

    def test_prop_signature(self) -> None:
        """Prop type signatures (as in existing tests) return no type classes."""
        assert extract_type_classes("Group.mul_assoc : Prop") == frozenset()

    def test_multiple_same_class(self) -> None:
        sig = "∀ {R : Type u_1} [inst : Ring R] [inst2 : Ring S], ..."
        assert extract_type_classes(sig) == frozenset({"Ring"})


class TestFamilyCompatibility:
    def setup_method(self) -> None:
        self.compat = FamilyCompatibility(provided_classes=DEFAULT_PROVIDED)

    def test_ring_satisfies_group_requirements(self) -> None:
        required = frozenset({"Group"})
        ok, ratio = self.compat.can_satisfy(required_classes=required, target_family="Ring.")
        assert ok is True
        assert ratio == 1.0

    def test_group_cannot_satisfy_module_requirements(self) -> None:
        required = frozenset({"Module"})
        ok, ratio = self.compat.can_satisfy(required_classes=required, target_family="Group.")
        assert ok is False
        assert ratio < 0.5

    def test_universal_classes_ignored(self) -> None:
        required = frozenset({"DecidableEq", "Fintype", "Group"})
        ok, ratio = self.compat.can_satisfy(required_classes=required, target_family="Ring.")
        # DecidableEq and Fintype are universal → ignored; Group is satisfied by Ring
        assert ok is True
        assert ratio == 1.0

    def test_empty_requirements(self) -> None:
        ok, ratio = self.compat.can_satisfy(required_classes=frozenset(), target_family="Group.")
        assert ok is True
        assert ratio == 1.0

    def test_unknown_family_prefix(self) -> None:
        ok, ratio = self.compat.can_satisfy(
            required_classes=frozenset({"Group"}), target_family="UnknownFamily."
        )
        assert ok is False
        assert ratio == 0.0

    def test_module_to_ring_compatible(self) -> None:
        """Ring is a Module over itself, so Ring should satisfy Module requirements."""
        required = frozenset({"Module"})
        ok, ratio = self.compat.can_satisfy(required_classes=required, target_family="Ring.")
        assert ok is True
        assert ratio == 1.0

    def test_only_universal_requirements(self) -> None:
        """When all requirements are universal, everything is compatible."""
        required = frozenset({"DecidableEq", "Fintype"})
        ok, ratio = self.compat.can_satisfy(required_classes=required, target_family="Group.")
        assert ok is True
        assert ratio == 1.0
