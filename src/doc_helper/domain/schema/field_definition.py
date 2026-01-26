"""Field definition for schema.

FieldDefinition describes a single field's metadata, type, and validation rules.
"""

from dataclasses import dataclass
from typing import Optional

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.value_object import ValueObject
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import FieldDefinitionId
from doc_helper.domain.validation.constraints import FieldConstraint
from doc_helper.domain.schema.output_mapping import OutputMapping


@dataclass(frozen=True)
class FieldDefinition(ValueObject):
    """Definition of a field in an entity.

    FieldDefinition is an immutable value object that describes:
    - Field identity and type
    - Display metadata (label, help text)
    - Validation constraints
    - Options for choice fields (dropdown, radio)
    - Formula for calculated fields

    RULES (IMPLEMENTATION_RULES.md Section 3.3):
    - FieldDefinition is immutable (frozen dataclass)
    - Constraints stored as tuple (immutable)
    - Options stored as tuple (immutable)
    - NO behavior logic (pure data)

    Example:
        # Text field with constraints
        field = FieldDefinition(
            id=FieldDefinitionId("site_location"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.site_location"),
            required=True,
            constraints=(
                RequiredConstraint(),
                MinLengthConstraint(min_length=5),
                MaxLengthConstraint(max_length=100),
            ),
        )

        # Dropdown field with options
        field = FieldDefinition(
            id=FieldDefinitionId("soil_type"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.soil_type"),
            required=True,
            options=(
                ("clay", TranslationKey("soil_type.clay")),
                ("sand", TranslationKey("soil_type.sand")),
                ("silt", TranslationKey("soil_type.silt")),
            ),
        )

        # Calculated field with formula
        field = FieldDefinition(
            id=FieldDefinitionId("total_depth"),
            field_type=FieldType.CALCULATED,
            label_key=TranslationKey("field.total_depth"),
            formula="depth_from + depth_to",
        )
    """

    id: FieldDefinitionId
    field_type: FieldType
    label_key: TranslationKey
    required: bool = False
    help_text_key: Optional[TranslationKey] = None
    default_value: Optional[any] = None
    constraints: tuple = ()  # Tuple of FieldConstraint
    options: tuple = ()  # Tuple of (value, label_key) for choice fields
    formula: Optional[str] = None  # Formula expression for calculated fields
    lookup_entity_id: Optional[str] = None  # Entity ID for lookup fields
    lookup_display_field: Optional[str] = None  # Field to display for lookups
    child_entity_id: Optional[str] = None  # Entity ID for table fields
    control_rules: tuple = ()  # Tuple of ControlRule that target this field
    output_mappings: tuple = ()  # Tuple of OutputMapping for document output (Phase F-12.5)

    def __post_init__(self) -> None:
        """Validate field definition."""
        # Validate constraints are FieldConstraint instances
        if not isinstance(self.constraints, tuple):
            raise ValueError("constraints must be a tuple (immutable)")
        for constraint in self.constraints:
            if not isinstance(constraint, FieldConstraint):
                raise ValueError(f"All constraints must be FieldConstraint, got {type(constraint)}")

        # Validate options are tuples
        if not isinstance(self.options, tuple):
            raise ValueError("options must be a tuple (immutable)")
        if self.options:
            for option in self.options:
                if not isinstance(option, tuple) or len(option) != 2:
                    raise ValueError("Each option must be a tuple of (value, label_key)")

        # Validate field-type-specific requirements
        # Note: Choice fields (DROPDOWN, RADIO) are allowed to have empty options
        # at creation time. Options can be added later via the workflow.
        # Validation for non-empty options happens at runtime/export time.

        # Note: CALCULATED fields are allowed to have formula=None at creation time.
        # Formula can be added later via the workflow.
        # Validation for non-empty formula happens at runtime/export time.

        # =====================================================================
        # CALCULATED FIELD INVARIANT: CALCULATED fields are NEVER required.
        # They derive their values from formulas, not user input.
        # Force required=False regardless of what was passed.
        # =====================================================================
        if self.field_type == FieldType.CALCULATED:
            object.__setattr__(self, 'required', False)

        if self.field_type == FieldType.LOOKUP:
            if not self.lookup_entity_id:
                raise ValueError("LOOKUP field must have lookup_entity_id")

        if self.field_type == FieldType.TABLE:
            if not self.child_entity_id:
                raise ValueError("TABLE field must have child_entity_id")

    @property
    def is_required(self) -> bool:
        """Check if field is required.

        Returns:
            True if field is required
        """
        return self.required

    @property
    def is_calculated(self) -> bool:
        """Check if field is calculated (read-only).

        Returns:
            True if field is calculated
        """
        return self.field_type == FieldType.CALCULATED

    @property
    def is_choice_field(self) -> bool:
        """Check if field requires options (dropdown, radio).

        Returns:
            True if field is a choice field
        """
        return self.field_type.is_choice

    @property
    def is_collection_field(self) -> bool:
        """Check if field stores multiple values (table).

        Returns:
            True if field is a collection
        """
        return self.field_type.is_collection

    def get_option_values(self) -> tuple:
        """Get list of valid option values.

        Returns:
            Tuple of option values (for choice fields)
        """
        return tuple(value for value, _ in self.options)

    def get_option_label_key(self, value: str) -> Optional[TranslationKey]:
        """Get translation key for an option value.

        Args:
            value: Option value

        Returns:
            TranslationKey for the option label, or None if not found
        """
        for opt_value, label_key in self.options:
            if opt_value == value:
                return label_key
        return None
