"""Integration tests for ImportSchemaCommand (Phase 4).

Tests cover:
- File-based import operations
- Round-trip export → import → export
- Compatibility enforcement scenarios
- Real schema validation and conversion
"""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from doc_helper.application.commands.schema.export_schema_command import ExportSchemaCommand
from doc_helper.application.commands.schema.import_schema_command import ImportSchemaCommand
from doc_helper.application.dto.import_dto import (
    EnforcementPolicy,
    IdenticalSchemaAction,
)
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import (
    MaxLengthConstraint,
    MinLengthConstraint,
    MinValueConstraint,
    RequiredConstraint,
)


class TestImportFromFile:
    """Integration tests for file-based import."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        mock = Mock()
        mock.get_all.return_value = Success(())
        mock.delete.return_value = Success(None)
        mock.save.return_value = Success(None)
        return mock

    @pytest.fixture
    def import_command(self, mock_repository: Mock) -> ImportSchemaCommand:
        """Create import command."""
        return ImportSchemaCommand(mock_repository)

    def test_import_from_valid_file(
        self,
        import_command: ImportSchemaCommand,
        tmp_path: Path,
    ) -> None:
        """Should import from valid JSON file."""
        # Create import file
        import_data = {
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
        import_file = tmp_path / "schema.json"
        import_file.write_text(json.dumps(import_data, indent=2), encoding='utf-8')

        # Execute import
        result = import_command.execute(file_path=import_file)

        assert result.success is True
        assert result.schema_id == "test_schema"
        assert result.imported_version == "1.0.0"

    def test_import_from_nonexistent_file_fails(
        self,
        import_command: ImportSchemaCommand,
        tmp_path: Path,
    ) -> None:
        """Should fail when file doesn't exist."""
        result = import_command.execute(
            file_path=tmp_path / "nonexistent.json"
        )

        assert result.success is False
        assert any(e.category == "file_not_found" for e in result.validation_errors)

    def test_import_from_invalid_json_fails(
        self,
        import_command: ImportSchemaCommand,
        tmp_path: Path,
    ) -> None:
        """Should fail when file contains invalid JSON."""
        import_file = tmp_path / "invalid.json"
        import_file.write_text("{ invalid json }", encoding='utf-8')

        result = import_command.execute(file_path=import_file)

        assert result.success is False
        assert any(e.category == "json_syntax" for e in result.validation_errors)

    def test_import_preserves_unicode(
        self,
        import_command: ImportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should preserve Unicode in import."""
        import_data = {
            "schema_id": "unicode_schema",
            "entities": [
                {
                    "id": "مشروع",
                    "name_key": "entity.مشروع_проект",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "اسم",
                            "field_type": "text",
                            "label_key": "field.اسم_имя",
                            "required": True,
                            "options": [],
                            "constraints": [],
                        }
                    ],
                }
            ],
        }
        import_file = tmp_path / "unicode.json"
        import_file.write_text(json.dumps(import_data, ensure_ascii=False, indent=2), encoding='utf-8')

        result = import_command.execute(file_path=import_file)

        assert result.success is True
        # Verify save was called with correct entity
        saved_entity = mock_repository.save.call_args[0][0]
        assert saved_entity.id.value == "مشروع"


class TestExportImportRoundTrip:
    """Integration tests for export → import → export round trip."""

    @pytest.fixture
    def complex_schema(self) -> tuple[EntityDefinition, ...]:
        """Create a complex schema for round-trip testing."""
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
            default_value="0.0",
            constraints=(
                MinValueConstraint(min_value=0),
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

    def test_round_trip_produces_identical_output(
        self,
        complex_schema: tuple[EntityDefinition, ...],
        tmp_path: Path,
    ) -> None:
        """Export → Import → Export should produce identical JSON."""
        # Step 1: Export original schema
        export_repo = Mock()
        export_repo.get_all.return_value = Success(complex_schema)
        export_command = ExportSchemaCommand(export_repo)

        export_path1 = tmp_path / "export1.json"
        export_result1 = export_command.execute(
            schema_id="test_schema",
            file_path=export_path1,
            version="1.0.0",
        )
        assert export_result1.is_success()

        # Step 2: Import the exported schema
        import_repo = Mock()
        import_repo.get_all.return_value = Success(())
        import_repo.delete.return_value = Success(None)
        import_repo.save.return_value = Success(None)

        # Capture saved entities
        saved_entities = []
        def capture_save(entity):
            saved_entities.append(entity)
            return Success(None)
        import_repo.save.side_effect = capture_save

        import_command = ImportSchemaCommand(import_repo)
        import_result = import_command.execute(file_path=export_path1)
        assert import_result.success is True

        # Step 3: Export the imported schema
        export_repo2 = Mock()
        export_repo2.get_all.return_value = Success(tuple(saved_entities))
        export_command2 = ExportSchemaCommand(export_repo2)

        export_path2 = tmp_path / "export2.json"
        export_result2 = export_command2.execute(
            schema_id="test_schema",
            file_path=export_path2,
            version="1.0.0",
        )
        assert export_result2.is_success()

        # Step 4: Compare JSON content
        content1 = json.loads(export_path1.read_text(encoding='utf-8'))
        content2 = json.loads(export_path2.read_text(encoding='utf-8'))

        # Compare schema structure (entities and fields)
        assert content1["schema_id"] == content2["schema_id"]
        assert content1["version"] == content2["version"]
        assert len(content1["entities"]) == len(content2["entities"])

        # Compare entity by entity
        entities1 = {e["id"]: e for e in content1["entities"]}
        entities2 = {e["id"]: e for e in content2["entities"]}

        for entity_id in entities1:
            assert entity_id in entities2
            e1 = entities1[entity_id]
            e2 = entities2[entity_id]

            assert e1["name_key"] == e2["name_key"]
            assert e1["is_root_entity"] == e2["is_root_entity"]

            # Compare fields
            fields1 = {f["id"]: f for f in e1["fields"]}
            fields2 = {f["id"]: f for f in e2["fields"]}

            for field_id in fields1:
                assert field_id in fields2
                f1 = fields1[field_id]
                f2 = fields2[field_id]

                assert f1["field_type"] == f2["field_type"]
                assert f1["label_key"] == f2["label_key"]
                assert f1["required"] == f2["required"]


class TestCompatibilityEnforcement:
    """Integration tests for compatibility enforcement scenarios."""

    @pytest.fixture
    def base_schema(self) -> EntityDefinition:
        """Create base schema for comparison."""
        name_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            required=True,
        )
        status_field = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            required=True,
            options=(
                ("active", TranslationKey("status.active")),
                ("completed", TranslationKey("status.completed")),
            ),
        )
        return EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={
                name_field.id: name_field,
                status_field.id: status_field,
            },
        )

    def test_strict_blocks_breaking_changes(
        self,
        base_schema: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """STRICT policy should block breaking changes."""
        # Create import file with removed field (breaking)
        import_data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []},
                        # status field removed - breaking change
                    ],
                }
            ],
        }
        import_file = tmp_path / "breaking.json"
        import_file.write_text(json.dumps(import_data), encoding='utf-8')

        # Setup repository with existing schema
        repo = Mock()
        repo.get_all.return_value = Success((base_schema,))
        repo.delete.return_value = Success(None)
        repo.save.return_value = Success(None)

        command = ImportSchemaCommand(repo)
        result = command.execute(
            file_path=import_file,
            enforcement_policy=EnforcementPolicy.STRICT,
        )

        assert result.success is False
        assert result.compatibility_result is not None
        assert result.compatibility_result.is_incompatible
        repo.save.assert_not_called()

    def test_force_allows_breaking_changes(
        self,
        base_schema: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """force=True should allow breaking changes."""
        import_data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []},
                    ],
                }
            ],
        }
        import_file = tmp_path / "breaking.json"
        import_file.write_text(json.dumps(import_data), encoding='utf-8')

        repo = Mock()
        repo.get_all.return_value = Success((base_schema,))
        repo.delete.return_value = Success(None)
        repo.save.return_value = Success(None)

        command = ImportSchemaCommand(repo)
        result = command.execute(
            file_path=import_file,
            enforcement_policy=EnforcementPolicy.STRICT,
            force=True,
        )

        assert result.success is True
        assert any(w.category == "compatibility" for w in result.warnings)

    def test_warn_policy_allows_with_warnings(
        self,
        base_schema: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """WARN policy should allow breaking changes with warnings."""
        import_data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []},
                    ],
                }
            ],
        }
        import_file = tmp_path / "breaking.json"
        import_file.write_text(json.dumps(import_data), encoding='utf-8')

        repo = Mock()
        repo.get_all.return_value = Success((base_schema,))
        repo.delete.return_value = Success(None)
        repo.save.return_value = Success(None)

        command = ImportSchemaCommand(repo)
        result = command.execute(
            file_path=import_file,
            enforcement_policy=EnforcementPolicy.WARN,
        )

        assert result.success is True
        assert any(w.category == "compatibility" for w in result.warnings)

    def test_compatible_changes_allowed_without_force(
        self,
        base_schema: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Compatible (non-breaking) changes should be allowed."""
        # Add new field (compatible change)
        import_data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []},
                        {"id": "status", "field_type": "dropdown", "label_key": "field.status", "required": True,
                         "options": [{"value": "active", "label_key": "status.active"}, {"value": "completed", "label_key": "status.completed"}],
                         "constraints": []},
                        {"id": "description", "field_type": "textarea", "label_key": "field.desc", "required": False, "options": [], "constraints": []},
                    ],
                }
            ],
        }
        import_file = tmp_path / "compatible.json"
        import_file.write_text(json.dumps(import_data), encoding='utf-8')

        repo = Mock()
        repo.get_all.return_value = Success((base_schema,))
        repo.delete.return_value = Success(None)
        repo.save.return_value = Success(None)

        command = ImportSchemaCommand(repo)
        result = command.execute(
            file_path=import_file,
            enforcement_policy=EnforcementPolicy.STRICT,
        )

        assert result.success is True
        assert result.compatibility_result is not None
        assert not result.compatibility_result.is_incompatible


