"""Integration tests for export/import round-trip workflow.

ADR-039: Import/Export Data Format
Tests that exporting a project and then importing it produces equivalent data.
"""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.common.result import Success
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.infrastructure.interchange.json_project_exporter import JsonProjectExporter
from doc_helper.infrastructure.interchange.json_project_importer import JsonProjectImporter


class TestExportImportRoundTrip:
    """Integration tests for export→import round-trip."""

    @pytest.fixture
    def exporter(self) -> JsonProjectExporter:
        """Create JSON project exporter."""
        return JsonProjectExporter()

    @pytest.fixture
    def importer(self) -> JsonProjectImporter:
        """Create JSON project importer."""
        return JsonProjectImporter()

    @pytest.fixture
    def project(self) -> Project:
        """Create sample project with data."""
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Round-Trip Project",
            entity_definition_id=EntityDefinitionId("test_entity"),
            field_values={},
        )
        return project

    @pytest.fixture
    def export_path(self, tmp_path: Path) -> Path:
        """Create temporary export file path."""
        return tmp_path / "round_trip_export.json"

    def test_export_then_import_produces_valid_json(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Export should produce valid JSON that can be parsed."""
        # Arrange: Create minimal schema
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Export project
        result = exporter.export_to_file(
            project=project,
            entity_definitions=schema,
            output_path=export_path,
        )

        # Assert: Export succeeded
        assert isinstance(result, Success)

        # Assert: File exists and contains valid JSON
        assert export_path.exists()
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)  # Should not raise JSONDecodeError

        # Assert: Required sections present
        assert "format_version" in data
        assert "metadata" in data
        assert "schema" in data
        assert "data" in data

    def test_export_then_import_preserves_project_metadata(
        self,
        exporter: JsonProjectExporter,
        importer: JsonProjectImporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Import should preserve project name and other metadata from export."""
        # Arrange: Create schema
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Export project
        export_result = exporter.export_to_file(
            project=project,
            entity_definitions=schema,
            output_path=export_path,
        )
        assert isinstance(export_result, Success)

        # Act: Import project
        import_result = importer.import_from_file(
            input_path=export_path,
            entity_definitions=schema,
        )

        # Assert: Import succeeded
        assert isinstance(import_result, Success)
        import_data = import_result.value

        # Assert: Project name preserved
        assert import_data["project_name"] == project.name

        # Assert: Format version preserved
        assert import_data["format_version"] == "1.0"

    def test_export_includes_format_version(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Export should include format_version field."""
        # Arrange
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Export
        result = exporter.export_to_file(
            project=project,
            entity_definitions=schema,
            output_path=export_path,
        )

        # Assert: Success and format_version in result
        assert isinstance(result, Success)
        assert result.value["format_version"] == "1.0"

        # Assert: format_version in JSON file
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["format_version"] == "1.0"

    def test_export_includes_metadata_section(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Export should include complete metadata section."""
        # Arrange
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Export
        result = exporter.export_to_file(
            project=project,
            entity_definitions=schema,
            output_path=export_path,
        )

        # Assert: Export succeeded
        assert isinstance(result, Success)

        # Assert: Metadata section in JSON
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = data["metadata"]
        assert "project_id" in metadata
        assert "project_name" in metadata
        assert metadata["project_name"] == "Test Round-Trip Project"
        assert "created_at" in metadata
        assert "modified_at" in metadata
        assert "app_version" in metadata
        assert "exported_at" in metadata
        assert "exported_by" in metadata

    def test_export_includes_schema_section(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Export should include schema section with entities and fields."""
        # Arrange
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Export
        result = exporter.export_to_file(
            project=project,
            entity_definitions=schema,
            output_path=export_path,
        )

        # Assert: Export succeeded
        assert isinstance(result, Success)

        # Assert: Schema section in JSON
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        schema_section = data["schema"]
        assert "entities" in schema_section
        assert "fields" in schema_section
        assert isinstance(schema_section["entities"], list)
        assert isinstance(schema_section["fields"], list)

    def test_export_includes_data_section(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Export should include data section organized by entity."""
        # Arrange
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Export
        result = exporter.export_to_file(
            project=project,
            entity_definitions=schema,
            output_path=export_path,
        )

        # Assert: Export succeeded
        assert isinstance(result, Success)

        # Assert: Data section in JSON
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data_section = data["data"]
        assert isinstance(data_section, dict)

    def test_import_validates_format_structure(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Import should validate that required sections are present."""
        # Arrange: Create invalid JSON (missing sections)
        invalid_path = tmp_path / "invalid.json"
        invalid_path.write_text('{"format_version": "1.0"}')  # Missing other sections

        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Import invalid file
        result = importer.import_from_file(
            input_path=invalid_path,
            entity_definitions=schema,
        )

        # Assert: Import failed with validation error
        from doc_helper.domain.common.result import Failure
        assert isinstance(result, Failure)
        assert "missing required sections" in result.error.lower()

    def test_import_validates_format_version(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Import should validate format version is supported."""
        # Arrange: Create JSON with unsupported version
        invalid_version_path = tmp_path / "unsupported_version.json"
        invalid_data = {
            "format_version": "99.0",
            "metadata": {"project_id": "test", "project_name": "Test"},
            "schema": {"entities": [], "fields": []},
            "data": {},
        }
        invalid_version_path.write_text(json.dumps(invalid_data))

        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Import file with unsupported version
        result = importer.import_from_file(
            input_path=invalid_version_path,
            entity_definitions=schema,
        )

        # Assert: Import failed
        from doc_helper.domain.common.result import Failure
        assert isinstance(result, Failure)
        assert "unsupported format version" in result.error.lower()

    def test_import_handles_malformed_json(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Import should handle malformed JSON gracefully."""
        # Arrange: Create malformed JSON file
        malformed_path = tmp_path / "malformed.json"
        malformed_path.write_text('{"invalid": json}')  # Invalid JSON

        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Import malformed file
        result = importer.import_from_file(
            input_path=malformed_path,
            entity_definitions=schema,
        )

        # Assert: Import failed with parse error
        from doc_helper.domain.common.result import Failure
        assert isinstance(result, Failure)
        assert "invalid json" in result.error.lower()

    def test_import_creates_new_project_id(
        self,
        exporter: JsonProjectExporter,
        importer: JsonProjectImporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Import should create new project with different ID (ADR-039: never reuse IDs)."""
        # Arrange
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()
        original_project_id = str(project.id.value)

        # Act: Export then import
        exporter.export_to_file(project=project, entity_definitions=schema, output_path=export_path)
        import_result = importer.import_from_file(input_path=export_path, entity_definitions=schema)

        # Assert: Import succeeded
        assert isinstance(import_result, Success)
        import_data = import_result.value

        # Assert: New project created
        imported_project = import_data["project"]
        assert imported_project is not None

        # Assert: New project has different ID (ADR-039)
        imported_project_id = str(imported_project.id.value)
        assert imported_project_id != original_project_id

    def test_export_json_is_human_readable(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Export should produce formatted JSON (human-readable)."""
        # Arrange
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Export
        result = exporter.export_to_file(
            project=project,
            entity_definitions=schema,
            output_path=export_path,
        )

        # Assert: Export succeeded
        assert isinstance(result, Success)

        # Assert: JSON is formatted with indentation
        json_content = export_path.read_text(encoding="utf-8")
        assert "\n" in json_content  # Has newlines (formatted)
        assert "  " in json_content  # Has indentation

    def test_export_json_uses_utf8_encoding(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        export_path: Path,
    ) -> None:
        """Export should use UTF-8 encoding (ADR-039: international support)."""
        # Arrange: Project with non-ASCII name
        project_with_unicode = Project(
            id=ProjectId(uuid4()),
            name="مشروع اختبار",  # Arabic text
            entity_definition_id=EntityDefinitionId("test_entity"),
            field_values={},
        )

        from doc_helper.domain.schema.entity_definition import EntityDefinition
        schema = ()

        # Act: Export
        result = exporter.export_to_file(
            project=project_with_unicode,
            entity_definitions=schema,
            output_path=export_path,
        )

        # Assert: Export succeeded
        assert isinstance(result, Success)

        # Assert: File readable as UTF-8 and preserves Arabic text
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["metadata"]["project_name"] == "مشروع اختبار"
