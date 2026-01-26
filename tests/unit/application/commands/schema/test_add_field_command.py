"""Unit tests for AddFieldCommand (Phase 2 Step 2)."""

import pytest
from unittest.mock import Mock

from doc_helper.application.commands.schema.add_field_command import AddFieldCommand
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_repository import ISchemaRepository


class TestAddFieldCommand:
    """Unit tests for AddFieldCommand."""

    @pytest.fixture
    def mock_entity(self) -> EntityDefinition:
        """Create a mock entity."""
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test_entity"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=None,
        )

    @pytest.fixture
    def mock_repository(self, mock_entity: EntityDefinition) -> Mock:
        """Create mock schema repository."""
        repository = Mock(spec=ISchemaRepository)
        repository.exists = Mock(return_value=True)
        repository.get_by_id = Mock(return_value=Success(mock_entity))
        repository.save = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def command(self, mock_repository: Mock) -> AddFieldCommand:
        """Create command instance with mock repository."""
        return AddFieldCommand(mock_repository)

    def test_add_field_success(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should successfully add field when inputs are valid."""
        result = command.execute(
            entity_id="test_entity",
            field_id="test_field",
            field_type="text",
            label_key="field.test_field",
            help_text_key="field.test_field.help",
            required=True,
            default_value="default_text",
        )

        # Assert success
        assert result.is_success()
        assert result.value == FieldDefinitionId("test_field")

        # Assert repository methods called correctly
        mock_repository.exists.assert_called_once_with(
            EntityDefinitionId("test_entity")
        )
        mock_repository.get_by_id.assert_called_once_with(
            EntityDefinitionId("test_entity")
        )
        mock_repository.save.assert_called_once()

        # Check saved entity has the new field
        saved_entity = mock_repository.save.call_args[0][0]
        assert isinstance(saved_entity, EntityDefinition)
        assert len(saved_entity.fields) == 1
        assert FieldDefinitionId("test_field") in saved_entity.fields

        # Check field properties
        field = saved_entity.fields[FieldDefinitionId("test_field")]
        assert field.field_type == FieldType.TEXT
        assert field.label_key == TranslationKey("field.test_field")
        assert field.help_text_key == TranslationKey("field.test_field.help")
        assert field.required is True
        assert field.default_value == "default_text"

    def test_add_field_creates_required_constraint_when_required_true(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should create RequiredConstraint when required=True.

        This verifies BUG FIX: Previously, setting required=True did not
        create the RequiredConstraint, causing the validation rule not to
        appear in the Validation Rules panel.
        """
        from doc_helper.domain.validation.constraints import RequiredConstraint

        result = command.execute(
            entity_id="test_entity",
            field_id="required_field",
            field_type="text",
            label_key="field.required_field",
            required=True,
        )

        assert result.is_success()
        saved_entity = mock_repository.save.call_args[0][0]
        field = saved_entity.fields[FieldDefinitionId("required_field")]

        # CRITICAL: Verify RequiredConstraint is in constraints tuple
        assert field.required is True
        assert len(field.constraints) == 1
        assert isinstance(field.constraints[0], RequiredConstraint)

    def test_add_field_no_constraint_when_required_false(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should not create RequiredConstraint when required=False."""
        result = command.execute(
            entity_id="test_entity",
            field_id="optional_field",
            field_type="text",
            label_key="field.optional_field",
            required=False,
        )

        assert result.is_success()
        saved_entity = mock_repository.save.call_args[0][0]
        field = saved_entity.fields[FieldDefinitionId("optional_field")]

        # No constraints for optional fields
        assert field.required is False
        assert len(field.constraints) == 0

    def test_add_field_without_optional_params(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should successfully add field without optional parameters."""
        result = command.execute(
            entity_id="test_entity",
            field_id="test_field",
            field_type="number",
            label_key="field.test_field",
        )

        assert result.is_success()
        saved_entity = mock_repository.save.call_args[0][0]
        field = saved_entity.fields[FieldDefinitionId("test_field")]
        assert field.help_text_key is None
        assert field.required is False
        assert field.default_value is None

    def test_add_field_all_field_types(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should support field types that can be created in Phase 2 Step 2.

        Note: DROPDOWN, RADIO, CALCULATED, LOOKUP, TABLE cannot be created
        without additional data (options, formula, entity references).
        These will be testable in Phase 2 Step 3 when editing is implemented.
        """
        # Field types that can be created without additional data
        field_types = [
            "text",
            "textarea",
            "number",
            "date",
            "checkbox",
            "file",
            "image",
        ]

        for field_type in field_types:
            result = command.execute(
                entity_id="test_entity",
                field_id=f"field_{field_type.lower()}",
                field_type=field_type,
                label_key=f"field.{field_type.lower()}",
            )
            assert result.is_success(), f"Failed for field type: {field_type}"

    def test_add_field_duplicate_rejection(
        self, command: AddFieldCommand, mock_repository: Mock, mock_entity: EntityDefinition
    ) -> None:
        """Should reject duplicate field ID within same entity."""
        # Add existing field to entity
        existing_field = FieldDefinition(
            id=FieldDefinitionId("existing_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.existing"),
            help_text_key=None,
            required=False,
            default_value=None,
            constraints=(),
            options=(),
            formula=None,
            lookup_entity_id=None,
            lookup_display_field=None,
            child_entity_id=None,
            control_rules=(),
        )
        mock_entity.fields[FieldDefinitionId("existing_field")] = existing_field

        result = command.execute(
            entity_id="test_entity",
            field_id="existing_field",
            field_type="text",
            label_key="field.duplicate",
        )

        # Assert failure
        assert result.is_failure()
        assert "already exists" in result.error.lower()

        # Assert save not called
        mock_repository.save.assert_not_called()

    def test_add_field_invalid_field_type_rejection(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject invalid field type."""
        result = command.execute(
            entity_id="test_entity",
            field_id="test_field",
            field_type="INVALID_TYPE",
            label_key="field.test_field",
        )

        # Assert failure
        assert result.is_failure()
        assert "invalid field_type" in result.error.lower()
        assert "INVALID_TYPE" in result.error

        # Assert save not called
        mock_repository.save.assert_not_called()

    def test_add_field_to_nonexistent_entity(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject adding field to nonexistent entity."""
        # Mock repository to indicate entity does not exist
        mock_repository.exists.return_value = False

        result = command.execute(
            entity_id="nonexistent_entity",
            field_id="test_field",
            field_type="text",
            label_key="field.test_field",
        )

        # Assert failure
        assert result.is_failure()
        assert "does not exist" in result.error.lower()

    def test_add_field_missing_entity_id(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject missing entity_id."""
        result = command.execute(
            entity_id="",
            field_id="test_field",
            field_type="text",
            label_key="field.test_field",
        )

        assert result.is_failure()
        assert "entity_id is required" in result.error

    def test_add_field_missing_field_id(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject missing field_id."""
        result = command.execute(
            entity_id="test_entity",
            field_id="",
            field_type="text",
            label_key="field.test_field",
        )

        assert result.is_failure()
        assert "field_id is required" in result.error

    def test_add_field_missing_field_type(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject missing field_type."""
        result = command.execute(
            entity_id="test_entity",
            field_id="test_field",
            field_type="",
            label_key="field.test_field",
        )

        assert result.is_failure()
        assert "field_type is required" in result.error

    def test_add_field_missing_label_key(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should reject missing label_key."""
        result = command.execute(
            entity_id="test_entity",
            field_id="test_field",
            field_type="text",
            label_key="",
        )

        assert result.is_failure()
        assert "label_key is required" in result.error

    def test_add_field_repository_load_failure(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should propagate repository load failure."""
        mock_repository.get_by_id.return_value = Failure("Database error: connection lost")

        result = command.execute(
            entity_id="test_entity",
            field_id="test_field",
            field_type="text",
            label_key="field.test_field",
        )

        assert result.is_failure()
        assert "failed to load entity" in result.error.lower()

    def test_add_field_repository_save_failure(
        self, command: AddFieldCommand, mock_repository: Mock
    ) -> None:
        """Should propagate repository save failure."""
        mock_repository.save.return_value = Failure("Database error: constraint violation")

        result = command.execute(
            entity_id="test_entity",
            field_id="test_field",
            field_type="text",
            label_key="field.test_field",
        )

        assert result.is_failure()
        assert "failed to save field" in result.error.lower()
