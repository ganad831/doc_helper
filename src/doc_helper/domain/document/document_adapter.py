"""Document adapter interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from doc_helper.domain.common.result import Result
from doc_helper.domain.document.document_format import DocumentFormat


class IDocumentAdapter(ABC):
    """Interface for document generation adapters.

    Document adapters handle format-specific document generation.
    Each adapter implements generation for a specific document format
    (Word, Excel, PDF, etc.).

    Adapters receive:
    - Template file path
    - Output file path
    - Field values to insert

    Example:
        adapter = WordDocumentAdapter()
        result = adapter.generate(
            template_path="template.docx",
            output_path="output.docx",
            field_values={"name": "John", "date": "2024-01-15"}
        )
    """

    @property
    @abstractmethod
    def format(self) -> DocumentFormat:
        """Get supported document format.

        Returns:
            Document format this adapter handles
        """
        pass

    @abstractmethod
    def generate(
        self,
        template_path: str | Path,
        output_path: str | Path,
        field_values: dict[str, Any],
    ) -> Result[None, str]:
        """Generate document from template.

        Args:
            template_path: Path to template file
            output_path: Path for generated document
            field_values: Field values to insert (field_name -> value)

        Returns:
            Success(None) if generated, Failure(error) otherwise

        Raises:
            No exceptions - all errors returned as Failure
        """
        pass

    @abstractmethod
    def validate_template(self, template_path: str | Path) -> Result[None, str]:
        """Validate template file.

        Checks if template file exists and is valid for this format.

        Args:
            template_path: Path to template file

        Returns:
            Success(None) if valid, Failure(error) otherwise
        """
        pass
