"""Entity definition for schema.

EntityDefinition is an aggregate root that defines an entity's structure.
"""

from dataclasses import dataclass, field
from typing import Optional

from doc_helper.domain.common.entity import AggregateRoot
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId


@dataclass(kw_only=True)
class EntityDefinition(AggregateRoot[EntityDefinitionId]):
    """Definition of an entity (e.g., Project, Borehole, Lab Test).

    EntityDefinition is an aggregate root that:
    - Defines entity structure (fields)
    - Enforces field uniqueness
    - Controls access to field definitions
    - Validates field references

    RULES (ADR-008):
    - EntityDefinition is an aggregate root
    - Access fields only through EntityDefinition
    - Field IDs must be unique within entity
    - Cannot modify fields after creation (immutable structure)

    Example:
        entity = EntityDefinition(
            id=EntityDefinitionId("project"),
            name_key=TranslationKey("entity.project"),
            description_key=TranslationKey("entity.project.description"),
            fields={
                FieldDefinitionId("site_location"): FieldDefinition(...),
                FieldDefinitionId("project_date"): FieldDefinition(...),
                FieldDefinitionId("soil_type"): FieldDefinition(...),
            },
        )

        # Access field by ID
        field = entity.get_field(FieldDefinitionId("site_location"))

        # Check if field exists
        has_field = entity.has_field(FieldDefinitionId("soil_type"))

        # Get all fields
        all_fields = entity.get_all_fields()
    """

    name_key: TranslationKey
    description_key: Optional[TranslationKey] = None
    fields: dict = field(default_factory=dict)  # Dict[FieldDefinitionId, FieldDefinition]
    is_root_entity: bool = False  # True for top-level entities (e.g., Project)
    parent_entity_id: Optional[EntityDefinitionId] = None  # For child entities

    def __post_init__(self) -> None:
        """Validate entity definition."""
        # Validate fields is a dict
        if not isinstance(self.fields, dict):
            raise ValueError("fields must be a dict")

        # Validate all keys are FieldDefinitionId and values are FieldDefinition
        for field_id, field_def in self.fields.items():
            if not isinstance(field_id, FieldDefinitionId):
                raise ValueError(f"All field keys must be FieldDefinitionId, got {type(field_id)}")
            if not isinstance(field_def, FieldDefinition):
                raise ValueError(f"All field values must be FieldDefinition, got {type(field_def)}")
            # Ensure field_def.id matches the key
            if field_def.id != field_id:
                raise ValueError(
                    f"Field definition ID mismatch: key={field_id}, field.id={field_def.id}"
                )

    def get_field(self, field_id: FieldDefinitionId) -> Optional[FieldDefinition]:
        """Get field definition by ID.

        Args:
            field_id: Field definition ID

        Returns:
            FieldDefinition if found, None otherwise
        """
        return self.fields.get(field_id)

    def has_field(self, field_id: FieldDefinitionId) -> bool:
        """Check if entity has a field.

        Args:
            field_id: Field definition ID

        Returns:
            True if field exists
        """
        return field_id in self.fields

    def get_all_fields(self) -> tuple:
        """Get all field definitions.

        Returns:
            Tuple of FieldDefinition objects
        """
        return tuple(self.fields.values())

    def get_required_fields(self) -> tuple:
        """Get all required field definitions.

        Returns:
            Tuple of required FieldDefinition objects
        """
        return tuple(field_def for field_def in self.fields.values() if field_def.is_required)

    def get_calculated_fields(self) -> tuple:
        """Get all calculated field definitions.

        Returns:
            Tuple of calculated FieldDefinition objects
        """
        return tuple(field_def for field_def in self.fields.values() if field_def.is_calculated)

    def get_table_fields(self) -> tuple:
        """Get all table (child entity) field definitions.

        Returns:
            Tuple of table FieldDefinition objects
        """
        return tuple(field_def for field_def in self.fields.values() if field_def.is_collection_field)

    @property
    def field_count(self) -> int:
        """Get number of fields in this entity.

        Returns:
            Count of fields
        """
        return len(self.fields)

    @property
    def is_child_entity(self) -> bool:
        """Check if this is a child entity (has parent).

        Returns:
            True if entity has a parent
        """
        return self.parent_entity_id is not None

    def validate_field_reference(self, field_id: FieldDefinitionId) -> None:
        """Validate that a field ID exists in this entity.

        Args:
            field_id: Field definition ID to validate

        Raises:
            ValueError: If field does not exist
        """
        if not self.has_field(field_id):
            raise ValueError(
                f"Field '{field_id}' does not exist in entity '{self.id}'. "
                f"Available fields: {list(self.fields.keys())}"
            )

    # =========================================================================
    # AGGREGATE MUTATION METHODS (Phase H-1: Aggregate Boundary Hardening)
    # =========================================================================
    # These methods are the ONLY authorized way to mutate the fields collection.
    # External code MUST use these methods instead of directly accessing fields.
    # =========================================================================

    def add_field(self, field: FieldDefinition) -> None:
        """Add a field to this entity.

        This is the ONLY authorized way to add fields to the entity.
        The field's ID is used as the key in the fields collection.

        Args:
            field: The field definition to add
        """
        self.fields[field.id] = field

    def update_field(self, field_id: FieldDefinitionId, field: FieldDefinition) -> None:
        """Update an existing field in this entity.

        This is the ONLY authorized way to update fields in the entity.

        Args:
            field_id: The ID of the field to update
            field: The new field definition (replaces existing)
        """
        self.fields[field_id] = field

    def remove_field(self, field_id: FieldDefinitionId) -> None:
        """Remove a field from this entity.

        This is the ONLY authorized way to remove fields from the entity.

        Args:
            field_id: The ID of the field to remove
        """
        del self.fields[field_id]
