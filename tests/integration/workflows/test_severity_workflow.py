"""Integration tests for severity-based workflow control (ADR-025)."""

from pathlib import Path
from uuid import uuid4

import pytest

from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success
from doc_helper.domain.project.field_value import FieldValue
from doc_helper.domain.project.project import Project
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import (
    MaxLengthConstraint,
    MinLengthConstraint,
    RequiredConstraint,
)
from doc_helper.domain.validation.severity import Severity
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.infrastructure.persistence.sqlite_project_repository import (
    SqliteProjectRepository,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create temporary database."""
    return tmp_path / "test.db"


@pytest.fixture
def project_repository(temp_db: Path) -> SqliteProjectRepository:
    """Create SQLite project repository."""
    return SqliteProjectRepository(temp_db)


@pytest.fixture
def entity_definition() -> EntityDefinition:
    """Create entity definition with fields that have different severity constraints."""
    # Field with ERROR-level constraint (required)
    name_field = FieldDefinition(
        id=FieldDefinitionId("name"),
        field_type=FieldType.TEXT,
        label_key=TranslationKey("field.name"),
        required=True,
        constraints=(RequiredConstraint(severity=Severity.ERROR),),
    )

    # Field with WARNING-level constraint (min length)
    description_field = FieldDefinition(
        id=FieldDefinitionId("description"),
        field_type=FieldType.TEXT,
        label_key=TranslationKey("field.description"),
        required=False,
        constraints=(MinLengthConstraint(min_length=10, severity=Severity.WARNING),),
    )

    # Field with INFO-level constraint (max length)
    notes_field = FieldDefinition(
        id=FieldDefinitionId("notes"),
        field_type=FieldType.TEXT,
        label_key=TranslationKey("field.notes"),
        required=False,
        constraints=(MaxLengthConstraint(max_length=100, severity=Severity.INFO),),
    )

    return EntityDefinition(
        id=EntityDefinitionId("test_entity"),
        name_key=TranslationKey("entity.test"),
        fields={
            FieldDefinitionId("name"): name_field,
            FieldDefinitionId("description"): description_field,
            FieldDefinitionId("notes"): notes_field,
        },
    )


class TestSeverityWorkflowIntegration:
    """Integration tests for severity-based workflow control."""

    def test_validation_with_error_severity_blocks_workflow(
        self,
        entity_definition: EntityDefinition,
    ) -> None:
        """ERROR-level validation failures should block workflows.

        ADR-025: ERROR severity blocks workflows unconditionally.
        """
        # Create project with empty required field (ERROR)
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("name"): FieldValue(
                    field_id=FieldDefinitionId("name"),
                    value="",  # Empty required field (ERROR)
                ),
            },
        )

        # Create validation service
        validation_service = ValidationService()

        # Validate project
        result = validation_service.validate_project(project, entity_definition)

        # Verify ERROR is present and blocks workflow
        assert result.is_invalid()
        assert result.has_blocking_errors()
        assert result.blocks_workflow()
        assert len(result.get_errors_by_severity(Severity.ERROR)) == 1

    def test_validation_with_warning_severity_allows_workflow(
        self,
        entity_definition: EntityDefinition,
    ) -> None:
        """WARNING-level validation failures should NOT block workflows.

        ADR-025: WARNING severity allows continuation (user confirmation in UI).
        """
        # Create project with WARNING-level failure (short description)
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("name"): FieldValue(
                    field_id=FieldDefinitionId("name"),
                    value="Valid Name",
                ),
                FieldDefinitionId("description"): FieldValue(
                    field_id=FieldDefinitionId("description"),
                    value="Short",  # Less than 10 chars (WARNING)
                ),
            },
        )

        # Validate project
        validation_service = ValidationService()
        result = validation_service.validate_project(project, entity_definition)

        # Verify WARNING is present but does not block
        assert result.is_invalid()
        assert result.has_warnings()
        assert not result.has_blocking_errors()
        assert not result.blocks_workflow()
        assert len(result.get_errors_by_severity(Severity.WARNING)) == 1

    def test_validation_with_info_severity_allows_workflow(
        self,
        entity_definition: EntityDefinition,
    ) -> None:
        """INFO-level validation failures should NOT block workflows.

        ADR-025: INFO severity is informational only, never blocks.
        """
        # Create project with INFO-level failure (long notes)
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("name"): FieldValue(
                    field_id=FieldDefinitionId("name"),
                    value="Valid Name",
                ),
                FieldDefinitionId("notes"): FieldValue(
                    field_id=FieldDefinitionId("notes"),
                    value="A" * 150,  # More than 100 chars (INFO)
                ),
            },
        )

        # Validate project
        validation_service = ValidationService()
        result = validation_service.validate_project(project, entity_definition)

        # Verify INFO is present but does not block
        assert result.is_invalid()
        assert result.has_info()
        assert not result.has_blocking_errors()
        assert not result.blocks_workflow()
        assert len(result.get_errors_by_severity(Severity.INFO)) == 1

    def test_mixed_severity_validation_blocks_on_error(
        self,
        entity_definition: EntityDefinition,
    ) -> None:
        """Mixed severity failures should block if ANY ERROR exists.

        ADR-025: ERROR takes precedence over WARNING/INFO.
        """
        # Create project with multiple severity failures
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("name"): FieldValue(
                    field_id=FieldDefinitionId("name"),
                    value="",  # Empty required field (ERROR)
                ),
                FieldDefinitionId("description"): FieldValue(
                    field_id=FieldDefinitionId("description"),
                    value="Short",  # WARNING: too short
                ),
                FieldDefinitionId("notes"): FieldValue(
                    field_id=FieldDefinitionId("notes"),
                    value="A" * 150,  # INFO: too long
                ),
            },
        )

        # Validate project
        validation_service = ValidationService()
        result = validation_service.validate_project(project, entity_definition)

        # Verify all severity levels present, but ERROR blocks
        assert result.is_invalid()
        assert result.has_blocking_errors()  # ERROR present
        assert result.has_warnings()  # WARNING present
        assert result.has_info()  # INFO present
        assert result.blocks_workflow()  # Blocks due to ERROR
        assert len(result.get_errors_by_severity(Severity.ERROR)) >= 1

    def test_all_valid_fields_no_blocking(
        self,
        entity_definition: EntityDefinition,
    ) -> None:
        """Valid project should not block any workflows.

        ADR-025: No validation failures = no blocking.
        """
        # Create project with all valid fields
        project = Project(
            id=ProjectId(uuid4()),
            name="Test Project",
            entity_definition_id=entity_definition.id,
            field_values={
                FieldDefinitionId("name"): FieldValue(
                    field_id=FieldDefinitionId("name"),
                    value="Valid Name",
                ),
                FieldDefinitionId("description"): FieldValue(
                    field_id=FieldDefinitionId("description"),
                    value="Valid description with enough length",
                ),
                FieldDefinitionId("notes"): FieldValue(
                    field_id=FieldDefinitionId("notes"),
                    value="Short notes",
                ),
            },
        )

        # Validate project
        validation_service = ValidationService()
        result = validation_service.validate_project(project, entity_definition)

        # Verify no failures
        assert result.is_valid()
        assert not result.has_blocking_errors()
        assert not result.has_warnings()
        assert not result.has_info()
        assert not result.blocks_workflow()
