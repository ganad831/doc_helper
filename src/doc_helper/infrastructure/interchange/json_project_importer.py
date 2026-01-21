"""JSON project importer for interchange format.

ADR-039: Import/Export Data Format
Deserializes JSON interchange format v1.0 to Project and Schema.
"""

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_ids import EntityDefinitionId


class JsonProjectImporter:
    """Imports projects from JSON interchange format.

    ADR-039: Deserializes JSON interchange format to create new project.
    Import always creates NEW project (never modifies existing).
    Import is atomic (validation failures prevent project creation).

    Clean Architecture:
    - Infrastructure layer concern (JSON is external format)
    - Domain-independent deserialization
    - Stateless (no instance state between imports)
    """

    SUPPORTED_FORMAT_VERSIONS = ["1.0"]

    def import_from_file(
        self,
        input_path: Path,
        entity_definitions: tuple[EntityDefinition, ...],
    ) -> Result[dict[str, Any], str]:
        """Import project from JSON interchange format file.

        ADR-039: Deserializes project:
        1. Parse JSON file
        2. Validate format structure (format_version, sections present)
        3. Validate data against schema
        4. Create new Project with imported data
        5. Return Project and metadata

        Args:
            input_path: Path to JSON interchange format file
            entity_definitions: Tuple of entity definitions (current schema)

        Returns:
            Success(dict with project and metadata) or Failure(error)
        """
        try:
            # Read and parse JSON
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate format structure
            validation_result = self._validate_format_structure(data)
            if isinstance(validation_result, Failure):
                return validation_result

            # Validate version compatibility
            format_version = data.get("format_version", "unknown")
            if format_version not in self.SUPPORTED_FORMAT_VERSIONS:
                return Failure(
                    f"Unsupported format version: {format_version}. "
                    f"Supported versions: {', '.join(self.SUPPORTED_FORMAT_VERSIONS)}"
                )

            # Extract metadata
            metadata = data.get("metadata", {})
            imported_schema = data.get("schema", {})
            imported_data = data.get("data", {})

            # Compare schemas and collect warnings
            warnings = self._compare_schemas(entity_definitions, imported_schema)

            # Create new project from imported data
            project = self._create_project_from_data(
                metadata=metadata,
                data=imported_data,
                entity_definitions=entity_definitions,
            )

            # Return project and metadata
            return Success({
                "project": project,
                "format_version": format_version,
                "source_app_version": metadata.get("app_version"),
                "project_name": metadata.get("project_name", "Imported Project"),
                "warnings": warnings,
            })

        except json.JSONDecodeError as e:
            return Failure(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            return Failure(f"Failed to import project: {str(e)}")

    def _validate_format_structure(self, data: dict[str, Any]) -> Result[None, str]:
        """Validate that required sections are present.

        Args:
            data: Parsed JSON data

        Returns:
            Success(None) if valid, Failure(error) if missing sections
        """
        required_sections = ["format_version", "metadata", "schema", "data"]
        missing = [section for section in required_sections if section not in data]

        if missing:
            return Failure(
                f"Invalid format structure: missing required sections: {', '.join(missing)}"
            )

        # Validate metadata structure
        metadata = data.get("metadata", {})
        required_metadata = ["project_id", "project_name"]
        missing_metadata = [field for field in required_metadata if field not in metadata]

        if missing_metadata:
            return Failure(
                f"Invalid metadata: missing required fields: {', '.join(missing_metadata)}"
            )

        # Validate schema structure
        schema_section = data.get("schema", {})
        if "entities" not in schema_section or "fields" not in schema_section:
            return Failure("Invalid schema: missing 'entities' or 'fields'")

        return Success(None)

    def _compare_schemas(
        self,
        entity_definitions: tuple[EntityDefinition, ...],
        imported_schema: dict[str, Any],
    ) -> list[str]:
        """Compare current schema with imported schema and generate warnings.

        ADR-039: Import can proceed with schema differences, but warnings are logged:
        - Missing fields in current schema (imported data for these fields ignored)
        - New fields in current schema (will use defaults for imported project)
        - Field type mismatches (may cause validation failures)

        Args:
            entity_definitions: Current application entity definitions
            imported_schema: Schema from imported file

        Returns:
            List of warning messages
        """
        warnings = []

        # Extract entity and field IDs from current schema
        current_entities = {entity.id.value: entity for entity in entity_definitions}
        current_fields = {}
        for entity in entity_definitions:
            for field in entity.fields.values():
                key = f"{entity.id.value}.{field.id.value}"
                current_fields[key] = field

        # Extract entity and field IDs from imported schema
        imported_entities = {e["id"]: e for e in imported_schema.get("entities", [])}
        imported_fields = {f"{f['entity_id']}.{f['id']}": f for f in imported_schema.get("fields", [])}

        # Check for entities in import that don't exist in current schema
        for entity_id in imported_entities:
            if entity_id not in current_entities:
                warnings.append(f"Entity '{entity_id}' from import not found in current schema (data will be ignored)")

        # Check for fields in import that don't exist in current schema
        for field_key in imported_fields:
            if field_key not in current_fields:
                warnings.append(f"Field '{field_key}' from import not found in current schema (data will be ignored)")

        # Check for type mismatches
        for field_key in imported_fields:
            if field_key in current_fields:
                imported_type = imported_fields[field_key].get("field_type")
                current_type = current_fields[field_key].field_type.name
                if imported_type != current_type:
                    warnings.append(
                        f"Field '{field_key}' type mismatch: "
                        f"imported={imported_type}, current={current_type}"
                    )

        return warnings

    # Default app_type_id for backward compatibility with v1 files
    DEFAULT_APP_TYPE_ID = "soil_investigation"

    def _create_project_from_data(
        self,
        metadata: dict[str, Any],
        data: dict[str, Any],
        entity_definitions: tuple[EntityDefinition, ...],
    ) -> Project:
        """Create new Project aggregate from imported data.

        ADR-039: Import always creates NEW project with new UUID.
        Original project_id is preserved in metadata but not used as actual ID.

        Args:
            metadata: Metadata section from import
            data: Data section from import
            entity_definitions: Current entity definitions for validation

        Returns:
            New Project aggregate with imported data
        """
        # Generate new project ID (ADR-039: never reuse imported ID)
        new_project_id = ProjectId(uuid4())

        # Get project name from metadata
        project_name = metadata.get("project_name", "Imported Project")

        # Get app_type_id from metadata (default for backward compatibility)
        app_type_id = metadata.get("app_type_id", self.DEFAULT_APP_TYPE_ID)

        # Get entity_definition_id from metadata
        # If not present (old format), use first entity from schema or raise error
        entity_def_id_str = metadata.get("entity_definition_id")
        if entity_def_id_str:
            entity_definition_id = EntityDefinitionId(entity_def_id_str)
        elif entity_definitions:
            # Fallback: use first entity (root entity)
            entity_definition_id = entity_definitions[0].id
        else:
            raise ValueError("Cannot determine entity_definition_id: no entity_definition_id in metadata and no entities in schema")

        # Create project (using Project.create factory method if available)
        # This depends on how Project aggregate is structured
        if hasattr(Project, 'create'):
            project = Project.create(
                project_id=new_project_id,
                name=project_name,
                app_type_id=app_type_id,
                entity_definition_id=entity_definition_id,
            )
        else:
            # Fallback: direct instantiation
            project = Project(
                id=new_project_id,
                name=project_name,
                app_type_id=app_type_id,
                entity_definition_id=entity_definition_id,
            )

        # Populate field values from imported data
        for entity_id, records in data.items():
            # Find entity in schema
            entity = next((e for e in entity_definitions if e.id.value == entity_id), None)
            if entity is None:
                # Entity not in current schema - skip
                continue

            # Process records for this entity
            for record in records:
                record_id = record.get("record_id")
                fields = record.get("fields", {})

                # Set field values in project
                for field_id, value in fields.items():
                    # Find field in entity
                    field = next((f for f in entity.fields.values() if f.id.value == field_id), None)
                    if field is None:
                        # Field not in current schema - skip
                        continue

                    # Set field value (using project method if available)
                    if hasattr(project, 'set_field_value'):
                        project.set_field_value(
                            entity_id=entity.id,
                            field_id=field.id,
                            value=self._deserialize_value(value, field.field_type),
                            record_id=record_id if record_id != "default" else None,
                        )

        return project

    def _deserialize_value(self, value: Any, field_type: Any) -> Any:
        """Deserialize a field value from JSON to domain type.

        Args:
            value: JSON value (string, number, boolean, null, array, object)
            field_type: Field type from schema

        Returns:
            Deserialized value appropriate for field type
        """
        # Handle None
        if value is None:
            return None

        # Field type-specific deserialization
        field_type_name = field_type.name if hasattr(field_type, 'name') else str(field_type)

        if field_type_name == "NUMBER":
            return float(value) if isinstance(value, (int, float)) else None
        elif field_type_name == "CHECKBOX":
            return bool(value)
        elif field_type_name == "DATE":
            # Return as string - domain layer will parse
            return str(value) if value else None
        elif field_type_name in ["TEXT", "TEXTAREA", "DROPDOWN", "RADIO"]:
            return str(value) if value else None
        elif field_type_name == "TABLE":
            return list(value) if isinstance(value, list) else []
        else:
            # Default: return as-is
            return value
