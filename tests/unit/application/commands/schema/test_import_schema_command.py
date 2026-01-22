"""Unit tests for ImportSchemaCommand (Phase 4)."""

from unittest.mock import Mock

import pytest

from doc_helper.application.commands.schema.import_schema_command import ImportSchemaCommand
from doc_helper.application.dto.import_dto import (
    EnforcementPolicy,
    IdenticalSchemaAction,
)
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId


class TestImportSchemaCommand:
    """Tests for ImportSchemaCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        mock = Mock()
        mock.get_all.return_value = Success(())
        mock.delete.return_value = Success(None)
        mock.save.return_value = Success(None)
        return mock

    @pytest.fixture
    def command(self, mock_repository: Mock) -> ImportSchemaCommand:
        """Create command with mock repository."""
        return ImportSchemaCommand(mock_repository)

    @pytest.fixture
    def valid_import_data(self) -> dict:
        """Create valid import data."""
        return {
            "schema_id": "test_schema",
            "version": "1.0.0",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "text",
                            "label_key": "field.name",
                            "required": True,
                            "options": [],
                            "constraints": [],
                        }
                    ],
                }
            ],
        }

    @pytest.fixture
    def existing_entity(self) -> EntityDefinition:
        """Create existing entity for comparison tests."""
        field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            required=True,
        )
        return EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={field.id: field},
        )

    # =========================================================================
    # Basic Import Tests
    # =========================================================================

    def test_import_to_empty_repository_succeeds(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        valid_import_data: dict,
    ) -> None:
        """Should successfully import to empty repository."""
        result = command.execute_from_data(valid_import_data)

        assert result.success is True
        assert result.schema_id == "test_schema"
        assert result.imported_version == "1.0.0"
        assert result.entity_count == 1
        assert result.field_count == 1
        mock_repository.save.assert_called_once()

    def test_import_calls_save_for_each_entity(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
    ) -> None:
        """Should call save for each entity."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "entity1",
                    "name_key": "entity.1",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "f1", "field_type": "text", "label_key": "l1", "required": True, "options": [], "constraints": []}
                    ],
                },
                {
                    "id": "entity2",
                    "name_key": "entity.2",
                    "is_root_entity": False,
                    "fields": [
                        {"id": "f2", "field_type": "number", "label_key": "l2", "required": False, "options": [], "constraints": []}
                    ],
                },
            ],
        }
        result = command.execute_from_data(data)

        assert result.success is True
        assert result.entity_count == 2
        assert mock_repository.save.call_count == 2

    def test_import_invalid_data_fails(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
    ) -> None:
        """Should fail on invalid import data."""
        data = {
            "entities": [],  # Missing schema_id
        }
        result = command.execute_from_data(data)

        assert result.success is False
        assert len(result.validation_errors) > 0
        mock_repository.save.assert_not_called()

    # =========================================================================
    # Identical Schema Tests (Decision 1)
    # =========================================================================

    def test_identical_schema_skip_action(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        valid_import_data: dict,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should skip import when schema is identical and action is SKIP."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        result = command.execute_from_data(
            valid_import_data,
            identical_action=IdenticalSchemaAction.SKIP,
        )

        assert result.success is True
        assert result.was_identical is True
        assert result.was_skipped is True
        mock_repository.save.assert_not_called()
        mock_repository.delete.assert_not_called()

    def test_identical_schema_replace_action(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        valid_import_data: dict,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should replace when schema is identical and action is REPLACE."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        result = command.execute_from_data(
            valid_import_data,
            identical_action=IdenticalSchemaAction.REPLACE,
        )

        assert result.success is True
        assert result.was_identical is True
        assert result.was_skipped is False
        # Should have warning about replacing identical
        assert any(w.category == "identical_schema" for w in result.warnings)
        mock_repository.delete.assert_called_once()
        mock_repository.save.assert_called_once()

    # =========================================================================
    # Compatible Schema Tests (Decision 2)
    # =========================================================================

    def test_compatible_schema_replaces_with_change_list(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should replace compatible schema and include change list."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        # Import with additional field (compatible change)
        data = {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []},
                        {"id": "description", "field_type": "textarea", "label_key": "field.desc", "required": False, "options": [], "constraints": []},
                    ],
                }
            ],
        }
        result = command.execute_from_data(data)

        assert result.success is True
        assert result.compatibility_result is not None
        assert not result.compatibility_result.is_incompatible
        mock_repository.save.assert_called()

    # =========================================================================
    # Incompatible Schema Tests (Decision 3 & 4)
    # =========================================================================

    def test_incompatible_schema_fails_with_strict_policy(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should fail on incompatible schema with STRICT policy (default)."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        # Import with removed field (breaking change)
        data = {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [],  # Removed 'name' field
                }
            ],
        }
        result = command.execute_from_data(
            data,
            enforcement_policy=EnforcementPolicy.STRICT,
        )

        assert result.success is False
        assert "incompatible" in result.error.lower()
        assert result.compatibility_result is not None
        assert result.compatibility_result.is_incompatible
        mock_repository.save.assert_not_called()

    def test_incompatible_schema_warns_with_warn_policy(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should allow incompatible schema with WARN policy but include warnings."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        data = {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [],
                }
            ],
        }
        result = command.execute_from_data(
            data,
            enforcement_policy=EnforcementPolicy.WARN,
        )

        assert result.success is True
        assert any(w.category == "compatibility" for w in result.warnings)
        mock_repository.save.assert_called()

    def test_incompatible_schema_allowed_with_force_flag(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should allow incompatible schema with force flag."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        data = {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [],
                }
            ],
        }
        result = command.execute_from_data(
            data,
            enforcement_policy=EnforcementPolicy.STRICT,
            force=True,
        )

        assert result.success is True
        assert any(w.category == "compatibility" for w in result.warnings)

    def test_incompatible_schema_allowed_with_none_policy(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should allow incompatible schema with NONE policy."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        data = {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [],
                }
            ],
        }
        result = command.execute_from_data(
            data,
            enforcement_policy=EnforcementPolicy.NONE,
        )

        assert result.success is True

    # =========================================================================
    # Version Handling Tests (Decision 5)
    # =========================================================================

    def test_warns_on_version_backward(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should warn when imported version is older (Decision 5)."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        data = {
            "schema_id": "test_schema",
            "version": "0.9.0",  # Older than existing
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []}
                    ],
                }
            ],
        }
        result = command.execute_from_data(
            data,
            existing_version="1.0.0",
        )

        assert result.success is True
        assert any(w.category == "version_backward" for w in result.warnings)

    def test_no_warning_on_version_forward(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should not warn when imported version is newer."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        data = {
            "schema_id": "test_schema",
            "version": "2.0.0",  # Newer than existing
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []}
                    ],
                }
            ],
        }
        result = command.execute_from_data(
            data,
            existing_version="1.0.0",
        )

        assert result.success is True
        assert not any(w.category == "version_backward" for w in result.warnings)

    # =========================================================================
    # Empty Entity Tests (Decision 6)
    # =========================================================================

    def test_empty_entity_warns_but_allows(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
    ) -> None:
        """Should warn but allow entity with no fields (Decision 6)."""
        data = {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "empty_entity",
                    "name_key": "entity.empty",
                    "is_root_entity": True,
                    "fields": [],
                }
            ],
        }
        result = command.execute_from_data(data)

        assert result.success is True
        assert any(w.category == "empty_entity" for w in result.warnings)
        assert result.entity_count == 1
        assert result.field_count == 0

    # =========================================================================
    # Repository Error Handling Tests
    # =========================================================================

    def test_delete_failure_returns_error(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should return error when delete fails."""
        mock_repository.get_all.return_value = Success((existing_entity,))
        mock_repository.delete.return_value = Failure("Delete failed")

        data = {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []}
                    ],
                }
            ],
        }
        result = command.execute_from_data(
            data,
            identical_action=IdenticalSchemaAction.REPLACE,
        )

        assert result.success is False
        assert "delete" in result.error.lower()

    def test_save_failure_returns_error(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
    ) -> None:
        """Should return error when save fails."""
        mock_repository.save.return_value = Failure("Save failed")

        data = {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []}
                    ],
                }
            ],
        }
        result = command.execute_from_data(data)

        assert result.success is False
        assert "save" in result.error.lower()

    # =========================================================================
    # Result Content Tests
    # =========================================================================

    def test_result_includes_all_required_fields(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        valid_import_data: dict,
    ) -> None:
        """Should include all required fields in result."""
        result = command.execute_from_data(valid_import_data)

        assert result.success is True
        assert result.schema_id == "test_schema"
        assert result.imported_version == "1.0.0"
        assert result.entity_count == 1
        assert result.field_count == 1
        assert result.validation_errors == ()
        assert result.error is None

    def test_result_always_includes_compatibility_when_existing_schema(
        self,
        command: ImportSchemaCommand,
        mock_repository: Mock,
        valid_import_data: dict,
        existing_entity: EntityDefinition,
    ) -> None:
        """Should always include compatibility result when existing schema."""
        mock_repository.get_all.return_value = Success((existing_entity,))

        result = command.execute_from_data(valid_import_data)

        assert result.compatibility_result is not None
