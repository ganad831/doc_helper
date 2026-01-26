"""Unit tests for SchemaUseCases control rule operations (Phase A5.1).

Tests for control rule CRUD operations in SchemaUseCases, verifying:
- Add, update, delete control rules via use case layer
- OperationResult wrapping
- Validation integration
- Design-time only behavior

INVARIANTS (enforced by tests):
- Control rules are DESIGN-TIME metadata only
- NO runtime execution occurs
- One rule per type per field
- Rule type is identity (cannot be changed)
- Formula validation via ControlRuleUseCases (F-6, F-8)
"""

import pytest
from dataclasses import replace
from unittest.mock import Mock, MagicMock, patch

from doc_helper.application.dto.operation_result import OperationResult
from doc_helper.application.dto.export_dto import ControlRuleExportDTO
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.domain.common.result import Success, Failure
from doc_helper.domain.common.i18n import TranslationKey
from doc_helper.domain.schema.schema_ids import EntityDefinitionId, FieldDefinitionId
from doc_helper.domain.schema.field_definition import FieldDefinition
from doc_helper.domain.schema.field_type import FieldType


class TestSchemaUseCasesAddControlRule:
    """Tests for add_control_rule in SchemaUseCases."""

    @pytest.fixture
    def mock_field_definition(self) -> FieldDefinition:
        """Create mock field definition with no control rules."""
        return FieldDefinition(
            id=FieldDefinitionId("test_field"),
            label_key=TranslationKey("field.test"),
            field_type=FieldType.TEXT,
            control_rules=(),
        )

    @pytest.fixture
    def mock_entity(self, mock_field_definition: FieldDefinition) -> Mock:
        """Create mock entity with field."""
        entity = Mock()
        entity.fields = {FieldDefinitionId("test_field"): mock_field_definition}
        entity.update_field = Mock()
        entity.id = EntityDefinitionId("test_entity")
        return entity

    @pytest.fixture
    def mock_schema_repository(self, mock_entity: Mock) -> Mock:
        """Create mock schema repository."""
        repository = Mock()
        repository.exists = Mock(return_value=True)
        repository.get_by_id = Mock(return_value=Success(mock_entity))
        repository.save = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key
        return service

    @pytest.fixture
    def mock_control_rule_usecases(self) -> Mock:
        """Create mock ControlRuleUseCases."""
        from doc_helper.application.dto.control_rule_dto import (
            ControlRuleResultDTO,
            ControlRuleStatus,
        )

        usecases = Mock()
        # Return valid ALLOWED status by default
        mock_result = ControlRuleResultDTO(
            status=ControlRuleStatus.ALLOWED,
            rule=None,  # Actual rule DTO not needed for validation check
            block_reason=None,
        )
        usecases.validate_control_rule = Mock(return_value=mock_result)
        return usecases

    @pytest.fixture
    def usecases(
        self,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
        mock_translation_service: Mock,
        mock_control_rule_usecases: Mock,
    ) -> SchemaUseCases:
        """Create SchemaUseCases with mock dependencies."""
        uc = SchemaUseCases(
            schema_repository=mock_schema_repository,
            relationship_repository=mock_relationship_repository,
            translation_service=mock_translation_service,
        )
        # Inject mock control rule usecases
        uc._control_rule_usecases = mock_control_rule_usecases
        return uc

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_add_control_rule_success(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity: Mock,
    ) -> None:
        """Should successfully add control rule and return OperationResult.ok."""
        result = usecases.add_control_rule(
            entity_id="test_entity",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="is_valid == true",
        )

        assert result.success is True
        assert result.value == "test_field"  # Returns field ID string

    def test_add_control_rule_all_types(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
        mock_control_rule_usecases: Mock,
    ) -> None:
        """Should accept all valid rule types: VISIBILITY, ENABLED, REQUIRED."""
        from doc_helper.application.dto.control_rule_dto import (
            ControlRuleResultDTO,
            ControlRuleStatus,
        )

        for rule_type in ["VISIBILITY", "ENABLED", "REQUIRED"]:
            # Reset field for each iteration
            mock_entity.fields = {
                FieldDefinitionId("test_field"): mock_field_definition
            }

            # Update mock return value for this rule type - ALLOWED status
            mock_result = ControlRuleResultDTO(
                status=ControlRuleStatus.ALLOWED,
                rule=None,
                block_reason=None,
            )
            mock_control_rule_usecases.validate_control_rule.return_value = mock_result

            result = usecases.add_control_rule(
                entity_id="test_entity",
                field_id="test_field",
                rule_type=rule_type,
                formula_text="formula",
            )

            assert result.success is True, f"Failed for rule_type={rule_type}"

    # =========================================================================
    # VALIDATION FAILURE TESTS
    # =========================================================================

    def test_add_control_rule_invalid_type_rejected(
        self,
        usecases: SchemaUseCases,
    ) -> None:
        """Should reject invalid rule type."""
        result = usecases.add_control_rule(
            entity_id="test_entity",
            field_id="test_field",
            rule_type="INVALID",
            formula_text="formula",
        )

        assert result.success is False
        assert "invalid rule type" in result.error.lower()

    def test_add_control_rule_entity_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should fail if entity does not exist."""
        mock_schema_repository.exists.return_value = False

        result = usecases.add_control_rule(
            entity_id="nonexistent",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="formula",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_add_control_rule_field_not_found(
        self,
        usecases: SchemaUseCases,
        mock_entity: Mock,
    ) -> None:
        """Should fail if field does not exist in entity."""
        result = usecases.add_control_rule(
            entity_id="test_entity",
            field_id="nonexistent_field",
            rule_type="VISIBILITY",
            formula_text="formula",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_add_control_rule_blocked_by_validation(
        self,
        usecases: SchemaUseCases,
        mock_control_rule_usecases: Mock,
    ) -> None:
        """Should fail if formula validation returns BLOCKED status."""
        from doc_helper.application.dto.control_rule_dto import (
            ControlRuleResultDTO,
            ControlRuleStatus,
        )

        mock_result = ControlRuleResultDTO(
            status=ControlRuleStatus.BLOCKED,
            rule=None,
            block_reason="Parse error: invalid syntax",
        )
        mock_control_rule_usecases.validate_control_rule.return_value = mock_result

        result = usecases.add_control_rule(
            entity_id="test_entity",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="invalid formula",
        )

        assert result.success is False
        assert "blocked" in result.error.lower()

    def test_add_control_rule_duplicate_type_rejected(
        self,
        usecases: SchemaUseCases,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should reject adding duplicate rule type to same field."""
        # Setup: field already has VISIBILITY rule
        existing_rule = ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="existing",
        )
        field_with_rule = replace(mock_field_definition, control_rules=(existing_rule,))
        mock_entity.fields = {FieldDefinitionId("test_field"): field_with_rule}

        result = usecases.add_control_rule(
            entity_id="test_entity",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="new formula",
        )

        assert result.success is False
        assert "already has" in result.error.lower()


