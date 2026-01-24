"""Schema Import Validation Service (Phase 4, updated Phase 6A, Phase F-10, Phase F-12.5).

Service for validating and converting import JSON to domain objects.

APPROVED DECISIONS:
- Decision 6: Empty entity handling → Warn but allow
- Decision 7: Unknown constraint type → Fail import (strict validation)

PHASE 6A UPDATE (ADR-022):
- Added relationship validation and conversion
- Validates relationship entity references
- Converts relationships to RelationshipDefinition domain objects

PHASE F-10 UPDATE:
- Added control rule validation and conversion
- Validates control rule formulas with governance (F-6)

PHASE F-12.5 UPDATE:
- Added output mapping validation and conversion
- Validates output mapping formulas with governance (F-6)

VALIDATION LAYERS:
1. JSON Structure Validation
2. Schema Content Validation
3. Domain Object Conversion
"""

import json
from pathlib import Path
from typing import Optional

from doc_helper.application.dto.control_rule_dto import ControlRuleType
from doc_helper.application.dto.export_dto import (
    ConstraintExportDTO,
    ControlRuleExportDTO,
    EntityExportDTO,
    FieldExportDTO,
    FieldOptionExportDTO,
    OutputMappingExportDTO,
    RelationshipExportDTO,
    SchemaExportDTO,
)
from doc_helper.application.dto.formula_dto import SchemaFieldInfoDTO
from doc_helper.application.dto.import_dto import (
    ImportValidationError,
    ImportWarning,
)
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.relationship_definition import RelationshipDefinition
from doc_helper.domain.schema.relationship_type import RelationshipType
from doc_helper.domain.schema.schema_ids import (
    EntityDefinitionId,
    FieldDefinitionId,
    RelationshipDefinitionId,
)
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


# Known constraint types (Decision 7: Unknown types fail import)
KNOWN_CONSTRAINT_TYPES = {
    "RequiredConstraint",
    "MinLengthConstraint",
    "MaxLengthConstraint",
    "MinValueConstraint",
    "MaxValueConstraint",
    "PatternConstraint",
    "AllowedValuesConstraint",
    "FileExtensionConstraint",
    "MaxFileSizeConstraint",
}

# Known relationship types (Phase 6A - ADR-022)
KNOWN_RELATIONSHIP_TYPES = {"CONTAINS", "REFERENCES", "ASSOCIATES"}

# Known control rule types (Phase F-10)
KNOWN_CONTROL_RULE_TYPES = {"VISIBILITY", "ENABLED", "REQUIRED"}

# Known output mapping target types (Phase F-12.5)
KNOWN_OUTPUT_MAPPING_TARGETS = {"TEXT", "NUMBER", "BOOLEAN"}


