"""Tests for conflict detector."""

import pytest

from doc_helper.domain.override.conflict_detector import ConflictDetector, ConflictInfo
from doc_helper.domain.schema.schema_ids import FieldDefinitionId


class TestConflictInfo:
    """Tests for ConflictInfo."""

    def test_create_conflict_info(self) -> None:
        """ConflictInfo should be created with required fields."""
        conflict = ConflictInfo(
            field_id=FieldDefinitionId("total"),
            conflict_type="formula",
            override_value=1600,
            computed_value=1500,
        )
        assert conflict.field_id == FieldDefinitionId("total")
        assert conflict.conflict_type == "formula"
        assert conflict.override_value == 1600
        assert conflict.computed_value == 1500

    def test_create_conflict_info_with_description(self) -> None:
        """ConflictInfo should accept optional description."""
        conflict = ConflictInfo(
            field_id=FieldDefinitionId("total"),
            conflict_type="formula",
            override_value=1600,
            description="Values differ",
        )
        assert conflict.description == "Values differ"

    def test_conflict_info_is_immutable(self) -> None:
        """ConflictInfo should be immutable."""
        conflict = ConflictInfo(
            field_id=FieldDefinitionId("total"),
            conflict_type="formula",
            override_value=1600,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            conflict.conflict_type = "control"  # type: ignore

    def test_conflict_info_requires_field_definition_id(self) -> None:
        """ConflictInfo should require FieldDefinitionId."""
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            ConflictInfo(
                field_id="total",  # type: ignore
                conflict_type="formula",
                override_value=1600,
            )

    def test_conflict_info_requires_conflict_type_string(self) -> None:
        """ConflictInfo should require string conflict_type."""
        with pytest.raises(TypeError, match="conflict_type must be a string"):
            ConflictInfo(
                field_id=FieldDefinitionId("total"),
                conflict_type=123,  # type: ignore
                override_value=1600,
            )

    def test_conflict_info_conflict_type_cannot_be_empty(self) -> None:
        """ConflictInfo should reject empty conflict_type."""
        with pytest.raises(ValueError, match="conflict_type cannot be empty"):
            ConflictInfo(
                field_id=FieldDefinitionId("total"),
                conflict_type="",
                override_value=1600,
            )

    def test_is_formula_conflict(self) -> None:
        """is_formula_conflict should check conflict type."""
        conflict1 = ConflictInfo(
            field_id=FieldDefinitionId("total"),
            conflict_type="formula",
            override_value=1600,
        )
        assert conflict1.is_formula_conflict is True
        assert conflict1.is_control_conflict is False
        assert conflict1.is_dual_conflict is False

    def test_is_control_conflict(self) -> None:
        """is_control_conflict should check conflict type."""
        conflict = ConflictInfo(
            field_id=FieldDefinitionId("status"),
            conflict_type="control",
            override_value="active",
        )
        assert conflict.is_formula_conflict is False
        assert conflict.is_control_conflict is True
        assert conflict.is_dual_conflict is False

    def test_is_dual_conflict(self) -> None:
        """is_dual_conflict should check conflict type."""
        conflict = ConflictInfo(
            field_id=FieldDefinitionId("total"),
            conflict_type="formula_control",
            override_value=1600,
        )
        assert conflict.is_formula_conflict is True
        assert conflict.is_control_conflict is True
        assert conflict.is_dual_conflict is True


class TestConflictDetector:
    """Tests for ConflictDetector."""

    def test_detect_formula_conflict_when_values_differ(self) -> None:
        """detect_formula_conflict should detect when values differ."""
        detector = ConflictDetector()
        conflict = detector.detect_formula_conflict(
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            computed_value=1500,
        )
        assert conflict is not None
        assert conflict.field_id == FieldDefinitionId("total")
        assert conflict.conflict_type == "formula"
        assert conflict.override_value == 1600
        assert conflict.computed_value == 1500
        assert "differs from" in conflict.description

    def test_detect_formula_conflict_when_values_match(self) -> None:
        """detect_formula_conflict should return None when values match."""
        detector = ConflictDetector()
        conflict = detector.detect_formula_conflict(
            field_id=FieldDefinitionId("total"),
            override_value=1500,
            computed_value=1500,
        )
        assert conflict is None

    def test_detect_formula_conflict_requires_field_definition_id(self) -> None:
        """detect_formula_conflict should require FieldDefinitionId."""
        detector = ConflictDetector()
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            detector.detect_formula_conflict(
                field_id="total",  # type: ignore
                override_value=1600,
                computed_value=1500,
            )

    def test_detect_control_conflict_when_values_differ(self) -> None:
        """detect_control_conflict should detect when values differ."""
        detector = ConflictDetector()
        conflict = detector.detect_control_conflict(
            field_id=FieldDefinitionId("status"),
            override_value="active",
            control_value="disabled",
        )
        assert conflict is not None
        assert conflict.field_id == FieldDefinitionId("status")
        assert conflict.conflict_type == "control"
        assert conflict.override_value == "active"
        assert conflict.control_value == "disabled"
        assert "differs from" in conflict.description

    def test_detect_control_conflict_when_values_match(self) -> None:
        """detect_control_conflict should return None when values match."""
        detector = ConflictDetector()
        conflict = detector.detect_control_conflict(
            field_id=FieldDefinitionId("status"),
            override_value="active",
            control_value="active",
        )
        assert conflict is None

    def test_detect_control_conflict_requires_field_definition_id(self) -> None:
        """detect_control_conflict should require FieldDefinitionId."""
        detector = ConflictDetector()
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            detector.detect_control_conflict(
                field_id="status",  # type: ignore
                override_value="active",
                control_value="disabled",
            )

    def test_detect_dual_conflict_when_all_differ(self) -> None:
        """detect_dual_conflict should detect when override differs from both."""
        detector = ConflictDetector()
        conflict = detector.detect_dual_conflict(
            field_id=FieldDefinitionId("total"),
            override_value=1600,
            computed_value=1500,
            control_value=1550,
        )
        assert conflict is not None
        assert conflict.field_id == FieldDefinitionId("total")
        assert conflict.conflict_type == "formula_control"
        assert conflict.override_value == 1600
        assert conflict.computed_value == 1500
        assert conflict.control_value == 1550
        assert "differs from both" in conflict.description

    def test_detect_dual_conflict_when_override_matches_computed(self) -> None:
        """detect_dual_conflict should return None if override matches computed."""
        detector = ConflictDetector()
        conflict = detector.detect_dual_conflict(
            field_id=FieldDefinitionId("total"),
            override_value=1500,  # Matches computed
            computed_value=1500,
            control_value=1550,
        )
        assert conflict is None

    def test_detect_dual_conflict_when_override_matches_control(self) -> None:
        """detect_dual_conflict should return None if override matches control."""
        detector = ConflictDetector()
        conflict = detector.detect_dual_conflict(
            field_id=FieldDefinitionId("total"),
            override_value=1550,  # Matches control
            computed_value=1500,
            control_value=1550,
        )
        assert conflict is None

    def test_detect_dual_conflict_when_all_match(self) -> None:
        """detect_dual_conflict should return None if all values match."""
        detector = ConflictDetector()
        conflict = detector.detect_dual_conflict(
            field_id=FieldDefinitionId("total"),
            override_value=1500,
            computed_value=1500,
            control_value=1500,
        )
        assert conflict is None

    def test_detect_dual_conflict_requires_field_definition_id(self) -> None:
        """detect_dual_conflict should require FieldDefinitionId."""
        detector = ConflictDetector()
        with pytest.raises(TypeError, match="field_id must be a FieldDefinitionId"):
            detector.detect_dual_conflict(
                field_id="total",  # type: ignore
                override_value=1600,
                computed_value=1500,
                control_value=1550,
            )

    def test_check_values_match_with_same_values(self) -> None:
        """check_values_match should return True for equal values."""
        detector = ConflictDetector()
        assert detector.check_values_match(1500, 1500) is True
        assert detector.check_values_match("active", "active") is True
        assert detector.check_values_match(True, True) is True

    def test_check_values_match_with_different_values(self) -> None:
        """check_values_match should return False for different values."""
        detector = ConflictDetector()
        assert detector.check_values_match(1500, 1600) is False
        assert detector.check_values_match("active", "disabled") is False
        assert detector.check_values_match(True, False) is False

    def test_check_values_match_with_different_types(self) -> None:
        """check_values_match should handle type differences."""
        detector = ConflictDetector()
        assert detector.check_values_match(1500, "1500") is False
        assert detector.check_values_match(0, False) is False
        assert detector.check_values_match(1, True) is False

    def test_conflict_detection_with_none_values(self) -> None:
        """Conflict detector should handle None values."""
        detector = ConflictDetector()

        # Formula conflict with None
        conflict1 = detector.detect_formula_conflict(
            field_id=FieldDefinitionId("optional"),
            override_value=None,
            computed_value="value",
        )
        assert conflict1 is not None

        # Control conflict with None
        conflict2 = detector.detect_control_conflict(
            field_id=FieldDefinitionId("optional"),
            override_value="value",
            control_value=None,
        )
        assert conflict2 is not None

        # No conflict when both None
        conflict3 = detector.detect_formula_conflict(
            field_id=FieldDefinitionId("optional"),
            override_value=None,
            computed_value=None,
        )
        assert conflict3 is None

    def test_conflict_detection_with_complex_types(self) -> None:
        """Conflict detector should handle lists and dicts."""
        detector = ConflictDetector()

        # List conflict
        conflict1 = detector.detect_formula_conflict(
            field_id=FieldDefinitionId("items"),
            override_value=[1, 2, 3],
            computed_value=[1, 2],
        )
        assert conflict1 is not None

        # Dict conflict
        conflict2 = detector.detect_control_conflict(
            field_id=FieldDefinitionId("config"),
            override_value={"key": "value1"},
            control_value={"key": "value2"},
        )
        assert conflict2 is not None

        # No conflict when equal
        conflict3 = detector.detect_formula_conflict(
            field_id=FieldDefinitionId("items"),
            override_value=[1, 2, 3],
            computed_value=[1, 2, 3],
        )
        assert conflict3 is None
