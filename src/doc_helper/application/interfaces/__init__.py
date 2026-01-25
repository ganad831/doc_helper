"""Application layer interfaces (output ports).

These interfaces define contracts for infrastructure services used by the application layer.
Infrastructure layer provides concrete implementations.

Phase H-4: Application I/O Extraction
- Interfaces for file I/O operations
- Commands use interfaces, infrastructure implements
"""

from doc_helper.application.interfaces.schema_export_writer import ISchemaExportWriter

__all__ = [
    "ISchemaExportWriter",
]
