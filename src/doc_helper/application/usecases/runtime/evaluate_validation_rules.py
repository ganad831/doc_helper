"""Evaluate Validation Rules Use Case (Phase R-2).

Runtime evaluation of validation constraints for entity fields.

ADR-050 Compliance:
- Pull-based evaluation (caller provides all inputs)
- Deterministic (same inputs → same outputs)
- Read-only (no side effects, no persistence)
- Blocking determination based on severity
- Single-entity scope only
- Strict type enforcement (no coercion)
"""

import re
from typing import Any, Optional

from doc_helper.application.dto.export_dto import ConstraintExportDTO
from doc_helper.application.dto.runtime_dto import (
    ValidationEvaluationRequestDTO,
    ValidationEvaluationResultDTO,
    ValidationIssueDTO,
)
from doc_helper.application.usecases.schema_usecases import SchemaUseCases


class EvaluateValidationRulesUseCase:
    """Use case for evaluating validation constraints at runtime (Phase R-2).

    Evaluates all constraints for fields in an entity based on provided field values.

    ADR-050 Rules:
        - Pull-based: Caller provides entity_id, field_values
        - Deterministic: Same inputs → same outputs
        - Read-only: No persistence of results
        - Blocking: ERROR severity issues block operations
        - Single-entity scope: All fields within same entity
        - Strict type checking: No coercion

    Usage:
        use_case = EvaluateValidationRulesUseCase(schema_usecases)
        request = ValidationEvaluationRequestDTO(
            entity_id="project",
            field_values={"project_name": "", "depth": 5.0}
        )
        result = use_case.execute(request)
        if result.blocking:
            # Handle errors
            pass
    """

    def __init__(self, schema_usecases: SchemaUseCases) -> None:
        """Initialize EvaluateValidationRulesUseCase.

        Args:
            schema_usecases: SchemaUseCases instance for fetching constraints and fields
        """
        self._schema_usecases = schema_usecases

    def execute(
        self,
        request: ValidationEvaluationRequestDTO,
    ) -> ValidationEvaluationResultDTO:
        """Execute validation constraint evaluation for an entity.

        ADR-050 Compliance:
            - Pull-based: All inputs provided by caller
            - Deterministic: Same inputs → same outputs
            - Read-only: No persistence
            - Blocking: Determined by ERROR severity issues
            - Single-entity scope only

        Args:
            request: ValidationEvaluationRequestDTO with:
                - entity_id: Entity whose fields should be validated
                - field_values: Current field values (snapshot)

        Returns:
            ValidationEvaluationResultDTO with:
                - success: True if evaluation completed without exceptions
                - errors: Tuple of ERROR severity issues (blocking)
                - warnings: Tuple of WARNING severity issues
                - info: Tuple of INFO severity issues
                - blocking: True if any ERROR issues found
                - evaluated_fields: Field IDs that were evaluated
                - failed_fields: Field IDs with ERROR issues
                - error_message: Exception message if evaluation failed

        Severity Rules:
            - Use constraint's severity field (ERROR/WARNING/INFO)
            - Default to ERROR if severity missing
            - blocking = any ERROR issue present

        Null/Empty Handling:
            - REQUIRED: None, "", whitespace → violation
            - Other constraints: skip if value is None/empty
            - No type coercion (strict)

        File Metadata Shape:
            - Dict with {"name": str, "size_bytes": int}

        Example:
            request = ValidationEvaluationRequestDTO(
                entity_id="project",
                field_values={"project_name": "Test", "depth": -5}
            )
            result = use_case.execute(request)
            if result.blocking:
                # Show errors
                for error in result.errors:
                    print(f"{error.field_label}: {error.message}")
        """
        # Fetch all fields for the entity to get field labels
        try:
            entities = self._schema_usecases.get_all_entities()
            entity_dto = next((e for e in entities if e.id == request.entity_id), None)
            if not entity_dto:
                return ValidationEvaluationResultDTO.failure(
                    error_message=f"Entity '{request.entity_id}' not found"
                )
        except Exception as e:
            return ValidationEvaluationResultDTO.failure(
                error_message=f"Failed to fetch entity: {str(e)}"
            )

        # Build field ID → field label mapping
        field_labels: dict[str, str] = {}
        for field_dto in entity_dto.fields:
            field_labels[field_dto.id] = field_dto.label

        # Collect validation issues by severity
        errors: list[ValidationIssueDTO] = []
        warnings: list[ValidationIssueDTO] = []
        info: list[ValidationIssueDTO] = []
        evaluated_fields: set[str] = set()
        failed_fields: set[str] = set()

        # Evaluate constraints for each field in field_values
        for field_id, field_value in request.field_values.items():
            evaluated_fields.add(field_id)

            # Fetch constraints for this field
            try:
                constraints: tuple[ConstraintExportDTO, ...] = (
                    self._schema_usecases.list_constraints_for_field(
                        entity_id=request.entity_id,
                        field_id=field_id,
                    )
                )
            except Exception as e:
                # Skip field if constraint fetch fails (non-blocking)
                continue

            # Get field label (use field_id if not found)
            field_label = field_labels.get(field_id, field_id)

            # Evaluate each constraint for this field
            for constraint_dto in constraints:
                constraint_type = constraint_dto.constraint_type
                parameters = constraint_dto.parameters

                # Extract severity (default to ERROR if missing)
                severity = parameters.get("severity", "ERROR")

                # Evaluate constraint based on type
                issue = self._evaluate_constraint(
                    field_id=field_id,
                    field_label=field_label,
                    field_value=field_value,
                    constraint_type=constraint_type,
                    parameters=parameters,
                    severity=severity,
                )

                # Categorize issue by severity
                if issue:
                    if severity == "ERROR":
                        errors.append(issue)
                        failed_fields.add(field_id)
                    elif severity == "WARNING":
                        warnings.append(issue)
                    elif severity == "INFO":
                        info.append(issue)

        # Return aggregated result
        return ValidationEvaluationResultDTO.success_result(
            errors=tuple(errors),
            warnings=tuple(warnings),
            info=tuple(info),
            evaluated_fields=tuple(evaluated_fields),
            failed_fields=tuple(failed_fields),
        )

    def _evaluate_constraint(
        self,
        field_id: str,
        field_label: str,
        field_value: Any,
        constraint_type: str,
        parameters: dict,
        severity: str,
    ) -> Optional[ValidationIssueDTO]:
        """Evaluate a single constraint for a field value.

        Args:
            field_id: Field identifier
            field_label: Translated field label
            field_value: Current field value
            constraint_type: Type of constraint (e.g., "RequiredConstraint")
            parameters: Constraint-specific parameters
            severity: Severity level (ERROR/WARNING/INFO)

        Returns:
            ValidationIssueDTO if constraint violated, None if valid
        """
        # RequiredConstraint: None, "", whitespace → violation
        if constraint_type == "RequiredConstraint":
            if field_value is None or (
                isinstance(field_value, str) and not field_value.strip()
            ):
                return ValidationIssueDTO(
                    field_id=field_id,
                    field_label=field_label,
                    constraint_type=constraint_type,
                    severity=severity,
                    message=f"{field_label} is required",
                    code="REQUIRED_FIELD_EMPTY",
                    details=None,
                )

        # Skip other constraints if value is None or empty string
        if field_value is None or (isinstance(field_value, str) and field_value == ""):
            return None

        # MinLengthConstraint: string length >= min_length
        if constraint_type == "MinLengthConstraint":
            min_length = parameters.get("min_length")
            if isinstance(field_value, str) and len(field_value) < min_length:
                return ValidationIssueDTO(
                    field_id=field_id,
                    field_label=field_label,
                    constraint_type=constraint_type,
                    severity=severity,
                    message=f"{field_label} must be at least {min_length} characters",
                    code="VALUE_TOO_SHORT",
                    details={"min_length": min_length, "actual_length": len(field_value)},
                )

        # MaxLengthConstraint: string length <= max_length
        if constraint_type == "MaxLengthConstraint":
            max_length = parameters.get("max_length")
            if isinstance(field_value, str) and len(field_value) > max_length:
                return ValidationIssueDTO(
                    field_id=field_id,
                    field_label=field_label,
                    constraint_type=constraint_type,
                    severity=severity,
                    message=f"{field_label} must be at most {max_length} characters",
                    code="VALUE_TOO_LONG",
                    details={"max_length": max_length, "actual_length": len(field_value)},
                )

        # MinValueConstraint: numeric value >= min_value
        if constraint_type == "MinValueConstraint":
            min_value = parameters.get("min_value")
            if isinstance(field_value, (int, float)) and field_value < min_value:
                return ValidationIssueDTO(
                    field_id=field_id,
                    field_label=field_label,
                    constraint_type=constraint_type,
                    severity=severity,
                    message=f"{field_label} must be at least {min_value}",
                    code="VALUE_TOO_SMALL",
                    details={"min_value": min_value, "actual_value": field_value},
                )

        # MaxValueConstraint: numeric value <= max_value
        if constraint_type == "MaxValueConstraint":
            max_value = parameters.get("max_value")
            if isinstance(field_value, (int, float)) and field_value > max_value:
                return ValidationIssueDTO(
                    field_id=field_id,
                    field_label=field_label,
                    constraint_type=constraint_type,
                    severity=severity,
                    message=f"{field_label} must be at most {max_value}",
                    code="VALUE_TOO_LARGE",
                    details={"max_value": max_value, "actual_value": field_value},
                )

        # PatternConstraint: string matches regex pattern
        if constraint_type == "PatternConstraint":
            pattern = parameters.get("pattern")
            description = parameters.get("description", "valid format")
            if isinstance(field_value, str):
                try:
                    if not re.match(pattern, field_value):
                        return ValidationIssueDTO(
                            field_id=field_id,
                            field_label=field_label,
                            constraint_type=constraint_type,
                            severity=severity,
                            message=f"{field_label} must match {description}",
                            code="PATTERN_MISMATCH",
                            details={"pattern": pattern, "value": field_value},
                        )
                except re.error:
                    # Invalid regex pattern - skip constraint
                    pass

        # AllowedValuesConstraint: value in allowed_values list
        if constraint_type == "AllowedValuesConstraint":
            allowed_values = parameters.get("allowed_values", [])
            if field_value not in allowed_values:
                return ValidationIssueDTO(
                    field_id=field_id,
                    field_label=field_label,
                    constraint_type=constraint_type,
                    severity=severity,
                    message=f"{field_label} must be one of: {', '.join(str(v) for v in allowed_values)}",
                    code="VALUE_NOT_ALLOWED",
                    details={"allowed_values": allowed_values, "actual_value": field_value},
                )

        # FileExtensionConstraint: file extension in allowed_extensions
        if constraint_type == "FileExtensionConstraint":
            allowed_extensions = parameters.get("allowed_extensions", [])
            # Expect file metadata dict with "name" key
            if isinstance(field_value, dict) and "name" in field_value:
                file_name = field_value["name"]
                file_ext = file_name.split(".")[-1].lower() if "." in file_name else ""
                if file_ext not in [ext.lower() for ext in allowed_extensions]:
                    return ValidationIssueDTO(
                        field_id=field_id,
                        field_label=field_label,
                        constraint_type=constraint_type,
                        severity=severity,
                        message=f"{field_label} must be one of: {', '.join(allowed_extensions)}",
                        code="FILE_EXTENSION_NOT_ALLOWED",
                        details={
                            "allowed_extensions": allowed_extensions,
                            "file_name": file_name,
                            "file_extension": file_ext,
                        },
                    )

        # MaxFileSizeConstraint: file size <= max_size_bytes
        if constraint_type == "MaxFileSizeConstraint":
            max_size_bytes = parameters.get("max_size_bytes")
            # Expect file metadata dict with "size_bytes" key
            if isinstance(field_value, dict) and "size_bytes" in field_value:
                file_size = field_value["size_bytes"]
                if file_size > max_size_bytes:
                    # Convert bytes to human-readable format
                    max_size_mb = max_size_bytes / (1024 * 1024)
                    actual_size_mb = file_size / (1024 * 1024)
                    return ValidationIssueDTO(
                        field_id=field_id,
                        field_label=field_label,
                        constraint_type=constraint_type,
                        severity=severity,
                        message=f"{field_label} must be smaller than {max_size_mb:.2f} MB",
                        code="FILE_TOO_LARGE",
                        details={
                            "max_size_bytes": max_size_bytes,
                            "actual_size_bytes": file_size,
                            "max_size_mb": max_size_mb,
                            "actual_size_mb": actual_size_mb,
                        },
                    )

        # No violation found
        return None
