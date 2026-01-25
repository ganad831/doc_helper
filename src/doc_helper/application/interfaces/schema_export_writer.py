"""Interface for schema export file writing.

Phase H-4: Application I/O Extraction
- Application layer commands MUST NOT perform filesystem I/O
- This interface defines the contract for file writing
- Infrastructure layer provides implementation
"""

from abc import ABC, abstractmethod
from pathlib import Path

from doc_helper.domain.common.result import Result
from doc_helper.application.dto.export_dto import SchemaExportDTO


class ISchemaExportWriter(ABC):
    """Interface for writing schema exports to filesystem.

    Phase H-4: Application I/O Extraction
    - Application commands return pure data structures (DTOs)
    - Infrastructure handles all filesystem operations
    - Commands depend on this interface (Dependency Inversion)

    Clean Architecture:
    - Interface defined in Application layer
    - Implementation in Infrastructure layer
    - Follows Dependency Inversion Principle

    Example:
        writer = JsonSchemaExportWriter()
        result = writer.write(
            file_path=Path("/path/to/export.json"),
            export_data=schema_export_dto
        )
        if result.is_success():
            print("Export written successfully")
    """

    @abstractmethod
    def file_exists(self, file_path: Path) -> bool:
        """Check if a file already exists at the given path.

        Args:
            file_path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def write(
        self,
        file_path: Path,
        export_data: SchemaExportDTO,
    ) -> Result[None, str]:
        """Write schema export data to file.

        Creates parent directories if they don't exist.
        Writes export data as JSON with proper encoding.

        Args:
            file_path: Path where file should be written
            export_data: Schema export DTO to serialize

        Returns:
            Success(None) if written successfully
            Failure(error) if write failed

        Raises:
            No exceptions - all errors returned as Failure
        """
        pass
