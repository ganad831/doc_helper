"""Export Schema Command (Phase 2 Step 4, updated Phase 3, Phase 6A, Phase F-10, Phase F-12.5, Phase H-4).

Command for exporting schema definitions to file.
Follows approved guardrails and decisions.

PHASE 2 APPROVED DECISIONS:
- Decision 1: Fail if file exists
- Decision 2: Fail if schema is empty
- Decision 3: Validate translation key format only (non-empty string)
- Decision 4: Category-level warnings for excluded data
- Decision 5: Any user-selected path allowed
- Decision 6: No timestamp in export
- Decision 7: Include schema identifier
- Decision 8: Allow zero root entities
- Decision 9: No circular reference checking

PHASE 3 UPDATE:
- Decision 5: Version field is optional in export

PHASE 6A UPDATE (ADR-022):
- Relationships are now exported (RelationshipDefinition)
- Relationships serialized after entities (dependency order)

PHASE F-10 UPDATE:
- Control rules are now exported (ControlRuleExportDTO)
- Control rules are design-time metadata only (no runtime execution)
- Formulas, lookups, child entities still excluded

PHASE F-12.5 UPDATE:
- Output mappings are now exported (OutputMappingExportDTO)
- Output mappings are design-time metadata only (no runtime execution)

PHASE H-4 UPDATE:
- File I/O extracted to ISchemaExportWriter interface
- Command delegates filesystem operations to infrastructure
- Command returns pure data structures only

FORBIDDEN:
- No import functionality
- No formulas (still excluded)
- No runtime semantics
- No filesystem I/O in command (Phase H-4)
"""

from pathlib import Path
from typing import Optional

from doc_helper.application.dto.export_dto import (
    ConstraintExportDTO,
    ControlRuleExportDTO,
    EntityExportDTO,
    ExportResult,
    ExportWarning,
    FieldExportDTO,
    FieldOptionExportDTO,
    OutputMappingExportDTO,
    RelationshipExportDTO,
    SchemaExportDTO,
)
from doc_helper.application.interfaces.schema_export_writer import ISchemaExportWriter
from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_repository import IRelationshipRepository
from doc_helper.domain.schema.schema_repository import ISchemaRepository
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


