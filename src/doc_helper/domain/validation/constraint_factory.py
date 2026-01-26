"""Constraint Factory - Domain Layer.

Factory for creating FieldConstraint objects from raw persistence data.
This keeps domain object instantiation in the Domain layer.

ARCHITECTURE:
- Factory lives in Domain layer
- Infrastructure layer uses this factory to hydrate constraints
- Infrastructure NEVER directly instantiates constraint objects
"""

from typing import Optional

from doc_helper.domain.validation.constraints import (
    FieldConstraint,
    RequiredConstraint,
    MinLengthConstraint,
    MaxLengthConstraint,
    MinValueConstraint,
    MaxValueConstraint,
    PatternConstraint,
    AllowedValuesConstraint,
    FileExtensionConstraint,
    MaxFileSizeConstraint,
)


class ConstraintFactory:
    """Factory for creating FieldConstraint objects from raw data.

    This factory is the ONLY authorized way for infrastructure to create
    constraint objects. It ensures domain object creation stays in domain layer.

    Usage (in repository):
        factory = ConstraintFactory()
        constraint = factory.create_from_raw("REQUIRED", None)
        raw_type, raw_value = factory.serialize_to_raw(constraint)
    """

    # Rule type constants (used in persistence)
    RULE_REQUIRED = "REQUIRED"
    RULE_MIN_LENGTH = "MIN_LENGTH"
    RULE_MAX_LENGTH = "MAX_LENGTH"
    RULE_MIN_VALUE = "MIN_VALUE"
    RULE_MAX_VALUE = "MAX_VALUE"
    RULE_PATTERN = "PATTERN"
    RULE_ALLOWED_VALUES = "ALLOWED_VALUES"
    RULE_FILE_EXTENSION = "FILE_EXTENSION"
    RULE_MAX_FILE_SIZE = "MAX_FILE_SIZE"

    def create_from_raw(
        self, rule_type: str, rule_value: Optional[str]
    ) -> Optional[FieldConstraint]:
        """Create a FieldConstraint from raw persistence data.

        Args:
            rule_type: Rule type string from database
            rule_value: Rule value string from database (may be None)

        Returns:
            FieldConstraint instance or None if unknown type
        """
        if rule_type == self.RULE_REQUIRED:
            return RequiredConstraint()

        elif rule_type == self.RULE_MIN_LENGTH:
            return MinLengthConstraint(min_length=int(rule_value))

        elif rule_type == self.RULE_MAX_LENGTH:
            return MaxLengthConstraint(max_length=int(rule_value))

        elif rule_type == self.RULE_MIN_VALUE:
            return MinValueConstraint(min_value=float(rule_value))

        elif rule_type == self.RULE_MAX_VALUE:
            return MaxValueConstraint(max_value=float(rule_value))

        elif rule_type == self.RULE_PATTERN:
            return PatternConstraint(pattern=rule_value)

        elif rule_type == self.RULE_ALLOWED_VALUES:
            import json
            values = json.loads(rule_value)
            return AllowedValuesConstraint(allowed_values=tuple(values))

        elif rule_type == self.RULE_FILE_EXTENSION:
            import json
            exts = json.loads(rule_value)
            return FileExtensionConstraint(allowed_extensions=tuple(exts))

        elif rule_type == self.RULE_MAX_FILE_SIZE:
            return MaxFileSizeConstraint(max_size_bytes=int(rule_value))

        else:
            return None

    def serialize_to_raw(self, constraint: FieldConstraint) -> tuple[str, Optional[str]]:
        """Serialize a FieldConstraint to raw persistence data.

        Args:
            constraint: FieldConstraint to serialize

        Returns:
            Tuple of (rule_type, rule_value) for persistence
        """
        if isinstance(constraint, RequiredConstraint):
            return (self.RULE_REQUIRED, None)

        elif isinstance(constraint, MinLengthConstraint):
            return (self.RULE_MIN_LENGTH, str(constraint.min_length))

        elif isinstance(constraint, MaxLengthConstraint):
            return (self.RULE_MAX_LENGTH, str(constraint.max_length))

        elif isinstance(constraint, MinValueConstraint):
            return (self.RULE_MIN_VALUE, str(constraint.min_value))

        elif isinstance(constraint, MaxValueConstraint):
            return (self.RULE_MAX_VALUE, str(constraint.max_value))

        elif isinstance(constraint, PatternConstraint):
            return (self.RULE_PATTERN, constraint.pattern)

        elif isinstance(constraint, AllowedValuesConstraint):
            import json
            return (self.RULE_ALLOWED_VALUES, json.dumps(constraint.allowed_values))

        elif isinstance(constraint, FileExtensionConstraint):
            import json
            return (self.RULE_FILE_EXTENSION, json.dumps(constraint.allowed_extensions))

        elif isinstance(constraint, MaxFileSizeConstraint):
            return (self.RULE_MAX_FILE_SIZE, str(constraint.max_size_bytes))

        else:
            return ("UNKNOWN", None)
