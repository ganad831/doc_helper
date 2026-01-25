"""JSON schema exporter for schema export files.

Phase H-4: Application I/O Extraction
Implements ISchemaExportWriter interface for filesystem operations.
All file I/O is contained in infrastructure layer.
"""

import json
from pathlib import Path

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.application.interfaces.schema_export_writer import ISchemaExportWriter
from doc_helper.application.dto.export_dto import SchemaExportDTO


class JsonSchemaExportWriter(ISchemaExportWriter):
    """Writes schema exports to JSON files.

    Phase H-4: Application I/O Extraction
    - Implements ISchemaExportWriter interface
    - Handles all filesystem operations for schema export
    - Application layer delegates file I/O to this class

    Clean Architecture:
    - Infrastructure layer concern (filesystem is external)
    - Implements application layer interface
    - Stateless (no instance state between writes)
    """

    def file_exists(self, file_path: Path) -> bool:
        """Check if a file already exists at the given path.

        Args:
            file_path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        return file_path.exists()

    def write(
        self,
        file_path: Path,
        export_data: SchemaExportDTO,
    ) -> Result[None, str]:
        """Write schema export data to JSON file.

        Creates parent directories if they don't exist.
        Writes JSON with proper encoding and formatting.

        Args:
            file_path: Path where file should be written
            export_data: Schema export DTO to serialize

        Returns:
            Success(None) if written successfully
            Failure(error) if write failed
        """
        try:
            # Convert to dict for JSON serialization
            export_dict = self._export_to_dict(export_data)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_dict, f, indent=2, ensure_ascii=False)

            return Success(None)

        except Exception as e:
            return Failure(f"Failed to write export file: {e}")

    def _export_to_dict(self, export_data: SchemaExportDTO) -> dict:
        """Convert SchemaExportDTO to dict for JSON serialization.

        Args:
            export_data: Export data to convert

        Returns:
            Dict representation for JSON

        Phase F-10: Includes control_rules in field serialization.
        Phase F-12.5: Includes output_mappings in field serialization.
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
                            # Phase F-12.5: Include output mappings
                            "output_mappings": [
                                {
                                    "target": om.target,
                                    "formula_text": om.formula_text,
                                }
                                for om in field.output_mappings
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