class ExportSchemaCommand:
    """Command to export schema to file.

    Validates schema against Phase 1 and Phase 2 invariants,
    generates quality warnings, and writes export file.

    Phase H-4: File I/O delegated to ISchemaExportWriter.
    Command builds pure data structures (DTOs), infrastructure writes files.

    Usage:
        writer = JsonSchemaExportWriter()
        command = ExportSchemaCommand(schema_repository, writer)
        result = command.execute(
            schema_id="soil_investigation",
            file_path=Path("/path/to/export.json")
        )
        if result.is_success():
            export_result = result.value
            if export_result.warnings:
                # Display warnings to user
            # Success!
        else:
            # Handle error
            print(result.error)
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        schema_export_writer: ISchemaExportWriter,
        relationship_repository: Optional[IRelationshipRepository] = None,
    ) -> None:
        """Initialize command.

        Args:
            schema_repository: Repository for reading schema definitions
            schema_export_writer: Infrastructure service for file I/O (Phase H-4)
            relationship_repository: Repository for reading relationships (Phase 6A)
        """
        self._schema_repository = schema_repository
        self._schema_export_writer = schema_export_writer
        self._relationship_repository = relationship_repository

    def execute(
        self,
        schema_id: str,
        file_path: Path,
        version: Optional[str] = None,
    ) -> Result[ExportResult, str]:
        """Execute schema export.

        Args:
            schema_id: Identifier for the schema (included in export per Decision 7)
            file_path: Path to write export file
            version: Optional semantic version string (Phase 3 Decision 5)

        Returns:
            Result containing ExportResult (with warnings) or error message

        Validation:
            - Schema must not be empty (Decision 2)
            - File must not already exist (Decision 1)
            - Translation keys must be non-empty strings (Decision 3)
        """
        # Validate file path - must not exist (Decision 1)
        # Phase H-4: Delegate filesystem check to infrastructure
        if self._schema_export_writer.file_exists(file_path):
            return Failure(f"Export file already exists: {file_path}")

        # Load all entities from repository
        entities_result = self._schema_repository.get_all()
        if entities_result.is_failure():
            return Failure(f"Failed to load schema: {entities_result.error}")

        entities: tuple = entities_result.value

        # Validate schema not empty (Decision 2)
        if not entities:
            return Failure("Cannot export empty schema: no entities defined")

        # Check if at least one entity has fields
        total_fields = sum(entity.field_count for entity in entities)
        if total_fields == 0:
            return Failure("Cannot export empty schema: no fields defined in any entity")

        # Validate translation keys and build export data
        warnings: list[ExportWarning] = []
        entity_exports: list[EntityExportDTO] = []

        for entity in entities:
            # Validate entity translation keys (Decision 3)
            key_error = self._validate_translation_key(entity.name_key.key, f"entity {entity.id.value} name_key")
            if key_error:
                return Failure(key_error)

            if entity.description_key:
                key_error = self._validate_translation_key(
                    entity.description_key.key,
                    f"entity {entity.id.value} description_key"
                )
                if key_error:
                    return Failure(key_error)

            # Check for quality warnings
            if entity.field_count == 0:
                warnings.append(ExportWarning(
                    category="incomplete_entity",
                    message=f"Entity '{entity.id.value}' has no fields"
                ))

            # Convert fields
            field_exports: list[FieldExportDTO] = []
            for field_def in entity.get_all_fields():
                field_export, field_warnings = self._convert_field(field_def, entity.id.value)
                if isinstance(field_export, str):
                    # It's an error message
                    return Failure(field_export)
                field_exports.append(field_export)
                warnings.extend(field_warnings)

            entity_export = EntityExportDTO(
                id=entity.id.value,
                name_key=entity.name_key.key,
                description_key=entity.description_key.key if entity.description_key else None,
                is_root_entity=entity.is_root_entity,
                fields=tuple(field_exports),
            )
            entity_exports.append(entity_export)

        # Check for excluded data and generate category-level warnings (Decision 4)
        excluded_warnings = self._check_excluded_data(entities)
        warnings.extend(excluded_warnings)

        # Load relationships (Phase 6A - ADR-022)
        relationship_exports: list[RelationshipExportDTO] = []
        if self._relationship_repository:
            relationships_result = self._relationship_repository.get_all()
            if relationships_result.is_success():
                for rel_def in relationships_result.value:
                    rel_export, rel_warnings = self._convert_relationship(rel_def)
                    if isinstance(rel_export, str):
                        # It's an error message
                        return Failure(rel_export)
                    relationship_exports.append(rel_export)
                    warnings.extend(rel_warnings)
            # Note: If relationships fail to load, we still export entities

        # Create export data (with optional version - Phase 3 Decision 5)
        export_data = SchemaExportDTO(
            schema_id=schema_id,
            entities=tuple(entity_exports),
            version=version,
            relationships=tuple(relationship_exports),
        )

        # Write to file (Phase H-4: delegate to infrastructure)
        write_result = self._schema_export_writer.write(file_path, export_data)
        if write_result.is_failure():
            return Failure(write_result.error)

        return Success(ExportResult(
            success=True,
            export_data=export_data,
            warnings=tuple(warnings),
            error=None,
        ))

    def _validate_translation_key(self, key: str, context: str) -> Optional[str]:
        """Validate translation key format (Decision 3).

        Args:
            key: Translation key to validate
            context: Context for error message

        Returns:
            Error message if invalid, None if valid
        """
        if not key or not isinstance(key, str):
            return f"Invalid translation key for {context}: key must be non-empty string"
        if not key.strip():
            return f"Invalid translation key for {context}: key must not be whitespace-only"
        return None

    def _convert_field(
        self,
        field_def: FieldDefinition,
        entity_id: str,
    ) -> tuple[FieldExportDTO | str, list[ExportWarning]]:
        """Convert field definition to export DTO.

        Args:
            field_def: Field definition to convert
            entity_id: Parent entity ID for context

        Returns:
            Tuple of (FieldExportDTO or error string, list of warnings)
        """
        warnings: list[ExportWarning] = []

        # Validate translation keys (Decision 3)
        key_error = self._validate_translation_key(
            field_def.label_key.key,
            f"field {entity_id}.{field_def.id.value} label_key"
        )
        if key_error:
            return key_error, []

        if field_def.help_text_key:
            key_error = self._validate_translation_key(
                field_def.help_text_key.key,
                f"field {entity_id}.{field_def.id.value} help_text_key"
            )
            if key_error:
                return key_error, []
        else:
            # Quality warning for missing help text
            warnings.append(ExportWarning(
                category="missing_metadata",
                message=f"Field '{entity_id}.{field_def.id.value}' has no help text"
            ))

        # Convert options for choice fields
        options: list[FieldOptionExportDTO] = []
        if field_def.is_choice_field:
            if not field_def.options:
                warnings.append(ExportWarning(
                    category="incomplete_field",
                    message=f"Choice field '{entity_id}.{field_def.id.value}' has no options"
                ))
            else:
                for opt_value, opt_label_key in field_def.options:
                    # Validate option label key
                    key_error = self._validate_translation_key(
                        opt_label_key.key if hasattr(opt_label_key, 'key') else str(opt_label_key),
                        f"field {entity_id}.{field_def.id.value} option '{opt_value}' label_key"
                    )
                    if key_error:
                        return key_error, []

                    options.append(FieldOptionExportDTO(
                        value=str(opt_value),
                        label_key=opt_label_key.key if hasattr(opt_label_key, 'key') else str(opt_label_key),
                    ))

        # Convert constraints
        constraints: list[ConstraintExportDTO] = []
        for constraint in field_def.constraints:
            constraint_export = self._convert_constraint(constraint)
            constraints.append(constraint_export)

        # Phase F-10: Convert control rules
        control_rules: list[ControlRuleExportDTO] = []
        for rule in field_def.control_rules:
            if isinstance(rule, ControlRuleExportDTO):
                # Already in export format, use directly
                control_rules.append(rule)
            elif hasattr(rule, 'rule_type') and hasattr(rule, 'formula_text'):
                # Convert from other format if needed
                control_rules.append(ControlRuleExportDTO(
                    rule_type=str(rule.rule_type),
                    target_field_id=str(getattr(rule, 'target_field_id', field_def.id.value)),
                    formula_text=str(rule.formula_text),
                ))

        # Phase F-12.5: Convert output mappings
        output_mappings: list[OutputMappingExportDTO] = []
        for mapping in field_def.output_mappings:
            if isinstance(mapping, OutputMappingExportDTO):
                # Already in export format, use directly
                output_mappings.append(mapping)
            elif hasattr(mapping, 'target') and hasattr(mapping, 'formula_text'):
                # Convert from other format if needed
                output_mappings.append(OutputMappingExportDTO(
                    target=str(mapping.target),
                    formula_text=str(mapping.formula_text),
                ))

        field_export = FieldExportDTO(
            id=field_def.id.value,
            field_type=field_def.field_type.value,
            label_key=field_def.label_key.key,
            required=field_def.required,
            help_text_key=field_def.help_text_key.key if field_def.help_text_key else None,
            default_value=str(field_def.default_value) if field_def.default_value is not None else None,
            options=tuple(options),
            constraints=tuple(constraints),
            control_rules=tuple(control_rules),
            output_mappings=tuple(output_mappings),
        )

        return field_export, warnings

    def _convert_constraint(self, constraint: FieldConstraint) -> ConstraintExportDTO:
        """Convert constraint to export DTO.

        Args:
            constraint: Constraint to convert

        Returns:
            ConstraintExportDTO with type and parameters
        """
        constraint_type = type(constraint).__name__
        parameters: dict = {}

        if isinstance(constraint, RequiredConstraint):
            # No parameters for required constraint
            pass
        elif isinstance(constraint, MinLengthConstraint):
            parameters["min_length"] = constraint.min_length
        elif isinstance(constraint, MaxLengthConstraint):
            parameters["max_length"] = constraint.max_length
        elif isinstance(constraint, MinValueConstraint):
            parameters["min_value"] = constraint.min_value
        elif isinstance(constraint, MaxValueConstraint):
            parameters["max_value"] = constraint.max_value
        elif isinstance(constraint, PatternConstraint):
            parameters["pattern"] = constraint.pattern
            if constraint.description:
                parameters["description"] = constraint.description
        elif isinstance(constraint, AllowedValuesConstraint):
            parameters["allowed_values"] = list(constraint.allowed_values)
        elif isinstance(constraint, FileExtensionConstraint):
            parameters["allowed_extensions"] = list(constraint.allowed_extensions)
        elif isinstance(constraint, MaxFileSizeConstraint):
            parameters["max_size_bytes"] = constraint.max_size_bytes

        return ConstraintExportDTO(
            constraint_type=constraint_type,
            parameters=parameters,
        )

    def _check_excluded_data(self, entities: tuple) -> list[ExportWarning]:
        """Check for excluded data and generate category-level warnings (Decision 4).

        Args:
            entities: All entities in schema

        Returns:
            List of warnings for excluded data categories

        Phase F-10: Control rules are now exported, so no warning is generated for them.
        """
        warnings: list[ExportWarning] = []

        formula_count = 0
        lookup_count = 0
        table_count = 0

        for entity in entities:
            for field_def in entity.get_all_fields():
                # Count formulas (excluded from export)
                if field_def.formula:
                    formula_count += 1

                # Phase F-10: Control rules are now exported (no warning needed)

                # Count lookup references (behavioral - excluded)
                if field_def.lookup_entity_id:
                    lookup_count += 1

                # Count table references (behavioral - excluded)
                if field_def.child_entity_id:
                    table_count += 1

        # Generate category-level warnings (Decision 4: Category warnings)
        if formula_count > 0:
            warnings.append(ExportWarning(
                category="excluded_data",
                message=f"{formula_count} formula(s) not exported (Phase 2.2 feature)"
            ))

        # Phase F-10: Control rules are now exported, no warning needed

        if lookup_count > 0:
            warnings.append(ExportWarning(
                category="excluded_data",
                message=f"{lookup_count} lookup reference(s) not exported (behavioral data)"
            ))

        if table_count > 0:
            warnings.append(ExportWarning(
                category="excluded_data",
                message=f"{table_count} table/child entity reference(s) not exported (behavioral data)"
            ))

        return warnings

    def _convert_relationship(
        self,
        rel_def: RelationshipDefinition,
    ) -> tuple[RelationshipExportDTO | str, list[ExportWarning]]:
        """Convert relationship definition to export DTO (Phase 6A - ADR-022).

        Args:
            rel_def: Relationship definition to convert

        Returns:
            Tuple of (RelationshipExportDTO or error string, list of warnings)
        """
        warnings: list[ExportWarning] = []

        # Validate translation keys (Decision 3)
        key_error = self._validate_translation_key(
            rel_def.name_key.key,
            f"relationship {rel_def.id.value} name_key"
        )
        if key_error:
            return key_error, []

        if rel_def.description_key:
            key_error = self._validate_translation_key(
                rel_def.description_key.key,
                f"relationship {rel_def.id.value} description_key"
            )
            if key_error:
                return key_error, []

        if rel_def.inverse_name_key:
            key_error = self._validate_translation_key(
                rel_def.inverse_name_key.key,
                f"relationship {rel_def.id.value} inverse_name_key"
            )
            if key_error:
                return key_error, []

        rel_export = RelationshipExportDTO(
            id=rel_def.id.value,
            source_entity_id=rel_def.source_entity_id.value,
            target_entity_id=rel_def.target_entity_id.value,
            relationship_type=rel_def.relationship_type.value,
            name_key=rel_def.name_key.key,
            description_key=rel_def.description_key.key if rel_def.description_key else None,
            inverse_name_key=rel_def.inverse_name_key.key if rel_def.inverse_name_key else None,
        )

        return rel_export, warnings

    # Phase H-4: _write_export_file and _export_to_dict moved to JsonSchemaExportWriter
    # in infrastructure/interchange/json_schema_exporter.py
