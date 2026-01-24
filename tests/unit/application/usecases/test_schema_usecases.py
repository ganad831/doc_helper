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
