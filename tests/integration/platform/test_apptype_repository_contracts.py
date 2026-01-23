"""T1: AppType Repository Contract Smoke Test.

This test ensures that every AppType's get_schema_repository() returns
an object that fully implements ISchemaRepository (all abstract methods).

This test would have caught the runtime failure where SqliteSchemaRepository
was missing 5 abstract method implementations.

Purpose: Prevent interface contract violations from reaching production.
"""

import inspect
from abc import abstractmethod

import pytest

from doc_helper.app_types.contracts.i_app_type import IAppType
from doc_helper.app_types.soil_investigation import SoilInvestigationAppType
from doc_helper.domain.schema.schema_repository import ISchemaRepository


def get_abstract_methods(cls: type) -> set[str]:
    """Extract all abstract method names from an ABC class."""
    abstract_methods = set()
    for name, method in inspect.getmembers(cls):
        if getattr(method, "__isabstractmethod__", False):
            abstract_methods.add(name)
    return abstract_methods


class TestAppTypeRepositoryContracts:
    """Smoke tests for AppType repository interface compliance."""

    # All abstract methods that ISchemaRepository requires
    REQUIRED_METHODS = {
        "get_by_id",
        "get_all",
        "get_root_entity",
        "exists",
        "get_child_entities",
        "save",
        "update",
        "delete",
        "get_entity_dependencies",
        "get_field_dependencies",
    }

    def test_ischema_repository_has_expected_abstract_methods(self) -> None:
        """Verify our test knows the correct abstract methods."""
        actual_methods = get_abstract_methods(ISchemaRepository)
        assert actual_methods == self.REQUIRED_METHODS, (
            f"ISchemaRepository abstract methods changed. "
            f"Expected: {self.REQUIRED_METHODS}, Got: {actual_methods}"
        )

    def test_soil_investigation_apptype_instantiation(self) -> None:
        """SoilInvestigationAppType can be instantiated."""
        app_type = SoilInvestigationAppType()
        assert app_type is not None
        assert isinstance(app_type, IAppType)

    def test_soil_investigation_repository_is_ischema_repository(self) -> None:
        """SoilInvestigationAppType.get_schema_repository() returns ISchemaRepository.

        Note: This test requires config.db to exist. If not available,
        test is skipped (not failed) as this is an integration test.
        """
        app_type = SoilInvestigationAppType()

        try:
            repo = app_type.get_schema_repository()
        except FileNotFoundError:
            pytest.skip("config.db not available - skipping repository test")

        assert isinstance(repo, ISchemaRepository), (
            f"get_schema_repository() returned {type(repo).__name__}, "
            f"expected ISchemaRepository implementation"
        )

    def test_soil_investigation_repository_implements_all_abstract_methods(
        self,
    ) -> None:
        """SoilInvestigationAppType's repository implements all ISchemaRepository methods.

        This is the critical test that would have caught the runtime failure.
        """
        app_type = SoilInvestigationAppType()

        try:
            repo = app_type.get_schema_repository()
        except FileNotFoundError:
            pytest.skip("config.db not available - skipping repository test")

        repo_type = type(repo)

        # Check each required method exists and is not abstract
        missing_methods = []
        abstract_methods = []

        for method_name in self.REQUIRED_METHODS:
            if not hasattr(repo, method_name):
                missing_methods.append(method_name)
            else:
                method = getattr(repo, method_name)
                if getattr(method, "__isabstractmethod__", False):
                    abstract_methods.append(method_name)

        error_parts = []
        if missing_methods:
            error_parts.append(f"Missing methods: {missing_methods}")
        if abstract_methods:
            error_parts.append(f"Still abstract: {abstract_methods}")

        assert not error_parts, (
            f"{repo_type.__name__} does not fully implement ISchemaRepository. "
            + "; ".join(error_parts)
        )

    def test_soil_investigation_repository_methods_are_callable(self) -> None:
        """All repository methods are callable (not just defined)."""
        app_type = SoilInvestigationAppType()

        try:
            repo = app_type.get_schema_repository()
        except FileNotFoundError:
            pytest.skip("config.db not available - skipping repository test")

        for method_name in self.REQUIRED_METHODS:
            method = getattr(repo, method_name)
            assert callable(method), f"{method_name} is not callable"


class TestAppTypeRepositoryContractEnforcement:
    """Tests that validate interface contract enforcement at import time."""

    def test_cannot_instantiate_abstract_ischema_repository(self) -> None:
        """ISchemaRepository cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            ISchemaRepository()  # type: ignore

    def test_incomplete_repository_cannot_be_instantiated(self) -> None:
        """A class missing abstract methods cannot be instantiated.

        This demonstrates the Python ABC mechanism that should catch violations.
        """
        # Define an incomplete implementation
        class IncompleteRepository(ISchemaRepository):
            # Only implement some methods
            def get_by_id(self, entity_id):
                pass

            def get_all(self):
                pass

            # Missing: get_root_entity, exists, get_child_entities,
            #          save, update, delete, get_entity_dependencies,
            #          get_field_dependencies

        with pytest.raises(TypeError, match="abstract"):
            IncompleteRepository()  # type: ignore
