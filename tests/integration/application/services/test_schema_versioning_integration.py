"""Integration tests for Schema Versioning and Comparison (Phase 3).

Tests cover:
- Export with version field
- Schema comparison with realistic entity structures
- Version bump suggestions based on detected changes
- End-to-end comparison workflows

APPROVED DECISIONS (Phase 3):
- Decision 1: Semantic versioning (MAJOR.MINOR.PATCH)
- Decision 2: No rename detection (rename = delete + add)
- Decision 3: Moderate breaking-change policy
- Decision 5: Version field is optional in export
- Decision 6: Three-level compatibility (IDENTICAL / COMPATIBLE / INCOMPATIBLE)
- Decision 7: Structural comparison only

IMPORTANT: Compatibility is informational only and MUST NOT block operations.
"""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from doc_helper.application.commands.schema.export_schema_command import ExportSchemaCommand
from doc_helper.application.services.schema_comparison_service import SchemaComparisonService
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_change import ChangeType
from doc_helper.domain.schema.schema_compatibility import CompatibilityLevel
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_version import SchemaVersion
from doc_helper.domain.validation.constraints import (
    MinLengthConstraint,
    MaxLengthConstraint,
    RequiredConstraint,
    MinValueConstraint,
    MaxValueConstraint,
)
from doc_helper.infrastructure.interchange import JsonSchemaExportWriter


