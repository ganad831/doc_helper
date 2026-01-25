"""Integration tests for ExportSchemaCommand (Phase 2 Step 4).

Tests cover:
- File system operations (creates files, handles errors)
- Content validation (exported JSON can be parsed and matches source)
- Consistent snapshot behavior
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from doc_helper.application.commands.schema.export_schema_command import ExportSchemaCommand
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import (
    MinLengthConstraint,
    MaxLengthConstraint,
    RequiredConstraint,
    PatternConstraint,
)
from doc_helper.infrastructure.interchange import JsonSchemaExportWriter


class TestExportSchemaIntegration:
    """Integration tests for schema export file system operations."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def schema_export_writer(self) -> JsonSchemaExportWriter:
        """Create schema export writer (Phase H-4)."""
        return JsonSchemaExportWriter()

    @pytest.fixture
    def command(self, mock_repository: Mock, schema_export_writer: JsonSchemaExportWriter) -> ExportSchemaCommand:
        """Create command with mock repository and schema export writer."""
        return ExportSchemaCommand(mock_repository, schema_export_writer)

    @pytest.fixture
    def complete_schema(self) -> tuple[EntityDefinition, ...]:
        """Create a complete schema with multiple entities and fields."""
        # Field definitions for project entity
        project_name_field = FieldDefinition(
            id=FieldDefinitionId("project_name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.project_name"),
            help_text_key=TranslationKey("field.project_name.help"),
            required=True,
            constraints=(
                RequiredConstraint(),
                MinLengthConstraint(min_length=3),
                MaxLengthConstraint(max_length=100),
            ),
        )

        project_date_field = FieldDefinition(
            id=FieldDefinitionId("project_date"),
            field_type=FieldType.DATE,
            label_key=TranslationKey("field.project_date"),
            help_text_key=TranslationKey("field.project_date.help"),
            required=True,
        )

        status_field = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            help_text_key=TranslationKey("field.status.help"),
            required=True,
            options=(
                ("active", TranslationKey("status.active")),
                ("completed", TranslationKey("status.completed")),
                ("archived", TranslationKey("status.archived")),
            ),
        )

        project_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            description_key=TranslationKey("entity.project.description"),
            is_root_entity=True,
            fields={
                project_name_field.id: project_name_field,
                project_date_field.id: project_date_field,
                status_field.id: status_field,
            },
        )

        # Field definitions for sample entity
        sample_id_field = FieldDefinition(
            id=FieldDefinitionId("sample_id"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.sample_id"),
            help_text_key=TranslationKey("field.sample_id.help"),
            required=True,
            constraints=(
                PatternConstraint(pattern=r"^S-\d{4}$", description="Sample ID format"),
            ),
        )

        depth_field = FieldDefinition(
            id=FieldDefinitionId("depth"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.depth"),
            help_text_key=TranslationKey("field.depth.help"),
            required=True,
            default_value="0.0",
        )

        sample_entity = EntityDefinition(
            id=EntityDefinitionId("sample"),
            name_key=TranslationKey("entity.sample"),
            description_key=TranslationKey("entity.sample.description"),
            is_root_entity=False,
            fields={
                sample_id_field.id: sample_id_field,
                depth_field.id: depth_field,
            },
        )

        return (project_entity, sample_entity)

    # =========================================================================
    # File System Tests
    # =========================================================================

    def test_export_creates_file_at_specified_path(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        complete_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Should create export file at the exact path specified."""
        # Setup
        mock_repository.get_all.return_value = Success(complete_schema)
        export_path = tmp_path / "my_export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        assert export_path.exists()
        assert export_path.is_file()

    def test_export_creates_nested_directories(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        complete_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Should create parent directories if they don't exist."""
        # Setup
        mock_repository.get_all.return_value = Success(complete_schema)
        export_path = tmp_path / "level1" / "level2" / "level3" / "export.json"

        # Assert directories don't exist yet
        assert not export_path.parent.exists()

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        assert export_path.exists()
        assert (tmp_path / "level1" / "level2" / "level3").is_dir()

    def test_export_file_has_correct_encoding(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should write file with UTF-8 encoding for Unicode support."""
        # Setup - entity with Unicode characters in translation keys
        field = FieldDefinition(
            id=FieldDefinitionId("unicode_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.unicode_тест_اختبار"),
            help_text_key=TranslationKey("field.unicode.help"),
        )
        entity = EntityDefinition(
            id=EntityDefinitionId("unicode_entity"),
            name_key=TranslationKey("entity.unicode_مشروع_проект"),
            is_root_entity=True,
            fields={field.id: field},
        )
        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "unicode_export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()

        # Read with UTF-8 and verify Unicode preserved
        content = export_path.read_text(encoding='utf-8')
        assert "unicode_тест_اختبار" in content
        assert "unicode_مشروع_проект" in content

    @pytest.mark.skipif(
        os.name == 'nt',
        reason="chmod directory permissions don't work reliably on Windows"
    )
    def test_export_handles_permission_error_gracefully(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        complete_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Should fail gracefully when write permission denied."""
        # Setup
        mock_repository.get_all.return_value = Success(complete_schema)

        # Create a read-only directory (platform-specific)
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()

        export_path = readonly_dir / "export.json"

        # Make directory read-only
        try:
            os.chmod(readonly_dir, 0o444)

            # Execute
            result = command.execute(schema_id="test_schema", file_path=export_path)

            # Assert - should fail with file write error
            assert result.is_failure()
            assert "failed to write" in result.error.lower()

        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    # =========================================================================
    # Content Validation Tests
    # =========================================================================

    def test_exported_json_is_valid_and_parseable(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        complete_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Should create valid JSON that can be parsed."""
        # Setup
        mock_repository.get_all.return_value = Success(complete_schema)
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()

        # Parse JSON
        content = export_path.read_text(encoding='utf-8')
        parsed = json.loads(content)

        # Basic structure checks
        assert "schema_id" in parsed
        assert "entities" in parsed
        assert isinstance(parsed["entities"], list)

    def test_exported_content_matches_source_schema(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        complete_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Should export content that exactly matches source schema."""
        # Setup
        mock_repository.get_all.return_value = Success(complete_schema)
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="my_schema", file_path=export_path)

        # Assert
        assert result.is_success()

        # Parse and validate content
        content = export_path.read_text(encoding='utf-8')
        parsed = json.loads(content)

        # Verify schema_id
        assert parsed["schema_id"] == "my_schema"

        # Verify entity count
        assert len(parsed["entities"]) == 2

        # Find project entity
        project_data = next(e for e in parsed["entities"] if e["id"] == "project")
        assert project_data["name_key"] == "entity.project"
        assert project_data["description_key"] == "entity.project.description"
        assert project_data["is_root_entity"] is True
        assert len(project_data["fields"]) == 3

        # Verify project name field
        name_field = next(f for f in project_data["fields"] if f["id"] == "project_name")
        assert name_field["field_type"] == "text"  # FieldType enum values are lowercase
        assert name_field["label_key"] == "field.project_name"
        assert name_field["required"] is True
        assert len(name_field["constraints"]) == 3

        # Verify constraints
        constraint_types = {c["constraint_type"] for c in name_field["constraints"]}
        assert "RequiredConstraint" in constraint_types
        assert "MinLengthConstraint" in constraint_types
        assert "MaxLengthConstraint" in constraint_types

        # Verify min length parameter
        min_constraint = next(
            c for c in name_field["constraints"]
            if c["constraint_type"] == "MinLengthConstraint"
        )
        assert min_constraint["parameters"]["min_length"] == 3

        # Verify dropdown options
        status_field = next(f for f in project_data["fields"] if f["id"] == "status")
        assert len(status_field["options"]) == 3
        option_values = {o["value"] for o in status_field["options"]}
        assert option_values == {"active", "completed", "archived"}

        # Find sample entity
        sample_data = next(e for e in parsed["entities"] if e["id"] == "sample")
        assert sample_data["is_root_entity"] is False
        assert len(sample_data["fields"]) == 2

        # Verify pattern constraint
        sample_id_field = next(f for f in sample_data["fields"] if f["id"] == "sample_id")
        pattern_constraint = next(
            c for c in sample_id_field["constraints"]
            if c["constraint_type"] == "PatternConstraint"
        )
        assert pattern_constraint["parameters"]["pattern"] == r"^S-\d{4}$"
        assert pattern_constraint["parameters"]["description"] == "Sample ID format"

        # Verify default value
        depth_field = next(f for f in sample_data["fields"] if f["id"] == "depth")
        assert depth_field["default_value"] == "0.0"

    def test_export_round_trip_structure_validation(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        complete_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Should export data that preserves structural integrity."""
        # Setup
        mock_repository.get_all.return_value = Success(complete_schema)
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()

        # Parse exported content
        content = export_path.read_text(encoding='utf-8')
        parsed = json.loads(content)

        # Verify all expected fields are present in export
        for entity_data in parsed["entities"]:
            # Entity must have required fields
            assert "id" in entity_data
            assert "name_key" in entity_data
            assert "is_root_entity" in entity_data
            assert "fields" in entity_data

            for field_data in entity_data["fields"]:
                # Field must have required fields
                assert "id" in field_data
                assert "field_type" in field_data
                assert "label_key" in field_data
                assert "required" in field_data
                assert "options" in field_data
                assert "constraints" in field_data

                for constraint_data in field_data["constraints"]:
                    # Constraint must have required fields
                    assert "constraint_type" in constraint_data
                    assert "parameters" in constraint_data

    # =========================================================================
    # Consistency Tests
    # =========================================================================

    def test_multiple_exports_produce_same_content(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        complete_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Should produce identical content for same schema state (idempotent)."""
        # Setup
        mock_repository.get_all.return_value = Success(complete_schema)
        export_path1 = tmp_path / "export1.json"
        export_path2 = tmp_path / "export2.json"

        # Execute twice
        result1 = command.execute(schema_id="test_schema", file_path=export_path1)
        result2 = command.execute(schema_id="test_schema", file_path=export_path2)

        # Assert both succeed
        assert result1.is_success()
        assert result2.is_success()

        # Compare content (should be identical)
        content1 = export_path1.read_text(encoding='utf-8')
        content2 = export_path2.read_text(encoding='utf-8')
        assert content1 == content2

    def test_export_data_matches_result_object(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        complete_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Should return ExportResult.export_data that matches file content."""
        # Setup
        mock_repository.get_all.return_value = Success(complete_schema)
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()

        # Parse file content
        content = export_path.read_text(encoding='utf-8')
        file_data = json.loads(content)

        # Compare with ExportResult.export_data
        export_data = result.value.export_data
        assert export_data.schema_id == file_data["schema_id"]
        assert len(export_data.entities) == len(file_data["entities"])

        # Verify entity IDs match
        result_entity_ids = {e.id for e in export_data.entities}
        file_entity_ids = {e["id"] for e in file_data["entities"]}
        assert result_entity_ids == file_entity_ids
