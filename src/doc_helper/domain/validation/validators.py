"""Field validators for different field types.

Validators apply constraints to field values and produce ValidationResults.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Optional
import re

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.validation.constraints import (
    AllowedValuesConstraint,
    FieldConstraint,
    FileExtensionConstraint,
    MaxFileSizeConstraint,
    MaxLengthConstraint,
    MaxValueConstraint,
    MinLengthConstraint,
    MinValueConstraint,
    PatternConstraint,
    RequiredConstraint,
)
from doc_helper.domain.validation.validation_result import (
    ValidationError,
    ValidationResult,
)


class IValidator(ABC):
    """Interface for field validators.

    Validators apply constraints to field values and return validation results.

    RULES (IMPLEMENTATION_RULES.md Section 3):
    - Validators are stateless (no instance state beyond constraints)
    - Validators are pure functions (no side effects)
    - Return ValidationResult (never raise exceptions for business logic)

    Usage:
        validator = TextValidator(constraints=(
            RequiredConstraint(),
            MinLengthConstraint(min_length=3),
        ))
        result = validator.validate(field_path="name", value="John")
    """

    def __init__(self, constraints: tuple = ()):
        """Initialize validator with constraints.

        Args:
            constraints: Tuple of FieldConstraint objects
        """
        if not isinstance(constraints, tuple):
            raise ValueError("constraints must be a tuple (immutable)")
        self.constraints = constraints

    @abstractmethod
    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate a field value against constraints.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate

        Returns:
            ValidationResult with any errors found
        """
        pass

    def _check_required(self, field_path: str, value: Any) -> Optional[ValidationError]:
        """Check RequiredConstraint if present.

        Args:
            field_path: Dot-notation path to field
            value: The value to check

        Returns:
            ValidationError if required and empty, None otherwise
        """
        for constraint in self.constraints:
            if isinstance(constraint, RequiredConstraint):
                if value is None or value == "" or value == []:
                    return ValidationError(
                        field_path=field_path,
                        message_key=TranslationKey("validation.required"),
                        constraint_type="RequiredConstraint",
                        current_value=value,
                    )
        return None


class TextValidator(IValidator):
    """Validator for TEXT field type.

    Applies constraints: Required, MinLength, MaxLength, Pattern

    Example:
        validator = TextValidator(constraints=(
            RequiredConstraint(),
            MinLengthConstraint(min_length=3),
            MaxLengthConstraint(max_length=50),
            PatternConstraint(pattern=r"^[A-Za-z ]+$"),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate text value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate

        Returns:
            ValidationResult with any errors
        """
        errors = []

        # Check required
        required_error = self._check_required(field_path, value)
        if required_error:
            errors.append(required_error)
            return ValidationResult.failure(tuple(errors))

        # Skip other checks if value is empty and not required
        if value is None or value == "":
            return ValidationResult.success()

        # Ensure value is string
        if not isinstance(value, str):
            errors.append(
                ValidationError(
                    field_path=field_path,
                    message_key=TranslationKey("validation.invalid_format"),
                    constraint_type="TypeCheck",
                    current_value=value,
                )
            )
            return ValidationResult.failure(tuple(errors))

        # Check MinLength
        for constraint in self.constraints:
            if isinstance(constraint, MinLengthConstraint):
                if len(value) < constraint.min_length:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.min_length"),
                            constraint_type="MinLengthConstraint",
                            current_value=value,
                            constraint_params={"min": constraint.min_length},
                        )
                    )

        # Check MaxLength
        for constraint in self.constraints:
            if isinstance(constraint, MaxLengthConstraint):
                if len(value) > constraint.max_length:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.max_length"),
                            constraint_type="MaxLengthConstraint",
                            current_value=value,
                            constraint_params={"max": constraint.max_length},
                        )
                    )

        # Check Pattern
        for constraint in self.constraints:
            if isinstance(constraint, PatternConstraint):
                if not re.match(constraint.pattern, value):
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.pattern"),
                            constraint_type="PatternConstraint",
                            current_value=value,
                        )
                    )

        if errors:
            return ValidationResult.failure(tuple(errors))
        return ValidationResult.success()


