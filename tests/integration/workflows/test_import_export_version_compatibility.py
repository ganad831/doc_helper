"""Integration tests for import/export version compatibility.

ADR-039: Import/Export Data Format
Tests for backward compatibility and version handling.
"""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_ids import EntityDefinitionId
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.infrastructure.interchange.json_project_exporter import JsonProjectExporter
from doc_helper.infrastructure.interchange.json_project_importer import JsonProjectImporter


class TestVersionCompatibility:
    """Tests for import/export version compatibility."""

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
        """Create sample project."""
        return Project(
            id=ProjectId(uuid4()),
            name="Version Test Project",
            app_type_id="soil_investigation",
            entity_definition_id=EntityDefinitionId("test_entity"),
            field_values={},
        )

    def test_exporter_uses_format_version_1_0(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        tmp_path: Path,
    ) -> None:
        """Exporter should produce format version 1.0."""
        # Arrange
        export_path = tmp_path / "export.json"
        entity_definitions = ()

        # Act: Export
        result = exporter.export_to_file(
            project=project,
            entity_definitions=entity_definitions,
            output_path=export_path,
        )

        # Assert: Export succeeded with version 1.0
        assert isinstance(result, Success)
        assert result.value["format_version"] == "1.0"

        # Assert: JSON file contains version 1.0
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["format_version"] == "1.0"

    def test_importer_accepts_format_version_1_0(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Importer should accept format version 1.0."""
        # Arrange: Create valid 1.0 format file
        import_path = tmp_path / "import_v1.json"
        data = {
            "format_version": "1.0",
            "metadata": {
                "project_id": str(uuid4()),
                "project_name": "Test Project",
                "entity_definition_id": "test_entity",
                "created_at": "2026-01-21T00:00:00Z",
                "modified_at": "2026-01-21T00:00:00Z",
                "app_version": "1.0.0",
                "exported_at": "2026-01-21T00:00:00Z",
                "exported_by": "Doc Helper 1.0.0",
            },
            "schema": {"entities": [], "fields": []},
            "data": {},
        }
        import_path.write_text(json.dumps(data))

        entity_definitions = ()

        # Act: Import
        result = importer.import_from_file(
            input_path=import_path,
            entity_definitions=entity_definitions,
        )

        # Assert: Import succeeded
        assert isinstance(result, Success)
        assert result.value["format_version"] == "1.0"

    def test_importer_rejects_unsupported_version(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Importer should reject unsupported format versions."""
        # Arrange: Create file with unsupported version
        import_path = tmp_path / "import_v99.json"
        data = {
            "format_version": "99.0",
            "metadata": {
                "project_id": str(uuid4()),
                "project_name": "Test Project",
            },
            "schema": {"entities": [], "fields": []},
            "data": {},
        }
        import_path.write_text(json.dumps(data))

        entity_definitions = ()

        # Act: Import
        result = importer.import_from_file(
            input_path=import_path,
            entity_definitions=entity_definitions,
        )

        # Assert: Import failed
        assert isinstance(result, Failure)
        assert "unsupported format version" in result.error.lower()
        assert "99.0" in result.error

    def test_importer_lists_supported_versions_in_error(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Importer should list supported versions when rejecting unsupported version."""
        # Arrange
        import_path = tmp_path / "import_unsupported.json"
        data = {
            "format_version": "2.0",
            "metadata": {"project_id": str(uuid4()), "project_name": "Test"},
            "schema": {"entities": [], "fields": []},
            "data": {},
        }
        import_path.write_text(json.dumps(data))

        entity_definitions = ()

        # Act
        result = importer.import_from_file(input_path=import_path, entity_definitions=entity_definitions)

        # Assert: Error message includes supported versions
        assert isinstance(result, Failure)
        assert "supported versions" in result.error.lower()
        assert "1.0" in result.error

    def test_export_includes_app_version(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        tmp_path: Path,
    ) -> None:
        """Export should include app_version in metadata (for compatibility tracking)."""
        # Arrange
        export_path = tmp_path / "export.json"
        entity_definitions = ()

        # Act: Export
        result = exporter.export_to_file(
            project=project,
            entity_definitions=entity_definitions,
            output_path=export_path,
        )

        # Assert: Export succeeded
        assert isinstance(result, Success)

        # Assert: app_version in metadata
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "app_version" in data["metadata"]
        assert data["metadata"]["app_version"]  # Not empty

    def test_import_preserves_source_app_version(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Import should preserve source_app_version from export."""
        # Arrange: File exported by older version
        import_path = tmp_path / "import_old_version.json"
        data = {
            "format_version": "1.0",
            "metadata": {
                "project_id": str(uuid4()),
                "project_name": "Old Version Project",
                "entity_definition_id": "test_entity",
                "created_at": "2025-01-01T00:00:00Z",
                "modified_at": "2025-01-01T00:00:00Z",
                "app_version": "0.9.0",  # Older version
                "exported_at": "2025-01-01T00:00:00Z",
                "exported_by": "Doc Helper 0.9.0",
            },
            "schema": {"entities": [], "fields": []},
            "data": {},
        }
        import_path.write_text(json.dumps(data))

        entity_definitions = ()

        # Act: Import
        result = importer.import_from_file(
            input_path=import_path,
            entity_definitions=entity_definitions,
        )

        # Assert: Import succeeded and preserved version
        assert isinstance(result, Success)
        assert result.value["source_app_version"] == "0.9.0"

    def test_import_generates_warnings_for_missing_fields(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Import should generate warnings when imported data has fields not in current schema."""
        # Arrange: Create schema with one entity
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId

        field1 = FieldDefinition(
            id=FieldDefinitionId("field1"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.field1"),
            required=False,
        )
        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test_entity"),
            description_key=TranslationKey("entity.test_entity.description"),
            fields={FieldDefinitionId("field1"): field1},
            is_root_entity=True,
            parent_entity_id=None,
        )
        schema = (entity,)

        # Create import file with extra field not in current schema
        import_path = tmp_path / "import_extra_field.json"
        data = {
            "format_version": "1.0",
            "metadata": {
                "project_id": str(uuid4()),
                "project_name": "Project with Extra Field",
            },
            "schema": {
                "entities": [
                    {
                        "id": "test_entity",
                        "name": "Test Entity",
                        "description": "",
                        "entity_type": "SINGLETON",
                    }
                ],
                "fields": [
                    {
                        "id": "field1",
                        "entity_id": "test_entity",
                        "label": "Field 1",
                        "field_type": "TEXT",
                        "required": False,
                    },
                    {
                        "id": "field2_old",  # Field that doesn't exist in current schema
                        "entity_id": "test_entity",
                        "label": "Old Field 2",
                        "field_type": "TEXT",
                        "required": False,
                    },
                ],
            },
            "data": {},
        }
        import_path.write_text(json.dumps(data))

        # Act: Import
        result = importer.import_from_file(
            input_path=import_path,
            entity_definitions=schema,
        )

        # Assert: Import succeeded with warnings
        assert isinstance(result, Success)
        warnings = result.value.get("warnings", [])
        assert len(warnings) > 0
        assert any("field2_old" in w.lower() for w in warnings)

    def test_backward_compatibility_guarantee(
        self,
        exporter: JsonProjectExporter,
        importer: JsonProjectImporter,
        project: Project,
        tmp_path: Path,
    ) -> None:
        """Newer importer should successfully import exports from version 1.0 (backward compatibility)."""
        # This test documents the ADR-039 backward compatibility guarantee:
        # Newer application versions MUST be able to import exports from older versions.

        # Arrange: Export with current version
        export_path = tmp_path / "v1_export.json"
        entity_definitions = ()
        export_result = exporter.export_to_file(
            project=project,
            entity_definitions=entity_definitions,
            output_path=export_path,
        )
        assert isinstance(export_result, Success)

        # Act: Import (simulating future version that still supports 1.0)
        import_result = importer.import_from_file(
            input_path=export_path,
            entity_definitions=entity_definitions,
        )

        # Assert: Import succeeds (backward compatibility maintained)
        assert isinstance(import_result, Success)
        assert import_result.value["format_version"] == "1.0"

    def test_import_handles_missing_optional_metadata_gracefully(
        self,
        importer: JsonProjectImporter,
        tmp_path: Path,
    ) -> None:
        """Import should handle missing optional metadata fields gracefully."""
        # Arrange: Minimal valid file (only required fields)
        import_path = tmp_path / "import_minimal.json"
        data = {
            "format_version": "1.0",
            "metadata": {
                "project_id": str(uuid4()),
                "project_name": "Minimal Project",
                "entity_definition_id": "test_entity",
                # Optional fields omitted: created_at, modified_at, app_version, etc.
            },
            "schema": {"entities": [], "fields": []},
            "data": {},
        }
        import_path.write_text(json.dumps(data))

        entity_definitions = ()

        # Act: Import
        result = importer.import_from_file(
            input_path=import_path,
            entity_definitions=entity_definitions,
        )

        # Assert: Import succeeded despite missing optional fields
        assert isinstance(result, Success)
        assert result.value["project_name"] == "Minimal Project"

    def test_format_version_is_independent_of_app_version(
        self,
        exporter: JsonProjectExporter,
        project: Project,
        tmp_path: Path,
    ) -> None:
        """Format version should be independent of application version (ADR-039)."""
        # The interchange format version (e.g., "1.0") is independent of the
        # application version (e.g., "1.5.2"). The format only changes when the
        # structure changes incompatibly.

        # Arrange
        export_path = tmp_path / "export.json"
        entity_definitions = ()

        # Act: Export
        exporter.export_to_file(project=project, entity_definitions=entity_definitions, output_path=export_path)

        # Assert: format_version and app_version are different fields
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        format_version = data["format_version"]
        app_version = data["metadata"]["app_version"]

        assert format_version == "1.0"  # Format version
        assert app_version != format_version  # App version is different
