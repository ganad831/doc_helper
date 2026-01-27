"""Tests for AddRelationshipDialog (Phase A5.2/A6.2 - Design-Time CRUD).

Tests the UI-only relationship add/edit dialog.
Verifies dialog modes, getter methods, and edit mode behavior.

PHASE A5.2/A6.2 COMPLIANCE:
- UI-only tests
- NO business logic validation
- NO schema mutation
- Tests both Add and Edit modes
"""

import pytest
from PyQt6.QtWidgets import QApplication

from doc_helper.application.dto.relationship_dto import RelationshipDTO
from doc_helper.presentation.dialogs.add_relationship_dialog import AddRelationshipDialog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def entity_pairs() -> tuple[tuple[str, str], ...]:
    """Create sample entity pairs for testing."""
    return (
        ("project", "Project"),
        ("borehole", "Borehole"),
        ("sample", "Sample"),
    )


class TestAddRelationshipDialogAddMode:
    """Tests for AddRelationshipDialog in Add mode (Phase A5.2/A6.2)."""

    def test_add_mode_initialization(
        self, qapp, entity_pairs: tuple[tuple[str, str], ...]
    ) -> None:
        """Dialog should initialize in add mode when no existing_relationship provided."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=None,
        )

        assert dialog.windowTitle() == "Add Relationship"
        assert not dialog._is_edit_mode

    def test_add_mode_source_entity_selectable(
        self, qapp, entity_pairs: tuple[tuple[str, str], ...]
    ) -> None:
        """Source entity combo should exist and be populated in add mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=None,
        )

        assert dialog._source_combo is not None
        # First item is placeholder "-- Select Source Entity --"
        assert dialog._source_combo.count() == len(entity_pairs) + 1
        # Check second item (first entity)
        assert dialog._source_combo.itemText(1) == "Project (project)"
        assert dialog._source_combo.itemData(1) == "project"

    def test_add_mode_target_entity_selectable(
        self, qapp, entity_pairs: tuple[tuple[str, str], ...]
    ) -> None:
        """Target entity combo should exist and be populated in add mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=None,
        )

        assert dialog._target_combo is not None
        # First item is placeholder "-- Select Target Entity --"
        assert dialog._target_combo.count() == len(entity_pairs) + 1

    def test_add_mode_relationship_id_editable(
        self, qapp, entity_pairs: tuple[tuple[str, str], ...]
    ) -> None:
        """Relationship ID input should exist in add mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=None,
        )

        assert dialog._relationship_id_input is not None
        assert dialog._relationship_id_input.isEnabled()

    def test_add_mode_relationship_type_selectable(
        self, qapp, entity_pairs: tuple[tuple[str, str], ...]
    ) -> None:
        """Relationship type combo should be populated with all types."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=None,
        )

        assert dialog._type_combo is not None
        assert dialog._type_combo.count() == 3  # CONTAINS, REFERENCES, ASSOCIATES
        assert dialog._type_combo.itemData(0) == "CONTAINS"
        assert dialog._type_combo.itemData(1) == "REFERENCES"
        assert dialog._type_combo.itemData(2) == "ASSOCIATES"


class TestAddRelationshipDialogEditMode:
    """Tests for AddRelationshipDialog in Edit mode (Phase A5.2/A6.2)."""

    @pytest.fixture
    def existing_relationship(self) -> RelationshipDTO:
        """Create sample existing relationship for edit mode."""
        return RelationshipDTO(
            id="project_contains_boreholes",
            source_entity_id="project",
            target_entity_id="borehole",
            relationship_type="CONTAINS",
            name_key="relationship.project_boreholes",
            description_key="relationship.project_boreholes.desc",
            inverse_name_key="relationship.borehole_project",
        )

    def test_edit_mode_initialization(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship: RelationshipDTO,
    ) -> None:
        """Dialog should initialize in edit mode when existing_relationship provided."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship,
        )

        assert dialog.windowTitle() == "Edit Relationship"
        assert dialog._is_edit_mode

    def test_edit_mode_source_entity_readonly(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship: RelationshipDTO,
    ) -> None:
        """Source entity should be displayed as read-only in edit mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship,
        )

        # Source combo should not exist in edit mode
        assert dialog._source_combo is None

    def test_edit_mode_target_entity_readonly(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship: RelationshipDTO,
    ) -> None:
        """Target entity should be displayed as read-only in edit mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship,
        )

        # Target combo should not exist in edit mode
        assert dialog._target_combo is None

    def test_edit_mode_relationship_id_readonly(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship: RelationshipDTO,
    ) -> None:
        """Relationship ID should be displayed as read-only in edit mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship,
        )

        # Relationship ID input should not exist in edit mode
        assert dialog._relationship_id_input is None

    def test_edit_mode_relationship_type_prefilled(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship: RelationshipDTO,
    ) -> None:
        """Relationship type should be pre-filled with existing type in edit mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship,
        )

        assert dialog._type_combo.currentData() == "CONTAINS"

    def test_edit_mode_name_key_prefilled(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship: RelationshipDTO,
    ) -> None:
        """Name key should be pre-filled with existing value in edit mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship,
        )

        assert dialog._name_key_input.text() == "relationship.project_boreholes"

    def test_edit_mode_description_key_prefilled(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship: RelationshipDTO,
    ) -> None:
        """Description key should be pre-filled with existing value in edit mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship,
        )

        assert dialog._description_key_input.text() == "relationship.project_boreholes.desc"

    def test_edit_mode_inverse_name_key_prefilled(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship: RelationshipDTO,
    ) -> None:
        """Inverse name key should be pre-filled with existing value in edit mode."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship,
        )

        assert dialog._inverse_name_key_input.text() == "relationship.borehole_project"


class TestAddRelationshipDialogGetters:
    """Tests for AddRelationshipDialog getter methods (Phase A5.2/A6.2)."""

    def test_get_relationship_data_returns_none_before_accept(
        self, qapp, entity_pairs: tuple[tuple[str, str], ...]
    ) -> None:
        """get_relationship_data should return None before dialog is accepted."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=None,
        )

        assert dialog.get_relationship_data() is None

    def test_relationship_types_constant(
        self, qapp, entity_pairs: tuple[tuple[str, str], ...]
    ) -> None:
        """RELATIONSHIP_TYPES constant should have all three types."""
        assert len(AddRelationshipDialog.RELATIONSHIP_TYPES) == 3
        types = [t[0] for t in AddRelationshipDialog.RELATIONSHIP_TYPES]
        assert "CONTAINS" in types
        assert "REFERENCES" in types
        assert "ASSOCIATES" in types


