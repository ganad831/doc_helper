"""Unit tests for ExportSchemaCommand (Phase 2 Step 4).

Tests cover:
- Invariant validation (empty schema, file exists, translation keys)
- Quality warning generation (category-level)
- Export content correctness
- Exclusion verification
- Failure behavior
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from doc_helper.application.commands.schema.export_schema_command import ExportSchemaCommand
from doc_helper.application.dto.export_dto import ExportResult
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import (
    MinLengthConstraint,
    MaxLengthConstraint,
    RequiredConstraint,
)


class TestExportSchemaCommand:
    """Unit tests for ExportSchemaCommand."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def command(self, mock_repository: Mock) -> ExportSchemaCommand:
        """Create command with mock repository."""
        return ExportSchemaCommand(mock_repository)

    @pytest.fixture
    def simple_field(self) -> FieldDefinition:
        """Create a simple text field."""
        return FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            help_text_key=TranslationKey("field.name.help"),
            required=True,
        )

    @pytest.fixture
    def field_with_constraints(self) -> FieldDefinition:
        """Create a field with constraints."""
        return FieldDefinition(
            id=FieldDefinitionId("description"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.description"),
            help_text_key=TranslationKey("field.description.help"),
            required=False,
            constraints=(
                MinLengthConstraint(min_length=5),
                MaxLengthConstraint(max_length=100),
            ),
        )

    @pytest.fixture
    def dropdown_field(self) -> FieldDefinition:
        """Create a dropdown field with options."""
        return FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            help_text_key=TranslationKey("field.status.help"),
            required=True,
            options=(
                ("active", TranslationKey("status.active")),
                ("inactive", TranslationKey("status.inactive")),
            ),
        )

    @pytest.fixture
    def entity_with_fields(
        self, simple_field: FieldDefinition, field_with_constraints: FieldDefinition
    ) -> EntityDefinition:
        """Create entity with multiple fields."""
        return EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            description_key=TranslationKey("entity.project.description"),
            is_root_entity=True,
            fields={
                simple_field.id: simple_field,
                field_with_constraints.id: field_with_constraints,
            },
        )

    @pytest.fixture
    def empty_entity(self) -> EntityDefinition:
        """Create entity with no fields."""
        return EntityDefinition(
            id=EntityDefinitionId("empty_entity"),
            name_key=TranslationKey("entity.empty"),
            is_root_entity=False,
            fields={},
        )

    # =========================================================================
    # SUCCESS Cases
    # =========================================================================

    def test_export_schema_success(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should successfully export valid schema."""
        # Setup
        mock_repository.get_all.return_value = Success((entity_with_fields,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        export_result: ExportResult = result.value
        assert export_result.success is True
        assert export_result.export_data is not None
        assert export_result.export_data.schema_id == "test_schema"
        assert len(export_result.export_data.entities) == 1
        assert export_result.error is None

        # Verify file was created
        assert export_path.exists()

    def test_export_includes_entity_metadata(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should include all allowed entity metadata in export."""
        # Setup
        mock_repository.get_all.return_value = Success((entity_with_fields,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        entity_export = result.value.export_data.entities[0]
        assert entity_export.id == "project"
        assert entity_export.name_key == "entity.project"
        assert entity_export.description_key == "entity.project.description"
        assert entity_export.is_root_entity is True

    def test_export_includes_field_metadata(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should include all allowed field metadata in export."""
        # Setup
        mock_repository.get_all.return_value = Success((entity_with_fields,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        fields = result.value.export_data.entities[0].fields
        assert len(fields) == 2

        # Find the name field
        name_field = next(f for f in fields if f.id == "name")
        assert name_field.field_type == "text"  # FieldType enum values are lowercase
        assert name_field.label_key == "field.name"
        assert name_field.help_text_key == "field.name.help"
        assert name_field.required is True

    def test_export_includes_constraints(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should include constraint metadata in export."""
        # Setup
        mock_repository.get_all.return_value = Success((entity_with_fields,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        fields = result.value.export_data.entities[0].fields

        # Find the description field with constraints
        desc_field = next(f for f in fields if f.id == "description")
        assert len(desc_field.constraints) == 2

        constraint_types = {c.constraint_type for c in desc_field.constraints}
        assert "MinLengthConstraint" in constraint_types
        assert "MaxLengthConstraint" in constraint_types

        # Check constraint parameters
        min_constraint = next(c for c in desc_field.constraints if c.constraint_type == "MinLengthConstraint")
        assert min_constraint.parameters["min_length"] == 5

    def test_export_includes_dropdown_options(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        dropdown_field: FieldDefinition,
        tmp_path: Path,
    ) -> None:
        """Should include options for choice fields."""
        # Setup
        entity = EntityDefinition(
            id=EntityDefinitionId("test"),
            name_key=TranslationKey("entity.test"),
            is_root_entity=True,
            fields={dropdown_field.id: dropdown_field},
        )
        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        field = result.value.export_data.entities[0].fields[0]
        assert len(field.options) == 2
        assert field.options[0].value == "active"
        assert field.options[0].label_key == "status.active"

    def test_export_includes_schema_id(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should include schema identifier in export (Decision 7)."""
        # Setup
        mock_repository.get_all.return_value = Success((entity_with_fields,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="my_custom_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        assert result.value.export_data.schema_id == "my_custom_schema"

    # =========================================================================
    # FAILURE Cases - Invariant Violations
    # =========================================================================

    def test_fail_if_file_exists(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should fail if export file already exists (Decision 1)."""
        # Setup - create existing file
        export_path = tmp_path / "existing.json"
        export_path.write_text("{}")

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_failure()
        assert "already exists" in result.error.lower()

        # Repository should not be called
        mock_repository.get_all.assert_not_called()

    def test_fail_if_schema_empty_no_entities(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should fail if schema has no entities (Decision 2)."""
        # Setup
        mock_repository.get_all.return_value = Success(())
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_failure()
        assert "empty schema" in result.error.lower()
        assert "no entities" in result.error.lower()

        # File should not be created
        assert not export_path.exists()

    def test_fail_if_schema_empty_no_fields(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        empty_entity: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should fail if schema has entities but no fields (Decision 2)."""
        # Setup
        mock_repository.get_all.return_value = Success((empty_entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_failure()
        assert "empty schema" in result.error.lower()
        assert "no fields" in result.error.lower()

        # File should not be created
        assert not export_path.exists()

    def test_fail_if_repository_error(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should fail if repository returns error."""
        # Setup
        mock_repository.get_all.return_value = Failure("Database connection failed")
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_failure()
        assert "failed to load schema" in result.error.lower()

    def test_fail_if_entity_name_key_empty(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        simple_field: FieldDefinition,
        tmp_path: Path,
    ) -> None:
        """Should fail if entity name_key is empty (Decision 3)."""
        # Setup - entity with empty name key
        # Note: TranslationKey validates non-empty, so we mock the entity
        entity = Mock()
        entity.id.value = "test"
        entity.name_key.key = ""  # Empty key - TranslationKey uses .key not .value
        entity.description_key = None
        entity.is_root_entity = False
        entity.field_count = 1
        entity.get_all_fields.return_value = [simple_field]

        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_failure()
        assert "translation key" in result.error.lower()

    def test_fail_if_field_label_key_empty(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should fail if field label_key is empty (Decision 3)."""
        # Setup - field with empty label key
        field = Mock()
        field.id.value = "test_field"
        field.field_type.value = "TEXT"
        field.label_key.key = "   "  # Whitespace-only - TranslationKey uses .key not .value
        field.help_text_key = None
        field.required = False
        field.default_value = None
        field.is_choice_field = False
        field.options = ()
        field.constraints = ()
        field.formula = None
        field.control_rules = ()
        field.lookup_entity_id = None
        field.child_entity_id = None

        entity = Mock()
        entity.id.value = "test"
        entity.name_key.key = "entity.test"  # TranslationKey uses .key not .value
        entity.description_key = None
        entity.is_root_entity = True
        entity.field_count = 1
        entity.get_all_fields.return_value = [field]

        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_failure()
        assert "translation key" in result.error.lower()

    # =========================================================================
    # WARNING Cases - Quality Checks
    # =========================================================================

    def test_warn_entity_with_no_fields(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        empty_entity: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should warn when entity has no fields."""
        # Setup - one entity with fields, one without
        mock_repository.get_all.return_value = Success((entity_with_fields, empty_entity))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert - should succeed with warning
        assert result.is_success()
        warnings = result.value.warnings

        # Find the warning about empty entity
        empty_warnings = [w for w in warnings if w.category == "incomplete_entity"]
        assert len(empty_warnings) == 1
        assert "empty_entity" in empty_warnings[0].message
        assert "no fields" in empty_warnings[0].message.lower()

    def test_warn_field_with_no_help_text(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should warn when field has no help text."""
        # Setup - field without help text
        field = FieldDefinition(
            id=FieldDefinitionId("no_help"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.no_help"),
            # No help_text_key
            required=False,
        )
        entity = EntityDefinition(
            id=EntityDefinitionId("test"),
            name_key=TranslationKey("entity.test"),
            is_root_entity=True,
            fields={field.id: field},
        )
        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        warnings = result.value.warnings

        missing_metadata_warnings = [w for w in warnings if w.category == "missing_metadata"]
        assert len(missing_metadata_warnings) >= 1
        assert any("no help text" in w.message.lower() for w in missing_metadata_warnings)

    def test_warn_excluded_formulas(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should warn when formulas are excluded (Decision 4: category warnings)."""
        # Setup - field with formula
        field = FieldDefinition(
            id=FieldDefinitionId("calculated"),
            field_type=FieldType.CALCULATED,
            label_key=TranslationKey("field.calculated"),
            help_text_key=TranslationKey("field.calculated.help"),
            formula="field1 + field2",
        )
        entity = EntityDefinition(
            id=EntityDefinitionId("test"),
            name_key=TranslationKey("entity.test"),
            is_root_entity=True,
            fields={field.id: field},
        )
        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        warnings = result.value.warnings

        excluded_warnings = [w for w in warnings if w.category == "excluded_data"]
        formula_warnings = [w for w in excluded_warnings if "formula" in w.message.lower()]
        assert len(formula_warnings) == 1
        assert "1 formula" in formula_warnings[0].message

    def test_export_control_rules(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should export control rules (Phase F-10)."""
        # Import ControlRuleExportDTO
        from doc_helper.application.dto.export_dto import ControlRuleExportDTO

        # Setup - field with control rules
        field = Mock()
        field.id.value = "controlled"
        field.field_type.value = "TEXT"
        field.label_key.key = "field.controlled"  # TranslationKey uses .key not .value
        field.help_text_key = Mock()
        field.help_text_key.key = "field.controlled.help"  # TranslationKey uses .key not .value
        field.required = False
        field.default_value = None
        field.is_choice_field = False
        field.options = ()
        field.constraints = ()
        field.formula = None
        # Phase F-10: Control rules are ControlRuleExportDTO objects
        field.control_rules = (
            ControlRuleExportDTO(
                rule_type="VISIBILITY",
                target_field_id="target_field",
                formula_text="{{status}} == 'active'",
            ),
            ControlRuleExportDTO(
                rule_type="ENABLED",
                target_field_id="target_field",
                formula_text="{{mode}} == 'edit'",
            ),
        )
        field.lookup_entity_id = None
        field.child_entity_id = None

        entity = Mock()
        entity.id.value = "test"
        entity.name_key.key = "entity.test"  # TranslationKey uses .key not .value
        entity.description_key = None
        entity.is_root_entity = True
        entity.field_count = 1
        entity.get_all_fields.return_value = [field]

        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()

        # Verify control rules are in the export file (not excluded)
        import json
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)

        # Check that control_rules are present in the exported field
        exported_field = exported_data["entities"][0]["fields"][0]
        assert "control_rules" in exported_field
        assert len(exported_field["control_rules"]) == 2
        assert exported_field["control_rules"][0]["rule_type"] == "VISIBILITY"
        assert exported_field["control_rules"][0]["formula_text"] == "{{status}} == 'active'"
        assert exported_field["control_rules"][1]["rule_type"] == "ENABLED"
        assert exported_field["control_rules"][1]["formula_text"] == "{{mode}} == 'edit'"

    def test_export_output_mappings(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should export output mappings (Phase F-12.5)."""
        # Import OutputMappingExportDTO
        from doc_helper.application.dto.export_dto import OutputMappingExportDTO

        # Setup - field with output mappings
        field = Mock()
        field.id.value = "mapped_field"
        field.field_type.value = "TEXT"
        field.label_key.key = "field.mapped"
        field.help_text_key = Mock()
        field.help_text_key.key = "field.mapped.help"
        field.required = False
        field.default_value = None
        field.is_choice_field = False
        field.options = ()
        field.constraints = ()
        field.formula = None
        field.control_rules = ()
        # Phase F-12.5: Output mappings are OutputMappingExportDTO objects
        field.output_mappings = (
            OutputMappingExportDTO(
                target="TEXT",
                formula_text="{{depth_from}} - {{depth_to}}",
            ),
            OutputMappingExportDTO(
                target="NUMBER",
                formula_text="{{area}} * {{density}}",
            ),
            OutputMappingExportDTO(
                target="BOOLEAN",
                formula_text="{{status}} == 'completed'",
            ),
        )
        field.lookup_entity_id = None
        field.child_entity_id = None

        entity = Mock()
        entity.id.value = "test"
        entity.name_key.key = "entity.test"
        entity.description_key = None
        entity.is_root_entity = True
        entity.field_count = 1
        entity.get_all_fields.return_value = [field]

        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()

        # Verify output mappings are in the export file
        import json
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)

        # Check that output_mappings are present in the exported field
        exported_field = exported_data["entities"][0]["fields"][0]
        assert "output_mappings" in exported_field
        assert len(exported_field["output_mappings"]) == 3
        assert exported_field["output_mappings"][0]["target"] == "TEXT"
        assert exported_field["output_mappings"][0]["formula_text"] == "{{depth_from}} - {{depth_to}}"
        assert exported_field["output_mappings"][1]["target"] == "NUMBER"
        assert exported_field["output_mappings"][1]["formula_text"] == "{{area}} * {{density}}"
        assert exported_field["output_mappings"][2]["target"] == "BOOLEAN"
        assert exported_field["output_mappings"][2]["formula_text"] == "{{status}} == 'completed'"

    # =========================================================================
    # EXCLUSION Verification
    # =========================================================================

    def test_excludes_formula_from_export(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should NOT include formula expression in export."""
        # Setup
        field = FieldDefinition(
            id=FieldDefinitionId("calculated"),
            field_type=FieldType.CALCULATED,
            label_key=TranslationKey("field.calculated"),
            help_text_key=TranslationKey("field.calculated.help"),
            formula="field1 + field2",
        )
        entity = EntityDefinition(
            id=EntityDefinitionId("test"),
            name_key=TranslationKey("entity.test"),
            is_root_entity=True,
            fields={field.id: field},
        )
        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        exported_field = result.value.export_data.entities[0].fields[0]

        # FieldExportDTO should not have formula attribute
        assert not hasattr(exported_field, 'formula')

    def test_excludes_lookup_entity_from_export(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should NOT include lookup_entity_id in export (behavioral)."""
        # Setup
        field = FieldDefinition(
            id=FieldDefinitionId("lookup"),
            field_type=FieldType.LOOKUP,
            label_key=TranslationKey("field.lookup"),
            help_text_key=TranslationKey("field.lookup.help"),
            lookup_entity_id="other_entity",
            lookup_display_field="name",
        )
        entity = EntityDefinition(
            id=EntityDefinitionId("test"),
            name_key=TranslationKey("entity.test"),
            is_root_entity=True,
            fields={field.id: field},
        )
        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        exported_field = result.value.export_data.entities[0].fields[0]

        # FieldExportDTO should not have lookup fields
        assert not hasattr(exported_field, 'lookup_entity_id')
        assert not hasattr(exported_field, 'lookup_display_field')

    def test_excludes_child_entity_from_export(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should NOT include child_entity_id in export (behavioral)."""
        # Setup
        field = FieldDefinition(
            id=FieldDefinitionId("table"),
            field_type=FieldType.TABLE,
            label_key=TranslationKey("field.table"),
            help_text_key=TranslationKey("field.table.help"),
            child_entity_id="child_entity",
        )
        entity = EntityDefinition(
            id=EntityDefinitionId("test"),
            name_key=TranslationKey("entity.test"),
            is_root_entity=True,
            fields={field.id: field},
        )
        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        exported_field = result.value.export_data.entities[0].fields[0]

        # FieldExportDTO should not have child_entity_id
        assert not hasattr(exported_field, 'child_entity_id')

    # =========================================================================
    # Decision 8: Root Entity Requirement
    # =========================================================================

    def test_allows_zero_root_entities(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        simple_field: FieldDefinition,
        tmp_path: Path,
    ) -> None:
        """Should allow export with zero root entities (Decision 8)."""
        # Setup - entity that is NOT root
        entity = EntityDefinition(
            id=EntityDefinitionId("child"),
            name_key=TranslationKey("entity.child"),
            is_root_entity=False,  # Not a root entity
            fields={simple_field.id: simple_field},
        )
        mock_repository.get_all.return_value = Success((entity,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert - should succeed without root entity
        assert result.is_success()
        assert result.value.export_data.entities[0].is_root_entity is False

    def test_allows_multiple_root_entities(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        simple_field: FieldDefinition,
        tmp_path: Path,
    ) -> None:
        """Should allow export with multiple root entities (Decision 8)."""
        # Setup - two root entities
        entity1 = EntityDefinition(
            id=EntityDefinitionId("root1"),
            name_key=TranslationKey("entity.root1"),
            is_root_entity=True,
            fields={simple_field.id: simple_field},
        )
        field2 = FieldDefinition(
            id=FieldDefinitionId("field2"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.field2"),
            help_text_key=TranslationKey("field.field2.help"),
        )
        entity2 = EntityDefinition(
            id=EntityDefinitionId("root2"),
            name_key=TranslationKey("entity.root2"),
            is_root_entity=True,
            fields={field2.id: field2},
        )
        mock_repository.get_all.return_value = Success((entity1, entity2))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert - should succeed with multiple root entities
        assert result.is_success()
        assert len(result.value.export_data.entities) == 2
        assert all(e.is_root_entity for e in result.value.export_data.entities)

    # =========================================================================
    # File Output Verification
    # =========================================================================

    def test_creates_valid_json_file(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should create valid JSON file."""
        import json

        # Setup
        mock_repository.get_all.return_value = Success((entity_with_fields,))
        export_path = tmp_path / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        assert export_path.exists()

        # Verify JSON is valid and parseable
        content = export_path.read_text(encoding='utf-8')
        parsed = json.loads(content)

        assert parsed["schema_id"] == "test_schema"
        assert len(parsed["entities"]) == 1
        assert parsed["entities"][0]["id"] == "project"

    def test_no_file_created_on_failure(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        tmp_path: Path,
    ) -> None:
        """Should not create file when export fails."""
        # Setup - empty schema
        mock_repository.get_all.return_value = Success(())
        export_path = tmp_path / "should_not_exist.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_failure()
        assert not export_path.exists()

    def test_creates_parent_directories(
        self,
        command: ExportSchemaCommand,
        mock_repository: Mock,
        entity_with_fields: EntityDefinition,
        tmp_path: Path,
    ) -> None:
        """Should create parent directories if they don't exist."""
        # Setup
        mock_repository.get_all.return_value = Success((entity_with_fields,))
        export_path = tmp_path / "nested" / "deep" / "export.json"

        # Execute
        result = command.execute(schema_id="test_schema", file_path=export_path)

        # Assert
        assert result.is_success()
        assert export_path.exists()
        assert export_path.parent.exists()
