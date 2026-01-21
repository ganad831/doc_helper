"""E2E Workflow 3: Validation workflow.

Tests complete validation workflow using real validators and repositories.

Test Coverage:
- Required field validation (blocking)
- Numeric constraints (min/max values)
- Text constraints (min/max length, pattern)
- Form-wide validity status
- Validation with multiple constraints per field
- Validation blocking operations (save, generate)
"""

import pytest
from pathlib import Path
from uuid import UUID

from doc_helper.application.commands.create_project_command import CreateProjectCommand
from doc_helper.application.commands.update_field_command import UpdateFieldCommand
from doc_helper.application.services.validation_service import ValidationService
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.project.project_ids import ProjectId
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.validation.constraints import (
    RequiredConstraint,
    MinLengthConstraint,
    MaxLengthConstraint,
    MinValueConstraint,
    MaxValueConstraint,
    PatternConstraint,
)
from doc_helper.infrastructure.persistence.sqlite_project_repository import (
    SqliteProjectRepository,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create temporary database file."""
    db_path = tmp_path / "test_validation_e2e.db"
    db_path.touch(exist_ok=True)
    return db_path


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create temporary project directory."""
    project_dir = tmp_path / "projects"
    project_dir.mkdir(exist_ok=True)
    return project_dir


@pytest.fixture
def test_schema() -> EntityDefinition:
    """Create test schema with various validation constraints."""
    fields = {
        # Required TEXT field
        FieldDefinitionId("project_name"): FieldDefinition(
            id=FieldDefinitionId("project_name"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.project_name"),
            required=True,
            constraints=(RequiredConstraint(),),
        ),
        # TEXT field with min/max length
        FieldDefinitionId("description"): FieldDefinition(
            id=FieldDefinitionId("description"),
            field_type=FieldType.TEXTAREA,
            label_key=TranslationKey("field.description"),
            required=False,
            constraints=(
                MinLengthConstraint(min_length=10),
                MaxLengthConstraint(max_length=200),
            ),
        ),
        # NUMBER field with min/max value
        FieldDefinitionId("sample_count"): FieldDefinition(
            id=FieldDefinitionId("sample_count"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.sample_count"),
            required=True,
            constraints=(
                RequiredConstraint(),
                MinValueConstraint(min_value=1),
                MaxValueConstraint(max_value=100),
            ),
        ),
        # TEXT field with pattern constraint (phone number format)
        FieldDefinitionId("contact_phone"): FieldDefinition(
            id=FieldDefinitionId("contact_phone"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.contact_phone"),
            required=False,
            constraints=(
                PatternConstraint(
                    pattern=r"^\d{3}-\d{3}-\d{4}$",
                    description="Phone number (XXX-XXX-XXXX)",
                ),
            ),
        ),
        # Optional TEXT field (no constraints)
        FieldDefinitionId("optional_notes"): FieldDefinition(
            id=FieldDefinitionId("optional_notes"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.optional_notes"),
            required=False,
            constraints=(),
        ),
    }

    entity_def = EntityDefinition(
        id=EntityDefinitionId("validation_test_entity"),
        name_key=TranslationKey("entity.validation_test"),
        fields=fields,
    )

    return entity_def


class TestValidationWorkflow:
    """E2E tests for Workflow 3: Validation workflow."""

    def test_required_field_validation(
        self, temp_db: Path, temp_project_dir: Path, test_schema: EntityDefinition
    ) -> None:
        """Test required field validation workflow.

        Workflow:
        1. Create project
        2. Attempt to save without required field (should fail validation)
        3. Set required field value
        4. Validation should pass
        """
        print("\n" + "=" * 70)
        print("TEST: Required Field Validation")
        print("=" * 70)

        # Step 1: Create project
        print("\nStep 1: Create Project")
        project_repo = SqliteProjectRepository(temp_db)
        create_command = CreateProjectCommand(project_repository=project_repo)

        create_result = create_command.execute(
            name="Validation Test Project",
            entity_definition_id=EntityDefinitionId("validation_test_entity"),
            description="Testing required field validation",
        )
        assert isinstance(create_result, Success)
        project_id = create_result.value
        print(f"   ✓ Project created: {project_id.value}")

        # Step 2: Set required fields to None (empty) to trigger validation
        print("\nStep 2: Set Required Fields to None (Empty)")
        update_command = UpdateFieldCommand(project_repository=project_repo)

        result1 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("project_name"),
            value=None,  # Empty required field
        )
        assert isinstance(result1, Success)
        print("   ✓ Set project_name = None")

        result2 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("sample_count"),
            value=None,  # Empty required field
        )
        assert isinstance(result2, Success)
        print("   ✓ Set sample_count = None")

        # Step 3: Validate with empty required fields
        print("\nStep 3: Validate with Empty Required Fields")
        validation_service = ValidationService()

        # Load project
        project_result = project_repo.get_by_id(project_id)
        assert isinstance(project_result, Success)
        project = project_result.value

        # Validate (should have 2 errors: project_name and sample_count empty)
        validation_result = validation_service.validate_project(project, test_schema)

        print(f"   - Validation result: {validation_result.error_count} errors")
        assert validation_result.is_invalid()
        assert validation_result.error_count == 2
        print("   ✓ Validation failed as expected (2 required fields empty)")

        # Check specific field errors
        assert validation_result.has_errors_for_field("project_name")
        assert validation_result.has_errors_for_field("sample_count")
        print("   ✓ Errors detected for 'project_name' and 'sample_count'")

        # Step 4: Set required field values
        print("\nStep 4: Set Required Field Values")

        result3 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("project_name"),
            value="Valid Project Name",
        )
        assert isinstance(result3, Success)
        print("   ✓ Set project_name = 'Valid Project Name'")

        result4 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("sample_count"),
            value=50,
        )
        assert isinstance(result4, Success)
        print("   ✓ Set sample_count = 50")

        # Step 5: Revalidate (should pass)
        print("\nStep 5: Revalidate")
        project_result2 = project_repo.get_by_id(project_id)
        assert isinstance(project_result2, Success)
        project2 = project_result2.value

        validation_result2 = validation_service.validate_project(project2, test_schema)

        print(f"   - Validation result: {validation_result2.error_count} errors")
        assert validation_result2.is_valid()
        assert validation_result2.error_count == 0
        print("   ✓ Validation passed with all required fields set")

        print("\n" + "=" * 70)
        print("✓ REQUIRED FIELD VALIDATION TEST PASSED")
        print("=" * 70)

    def test_length_constraint_validation(
        self, temp_db: Path, temp_project_dir: Path, test_schema: EntityDefinition
    ) -> None:
        """Test min/max length constraint validation.

        Workflow:
        1. Create project
        2. Set description too short (< 10 chars)
        3. Validation should fail
        4. Set description within valid range
        5. Validation should pass
        6. Set description too long (> 200 chars)
        7. Validation should fail
        """
        print("\n" + "=" * 70)
        print("TEST: Length Constraint Validation")
        print("=" * 70)

        # Step 1: Create project
        print("\nStep 1: Create Project with Required Fields")
        project_repo = SqliteProjectRepository(temp_db)
        create_command = CreateProjectCommand(project_repository=project_repo)

        create_result = create_command.execute(
            name="Length Test Project",
            entity_definition_id=EntityDefinitionId("validation_test_entity"),
        )
        assert isinstance(create_result, Success)
        project_id = create_result.value

        # Set required fields to pass basic validation
        update_command = UpdateFieldCommand(project_repository=project_repo)

        update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("project_name"),
            value="Project Name",
        )
        update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("sample_count"),
            value=50,
        )
        print("   ✓ Required fields set")

        validation_service = ValidationService()

        # Step 2: Set description too short
        print("\nStep 2: Set Description Too Short (< 10 chars)")
        result = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("description"),
            value="Short",  # Only 5 characters
        )
        assert isinstance(result, Success)
        print("   ✓ Set description = 'Short' (5 chars)")

        # Validate
        project_result = project_repo.get_by_id(project_id)
        assert isinstance(project_result, Success)
        validation_result = validation_service.validate_project(
            project_result.value, test_schema
        )

        print(f"   - Validation result: {validation_result.error_count} errors")
        assert validation_result.is_invalid()
        assert validation_result.has_errors_for_field("description")
        print("   ✓ Validation failed for description (too short)")

        # Step 3: Set description within valid range
        print("\nStep 3: Set Description Within Valid Range (10-200 chars)")
        result2 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("description"),
            value="This is a valid description with sufficient length.",  # 52 chars
        )
        assert isinstance(result2, Success)
        print("   ✓ Set description = 'This is a valid...' (52 chars)")

        # Validate
        project_result2 = project_repo.get_by_id(project_id)
        assert isinstance(project_result2, Success)
        validation_result2 = validation_service.validate_project(
            project_result2.value, test_schema
        )

        print(f"   - Validation result: {validation_result2.error_count} errors")
        assert validation_result2.is_valid()
        print("   ✓ Validation passed with valid length")

        # Step 4: Set description too long
        print("\nStep 4: Set Description Too Long (> 200 chars)")
        long_text = "A" * 250  # 250 characters
        result3 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("description"),
            value=long_text,
        )
        assert isinstance(result3, Success)
        print(f"   ✓ Set description = 'AAA...' ({len(long_text)} chars)")

        # Validate
        project_result3 = project_repo.get_by_id(project_id)
        assert isinstance(project_result3, Success)
        validation_result3 = validation_service.validate_project(
            project_result3.value, test_schema
        )

        print(f"   - Validation result: {validation_result3.error_count} errors")
        assert validation_result3.is_invalid()
        assert validation_result3.has_errors_for_field("description")
        print("   ✓ Validation failed for description (too long)")

        print("\n" + "=" * 70)
        print("✓ LENGTH CONSTRAINT VALIDATION TEST PASSED")
        print("=" * 70)

    def test_numeric_constraint_validation(
        self, temp_db: Path, temp_project_dir: Path, test_schema: EntityDefinition
    ) -> None:
        """Test min/max value constraint validation.

        Workflow:
        1. Create project
        2. Set sample_count below minimum (< 1)
        3. Validation should fail
        4. Set sample_count within valid range
        5. Validation should pass
        6. Set sample_count above maximum (> 100)
        7. Validation should fail
        """
        print("\n" + "=" * 70)
        print("TEST: Numeric Constraint Validation")
        print("=" * 70)

        # Step 1: Create project
        print("\nStep 1: Create Project")
        project_repo = SqliteProjectRepository(temp_db)
        create_command = CreateProjectCommand(project_repository=project_repo)

        create_result = create_command.execute(
            name="Numeric Test Project",
            entity_definition_id=EntityDefinitionId("validation_test_entity"),
        )
        assert isinstance(create_result, Success)
        project_id = create_result.value

        # Set required project_name
        update_command = UpdateFieldCommand(project_repository=project_repo)
        update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("project_name"),
            value="Project Name",
        )

        validation_service = ValidationService()

        # Step 2: Set sample_count below minimum
        print("\nStep 2: Set sample_count Below Minimum (< 1)")
        result = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("sample_count"),
            value=0,  # Below minimum of 1
        )
        assert isinstance(result, Success)
        print("   ✓ Set sample_count = 0 (below minimum)")

        # Validate
        project_result = project_repo.get_by_id(project_id)
        assert isinstance(project_result, Success)
        validation_result = validation_service.validate_project(
            project_result.value, test_schema
        )

        print(f"   - Validation result: {validation_result.error_count} errors")
        assert validation_result.is_invalid()
        assert validation_result.has_errors_for_field("sample_count")
        print("   ✓ Validation failed for sample_count (below minimum)")

        # Step 3: Set sample_count within valid range
        print("\nStep 3: Set sample_count Within Valid Range (1-100)")
        result2 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("sample_count"),
            value=50,
        )
        assert isinstance(result2, Success)
        print("   ✓ Set sample_count = 50 (valid)")

        # Validate
        project_result2 = project_repo.get_by_id(project_id)
        assert isinstance(project_result2, Success)
        validation_result2 = validation_service.validate_project(
            project_result2.value, test_schema
        )

        print(f"   - Validation result: {validation_result2.error_count} errors")
        assert validation_result2.is_valid()
        print("   ✓ Validation passed with valid value")

        # Step 4: Set sample_count above maximum
        print("\nStep 4: Set sample_count Above Maximum (> 100)")
        result3 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("sample_count"),
            value=150,  # Above maximum of 100
        )
        assert isinstance(result3, Success)
        print("   ✓ Set sample_count = 150 (above maximum)")

        # Validate
        project_result3 = project_repo.get_by_id(project_id)
        assert isinstance(project_result3, Success)
        validation_result3 = validation_service.validate_project(
            project_result3.value, test_schema
        )

        print(f"   - Validation result: {validation_result3.error_count} errors")
        assert validation_result3.is_invalid()
        assert validation_result3.has_errors_for_field("sample_count")
        print("   ✓ Validation failed for sample_count (above maximum)")

        print("\n" + "=" * 70)
        print("✓ NUMERIC CONSTRAINT VALIDATION TEST PASSED")
        print("=" * 70)

    def test_pattern_constraint_validation(
        self, temp_db: Path, temp_project_dir: Path, test_schema: EntityDefinition
    ) -> None:
        """Test pattern (regex) constraint validation.

        Workflow:
        1. Create project with required fields
        2. Set contact_phone with invalid format
        3. Validation should fail
        4. Set contact_phone with valid format (XXX-XXX-XXXX)
        5. Validation should pass
        """
        print("\n" + "=" * 70)
        print("TEST: Pattern Constraint Validation")
        print("=" * 70)

        # Step 1: Create project with required fields
        print("\nStep 1: Create Project with Required Fields")
        project_repo = SqliteProjectRepository(temp_db)
        create_command = CreateProjectCommand(project_repository=project_repo)

        create_result = create_command.execute(
            name="Pattern Test Project",
            entity_definition_id=EntityDefinitionId("validation_test_entity"),
        )
        assert isinstance(create_result, Success)
        project_id = create_result.value

        update_command = UpdateFieldCommand(project_repository=project_repo)

        # Set required fields
        update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("project_name"),
            value="Project Name",
        )
        update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("sample_count"),
            value=50,
        )
        print("   ✓ Required fields set")

        validation_service = ValidationService()

        # Step 2: Set contact_phone with invalid format
        print("\nStep 2: Set contact_phone with Invalid Format")
        result = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("contact_phone"),
            value="123456789",  # Invalid format (no dashes)
        )
        assert isinstance(result, Success)
        print("   ✓ Set contact_phone = '123456789' (invalid format)")

        # Validate
        project_result = project_repo.get_by_id(project_id)
        assert isinstance(project_result, Success)
        validation_result = validation_service.validate_project(
            project_result.value, test_schema
        )

        print(f"   - Validation result: {validation_result.error_count} errors")
        assert validation_result.is_invalid()
        assert validation_result.has_errors_for_field("contact_phone")
        print("   ✓ Validation failed for contact_phone (invalid pattern)")

        # Step 3: Set contact_phone with valid format
        print("\nStep 3: Set contact_phone with Valid Format (XXX-XXX-XXXX)")
        result2 = update_command.execute(
            project_id=project_id,
            field_id=FieldDefinitionId("contact_phone"),
            value="123-456-7890",  # Valid format
        )
        assert isinstance(result2, Success)
        print("   ✓ Set contact_phone = '123-456-7890' (valid format)")

        # Validate
        project_result2 = project_repo.get_by_id(project_id)
        assert isinstance(project_result2, Success)
        validation_result2 = validation_service.validate_project(
            project_result2.value, test_schema
        )

        print(f"   - Validation result: {validation_result2.error_count} errors")
        assert validation_result2.is_valid()
        print("   ✓ Validation passed with valid pattern")

        print("\n" + "=" * 70)
        print("✓ PATTERN CONSTRAINT VALIDATION TEST PASSED")
        print("=" * 70)
