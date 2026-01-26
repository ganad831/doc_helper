"""Unit tests for SchemaUseCases (Phase SD-5).

Tests for the application layer use-case class that serves as the ONLY
entry point for Presentation layer to access schema operations.

ARCHITECTURE COMPLIANCE:
- Tests verify SchemaUseCases delegates to appropriate commands/queries
- Tests verify OperationResult wrapping is correct
- Tests verify domain ID unwrapping happens in Application layer
"""

from unittest.mock import Mock, MagicMock
import pytest

from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId


class TestSchemaUseCasesEntityOperations:
    """Tests for entity CRUD operations in SchemaUseCases."""

    @pytest.fixture
    def mock_schema_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key  # Return key as translation
        return service

    @pytest.fixture
    def usecases(
        self,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
        mock_translation_service: Mock,
    ) -> SchemaUseCases:
        """Create SchemaUseCases with mock dependencies."""
        return SchemaUseCases(
            schema_repository=mock_schema_repository,
            relationship_repository=mock_relationship_repository,
            translation_service=mock_translation_service,
        )

    # =========================================================================
    # CREATE ENTITY
    # =========================================================================

    def test_create_entity_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.ok with entity ID string on success."""
        # Setup: Mock the command's execute method to return Success
        mock_schema_repository.exists.return_value = False
        mock_schema_repository.get_root_entity.return_value = Failure("No root")
        mock_schema_repository.save.return_value = Success(None)

        # Execute
        result = usecases.create_entity(
            entity_id="test_entity",
            name_key="entity.test",
            is_root_entity=True,
        )

        # Assert
        assert result.success is True
        assert result.value == "test_entity"  # Unwrapped to string

    def test_create_entity_failure_empty_id(
        self,
        usecases: SchemaUseCases,
    ) -> None:
        """Should return OperationResult.fail for empty entity_id."""
        result = usecases.create_entity(
            entity_id="",
            name_key="entity.test",
            is_root_entity=False,
        )

        assert result.success is False
        assert "required" in result.error.lower() or "empty" in result.error.lower()

    def test_create_entity_failure_duplicate(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail for duplicate entity_id."""
        mock_schema_repository.exists.return_value = True

        result = usecases.create_entity(
            entity_id="existing_entity",
            name_key="entity.existing",
            is_root_entity=False,
        )

        assert result.success is False
        assert "exists" in result.error.lower()

    # =========================================================================
    # UPDATE ENTITY
    # =========================================================================

    def test_update_entity_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.ok with entity ID string on success."""
        # Setup: Create a mock entity
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.common.i18n import TranslationKey

        mock_entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=EntityDefinitionId("parent"),
        )

        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity)
        mock_schema_repository.update.return_value = Success(None)

        # Execute
        result = usecases.update_entity(
            entity_id="test_entity",
            name_key="entity.test.updated",
        )

        # Assert
        assert result.success is True
        assert result.value == "test_entity"

    def test_update_entity_failure_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when entity not found."""
        mock_schema_repository.exists.return_value = False

        result = usecases.update_entity(
            entity_id="nonexistent",
            name_key="entity.nonexistent",
        )

        assert result.success is False
        assert "not exist" in result.error.lower()

    # =========================================================================
    # DELETE ENTITY
    # =========================================================================

    def test_delete_entity_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.ok(None) on success."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_entity_dependencies.return_value = Success({
            "referenced_by_table_fields": [],
            "referenced_by_lookup_fields": [],
            "child_entities": [],
        })
        mock_schema_repository.delete.return_value = Success(None)

        result = usecases.delete_entity(entity_id="test_entity")

        assert result.success is True
        assert result.value is None

    def test_delete_entity_failure_has_dependencies(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when entity has dependencies."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_entity_dependencies.return_value = Success({
            "referenced_by_table_fields": [("other_entity", "table_field")],
            "referenced_by_lookup_fields": [],
            "child_entities": [],
        })

        result = usecases.delete_entity(entity_id="test_entity")

        assert result.success is False
        assert "referenced" in result.error.lower() or "cannot delete" in result.error.lower()


