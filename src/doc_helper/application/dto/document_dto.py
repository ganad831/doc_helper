"""Document DTOs for UI display.

RULES (AGENT_RULES.md Section 3-4, unified_upgrade_plan.md H2):
- DTOs are immutable (frozen dataclasses)
- DTOs contain NO behavior
- DTOs are UI-facing data only
- NO domain types in DTOs (use string IDs, primitive types)
- NO previous_* fields (those belong in UndoState DTOs)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DocumentFormatDTO:
    """UI-facing document format option for display.

    Represents a document format option in format selection dialogs.
    """

    id: str  # Format ID (e.g., "DOCX", "PDF", "XLSX")
    name: str  # Display name (translated)
    description: str  # Format description (translated)
    extension: str  # File extension (e.g., ".docx")
    is_available: bool  # Whether format is available for current project


@dataclass(frozen=True)
class TemplateDTO:
    """UI-facing template data for display.

    Represents a document template in template selection dialogs.
    """

    id: str  # Template ID as string
    name: str  # Template name (translated)
    description: Optional[str]  # Template description (translated)
    file_path: str  # Template file path
    format: str  # Document format (e.g., "DOCX")
    is_default: bool  # Whether this is the default template


@dataclass(frozen=True)
class GenerationResultDTO:
    """UI-facing document generation result for display.

    Represents the result of a document generation operation.
    """

    success: bool  # Whether generation succeeded
    output_path: Optional[str]  # Path to generated document (if successful)
    error_message: Optional[str]  # Error message (if failed)
    warnings: tuple[str, ...]  # Warning messages
