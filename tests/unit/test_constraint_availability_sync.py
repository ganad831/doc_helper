"""Constraint Availability Synchronization Tests.

ARCHITECTURAL ENFORCEMENT TEST FILE.

This test module enforces synchronization between the Domain layer's
authoritative constraint availability matrix and the Presentation layer's
string-based copy.

PURPOSE:
    - Prevent silent drift between Domain and Presentation constraint matrices
    - Ensure architectural boundaries are maintained (Presentation has no domain imports)
    - Detect missing field types or constraint types immediately

ARCHITECTURE NOTES:
    - Domain layer (domain/validation/constraint_availability.py):
      Uses FieldType enums and FieldConstraint classes (authoritative)

    - Presentation layer (presentation/utils/constraint_availability.py):
      Uses strings to avoid domain imports (derived, must stay in sync)

    - This test file imports BOTH layers specifically to enforce synchronization.
      This is allowed because tests are outside the architectural layers.

IF THIS TEST FAILS:
    1. Check which field type or constraint diverged
    2. The Domain layer is AUTHORITATIVE - it defines the correct rules
    3. Update the Presentation layer to match Domain
    4. Re-run this test to confirm sync is restored
"""

import pytest

# Domain layer imports (authoritative)
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.validation.constraint_availability import (
    _CONSTRAINT_AVAILABILITY as DOMAIN_MATRIX,
    CONSTRAINT_TYPE_MAP,
)

# Presentation layer imports (derived)
from doc_helper.presentation.utils.constraint_availability import (
    _CONSTRAINT_AVAILABILITY as PRESENTATION_MATRIX,
    CONSTRAINT_TYPES as PRESENTATION_CONSTRAINT_TYPES,
)


class TestConstraintAvailabilitySync:
    """Tests enforcing Domain-Presentation constraint matrix synchronization."""

    def test_all_domain_field_types_exist_in_presentation(self) -> None:
        """Every FieldType in Domain must have a corresponding entry in Presentation.

        If this fails: A field type was added to Domain but not to Presentation.
        Fix: Add the missing field type to presentation/utils/constraint_availability.py
        """
        domain_field_types = set(ft.value.lower() for ft in FieldType)
        presentation_field_types = set(PRESENTATION_MATRIX.keys())

        missing_in_presentation = domain_field_types - presentation_field_types
        assert not missing_in_presentation, (
            f"Field types exist in Domain but missing in Presentation: {missing_in_presentation}\n"
            f"Fix: Add these to presentation/utils/constraint_availability.py"
        )

    def test_no_extra_field_types_in_presentation(self) -> None:
        """Presentation must not have field types that don't exist in Domain.

        If this fails: Presentation has stale/invalid field types.
        Fix: Remove the extra field types from presentation/utils/constraint_availability.py
        """
        domain_field_types = set(ft.value.lower() for ft in FieldType)
        presentation_field_types = set(PRESENTATION_MATRIX.keys())

        extra_in_presentation = presentation_field_types - domain_field_types
        assert not extra_in_presentation, (
            f"Field types exist in Presentation but not in Domain: {extra_in_presentation}\n"
            f"Fix: Remove these from presentation/utils/constraint_availability.py"
        )

    def test_all_domain_constraint_types_exist_in_presentation(self) -> None:
        """Every constraint type string in Domain must exist in Presentation.

        If this fails: A constraint type was added to Domain but not to Presentation.
        Fix: Add the missing constraint type to presentation CONSTRAINT_TYPES.
        """
        domain_constraint_types = set(CONSTRAINT_TYPE_MAP.keys())
        presentation_constraint_types = set(PRESENTATION_CONSTRAINT_TYPES)

        missing_in_presentation = domain_constraint_types - presentation_constraint_types
        assert not missing_in_presentation, (
            f"Constraint types exist in Domain but missing in Presentation: {missing_in_presentation}\n"
            f"Fix: Add these to CONSTRAINT_TYPES in presentation/utils/constraint_availability.py"
        )

    def test_no_extra_constraint_types_in_presentation(self) -> None:
        """Presentation must not have constraint types that don't exist in Domain.

        If this fails: Presentation has stale/invalid constraint types.
        Fix: Remove the extra constraint types from presentation CONSTRAINT_TYPES.
        """
        domain_constraint_types = set(CONSTRAINT_TYPE_MAP.keys())
        presentation_constraint_types = set(PRESENTATION_CONSTRAINT_TYPES)

        extra_in_presentation = presentation_constraint_types - domain_constraint_types
        assert not extra_in_presentation, (
            f"Constraint types exist in Presentation but not in Domain: {extra_in_presentation}\n"
            f"Fix: Remove these from CONSTRAINT_TYPES in presentation/utils/constraint_availability.py"
        )

    @pytest.mark.parametrize("field_type", list(FieldType))
    def test_allowed_constraints_match_for_field_type(self, field_type: FieldType) -> None:
        """For each field type, Domain and Presentation must have identical allowed constraints.

        If this fails: The allowed constraint sets have diverged.
        Domain is AUTHORITATIVE - update Presentation to match.
        """
        # Get Domain's allowed constraints as strings
        domain_allowed_classes = DOMAIN_MATRIX.get(field_type, frozenset())
        domain_allowed_strings = set()
        for constraint_class in domain_allowed_classes:
            # Find the string key for this class in CONSTRAINT_TYPE_MAP
            for type_string, cls in CONSTRAINT_TYPE_MAP.items():
                if cls == constraint_class:
                    domain_allowed_strings.add(type_string)
                    break

        # Get Presentation's allowed constraints
        presentation_key = field_type.value.lower()
        presentation_allowed = set(PRESENTATION_MATRIX.get(presentation_key, frozenset()))

        # Compare
        assert domain_allowed_strings == presentation_allowed, (
            f"DRIFT DETECTED for field type '{field_type.value}':\n"
            f"  Domain (authoritative): {sorted(domain_allowed_strings)}\n"
            f"  Presentation (derived):  {sorted(presentation_allowed)}\n"
            f"  In Domain but not Presentation: {sorted(domain_allowed_strings - presentation_allowed)}\n"
            f"  In Presentation but not Domain: {sorted(presentation_allowed - domain_allowed_strings)}\n"
            f"\nFix: Update presentation/utils/constraint_availability.py to match Domain."
        )


