"""Figure numbering service for calculating sequential figure numbers.

This service orchestrates the calculation of figure numbers for attachments
based on their position and index type. Each index type maintains an independent
counter (Figure 1, 2, 3... vs Image 1, 2, 3...).

RULES:
- Each index type has independent sequential numbering (1, 2, 3...)
- Attachments with exclude_from_index=True do NOT receive numbers
- Position determines numbering order within each index type
- Numbering is calculated on-demand, not stored in attachment entity
"""

from typing import Dict, List

from doc_helper.domain.common.result import Result, Success, Failure
from doc_helper.domain.file.entities.attachment import Attachment
from doc_helper.domain.file.value_objects.figure_number import FigureNumber
from doc_helper.domain.file.value_objects.index_type import IndexType
from doc_helper.domain.file.value_objects.numbering_format import NumberingFormat


class FigureNumberingService:
    """Application service for calculating figure numbers.

    This service implements the figure numbering algorithm:
    1. Group attachments by index_type
    2. Sort each group by position
    3. Filter out excluded attachments
    4. Assign sequential numbers starting from 1

    Example:
        attachments = [
            Attachment(index_type=FIGURE, position=0, exclude_from_index=False),
            Attachment(index_type=IMAGE, position=0, exclude_from_index=False),
            Attachment(index_type=FIGURE, position=1, exclude_from_index=False),
            Attachment(index_type=IMAGE, position=1, exclude_from_index=True),  # Excluded
        ]

        numbers = service.calculate_numbers(attachments)
        # Result:
        # - Attachment 0: Figure 1
        # - Attachment 1: Image 1
        # - Attachment 2: Figure 2
        # - Attachment 3: None (excluded)
    """

    def calculate_numbers(
        self,
        attachments: List[Attachment]
    ) -> Result[Dict[str, FigureNumber], str]:
        """Calculate figure numbers for a list of attachments.

        Args:
            attachments: List of attachments to number

        Returns:
            Result containing:
            - Success: Dict mapping attachment ID (str) to FigureNumber
            - Failure: Error message if input invalid

        Notes:
            - Excluded attachments will NOT appear in result dict
            - Each index type has independent numbering
            - Position determines order within index type
        """
        if not isinstance(attachments, list):
            return Failure("attachments must be a list")

        # Group attachments by index type
        by_type: Dict[IndexType, List[Attachment]] = {}
        for attachment in attachments:
            if not isinstance(attachment, Attachment):
                return Failure(f"All items must be Attachment instances, got {type(attachment)}")

            # Skip excluded attachments
            if attachment.exclude_from_index:
                continue

            index_type = attachment.index_type
            if index_type not in by_type:
                by_type[index_type] = []
            by_type[index_type].append(attachment)

        # Sort each group by position and assign sequential numbers
        result: Dict[str, FigureNumber] = {}

        for index_type, group in by_type.items():
            # Sort by position (ascending)
            sorted_group = sorted(group, key=lambda a: a.position)

            # Assign sequential numbers starting from 1
            for sequence, attachment in enumerate(sorted_group, start=1):
                figure_number = FigureNumber(
                    index_type=index_type,
                    sequence=sequence
                )
                result[str(attachment.id.value)] = figure_number

        return Success(result)

    def format_number(
        self,
        figure_number: FigureNumber,
        format_spec: NumberingFormat
    ) -> Result[str, str]:
        """Format a figure number according to a format specification.

        Args:
            figure_number: The figure number to format
            format_spec: Format specification (style, prefix, suffix)

        Returns:
            Result containing:
            - Success: Formatted string (e.g., "Fig. 5.")
            - Failure: Error message if inputs invalid

        Example:
            number = FigureNumber(index_type=FIGURE, sequence=5)
            format_spec = NumberingFormat(
                style=NumberingStyle.ARABIC,
                prefix="Fig. ",
                suffix="."
            )
            result = service.format_number(number, format_spec)
            # Returns Success("Fig. 5.")
        """
        if not isinstance(figure_number, FigureNumber):
            return Failure(f"figure_number must be FigureNumber, got {type(figure_number)}")

        if not isinstance(format_spec, NumberingFormat):
            return Failure(f"format_spec must be NumberingFormat, got {type(format_spec)}")

        try:
            formatted = format_spec.format_number(figure_number.sequence)
            return Success(formatted)
        except ValueError as e:
            return Failure(f"Formatting failed: {e}")

    def calculate_and_format(
        self,
        attachments: List[Attachment],
        format_specs: Dict[IndexType, NumberingFormat]
    ) -> Result[Dict[str, str], str]:
        """Calculate figure numbers and format them according to per-type specs.

        Args:
            attachments: List of attachments to number
            format_specs: Dict mapping IndexType to NumberingFormat

        Returns:
            Result containing:
            - Success: Dict mapping attachment ID (str) to formatted number string
            - Failure: Error message if calculation or formatting fails

        Example:
            attachments = [...]
            format_specs = {
                IndexType.FIGURE: NumberingFormat(prefix="Fig. ", suffix="."),
                IndexType.IMAGE: NumberingFormat(prefix="Image ", suffix=""),
            }
            result = service.calculate_and_format(attachments, format_specs)
            # Returns Success({"uuid1": "Fig. 1.", "uuid2": "Image 1", ...})
        """
        if not isinstance(format_specs, dict):
            return Failure("format_specs must be a dict")

        # Calculate numbers
        numbers_result = self.calculate_numbers(attachments)
        if not numbers_result.is_success:
            return Failure(f"Number calculation failed: {numbers_result.error}")

        numbers = numbers_result.value

        # Format each number
        formatted: Dict[str, str] = {}

        for attachment_id, figure_number in numbers.items():
            # Get format spec for this index type
            format_spec = format_specs.get(figure_number.index_type)

            if format_spec is None:
                # Use default format if not specified
                format_spec = NumberingFormat()

            # Format the number
            format_result = self.format_number(figure_number, format_spec)
            if not format_result.is_success:
                return Failure(f"Formatting failed for {attachment_id}: {format_result.error}")

            formatted[attachment_id] = format_result.value

        return Success(formatted)

    def get_next_position(
        self,
        attachments: List[Attachment],
        index_type: IndexType
    ) -> Result[int, str]:
        """Calculate the next available position for a new attachment of given type.

        Args:
            attachments: Existing attachments
            index_type: Type of attachment being added

        Returns:
            Result containing:
            - Success: Next position (0 if no attachments of this type exist)
            - Failure: Error message if inputs invalid

        Notes:
            - Position is calculated per index type
            - Returns max(existing_positions) + 1
            - Returns 0 if no attachments of this type exist
        """
        if not isinstance(attachments, list):
            return Failure("attachments must be a list")

        if not isinstance(index_type, IndexType):
            return Failure(f"index_type must be IndexType, got {type(index_type)}")

        # Filter to attachments of this type
        same_type = [a for a in attachments if isinstance(a, Attachment) and a.index_type == index_type]

        if not same_type:
            return Success(0)

        # Find max position
        max_position = max(a.position for a in same_type)
        return Success(max_position + 1)