class TestSchemaUseCasesUpdateControlRule:
    """Tests for update_control_rule in SchemaUseCases."""

    @pytest.fixture
    def existing_rule(self) -> ControlRuleExportDTO:
        """Create existing control rule."""
        return ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="original_formula",
        )

    @pytest.fixture
    def mock_field_definition(
        self, existing_rule: ControlRuleExportDTO
    ) -> FieldDefinition:
        """Create mock field definition with existing control rule."""
        return FieldDefinition(
            id=FieldDefinitionId("test_field"),
            label_key=TranslationKey("field.test"),
            field_type=FieldType.TEXT,
            control_rules=(existing_rule,),
        )

    @pytest.fixture
    def mock_entity(self, mock_field_definition: FieldDefinition) -> Mock:
        """Create mock entity with field."""
        entity = Mock()
        entity.fields = {FieldDefinitionId("test_field"): mock_field_definition}
        entity.update_field = Mock()
        entity.id = EntityDefinitionId("test_entity")
        return entity

    @pytest.fixture
    def mock_schema_repository(self, mock_entity: Mock) -> Mock:
        """Create mock schema repository."""
        repository = Mock()
        repository.exists = Mock(return_value=True)
        repository.get_by_id = Mock(return_value=Success(mock_entity))
        repository.save = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key
        return service

    @pytest.fixture
    def mock_control_rule_usecases(self) -> Mock:
        """Create mock ControlRuleUseCases."""
        from doc_helper.application.dto.control_rule_dto import (
            ControlRuleResultDTO,
            ControlRuleStatus,
        )

        usecases = Mock()
        mock_result = ControlRuleResultDTO(
            status=ControlRuleStatus.ALLOWED,
            rule=None,
            block_reason=None,
        )
        usecases.validate_control_rule = Mock(return_value=mock_result)
        return usecases

    @pytest.fixture
    def usecases(
        self,
        mock_schema_repository: Mock,
        mock_relationship_repository: Mock,
        mock_translation_service: Mock,
        mock_control_rule_usecases: Mock,
    ) -> SchemaUseCases:
        """Create SchemaUseCases with mock dependencies."""
        uc = SchemaUseCases(
            schema_repository=mock_schema_repository,
            relationship_repository=mock_relationship_repository,
            translation_service=mock_translation_service,
        )
        uc._control_rule_usecases = mock_control_rule_usecases
        return uc

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    def test_update_control_rule_success(
        self,
        usecases: SchemaUseCases,
    ) -> None:
        """Should successfully update control rule formula."""
        result = usecases.update_control_rule(
            entity_id="test_entity",
            field_id="test_field",
            rule_type="VISIBILITY",
            formula_text="updated_formula",
        )

        assert result.success is True
        assert result.value == "test_field"

    # =========================================================================
    # FAILURE TESTS
    # =========================================================================

    def test_update_nonexistent_rule_rejected(
        self,
        usecases: SchemaUseCases,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should fail if rule type does not exist on field."""
        # Field has VISIBILITY, try to update ENABLED
        result = usecases.update_control_rule(
            entity_id="test_entity",
            field_id="test_field",
            rule_type="ENABLED",
            formula_text="formula",
        )

        assert result.success is False
        assert "not found" in result.error.lower() or "no" in result.error.lower()


class TestSchemaUseCasesDeleteControlRule:
    """Tests for delete_control_rule in SchemaUseCases."""

    @pytest.fixture
    def existing_rule(self) -> ControlRuleExportDTO:
        """Create existing control rule."""
        return ControlRuleExportDTO(
            rule_type="VISIBILITY",
            target_field_id="test_field",
            formula_text="formula",
        )

    @pytest.fixture
    def mock_field_definition(
        self, existing_rule: ControlRuleExportDTO
    ) -> FieldDefinition:
        """Create mock field definition with existing control rule."""
        return FieldDefinition(
            id=FieldDefinitionId("test_field"),
            label_key=TranslationKey("field.test"),
            field_type=FieldType.TEXT,
            control_rules=(existing_rule,),
        )

    @pytest.fixture
    def mock_entity(self, mock_field_definition: FieldDefinition) -> Mock:
        """Create mock entity with field."""
        entity = Mock()
        entity.fields = {FieldDefinitionId("test_field"): mock_field_definition}
        entity.update_field = Mock()
        entity.id = EntityDefinitionId("test_entity")
        return entity

    @pytest.fixture
    def mock_schema_repository(self, mock_entity: Mock) -> Mock:
        """Create mock schema repository."""
        repository = Mock()
        repository.exists = Mock(return_value=True)
        repository.get_by_id = Mock(return_value=Success(mock_entity))
        repository.save = Mock(return_value=Success(None))
        return repository

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key
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
    # SUCCESS TESTS
    # =========================================================================

    def test_delete_control_rule_success(
        self,
        usecases: SchemaUseCases,
    ) -> None:
        """Should successfully delete existing control rule."""
        result = usecases.delete_control_rule(
            entity_id="test_entity",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.success is True

    # =========================================================================
    # FAILURE TESTS
    # =========================================================================

    def test_delete_nonexistent_rule_rejected(
        self,
        usecases: SchemaUseCases,
    ) -> None:
        """Should fail if rule type does not exist on field."""
        result = usecases.delete_control_rule(
            entity_id="test_entity",
            field_id="test_field",
            rule_type="ENABLED",  # Field has VISIBILITY, not ENABLED
        )

        assert result.success is False
        assert "not found" in result.error.lower() or "no" in result.error.lower()

    def test_delete_entity_not_found(
        self,
        usecases: SchemaUseCases,
        mock_schema_repository: Mock,
    ) -> None:
        """Should fail if entity does not exist."""
        mock_schema_repository.exists.return_value = False

        result = usecases.delete_control_rule(
            entity_id="nonexistent",
            field_id="test_field",
            rule_type="VISIBILITY",
        )

        assert result.success is False
        assert "not found" in result.error.lower()


class TestSchemaUseCasesListControlRules:
    """Tests for list_control_rules_for_field in SchemaUseCases."""

    @pytest.fixture
    def control_rules(self) -> tuple:
        """Create multiple control rules."""
        return (
            ControlRuleExportDTO(
                rule_type="VISIBILITY",
                target_field_id="test_field",
                formula_text="visibility_formula",
            ),
            ControlRuleExportDTO(
                rule_type="ENABLED",
                target_field_id="test_field",
                formula_text="enabled_formula",
            ),
        )

    @pytest.fixture
    def mock_field_definition(self, control_rules: tuple) -> FieldDefinition:
        """Create mock field definition with control rules."""
        return FieldDefinition(
            id=FieldDefinitionId("test_field"),
            label_key=TranslationKey("field.test"),
            field_type=FieldType.TEXT,
            control_rules=control_rules,
        )

    @pytest.fixture
    def mock_entity(self, mock_field_definition: FieldDefinition) -> Mock:
        """Create mock entity with field."""
        entity = Mock()
        entity.fields = {FieldDefinitionId("test_field"): mock_field_definition}
        entity.id = EntityDefinitionId("test_entity")
        return entity

    @pytest.fixture
    def mock_schema_repository(self, mock_entity: Mock) -> Mock:
        """Create mock schema repository."""
        repository = Mock()
        repository.exists = Mock(return_value=True)
        repository.get_by_id = Mock(return_value=Success(mock_entity))
        return repository

    @pytest.fixture
    def mock_relationship_repository(self) -> Mock:
        """Create mock relationship repository."""
        return Mock()

    @pytest.fixture
    def mock_translation_service(self) -> Mock:
        """Create mock translation service."""
        service = Mock()
        service.translate.side_effect = lambda key: key
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

    def test_list_control_rules_success(
        self,
        usecases: SchemaUseCases,
    ) -> None:
        """Should list all control rules for a field."""
        rules = usecases.list_control_rules_for_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        # Returns tuple of ControlRuleExportDTO directly
        assert len(rules) == 2
        rule_types = {r.rule_type for r in rules}
        assert "VISIBILITY" in rule_types
        assert "ENABLED" in rule_types

    def test_list_control_rules_empty_field(
        self,
        usecases: SchemaUseCases,
        mock_entity: Mock,
        mock_field_definition: FieldDefinition,
    ) -> None:
        """Should return empty tuple for field with no rules."""
        field_no_rules = replace(mock_field_definition, control_rules=())
        mock_entity.fields = {FieldDefinitionId("test_field"): field_no_rules}

        rules = usecases.list_control_rules_for_field(
            entity_id="test_entity",
            field_id="test_field",
        )

        # Returns empty tuple directly
        assert rules == ()
