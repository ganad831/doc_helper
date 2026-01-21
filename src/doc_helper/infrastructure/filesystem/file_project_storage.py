"""File-based project storage (.dhproj files)."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId


class FileProjectStorage:
    """File-based storage for projects (.dhproj files).

    Stores projects as JSON files with .dhproj extension.
    Provides save/load operations for portable project files.

    File format:
        {
            "version": "1.0",
            "project_id": "uuid-string",
            "name": "Project Name",
            "app_type_id": "soil_investigation",
            "entity_definition_id": "project",
            "description": "Optional description",
            "created_at": "ISO timestamp",
            "modified_at": "ISO timestamp",
            "field_values": {
                "field_id": {
                    "value": ...,
                    "is_computed": false,
                    "computed_from": null,
                    "is_override": false,
                    "original_computed_value": null
                }
            }
        }

    Example:
        storage = FileProjectStorage()
        result = storage.save(project, "path/to/project.dhproj")
        if isinstance(result, Success):
            print("Project saved")
    """

    VERSION = "1.0"
    # Default app_type_id for backward compatibility with v1 files
    DEFAULT_APP_TYPE_ID = "soil_investigation"

    def save(self, project: Project, file_path: str | Path) -> Result[None, str]:
        """Save project to .dhproj file.

        Args:
            project: Project to save
            file_path: Path to .dhproj file

        Returns:
            Success(None) if saved, Failure(error) otherwise
        """
        if not isinstance(project, Project):
            return Failure("project must be a Project instance")
        if not isinstance(file_path, (str, Path)):
            return Failure("file_path must be a string or Path")

        file_path = Path(file_path)

        # Ensure .dhproj extension
        if file_path.suffix != ".dhproj":
            return Failure("File must have .dhproj extension")

        try:
            # Serialize project to dict
            project_data = {
                "version": self.VERSION,
                "project_id": str(project.id.value),
                "name": project.name,
                "app_type_id": project.app_type_id,
                "entity_definition_id": project.entity_definition_id.value,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "modified_at": project.modified_at.isoformat(),
                "field_values": {
                    field_id.value: {
                        "value": field_value.value,
                        "is_computed": field_value.is_computed,
                        "computed_from": field_value.computed_from,
                        "is_override": field_value.is_override,
                        "original_computed_value": field_value.original_computed_value,
                    }
                    for field_id, field_value in project.field_values.items()
                },
            }

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            return Success(None)

        except OSError as e:
            return Failure(f"File I/O error: {str(e)}")
        except Exception as e:
            return Failure(f"Error saving project: {str(e)}")

    def load(self, file_path: str | Path) -> Result[Project, str]:
        """Load project from .dhproj file.

        Args:
            file_path: Path to .dhproj file

        Returns:
            Success(Project) if loaded, Failure(error) otherwise
        """
        if not isinstance(file_path, (str, Path)):
            return Failure("file_path must be a string or Path")

        file_path = Path(file_path)

        if not file_path.exists():
            return Failure(f"File not found: {file_path}")

        if file_path.suffix != ".dhproj":
            return Failure("File must have .dhproj extension")

        try:
            # Read file
            with open(file_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)

            # Validate version
            version = project_data.get("version")
            if version != self.VERSION:
                return Failure(
                    f"Unsupported file version: {version} (expected {self.VERSION})"
                )

            # Parse project_id
            try:
                project_id = ProjectId(UUID(project_data["project_id"]))
            except (KeyError, ValueError) as e:
                return Failure(f"Invalid project_id: {str(e)}")

            # Parse entity_definition_id
            try:
                entity_definition_id = EntityDefinitionId(
                    project_data["entity_definition_id"]
                )
            except KeyError:
                return Failure("Missing entity_definition_id")

            # Parse field_values
            field_values = {}
            for field_id_str, field_data in project_data.get(
                "field_values", {}
            ).items():
                field_id = FieldDefinitionId(field_id_str)
                field_value = FieldValue(
                    field_id=field_id,
                    value=field_data["value"],
                    is_computed=field_data.get("is_computed", False),
                    computed_from=field_data.get("computed_from"),
                    is_override=field_data.get("is_override", False),
                    original_computed_value=field_data.get("original_computed_value"),
                )
                field_values[field_id] = field_value

            # Parse timestamps
            try:
                created_at = datetime.fromisoformat(project_data["created_at"])
                modified_at = datetime.fromisoformat(project_data["modified_at"])
            except (KeyError, ValueError) as e:
                return Failure(f"Invalid timestamp: {str(e)}")

            # Get app_type_id (default for backward compatibility)
            app_type_id = project_data.get("app_type_id", self.DEFAULT_APP_TYPE_ID)

            # Build Project
            project = Project(
                id=project_id,
                name=project_data["name"],
                app_type_id=app_type_id,
                entity_definition_id=entity_definition_id,
                field_values=field_values,
                description=project_data.get("description"),
                file_path=str(file_path),
                created_at=created_at,
                modified_at=modified_at,
            )

            return Success(project)

        except json.JSONDecodeError as e:
            return Failure(f"Invalid JSON: {str(e)}")
        except OSError as e:
            return Failure(f"File I/O error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading project: {str(e)}")

    def exists(self, file_path: str | Path) -> bool:
        """Check if .dhproj file exists.

        Args:
            file_path: Path to .dhproj file

        Returns:
            True if file exists
        """
        if not isinstance(file_path, (str, Path)):
            return False

        file_path = Path(file_path)
        return file_path.exists() and file_path.suffix == ".dhproj"

    def delete(self, file_path: str | Path) -> Result[None, str]:
        """Delete .dhproj file.

        Args:
            file_path: Path to .dhproj file

        Returns:
            Success(None) if deleted, Failure(error) otherwise
        """
        if not isinstance(file_path, (str, Path)):
            return Failure("file_path must be a string or Path")

        file_path = Path(file_path)

        if not file_path.exists():
            return Failure(f"File not found: {file_path}")

        try:
            file_path.unlink()
            return Success(None)

        except OSError as e:
            return Failure(f"File I/O error: {str(e)}")
        except Exception as e:
            return Failure(f"Error deleting file: {str(e)}")

    def get_project_name(self, file_path: str | Path) -> Result[str, str]:
        """Get project name from .dhproj file without loading full project.

        Args:
            file_path: Path to .dhproj file

        Returns:
            Success(project name) if successful, Failure(error) otherwise
        """
        if not isinstance(file_path, (str, Path)):
            return Failure("file_path must be a string or Path")

        file_path = Path(file_path)

        if not file_path.exists():
            return Failure(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)
                name = project_data.get("name")
                if not name:
                    return Failure("Project name not found in file")
                return Success(name)

        except json.JSONDecodeError as e:
            return Failure(f"Invalid JSON: {str(e)}")
        except OSError as e:
            return Failure(f"File I/O error: {str(e)}")
        except Exception as e:
            return Failure(f"Error reading project name: {str(e)}")