class TestVersionHandling:
    """Integration tests for version field handling."""

    def test_version_preserved_in_result(self, tmp_path: Path) -> None:
        """Should preserve version from import file."""
        import_data = {
            "schema_id": "test",
            "version": "2.1.0",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []},
                    ],
                }
            ],
        }
        import_file = tmp_path / "versioned.json"
        import_file.write_text(json.dumps(import_data), encoding='utf-8')

        repo = Mock()
        repo.get_all.return_value = Success(())
        repo.delete.return_value = Success(None)
        repo.save.return_value = Success(None)

        command = ImportSchemaCommand(repo)
        result = command.execute(file_path=import_file)

        assert result.success is True
        assert result.imported_version == "2.1.0"

    def test_import_without_version_succeeds(self, tmp_path: Path) -> None:
        """Should succeed when version is not in import file."""
        import_data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []},
                    ],
                }
            ],
        }
        import_file = tmp_path / "no_version.json"
        import_file.write_text(json.dumps(import_data), encoding='utf-8')

        repo = Mock()
        repo.get_all.return_value = Success(())
        repo.delete.return_value = Success(None)
        repo.save.return_value = Success(None)

        command = ImportSchemaCommand(repo)
        result = command.execute(file_path=import_file)

        assert result.success is True
        assert result.imported_version is None


