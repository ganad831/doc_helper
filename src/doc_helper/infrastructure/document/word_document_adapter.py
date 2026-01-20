"""Word document adapter using python-docx."""

from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml.xmlchemy import BaseOxmlElement

from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.document.document_adapter import IDocumentAdapter
from doc_helper.domain.document.document_format import DocumentFormat


class WordDocumentAdapter(IDocumentAdapter):
    """Word document adapter using python-docx.

    Generates .docx documents by replacing content controls in templates.

    Content controls in Word templates should use field names as tags.
    For example, a content control tagged "project_name" will be replaced
    with the value of field_values["project_name"].

    Example:
        adapter = WordDocumentAdapter()
        result = adapter.generate(
            template_path="template.docx",
            output_path="output.docx",
            field_values={"project_name": "Soil Investigation Project"}
        )
    """

    @property
    def format(self) -> DocumentFormat:
        return DocumentFormat.WORD

    def generate(
        self,
        template_path: str | Path,
        output_path: str | Path,
        field_values: dict[str, Any],
    ) -> Result[None, str]:
        """Generate Word document from template.

        Args:
            template_path: Path to .docx template
            output_path: Path for generated .docx document
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
            # Load template
            doc = Document(str(template_path))

            # Replace content controls
            self._replace_content_controls(doc, field_values)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save document
            doc.save(str(output_path))

            return Success(None)

        except Exception as e:
            return Failure(f"Error generating Word document: {str(e)}")

    def validate_template(self, template_path: str | Path) -> Result[None, str]:
        """Validate Word template.

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

        if template_path.suffix.lower() != ".docx":
            return Failure(f"Template must be .docx file: {template_path}")

        # Try to load document
        try:
            Document(str(template_path))
            return Success(None)
        except Exception as e:
            return Failure(f"Invalid Word document: {str(e)}")

    def _replace_content_controls(
        self, doc: Document, field_values: dict[str, Any]
    ) -> None:
        """Replace content controls in document.

        Args:
            doc: Document object
            field_values: Field values to insert
        """
        # Search for content controls in body
        for element in doc.element.body.iter():
            if isinstance(element, BaseOxmlElement):
                # Find structured document tags (content controls)
                for sdt in element.findall(
                    ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sdt"
                ):
                    self._replace_sdt(sdt, field_values)

    def _replace_sdt(
        self, sdt: BaseOxmlElement, field_values: dict[str, Any]
    ) -> None:
        """Replace single structured document tag (content control).

        Args:
            sdt: SDT XML element
            field_values: Field values to insert
        """
        # Get tag name from sdtPr
        tag_element = sdt.find(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tag"
        )

        if tag_element is None:
            return

        tag_name = tag_element.get(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
        )

        if not tag_name or tag_name not in field_values:
            return

        # Get the content element
        content_element = sdt.find(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sdtContent"
        )

        if content_element is None:
            return

        # Find text run
        text_element = content_element.find(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
        )

        if text_element is not None:
            # Replace text with field value
            value = field_values[tag_name]
            text_element.text = str(value) if value is not None else ""