class TestArchitecturalInvariantsSync:
    """Tests enforcing that architectural invariants are synchronized."""

    def test_checkbox_has_no_constraints_in_both_layers(self) -> None:
        """CHECKBOX must have no constraints in both Domain and Presentation.

        Architectural rule: Boolean fields are always valid (true/false).
        """
        domain_checkbox = DOMAIN_MATRIX.get(FieldType.CHECKBOX, frozenset())
        presentation_checkbox = PRESENTATION_MATRIX.get("checkbox", frozenset())

        assert domain_checkbox == frozenset(), (
            f"INVARIANT VIOLATION: Domain CHECKBOX must have no constraints, got: {domain_checkbox}"
        )
        assert presentation_checkbox == frozenset(), (
            f"INVARIANT VIOLATION: Presentation CHECKBOX must have no constraints, got: {presentation_checkbox}"
        )

    def test_calculated_has_no_constraints_in_both_layers(self) -> None:
        """CALCULATED must have no constraints in both Domain and Presentation.

        Architectural rule: Calculated fields derive values from formulas.
        """
        domain_calculated = DOMAIN_MATRIX.get(FieldType.CALCULATED, frozenset())
        presentation_calculated = PRESENTATION_MATRIX.get("calculated", frozenset())

        assert domain_calculated == frozenset(), (
            f"INVARIANT VIOLATION: Domain CALCULATED must have no constraints, got: {domain_calculated}"
        )
        assert presentation_calculated == frozenset(), (
            f"INVARIANT VIOLATION: Presentation CALCULATED must have no constraints, got: {presentation_calculated}"
        )

    def test_table_has_no_constraints_in_both_layers(self) -> None:
        """TABLE must have no constraints in both Domain and Presentation.

        Architectural rule: TABLE fields hold child records, not user-typed values.
        """
        domain_table = DOMAIN_MATRIX.get(FieldType.TABLE, frozenset())
        presentation_table = PRESENTATION_MATRIX.get("table", frozenset())

        assert domain_table == frozenset(), (
            f"INVARIANT VIOLATION: Domain TABLE must have no constraints, got: {domain_table}"
        )
        assert presentation_table == frozenset(), (
            f"INVARIANT VIOLATION: Presentation TABLE must have no constraints, got: {presentation_table}"
        )

    def test_lookup_has_only_required_constraint_in_both_layers(self) -> None:
        """LOOKUP must have only REQUIRED constraint in both Domain and Presentation.

        Architectural rule: LOOKUP fields reference another entity.
        Only presence check (REQUIRED) is meaningful.
        """
        from doc_helper.domain.validation.constraints import RequiredConstraint

        domain_lookup = DOMAIN_MATRIX.get(FieldType.LOOKUP, frozenset())
        presentation_lookup = PRESENTATION_MATRIX.get("lookup", frozenset())

        assert domain_lookup == frozenset({RequiredConstraint}), (
            f"INVARIANT VIOLATION: Domain LOOKUP must have only RequiredConstraint, got: {domain_lookup}"
        )
        assert presentation_lookup == frozenset({"REQUIRED"}), (
            f"INVARIANT VIOLATION: Presentation LOOKUP must have only REQUIRED, got: {presentation_lookup}"
        )