class TestSchemaUseCasesFieldOperations:
    """Tests for field CRUD operations in SchemaUseCases."""

    @pytest.fixture
    def mock_schema_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key  # Return key as translation
        return service

    @pytest.fixture
    def usecases(
        self,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
        mock_translation_service: Mock,
    ) -> SchemaUseCases:
        """Create SchemaUseCases with mock dependencies."""
        return SchemaUseCases(
            schema_repository=mock_schema_repository,
            relationship_repository=mock_relationship_repository,
            translation_service=mock_translation_service,
        )

    @pytest.fixture
    def mock_entity_with_field(self) -> Mock:
        """Create a mock entity with a field."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        field = FieldDefinition(
            id=FieldDefinitionId("test_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.test"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    # =========================================================================
    # ADD FIELD
    # =========================================================================

    def test_add_field_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID string on success."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.common.i18n import TranslationKey

        mock_entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(mock_entity)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_field(
            entity_id="test_entity",
            field_id="new_field",
            field_type="text",
            label_key="field.new",
        )

        assert result.success is True
        assert result.value == "new_field"

    def test_add_field_failure_entity_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when entity not found."""
        mock_schema_repository.get_by_id.return_value = Failure("Entity not found")

        result = usecases.add_field(
            entity_id="nonexistent",
            field_id="new_field",
            field_type="TEXT",
            label_key="field.new",
        )

        assert result.success is False

    def test_add_field_failure_lookup_self_entity(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when LOOKUP field references its own entity.

        SELF-ENTITY LOOKUP INVARIANT (A1.1-2): LOOKUP fields cannot reference
        the same entity they belong to. Self-referential lookups are not allowed.
        """
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.common.i18n import TranslationKey

        # Setup: Create an entity
        mock_entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(mock_entity)

        # Execute: Try to add a LOOKUP field that references its own entity
        result = usecases.add_field(
            entity_id="test_entity",
            field_id="self_lookup_field",
            field_type="lookup",
            label_key="field.self_lookup",
            lookup_entity_id="test_entity",  # Same as entity_id - SHOULD FAIL
        )

        # Assert: Should fail with clear error message
        assert result.success is False
        assert "own entity" in result.error.lower() or "self" in result.error.lower()

    # =========================================================================
    # UPDATE FIELD
    # =========================================================================

    def test_update_field_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID string on success."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.update_field(
            entity_id="test_entity",
            field_id="test_field",
            label_key="field.test.updated",
        )

        assert result.success is True
        assert result.value == "test_field"

    def test_update_field_failure_field_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when field not found."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.common.i18n import TranslationKey

        # Entity exists but has no fields
        mock_entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(mock_entity)

        result = usecases.update_field(
            entity_id="test_entity",
            field_id="nonexistent_field",
            label_key="field.test.updated",
        )

        assert result.success is False
        assert "not found" in result.error.lower() or "does not exist" in result.error.lower()

    def test_update_field_failure_lookup_self_entity(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when updating LOOKUP to reference its own entity.

        SELF-ENTITY LOOKUP INVARIANT (A1.1-2): LOOKUP fields cannot reference
        the same entity they belong to. Self-referential lookups are not allowed.
        """
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        # Setup: Create an entity with an existing LOOKUP field pointing to a different entity
        lookup_field = FieldDefinition(
            id=FieldDefinitionId("lookup_field"),
            field_type=FieldType.LOOKUP,
            label_key=TranslationKey("field.lookup"),
            required=False,
            lookup_entity_id=EntityDefinitionId("other_entity"),  # Currently points elsewhere
        )

        mock_entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={lookup_field.id: lookup_field},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(mock_entity)
        mock_schema_repository.exists.return_value = True

        # Execute: Try to update the LOOKUP field to reference its own entity
        result = usecases.update_field(
            entity_id="test_entity",
            field_id="lookup_field",
            lookup_entity_id="test_entity",  # Same as entity_id - SHOULD FAIL
        )

        # Assert: Should fail with clear error message
        assert result.success is False
        assert "own entity" in result.error.lower() or "self" in result.error.lower()

    # =========================================================================
    # DELETE FIELD
    # =========================================================================

    def test_delete_field_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.ok(None) on success."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_field_dependencies.return_value = Success({
            "referenced_by_formulas": [],
            "referenced_by_controls_source": [],
            "referenced_by_controls_target": [],
            "referenced_by_lookup_display": [],
        })
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.delete_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        assert result.success is True
        assert result.value is None

    def test_delete_field_failure_has_dependencies(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.fail when field has dependencies."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)
        mock_schema_repository.get_field_dependencies.return_value = Success({
            "referenced_by_formulas": [("other_entity", "calc_field")],
            "referenced_by_controls_source": [],
            "referenced_by_controls_target": [],
            "referenced_by_lookup_display": [],
        })

        result = usecases.delete_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        assert result.success is False
        assert "referenced" in result.error.lower() or "cannot delete" in result.error.lower()


class TestSchemaUseCasesConstraintOperations:
    """Tests for constraint operations in SchemaUseCases."""

    @pytest.fixture
    def mock_schema_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key  # Return key as translation
        return service

    @pytest.fixture
    def usecases(
        self,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
        mock_translation_service: Mock,
    ) -> SchemaUseCases:
        """Create SchemaUseCases with mock dependencies."""
        return SchemaUseCases(
            schema_repository=mock_schema_repository,
            relationship_repository=mock_relationship_repository,
            translation_service=mock_translation_service,
        )

    @pytest.fixture
    def mock_entity_with_field(self) -> Mock:
        """Create a mock entity with a field."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        field = FieldDefinition(
            id=FieldDefinitionId("test_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.test"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    def test_add_constraint_required_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should add REQUIRED constraint successfully."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="REQUIRED",
            severity="ERROR",
        )

        assert result.success is True

    def test_add_constraint_min_value_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should add MIN_VALUE constraint successfully."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        # Create entity with NUMBER field
        field = FieldDefinition(
            id=FieldDefinitionId("number_field"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.number"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(entity)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="number_field",
            constraint_type="MIN_VALUE",
            value=0.0,
            severity="ERROR",
        )

        assert result.success is True

    def test_add_constraint_failure_invalid_type(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should fail for invalid constraint type."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="INVALID_TYPE",
            severity="ERROR",
        )

        assert result.success is False
        assert "unsupported" in result.error.lower() or "unknown" in result.error.lower()

    # =========================================================================
    # Phase SD-6: Advanced Constraint Tests
    # =========================================================================

    def test_add_constraint_pattern_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should add PATTERN constraint successfully (Phase SD-6)."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="PATTERN",
            severity="ERROR",
            pattern=r"^[A-Z]{2}\d{4}$",
            pattern_description="Must be 2 letters followed by 4 digits",
        )

        assert result.success is True

    def test_add_constraint_pattern_failure_missing_pattern(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should fail PATTERN constraint when pattern is missing."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="PATTERN",
            severity="ERROR",
            pattern=None,  # Missing pattern
        )

        assert result.success is False
        assert "pattern" in result.error.lower()

    def test_add_constraint_allowed_values_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should add ALLOWED_VALUES constraint successfully (Phase SD-6)."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="ALLOWED_VALUES",
            severity="ERROR",
            allowed_values=("value1", "value2", "value3"),
        )

        assert result.success is True

    def test_add_constraint_allowed_values_failure_empty(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should fail ALLOWED_VALUES constraint when values are empty."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="ALLOWED_VALUES",
            severity="ERROR",
            allowed_values=None,  # Missing values
        )

        assert result.success is False
        assert "values" in result.error.lower()

    def test_add_constraint_file_extension_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should add FILE_EXTENSION constraint successfully (Phase SD-6)."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        # Create entity with FILE field
        field = FieldDefinition(
            id=FieldDefinitionId("file_field"),
            field_type=FieldType.FILE,
            label_key=TranslationKey("field.file"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(entity)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="file_field",
            constraint_type="FILE_EXTENSION",
            severity="ERROR",
            allowed_extensions=(".pdf", ".doc", ".docx"),
        )

        assert result.success is True

    def test_add_constraint_file_extension_failure_missing_extensions(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should fail FILE_EXTENSION constraint when extensions are missing."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        field = FieldDefinition(
            id=FieldDefinitionId("file_field"),
            field_type=FieldType.FILE,
            label_key=TranslationKey("field.file"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(entity)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="file_field",
            constraint_type="FILE_EXTENSION",
            severity="ERROR",
            allowed_extensions=None,  # Missing extensions
        )

        assert result.success is False
        assert "extension" in result.error.lower()

    def test_add_constraint_max_file_size_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should add MAX_FILE_SIZE constraint successfully (Phase SD-6)."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        # Create entity with FILE field
        field = FieldDefinition(
            id=FieldDefinitionId("file_field"),
            field_type=FieldType.FILE,
            label_key=TranslationKey("field.file"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(entity)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="file_field",
            constraint_type="MAX_FILE_SIZE",
            severity="ERROR",
            max_size_bytes=10 * 1024 * 1024,  # 10 MB
        )

        assert result.success is True

    def test_add_constraint_max_file_size_failure_missing_size(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should fail MAX_FILE_SIZE constraint when size is missing."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        field = FieldDefinition(
            id=FieldDefinitionId("file_field"),
            field_type=FieldType.FILE,
            label_key=TranslationKey("field.file"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(entity)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="file_field",
            constraint_type="MAX_FILE_SIZE",
            severity="ERROR",
            max_size_bytes=None,  # Missing size
        )

        assert result.success is False
        assert "size" in result.error.lower()

    # =========================================================================
    # CONSTRAINT UNIQUENESS ENFORCEMENT (Phase S-3)
    # =========================================================================

    @pytest.fixture
    def mock_entity_with_min_length_constraint(self) -> Mock:
        """Create a mock entity with a field that already has a MIN_LENGTH constraint."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey
        from doc_helper.domain.validation.constraints import MinLengthConstraint

        # Field with existing MIN_LENGTH constraint
        field = FieldDefinition(
            id=FieldDefinitionId("text_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text"),
            required=False,
            constraints=(MinLengthConstraint(min_length=5),),  # Already has MIN_LENGTH
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    def test_add_constraint_blocks_duplicate_type_different_value(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_min_length_constraint: Mock,
    ) -> None:
        """Should BLOCK adding a constraint of the same TYPE even with different value.

        UNIQUENESS INVARIANT: Each constraint type may exist at most once per field.
        This is the canonical test for constraint type uniqueness at the Application Layer.
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_min_length_constraint
        )

        # Try to add MIN_LENGTH with a DIFFERENT value (10 instead of 5)
        # This should be BLOCKED because MIN_LENGTH already exists
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="text_field",
            constraint_type="MIN_LENGTH",
            value=10,  # Different from existing value of 5
            severity="ERROR",
        )

        # Assert: MUST be blocked
        assert result.success is False
        assert "already exists" in result.error.lower()
        assert "min_length" in result.error.lower()

        # Verify save was NOT called (constraint was blocked before reaching command)
        mock_schema_repository.save.assert_not_called()

    def test_add_constraint_allows_different_constraint_type(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_min_length_constraint: Mock,
    ) -> None:
        """Should ALLOW adding a DIFFERENT constraint type.

        Having MIN_LENGTH should not block adding MAX_LENGTH.
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_min_length_constraint
        )
        mock_schema_repository.save.return_value = Success(None)

        # Add MAX_LENGTH - different type than existing MIN_LENGTH
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="text_field",
            constraint_type="MAX_LENGTH",
            value=100,
            severity="ERROR",
        )

        # Assert: Should succeed
        assert result.success is True

    # =========================================================================
    # SEMANTIC CROSS-CONSTRAINT VALIDATION (Phase S-3)
    # =========================================================================

    @pytest.fixture
    def mock_entity_with_max_value_constraint(self) -> Mock:
        """Create a mock entity with a NUMBER field that has a MAX_VALUE constraint."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey
        from doc_helper.domain.validation.constraints import MaxValueConstraint

        field = FieldDefinition(
            id=FieldDefinitionId("number_field"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.number"),
            required=False,
            constraints=(MaxValueConstraint(max_value=100.0),),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    @pytest.fixture
    def mock_entity_with_min_value_constraint(self) -> Mock:
        """Create a mock entity with a NUMBER field that has a MIN_VALUE constraint."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey
        from doc_helper.domain.validation.constraints import MinValueConstraint

        field = FieldDefinition(
            id=FieldDefinitionId("number_field"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.number"),
            required=False,
            constraints=(MinValueConstraint(min_value=50.0),),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    @pytest.fixture
    def mock_entity_with_max_length_constraint(self) -> Mock:
        """Create a mock entity with a TEXT field that has a MAX_LENGTH constraint."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey
        from doc_helper.domain.validation.constraints import MaxLengthConstraint

        field = FieldDefinition(
            id=FieldDefinitionId("text_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text"),
            required=False,
            constraints=(MaxLengthConstraint(max_length=50),),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    @pytest.fixture
    def mock_entity_with_number_field_no_constraints(self) -> Mock:
        """Create a mock entity with a NUMBER field with no constraints."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        field = FieldDefinition(
            id=FieldDefinitionId("number_field"),
            field_type=FieldType.NUMBER,
            label_key=TranslationKey("field.number"),
            required=False,
            constraints=(),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    def test_reject_min_value_greater_than_existing_max_value(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_max_value_constraint: Mock,
    ) -> None:
        """Should REJECT adding MIN_VALUE > existing MAX_VALUE.

        SEMANTIC INVARIANT: min_value <= max_value
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_max_value_constraint
        )

        # Try to add MIN_VALUE=150 when MAX_VALUE=100 exists
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="number_field",
            constraint_type="MIN_VALUE",
            value=150,  # Greater than existing MAX_VALUE of 100
            severity="ERROR",
        )

        assert result.success is False
        assert "MIN_VALUE" in result.error
        assert "MAX_VALUE" in result.error
        assert "150" in result.error
        assert "100" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_reject_max_value_less_than_existing_min_value(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_min_value_constraint: Mock,
    ) -> None:
        """Should REJECT adding MAX_VALUE < existing MIN_VALUE.

        SEMANTIC INVARIANT: min_value <= max_value
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_min_value_constraint
        )

        # Try to add MAX_VALUE=30 when MIN_VALUE=50 exists
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="number_field",
            constraint_type="MAX_VALUE",
            value=30,  # Less than existing MIN_VALUE of 50
            severity="ERROR",
        )

        assert result.success is False
        assert "MIN_VALUE" in result.error
        assert "MAX_VALUE" in result.error
        assert "50" in result.error
        assert "30" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_reject_min_length_greater_than_existing_max_length(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_max_length_constraint: Mock,
    ) -> None:
        """Should REJECT adding MIN_LENGTH > existing MAX_LENGTH.

        SEMANTIC INVARIANT: min_length <= max_length
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_max_length_constraint
        )

        # Try to add MIN_LENGTH=100 when MAX_LENGTH=50 exists
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="text_field",
            constraint_type="MIN_LENGTH",
            value=100,  # Greater than existing MAX_LENGTH of 50
            severity="ERROR",
        )

        assert result.success is False
        assert "MIN_LENGTH" in result.error
        assert "MAX_LENGTH" in result.error
        assert "100" in result.error
        assert "50" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_reject_max_length_less_than_existing_min_length(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_min_length_constraint: Mock,
    ) -> None:
        """Should REJECT adding MAX_LENGTH < existing MIN_LENGTH.

        SEMANTIC INVARIANT: min_length <= max_length
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_min_length_constraint
        )

        # Try to add MAX_LENGTH=3 when MIN_LENGTH=5 exists
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="text_field",
            constraint_type="MAX_LENGTH",
            value=3,  # Less than existing MIN_LENGTH of 5
            severity="ERROR",
        )

        assert result.success is False
        assert "MIN_LENGTH" in result.error
        assert "MAX_LENGTH" in result.error
        assert "5" in result.error
        assert "3" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_reject_numeric_constraint_on_text_field(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should REJECT adding MIN_VALUE/MAX_VALUE to TEXT field.

        FIELD TYPE COMPATIBILITY: Numeric constraints only on NUMBER/DATE fields.
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        # mock_entity_with_field has a TEXT field
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="test_field",
            constraint_type="MIN_VALUE",
            value=10,
            severity="ERROR",
        )

        assert result.success is False
        assert "MIN_VALUE" in result.error
        assert "NUMBER" in result.error or "TEXT" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_reject_text_constraint_on_number_field(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_number_field_no_constraints: Mock,
    ) -> None:
        """Should REJECT adding MIN_LENGTH/MAX_LENGTH to NUMBER field.

        FIELD TYPE COMPATIBILITY: Text length constraints only on TEXT/TEXTAREA fields.
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_number_field_no_constraints
        )

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="number_field",
            constraint_type="MIN_LENGTH",
            value=5,
            severity="ERROR",
        )

        assert result.success is False
        assert "MIN_LENGTH" in result.error
        assert "TEXT" in result.error or "NUMBER" in result.error
        mock_schema_repository.save.assert_not_called()

    def test_allow_valid_min_max_value_combination(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_min_value_constraint: Mock,
    ) -> None:
        """Should ALLOW adding MAX_VALUE >= existing MIN_VALUE.

        Valid: MIN_VALUE=50, MAX_VALUE=100
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_min_value_constraint
        )
        mock_schema_repository.save.return_value = Success(None)

        # Add MAX_VALUE=100 when MIN_VALUE=50 exists (valid: 50 <= 100)
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="number_field",
            constraint_type="MAX_VALUE",
            value=100,
            severity="ERROR",
        )

        assert result.success is True

    def test_allow_single_min_value_without_max_value(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_number_field_no_constraints: Mock,
    ) -> None:
        """Should ALLOW adding MIN_VALUE when no MAX_VALUE exists."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_number_field_no_constraints
        )
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="number_field",
            constraint_type="MIN_VALUE",
            value=10,
            severity="ERROR",
        )

        assert result.success is True

    def test_allow_equal_min_max_value(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_min_value_constraint: Mock,
    ) -> None:
        """Should ALLOW adding MAX_VALUE == existing MIN_VALUE (edge case).

        Valid: MIN_VALUE=50, MAX_VALUE=50 (forces exact value)
        """
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(
            mock_entity_with_min_value_constraint
        )
        mock_schema_repository.save.return_value = Success(None)

        # Add MAX_VALUE=50 when MIN_VALUE=50 exists (valid: 50 <= 50)
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="number_field",
            constraint_type="MAX_VALUE",
            value=50,  # Equal to existing MIN_VALUE
            severity="ERROR",
        )

        assert result.success is True

    # =========================================================================
    # CALCULATED Field Constraint Invariant Tests
    # =========================================================================

    def test_add_constraint_fails_for_calculated_field_required(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject adding REQUIRED constraint to CALCULATED field.

        INVARIANT: CALCULATED fields cannot have any validation constraints
        because they derive their values from formulas, not user input.
        """
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        # Create entity with CALCULATED field
        field = FieldDefinition(
            id=FieldDefinitionId("total"),
            field_type=FieldType.CALCULATED,
            label_key=TranslationKey("field.total"),
            required=False,
            formula="{{qty}} * {{price}}",
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(entity)

        # Attempt to add REQUIRED constraint to CALCULATED field
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="total",
            constraint_type="REQUIRED",
            severity="ERROR",
        )

        assert result.success is False
        assert "calculated" in result.error.lower()
        assert "constraint" in result.error.lower()

    def test_add_constraint_fails_for_calculated_field_min_value(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should reject adding MIN_VALUE constraint to CALCULATED field."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        # Create entity with CALCULATED field
        field = FieldDefinition(
            id=FieldDefinitionId("total"),
            field_type=FieldType.CALCULATED,
            label_key=TranslationKey("field.total"),
            required=False,
            formula="{{qty}} * {{price}}",
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )

        mock_schema_repository.get_by_id.return_value = Success(entity)

        # Attempt to add MIN_VALUE constraint to CALCULATED field
        result = usecases.add_constraint(
            entity_id="test_entity",
            field_id="total",
            constraint_type="MIN_VALUE",
            value=0.0,
            severity="ERROR",
        )

        assert result.success is False
        assert "calculated" in result.error.lower()


class TestSchemaUseCasesOutputMappingOperations:
    """Tests for output mapping CRUD operations in SchemaUseCases (Phase F-12.5)."""

    @pytest.fixture
    def mock_schema_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key  # Return key as translation
        return service

    @pytest.fixture
    def usecases(
        self,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
        mock_translation_service: Mock,
    ) -> SchemaUseCases:
        """Create SchemaUseCases with mock dependencies."""
        return SchemaUseCases(
            schema_repository=mock_schema_repository,
            relationship_repository=mock_relationship_repository,
            translation_service=mock_translation_service,
        )

    @pytest.fixture
    def mock_entity_with_field(self) -> Mock:
        """Create a mock entity with a field."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        field = FieldDefinition(
            id=FieldDefinitionId("test_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.test"),
            required=False,
            output_mappings=(),  # Start with no output mappings
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    @pytest.fixture
    def mock_entity_with_output_mapping(self) -> Mock:
        """Create a mock entity with a field that has output mappings."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey
        from doc_helper.application.dto.export_dto import OutputMappingExportDTO

        mapping = OutputMappingExportDTO(
            target="TEXT",
            formula_text="{{depth_from}} - {{depth_to}}",
        )

        field = FieldDefinition(
            id=FieldDefinitionId("test_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.test"),
            required=False,
            output_mappings=(mapping,),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    # =========================================================================
    # ADD OUTPUT MAPPING
    # =========================================================================

    def test_add_output_mapping_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID on success."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_output_mapping(
            entity_id="test_entity",
            field_id="test_field",
            target="TEXT",
            formula_text="{{field1}} + {{field2}}",
        )

        assert result.success is True
        assert result.value == "test_field"

    def test_add_output_mapping_failure_entity_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when entity not found."""
        mock_schema_repository.get_by_id.return_value = Failure("Entity not found")

        result = usecases.add_output_mapping(
            entity_id="nonexistent",
            field_id="test_field",
            target="TEXT",
            formula_text="{{field1}}",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_add_output_mapping_failure_field_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.fail when field not found."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.add_output_mapping(
            entity_id="test_entity",
            field_id="nonexistent_field",
            target="TEXT",
            formula_text="{{field1}}",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_add_output_mapping_failure_empty_target(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.fail for empty target."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.add_output_mapping(
            entity_id="test_entity",
            field_id="test_field",
            target="",
            formula_text="{{field1}}",
        )

        assert result.success is False
        assert "target" in result.error.lower()

    def test_add_output_mapping_failure_empty_formula(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.fail for empty formula_text."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.add_output_mapping(
            entity_id="test_entity",
            field_id="test_field",
            target="TEXT",
            formula_text="",
        )

        assert result.success is False
        assert "formula" in result.error.lower()

    def test_add_output_mapping_failure_duplicate_target(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_output_mapping: Mock,
    ) -> None:
        """Should return OperationResult.fail for duplicate target type."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_output_mapping)

        result = usecases.add_output_mapping(
            entity_id="test_entity",
            field_id="test_field",
            target="TEXT",  # Already exists
            formula_text="{{field1}}",
        )

        assert result.success is False
        assert "already has" in result.error.lower() or "already exists" in result.error.lower()

    # =========================================================================
    # UPDATE OUTPUT MAPPING
    # =========================================================================

    def test_update_output_mapping_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_output_mapping: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID on success."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_output_mapping)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.update_output_mapping(
            entity_id="test_entity",
            field_id="test_field",
            target="TEXT",  # Update existing TEXT mapping
            formula_text="{{new_formula}}",
        )

        assert result.success is True
        assert result.value == "test_field"

    def test_update_output_mapping_failure_entity_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when entity not found."""
        mock_schema_repository.get_by_id.return_value = Failure("Entity not found")

        result = usecases.update_output_mapping(
            entity_id="nonexistent",
            field_id="test_field",
            target="TEXT",
            formula_text="{{field1}}",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_update_output_mapping_failure_field_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_output_mapping: Mock,
    ) -> None:
        """Should return OperationResult.fail when field not found."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_output_mapping)

        result = usecases.update_output_mapping(
            entity_id="test_entity",
            field_id="nonexistent_field",
            target="TEXT",
            formula_text="{{field1}}",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_update_output_mapping_failure_mapping_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.fail when output mapping not found."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.update_output_mapping(
            entity_id="test_entity",
            field_id="test_field",
            target="NUMBER",  # Does not exist
            formula_text="{{field1}}",
        )

        assert result.success is False
        assert "no output mapping" in result.error.lower() or "not found" in result.error.lower()

    # =========================================================================
    # DELETE OUTPUT MAPPING
    # =========================================================================

    def test_delete_output_mapping_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_output_mapping: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID on success."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_output_mapping)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.delete_output_mapping(
            entity_id="test_entity",
            field_id="test_field",
            target="TEXT",
        )

        assert result.success is True
        assert result.value == "test_field"

    def test_delete_output_mapping_failure_entity_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when entity not found."""
        mock_schema_repository.get_by_id.return_value = Failure("Entity not found")

        result = usecases.delete_output_mapping(
            entity_id="nonexistent",
            field_id="test_field",
            target="TEXT",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_delete_output_mapping_failure_field_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_output_mapping: Mock,
    ) -> None:
        """Should return OperationResult.fail when field not found."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_output_mapping)

        result = usecases.delete_output_mapping(
            entity_id="test_entity",
            field_id="nonexistent_field",
            target="TEXT",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_delete_output_mapping_failure_mapping_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return OperationResult.fail when output mapping not found."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.delete_output_mapping(
            entity_id="test_entity",
            field_id="test_field",
            target="NUMBER",  # Does not exist
        )

        assert result.success is False
        assert "no output mapping" in result.error.lower() or "not found" in result.error.lower()

    # =========================================================================
    # LIST OUTPUT MAPPINGS
    # =========================================================================

    def test_list_output_mappings_success_with_mappings(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_output_mapping: Mock,
    ) -> None:
        """Should return tuple of OutputMappingExportDTO when mappings exist."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_output_mapping)

        result = usecases.list_output_mappings_for_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        assert isinstance(result, tuple)
        assert len(result) == 1
        assert result[0].target == "TEXT"
        assert result[0].formula_text == "{{depth_from}} - {{depth_to}}"

    def test_list_output_mappings_success_empty(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return empty tuple when no mappings exist."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.list_output_mappings_for_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        assert isinstance(result, tuple)
        assert len(result) == 0

    def test_list_output_mappings_failure_entity_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return empty tuple when entity not found."""
        mock_schema_repository.get_by_id.return_value = Failure("Entity not found")

        result = usecases.list_output_mappings_for_field(
            entity_id="nonexistent",
            field_id="test_field",
        )

        assert isinstance(result, tuple)
        assert len(result) == 0

    def test_list_output_mappings_failure_field_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_field: Mock,
    ) -> None:
        """Should return empty tuple when field not found."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_field)

        result = usecases.list_output_mappings_for_field(
            entity_id="test_entity",
            field_id="nonexistent_field",
        )

        assert isinstance(result, tuple)
        assert len(result) == 0


class TestSchemaUseCasesFieldOptionOperations:
    """Tests for field option CRUD operations in SchemaUseCases (Phase F-14)."""

    @pytest.fixture
    def mock_schema_repository(self) -> Mock:
        """Create mock schema repository."""
        return Mock()

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key  # Return key as translation
        return service

    @pytest.fixture
    def usecases(
        self,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
        mock_translation_service: Mock,
    ) -> SchemaUseCases:
        """Create SchemaUseCases with mock dependencies."""
        return SchemaUseCases(
            schema_repository=mock_schema_repository,
            relationship_repository=mock_relationship_repository,
            translation_service=mock_translation_service,
        )

    @pytest.fixture
    def mock_entity_with_dropdown_field(self) -> Mock:
        """Create a mock entity with a DROPDOWN field with options."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        field = FieldDefinition(
            id=FieldDefinitionId("dropdown_field"),
            field_type=FieldType.DROPDOWN,
            label_key=TranslationKey("field.dropdown"),
            required=False,
            options=(
                ("option1", TranslationKey("option.1")),
                ("option2", TranslationKey("option.2")),
            ),
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    @pytest.fixture
    def mock_entity_with_text_field(self) -> Mock:
        """Create a mock entity with a TEXT field (not a choice field)."""
        from doc_helper.domain.schema.entity_definition import EntityDefinition
        from doc_helper.domain.schema.field_definition import FieldDefinition
        from doc_helper.domain.schema.field_type import FieldType
        from doc_helper.domain.common.i18n import TranslationKey

        field = FieldDefinition(
            id=FieldDefinitionId("text_field"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.text"),
            required=False,
        )

        entity = EntityDefinition(
            id=EntityDefinitionId("test_entity"),
            name_key=TranslationKey("entity.test"),
            description_key=None,
            fields={field.id: field},
            is_root_entity=False,
            parent_entity_id=None,
        )
        return entity

    # =========================================================================
    # ADD FIELD OPTION
    # =========================================================================

    def test_add_field_option_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID on success."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.add_field_option(
            entity_id="test_entity",
            field_id="dropdown_field",
            option_value="option3",
            option_label_key="option.3",
        )

        assert result.success is True
        assert result.value == "dropdown_field"

    def test_add_field_option_failure_entity_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return OperationResult.fail when entity not found."""
        mock_schema_repository.exists.return_value = False

        result = usecases.add_field_option(
            entity_id="nonexistent",
            field_id="dropdown_field",
            option_value="option3",
            option_label_key="option.3",
        )

        assert result.success is False
        assert "not exist" in result.error.lower()

    def test_add_field_option_failure_non_choice_field(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_text_field: Mock,
    ) -> None:
        """Should return OperationResult.fail for non-choice field."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        result = usecases.add_field_option(
            entity_id="test_entity",
            field_id="text_field",
            option_value="option1",
            option_label_key="option.1",
        )

        assert result.success is False
        assert "choice" in result.error.lower()

    def test_add_field_option_failure_duplicate_value(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.fail for duplicate option value."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        result = usecases.add_field_option(
            entity_id="test_entity",
            field_id="dropdown_field",
            option_value="option1",  # Already exists
            option_label_key="option.1.duplicate",
        )

        assert result.success is False
        assert "already exists" in result.error.lower()

    # =========================================================================
    # UPDATE FIELD OPTION
    # =========================================================================

    def test_update_field_option_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID on success."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.update_field_option(
            entity_id="test_entity",
            field_id="dropdown_field",
            option_value="option1",
            new_label_key="option.1.updated",
        )

        assert result.success is True
        assert result.value == "dropdown_field"

    def test_update_field_option_failure_option_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.fail when option not found."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        result = usecases.update_field_option(
            entity_id="test_entity",
            field_id="dropdown_field",
            option_value="nonexistent_option",
            new_label_key="option.new",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    # =========================================================================
    # DELETE FIELD OPTION
    # =========================================================================

    def test_delete_field_option_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID on success."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.delete_field_option(
            entity_id="test_entity",
            field_id="dropdown_field",
            option_value="option1",
        )

        assert result.success is True
        assert result.value == "dropdown_field"

    def test_delete_field_option_failure_option_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.fail when option not found."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        result = usecases.delete_field_option(
            entity_id="test_entity",
            field_id="dropdown_field",
            option_value="nonexistent_option",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_delete_field_option_failure_non_choice_field(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_text_field: Mock,
    ) -> None:
        """Should return OperationResult.fail for non-choice field."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        result = usecases.delete_field_option(
            entity_id="test_entity",
            field_id="text_field",
            option_value="option1",
        )

        assert result.success is False
        assert "choice" in result.error.lower()

    # =========================================================================
    # REORDER FIELD OPTIONS
    # =========================================================================

    def test_reorder_field_options_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.ok with field ID on success."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)
        mock_schema_repository.save.return_value = Success(None)

        result = usecases.reorder_field_options(
            entity_id="test_entity",
            field_id="dropdown_field",
            new_option_order=["option2", "option1"],  # Reversed order
        )

        assert result.success is True
        assert result.value == "dropdown_field"

    def test_reorder_field_options_failure_missing_options(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.fail when options are missing."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        result = usecases.reorder_field_options(
            entity_id="test_entity",
            field_id="dropdown_field",
            new_option_order=["option1"],  # Missing option2
        )

        assert result.success is False
        assert "missing" in result.error.lower()

    def test_reorder_field_options_failure_extra_options(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return OperationResult.fail when extra options provided."""
        mock_schema_repository.exists.return_value = True
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        result = usecases.reorder_field_options(
            entity_id="test_entity",
            field_id="dropdown_field",
            new_option_order=["option1", "option2", "option3"],  # option3 doesn't exist
        )

        assert result.success is False
        assert "unknown" in result.error.lower()

    # =========================================================================
    # LIST FIELD OPTIONS
    # =========================================================================

    def test_list_field_options_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return tuple of FieldOptionExportDTO."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        result = usecases.list_field_options(
            entity_id="test_entity",
            field_id="dropdown_field",
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0].value == "option1"
        assert result[0].label_key == "option.1"
        assert result[1].value == "option2"
        assert result[1].label_key == "option.2"

    def test_list_field_options_empty_for_non_choice_field(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_text_field: Mock,
    ) -> None:
        """Should return empty tuple for non-choice field."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_text_field)

        result = usecases.list_field_options(
            entity_id="test_entity",
            field_id="text_field",
        )

        assert isinstance(result, tuple)
        assert len(result) == 0

    def test_list_field_options_empty_for_nonexistent_entity(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should return empty tuple when entity not found."""
        mock_schema_repository.get_by_id.return_value = Failure("Entity not found")

        result = usecases.list_field_options(
            entity_id="nonexistent",
            field_id="dropdown_field",
        )

        assert isinstance(result, tuple)
        assert len(result) == 0

    def test_list_field_options_empty_for_nonexistent_field(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity_with_dropdown_field: Mock,
    ) -> None:
        """Should return empty tuple when field not found."""
        mock_schema_repository.get_by_id.return_value = Success(mock_entity_with_dropdown_field)

        result = usecases.list_field_options(
            entity_id="test_entity",
            field_id="nonexistent_field",
        )

        assert isinstance(result, tuple)
        assert len(result) == 0
