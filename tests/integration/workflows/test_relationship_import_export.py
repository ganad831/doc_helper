"""Integration tests for relationship import/export (Phase 6A - ADR-022).

Tests that relationship data is correctly handled during schema export/import.
"""

import json
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    FieldDefinitionId,
    RelationshipDefinitionId,
)
from doc_helper.application.commands.schema.export_schema_command import (
    ExportSchemaCommand,
)
from doc_helper.application.services.schema_import_validation_service import (
    SchemaImportValidationService,
)
from doc_helper.infrastructure.interchange import JsonSchemaExportWriter


class TestRelationshipExport:
    """Tests for relationship export functionality."""

    @pytest.fixture
    def sample_entities(self) -> tuple:
        """Create sample entities for testing."""
        project_field = FieldDefinition(
            id=FieldDefinitionId("project_name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.project_name"),
            required=True,
        )
        project = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            fields={project_field.id: project_field},
            is_root_entity=True,
        )

        borehole_field = FieldDefinition(
            id=FieldDefinitionId("depth"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.depth"),
        )
        borehole = EntityDefinition(
            id=EntityDefinitionId("borehole"),
            name_key=TranslationKey("entity.borehole"),
            fields={borehole_field.id: borehole_field},
        )

        return (project, borehole)

    @pytest.fixture
    def sample_relationships(self) -> tuple:
        """Create sample relationships for testing."""
        rel = RelationshipDefinition(
            id=RelationshipDefinitionId("project_contains_boreholes"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.CONTAINS,
            name_key=TranslationKey("relationship.project_boreholes"),
            description_key=TranslationKey("relationship.project_boreholes.desc"),
            inverse_name_key=TranslationKey("relationship.borehole_project"),
        )
        return (rel,)

    def test_export_includes_relationships(
        self,
        sample_entities: tuple,
        sample_relationships: tuple,
        tmp_path: Path,
    ) -> None:
        """Export should include relationships in output."""
        # Arrange: Mock repositories
        schema_repo = MagicMock()
        schema_repo.get_all.return_value = Success(sample_entities)

        relationship_repo = MagicMock()
        relationship_repo.get_all.return_value = Success(sample_relationships)

        export_path = tmp_path / "schema_export.json"
        schema_export_writer = JsonSchemaExportWriter()
        command = ExportSchemaCommand(
            schema_repo, schema_export_writer, relationship_repository=relationship_repo
        )

        # Act
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert isinstance(result, Success)
        assert export_path.exists()

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "relationships" in data
        assert len(data["relationships"]) == 1

        rel_data = data["relationships"][0]
        assert rel_data["id"] == "project_contains_boreholes"
        assert rel_data["source_entity_id"] == "project"
        assert rel_data["target_entity_id"] == "borehole"
        assert rel_data["relationship_type"] == "CONTAINS"
        assert rel_data["name_key"] == "relationship.project_boreholes"
        assert rel_data["description_key"] == "relationship.project_boreholes.desc"
        assert rel_data["inverse_name_key"] == "relationship.borehole_project"

    def test_export_without_relationship_repository(
        self,
        sample_entities: tuple,
        tmp_path: Path,
    ) -> None:
        """Export should work without relationship repository."""
        # Arrange: Mock only schema repository
        schema_repo = MagicMock()
        schema_repo.get_all.return_value = Success(sample_entities)

        export_path = tmp_path / "schema_export.json"
        schema_export_writer = JsonSchemaExportWriter()
        command = ExportSchemaCommand(schema_repo, schema_export_writer)  # No relationship repo

        # Act
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert isinstance(result, Success)

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Should have empty relationships array
        assert "relationships" in data
        assert data["relationships"] == []

    def test_export_with_empty_relationships(
        self,
        sample_entities: tuple,
        tmp_path: Path,
    ) -> None:
        """Export should handle empty relationships list."""
        # Arrange
        schema_repo = MagicMock()
        schema_repo.get_all.return_value = Success(sample_entities)

        relationship_repo = MagicMock()
        relationship_repo.get_all.return_value = Success(())  # Empty

        export_path = tmp_path / "schema_export.json"
        schema_export_writer = JsonSchemaExportWriter()
        command = ExportSchemaCommand(
            schema_repo, schema_export_writer, relationship_repository=relationship_repo
        )

        # Act
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert isinstance(result, Success)

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["relationships"] == []

    def test_export_relationship_with_minimal_fields(
        self,
        sample_entities: tuple,
        tmp_path: Path,
    ) -> None:
        """Export should handle relationship with only required fields."""
        # Arrange
        minimal_rel = RelationshipDefinition(
            id=RelationshipDefinitionId("minimal_rel"),
            source_entity_id=EntityDefinitionId("project"),
            target_entity_id=EntityDefinitionId("borehole"),
            relationship_type=RelationshipType.REFERENCES,
            name_key=TranslationKey("relationship.minimal"),
            # No description_key or inverse_name_key
        )

        schema_repo = MagicMock()
        schema_repo.get_all.return_value = Success(sample_entities)

        relationship_repo = MagicMock()
        relationship_repo.get_all.return_value = Success((minimal_rel,))

        export_path = tmp_path / "schema_export.json"
        schema_export_writer = JsonSchemaExportWriter()
        command = ExportSchemaCommand(
            schema_repo, schema_export_writer, relationship_repository=relationship_repo
        )

        # Act
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert isinstance(result, Success)

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rel_data = data["relationships"][0]
        assert rel_data["id"] == "minimal_rel"
        assert rel_data["description_key"] is None
        assert rel_data["inverse_name_key"] is None


class TestRelationshipImportValidation:
    """Tests for relationship import validation."""

    @pytest.fixture
    def validation_service(self) -> SchemaImportValidationService:
        """Create validation service."""
        return SchemaImportValidationService()

    def test_validate_relationship_structure_valid(
        self, validation_service: SchemaImportValidationService
    ) -> None:
        """Should accept valid relationship structure."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "TEXT",
                            "label_key": "field.name",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
                {
                    "id": "borehole",
                    "name_key": "entity.borehole",
                    "is_root_entity": False,
                    "fields": [
                        {
                            "id": "depth",
                            "field_type": "NUMBER",
                            "label_key": "field.depth",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
            ],
            "relationships": [
                {
                    "id": "project_boreholes",
                    "source_entity_id": "project",
                    "target_entity_id": "borehole",
                    "relationship_type": "CONTAINS",
                    "name_key": "relationship.project_boreholes",
                }
            ],
        }

        result = validation_service.validate_json_data(data)

        assert isinstance(result, Success)
        assert "relationships" in result.value
        assert len(result.value["relationships"]) == 1

    def test_validate_relationship_missing_required_field(
        self, validation_service: SchemaImportValidationService
    ) -> None:
        """Should reject relationship missing required fields."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "TEXT",
                            "label_key": "field.name",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
            ],
            "relationships": [
                {
                    "id": "invalid",
                    # Missing source_entity_id
                    "target_entity_id": "borehole",
                    "relationship_type": "CONTAINS",
                    "name_key": "relationship.test",
                }
            ],
        }

        result = validation_service.validate_json_data(data)

        assert isinstance(result, Failure)
        # Should have validation error about missing field
        errors = result.error
        assert len(errors) > 0

    def test_validate_relationship_invalid_type(
        self, validation_service: SchemaImportValidationService
    ) -> None:
        """Should reject relationship with invalid relationship_type."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "TEXT",
                            "label_key": "field.name",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
                {
                    "id": "borehole",
                    "name_key": "entity.borehole",
                    "is_root_entity": False,
                    "fields": [
                        {
                            "id": "depth",
                            "field_type": "NUMBER",
                            "label_key": "field.depth",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
            ],
            "relationships": [
                {
                    "id": "test_rel",
                    "source_entity_id": "project",
                    "target_entity_id": "borehole",
                    "relationship_type": "INVALID_TYPE",  # Invalid
                    "name_key": "relationship.test",
                }
            ],
        }

        result = validation_service.validate_json_data(data)

        assert isinstance(result, Failure)
        errors = result.error
        has_type_error = any("relationship_type" in str(e) for e in errors)
        assert has_type_error

    def test_validate_relationship_entity_not_in_schema(
        self, validation_service: SchemaImportValidationService
    ) -> None:
        """Should reject relationship referencing non-existent entity."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "TEXT",
                            "label_key": "field.name",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
            ],
            "relationships": [
                {
                    "id": "test_rel",
                    "source_entity_id": "project",
                    "target_entity_id": "nonexistent",  # Not in entities
                    "relationship_type": "CONTAINS",
                    "name_key": "relationship.test",
                }
            ],
        }

        result = validation_service.validate_json_data(data)

        assert isinstance(result, Failure)
        errors = result.error
        has_entity_error = any("nonexistent" in str(e).lower() for e in errors)
        assert has_entity_error

    def test_validate_relationship_with_optional_fields(
        self, validation_service: SchemaImportValidationService
    ) -> None:
        """Should accept relationship with all optional fields."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "TEXT",
                            "label_key": "field.name",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
                {
                    "id": "borehole",
                    "name_key": "entity.borehole",
                    "is_root_entity": False,
                    "fields": [
                        {
                            "id": "depth",
                            "field_type": "NUMBER",
                            "label_key": "field.depth",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
            ],
            "relationships": [
                {
                    "id": "full_rel",
                    "source_entity_id": "project",
                    "target_entity_id": "borehole",
                    "relationship_type": "CONTAINS",
                    "name_key": "relationship.full",
                    "description_key": "relationship.full.desc",
                    "inverse_name_key": "relationship.inverse",
                }
            ],
        }

        result = validation_service.validate_json_data(data)

        assert isinstance(result, Success)
        rels = result.value["relationships"]
        assert len(rels) == 1
        rel = rels[0]
        assert rel.description_key.key == "relationship.full.desc"
        assert rel.inverse_name_key.key == "relationship.inverse"

    def test_validate_empty_relationships_section(
        self, validation_service: SchemaImportValidationService
    ) -> None:
        """Should accept empty relationships array."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "TEXT",
                            "label_key": "field.name",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
            ],
            "relationships": [],
        }

        result = validation_service.validate_json_data(data)

        assert isinstance(result, Success)
        assert result.value["relationships"] == ()

    def test_validate_missing_relationships_section(
        self, validation_service: SchemaImportValidationService
    ) -> None:
        """Should accept data without relationships section (backward compatibility)."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "TEXT",
                            "label_key": "field.name",
                            "required": False,
                            "constraints": [],
                        }
                    ],
                },
            ],
            # No relationships key
        }

        result = validation_service.validate_json_data(data)

        assert isinstance(result, Success)
        # Should default to empty relationships
        assert result.value.get("relationships", ()) == ()