class TestAddRelationshipDialogEditModeWithNullOptionalFields:
    """Tests for Edit mode with null optional fields (Phase A5.2/A6.2)."""

    @pytest.fixture
    def existing_relationship_minimal(self) -> RelationshipDTO:
        """Create sample existing relationship with only required fields."""
        return RelationshipDTO(
            id="sample_references_lab",
            source_entity_id="sample",
            target_entity_id="borehole",
            relationship_type="REFERENCES",
            name_key="relationship.sample_lab",
            description_key=None,
            inverse_name_key=None,
        )

    def test_edit_mode_handles_null_description_key(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship_minimal: RelationshipDTO,
    ) -> None:
        """Edit mode should handle null description_key gracefully."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship_minimal,
        )

        # Should be empty, not "None" string
        assert dialog._description_key_input.text() == ""

    def test_edit_mode_handles_null_inverse_name_key(
        self,
        qapp,
        entity_pairs: tuple[tuple[str, str], ...],
        existing_relationship_minimal: RelationshipDTO,
    ) -> None:
        """Edit mode should handle null inverse_name_key gracefully."""
        dialog = AddRelationshipDialog(
            entities=entity_pairs,
            parent=None,
            existing_relationship=existing_relationship_minimal,
        )

        # Should be empty, not "None" string
        assert dialog._inverse_name_key_input.text() == ""