class NumberValidator(IValidator):
    """Validator for NUMBER field type.

    Applies constraints: Required, MinValue, MaxValue

    Example:
        validator = NumberValidator(constraints=(
            RequiredConstraint(),
            MinValueConstraint(min_value=0),
            MaxValueConstraint(max_value=100),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate number value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate

        Returns:
            ValidationResult with any errors
        """
        errors = []

        # Check required
        required_error = self._check_required(field_path, value)
        if required_error:
            errors.append(required_error)
            return ValidationResult.failure(tuple(errors))

        # Skip other checks if value is empty and not required
        if value is None:
            return ValidationResult.success()

        # Ensure value is numeric
        if not isinstance(value, (int, float)):
            errors.append(
                ValidationError(
                    field_path=field_path,
                    message_key=TranslationKey("validation.invalid_number"),
                    constraint_type="TypeCheck",
                    current_value=value,
                )
            )
            return ValidationResult.failure(tuple(errors))

        # Check MinValue
        for constraint in self.constraints:
            if isinstance(constraint, MinValueConstraint):
                if value < constraint.min_value:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.min_value"),
                            constraint_type="MinValueConstraint",
                            current_value=value,
                            constraint_params={"min": constraint.min_value},
                        )
                    )

        # Check MaxValue
        for constraint in self.constraints:
            if isinstance(constraint, MaxValueConstraint):
                if value > constraint.max_value:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.max_value"),
                            constraint_type="MaxValueConstraint",
                            current_value=value,
                            constraint_params={"max": constraint.max_value},
                        )
                    )

        if errors:
            return ValidationResult.failure(tuple(errors))
        return ValidationResult.success()


class DateValidator(IValidator):
    """Validator for DATE field type.

    Applies constraints: Required, MinValue, MaxValue (as dates)

    Example:
        validator = DateValidator(constraints=(
            RequiredConstraint(),
            MinValueConstraint(min_value=date(2020, 1, 1).toordinal()),
            MaxValueConstraint(max_value=date(2030, 12, 31).toordinal()),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate date value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate (date or datetime object)

        Returns:
            ValidationResult with any errors
        """
        errors = []

        # Check required
        required_error = self._check_required(field_path, value)
        if required_error:
            errors.append(required_error)
            return ValidationResult.failure(tuple(errors))

        # Skip other checks if value is empty and not required
        if value is None:
            return ValidationResult.success()

        # Ensure value is date or datetime
        if not isinstance(value, (date, datetime)):
            errors.append(
                ValidationError(
                    field_path=field_path,
                    message_key=TranslationKey("validation.invalid_date"),
                    constraint_type="TypeCheck",
                    current_value=value,
                )
            )
            return ValidationResult.failure(tuple(errors))

        # Convert datetime to date for comparison
        date_value = value.date() if isinstance(value, datetime) else value
        ordinal_value = date_value.toordinal()

        # Check MinValue
        for constraint in self.constraints:
            if isinstance(constraint, MinValueConstraint):
                if ordinal_value < constraint.min_value:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.min_value"),
                            constraint_type="MinValueConstraint",
                            current_value=value,
                            constraint_params={"min": date.fromordinal(int(constraint.min_value)).isoformat()},
                        )
                    )

        # Check MaxValue
        for constraint in self.constraints:
            if isinstance(constraint, MaxValueConstraint):
                if ordinal_value > constraint.max_value:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.max_value"),
                            constraint_type="MaxValueConstraint",
                            current_value=value,
                            constraint_params={"max": date.fromordinal(int(constraint.max_value)).isoformat()},
                        )
                    )

        if errors:
            return ValidationResult.failure(tuple(errors))
        return ValidationResult.success()


class DropdownValidator(IValidator):
    """Validator for DROPDOWN field type.

    Applies constraints: Required, AllowedValues

    Example:
        validator = DropdownValidator(constraints=(
            RequiredConstraint(),
            AllowedValuesConstraint(allowed_values=("small", "medium", "large")),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate dropdown value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate

        Returns:
            ValidationResult with any errors
        """
        errors = []

        # Check required
        required_error = self._check_required(field_path, value)
        if required_error:
            errors.append(required_error)
            return ValidationResult.failure(tuple(errors))

        # Skip other checks if value is empty and not required
        if value is None or value == "":
            return ValidationResult.success()

        # Check AllowedValues
        for constraint in self.constraints:
            if isinstance(constraint, AllowedValuesConstraint):
                if value not in constraint.allowed_values:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.invalid_option"),
                            constraint_type="AllowedValuesConstraint",
                            current_value=value,
                        )
                    )

        if errors:
            return ValidationResult.failure(tuple(errors))
        return ValidationResult.success()


