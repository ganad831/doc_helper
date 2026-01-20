"""Recent projects storage for tracking recently accessed projects."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from doc_helper.application.dto.project_dto import ProjectSummaryDTO
from doc_helper.domain.common.result import Failure, Result, Success


class RecentProjectsStorage:
    """Tracks recently accessed projects for quick reopening.

    Stores a list of recently accessed projects (last 5) in a JSON file.
    Projects are ordered by most recent access first.

    File format:
        {
            "version": "1.0",
            "projects": [
                {
                    "id": "project-id",
                    "name": "Project Name",
                    "file_path": "/path/to/project.dhproj",
                    "is_saved": true,
                    "last_accessed": "ISO timestamp"
                },
                ...
            ]
        }

    Example:
        storage = RecentProjectsStorage("config/recent_projects.json")
        storage.add(project_summary)
        recent = storage.get_recent()
    """

    VERSION = "1.0"
    MAX_RECENT_PROJECTS = 5

    def __init__(self, file_path: str | Path) -> None:
        """Initialize recent projects storage.

        Args:
            file_path: Path to JSON file for storing recent projects
        """
        self._file_path = Path(file_path)

    def add(
        self, project_summary: ProjectSummaryDTO
    ) -> Result[None, str]:
        """Add project to recent projects list.

        If project already exists in list, moves it to top.
        If list exceeds MAX_RECENT_PROJECTS, removes oldest entry.

        Args:
            project_summary: Project summary to add

        Returns:
            Success(None) if added, Failure(error) otherwise
        """
        if not isinstance(project_summary, ProjectSummaryDTO):
            return Failure("project_summary must be a ProjectSummaryDTO instance")

        # Load existing recent projects
        load_result = self.get_recent()
        if isinstance(load_result, Failure):
            # If file doesn't exist or is invalid, start fresh
            recent_projects = []
        else:
            recent_projects = load_result.value

        # Remove project if it already exists (will be re-added at top)
        recent_projects = [
            p for p in recent_projects if p["id"] != project_summary.id
        ]

        # Add new project at top with current timestamp
        new_entry = {
            "id": project_summary.id,
            "name": project_summary.name,
            "file_path": project_summary.file_path,
            "is_saved": project_summary.is_saved,
            "last_accessed": datetime.now().isoformat(),
        }
        recent_projects.insert(0, new_entry)

        # Limit to MAX_RECENT_PROJECTS
        recent_projects = recent_projects[: self.MAX_RECENT_PROJECTS]

        # Save to file
        return self._save(recent_projects)

    def get_recent(self) -> Result[List[dict], str]:
        """Get list of recent projects.

        Returns:
            Success(list of dicts) if successful, Failure(error) otherwise

        Note:
            Returns list of dicts (not ProjectSummaryDTO) to avoid coupling
            infrastructure to application DTOs for serialization.
        """
        if not self._file_path.exists():
            # No recent projects file yet - return empty list
            return Success([])

        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate version
            version = data.get("version")
            if version != self.VERSION:
                return Failure(
                    f"Unsupported file version: {version} (expected {self.VERSION})"
                )

            projects = data.get("projects", [])
            return Success(projects)

        except json.JSONDecodeError as e:
            return Failure(f"Invalid JSON: {str(e)}")
        except OSError as e:
            return Failure(f"File I/O error: {str(e)}")
        except Exception as e:
            return Failure(f"Error loading recent projects: {str(e)}")

    def remove(self, project_id: str) -> Result[None, str]:
        """Remove project from recent projects list.

        Args:
            project_id: ID of project to remove

        Returns:
            Success(None) if removed, Failure(error) otherwise
        """
        if not isinstance(project_id, str):
            return Failure("project_id must be a string")

        # Load existing recent projects
        load_result = self.get_recent()
        if isinstance(load_result, Failure):
            return load_result  # Propagate error

        recent_projects = load_result.value

        # Remove project
        recent_projects = [p for p in recent_projects if p["id"] != project_id]

        # Save to file
        return self._save(recent_projects)

    def clear(self) -> Result[None, str]:
        """Clear all recent projects.

        Returns:
            Success(None) if cleared, Failure(error) otherwise
        """
        return self._save([])

    def cleanup_missing(self) -> Result[int, str]:
        """Remove projects whose files no longer exist.

        Returns:
            Success(count of removed projects) if successful, Failure(error) otherwise
        """
        # Load existing recent projects
        load_result = self.get_recent()
        if isinstance(load_result, Failure):
            return load_result  # Propagate error

        recent_projects = load_result.value
        original_count = len(recent_projects)

        # Filter out projects with missing files
        recent_projects = [
            p
            for p in recent_projects
            if p.get("file_path") and Path(p["file_path"]).exists()
        ]

        removed_count = original_count - len(recent_projects)

        # Save updated list
        save_result = self._save(recent_projects)
        if isinstance(save_result, Failure):
            return save_result

        return Success(removed_count)

    def _save(self, recent_projects: List[dict]) -> Result[None, str]:
        """Save recent projects list to file.

        Args:
            recent_projects: List of project dicts to save

        Returns:
            Success(None) if saved, Failure(error) otherwise
        """
        try:
            # Create parent directories if needed
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            # Serialize to JSON
            data = {"version": self.VERSION, "projects": recent_projects}

            # Write to file
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return Success(None)

        except OSError as e:
            return Failure(f"File I/O error: {str(e)}")
        except Exception as e:
            return Failure(f"Error saving recent projects: {str(e)}")