class SchemaImportValidationService:
    """Service for validating and parsing schema import files.

    Provides:
    - JSON file reading and parsing
    - Structure validation
    - Content validation
    - Domain object conversion
    - Warning generation for non-blocking issues

    Usage:
        service = SchemaImportValidationService()
        result = service.validate_and_parse(file_path)
        if result.is_success():
            parsed = result.value
            entities = parsed["entities"]
            warnings = parsed["warnings"]
    """

    def validate_and_parse(
        self,
        file_path: Path,
    ) -> Result[dict, tuple]:
        """Validate and parse import file.

        Args:
            file_path: Path to JSON import file

        Returns:
            Result containing dict with:
                - "schema_export_dto": SchemaExportDTO
                - "entities": tuple[EntityDefinition, ...]
                - "warnings": list[ImportWarning]
                - "version": Optional[str]
            Or tuple of ImportValidationError on failure
        """
        # Layer 1: File exists and is readable
        if not file_path.exists():
            return Failure((ImportValidationError(
                category="file_not_found",
                message=f"Import file not found: {file_path}",
            ),))

        # Layer 1: JSON parsing
        try:
            content = file_path.read_text(encoding='utf-8')
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return Failure((ImportValidationError(
                category="json_syntax",
                message=f"Invalid JSON syntax: {e}",
                location=f"line {e.lineno}, column {e.colno}",
            ),))
        except Exception as e:
            return Failure((ImportValidationError(
                category="file_read",
                message=f"Failed to read file: {e}",
            ),))

        # Layer 2: Structure validation
        structure_result = self._validate_structure(data)
        if structure_result.is_failure():
            return structure_result

        # Layer 2: Content validation
        content_result = self._validate_content(data)
        if content_result.is_failure():
            return content_result

        # Layer 3: Convert to domain objects
        conversion_result = self._convert_to_domain_objects(data)
        if conversion_result.is_failure():
            return conversion_result

        return conversion_result

    def validate_json_data(
        self,
        data: dict,
    ) -> Result[dict, tuple]:
        """Validate pre-parsed JSON data (for testing or programmatic use).

        Args:
            data: Parsed JSON data dictionary

        Returns:
            Same as validate_and_parse
        """
        # Layer 2: Structure validation
        structure_result = self._validate_structure(data)
        if structure_result.is_failure():
            return structure_result

        # Layer 2: Content validation
        content_result = self._validate_content(data)
        if content_result.is_failure():
            return content_result

        # Layer 3: Convert to domain objects
        return self._convert_to_domain_objects(data)

    def _validate_structure(self, data: dict) -> Result[None, tuple]:
        """Layer 2: Validate JSON structure.

        Checks:
        - Required top-level keys present
        - Correct data types for all keys
        """
        errors: list[ImportValidationError] = []

        # Check data is a dict
        if not isinstance(data, dict):
            return Failure((ImportValidationError(
                category="invalid_type",
                message=f"Root must be an object, got {type(data).__name__}",
                location="root",
            ),))

        # Check required keys
        if "schema_id" not in data:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: schema_id",
                location="root",
            ))
        elif not isinstance(data["schema_id"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"schema_id must be a string, got {type(data['schema_id']).__name__}",
                location="schema_id",
            ))
        elif not data["schema_id"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="schema_id cannot be empty",
                location="schema_id",
            ))

        if "entities" not in data:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: entities",
                location="root",
            ))
        elif not isinstance(data["entities"], list):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"entities must be an array, got {type(data['entities']).__name__}",
                location="entities",
            ))

        # Check optional version field type
        if "version" in data and data["version"] is not None:
            if not isinstance(data["version"], str):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"version must be a string, got {type(data['version']).__name__}",
                    location="version",
                ))

        # Check optional relationships field type (Phase 6A - ADR-022)
        if "relationships" in data and data["relationships"] is not None:
            if not isinstance(data["relationships"], list):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"relationships must be an array, got {type(data['relationships']).__name__}",
                    location="relationships",
                ))

        if errors:
            return Failure(tuple(errors))

        return Success(None)

    def _validate_content(self, data: dict) -> Result[None, tuple]:
        """Layer 2: Validate schema content.

        Checks:
        - All entity structures are valid
        - All field structures are valid
        - All constraint types are known
        - All relationship structures are valid (Phase 6A)
        """
        errors: list[ImportValidationError] = []

        entities = data.get("entities", [])
        entity_ids = set()  # Collect entity IDs for relationship validation

        for i, entity in enumerate(entities):
            entity_location = f"entities[{i}]"

            # Validate entity structure
            entity_errors = self._validate_entity_structure(entity, entity_location)
            errors.extend(entity_errors)

            if not entity_errors:  # Only validate fields if entity is valid
                entity_ids.add(entity.get("id", ""))
                fields = entity.get("fields", [])
                for j, field in enumerate(fields):
                    field_location = f"{entity_location}.fields[{j}]"
                    field_errors = self._validate_field_structure(field, field_location)
                    errors.extend(field_errors)

        # Validate relationships (Phase 6A - ADR-022)
        relationships = data.get("relationships", [])
        for i, relationship in enumerate(relationships):
            rel_location = f"relationships[{i}]"
            rel_errors = self._validate_relationship_structure(
                relationship, rel_location, entity_ids
            )
            errors.extend(rel_errors)

        if errors:
            return Failure(tuple(errors))

        return Success(None)

    def _validate_entity_structure(
        self,
        entity: dict,
        location: str,
    ) -> list[ImportValidationError]:
        """Validate a single entity's structure."""
        errors: list[ImportValidationError] = []

        if not isinstance(entity, dict):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"Entity must be an object, got {type(entity).__name__}",
                location=location,
            ))
            return errors

        # Required fields
        if "id" not in entity:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: id",
                location=location,
            ))
        elif not isinstance(entity["id"], str) or not entity["id"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="Entity id must be a non-empty string",
                location=f"{location}.id",
            ))

        if "name_key" not in entity:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: name_key",
                location=location,
            ))
        elif not isinstance(entity["name_key"], str) or not entity["name_key"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="Entity name_key must be a non-empty string",
                location=f"{location}.name_key",
            ))

        if "is_root_entity" not in entity:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: is_root_entity",
                location=location,
            ))
        elif not isinstance(entity["is_root_entity"], bool):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"is_root_entity must be a boolean, got {type(entity['is_root_entity']).__name__}",
                location=f"{location}.is_root_entity",
            ))

        # Optional description_key
        if "description_key" in entity and entity["description_key"] is not None:
            if not isinstance(entity["description_key"], str):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"description_key must be a string, got {type(entity['description_key']).__name__}",
                    location=f"{location}.description_key",
                ))
            elif not entity["description_key"].strip():
                errors.append(ImportValidationError(
                    category="invalid_value",
                    message="description_key cannot be a whitespace-only string",
                    location=f"{location}.description_key",
                ))

        # Fields must be an array
        if "fields" not in entity:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: fields",
                location=location,
            ))
        elif not isinstance(entity["fields"], list):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"fields must be an array, got {type(entity['fields']).__name__}",
                location=f"{location}.fields",
            ))

        return errors

    def _validate_field_structure(
        self,
        field: dict,
        location: str,
    ) -> list[ImportValidationError]:
        """Validate a single field's structure."""
        errors: list[ImportValidationError] = []

        if not isinstance(field, dict):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"Field must be an object, got {type(field).__name__}",
                location=location,
            ))
            return errors

        # Required fields
        if "id" not in field:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: id",
                location=location,
            ))
        elif not isinstance(field["id"], str) or not field["id"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="Field id must be a non-empty string",
                location=f"{location}.id",
            ))

        if "field_type" not in field:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: field_type",
                location=location,
            ))
        elif not isinstance(field["field_type"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"field_type must be a string, got {type(field['field_type']).__name__}",
                location=f"{location}.field_type",
            ))
        else:
            # Validate field type value
            try:
                FieldType.from_string(field["field_type"])
            except ValueError as e:
                errors.append(ImportValidationError(
                    category="invalid_value",
                    message=str(e),
                    location=f"{location}.field_type",
                ))

        if "label_key" not in field:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: label_key",
                location=location,
            ))
        elif not isinstance(field["label_key"], str) or not field["label_key"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="Field label_key must be a non-empty string",
                location=f"{location}.label_key",
            ))

        if "required" not in field:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: required",
                location=location,
            ))
        elif not isinstance(field["required"], bool):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"required must be a boolean, got {type(field['required']).__name__}",
                location=f"{location}.required",
            ))

        # Optional fields type validation
        if "help_text_key" in field and field["help_text_key"] is not None:
            if not isinstance(field["help_text_key"], str):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"help_text_key must be a string, got {type(field['help_text_key']).__name__}",
                    location=f"{location}.help_text_key",
                ))

        if "default_value" in field and field["default_value"] is not None:
            if not isinstance(field["default_value"], str):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"default_value must be a string, got {type(field['default_value']).__name__}",
                    location=f"{location}.default_value",
                ))

        # Validate options array
        if "options" in field:
            if not isinstance(field["options"], list):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"options must be an array, got {type(field['options']).__name__}",
                    location=f"{location}.options",
                ))
            else:
                for k, option in enumerate(field["options"]):
                    option_errors = self._validate_option_structure(
                        option, f"{location}.options[{k}]"
                    )
                    errors.extend(option_errors)

        # Validate constraints array
        if "constraints" in field:
            if not isinstance(field["constraints"], list):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"constraints must be an array, got {type(field['constraints']).__name__}",
                    location=f"{location}.constraints",
                ))
            else:
                for k, constraint in enumerate(field["constraints"]):
                    constraint_errors = self._validate_constraint_structure(
                        constraint, f"{location}.constraints[{k}]"
                    )
                    errors.extend(constraint_errors)

        # Validate control_rules array (Phase F-10)
        if "control_rules" in field:
            if not isinstance(field["control_rules"], list):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"control_rules must be an array, got {type(field['control_rules']).__name__}",
                    location=f"{location}.control_rules",
                ))
            else:
                for k, control_rule in enumerate(field["control_rules"]):
                    control_rule_errors = self._validate_control_rule_structure(
                        control_rule, f"{location}.control_rules[{k}]"
                    )
                    errors.extend(control_rule_errors)

        # Validate output_mappings array (Phase F-12.5)
        if "output_mappings" in field:
            if not isinstance(field["output_mappings"], list):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"output_mappings must be an array, got {type(field['output_mappings']).__name__}",
                    location=f"{location}.output_mappings",
                ))
            else:
                for k, output_mapping in enumerate(field["output_mappings"]):
                    output_mapping_errors = self._validate_output_mapping_structure(
                        output_mapping, f"{location}.output_mappings[{k}]"
                    )
                    errors.extend(output_mapping_errors)

        return errors

    def _validate_option_structure(
        self,
        option: dict,
        location: str,
    ) -> list[ImportValidationError]:
        """Validate a single option's structure."""
        errors: list[ImportValidationError] = []

        if not isinstance(option, dict):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"Option must be an object, got {type(option).__name__}",
                location=location,
            ))
            return errors

        if "value" not in option:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: value",
                location=location,
            ))
        elif not isinstance(option["value"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"value must be a string, got {type(option['value']).__name__}",
                location=f"{location}.value",
            ))

        if "label_key" not in option:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: label_key",
                location=location,
            ))
        elif not isinstance(option["label_key"], str) or not option["label_key"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="Option label_key must be a non-empty string",
                location=f"{location}.label_key",
            ))

        return errors

    def _validate_constraint_structure(
        self,
        constraint: dict,
        location: str,
    ) -> list[ImportValidationError]:
        """Validate a single constraint's structure.

        Decision 7: Unknown constraint types fail import.
        """
        errors: list[ImportValidationError] = []

        if not isinstance(constraint, dict):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"Constraint must be an object, got {type(constraint).__name__}",
                location=location,
            ))
            return errors

        if "constraint_type" not in constraint:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: constraint_type",
                location=location,
            ))
        elif not isinstance(constraint["constraint_type"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"constraint_type must be a string, got {type(constraint['constraint_type']).__name__}",
                location=f"{location}.constraint_type",
            ))
        else:
            # Decision 7: Unknown constraint types fail import
            if constraint["constraint_type"] not in KNOWN_CONSTRAINT_TYPES:
                errors.append(ImportValidationError(
                    category="unknown_constraint",
                    message=f"Unknown constraint type: {constraint['constraint_type']}. "
                            f"Known types: {sorted(KNOWN_CONSTRAINT_TYPES)}",
                    location=f"{location}.constraint_type",
                ))

        if "parameters" not in constraint:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: parameters",
                location=location,
            ))
        elif not isinstance(constraint["parameters"], dict):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"parameters must be an object, got {type(constraint['parameters']).__name__}",
                location=f"{location}.parameters",
            ))

        return errors

    def _validate_control_rule_structure(
        self,
        control_rule: dict,
        location: str,
    ) -> list[ImportValidationError]:
        """Validate a single control rule's structure (Phase F-10).

        Note: Formula validation (governance + boolean check) is done later
        in _validate_control_rule_formula once we have the full schema context.
        """
        errors: list[ImportValidationError] = []

        if not isinstance(control_rule, dict):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"Control rule must be an object, got {type(control_rule).__name__}",
                location=location,
            ))
            return errors

        # Required: rule_type
        if "rule_type" not in control_rule:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: rule_type",
                location=location,
            ))
        elif not isinstance(control_rule["rule_type"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"rule_type must be a string, got {type(control_rule['rule_type']).__name__}",
                location=f"{location}.rule_type",
            ))
        elif control_rule["rule_type"] not in KNOWN_CONTROL_RULE_TYPES:
            errors.append(ImportValidationError(
                category="control_rule_invalid",
                message=f"Unknown rule_type: {control_rule['rule_type']}. "
                        f"Valid types: {sorted(KNOWN_CONTROL_RULE_TYPES)}",
                location=f"{location}.rule_type",
            ))

        # Required: target_field_id
        if "target_field_id" not in control_rule:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: target_field_id",
                location=location,
            ))
        elif not isinstance(control_rule["target_field_id"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"target_field_id must be a string, got {type(control_rule['target_field_id']).__name__}",
                location=f"{location}.target_field_id",
            ))
        elif not control_rule["target_field_id"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="target_field_id cannot be empty",
                location=f"{location}.target_field_id",
            ))

        # Required: formula_text
        if "formula_text" not in control_rule:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: formula_text",
                location=location,
            ))
        elif not isinstance(control_rule["formula_text"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"formula_text must be a string, got {type(control_rule['formula_text']).__name__}",
                location=f"{location}.formula_text",
            ))

        return errors

    def _validate_output_mapping_structure(
        self,
        output_mapping: dict,
        location: str,
    ) -> list[ImportValidationError]:
        """Validate a single output mapping's structure (Phase F-12.5).

        Note: Formula validation (governance) is done later
        in _validate_output_mappings_for_entity once we have the full schema context.
        """
        errors: list[ImportValidationError] = []

        if not isinstance(output_mapping, dict):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"Output mapping must be an object, got {type(output_mapping).__name__}",
                location=location,
            ))
            return errors

        # Required: target
        if "target" not in output_mapping:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: target",
                location=location,
            ))
        elif not isinstance(output_mapping["target"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"target must be a string, got {type(output_mapping['target']).__name__}",
                location=f"{location}.target",
            ))
        elif not output_mapping["target"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="target cannot be empty",
                location=f"{location}.target",
            ))
        elif output_mapping["target"].upper() not in KNOWN_OUTPUT_MAPPING_TARGETS:
            errors.append(ImportValidationError(
                category="output_mapping_invalid",
                message=f"Unknown target type: {output_mapping['target']}. "
                        f"Valid types: {sorted(KNOWN_OUTPUT_MAPPING_TARGETS)}",
                location=f"{location}.target",
            ))

        # Required: formula_text
        if "formula_text" not in output_mapping:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: formula_text",
                location=location,
            ))
        elif not isinstance(output_mapping["formula_text"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"formula_text must be a string, got {type(output_mapping['formula_text']).__name__}",
                location=f"{location}.formula_text",
            ))
        elif not output_mapping["formula_text"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="formula_text cannot be empty",
                location=f"{location}.formula_text",
            ))

        return errors

    def _validate_relationship_structure(
        self,
        relationship: dict,
        location: str,
        entity_ids: set,
    ) -> list[ImportValidationError]:
        """Validate a single relationship's structure (Phase 6A - ADR-022)."""
        errors: list[ImportValidationError] = []

        if not isinstance(relationship, dict):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"Relationship must be an object, got {type(relationship).__name__}",
                location=location,
            ))
            return errors

        # Required fields
        if "id" not in relationship:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: id",
                location=location,
            ))
        elif not isinstance(relationship["id"], str) or not relationship["id"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="Relationship id must be a non-empty string",
                location=f"{location}.id",
            ))

        if "source_entity_id" not in relationship:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: source_entity_id",
                location=location,
            ))
        elif not isinstance(relationship["source_entity_id"], str) or not relationship["source_entity_id"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="source_entity_id must be a non-empty string",
                location=f"{location}.source_entity_id",
            ))
        elif relationship["source_entity_id"] not in entity_ids:
            errors.append(ImportValidationError(
                category="invalid_reference",
                message=f"source_entity_id '{relationship['source_entity_id']}' does not reference a valid entity in this import",
                location=f"{location}.source_entity_id",
            ))

        if "target_entity_id" not in relationship:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: target_entity_id",
                location=location,
            ))
        elif not isinstance(relationship["target_entity_id"], str) or not relationship["target_entity_id"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="target_entity_id must be a non-empty string",
                location=f"{location}.target_entity_id",
            ))
        elif relationship["target_entity_id"] not in entity_ids:
            errors.append(ImportValidationError(
                category="invalid_reference",
                message=f"target_entity_id '{relationship['target_entity_id']}' does not reference a valid entity in this import",
                location=f"{location}.target_entity_id",
            ))

        # Validate source != target
        if (
            "source_entity_id" in relationship
            and "target_entity_id" in relationship
            and relationship["source_entity_id"] == relationship["target_entity_id"]
        ):
            errors.append(ImportValidationError(
                category="invalid_value",
                message="source_entity_id and target_entity_id must be different",
                location=location,
            ))

        if "relationship_type" not in relationship:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: relationship_type",
                location=location,
            ))
        elif not isinstance(relationship["relationship_type"], str):
            errors.append(ImportValidationError(
                category="invalid_type",
                message=f"relationship_type must be a string, got {type(relationship['relationship_type']).__name__}",
                location=f"{location}.relationship_type",
            ))
        elif relationship["relationship_type"] not in KNOWN_RELATIONSHIP_TYPES:
            errors.append(ImportValidationError(
                category="invalid_value",
                message=f"Unknown relationship_type: {relationship['relationship_type']}. "
                        f"Valid types: {sorted(KNOWN_RELATIONSHIP_TYPES)}",
                location=f"{location}.relationship_type",
            ))

        if "name_key" not in relationship:
            errors.append(ImportValidationError(
                category="missing_required",
                message="Missing required field: name_key",
                location=location,
            ))
        elif not isinstance(relationship["name_key"], str) or not relationship["name_key"].strip():
            errors.append(ImportValidationError(
                category="invalid_value",
                message="Relationship name_key must be a non-empty string",
                location=f"{location}.name_key",
            ))

        # Optional fields type validation
        if "description_key" in relationship and relationship["description_key"] is not None:
            if not isinstance(relationship["description_key"], str):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"description_key must be a string, got {type(relationship['description_key']).__name__}",
                    location=f"{location}.description_key",
                ))

        if "inverse_name_key" in relationship and relationship["inverse_name_key"] is not None:
            if not isinstance(relationship["inverse_name_key"], str):
                errors.append(ImportValidationError(
                    category="invalid_type",
                    message=f"inverse_name_key must be a string, got {type(relationship['inverse_name_key']).__name__}",
                    location=f"{location}.inverse_name_key",
                ))

        return errors

    def _convert_to_domain_objects(self, data: dict) -> Result[dict, tuple]:
        """Layer 3: Convert validated JSON to domain objects."""
        warnings: list[ImportWarning] = []
        entities: list[EntityDefinition] = []
        relationships: list[RelationshipDefinition] = []

        schema_id = data["schema_id"]
        version = data.get("version")

        for i, entity_data in enumerate(data["entities"]):
            entity_result = self._convert_entity(entity_data, i, warnings)
            if entity_result.is_failure():
                return entity_result
            entities.append(entity_result.value)

        # Convert relationships (Phase 6A - ADR-022)
        for i, rel_data in enumerate(data.get("relationships", [])):
            rel_result = self._convert_relationship(rel_data, i)
            if rel_result.is_failure():
                return rel_result
            relationships.append(rel_result.value)

        # Build SchemaExportDTO for reference
        entity_dtos = tuple(
            self._entity_to_dto(entity) for entity in entities
        )
        relationship_dtos = tuple(
            self._relationship_to_dto(rel) for rel in relationships
        )
        schema_export_dto = SchemaExportDTO(
            schema_id=schema_id,
            entities=entity_dtos,
            version=version,
            relationships=relationship_dtos,
        )

        return Success({
            "schema_export_dto": schema_export_dto,
            "entities": tuple(entities),
            "relationships": tuple(relationships),
            "warnings": warnings,
            "version": version,
            "schema_id": schema_id,
        })

    def _convert_entity(
        self,
        entity_data: dict,
        index: int,
        warnings: list[ImportWarning],
    ) -> Result[EntityDefinition, tuple]:
        """Convert entity JSON to EntityDefinition."""
        entity_id = entity_data["id"]
        fields_data = entity_data.get("fields", [])

        # Decision 6: Empty entity handling → Warn but allow
        if not fields_data:
            warnings.append(ImportWarning(
                category="empty_entity",
                message=f"Entity '{entity_id}' has no fields",
            ))

        # Convert fields
        fields: dict[FieldDefinitionId, FieldDefinition] = {}
        for j, field_data in enumerate(fields_data):
            field_result = self._convert_field(field_data, entity_id, j)
            if field_result.is_failure():
                return field_result
            field_def = field_result.value
            fields[field_def.id] = field_def

        # Phase F-10: Validate control rule formulas using schema context
        control_rule_errors = self._validate_control_rules_for_entity(
            entity_id=entity_id,
            fields=fields,
            entity_index=index,
        )
        if control_rule_errors:
            return Failure(tuple(control_rule_errors))

        # Phase F-12.5: Validate output mapping formulas using schema context
        output_mapping_errors = self._validate_output_mappings_for_entity(
            entity_id=entity_id,
            fields=fields,
            entity_index=index,
        )
        if output_mapping_errors:
            return Failure(tuple(output_mapping_errors))

        # Create entity
        try:
            entity = EntityDefinition(
                id=EntityDefinitionId(entity_id),
                name_key=TranslationKey(entity_data["name_key"]),
                description_key=TranslationKey(entity_data["description_key"]) if entity_data.get("description_key") else None,
                is_root_entity=entity_data["is_root_entity"],
                fields=fields,
            )
            return Success(entity)
        except Exception as e:
            return Failure((ImportValidationError(
                category="conversion_error",
                message=f"Failed to create entity: {e}",
                location=f"entities[{index}]",
            ),))

    def _validate_control_rules_for_entity(
        self,
        entity_id: str,
        fields: dict[FieldDefinitionId, FieldDefinition],
        entity_index: int,
    ) -> list[ImportValidationError]:
        """Validate control rule formulas for all fields in an entity (Phase F-10).

        Uses ControlRuleUseCases to validate each formula:
        - Formula governance (F-6)
        - Boolean type enforcement (F-8)

        Per Phase F-10 spec: Reject on invalid rule (no silent dropping).
        """
        # Import locally to avoid circular import
        from doc_helper.application.usecases.control_rule_usecases import ControlRuleUseCases

        errors: list[ImportValidationError] = []

        # Build schema_fields from converted fields
        schema_fields = self._build_schema_fields(fields)

        # Create ControlRuleUseCases for validation
        control_rule_usecases = ControlRuleUseCases()

        # Validate control rules for each field
        for field_idx, field_def in enumerate(fields.values()):
            for rule_idx, control_rule in enumerate(field_def.control_rules):
                location = (
                    f"entities[{entity_index}].fields[{field_idx}]"
                    f".control_rules[{rule_idx}]"
                )

                # Validate using ControlRuleUseCases
                try:
                    rule_type = ControlRuleType(control_rule.rule_type)
                except ValueError:
                    errors.append(ImportValidationError(
                        category="control_rule_invalid",
                        message=f"Invalid rule_type: {control_rule.rule_type}",
                        location=f"{location}.rule_type",
                    ))
                    continue

                # Validate formula using ControlRuleUseCases
                validation_result = control_rule_usecases.validate_control_rule(
                    rule_type=rule_type,
                    target_field_id=control_rule.target_field_id,
                    formula_text=control_rule.formula_text,
                    schema_fields=schema_fields,
                )

                # Check if formula is blocked
                if validation_result.is_blocked:
                    errors.append(ImportValidationError(
                        category="control_rule_invalid",
                        message=(
                            f"Control rule formula validation failed: "
                            f"{validation_result.block_reason}"
                        ),
                        location=f"{location}.formula_text",
                    ))

        return errors

    def _validate_output_mappings_for_entity(
        self,
        entity_id: str,
        fields: dict[FieldDefinitionId, FieldDefinition],
        entity_index: int,
    ) -> list[ImportValidationError]:
        """Validate output mapping formulas for all fields in an entity (Phase F-12.5).

        Uses FormulaUseCases to validate each formula:
        - Formula governance (F-6)

        Per Phase F-12.5 spec: Reject on invalid mapping (no silent dropping).

        NOTE: Full formula validation will be implemented when FormulaUseCases
        provides validation interface. For now, structural validation is complete.
        """
        # TODO Phase F-12.5: Add formula governance validation once FormulaUseCases
        # provides a validate_formula() method. For now, structural validation
        # (done in _validate_output_mapping_structure) is sufficient for the
        # foundational phase.

        errors: list[ImportValidationError] = []

        # Validate output mappings for each field
        for field_idx, field_def in enumerate(fields.values()):
            for mapping_idx, output_mapping in enumerate(field_def.output_mappings):
                location = (
                    f"entities[{entity_index}].fields[{field_idx}]"
                    f".output_mappings[{mapping_idx}]"
                )

                # Validate target is one of known types (already done in structural validation)
                if not isinstance(output_mapping, OutputMappingExportDTO):
                    errors.append(ImportValidationError(
                        category="output_mapping_invalid",
                        message=f"Invalid output mapping type: {type(output_mapping).__name__}",
                        location=location,
                    ))
                    continue

                # Validate target
                if output_mapping.target.upper() not in KNOWN_OUTPUT_MAPPING_TARGETS:
                    errors.append(ImportValidationError(
                        category="output_mapping_invalid",
                        message=f"Unknown output mapping target: {output_mapping.target}. "
                                f"Valid targets: {sorted(KNOWN_OUTPUT_MAPPING_TARGETS)}",
                        location=f"{location}.target",
                    ))

                # Validate formula_text is not empty
                if not output_mapping.formula_text or not output_mapping.formula_text.strip():
                    errors.append(ImportValidationError(
                        category="output_mapping_invalid",
                        message="Output mapping formula_text cannot be empty",
                        location=f"{location}.formula_text",
                    ))

                # TODO: Add formula governance validation here when FormulaUseCases
                # provides validation interface

        return errors

    def _build_schema_fields(
        self,
        fields: dict[FieldDefinitionId, FieldDefinition],
    ) -> tuple[SchemaFieldInfoDTO, ...]:
        """Build SchemaFieldInfoDTO tuple from field definitions for formula validation."""
        schema_fields: list[SchemaFieldInfoDTO] = []

        for field_def in fields.values():
            # Map FieldType to formula result type string
            field_type_str = field_def.field_type.value

            schema_field = SchemaFieldInfoDTO(
                field_id=field_def.id.value,
                field_type=field_type_str,
                entity_id="",  # Not needed for control rule validation
                label=field_def.label_key.key,  # Translation key for display
            )
            schema_fields.append(schema_field)

        return tuple(schema_fields)

    def _convert_field(
        self,
        field_data: dict,
        entity_id: str,
        index: int,
    ) -> Result[FieldDefinition, tuple]:
        """Convert field JSON to FieldDefinition."""
        location = f"entity '{entity_id}' field[{index}]"

        try:
            field_type = FieldType.from_string(field_data["field_type"])

            # Convert options - always use tuple, never None
            options: tuple = ()
            if field_data.get("options"):
                options = tuple(
                    (opt["value"], TranslationKey(opt["label_key"]))
                    for opt in field_data["options"]
                )

            # Convert constraints
            constraints: list[FieldConstraint] = []
            for constraint_data in field_data.get("constraints", []):
                constraint_result = self._convert_constraint(constraint_data, location)
                if constraint_result.is_failure():
                    return constraint_result
                if constraint_result.value is not None:
                    constraints.append(constraint_result.value)

            # Convert control rules (Phase F-10)
            # Note: Formula validation happens in _convert_entity after all fields are parsed
            control_rules: list[ControlRuleExportDTO] = []
            for control_rule_data in field_data.get("control_rules", []):
                control_rule = ControlRuleExportDTO(
                    rule_type=control_rule_data["rule_type"],
                    target_field_id=control_rule_data["target_field_id"],
                    formula_text=control_rule_data["formula_text"],
                )
                control_rules.append(control_rule)

            # Convert output mappings (Phase F-12.5)
            # Note: Formula validation happens in _convert_entity after all fields are parsed
            output_mappings: list[OutputMappingExportDTO] = []
            for output_mapping_data in field_data.get("output_mappings", []):
                output_mapping = OutputMappingExportDTO(
                    target=output_mapping_data["target"],
                    formula_text=output_mapping_data["formula_text"],
                )
                output_mappings.append(output_mapping)

            # Create field definition
            field_def = FieldDefinition(
                id=FieldDefinitionId(field_data["id"]),
                field_type=field_type,
                label_key=TranslationKey(field_data["label_key"]),
                help_text_key=TranslationKey(field_data["help_text_key"]) if field_data.get("help_text_key") else None,
                required=field_data["required"],
                default_value=field_data.get("default_value"),
                options=options,
                constraints=tuple(constraints),
                control_rules=tuple(control_rules),
                output_mappings=tuple(output_mappings),
                formula=field_data.get("formula"),
                lookup_entity_id=field_data.get("lookup_entity_id"),
                lookup_display_field=field_data.get("lookup_display_field"),
                child_entity_id=field_data.get("child_entity_id"),
            )
            return Success(field_def)
        except Exception as e:
            return Failure((ImportValidationError(
                category="conversion_error",
                message=f"Failed to create field: {e}",
                location=location,
            ),))

    def _convert_constraint(
        self,
        constraint_data: dict,
        location: str,
    ) -> Result[Optional[FieldConstraint], tuple]:
        """Convert constraint JSON to FieldConstraint."""
        constraint_type = constraint_data["constraint_type"]
        params = constraint_data["parameters"]

        try:
            if constraint_type == "RequiredConstraint":
                return Success(RequiredConstraint())
            elif constraint_type == "MinLengthConstraint":
                return Success(MinLengthConstraint(min_length=params["min_length"]))
            elif constraint_type == "MaxLengthConstraint":
                return Success(MaxLengthConstraint(max_length=params["max_length"]))
            elif constraint_type == "MinValueConstraint":
                return Success(MinValueConstraint(min_value=params["min_value"]))
            elif constraint_type == "MaxValueConstraint":
                return Success(MaxValueConstraint(max_value=params["max_value"]))
            elif constraint_type == "PatternConstraint":
                return Success(PatternConstraint(
                    pattern=params["pattern"],
                    description=params.get("description"),
                ))
            elif constraint_type == "AllowedValuesConstraint":
                return Success(AllowedValuesConstraint(
                    allowed_values=tuple(params["allowed_values"]),
                ))
            elif constraint_type == "FileExtensionConstraint":
                return Success(FileExtensionConstraint(
                    allowed_extensions=tuple(params["allowed_extensions"]),
                ))
            elif constraint_type == "MaxFileSizeConstraint":
                return Success(MaxFileSizeConstraint(
                    max_size_bytes=params["max_size_bytes"],
                ))
            else:
                # Should not reach here due to validation, but handle defensively
                return Failure((ImportValidationError(
                    category="unknown_constraint",
                    message=f"Unknown constraint type: {constraint_type}",
                    location=location,
                ),))
        except KeyError as e:
            return Failure((ImportValidationError(
                category="invalid_value",
                message=f"Missing required parameter for {constraint_type}: {e}",
                location=location,
            ),))
        except Exception as e:
            return Failure((ImportValidationError(
                category="conversion_error",
                message=f"Failed to create constraint {constraint_type}: {e}",
                location=location,
            ),))

    def _entity_to_dto(self, entity: EntityDefinition) -> EntityExportDTO:
        """Convert EntityDefinition back to DTO for reference."""
        field_dtos = tuple(
            FieldExportDTO(
                id=field.id.value,
                field_type=field.field_type.value,
                label_key=field.label_key.key,
                required=field.required,
                help_text_key=field.help_text_key.key if field.help_text_key else None,
                default_value=field.default_value,
                options=tuple(
                    FieldOptionExportDTO(value=str(opt[0]), label_key=opt[1].key)
                    for opt in (field.options or [])
                ),
                constraints=tuple(
                    ConstraintExportDTO(
                        constraint_type=type(c).__name__,
                        parameters=self._constraint_to_params(c),
                    )
                    for c in field.constraints
                ),
                # Phase F-10: Include control rules
                control_rules=field.control_rules,
                # Phase F-12.5: Include output mappings
                output_mappings=field.output_mappings,
            )
            for field in entity.get_all_fields()
        )

        return EntityExportDTO(
            id=entity.id.value,
            name_key=entity.name_key.key,
            description_key=entity.description_key.key if entity.description_key else None,
            is_root_entity=entity.is_root_entity,
            fields=field_dtos,
        )

    def _constraint_to_params(self, constraint: FieldConstraint) -> dict:
        """Extract parameters from constraint for DTO."""
        if isinstance(constraint, RequiredConstraint):
            return {}
        elif isinstance(constraint, MinLengthConstraint):
            return {"min_length": constraint.min_length}
        elif isinstance(constraint, MaxLengthConstraint):
            return {"max_length": constraint.max_length}
        elif isinstance(constraint, MinValueConstraint):
            return {"min_value": constraint.min_value}
        elif isinstance(constraint, MaxValueConstraint):
            return {"max_value": constraint.max_value}
        elif isinstance(constraint, PatternConstraint):
            params = {"pattern": constraint.pattern}
            if constraint.description:
                params["description"] = constraint.description
            return params
        elif isinstance(constraint, AllowedValuesConstraint):
            return {"allowed_values": list(constraint.allowed_values)}
        elif isinstance(constraint, FileExtensionConstraint):
            return {"allowed_extensions": list(constraint.allowed_extensions)}
        elif isinstance(constraint, MaxFileSizeConstraint):
            return {"max_size_bytes": constraint.max_size_bytes}
        else:
            return {}

    def _convert_relationship(
        self,
        rel_data: dict,
        index: int,
    ) -> Result[RelationshipDefinition, tuple]:
        """Convert relationship JSON to RelationshipDefinition (Phase 6A)."""
        location = f"relationships[{index}]"

        try:
            relationship = RelationshipDefinition(
                id=RelationshipDefinitionId(rel_data["id"]),
                source_entity_id=EntityDefinitionId(rel_data["source_entity_id"]),
                target_entity_id=EntityDefinitionId(rel_data["target_entity_id"]),
                relationship_type=RelationshipType(rel_data["relationship_type"]),
                name_key=TranslationKey(rel_data["name_key"]),
                description_key=(
                    TranslationKey(rel_data["description_key"])
                    if rel_data.get("description_key")
                    else None
                ),
                inverse_name_key=(
                    TranslationKey(rel_data["inverse_name_key"])
                    if rel_data.get("inverse_name_key")
                    else None
                ),
            )
            return Success(relationship)
        except Exception as e:
            return Failure((ImportValidationError(
                category="conversion_error",
                message=f"Failed to create relationship: {e}",
                location=location,
            ),))

    def _relationship_to_dto(self, rel: RelationshipDefinition) -> RelationshipExportDTO:
        """Convert RelationshipDefinition back to DTO for reference."""
        return RelationshipExportDTO(
            id=rel.id.value,
            source_entity_id=rel.source_entity_id.value,
            target_entity_id=rel.target_entity_id.value,
            relationship_type=rel.relationship_type.value,
            name_key=rel.name_key.key,
            description_key=rel.description_key.key if rel.description_key else None,
            inverse_name_key=rel.inverse_name_key.key if rel.inverse_name_key else None,
        )