class CheckboxValidator(IValidator):
    """Validator for CHECKBOX field type.

    Applies constraints: Required (checkbox must be checked)

    Example:
        validator = CheckboxValidator(constraints=(
            RequiredConstraint(),  # Checkbox must be checked
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate checkbox value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate (boolean)

        Returns:
            ValidationResult with any errors
        """
        errors = []

        # Ensure value is boolean
        if value is not None and not isinstance(value, bool):
            errors.append(
                ValidationError(
                    field_path=field_path,
                    message_key=TranslationKey("validation.invalid_format"),
                    constraint_type="TypeCheck",
                    current_value=value,
                )
            )
            return ValidationResult.failure(tuple(errors))

        # Check required (must be True if required)
        for constraint in self.constraints:
            if isinstance(constraint, RequiredConstraint):
                if not value:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.required"),
                            constraint_type="RequiredConstraint",
                            current_value=value,
                        )
                    )

        if errors:
            return ValidationResult.failure(tuple(errors))
        return ValidationResult.success()


class RadioValidator(IValidator):
    """Validator for RADIO field type.

    Applies constraints: Required, AllowedValues

    Example:
        validator = RadioValidator(constraints=(
            RequiredConstraint(),
            AllowedValuesConstraint(allowed_values=("yes", "no", "maybe")),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate radio button value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate

        Returns:
            ValidationResult with any errors
        """
        # Radio validation is identical to Dropdown
        return DropdownValidator(self.constraints).validate(field_path, value)


class CalculatedValidator(IValidator):
    """Validator for CALCULATED field type.

    Calculated fields are read-only and typically don't need validation
    beyond type checking. Constraints are minimal.

    Example:
        validator = CalculatedValidator()  # Usually no constraints
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate calculated value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate

        Returns:
            ValidationResult (usually success)
        """
        # Calculated fields are generally always valid
        # They are derived from formulas, not user input
        return ValidationResult.success()


class LookupValidator(IValidator):
    """Validator for LOOKUP field type.

    Applies constraints: Required

    Example:
        validator = LookupValidator(constraints=(
            RequiredConstraint(),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate lookup value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate

        Returns:
            ValidationResult with any errors
        """
        errors = []

        # Check required
        required_error = self._check_required(field_path, value)
        if required_error:
            errors.append(required_error)
            return ValidationResult.failure(tuple(errors))

        return ValidationResult.success()


class FileValidator(IValidator):
    """Validator for FILE field type.

    Applies constraints: Required, FileExtension, MaxFileSize

    Example:
        validator = FileValidator(constraints=(
            RequiredConstraint(),
            FileExtensionConstraint(allowed_extensions=(".pdf", ".docx")),
            MaxFileSizeConstraint(max_size_bytes=10 * 1024 * 1024),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate file reference.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate (file path string or file metadata dict)

        Returns:
            ValidationResult with any errors
        """
        errors = []

        # Check required
        required_error = self._check_required(field_path, value)
        if required_error:
            errors.append(required_error)
            return ValidationResult.failure(tuple(errors))

        # Skip other checks if value is empty and not required
        if value is None or value == "":
            return ValidationResult.success()

        # Extract filename and size if value is dict (file metadata)
        filename = value if isinstance(value, str) else value.get("filename", "")
        file_size = value.get("size", 0) if isinstance(value, dict) else None

        # Check FileExtension
        for constraint in self.constraints:
            if isinstance(constraint, FileExtensionConstraint):
                if not any(filename.lower().endswith(ext) for ext in constraint.allowed_extensions):
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.invalid_file_extension"),
                            constraint_type="FileExtensionConstraint",
                            current_value=value,
                        )
                    )

        # Check MaxFileSize
        for constraint in self.constraints:
            if isinstance(constraint, MaxFileSizeConstraint):
                if file_size and file_size > constraint.max_size_bytes:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.file_too_large"),
                            constraint_type="MaxFileSizeConstraint",
                            current_value=value,
                            constraint_params={"max": constraint.max_size_bytes},
                        )
                    )

        if errors:
            return ValidationResult.failure(tuple(errors))
        return ValidationResult.success()


