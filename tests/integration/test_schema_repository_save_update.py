"""Integration tests for schema repository save/update (Phase 2 Step 3).

Tests the enhanced save() method that now supports field updates.
"""

import pytest
import sqlite3
from pathlib import Path
from dataclasses import replace

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.infrastructure.persistence.sqlite.repositories.schema_repository import (
    SqliteSchemaRepository,
)


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Create temporary test database."""
    db_path = tmp_path / "test_schema.db"

    # Create schema tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE entities (
            id TEXT PRIMARY KEY,
            name_key TEXT NOT NULL,
            description_key TEXT,
            is_root_entity INTEGER NOT NULL DEFAULT 0,
            parent_entity_id TEXT,
            display_order INTEGER DEFAULT 0
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE fields (
            id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL,
            field_type TEXT NOT NULL,
            label_key TEXT NOT NULL,
            help_text_key TEXT,
            required INTEGER NOT NULL DEFAULT 0,
            default_value TEXT,
            display_order INTEGER DEFAULT 0,
            formula TEXT,
            lookup_entity_id TEXT,
            lookup_display_field TEXT,
            child_entity_id TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS validation_rules (
            id TEXT PRIMARY KEY,
            field_id TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            rule_value TEXT,
            error_message_key TEXT,
            FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def repository(test_db_path: Path) -> SqliteSchemaRepository:
    """Create repository instance."""
    return SqliteSchemaRepository(test_db_path)


@pytest.fixture
def sample_entity() -> EntityDefinition:
    """Create sample entity with fields."""
    field_text = FieldDefinition(
        id=FieldDefinitionId("field_text"),
        field_type=FieldType.TEXT,
        label_key=TranslationKey("field.text.label"),
        help_text_key=TranslationKey("field.text.help"),
        required=True,
        default_value="default_value",
    )

    field_number = FieldDefinition(
        id=FieldDefinitionId("field_number"),
        field_type=FieldType.NUMBER,
        label_key=TranslationKey("field.number.label"),
        required=False,
        default_value="0",
    )

    return EntityDefinition(
        id=EntityDefinitionId("test_entity"),
        name_key=TranslationKey("entity.test"),
        description_key=TranslationKey("entity.test.description"),
        fields={field_text.id: field_text, field_number.id: field_number},
        is_root_entity=False,
        parent_entity_id=None,
    )


class TestSchemaRepositorySaveUpdate:
    """Integration tests for save() method with field updates."""

    # =========================================================================
    # Phase 2 Step 2: CREATE and ADD FIELDS (existing behavior)
    # =========================================================================

    def test_save_new_entity_with_fields(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should create new entity with all fields."""
        # Execute
        result = repository.save(sample_entity)

        # Assert
        assert result.is_success()

        # Verify entity was created
        assert repository.exists(sample_entity.id)

        # Verify fields were created
        loaded_result = repository.get_by_id(sample_entity.id)
        assert loaded_result.is_success()

        loaded_entity = loaded_result.value
        assert len(loaded_entity.fields) == 2
        assert FieldDefinitionId("field_text") in loaded_entity.fields
        assert FieldDefinitionId("field_number") in loaded_entity.fields

    def test_save_add_new_field_to_existing_entity(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should add new field to existing entity."""
        # Setup: Create entity with initial fields
        repository.save(sample_entity)

        # Add new field to entity
        new_field = FieldDefinition(
            id=FieldDefinitionId("field_date"),
            field_type=FieldType.DATE,
            label_key=TranslationKey("field.date.label"),
            required=False,
        )

        updated_fields = dict(sample_entity.fields)
        updated_fields[new_field.id] = new_field
        entity_with_new_field = replace(sample_entity, fields=updated_fields)

        # Execute: Save entity with new field
        result = repository.save(entity_with_new_field)

        # Assert
        assert result.is_success()

        # Verify field was added
        loaded_result = repository.get_by_id(sample_entity.id)
        assert loaded_result.is_success()

        loaded_entity = loaded_result.value
        assert len(loaded_entity.fields) == 3
        assert FieldDefinitionId("field_date") in loaded_entity.fields

    # =========================================================================
    # Phase 2 Step 3: UPDATE FIELDS (new behavior)
    # =========================================================================

    def test_save_update_existing_field_label(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should update existing field's label_key."""
        # Setup: Create entity
        repository.save(sample_entity)

        # Modify field label
        original_field = sample_entity.fields[FieldDefinitionId("field_text")]
        updated_field = replace(original_field, label_key=TranslationKey("field.text.label.updated"))

        updated_fields = dict(sample_entity.fields)
        updated_fields[updated_field.id] = updated_field
        entity_with_updated_field = replace(sample_entity, fields=updated_fields)

        # Execute: Save entity with updated field
        result = repository.save(entity_with_updated_field)

        # Assert
        assert result.is_success()

        # Verify field was updated
        loaded_result = repository.get_by_id(sample_entity.id)
        assert loaded_result.is_success()

        loaded_entity = loaded_result.value
        loaded_field = loaded_entity.fields[FieldDefinitionId("field_text")]
        assert loaded_field.label_key == TranslationKey("field.text.label.updated")

    def test_save_update_existing_field_help_text(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should update existing field's help_text_key."""
        # Setup: Create entity
        repository.save(sample_entity)

        # Modify field help text
        original_field = sample_entity.fields[FieldDefinitionId("field_text")]
        updated_field = replace(original_field, help_text_key=TranslationKey("field.text.help.updated"))

        updated_fields = dict(sample_entity.fields)
        updated_fields[updated_field.id] = updated_field
        entity_with_updated_field = replace(sample_entity, fields=updated_fields)

        # Execute
        result = repository.save(entity_with_updated_field)

        # Assert
        assert result.is_success()

        # Verify
        loaded_result = repository.get_by_id(sample_entity.id)
        loaded_field = loaded_result.value.fields[FieldDefinitionId("field_text")]
        assert loaded_field.help_text_key == TranslationKey("field.text.help.updated")

    def test_save_update_field_required_flag(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should update existing field's required flag."""
        # Setup
        repository.save(sample_entity)

        # Modify field required flag (from True to False)
        original_field = sample_entity.fields[FieldDefinitionId("field_text")]
        updated_field = replace(original_field, required=False)

        updated_fields = dict(sample_entity.fields)
        updated_fields[updated_field.id] = updated_field
        entity_with_updated_field = replace(sample_entity, fields=updated_fields)

        # Execute
        result = repository.save(entity_with_updated_field)

        # Assert
        assert result.is_success()

        # Verify
        loaded_result = repository.get_by_id(sample_entity.id)
        loaded_field = loaded_result.value.fields[FieldDefinitionId("field_text")]
        assert loaded_field.required is False

    def test_save_update_field_default_value(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should update existing field's default_value."""
        # Setup
        repository.save(sample_entity)

        # Modify field default value
        original_field = sample_entity.fields[FieldDefinitionId("field_text")]
        updated_field = replace(original_field, default_value="new_default")

        updated_fields = dict(sample_entity.fields)
        updated_fields[updated_field.id] = updated_field
        entity_with_updated_field = replace(sample_entity, fields=updated_fields)

        # Execute
        result = repository.save(entity_with_updated_field)

        # Assert
        assert result.is_success()

        # Verify
        loaded_result = repository.get_by_id(sample_entity.id)
        loaded_field = loaded_result.value.fields[FieldDefinitionId("field_text")]
        assert loaded_field.default_value == "new_default"

    def test_save_update_multiple_fields(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should update multiple existing fields in one save."""
        # Setup
        repository.save(sample_entity)

        # Modify both fields
        updated_field_text = replace(
            sample_entity.fields[FieldDefinitionId("field_text")],
            label_key=TranslationKey("field.text.updated"),
        )
        updated_field_number = replace(
            sample_entity.fields[FieldDefinitionId("field_number")],
            label_key=TranslationKey("field.number.updated"),
        )

        updated_fields = {
            updated_field_text.id: updated_field_text,
            updated_field_number.id: updated_field_number,
        }
        entity_with_updated_fields = replace(sample_entity, fields=updated_fields)

        # Execute
        result = repository.save(entity_with_updated_fields)

        # Assert
        assert result.is_success()

        # Verify both fields were updated
        loaded_result = repository.get_by_id(sample_entity.id)
        loaded_entity = loaded_result.value

        assert loaded_entity.fields[FieldDefinitionId("field_text")].label_key == TranslationKey(
            "field.text.updated"
        )
        assert loaded_entity.fields[FieldDefinitionId("field_number")].label_key == TranslationKey(
            "field.number.updated"
        )

    def test_save_mixed_add_and_update_fields(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should handle both adding new fields and updating existing fields."""
        # Setup
        repository.save(sample_entity)

        # Update existing field
        updated_field_text = replace(
            sample_entity.fields[FieldDefinitionId("field_text")],
            label_key=TranslationKey("field.text.updated"),
        )

        # Add new field
        new_field_date = FieldDefinition(
            id=FieldDefinitionId("field_date"),
            field_type=FieldType.DATE,
            label_key=TranslationKey("field.date.label"),
            required=False,
        )

        updated_fields = {
            updated_field_text.id: updated_field_text,
            FieldDefinitionId("field_number"): sample_entity.fields[FieldDefinitionId("field_number")],
            new_field_date.id: new_field_date,
        }
        entity_with_changes = replace(sample_entity, fields=updated_fields)

        # Execute
        result = repository.save(entity_with_changes)

        # Assert
        assert result.is_success()

        # Verify: updated field changed, new field added
        loaded_result = repository.get_by_id(sample_entity.id)
        loaded_entity = loaded_result.value

        assert len(loaded_entity.fields) == 3
        assert loaded_entity.fields[FieldDefinitionId("field_text")].label_key == TranslationKey(
            "field.text.updated"
        )
        assert FieldDefinitionId("field_date") in loaded_entity.fields


class TestSchemaRepositoryEntityUpdate:
    """Integration tests for update() method (entity metadata)."""

    def test_update_entity_name_key(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should update entity name_key."""
        # Setup: Create entity
        repository.save(sample_entity)

        # Modify entity name
        updated_entity = replace(sample_entity, name_key=TranslationKey("entity.test.updated"))

        # Execute
        result = repository.update(updated_entity)

        # Assert
        assert result.is_success()

        # Verify
        loaded_result = repository.get_by_id(sample_entity.id)
        assert loaded_result.value.name_key == TranslationKey("entity.test.updated")

    def test_update_entity_description_key(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should update entity description_key."""
        # Setup
        repository.save(sample_entity)

        # Modify entity description
        updated_entity = replace(
            sample_entity, description_key=TranslationKey("entity.test.description.updated")
        )

        # Execute
        result = repository.update(updated_entity)

        # Assert
        assert result.is_success()

        # Verify
        loaded_result = repository.get_by_id(sample_entity.id)
        assert loaded_result.value.description_key == TranslationKey("entity.test.description.updated")

    def test_update_entity_root_status(
        self, repository: SqliteSchemaRepository, sample_entity: EntityDefinition
    ) -> None:
        """Should update entity is_root_entity flag."""
        # Setup
        repository.save(sample_entity)

        # Change to root entity
        updated_entity = replace(sample_entity, is_root_entity=True, parent_entity_id=None)

        # Execute
        result = repository.update(updated_entity)

        # Assert
        assert result.is_success()

        # Verify
        loaded_result = repository.get_by_id(sample_entity.id)
        assert loaded_result.value.is_root_entity is True
        assert loaded_result.value.parent_entity_id is None

    def test_update_nonexistent_entity_fails(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should reject update of non-existent entity."""
        # Create entity that doesn't exist in database
        nonexistent_entity = EntityDefinition(
            id=EntityDefinitionId("nonexistent"),
            name_key=TranslationKey("entity.nonexistent"),
            fields={},
            is_root_entity=False,
            parent_entity_id=None,
        )

        # Execute
        result = repository.update(nonexistent_entity)

        # Assert
        assert result.is_failure()
        assert "does not exist" in result.error.lower()


class TestSchemaRepositoryConstraintPersistence:
    """Integration tests for constraint persistence in schema repository.

    Tests that FieldConstraint objects are correctly persisted to and loaded
    from the validation_rules table via the ConstraintFactory.
    """

    @pytest.fixture
    def test_db_path(self, tmp_path: Path) -> Path:
        """Create temporary test database with validation_rules table."""
        db_path = tmp_path / "test_constraints.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE entities (
                id TEXT PRIMARY KEY,
                name_key TEXT NOT NULL,
                description_key TEXT,
                is_root_entity INTEGER NOT NULL DEFAULT 0,
                parent_entity_id TEXT,
                display_order INTEGER DEFAULT 0
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE fields (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                field_type TEXT NOT NULL,
                label_key TEXT NOT NULL,
                help_text_key TEXT,
                required INTEGER NOT NULL DEFAULT 0,
                default_value TEXT,
                display_order INTEGER DEFAULT 0,
                formula TEXT,
                lookup_entity_id TEXT,
                lookup_display_field TEXT,
                child_entity_id TEXT,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS validation_rules (
                id TEXT PRIMARY KEY,
                field_id TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                rule_value TEXT,
                error_message_key TEXT,
                FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()
        conn.close()

        return db_path

    @pytest.fixture
    def repository(self, test_db_path: Path) -> SqliteSchemaRepository:
        """Create repository instance."""
        return SqliteSchemaRepository(test_db_path)

    def test_save_and_load_required_constraint(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should persist and reload RequiredConstraint through ConstraintFactory."""
        from doc_helper.domain.validation.constraints import RequiredConstraint

        # Create field with RequiredConstraint
        field_with_required = FieldDefinition(
            id=FieldDefinitionId("required_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.required"),
            required=True,
            constraints=(RequiredConstraint(),),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("constraint_test_entity"),
            name_key=TranslationKey("entity.constraint_test"),
            fields={field_with_required.id: field_with_required},
            is_root_entity=False,
        )

        # Save
        result = repository.save(entity)
        assert result.is_success()

        # Load and verify constraint was persisted
        loaded_result = repository.get_by_id(entity.id)
        assert loaded_result.is_success()

        loaded_entity = loaded_result.value
        loaded_field = loaded_entity.fields[FieldDefinitionId("required_field")]

        # Verify constraints were loaded
        assert len(loaded_field.constraints) == 1
        assert isinstance(loaded_field.constraints[0], RequiredConstraint)

    def test_save_and_load_multiple_constraints(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should persist and reload multiple constraints."""
        from doc_helper.domain.validation.constraints import (
            RequiredConstraint,
            MinLengthConstraint,
            MaxLengthConstraint,
        )

        # Create field with multiple constraints
        field_with_constraints = FieldDefinition(
            id=FieldDefinitionId("multi_constraint_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.multi_constraint"),
            required=True,
            constraints=(
                RequiredConstraint(),
                MinLengthConstraint(min_length=5),
                MaxLengthConstraint(max_length=100),
            ),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("multi_constraint_entity"),
            name_key=TranslationKey("entity.multi_constraint"),
            fields={field_with_constraints.id: field_with_constraints},
            is_root_entity=False,
        )

        # Save
        result = repository.save(entity)
        assert result.is_success()

        # Load and verify
        loaded_result = repository.get_by_id(entity.id)
        assert loaded_result.is_success()

        loaded_field = loaded_result.value.fields[FieldDefinitionId("multi_constraint_field")]

        # Verify all constraints were loaded
        assert len(loaded_field.constraints) == 3

        # Check constraint types and values
        constraint_types = {type(c).__name__ for c in loaded_field.constraints}
        assert "RequiredConstraint" in constraint_types
        assert "MinLengthConstraint" in constraint_types
        assert "MaxLengthConstraint" in constraint_types

        # Check constraint values
        for c in loaded_field.constraints:
            if isinstance(c, MinLengthConstraint):
                assert c.min_length == 5
            elif isinstance(c, MaxLengthConstraint):
                assert c.max_length == 100

    def test_update_field_constraints(
        self, repository: SqliteSchemaRepository
    ) -> None:
        """Should update field constraints on save."""
        from doc_helper.domain.validation.constraints import (
            RequiredConstraint,
            MinLengthConstraint,
        )

        # Initial field with RequiredConstraint
        initial_field = FieldDefinition(
            id=FieldDefinitionId("update_test_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.update_test"),
            required=True,
            constraints=(RequiredConstraint(),),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("update_constraint_entity"),
            name_key=TranslationKey("entity.update_constraint"),
            fields={initial_field.id: initial_field},
            is_root_entity=False,
        )

        # Save initial
        repository.save(entity)

        # Update: add MinLengthConstraint
        updated_field = replace(
            initial_field,
            constraints=(RequiredConstraint(), MinLengthConstraint(min_length=10)),
        )

        updated_entity = replace(
            entity,
            fields={updated_field.id: updated_field},
        )

        # Save updated
        result = repository.save(updated_entity)
        assert result.is_success()

        # Load and verify constraints were updated
        loaded_result = repository.get_by_id(entity.id)
        loaded_field = loaded_result.value.fields[FieldDefinitionId("update_test_field")]

        assert len(loaded_field.constraints) == 2
        constraint_types = {type(c).__name__ for c in loaded_field.constraints}
        assert "RequiredConstraint" in constraint_types
        assert "MinLengthConstraint" in constraint_types
