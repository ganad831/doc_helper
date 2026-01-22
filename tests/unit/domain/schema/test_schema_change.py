"""Unit tests for SchemaChange and ChangeType (Phase 3)."""

import pytest

from doc_helper.domain.schema.schema_change import ChangeType, SchemaChange


class TestChangeType:
    """Unit tests for ChangeType enum."""

    # =========================================================================
    # Breaking Change Classification (Decision 3: Moderate Policy)
    # =========================================================================

    def test_entity_removed_is_breaking(self) -> None:
        """Entity removal should be breaking."""
        assert ChangeType.ENTITY_REMOVED.is_breaking is True

    def test_field_removed_is_breaking(self) -> None:
        """Field removal should be breaking."""
        assert ChangeType.FIELD_REMOVED.is_breaking is True

    def test_field_type_changed_is_breaking(self) -> None:
        """Field type change should be breaking."""
        assert ChangeType.FIELD_TYPE_CHANGED.is_breaking is True

    def test_option_removed_is_breaking(self) -> None:
        """Option removal should be breaking."""
        assert ChangeType.OPTION_REMOVED.is_breaking is True

    # =========================================================================
    # Non-Breaking Change Classification
    # =========================================================================

    def test_entity_added_is_not_breaking(self) -> None:
        """Entity addition should not be breaking."""
        assert ChangeType.ENTITY_ADDED.is_breaking is False

    def test_field_added_is_not_breaking(self) -> None:
        """Field addition should not be breaking."""
        assert ChangeType.FIELD_ADDED.is_breaking is False

    def test_field_required_changed_is_not_breaking(self) -> None:
        """Required flag change should not be breaking."""
        assert ChangeType.FIELD_REQUIRED_CHANGED.is_breaking is False

    def test_constraint_added_is_not_breaking(self) -> None:
        """Constraint addition should not be breaking."""
        assert ChangeType.CONSTRAINT_ADDED.is_breaking is False

    def test_constraint_removed_is_not_breaking(self) -> None:
        """Constraint removal should not be breaking."""
        assert ChangeType.CONSTRAINT_REMOVED.is_breaking is False

    def test_constraint_modified_is_not_breaking(self) -> None:
        """Constraint modification should not be breaking."""
        assert ChangeType.CONSTRAINT_MODIFIED.is_breaking is False

    def test_option_added_is_not_breaking(self) -> None:
        """Option addition should not be breaking."""
        assert ChangeType.OPTION_ADDED.is_breaking is False

    # =========================================================================
    # Structural Classification
    # =========================================================================

    def test_entity_added_is_structural(self) -> None:
        """Entity addition should be structural."""
        assert ChangeType.ENTITY_ADDED.is_structural is True

    def test_entity_removed_is_structural(self) -> None:
        """Entity removal should be structural."""
        assert ChangeType.ENTITY_REMOVED.is_structural is True

    def test_field_added_is_structural(self) -> None:
        """Field addition should be structural."""
        assert ChangeType.FIELD_ADDED.is_structural is True

    def test_field_removed_is_structural(self) -> None:
        """Field removal should be structural."""
        assert ChangeType.FIELD_REMOVED.is_structural is True

    def test_field_type_changed_is_structural(self) -> None:
        """Field type change should be structural."""
        assert ChangeType.FIELD_TYPE_CHANGED.is_structural is True

    def test_constraint_added_is_not_structural(self) -> None:
        """Constraint addition should not be structural."""
        assert ChangeType.CONSTRAINT_ADDED.is_structural is False

    def test_option_added_is_not_structural(self) -> None:
        """Option addition should not be structural."""
        assert ChangeType.OPTION_ADDED.is_structural is False


