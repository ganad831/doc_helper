"""Caption generation service for file attachments.

This service generates formatted caption strings by combining:
- Figure numbers (e.g., "Figure 1")
- User-provided caption text (may contain placeholders)
- Prefix/suffix formatting

Placeholder Resolution:
- {label}: Index type label ("Figure", "Image", etc.)
- {number}: Sequence number formatted according to numbering format
- {caption}: User-provided caption text

Examples:
    # Simple caption with prefix/suffix
    format = NumberingFormat(prefix="(", suffix=")")
    caption = "Site overview"
    → "(Figure 1) Site overview"

    # Caption with placeholders
    caption_template = "{label} {number}: {caption}"
    → "Figure 1: Site overview"

    # Roman numerals
    format = NumberingFormat(style=NumberingStyle.ROMAN_UPPER)
    caption = "Cross-section view"
    → "Figure I: Cross-section view"
"""

from dataclasses import dataclass
from typing import Dict, Optional

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.file.value_objects.figure_number import FigureNumber
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.file.value_objects.numbering_format import NumberingFormat


@dataclass
class CaptionGenerationService:
    """Application service for generating formatted captions.

    Combines figure numbers with user caption text and applies formatting.
    """

    def generate_caption(
        self,
        figure_number: FigureNumber,
        user_caption: str,
        numbering_format: NumberingFormat,
    ) -> Result[str, str]:
        """Generate formatted caption string.

        Args:
            figure_number: The assigned figure number
            user_caption: User-provided caption text (may contain placeholders)
            numbering_format: Format specification for the figure number

        Returns:
            Result containing:
            - Success: Formatted caption string
            - Failure: Error message if generation fails

        Example:
            figure_number = FigureNumber(IndexType.FIGURE, 1)
            user_caption = "{label} {number}: Site overview"
            format = NumberingFormat(style=NumberingStyle.ARABIC)

            result = service.generate_caption(figure_number, user_caption, format)
            # Result: "Figure 1: Site overview"
        """
        if not isinstance(figure_number, FigureNumber):
            return Failure(f"figure_number must be FigureNumber, got {type(figure_number)}")

        if not isinstance(numbering_format, NumberingFormat):
            return Failure(f"numbering_format must be NumberingFormat, got {type(numbering_format)}")

        # Format the figure number according to the numbering format
        formatted_number = numbering_format.format_number(figure_number.sequence)

        # Get the index type label
        label = figure_number.index_type.display_name

        # Build placeholder values
        placeholders: Dict[str, str] = {
            "label": label,
            "number": formatted_number,
            "caption": user_caption,
        }

        # If user caption contains placeholders, resolve them
        if "{" in user_caption:
            resolved_caption = self._resolve_placeholders(user_caption, placeholders)
        else:
            # No placeholders, just combine label + number + caption
            resolved_caption = f"{label} {formatted_number}"
            if user_caption:
                resolved_caption += f": {user_caption}"

        return Success(resolved_caption)

    def generate_caption_with_format(
        self,
        figure_number: FigureNumber,
        user_caption: str,
        numbering_format: NumberingFormat,
        caption_prefix: str = "",
        caption_suffix: str = "",
    ) -> Result[str, str]:
        """Generate caption with additional prefix/suffix formatting.

        Args:
            figure_number: The assigned figure number
            user_caption: User-provided caption text
            numbering_format: Format specification for the figure number
            caption_prefix: Prefix to add before caption (e.g., "(")
            caption_suffix: Suffix to add after caption (e.g., ")")

        Returns:
            Result containing:
            - Success: Formatted caption with prefix/suffix
            - Failure: Error message if generation fails

        Example:
            figure_number = FigureNumber(IndexType.FIGURE, 1)
            user_caption = "Site overview"
            format = NumberingFormat()

            result = service.generate_caption_with_format(
                figure_number, user_caption, format,
                caption_prefix="(", caption_suffix=")"
            )
            # Result: "(Figure 1) Site overview"
        """
        # Generate base caption
        base_result = self.generate_caption(figure_number, user_caption, numbering_format)
        if not base_result.is_success:
            return base_result

        base_caption = base_result.value

        # Apply prefix/suffix
        if caption_prefix or caption_suffix:
            # Split into label+number and caption parts if no placeholders
            if not ("{" in user_caption):
                parts = base_caption.split(": ", 1)
                if len(parts) == 2:
                    label_number = parts[0]
                    caption_text = parts[1]
                    formatted = f"{caption_prefix}{label_number}{caption_suffix}"
                    if caption_text:
                        formatted += f" {caption_text}"
                    return Success(formatted)

            # Has placeholders or no caption, just apply prefix/suffix
            return Success(f"{caption_prefix}{base_caption}{caption_suffix}")

        return Success(base_caption)

    def _resolve_placeholders(
        self,
        template: str,
        placeholders: Dict[str, str]
    ) -> str:
        """Resolve placeholders in template string.

        Args:
            template: Template string with {placeholder} markers
            placeholders: Dictionary of placeholder values

        Returns:
            Template with placeholders replaced by values

        Example:
            template = "{label} {number}: {caption}"
            placeholders = {"label": "Figure", "number": "1", "caption": "Overview"}
            → "Figure 1: Overview"
        """
        result = template
        for key, value in placeholders.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def generate_simple_caption(
        self,
        index_type: IndexType,
        sequence: int,
        user_caption: str = "",
    ) -> Result[str, str]:
        """Generate simple caption with default Arabic numbering.

        Convenience method for generating captions with default formatting.

        Args:
            index_type: Type of index (FIGURE, IMAGE, etc.)
            sequence: Sequence number (1-based)
            user_caption: Optional user-provided caption text

        Returns:
            Result containing:
            - Success: Formatted caption (e.g., "Figure 1: Overview")
            - Failure: Error message if generation fails
        """
        if not isinstance(index_type, IndexType):
            return Failure(f"index_type must be IndexType, got {type(index_type)}")

        if sequence < 1:
            return Failure(f"sequence must be >= 1, got {sequence}")

        figure_number = FigureNumber(index_type=index_type, sequence=sequence)
        numbering_format = NumberingFormat()  # Default: Arabic, no prefix/suffix

        return self.generate_caption(figure_number, user_caption, numbering_format)
