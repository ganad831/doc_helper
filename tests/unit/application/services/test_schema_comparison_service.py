"""Unit tests for SchemaComparisonService (Phase 3)."""

import pytest

from doc_helper.application.services.schema_comparison_service import (
    SchemaComparisonService,
)
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_change import ChangeType, SchemaChange
from doc_helper.domain.schema.schema_compatibility import CompatibilityLevel
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.schema_version import SchemaVersion
from doc_helper.domain.validation.constraints import (
    MinLengthConstraint,
    MaxLengthConstraint,
    RequiredConstraint,
)


class TestSchemaComparisonService:
    """Unit tests for SchemaComparisonService."""

    @pytest.fixture
    def service(self) -> SchemaComparisonService:
        """Create comparison service."""
        return SchemaComparisonService()

    @pytest.fixture
    def simple_field(self) -> FieldDefinition:
        """Create a simple text field."""
        return FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            required=True,
        )

    @pytest.fixture
    def simple_entity(self, simple_field: FieldDefinition) -> EntityDefinition:
        """Create a simple entity with one field."""
        return EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={simple_field.id: simple_field},
        )

    # =========================================================================
    # Identical Schema Tests
    # =========================================================================

    def test_identical_schemas(
        self,
        service: SchemaComparisonService,
        simple_entity: EntityDefinition,
    ) -> None:
        """Should return IDENTICAL for same schemas."""
        source = (simple_entity,)
        target = (simple_entity,)

        result = service.compare(source, target)

        assert result.level == CompatibilityLevel.IDENTICAL
        assert result.total_changes == 0
        assert result.is_identical

    def test_empty_schemas_identical(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should return IDENTICAL for two empty schemas."""
        result = service.compare((), ())

        assert result.level == CompatibilityLevel.IDENTICAL
        assert result.total_changes == 0

    # =========================================================================
    # Entity-Level Change Tests
    # =========================================================================

    def test_entity_added(
        self,
        service: SchemaComparisonService,
        simple_entity: EntityDefinition,
    ) -> None:
        """Should detect entity addition (non-breaking)."""
        source = ()
        target = (simple_entity,)

        result = service.compare(source, target)

        assert result.level == CompatibilityLevel.COMPATIBLE
        assert result.total_changes == 1
        assert result.breaking_change_count == 0

        change = result.changes[0]
        assert change.change_type == ChangeType.ENTITY_ADDED
        assert change.entity_id == "project"

    def test_entity_removed(
        self,
        service: SchemaComparisonService,
        simple_entity: EntityDefinition,
    ) -> None:
        """Should detect entity removal (BREAKING)."""
        source = (simple_entity,)
        target = ()

        result = service.compare(source, target)

        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert result.total_changes == 1
        assert result.breaking_change_count == 1

        change = result.changes[0]
        assert change.change_type == ChangeType.ENTITY_REMOVED
        assert change.entity_id == "project"

    def test_multiple_entities_mixed_changes(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect multiple entity changes."""
        field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
        )
        entity_a = EntityDefinition(
            id=EntityDefinitionId("entity_a"),
            name_key=TranslationKey("entity.a"),
            is_root_entity=True,
            fields={field.id: field},
        )
        entity_b = EntityDefinition(
            id=EntityDefinitionId("entity_b"),
            name_key=TranslationKey("entity.b"),
            is_root_entity=False,
            fields={field.id: field},
        )
        entity_c = EntityDefinition(
            id=EntityDefinitionId("entity_c"),
            name_key=TranslationKey("entity.c"),
            is_root_entity=False,
            fields={field.id: field},
        )

        source = (entity_a, entity_b)  # A and B exist
        target = (entity_a, entity_c)  # A and C exist (B removed, C added)

        result = service.compare(source, target)

        assert result.level == CompatibilityLevel.INCOMPATIBLE  # B removed is breaking
        assert result.total_changes == 2

        change_types = {c.change_type for c in result.changes}
        assert ChangeType.ENTITY_ADDED in change_types
        assert ChangeType.ENTITY_REMOVED in change_types

    # =========================================================================
    # Field-Level Change Tests
    # =========================================================================

    def test_field_added(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect field addition (non-breaking)."""
        field1 = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
        )
        field2 = FieldDefinition(
            id=FieldDefinitionId("description"),
            field_type=FieldType.TEXTAREA,
            label_key=TranslationKey("field.description"),
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={field1.id: field1},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={field1.id: field1, field2.id: field2},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.COMPATIBLE
        assert result.total_changes == 1

        change = result.changes[0]
        assert change.change_type == ChangeType.FIELD_ADDED
        assert change.field_id == "description"

    def test_field_removed(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect field removal (BREAKING)."""
        field1 = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
        )
        field2 = FieldDefinition(
            id=FieldDefinitionId("old_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.old"),
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={field1.id: field1, field2.id: field2},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={field1.id: field1},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.INCOMPATIBLE
        assert result.breaking_change_count == 1

        change = result.changes[0]
        assert change.change_type == ChangeType.FIELD_REMOVED
        assert change.field_id == "old_field"

    def test_field_type_changed(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect field type change (BREAKING)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.status"),
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            options=(
                ("active", TranslationKey("status.active")),
            ),
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.INCOMPATIBLE

        type_changes = [c for c in result.changes if c.change_type == ChangeType.FIELD_TYPE_CHANGED]
        assert len(type_changes) == 1
        assert type_changes[0].old_value == "text"
        assert type_changes[0].new_value == "dropdown"

    def test_field_required_changed(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect required flag change (non-breaking)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            required=False,
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            required=True,
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.COMPATIBLE  # required change is non-breaking
        assert result.total_changes == 1

        change = result.changes[0]
        assert change.change_type == ChangeType.FIELD_REQUIRED_CHANGED

    # =========================================================================
    # Constraint Change Tests
    # =========================================================================

    def test_constraint_added(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect constraint addition (non-breaking)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            constraints=(),
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            constraints=(MinLengthConstraint(min_length=3),),
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.COMPATIBLE

        constraint_changes = [c for c in result.changes if c.change_type == ChangeType.CONSTRAINT_ADDED]
        assert len(constraint_changes) == 1
        assert constraint_changes[0].constraint_type == "MinLengthConstraint"

    def test_constraint_removed(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect constraint removal (non-breaking)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            constraints=(MinLengthConstraint(min_length=3),),
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            constraints=(),
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.COMPATIBLE

        constraint_changes = [c for c in result.changes if c.change_type == ChangeType.CONSTRAINT_REMOVED]
        assert len(constraint_changes) == 1

    def test_constraint_modified(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect constraint modification (non-breaking)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            constraints=(MinLengthConstraint(min_length=3),),
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name"),
            constraints=(MinLengthConstraint(min_length=5),),  # Changed from 3 to 5
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.COMPATIBLE

        constraint_changes = [c for c in result.changes if c.change_type == ChangeType.CONSTRAINT_MODIFIED]
        assert len(constraint_changes) == 1

    # =========================================================================
    # Option Change Tests
    # =========================================================================

    def test_option_added(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect option addition (non-breaking)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            options=(
                ("active", TranslationKey("status.active")),
            ),
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            options=(
                ("active", TranslationKey("status.active")),
                ("inactive", TranslationKey("status.inactive")),
            ),
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.COMPATIBLE

        option_changes = [c for c in result.changes if c.change_type == ChangeType.OPTION_ADDED]
        assert len(option_changes) == 1
        assert option_changes[0].option_value == "inactive"

    def test_option_removed(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should detect option removal (BREAKING)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            options=(
                ("active", TranslationKey("status.active")),
                ("archived", TranslationKey("status.archived")),
            ),
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("status"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.status"),
            options=(
                ("active", TranslationKey("status.active")),
            ),
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        assert result.level == CompatibilityLevel.INCOMPATIBLE  # Option removed is breaking

        option_changes = [c for c in result.changes if c.change_type == ChangeType.OPTION_REMOVED]
        assert len(option_changes) == 1
        assert option_changes[0].option_value == "archived"

    # =========================================================================
    # Structural Comparison Only (Decision 7)
    # =========================================================================

    def test_ignores_translation_key_changes(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should ignore translation key changes (Decision 7)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name.old"),
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.name.new"),  # Different label key
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project.old"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project.new"),  # Different name key
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        # Should be identical because we ignore metadata
        assert result.level == CompatibilityLevel.IDENTICAL
        assert result.total_changes == 0

    def test_ignores_default_value_changes(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should ignore default value changes (Decision 7)."""
        source_field = FieldDefinition(
            id=FieldDefinitionId("count"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.count"),
            default_value="0",
        )
        target_field = FieldDefinition(
            id=FieldDefinitionId("count"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.count"),
            default_value="10",  # Different default
        )

        source_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={source_field.id: source_field},
        )
        target_entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            is_root_entity=True,
            fields={target_field.id: target_field},
        )

        result = service.compare((source_entity,), (target_entity,))

        # Should be identical because we ignore default values
        assert result.level == CompatibilityLevel.IDENTICAL
        assert result.total_changes == 0

    # =========================================================================
    # Version Suggestion Tests
    # =========================================================================

    def test_suggest_no_bump_for_identical(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should suggest same version for no changes."""
        current = SchemaVersion(1, 0, 0)
        suggested = service.suggest_version_bump(current, ())
        assert suggested == current

    def test_suggest_major_bump_for_breaking(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should suggest major bump for breaking changes."""
        current = SchemaVersion(1, 2, 3)
        changes = (
            SchemaChange(ChangeType.FIELD_REMOVED, "e1", "f1"),
        )
        suggested = service.suggest_version_bump(current, changes)
        assert suggested == SchemaVersion(2, 0, 0)

    def test_suggest_minor_bump_for_structural(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should suggest minor bump for non-breaking structural changes."""
        current = SchemaVersion(1, 2, 3)
        changes = (
            SchemaChange(ChangeType.FIELD_ADDED, "e1", "f1"),
        )
        suggested = service.suggest_version_bump(current, changes)
        assert suggested == SchemaVersion(1, 3, 0)

    def test_suggest_patch_bump_for_non_structural(
        self,
        service: SchemaComparisonService,
    ) -> None:
        """Should suggest patch bump for non-structural changes."""
        current = SchemaVersion(1, 2, 3)
        changes = (
            SchemaChange(ChangeType.CONSTRAINT_MODIFIED, "e1", "f1", constraint_type="MinLength"),
        )
        suggested = service.suggest_version_bump(current, changes)
        assert suggested == SchemaVersion(1, 2, 4)

    # =========================================================================
    # Version Metadata Tests
    # =========================================================================

    def test_includes_version_in_result(
        self,
        service: SchemaComparisonService,
        simple_entity: EntityDefinition,
    ) -> None:
        """Should include versions in comparison result."""
        source_version = SchemaVersion(1, 0, 0)
        target_version = SchemaVersion(1, 1, 0)

        result = service.compare(
            (simple_entity,),
            (simple_entity,),
            source_version=source_version,
            target_version=target_version,
        )

        assert result.source_version == source_version
        assert result.target_version == target_version
