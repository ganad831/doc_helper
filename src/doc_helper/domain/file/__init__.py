"""File management bounded context.

This context handles:
- File attachments (FILE and IMAGE field types)
- Figure numbering (auto-assignment of sequential numbers)
- Caption generation (labels with placeholders)
- Multiple index types (FIGURE, IMAGE, PLAN, TABLE, APPENDIX)
- Numbering styles (Arabic, Roman, Alpha)

Domain entities:
- Attachment: File reference aggregate

Value objects:
- FigureNumber: Auto-assigned sequential number
- NumberingFormat: Style + prefix + suffix
- IndexType: FIGURE, IMAGE, PLAN, etc.
- NumberingStyle: ARABIC, ROMAN, ALPHA, etc.

Services:
- NumberingService: Figure number calculation
- CaptionService: Caption generation with placeholders
"""

from doc_helper.domain.file.entities.attachment import Attachment
from doc_helper.domain.file.file_ids import AttachmentId
from doc_helper.domain.file.repositories import IAttachmentRepository
from doc_helper.domain.file.value_objects.figure_number import FigureNumber
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.file.value_objects.numbering_format import NumberingFormat
from doc_helper.domain.file.value_objects.numbering_style import NumberingStyle

__all__ = [
    "Attachment",
    "AttachmentId",
    "IAttachmentRepository",
    "FigureNumber",
    "IndexType",
    "NumberingFormat",
    "NumberingStyle",
]
