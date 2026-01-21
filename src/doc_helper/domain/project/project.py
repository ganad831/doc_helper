"""Project aggregate root."""

from dataclasses import dataclass, field
from typing import Optional

from doc_helper.domain.common.entity import AggregateRoot
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.project.field_history import ChangeSource
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project_events import FieldValueChanged
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId


@dataclass(kw_only=True)
class Project(AggregateRoot[ProjectId]):
    """Project aggregate root representing a document generation project.

    Project is the main aggregate root for the application. It:
    - Manages field values for all entities
    - Tracks project metadata (name, description, file path)
    - Controls access to field values
    - Validates field changes

    RULES (v1 scope):
    - Project is an aggregate root
    - Field values accessed only through Project
    - Project manages consistency of field values
    - NO field history (v2+)
    - NO auto-save (v2+)
    - NO document versioning (v2+)

    Example:
        from uuid import uuid4

        project = Project(
            id=ProjectId(uuid4()),
            name="Downtown Soil Investigation",
            entity_definition_id=EntityDefinitionId("project"),
            field_values={
                FieldDefinitionId("site_location"): FieldValue(...),
                FieldDefinitionId("project_date"): FieldValue(...),
            }
        )

        # Get field value
        location = project.get_field_value(FieldDefinitionId("site_location"))

        # Set field value
        project.set_field_value(
            FieldDefinitionId("site_location"),
            "456 Oak Avenue"
        )

        # Check if field has value
        has_date = project.has_field_value(FieldDefinitionId("project_date"))
    """

    name: str  # Project name (user-visible)
    entity_definition_id: EntityDefinitionId  # Schema definition for this project
    field_values: dict = field(
        default_factory=dict
    )  # Dict[FieldDefinitionId, FieldValue]
    description: Optional[str] = None  # Optional project description
    file_path: Optional[str] = None  # File path where project is saved (if any)

    def __post_init__(self) -> None:
        """Validate project."""
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if not isinstance(self.entity_definition_id, EntityDefinitionId):
            raise TypeError("entity_definition_id must be an EntityDefinitionId")
        if not isinstance(self.field_values, dict):
            raise TypeError("field_values must be a dict")

        # Validate all keys are FieldDefinitionId and values are FieldValue
        for field_id, field_value in self.field_values.items():
            if not isinstance(field_id, FieldDefinitionId):
                raise TypeError(
                    f"All field_values keys must be FieldDefinitionId, got {type(field_id)}"
                )
            if not isinstance(field_value, FieldValue):
                raise TypeError(
                    f"All field_values values must be FieldValue, got {type(field_value)}"
                )
            # Ensure field_value.field_id matches the key
            if field_value.field_id != field_id:
                raise ValueError(
                    f"FieldValue field_id mismatch: key={field_id}, value.field_id={field_value.field_id}"
                )

        if self.description is not None and not isinstance(self.description, str):
            raise TypeError("description must be a string or None")

        if self.file_path is not None and not isinstance(self.file_path, str):
            raise TypeError("file_path must be a string or None")

    def get_field_value(self, field_id: FieldDefinitionId) -> Optional[FieldValue]:
        """Get field value by ID.

        Args:
            field_id: Field definition ID

        Returns:
            FieldValue if found, None otherwise
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")
        return self.field_values.get(field_id)

    def has_field_value(self, field_id: FieldDefinitionId) -> bool:
        """Check if field has a value.

        Args:
            field_id: Field definition ID

        Returns:
            True if field has a value
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")
        return field_id in self.field_values

    def set_field_value(
        self, field_id: FieldDefinitionId, value: any, user_id: Optional[str] = None
    ) -> None:
        """Set field value (user-provided).

        If the field already has a computed value, this creates an override.

        ADR-027: Emits FieldValueChanged event for field history tracking.

        Args:
            field_id: Field definition ID
            value: Value to set
            user_id: Optional user ID who made the change
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")

        existing = self.field_values.get(field_id)
        previous_value = existing.value if existing is not None else None

        if existing is not None:
            # Update existing field value
            new_field_value = existing.with_value(value)
        else:
            # Create new field value
            new_field_value = FieldValue(
                field_id=field_id, value=value, is_computed=False
            )

        self.field_values[field_id] = new_field_value
        self._touch()

        # ADR-027: Emit domain event for field history
        # Only emit if value actually changed
        if previous_value != value:
            self._add_domain_event(
                FieldValueChanged(
                    project_id=self.id,
                    field_id=field_id,
                    previous_value=previous_value,
                    new_value=value,
                    change_source=ChangeSource.USER_EDIT,
                    user_id=user_id,
                )
            )

    def set_computed_field_value(
        self, field_id: FieldDefinitionId, computed_value: any, formula: str
    ) -> None:
        """Set field value from formula computation.

        If the field has an override, the override is preserved and only
        the original_computed_value is updated.

        ADR-027: Emits FieldValueChanged event for field history tracking.

        Args:
            field_id: Field definition ID
            computed_value: Computed value from formula
            formula: Formula that computed the value
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")
        if not isinstance(formula, str):
            raise TypeError("formula must be a string")

        existing = self.field_values.get(field_id)
        # For computed values, track the actual displayed value (including overrides)
        previous_value = existing.value if existing is not None else None

        if existing is not None:
            # Update existing field value
            new_field_value = existing.with_computed_value(computed_value, formula)
        else:
            # Create new computed field value
            new_field_value = FieldValue(
                field_id=field_id,
                value=computed_value,
                is_computed=True,
                computed_from=formula,
            )

        self.field_values[field_id] = new_field_value
        self._touch()

        # ADR-027: Emit domain event for field history
        # Only emit if computed value actually changed
        # Note: If field has override, the displayed value doesn't change, only the underlying computed value
        new_displayed_value = new_field_value.value
        if previous_value != new_displayed_value:
            self._add_domain_event(
                FieldValueChanged(
                    project_id=self.id,
                    field_id=field_id,
                    previous_value=previous_value,
                    new_value=new_displayed_value,
                    change_source=ChangeSource.FORMULA_RECOMPUTATION,
                    user_id=None,  # System-initiated change
                )
            )

    def clear_field_override(
        self, field_id: FieldDefinitionId, user_id: Optional[str] = None
    ) -> None:
        """Clear override for a field, restoring computed value.

        ADR-027: Emits FieldValueChanged event for field history tracking.

        Args:
            field_id: Field definition ID
            user_id: Optional user ID who cleared the override

        Raises:
            KeyError: If field not found
            ValueError: If field is not an override
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")

        if field_id not in self.field_values:
            raise KeyError(f"Field '{field_id.value}' not found in project")

        existing = self.field_values[field_id]
        previous_value = existing.value

        new_field_value = existing.clear_override()
        self.field_values[field_id] = new_field_value
        self._touch()

        # ADR-027: Emit domain event for field history
        # Clearing override restores the computed value
        new_value = new_field_value.value
        if previous_value != new_value:
            self._add_domain_event(
                FieldValueChanged(
                    project_id=self.id,
                    field_id=field_id,
                    previous_value=previous_value,
                    new_value=new_value,
                    change_source=ChangeSource.USER_EDIT,
                    user_id=user_id,
                )
            )

    def remove_field_value(self, field_id: FieldDefinitionId) -> None:
        """Remove field value.

        Args:
            field_id: Field definition ID

        Raises:
            KeyError: If field not found
        """
        if not isinstance(field_id, FieldDefinitionId):
            raise TypeError("field_id must be a FieldDefinitionId")

        if field_id not in self.field_values:
            raise KeyError(f"Field '{field_id.value}' not found in project")

        del self.field_values[field_id]
        self._touch()

    def get_all_field_values(self) -> tuple:
        """Get all field values.

        Returns:
            Tuple of (field_id, field_value) pairs
        """
        return tuple(self.field_values.items())

    def get_computed_field_ids(self) -> tuple:
        """Get IDs of all computed fields.

        Returns:
            Tuple of FieldDefinitionId for computed fields
        """
        return tuple(
            field_id
            for field_id, field_value in self.field_values.items()
            if field_value.is_computed
        )

    def get_overridden_field_ids(self) -> tuple:
        """Get IDs of all overridden fields.

        Returns:
            Tuple of FieldDefinitionId for overridden fields
        """
        return tuple(
            field_id
            for field_id, field_value in self.field_values.items()
            if field_value.is_override
        )

    def rename(self, new_name: str) -> None:
        """Rename the project.

        Args:
            new_name: New project name

        Raises:
            TypeError: If new_name is not a string
            ValueError: If new_name is empty
        """
        if not isinstance(new_name, str):
            raise TypeError("new_name must be a string")
        if not new_name.strip():
            raise ValueError("new_name cannot be empty")

        self.name = new_name
        self._touch()

    def update_description(self, description: Optional[str]) -> None:
        """Update project description.

        Args:
            description: New description or None to clear

        Raises:
            TypeError: If description is not string or None
        """
        if description is not None and not isinstance(description, str):
            raise TypeError("description must be a string or None")

        self.description = description
        self._touch()

    def set_file_path(self, file_path: str) -> None:
        """Set the file path where project is saved.

        Args:
            file_path: File path

        Raises:
            TypeError: If file_path is not a string
        """
        if not isinstance(file_path, str):
            raise TypeError("file_path must be a string")

        self.file_path = file_path
        self._touch()

    @property
    def field_count(self) -> int:
        """Get count of field values.

        Returns:
            Number of field values
        """
        return len(self.field_values)

    @property
    def is_saved(self) -> bool:
        """Check if project has been saved to a file.

        Returns:
            True if project has a file path
        """
        return self.file_path is not None
