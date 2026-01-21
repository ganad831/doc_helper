"""Command handlers for write operations.

ADR-004: CQRS Pattern
- Commands are write operations that modify state
- Commands return Result[T, E] for explicit error handling
- Commands are stateless (dependencies injected)

ADR-031: Undo History Persistence
- SaveProjectCommand: Persists undo history after save
- OpenProjectCommand: Restores undo history after open
- CloseProjectCommand: Deletes undo history on close
"""

from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.commands.open_project_command import OpenProjectCommand
from doc_helper.application.commands.save_project_command import SaveProjectCommand
from doc_helper.application.commands.close_project_command import CloseProjectCommand
from doc_helper.application.commands.update_field_command import UpdateFieldCommand
from doc_helper.application.commands.delete_project_command import DeleteProjectCommand
from doc_helper.application.commands.generate_document_command import GenerateDocumentCommand
from doc_helper.application.commands.export_project_command import ExportProjectCommand
from doc_helper.application.commands.import_project_command import ImportProjectCommand

__all__ = [
    "CreateProjectCommand",
    "OpenProjectCommand",
    "SaveProjectCommand",
    "CloseProjectCommand",
    "UpdateFieldCommand",
    "DeleteProjectCommand",
    "GenerateDocumentCommand",
    "ExportProjectCommand",
    "ImportProjectCommand",
]
