"""Document format enumeration."""

from enum import Enum


class DocumentFormat(str, Enum):
    """Document output formats.

    Supported formats for document generation.

    v1 scope:
    - WORD: Microsoft Word (.docx)
    - EXCEL: Microsoft Excel (.xlsx)
    - PDF: Portable Document Format (.pdf)

    Example:
        format = DocumentFormat.WORD
        if format == DocumentFormat.WORD:
            # Generate Word document
    """

    WORD = "word"
    EXCEL = "excel"
    PDF = "pdf"