class ImageValidator(IValidator):
    """Validator for IMAGE field type.

    Applies constraints: Required, FileExtension (image formats), MaxFileSize

    Example:
        validator = ImageValidator(constraints=(
            RequiredConstraint(),
            FileExtensionConstraint(allowed_extensions=(".jpg", ".png", ".gif")),
            MaxFileSizeConstraint(max_size_bytes=5 * 1024 * 1024),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate image file reference.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate (image file path or metadata)

        Returns:
            ValidationResult with any errors
        """
        # Image validation is identical to File validation
        return FileValidator(self.constraints).validate(field_path, value)


class TableValidator(IValidator):
    """Validator for TABLE field type.

    Table fields contain nested records (child entities).
    Applies constraints: Required (must have at least one row)

    Example:
        validator = TableValidator(constraints=(
            RequiredConstraint(),  # At least one row required
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate table value (list of records).

        Args:
            field_path: Dot-notation path to field
            value: The value to validate (list of records)

        Returns:
            ValidationResult with any errors
        """
        errors = []

        # Ensure value is list or None
        if value is not None and not isinstance(value, (list, tuple)):
            errors.append(
                ValidationError(
                    field_path=field_path,
                    message_key=TranslationKey("validation.invalid_format"),
                    constraint_type="TypeCheck",
                    current_value=value,
                )
            )
            return ValidationResult.failure(tuple(errors))

        # Check required (must have at least one row)
        for constraint in self.constraints:
            if isinstance(constraint, RequiredConstraint):
                if not value or len(value) == 0:
                    errors.append(
                        ValidationError(
                            field_path=field_path,
                            message_key=TranslationKey("validation.required"),
                            constraint_type="RequiredConstraint",
                            current_value=value,
                        )
                    )

        if errors:
            return ValidationResult.failure(tuple(errors))
        return ValidationResult.success()


class TextAreaValidator(IValidator):
    """Validator for TEXTAREA field type.

    Applies same constraints as TEXT: Required, MinLength, MaxLength, Pattern

    Example:
        validator = TextAreaValidator(constraints=(
            RequiredConstraint(),
            MinLengthConstraint(min_length=10),
            MaxLengthConstraint(max_length=1000),
        ))
    """

    def validate(self, field_path: str, value: Any) -> ValidationResult:
        """Validate textarea value.

        Args:
            field_path: Dot-notation path to field
            value: The value to validate

        Returns:
            ValidationResult with any errors
        """
        # TextArea validation is identical to Text validation
        return TextValidator(self.constraints).validate(field_path, value)


def get_validator_for_field_type(
    field_type: "FieldType",  # type: ignore
    constraints: tuple = (),
) -> IValidator:
    """Get appropriate validator for a field type.

    Args:
        field_type: Field type to get validator for
        constraints: Constraints to apply

    Returns:
        Validator instance for the field type

    Raises:
        ValueError: If field type is unknown
    """
    from doc_helper.domain.schema.field_type import FieldType

    # Map field types to validator classes
    validator_map = {
        FieldType.TEXT: TextValidator,
        FieldType.TEXTAREA: TextAreaValidator,
        FieldType.NUMBER: NumberValidator,
        FieldType.DATE: DateValidator,
        FieldType.DROPDOWN: DropdownValidator,
        FieldType.CHECKBOX: CheckboxValidator,
        FieldType.RADIO: RadioValidator,
        FieldType.CALCULATED: CalculatedValidator,
        FieldType.LOOKUP: LookupValidator,
        FieldType.FILE: FileValidator,
        FieldType.IMAGE: ImageValidator,
        FieldType.TABLE: TableValidator,
    }

    validator_class = validator_map.get(field_type)
    if validator_class is None:
        raise ValueError(f"Unknown field type: {field_type}")

    return validator_class(constraints)