class TestSchemaChange:
    """Unit tests for SchemaChange value object."""

    # =========================================================================
    # Creation Tests
    # =========================================================================

    def test_create_entity_change(self) -> None:
        """Should create entity-level change."""
        change = SchemaChange(
            change_type=ChangeType.ENTITY_ADDED,
            entity_id="new_entity",
        )
        assert change.change_type == ChangeType.ENTITY_ADDED
        assert change.entity_id == "new_entity"
        assert change.field_id is None

    def test_create_field_change(self) -> None:
        """Should create field-level change."""
        change = SchemaChange(
            change_type=ChangeType.FIELD_REMOVED,
            entity_id="project",
            field_id="old_field",
        )
        assert change.change_type == ChangeType.FIELD_REMOVED
        assert change.entity_id == "project"
        assert change.field_id == "old_field"

    def test_create_field_type_change(self) -> None:
        """Should create field type change with old/new values."""
        change = SchemaChange(
            change_type=ChangeType.FIELD_TYPE_CHANGED,
            entity_id="project",
            field_id="status",
            old_value="text",
            new_value="dropdown",
        )
        assert change.old_value == "text"
        assert change.new_value == "dropdown"

    def test_create_constraint_change(self) -> None:
        """Should create constraint change."""
        change = SchemaChange(
            change_type=ChangeType.CONSTRAINT_ADDED,
            entity_id="project",
            field_id="name",
            constraint_type="MinLengthConstraint",
        )
        assert change.constraint_type == "MinLengthConstraint"

    def test_create_option_change(self) -> None:
        """Should create option change."""
        change = SchemaChange(
            change_type=ChangeType.OPTION_REMOVED,
            entity_id="project",
            field_id="status",
            option_value="archived",
        )
        assert change.option_value == "archived"

    # =========================================================================
    # is_breaking Property Tests
    # =========================================================================

    def test_breaking_change_property(self) -> None:
        """Should reflect change type breaking status."""
        breaking = SchemaChange(
            change_type=ChangeType.ENTITY_REMOVED,
            entity_id="old_entity",
        )
        assert breaking.is_breaking is True

        non_breaking = SchemaChange(
            change_type=ChangeType.ENTITY_ADDED,
            entity_id="new_entity",
        )
        assert non_breaking.is_breaking is False

    # =========================================================================
    # Location Property Tests
    # =========================================================================

    def test_location_entity_only(self) -> None:
        """Should return entity ID for entity-level changes."""
        change = SchemaChange(
            change_type=ChangeType.ENTITY_ADDED,
            entity_id="new_entity",
        )
        assert change.location == "new_entity"

    def test_location_entity_and_field(self) -> None:
        """Should return entity.field for field-level changes."""
        change = SchemaChange(
            change_type=ChangeType.FIELD_ADDED,
            entity_id="project",
            field_id="new_field",
        )
        assert change.location == "project.new_field"

    def test_location_with_constraint(self) -> None:
        """Should include constraint type in location."""
        change = SchemaChange(
            change_type=ChangeType.CONSTRAINT_ADDED,
            entity_id="project",
            field_id="name",
            constraint_type="MinLengthConstraint",
        )
        assert change.location == "project.name[MinLengthConstraint]"

    def test_location_with_option(self) -> None:
        """Should include option value in location."""
        change = SchemaChange(
            change_type=ChangeType.OPTION_REMOVED,
            entity_id="project",
            field_id="status",
            option_value="archived",
        )
        assert change.location == "project.status[option:archived]"

    # =========================================================================
    # Description Property Tests
    # =========================================================================

    def test_description_entity_added(self) -> None:
        """Should generate entity added description."""
        change = SchemaChange(
            change_type=ChangeType.ENTITY_ADDED,
            entity_id="new_entity",
        )
        assert "Entity 'new_entity' added" in change.description

    def test_description_field_removed(self) -> None:
        """Should generate field removed description."""
        change = SchemaChange(
            change_type=ChangeType.FIELD_REMOVED,
            entity_id="project",
            field_id="old_field",
        )
        assert "Field 'project.old_field' removed" in change.description

    def test_description_field_type_changed(self) -> None:
        """Should include old and new values in description."""
        change = SchemaChange(
            change_type=ChangeType.FIELD_TYPE_CHANGED,
            entity_id="project",
            field_id="status",
            old_value="text",
            new_value="dropdown",
        )
        assert "text" in change.description
        assert "dropdown" in change.description