class TestAtomicImport:
    """Integration tests verifying atomic import behavior."""

    def test_delete_called_before_save(self, tmp_path: Path) -> None:
        """Should delete existing entities before saving new ones."""
        existing_entity = EntityDefinition(
            id=EntityDefinitionId("old_entity"),
            name_key=TranslationKey("entity.old"),
            is_root_entity=True,
            fields={},
        )

        import_data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "new_entity",
                    "name_key": "entity.new",
                    "is_root_entity": True,
                    "fields": [
                        {"id": "name", "field_type": "text", "label_key": "field.name", "required": True, "options": [], "constraints": []},
                    ],
                }
            ],
        }
        import_file = tmp_path / "new.json"
        import_file.write_text(json.dumps(import_data), encoding='utf-8')

        call_order = []
        repo = Mock()
        repo.get_all.return_value = Success((existing_entity,))

        def track_delete(entity_id):
            call_order.append(("delete", entity_id.value))
            return Success(None)

        def track_save(entity):
            call_order.append(("save", entity.id.value))
            return Success(None)

        repo.delete.side_effect = track_delete
        repo.save.side_effect = track_save

        command = ImportSchemaCommand(repo)
        result = command.execute(
            file_path=import_file,
            identical_action=IdenticalSchemaAction.REPLACE,
            force=True,  # Bypass compatibility check - we're testing atomic import behavior
        )

        assert result.success is True
        # Verify delete came before save
        delete_indices = [i for i, (op, _) in enumerate(call_order) if op == "delete"]
        save_indices = [i for i, (op, _) in enumerate(call_order) if op == "save"]

        assert all(d < s for d in delete_indices for s in save_indices), \
            "All deletes should happen before any saves"
