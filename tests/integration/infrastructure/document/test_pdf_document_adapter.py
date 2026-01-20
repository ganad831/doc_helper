"""Integration tests for PdfDocumentAdapter."""

from pathlib import Path

import pytest

from doc_helper.domain.common.result import Failure, Success
from doc_helper.domain.document.document_format import DocumentFormat
from doc_helper.infrastructure.document.pdf_document_adapter import (
    PdfDocumentAdapter,
)

# Try to import PyMuPDF, skip tests if not available
pytest.importorskip("fitz", reason="PyMuPDF not installed")


class TestPdfDocumentAdapter:
    """Integration tests for PdfDocumentAdapter."""

    @pytest.fixture
    def adapter(self) -> PdfDocumentAdapter:
        """Create adapter instance."""
        return PdfDocumentAdapter()

    @pytest.fixture
    def template_file(self, tmp_path: Path) -> Path:
        """Create a simple PDF template."""
        import fitz

        template_path = tmp_path / "template.pdf"

        # Create a simple PDF document
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test Template", fontsize=12)
        page.insert_text((72, 100), "Project: ", fontsize=12)
        page.insert_text((72, 120), "Date: ", fontsize=12)
        doc.save(str(template_path))
        doc.close()

        return template_path

    def test_adapter_format(self, adapter: PdfDocumentAdapter) -> None:
        """Adapter should report PDF format."""
        assert adapter.format == DocumentFormat.PDF

    def test_validate_template_success(
        self, adapter: PdfDocumentAdapter, template_file: Path
    ) -> None:
        """validate_template should succeed for valid template."""
        result = adapter.validate_template(template_file)
        assert isinstance(result, Success)

    def test_validate_template_not_found(self, adapter: PdfDocumentAdapter) -> None:
        """validate_template should fail for non-existent template."""
        result = adapter.validate_template("nonexistent.pdf")
        assert isinstance(result, Failure)
        assert "not found" in result.error.lower()

    def test_validate_template_invalid_file(
        self, adapter: PdfDocumentAdapter, tmp_path: Path
    ) -> None:
        """validate_template should fail for invalid PDF file."""
        # Create a non-PDF file
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("Not a PDF document")

        result = adapter.validate_template(invalid_file)
        assert isinstance(result, Failure)
        assert "invalid" in result.error.lower()

    def test_generate_document_success(
        self, adapter: PdfDocumentAdapter, template_file: Path, tmp_path: Path
    ) -> None:
        """generate should create output document."""
        output_path = tmp_path / "output.pdf"
        field_values = {"project_name": "Test Project", "date": "2024-01-15"}

        result = adapter.generate(
            template_path=template_file,
            output_path=output_path,
            field_values=field_values,
        )

        assert isinstance(result, Success)
        assert output_path.exists()

    def test_generate_creates_parent_directories(
        self, adapter: PdfDocumentAdapter, template_file: Path, tmp_path: Path
    ) -> None:
        """generate should create parent directories if needed."""
        output_path = tmp_path / "subdir" / "output.pdf"
        field_values = {}

        result = adapter.generate(
            template_path=template_file,
            output_path=output_path,
            field_values=field_values,
        )

        assert isinstance(result, Success)
        assert output_path.exists()
        assert output_path.parent.exists()

    def test_generate_with_invalid_template(
        self, adapter: PdfDocumentAdapter, tmp_path: Path
    ) -> None:
        """generate should fail with invalid template."""
        output_path = tmp_path / "output.pdf"
        field_values = {}

        result = adapter.generate(
            template_path="nonexistent.pdf",
            output_path=output_path,
            field_values=field_values,
        )

        assert isinstance(result, Failure)

    def test_generated_document_is_valid(
        self, adapter: PdfDocumentAdapter, template_file: Path, tmp_path: Path
    ) -> None:
        """Generated document should be a valid PDF."""
        import fitz

        output_path = tmp_path / "output.pdf"
        field_values = {"test_field": "test_value"}

        adapter.generate(
            template_path=template_file,
            output_path=output_path,
            field_values=field_values,
        )

        # Should be able to open the generated document
        doc = fitz.open(str(output_path))
        assert doc is not None
        assert doc.page_count > 0
        doc.close()

    def test_generate_preserves_template_content(
        self, adapter: PdfDocumentAdapter, template_file: Path, tmp_path: Path
    ) -> None:
        """Generated PDF should preserve template content (v1 implementation)."""
        import fitz

        output_path = tmp_path / "output.pdf"
        field_values = {}

        adapter.generate(
            template_path=template_file,
            output_path=output_path,
            field_values=field_values,
        )

        # In v1, PDF adapter just copies the template
        # Verify the output has the same page count as template
        template_doc = fitz.open(str(template_file))
        output_doc = fitz.open(str(output_path))

        assert output_doc.page_count == template_doc.page_count

        template_doc.close()
        output_doc.close()
