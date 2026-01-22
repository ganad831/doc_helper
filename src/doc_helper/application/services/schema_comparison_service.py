"""Schema Comparison Service (Phase 3).

Service for comparing schema versions and determining compatibility.

APPROVED DECISIONS:
- Decision 2: No rename detection (rename = delete + add)
- Decision 3: Moderate breaking-change policy
- Decision 6: Three-level compatibility (IDENTICAL / COMPATIBLE / INCOMPATIBLE)
- Decision 7: Structural comparison only

IMPORTANT: Compatibility is informational only and MUST NOT block operations.
"""

from typing import Optional

from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.schema_change import ChangeType, SchemaChange
from doc_helper.domain.schema.schema_compatibility import (
    CompatibilityLevel,
    CompatibilityResult,
)
from doc_helper.domain.schema.schema_version import SchemaVersion


class SchemaComparisonService:
    """Service for comparing schema versions.

    Provides:
    - Change detection between schema versions
    - Compatibility level classification
    - Diff generation

    Usage:
        service = SchemaComparisonService()
        result = service.compare(source_entities, target_entities)
        if result.is_incompatible:
            print(f"Breaking changes: {result.breaking_change_count}")

    IMPORTANT: Results are informational only. Do not use to block operations.
    """

    def compare(
        self,
        source_entities: tuple,
        target_entities: tuple,
        source_version: Optional[SchemaVersion] = None,
        target_version: Optional[SchemaVersion] = None,
    ) -> CompatibilityResult:
        """Compare two schema states and determine compatibility.

        Args:
            source_entities: Tuple of EntityDefinition from source schema
            target_entities: Tuple of EntityDefinition from target schema
            source_version: Optional version of source schema
            target_version: Optional version of target schema

        Returns:
            CompatibilityResult with level and list of changes
        """
        changes: list[SchemaChange] = []

        # Build lookup maps by entity ID
        source_map = {e.id.value: e for e in source_entities}
        target_map = {e.id.value: e for e in target_entities}

        # Detect entity-level changes
        entity_changes = self._compare_entities(source_map, target_map)
        changes.extend(entity_changes)

        # Detect field-level changes for entities that exist in both
        common_entity_ids = set(source_map.keys()) & set(target_map.keys())
        for entity_id in common_entity_ids:
            source_entity = source_map[entity_id]
            target_entity = target_map[entity_id]
            field_changes = self._compare_fields(entity_id, source_entity, target_entity)
            changes.extend(field_changes)

        # Determine compatibility level
        level = self._determine_level(changes)

        return CompatibilityResult(
            level=level,
            changes=tuple(changes),
            source_version=source_version,
            target_version=target_version,
        )

    def _compare_entities(
        self,
        source_map: dict,
        target_map: dict,
    ) -> list[SchemaChange]:
        """Compare entity presence between schemas.

        Args:
            source_map: Dict of entity_id -> EntityDefinition for source
            target_map: Dict of entity_id -> EntityDefinition for target

        Returns:
            List of entity-level changes
        """
        changes: list[SchemaChange] = []

        source_ids = set(source_map.keys())
        target_ids = set(target_map.keys())

        # Entities added (in target but not in source)
        for entity_id in target_ids - source_ids:
            changes.append(SchemaChange(
                change_type=ChangeType.ENTITY_ADDED,
                entity_id=entity_id,
            ))

        # Entities removed (in source but not in target)
        for entity_id in source_ids - target_ids:
            changes.append(SchemaChange(
                change_type=ChangeType.ENTITY_REMOVED,
                entity_id=entity_id,
            ))

        return changes

    def _compare_fields(
        self,
        entity_id: str,
        source_entity: EntityDefinition,
        target_entity: EntityDefinition,
    ) -> list[SchemaChange]:
        """Compare fields between two versions of an entity.

        Args:
            entity_id: Entity ID being compared
            source_entity: Source entity definition
            target_entity: Target entity definition

        Returns:
            List of field-level changes
        """
        changes: list[SchemaChange] = []

        # Build field maps
        source_fields = {f.id.value: f for f in source_entity.get_all_fields()}
        target_fields = {f.id.value: f for f in target_entity.get_all_fields()}

        source_field_ids = set(source_fields.keys())
        target_field_ids = set(target_fields.keys())

        # Fields added
        for field_id in target_field_ids - source_field_ids:
            changes.append(SchemaChange(
                change_type=ChangeType.FIELD_ADDED,
                entity_id=entity_id,
                field_id=field_id,
            ))

        # Fields removed
        for field_id in source_field_ids - target_field_ids:
            changes.append(SchemaChange(
                change_type=ChangeType.FIELD_REMOVED,
                entity_id=entity_id,
                field_id=field_id,
            ))

        # Fields modified (present in both)
        for field_id in source_field_ids & target_field_ids:
            source_field = source_fields[field_id]
            target_field = target_fields[field_id]
            field_changes = self._compare_field_details(
                entity_id, field_id, source_field, target_field
            )
            changes.extend(field_changes)

        return changes

    def _compare_field_details(
        self,
        entity_id: str,
        field_id: str,
        source_field: FieldDefinition,
        target_field: FieldDefinition,
    ) -> list[SchemaChange]:
        """Compare details of a single field between versions.

        Structural comparison only (Decision 7):
        - Field type
        - Required flag
        - Constraints
        - Options (for choice fields)

        Excludes:
        - Translation keys
        - Help text keys
        - Description keys
        - Default values

        Args:
            entity_id: Parent entity ID
            field_id: Field ID
            source_field: Source field definition
            target_field: Target field definition

        Returns:
            List of changes for this field
        """
        changes: list[SchemaChange] = []

        # Field type changed (BREAKING)
        if source_field.field_type != target_field.field_type:
            changes.append(SchemaChange(
                change_type=ChangeType.FIELD_TYPE_CHANGED,
                entity_id=entity_id,
                field_id=field_id,
                old_value=source_field.field_type.value,
                new_value=target_field.field_type.value,
            ))

        # Required changed (non-breaking)
        if source_field.required != target_field.required:
            changes.append(SchemaChange(
                change_type=ChangeType.FIELD_REQUIRED_CHANGED,
                entity_id=entity_id,
                field_id=field_id,
                old_value=str(source_field.required),
                new_value=str(target_field.required),
            ))

        # Compare constraints
        constraint_changes = self._compare_constraints(
            entity_id, field_id, source_field, target_field
        )
        changes.extend(constraint_changes)

        # Compare options for choice fields
        if source_field.is_choice_field or target_field.is_choice_field:
            option_changes = self._compare_options(
                entity_id, field_id, source_field, target_field
            )
            changes.extend(option_changes)

        return changes

    def _compare_constraints(
        self,
        entity_id: str,
        field_id: str,
        source_field: FieldDefinition,
        target_field: FieldDefinition,
    ) -> list[SchemaChange]:
        """Compare constraints between field versions.

        Args:
            entity_id: Parent entity ID
            field_id: Field ID
            source_field: Source field definition
            target_field: Target field definition

        Returns:
            List of constraint changes
        """
        changes: list[SchemaChange] = []

        # Build constraint type maps
        source_constraints = {type(c).__name__: c for c in source_field.constraints}
        target_constraints = {type(c).__name__: c for c in target_field.constraints}

        source_types = set(source_constraints.keys())
        target_types = set(target_constraints.keys())

        # Constraints added
        for constraint_type in target_types - source_types:
            changes.append(SchemaChange(
                change_type=ChangeType.CONSTRAINT_ADDED,
                entity_id=entity_id,
                field_id=field_id,
                constraint_type=constraint_type,
            ))

        # Constraints removed
        for constraint_type in source_types - target_types:
            changes.append(SchemaChange(
                change_type=ChangeType.CONSTRAINT_REMOVED,
                entity_id=entity_id,
                field_id=field_id,
                constraint_type=constraint_type,
            ))

        # Constraints modified (same type, different parameters)
        for constraint_type in source_types & target_types:
            source_c = source_constraints[constraint_type]
            target_c = target_constraints[constraint_type]
            if source_c != target_c:
                changes.append(SchemaChange(
                    change_type=ChangeType.CONSTRAINT_MODIFIED,
                    entity_id=entity_id,
                    field_id=field_id,
                    constraint_type=constraint_type,
                ))

        return changes

    def _compare_options(
        self,
        entity_id: str,
        field_id: str,
        source_field: FieldDefinition,
        target_field: FieldDefinition,
    ) -> list[SchemaChange]:
        """Compare options for choice fields.

        Args:
            entity_id: Parent entity ID
            field_id: Field ID
            source_field: Source field definition
            target_field: Target field definition

        Returns:
            List of option changes
        """
        changes: list[SchemaChange] = []

        # Extract option values (ignore label keys per Decision 7)
        source_options = {opt[0] for opt in source_field.options} if source_field.options else set()
        target_options = {opt[0] for opt in target_field.options} if target_field.options else set()

        # Options added (non-breaking)
        for option_value in target_options - source_options:
            changes.append(SchemaChange(
                change_type=ChangeType.OPTION_ADDED,
                entity_id=entity_id,
                field_id=field_id,
                option_value=str(option_value),
            ))

        # Options removed (BREAKING)
        for option_value in source_options - target_options:
            changes.append(SchemaChange(
                change_type=ChangeType.OPTION_REMOVED,
                entity_id=entity_id,
                field_id=field_id,
                option_value=str(option_value),
            ))

        return changes

    def _determine_level(self, changes: list[SchemaChange]) -> CompatibilityLevel:
        """Determine compatibility level from changes.

        Decision 6: Three-level classification
        - IDENTICAL: No changes
        - COMPATIBLE: Non-breaking changes only
        - INCOMPATIBLE: At least one breaking change

        Args:
            changes: List of detected changes

        Returns:
            CompatibilityLevel
        """
        if not changes:
            return CompatibilityLevel.IDENTICAL

        has_breaking = any(c.is_breaking for c in changes)
        if has_breaking:
            return CompatibilityLevel.INCOMPATIBLE

        return CompatibilityLevel.COMPATIBLE

    def suggest_version_bump(
        self,
        current_version: SchemaVersion,
        changes: tuple,
    ) -> SchemaVersion:
        """Suggest next version based on changes.

        - MAJOR bump: Breaking changes present
        - MINOR bump: Non-breaking structural changes
        - PATCH bump: No structural changes (metadata only)

        Args:
            current_version: Current schema version
            changes: Tuple of SchemaChange from comparison

        Returns:
            Suggested new SchemaVersion
        """
        if not changes:
            return current_version

        # Check for breaking changes
        has_breaking = any(c.is_breaking for c in changes)
        if has_breaking:
            return current_version.bump_major()

        # Check for structural changes
        has_structural = any(c.change_type.is_structural for c in changes)
        if has_structural:
            return current_version.bump_minor()

        # Metadata-only changes
        return current_version.bump_patch()