class TestExportWithVersion:
    """Integration tests for export with version field."""

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
    def sample_entity(self) -> EntityDefinition:
        """Create a sample entity for testing."""
        field = FieldDefinition(
            id=FieldDefinitionId("test_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.test"),
            help_text_key=TranslationKey("field.test.help"),
            required=True,
        )
        return EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            is_root_entity=True,
            fields={field.id: field},
        )

    def test_export_with_version_includes_version_in_file(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        sample_entity: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should include version field in exported JSON when provided."""
        # Setup
        mock_repository.get_all.return_value = Success((sample_entity,))
        export_path = tmp_path / "versioned_export.json"

        # Execute with version
        result = command.execute(
            schema_id="test_schema",
            file_path=export_path,
            version="1.2.3",
        )

        # Assert
        assert result.is_success()
        assert export_path.exists()

        # Parse and verify version
        content = export_path.read_text(encoding='utf-8')
        parsed = json.loads(content)
        assert parsed["version"] == "1.2.3"

    def test_export_without_version_omits_version_field(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        sample_entity: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should not include version field in exported JSON when not provided."""
        # Setup
        mock_repository.get_all.return_value = Success((sample_entity,))
        export_path = tmp_path / "unversioned_export.json"

        # Execute without version
        result = command.execute(
            schema_id="test_schema",
            file_path=export_path,
        )

        # Assert
        assert result.is_success()

        # Parse and verify no version
        content = export_path.read_text(encoding='utf-8')
        parsed = json.loads(content)
        assert "version" not in parsed

    def test_export_result_dto_contains_version(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        sample_entity: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should include version in ExportResult.export_data when provided."""
        # Setup
        mock_repository.get_all.return_value = Success((sample_entity,))
        export_path = tmp_path / "export.json"

        # Execute with version
        result = command.execute(
            schema_id="test_schema",
            file_path=export_path,
            version="2.0.0",
        )

        # Assert
        assert result.is_success()
        assert result.value.export_data.version == "2.0.0"


class TestSchemaComparisonIntegration:
    """Integration tests for schema comparison service with realistic schemas."""

    @pytest.fixture
    def comparison_service(self) -> SchemaComparisonService:
        """Create schema comparison service."""
        return SchemaComparisonService()

    @pytest.fixture
    def base_schema_v1(self) -> tuple[EntityDefinition, ...]:
        """Create v1.0.0 base schema with project and sample entities."""
        # Project entity
        project_name = FieldDefinition(
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

        project_date = FieldDefinition(
            id=FieldDefinitionId("project_date"),
            field_type=FieldType.DATE,
            label_key=TranslationKey("field.project_date"),
            help_text_key=TranslationKey("field.project_date.help"),
            required=True,
        )

        status = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            help_text_key=TranslationKey("field.status.help"),
            required=True,
            options=(
                ("draft", TranslationKey("status.draft")),
                ("active", TranslationKey("status.active")),
                ("completed", TranslationKey("status.completed")),
            ),
        )

        project_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            description_key=TranslationKey("entity.project.description"),
            is_root_entity=True,
            fields={
                project_name.id: project_name,
                project_date.id: project_date,
                status.id: status,
            },
        )

        # Sample entity
        sample_id = FieldDefinition(
            id=FieldDefinitionId("sample_id"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.sample_id"),
            help_text_key=TranslationKey("field.sample_id.help"),
            required=True,
        )

        depth = FieldDefinition(
            id=FieldDefinitionId("depth"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.depth"),
            help_text_key=TranslationKey("field.depth.help"),
            required=True,
            constraints=(
                MinValueConstraint(min_value=0),
                MaxValueConstraint(max_value=100),
            ),
        )

        sample_entity = EntityDefinition(
            id=EntityDefinitionId("sample"),
            name_key=TranslationKey("entity.sample"),
            is_root_entity=False,
            fields={
                sample_id.id: sample_id,
                depth.id: depth,
            },
        )

        return (project_entity, sample_entity)

    # =========================================================================
    # Identical Schema Tests
    # =========================================================================

    def test_identical_schemas_produce_identical_level(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Comparing schema with itself should produce IDENTICAL level."""
        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=base_schema_v1,
            source_version=SchemaVersion(1, 0, 0),
            target_version=SchemaVersion(1, 0, 0),
        )

        assert result.level == CompatibilityLevel.IDENTICAL
        assert len(result.changes) == 0
        assert result.is_identical

    # =========================================================================
    # Compatible Schema Changes (Non-Breaking)
    # =========================================================================

    def test_adding_entity_is_compatible(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Adding a new entity should be COMPATIBLE (non-breaking)."""
        # Create v1.1.0 with new entity
        new_entity = EntityDefinition(
            id=EntityDefinitionId("laboratory"),
            name_key=TranslationKey("entity.laboratory"),
            is_root_entity=False,
            fields={},
        )
        v1_1_schema = base_schema_v1 + (new_entity,)

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v1_1_schema,
            source_version=SchemaVersion(1, 0, 0),
            target_version=SchemaVersion(1, 1, 0),
        )

        assert result.level == CompatibilityLevel.COMPATIBLE
        assert not result.is_incompatible
        assert any(c.change_type == ChangeType.ENTITY_ADDED for c in result.changes)

    def test_adding_field_is_compatible(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Adding a new field to an entity should be COMPATIBLE (non-breaking)."""
        # Create modified project entity with new field
        new_field = FieldDefinition(
            id=FieldDefinitionId("client_name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.client_name"),
            help_text_key=TranslationKey("field.client_name.help"),
            required=False,
        )

        original_project = base_schema_v1[0]
        modified_fields = dict(original_project.fields)
        modified_fields[new_field.id] = new_field

        modified_project = EntityDefinition(
            id=original_project.id,
            name_key=original_project.name_key,
            description_key=original_project.description_key,
            is_root_entity=original_project.is_root_entity,
            fields=modified_fields,
        )

        v1_1_schema = (modified_project, base_schema_v1[1])

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v1_1_schema,
        )

        assert result.level == CompatibilityLevel.COMPATIBLE
        assert any(
            c.change_type == ChangeType.FIELD_ADDED and c.field_id == "client_name"
            for c in result.changes
        )

    def test_adding_option_is_compatible(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Adding a new dropdown option should be COMPATIBLE (non-breaking)."""
        # Create modified status field with new option
        original_project = base_schema_v1[0]
        original_status = original_project.get_field(FieldDefinitionId("status"))

        new_options = original_status.options + (
            ("archived", TranslationKey("status.archived")),
        )

        modified_status = FieldDefinition(
            id=original_status.id,
            field_type=original_status.field_type,
            label_key=original_status.label_key,
            help_text_key=original_status.help_text_key,
            required=original_status.required,
            options=new_options,
        )

        modified_fields = dict(original_project.fields)
        modified_fields[modified_status.id] = modified_status

        modified_project = EntityDefinition(
            id=original_project.id,
            name_key=original_project.name_key,
            description_key=original_project.description_key,
            is_root_entity=original_project.is_root_entity,
            fields=modified_fields,
        )

        v1_1_schema = (modified_project, base_schema_v1[1])

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v1_1_schema,
        )

        assert result.level == CompatibilityLevel.COMPATIBLE
        assert any(
            c.change_type == ChangeType.OPTION_ADDED and c.option_value == "archived"
            for c in result.changes
        )

    # =========================================================================
    # Incompatible Schema Changes (Breaking)
    # =========================================================================

    def test_removing_entity_is_incompatible(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Removing an entity should be INCOMPATIBLE (breaking)."""
        # Remove sample entity
        v2_schema = (base_schema_v1[0],)  # Only project entity

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v2_schema,
        )

        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert result.is_incompatible
        assert any(
            c.change_type == ChangeType.ENTITY_REMOVED and c.entity_id == "sample"
            for c in result.changes
        )

    def test_removing_field_is_incompatible(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Removing a field from an entity should be INCOMPATIBLE (breaking)."""
        # Remove project_date field
        original_project = base_schema_v1[0]
        modified_fields = {
            k: v for k, v in original_project.fields.items()
            if k.value != "project_date"
        }

        modified_project = EntityDefinition(
            id=original_project.id,
            name_key=original_project.name_key,
            description_key=original_project.description_key,
            is_root_entity=original_project.is_root_entity,
            fields=modified_fields,
        )

        v2_schema = (modified_project, base_schema_v1[1])

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v2_schema,
        )

        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert any(
            c.change_type == ChangeType.FIELD_REMOVED and c.field_id == "project_date"
            for c in result.changes
        )

    def test_changing_field_type_is_incompatible(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Changing a field's type should be INCOMPATIBLE (breaking)."""
        # Change depth from NUMBER to TEXT
        original_sample = base_schema_v1[1]
        original_depth = original_sample.get_field(FieldDefinitionId("depth"))

        modified_depth = FieldDefinition(
            id=original_depth.id,
            field_type=FieldType.TEXT,  # Changed from NUMBER
            label_key=original_depth.label_key,
            help_text_key=original_depth.help_text_key,
            required=original_depth.required,
        )

        modified_fields = dict(original_sample.fields)
        modified_fields[modified_depth.id] = modified_depth

        modified_sample = EntityDefinition(
            id=original_sample.id,
            name_key=original_sample.name_key,
            is_root_entity=original_sample.is_root_entity,
            fields=modified_fields,
        )

        v2_schema = (base_schema_v1[0], modified_sample)

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v2_schema,
        )

        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert any(
            c.change_type == ChangeType.FIELD_TYPE_CHANGED
            and c.field_id == "depth"
            and c.old_value == "number"
            and c.new_value == "text"
            for c in result.changes
        )

    def test_removing_option_is_incompatible(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Removing a dropdown option should be INCOMPATIBLE (breaking)."""
        # Remove "draft" option from status field
        original_project = base_schema_v1[0]
        original_status = original_project.get_field(FieldDefinitionId("status"))

        # Keep only active and completed
        new_options = tuple(
            opt for opt in original_status.options
            if opt[0] != "draft"
        )

        modified_status = FieldDefinition(
            id=original_status.id,
            field_type=original_status.field_type,
            label_key=original_status.label_key,
            help_text_key=original_status.help_text_key,
            required=original_status.required,
            options=new_options,
        )

        modified_fields = dict(original_project.fields)
        modified_fields[modified_status.id] = modified_status

        modified_project = EntityDefinition(
            id=original_project.id,
            name_key=original_project.name_key,
            description_key=original_project.description_key,
            is_root_entity=original_project.is_root_entity,
            fields=modified_fields,
        )

        v2_schema = (modified_project, base_schema_v1[1])

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v2_schema,
        )

        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert any(
            c.change_type == ChangeType.OPTION_REMOVED and c.option_value == "draft"
            for c in result.changes
        )

    # =========================================================================
    # Structural Comparison Only (Decision 7)
    # =========================================================================

    def test_metadata_changes_not_detected(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Changes to metadata (translation keys) should NOT be detected."""
        # Change translation keys (metadata only)
        original_project = base_schema_v1[0]
        original_name_field = original_project.get_field(FieldDefinitionId("project_name"))

        # Different translation keys
        modified_name_field = FieldDefinition(
            id=original_name_field.id,
            field_type=original_name_field.field_type,
            label_key=TranslationKey("field.project_name.v2"),  # Different key
            help_text_key=TranslationKey("field.project_name.help.v2"),  # Different key
            required=original_name_field.required,
            constraints=original_name_field.constraints,
        )

        modified_fields = dict(original_project.fields)
        modified_fields[modified_name_field.id] = modified_name_field

        modified_project = EntityDefinition(
            id=original_project.id,
            name_key=TranslationKey("entity.project.v2"),  # Different key
            description_key=TranslationKey("entity.project.description.v2"),  # Different key
            is_root_entity=original_project.is_root_entity,
            fields=modified_fields,
        )

        v1_metadata_changed = (modified_project, base_schema_v1[1])

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v1_metadata_changed,
        )

        # Metadata changes should result in IDENTICAL (no structural changes)
        assert result.level == CompatibilityLevel.IDENTICAL
        assert len(result.changes) == 0

    # =========================================================================
    # Version Bump Suggestions
    # =========================================================================

    def test_suggests_major_bump_for_breaking_changes(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Should suggest MAJOR version bump for breaking changes."""
        # Remove entity (breaking)
        v2_schema = (base_schema_v1[0],)

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v2_schema,
        )

        suggested = comparison_service.suggest_version_bump(
            current_version=SchemaVersion(1, 2, 3),
            changes=result.changes,
        )

        # Major bump: 1.2.3 -> 2.0.0
        assert suggested == SchemaVersion(2, 0, 0)

    def test_suggests_minor_bump_for_non_breaking_changes(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Should suggest MINOR version bump for non-breaking structural changes."""
        # Add entity (non-breaking)
        new_entity = EntityDefinition(
            id=EntityDefinitionId("laboratory"),
            name_key=TranslationKey("entity.laboratory"),
            is_root_entity=False,
            fields={},
        )
        v1_1_schema = base_schema_v1 + (new_entity,)

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v1_1_schema,
        )

        suggested = comparison_service.suggest_version_bump(
            current_version=SchemaVersion(1, 2, 3),
            changes=result.changes,
        )

        # Minor bump: 1.2.3 -> 1.3.0
        assert suggested == SchemaVersion(1, 3, 0)

    def test_suggests_no_change_for_identical_schemas(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Should return same version for identical schemas."""
        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=base_schema_v1,
        )

        suggested = comparison_service.suggest_version_bump(
            current_version=SchemaVersion(1, 2, 3),
            changes=result.changes,
        )

        # No change
        assert suggested == SchemaVersion(1, 2, 3)

    # =========================================================================
    # Complex Scenario Tests
    # =========================================================================

    def test_mixed_changes_with_breaking_is_incompatible(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Mixed breaking and non-breaking changes should be INCOMPATIBLE."""
        # Add new entity (non-breaking) AND remove a field (breaking)
        new_entity = EntityDefinition(
            id=EntityDefinitionId("laboratory"),
            name_key=TranslationKey("entity.laboratory"),
            is_root_entity=False,
            fields={},
        )

        # Remove project_date field
        original_project = base_schema_v1[0]
        modified_fields = {
            k: v for k, v in original_project.fields.items()
            if k.value != "project_date"
        }

        modified_project = EntityDefinition(
            id=original_project.id,
            name_key=original_project.name_key,
            description_key=original_project.description_key,
            is_root_entity=original_project.is_root_entity,
            fields=modified_fields,
        )

        v2_schema = (modified_project, base_schema_v1[1], new_entity)

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v2_schema,
        )

        # Mixed changes with breaking -> INCOMPATIBLE
        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert len(result.changes) >= 2

        # Has both breaking and non-breaking
        assert result.breaking_change_count >= 1
        assert result.non_breaking_change_count >= 1

    def test_rename_detected_as_delete_plus_add(
        self,
        comparison_service: SchemaComparisonService,
        base_schema_v1: tuple[EntityDefinition, ...],
    ) -> None:
        """Renaming a field should be detected as delete + add (Decision 2)."""
        # "Rename" sample_id to sample_code
        original_sample = base_schema_v1[1]

        # Remove old field
        modified_fields = {
            k: v for k, v in original_sample.fields.items()
            if k.value != "sample_id"
        }

        # Add "new" field
        new_field = FieldDefinition(
            id=FieldDefinitionId("sample_code"),  # Different ID
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.sample_code"),
            help_text_key=TranslationKey("field.sample_code.help"),
            required=True,
        )
        modified_fields[new_field.id] = new_field

        modified_sample = EntityDefinition(
            id=original_sample.id,
            name_key=original_sample.name_key,
            is_root_entity=original_sample.is_root_entity,
            fields=modified_fields,
        )

        v2_schema = (base_schema_v1[0], modified_sample)

        result = comparison_service.compare(
            source_entities=base_schema_v1,
            target_entities=v2_schema,
        )

        # Should see FIELD_REMOVED (sample_id) and FIELD_ADDED (sample_code)
        # No rename detection means this is breaking (field removed)
        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert any(
            c.change_type == ChangeType.FIELD_REMOVED and c.field_id == "sample_id"
            for c in result.changes
        )
        assert any(
            c.change_type == ChangeType.FIELD_ADDED and c.field_id == "sample_code"
            for c in result.changes
        )


class TestSchemaVersioningWorkflow:
    """End-to-end workflow tests for versioning and comparison."""

    @pytest.fixture
    def comparison_service(self) -> SchemaComparisonService:
        """Create schema comparison service."""
        return SchemaComparisonService()

    def test_version_evolution_workflow(
        self,
        comparison_service: SchemaComparisonService,
    ) -> None:
        """Test a realistic version evolution workflow."""
        # v1.0.0: Initial schema
        v1_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            help_text_key=TranslationKey("field.name.help"),
            required=True,
        )
        v1_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={v1_field.id: v1_field},
        )
        v1_schema = (v1_entity,)
        current_version = SchemaVersion(1, 0, 0)

        # v1.1.0: Add new optional field (non-breaking)
        v1_1_new_field = FieldDefinition(
            id=FieldDefinitionId("description"),
            field_type=FieldType.TEXTAREA,
            label_key=TranslationKey("field.description"),
            help_text_key=TranslationKey("field.description.help"),
            required=False,
        )
        v1_1_fields = {v1_field.id: v1_field, v1_1_new_field.id: v1_1_new_field}
        v1_1_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields=v1_1_fields,
        )
        v1_1_schema = (v1_1_entity,)

        result_1_to_1_1 = comparison_service.compare(v1_schema, v1_1_schema)
        assert result_1_to_1_1.level == CompatibilityLevel.COMPATIBLE

        suggested_v1_1 = comparison_service.suggest_version_bump(
            current_version, result_1_to_1_1.changes
        )
        assert suggested_v1_1 == SchemaVersion(1, 1, 0)

        # v2.0.0: Change field type (breaking)
        v2_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.NUMBER,  # Changed from TEXT
            label_key=TranslationKey("field.name"),
            help_text_key=TranslationKey("field.name.help"),
            required=True,
        )
        v2_fields = {v2_field.id: v2_field, v1_1_new_field.id: v1_1_new_field}
        v2_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields=v2_fields,
        )
        v2_schema = (v2_entity,)

        result_1_1_to_2 = comparison_service.compare(v1_1_schema, v2_schema)
        assert result_1_1_to_2.level == CompatibilityLevel.INCOMPATIBLE

        suggested_v2 = comparison_service.suggest_version_bump(
            suggested_v1_1, result_1_1_to_2.changes
        )
        assert suggested_v2 == SchemaVersion(2, 0, 0)

    def test_compatibility_is_informational_only(
        self,
        comparison_service: SchemaComparisonService,
    ) -> None:
        """Compatibility results are informational and do not block anything."""
        # Create breaking change scenario
        v1_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            help_text_key=TranslationKey("field.name.help"),
            required=True,
        )
        v1_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={v1_field.id: v1_field},
        )
        v1_schema = (v1_entity,)

        # v2 removes the field (breaking)
        v2_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={},  # Empty - field removed
        )
        v2_schema = (v2_entity,)

        # Compare returns INCOMPATIBLE
        result = comparison_service.compare(v1_schema, v2_schema)
        assert result.is_incompatible

        # But the result is just information - no blocking behavior
        # The result contains all the data needed for reporting
        assert len(result.changes) > 0
        assert result.breaking_change_count > 0

        # Applications can use this info as they wish, but it doesn't block
        # This is the key Phase 3 clarification: informational only
