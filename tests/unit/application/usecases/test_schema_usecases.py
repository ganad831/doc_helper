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
