"""JSON project exporter for interchange format.

ADR-039: Import/Export Data Format
Serializes Project and Schema to JSON interchange format v1.0.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.schema.entity_definition import EntityDefinition


class JsonProjectExporter:
    """Exports projects to JSON interchange format.

    ADR-039: Serializes complete project (schema + data) to JSON file.
    Format version 1.0 with four sections:
    - format_version: Version identifier
    - metadata: Project metadata (IDs, timestamps, versions)
    - schema: Complete schema structure (entities, fields)
    - data: All field values organized by entity

    Clean Architecture:
    - Infrastructure layer concern (JSON is external format)
    - Domain-independent (no domain types in JSON)
    - Stateless (no instance state between exports)
    """

    FORMAT_VERSION = "1.0"
    APP_VERSION = "1.0.0"  # TODO: Load from application version config

    def export_to_file(
        self,
        project: Project,
        entity_definitions: tuple[EntityDefinition, ...],
        output_path: Path,
    ) -> Result[dict[str, Any], str]:
        """Export project to JSON interchange format file.

        ADR-039: Serializes project as:
        1. Format version (for compatibility)
        2. Metadata (project info, timestamps, versions)
        3. Schema (entities, fields, validation rules)
        4. Data (all field values for all entities)

        Args:
            project: Project to export
            entity_definitions: Tuple of entity definitions from schema
            output_path: Path where JSON file will be written

        Returns:
            Success(metadata_dict) with counts, or Failure(error)
        """
        try:
            # Build JSON structure
            export_data = self._build_export_structure(project, entity_definitions)

            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            # Count exported items
            entity_count = len(export_data["schema"]["entities"])
            record_count = sum(len(records) for records in export_data["data"].values())
            field_value_count = sum(
                len(record["fields"])
                for records in export_data["data"].values()
                for record in records
            )

            # Return metadata
            return Success({
                "format_version": self.FORMAT_VERSION,
                "entity_count": entity_count,
                "record_count": record_count,
                "field_value_count": field_value_count,
            })

        except Exception as e:
            return Failure(f"Failed to export project: {str(e)}")

    def _build_export_structure(
        self,
        project: Project,
        entity_definitions: tuple[EntityDefinition, ...],
    ) -> dict[str, Any]:
        """Build complete export JSON structure.

        Args:
            project: Project to export
            entity_definitions: Tuple of entity definitions

        Returns:
            Complete JSON structure per ADR-039 specification
        """
        now = datetime.now(timezone.utc).isoformat()

        return {
            "format_version": self.FORMAT_VERSION,
            "metadata": self._build_metadata(project, now),
            "schema": self._build_schema_section(entity_definitions),
            "data": self._build_data_section(project, entity_definitions),
        }

    def _build_metadata(self, project: Project, exported_at: str) -> dict[str, Any]:
        """Build metadata section.

        Args:
            project: Project to export
            exported_at: ISO-8601 timestamp of export

        Returns:
            Metadata dict per ADR-039 specification
        """
        return {
            "project_id": str(project.id.value),
            "project_name": project.name,
            "app_type_id": project.app_type_id,
            "entity_definition_id": project.entity_definition_id.value,
            "created_at": project.created_at.isoformat() if hasattr(project, 'created_at') else exported_at,
            "modified_at": project.modified_at.isoformat() if hasattr(project, 'modified_at') else exported_at,
            "app_version": self.APP_VERSION,
            "exported_at": exported_at,
            "exported_by": f"Doc Helper {self.APP_VERSION}",
        }

    def _build_schema_section(self, entity_definitions: tuple[EntityDefinition, ...]) -> dict[str, Any]:
        """Build schema section with entities and fields.

        Args:
            entity_definitions: Tuple of entity definitions

        Returns:
            Schema dict per ADR-039 specification
        """
        entities = []
        fields = []

        for entity in entity_definitions:
            # Add entity definition
            entities.append({
                "id": entity.id.value,
                "name": entity.name,
                "description": entity.description or "",
                "entity_type": entity.entity_type.name,  # SINGLETON or COLLECTION
            })

            # Add field definitions for this entity
            for field in entity.fields.values():
                field_def = {
                    "id": field.id.value,
                    "entity_id": entity.id.value,
                    "label": field.label_key.key if field.label_key else "",
                    "field_type": field.field_type.name,
                    "required": field.required,
                }

                # Add validation rules if present
                if field.validation_rules:
                    field_def["validation_rules"] = self._serialize_validation_rules(field.validation_rules)

                # Add options for dropdown/radio/checkbox fields
                if hasattr(field, 'options') and field.options:
                    field_def["options"] = [
                        {"value": opt.value, "label": opt.label}
                        for opt in field.options
                    ]

                # Add formula for calculated fields
                if hasattr(field, 'formula') and field.formula:
                    field_def["formula"] = field.formula

                fields.append(field_def)

        return {
            "entities": entities,
            "fields": fields,
        }

    def _serialize_validation_rules(self, rules: Any) -> dict[str, Any]:
        """Serialize validation rules to JSON-compatible dict.

        Args:
            rules: Validation rules from field definition

        Returns:
            Dictionary of validation constraints
        """
        # Convert validation rules to JSON-serializable format
        result = {}

        if hasattr(rules, '__dict__'):
            for key, value in rules.__dict__.items():
                if not key.startswith('_') and value is not None:
                    result[key] = value

        return result

    def _build_data_section(self, project: Project, entity_definitions: tuple[EntityDefinition, ...]) -> dict[str, Any]:
        """Build data section with all field values.

        Args:
            project: Project with field values
            entity_definitions: Tuple of entity definitions

        Returns:
            Data dict organized by entity ID per ADR-039 specification
        """
        data = {}

        for entity in entity_definitions:
            entity_id = entity.id.value
            records = []

            # Get records for this entity from project
            if entity.entity_type.name == "SINGLETON":
                # Single record with ID "default"
                record_data = self._extract_field_values(project, entity)
                if record_data:
                    records.append({
                        "record_id": "default",
                        "fields": record_data,
                    })
            else:
                # Multiple records (COLLECTION)
                # Get records from project - implementation depends on how project stores collection data
                entity_records = self._get_entity_records(project, entity)
                for record_id, field_values in entity_records.items():
                    records.append({
                        "record_id": record_id,
                        "fields": field_values,
                    })

            if records:
                data[entity_id] = records

        return data

    def _extract_field_values(self, project: Project, entity: Any) -> dict[str, Any]:
        """Extract field values for an entity from project.

        Args:
            project: Project with field values
            entity: Entity definition

        Returns:
            Dictionary of field_id → value
        """
        field_values = {}

        for field in entity.fields.values():
            field_id = field.id.value

            # Get value from project - this depends on how project stores values
            # Assuming project has a get_field_value method
            if hasattr(project, 'get_field_value'):
                value = project.get_field_value(entity.id, field_id)
                if value is not None:
                    field_values[field_id] = self._serialize_value(value)

        return field_values

    def _get_entity_records(self, project: Project, entity: Any) -> dict[str, dict[str, Any]]:
        """Get all records for a collection entity.

        Args:
            project: Project with field values
            entity: Entity definition

        Returns:
            Dictionary mapping record_id → field_values_dict
        """
        # This depends on how project stores collection data
        # Assuming project has a method to get records for an entity
        records = {}

        if hasattr(project, 'get_entity_records'):
            entity_records = project.get_entity_records(entity.id)
            for record in entity_records:
                record_id = str(record.id.value) if hasattr(record, 'id') else str(record)
                field_values = {}
                for field in entity.fields.values():
                    value = record.get(field.id.value) if isinstance(record, dict) else getattr(record, field.id.value, None)
                    if value is not None:
                        field_values[field.id.value] = self._serialize_value(value)
                records[record_id] = field_values

        return records

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a field value to JSON-compatible type.

        Args:
            value: Field value from domain

        Returns:
            JSON-serializable value (string, number, boolean, null, array, object)
        """
        # Handle None
        if value is None:
            return None

        # Handle basic types
        if isinstance(value, (str, int, float, bool)):
            return value

        # Handle datetime
        if hasattr(value, 'isoformat'):
            return value.isoformat()

        # Handle lists
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]

        # Handle dicts
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}

        # Handle value objects with .value attribute
        if hasattr(value, 'value'):
            return self._serialize_value(value.value)

        # Default: convert to string
        return str(value)
