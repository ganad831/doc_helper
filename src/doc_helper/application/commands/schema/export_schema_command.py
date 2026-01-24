"""Export Schema Command (Phase 2 Step 4, updated Phase 3, Phase 6A, Phase F-10).

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

FORBIDDEN:
- No import functionality
- No formulas (still excluded)
- No runtime semantics
"""

import json
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
    RelationshipExportDTO,
    SchemaExportDTO,
)
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

    Usage:
        command = ExportSchemaCommand(schema_repository)
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
        relationship_repository: Optional[IRelationshipRepository] = None,
    ) -> None:
        """Initialize command.

        Args:
            schema_repository: Repository for reading schema definitions
            relationship_repository: Repository for reading relationships (Phase 6A)
        """
        self._schema_repository = schema_repository
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
        if file_path.exists():
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

        # Write to file
        try:
            self._write_export_file(file_path, export_data)
        except Exception as e:
            return Failure(f"Failed to write export file: {e}")

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

    def _write_export_file(self, file_path: Path, export_data: SchemaExportDTO) -> None:
        """Write export data to JSON file.

        Args:
            file_path: Path to write file
            export_data: Export data to serialize

        Raises:
            Exception: If file write fails
        """
        # Convert to dict for JSON serialization
        export_dict = self._export_to_dict(export_data)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_dict, f, indent=2, ensure_ascii=False)

    def _export_to_dict(self, export_data: SchemaExportDTO) -> dict:
        """Convert SchemaExportDTO to dict for JSON serialization.

        Args:
            export_data: Export data to convert

        Returns:
            Dict representation for JSON

        Phase F-10: Includes control_rules in field serialization.
        """
        result = {
            "schema_id": export_data.schema_id,
            "entities": [
                {
                    "id": entity.id,
                    "name_key": entity.name_key,
                    "description_key": entity.description_key,
                    "is_root_entity": entity.is_root_entity,
                    "fields": [
                        {
                            "id": field.id,
                            "field_type": field.field_type,
                            "label_key": field.label_key,
                            "required": field.required,
                            "help_text_key": field.help_text_key,
                            "default_value": field.default_value,
                            "options": [
                                {
                                    "value": opt.value,
                                    "label_key": opt.label_key,
                                }
                                for opt in field.options
                            ],
                            "constraints": [
                                {
                                    "constraint_type": c.constraint_type,
                                    "parameters": c.parameters,
                                }
                                for c in field.constraints
                            ],
                            # Phase F-10: Include control rules
                            "control_rules": [
                                {
                                    "rule_type": cr.rule_type,
                                    "target_field_id": cr.target_field_id,
                                    "formula_text": cr.formula_text,
                                }
                                for cr in field.control_rules
                            ],
                        }
                        for field in entity.fields
                    ],
                }
                for entity in export_data.entities
            ],
        }

        # Include version only if provided (Phase 3 Decision 5: Optional)
        if export_data.version is not None:
            result["version"] = export_data.version

        # Include relationships (Phase 6A - ADR-022)
        # Relationships are always included (can be empty array)
        result["relationships"] = [
            {
                "id": rel.id,
                "source_entity_id": rel.source_entity_id,
                "target_entity_id": rel.target_entity_id,
                "relationship_type": rel.relationship_type,
                "name_key": rel.name_key,
                "description_key": rel.description_key,
                "inverse_name_key": rel.inverse_name_key,
            }
            for rel in export_data.relationships
        ]

        return result
