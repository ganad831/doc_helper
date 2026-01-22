"""Unit tests for SchemaImportValidationService (Phase 4)."""

import pytest

from doc_helper.application.services.schema_import_validation_service import (
    KNOWN_CONSTRAINT_TYPES,
    SchemaImportValidationService,
)


class TestSchemaImportValidationService:
    """Tests for import validation service."""

    @pytest.fixture
    def service(self) -> SchemaImportValidationService:
        """Create validation service."""
        return SchemaImportValidationService()

    @pytest.fixture
    def valid_minimal_schema(self) -> dict:
        """Create minimal valid schema data."""
        return {
            "schema_id": "test_schema",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "text",
                            "label_key": "field.name",
                            "required": True,
                            "options": [],
                            "constraints": [],
                        }
                    ],
                }
            ],
        }

    @pytest.fixture
    def valid_full_schema(self) -> dict:
        """Create full valid schema with all features."""
        return {
            "schema_id": "soil_investigation",
            "version": "1.0.0",
            "entities": [
                {
                    "id": "project",
                    "name_key": "entity.project",
                    "description_key": "entity.project.description",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "name",
                            "field_type": "text",
                            "label_key": "field.name",
                            "help_text_key": "field.name.help",
                            "required": True,
                            "default_value": None,
                            "options": [],
                            "constraints": [
                                {
                                    "constraint_type": "RequiredConstraint",
                                    "parameters": {},
                                },
                                {
                                    "constraint_type": "MinLengthConstraint",
                                    "parameters": {"min_length": 3},
                                },
                            ],
                        },
                        {
                            "id": "status",
                            "field_type": "dropdown",
                            "label_key": "field.status",
                            "required": True,
                            "options": [
                                {"value": "active", "label_key": "status.active"},
                                {"value": "completed", "label_key": "status.completed"},
                            ],
                            "constraints": [],
                        },
                    ],
                },
                {
                    "id": "sample",
                    "name_key": "entity.sample",
                    "is_root_entity": False,
                    "fields": [
                        {
                            "id": "depth",
                            "field_type": "number",
                            "label_key": "field.depth",
                            "required": True,
                            "options": [],
                            "constraints": [
                                {
                                    "constraint_type": "MinValueConstraint",
                                    "parameters": {"min_value": 0},
                                },
                                {
                                    "constraint_type": "MaxValueConstraint",
                                    "parameters": {"max_value": 100},
                                },
                            ],
                        },
                    ],
                },
            ],
        }

    # =========================================================================
    # Structure Validation Tests
    # =========================================================================

    def test_valid_minimal_schema_parses(
        self,
        service: SchemaImportValidationService,
        valid_minimal_schema: dict,
    ) -> None:
        """Should successfully parse valid minimal schema."""
        result = service.validate_json_data(valid_minimal_schema)
        assert result.is_success()
        assert result.value["schema_id"] == "test_schema"
        assert len(result.value["entities"]) == 1

    def test_valid_full_schema_parses(
        self,
        service: SchemaImportValidationService,
        valid_full_schema: dict,
    ) -> None:
        """Should successfully parse full valid schema."""
        result = service.validate_json_data(valid_full_schema)
        assert result.is_success()
        assert result.value["version"] == "1.0.0"
        assert len(result.value["entities"]) == 2

    def test_missing_schema_id_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when schema_id is missing."""
        data = {
            "entities": [],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()
        errors = result.error
        assert any(e.category == "missing_required" and "schema_id" in e.message for e in errors)

    def test_empty_schema_id_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when schema_id is empty."""
        data = {
            "schema_id": "   ",
            "entities": [],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()
        errors = result.error
        assert any(e.category == "invalid_value" and "empty" in e.message.lower() for e in errors)

    def test_missing_entities_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when entities is missing."""
        data = {
            "schema_id": "test",
        }
        result = service.validate_json_data(data)
        assert result.is_failure()
        errors = result.error
        assert any(e.category == "missing_required" and "entities" in e.message for e in errors)

    def test_entities_not_array_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when entities is not an array."""
        data = {
            "schema_id": "test",
            "entities": "not an array",
        }
        result = service.validate_json_data(data)
        assert result.is_failure()
        errors = result.error
        assert any(e.category == "invalid_type" for e in errors)

    def test_root_not_object_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when root is not an object."""
        result = service.validate_json_data(["array"])
        assert result.is_failure()

    # =========================================================================
    # Entity Validation Tests
    # =========================================================================

    def test_entity_missing_id_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when entity is missing id."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "name_key": "entity.test",
                    "is_root_entity": True,
                    "fields": [],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()
        errors = result.error
        assert any("id" in e.message for e in errors)

    def test_entity_missing_name_key_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when entity is missing name_key."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "test",
                    "is_root_entity": True,
                    "fields": [],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()
        errors = result.error
        assert any("name_key" in e.message for e in errors)

    def test_entity_missing_is_root_entity_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when entity is missing is_root_entity."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "test",
                    "name_key": "entity.test",
                    "fields": [],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()

    def test_entity_with_no_fields_warns(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should warn but allow entity with no fields (Decision 6)."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "empty_entity",
                    "name_key": "entity.empty",
                    "is_root_entity": True,
                    "fields": [],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_success()
        warnings = result.value["warnings"]
        assert any(w.category == "empty_entity" for w in warnings)

    # =========================================================================
    # Field Validation Tests
    # =========================================================================

    def test_field_missing_id_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when field is missing id."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "test",
                    "name_key": "entity.test",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "field_type": "text",
                            "label_key": "field.test",
                            "required": True,
                            "options": [],
                            "constraints": [],
                        }
                    ],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()

    def test_field_invalid_type_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when field has invalid field_type."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "test",
                    "name_key": "entity.test",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "test_field",
                            "field_type": "invalid_type",
                            "label_key": "field.test",
                            "required": True,
                            "options": [],
                            "constraints": [],
                        }
                    ],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()
        errors = result.error
        assert any("invalid_type" in e.message.lower() or "field_type" in e.location for e in errors)

    def test_field_all_valid_types_accepted(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should accept all 12 valid field types."""
        # Some field types have special requirements:
        # - DROPDOWN, RADIO require options
        # - CALCULATED requires formula
        # - LOOKUP requires lookup_entity_id
        # - TABLE requires child_entity_id
        field_configs = {
            "text": {},
            "textarea": {},
            "number": {},
            "date": {},
            "dropdown": {"options": [{"value": "opt1", "label_key": "option.1"}]},
            "checkbox": {},
            "radio": {"options": [{"value": "opt1", "label_key": "option.1"}]},
            "calculated": {"formula": "1 + 1"},
            "lookup": {"lookup_entity_id": "other_entity"},
            "file": {},
            "image": {},
            "table": {"child_entity_id": "child_entity"},
        }
        for field_type, extra_fields in field_configs.items():
            field_data = {
                "id": "test_field",
                "field_type": field_type,
                "label_key": "field.test",
                "required": True,
                "options": [],
                "constraints": [],
            }
            field_data.update(extra_fields)
            data = {
                "schema_id": "test",
                "entities": [
                    {
                        "id": "test",
                        "name_key": "entity.test",
                        "is_root_entity": True,
                        "fields": [field_data],
                    }
                ],
            }
            result = service.validate_json_data(data)
            assert result.is_success(), f"Field type {field_type} should be valid, got: {result.error if result.is_failure() else 'success'}"

    # =========================================================================
    # Constraint Validation Tests (Decision 7)
    # =========================================================================

    def test_unknown_constraint_type_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when constraint type is unknown (Decision 7)."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "test",
                    "name_key": "entity.test",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "test_field",
                            "field_type": "text",
                            "label_key": "field.test",
                            "required": True,
                            "options": [],
                            "constraints": [
                                {
                                    "constraint_type": "UnknownConstraint",
                                    "parameters": {},
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()
        errors = result.error
        assert any(e.category == "unknown_constraint" for e in errors)

    def test_all_known_constraint_types_accepted(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should accept all known constraint types."""
        constraint_configs = [
            ("RequiredConstraint", {}),
            ("MinLengthConstraint", {"min_length": 5}),
            ("MaxLengthConstraint", {"max_length": 100}),
            ("MinValueConstraint", {"min_value": 0}),
            ("MaxValueConstraint", {"max_value": 100}),
            ("PatternConstraint", {"pattern": r"^[A-Z]+$"}),
            ("AllowedValuesConstraint", {"allowed_values": ["a", "b"]}),
            ("FileExtensionConstraint", {"allowed_extensions": [".pdf", ".txt"]}),
            ("MaxFileSizeConstraint", {"max_size_bytes": 1000}),
        ]

        for constraint_type, params in constraint_configs:
            data = {
                "schema_id": "test",
                "entities": [
                    {
                        "id": "test",
                        "name_key": "entity.test",
                        "is_root_entity": True,
                        "fields": [
                            {
                                "id": "test_field",
                                "field_type": "text",
                                "label_key": "field.test",
                                "required": True,
                                "options": [],
                                "constraints": [
                                    {
                                        "constraint_type": constraint_type,
                                        "parameters": params,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
            result = service.validate_json_data(data)
            assert result.is_success(), f"Constraint {constraint_type} should be valid"

    # =========================================================================
    # Option Validation Tests
    # =========================================================================

    def test_option_missing_value_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when option is missing value."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "test",
                    "name_key": "entity.test",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "test_field",
                            "field_type": "dropdown",
                            "label_key": "field.test",
                            "required": True,
                            "options": [
                                {"label_key": "option.a"}
                            ],
                            "constraints": [],
                        }
                    ],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()

    def test_option_missing_label_key_fails(
        self,
        service: SchemaImportValidationService,
    ) -> None:
        """Should fail when option is missing label_key."""
        data = {
            "schema_id": "test",
            "entities": [
                {
                    "id": "test",
                    "name_key": "entity.test",
                    "is_root_entity": True,
                    "fields": [
                        {
                            "id": "test_field",
                            "field_type": "dropdown",
                            "label_key": "field.test",
                            "required": True,
                            "options": [
                                {"value": "a"}
                            ],
                            "constraints": [],
                        }
                    ],
                }
            ],
        }
        result = service.validate_json_data(data)
        assert result.is_failure()

    # =========================================================================
    # Domain Object Conversion Tests
    # =========================================================================

    def test_converts_to_entity_definitions(
        self,
        service: SchemaImportValidationService,
        valid_full_schema: dict,
    ) -> None:
        """Should convert to EntityDefinition domain objects."""
        result = service.validate_json_data(valid_full_schema)
        assert result.is_success()

        entities = result.value["entities"]
        assert len(entities) == 2

        # Check first entity
        project = entities[0]
        assert project.id.value == "project"
        assert project.name_key.key == "entity.project"
        assert project.is_root_entity is True
        assert project.field_count == 2

    def test_converts_constraints(
        self,
        service: SchemaImportValidationService,
        valid_full_schema: dict,
    ) -> None:
        """Should convert constraints to domain objects."""
        result = service.validate_json_data(valid_full_schema)
        assert result.is_success()

        entities = result.value["entities"]
        project = entities[0]
        name_field = project.get_field(project.get_all_fields()[0].id)

        # Check constraints
        assert len(name_field.constraints) == 2

    def test_converts_options(
        self,
        service: SchemaImportValidationService,
        valid_full_schema: dict,
    ) -> None:
        """Should convert options to tuples."""
        result = service.validate_json_data(valid_full_schema)
        assert result.is_success()

        entities = result.value["entities"]
        project = entities[0]

        # Find status field (dropdown)
        status_field = None
        for field in project.get_all_fields():
            if field.id.value == "status":
                status_field = field
                break

        assert status_field is not None
        assert len(status_field.options) == 2
        assert status_field.options[0][0] == "active"

    # =========================================================================
    # Known Constraint Types Registry
    # =========================================================================

    def test_known_constraint_types_complete(self) -> None:
        """Should have all expected constraint types."""
        expected = {
            "RequiredConstraint",
            "MinLengthConstraint",
            "MaxLengthConstraint",
            "MinValueConstraint",
            "MaxValueConstraint",
            "PatternConstraint",
            "AllowedValuesConstraint",
            "FileExtensionConstraint",
            "MaxFileSizeConstraint",
        }
        assert KNOWN_CONSTRAINT_TYPES == expected
