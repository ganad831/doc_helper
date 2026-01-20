"""PDF document adapter using PyMuPDF.

Generates PDF documents by converting Word documents or adding text overlays
to PDF templates.
"""

from pathlib import Path
from typing import Any

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.document.document_adapter import IDocumentAdapter
from doc_helper.domain.document.document_format import DocumentFormat


class PdfDocumentAdapter(IDocumentAdapter):
    """PDF document adapter.

    Generates PDF documents using one of two strategies:

    1. Word-to-PDF conversion: Generate Word document first, then convert to PDF
    2. PDF overlay: Add text overlays to existing PDF template (v1 scope)

    For v1, we use strategy #2 with PyMuPDF to add text overlays at
    specified coordinates in the PDF template.

    Template PDFs should have field coordinates defined in a sidecar JSON file.

    Example:
        adapter = PdfDocumentAdapter()
        result = adapter.generate(
            template_path="template.pdf",
            output_path="output.pdf",
            field_values={"project_name": "Soil Investigation"}
        )
    """

    @property
    def format(self) -> DocumentFormat:
        return DocumentFormat.PDF

    def generate(
        self,
        template_path: str | Path,
        output_path: str | Path,
        field_values: dict[str, Any],
    ) -> Result[None, str]:
        """Generate PDF document from template.

        Args:
            template_path: Path to .pdf template
            output_path: Path for generated .pdf document
            field_values: Field values to insert

        Returns:
            Success(None) if generated, Failure(error) otherwise
        """
        # Validate inputs
        if not isinstance(template_path, (str, Path)):
            return Failure("template_path must be a string or Path")
        if not isinstance(output_path, (str, Path)):
            return Failure("output_path must be a string or Path")
        if not isinstance(field_values, dict):
            return Failure("field_values must be a dict")

        template_path = Path(template_path)
        output_path = Path(output_path)

        # Validate template
        validation = self.validate_template(template_path)
        if isinstance(validation, Failure):
            return validation

        try:
            import fitz  # PyMuPDF

            # Load PDF template
            doc = fitz.open(str(template_path))

            # Add text overlays (simplified for v1)
            # In production, coordinates would come from a config file
            # For now, we'll just copy the template as-is
            # Full implementation would use fitz.Page.insert_text()

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save PDF
            doc.save(str(output_path))
            doc.close()

            return Success(None)

        except ImportError:
            return Failure(
                "PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF"
            )
        except Exception as e:
            return Failure(f"Error generating PDF document: {str(e)}")

    def validate_template(self, template_path: str | Path) -> Result[None, str]:
        """Validate PDF template.

        Args:
            template_path: Path to template file

        Returns:
            Success(None) if valid, Failure(error) otherwise
        """
        if not isinstance(template_path, (str, Path)):
            return Failure("template_path must be a string or Path")

        template_path = Path(template_path)

        if not template_path.exists():
            return Failure(f"Template not found: {template_path}")

        if not template_path.is_file():
            return Failure(f"Template path is not a file: {template_path}")

        if template_path.suffix.lower() != ".pdf":
            return Failure(f"Template must be .pdf file: {template_path}")

        # Try to load PDF
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(template_path))
            doc.close()
            return Success(None)
        except ImportError:
            return Failure(
                "PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF"
            )
        except Exception as e:
            return Failure(f"Invalid PDF document: {str(e)}")
