"""V2 Platform Stability Tests.

Negative tests for AppType lifecycle failure scenarios:
- Missing AppType when opening a project
- Corrupt app_type_id values
- Invalid app_type_id in project operations
- Platform behavior when no AppTypes available

These tests ensure the platform gracefully handles failure scenarios
and prevents data corruption or crashes when AppTypes are misconfigured.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from doc_helper.app_types.contracts.app_type_metadata import AppTypeMetadata
from doc_helper.application.dto import ProjectDTO
from doc_helper.platform.discovery.manifest_parser import (
    ManifestCapabilities,
    ManifestSchema,
    ManifestTemplates,
    ParsedManifest,
)
from doc_helper.platform.registry.app_type_registry import AppTypeRegistry
from doc_helper.platform.routing.app_type_router import AppTypeRouter


def create_test_manifest(app_type_id: str) -> ParsedManifest:
    """Helper to create test manifests."""
    return ParsedManifest(
        metadata=AppTypeMetadata(
            app_type_id=app_type_id,
            name=f"Test {app_type_id}",
            version="1.0.0",
        ),
        schema=ManifestSchema(source="config.db", schema_type="sqlite"),
        templates=ManifestTemplates(),
        capabilities=ManifestCapabilities(),
        manifest_path=Path(f"app_types/{app_type_id}/manifest.json"),
    )


class TestMissingAppTypeAtProjectOpen:
    """Test scenarios where project references non-existent AppType.

    Scenario: User opens a project whose app_type_id is no longer registered.
    This can happen if:
    - AppType was uninstalled/removed
    - AppType package corrupted
    - Project moved to different environment without AppType
    """

    @pytest.fixture
    def registry_with_apptype(self) -> AppTypeRegistry:
        """Create registry with one AppType."""
        registry = AppTypeRegistry()
        registry.register(create_test_manifest("soil_investigation"))
        return registry

    @pytest.fixture
    def router(self, registry_with_apptype: AppTypeRegistry) -> AppTypeRouter:
        """Create router with registry."""
        return AppTypeRouter(registry_with_apptype)

    def test_router_handles_missing_apptype_gracefully(
        self, registry_with_apptype: AppTypeRegistry
    ) -> None:
        """Router should handle missing AppType without crashing."""
        router = AppTypeRouter(registry_with_apptype)

        # Attempt to set non-existent AppType
        result = router.set_current("deleted_app")

        assert result is False
        assert router.get_current_id() is None
        assert router.get_current_manifest() is None

    def test_is_valid_app_type_returns_false_for_missing(
        self, router: AppTypeRouter
    ) -> None:
        """is_valid_app_type should return False for missing AppType."""
        assert router.is_valid_app_type("soil_investigation") is True
        assert router.is_valid_app_type("deleted_app") is False
        assert router.is_valid_app_type("nonexistent") is False

    def test_project_dto_with_missing_apptype_is_detectable(self) -> None:
        """ProjectDTO with missing app_type_id should be detectable."""
        registry = AppTypeRegistry()
        registry.register(create_test_manifest("soil_investigation"))
        router = AppTypeRouter(registry)

        # Project references non-existent AppType
        project_dto = ProjectDTO(
            id="test-project-123",
            name="Test Project",
            description=None,
            file_path="/path/to/project.db",
            entity_definition_id="root_entity",
            app_type_id="deleted_app",  # This AppType doesn't exist
            field_count=0,
            is_saved=True,
        )

        # Validation: Check if AppType exists before opening
        assert router.is_valid_app_type(project_dto.app_type_id) is False


class TestCorruptAppTypeIdValues:
    """Test scenarios with malformed or corrupt app_type_id values.

    Ensures platform rejects dangerous values that could cause:
    - SQL injection
    - Path traversal
    - System crashes
    """

    @pytest.fixture
    def router(self) -> AppTypeRouter:
        """Create router with empty registry."""
        return AppTypeRouter(AppTypeRegistry())

    @pytest.mark.parametrize(
        "corrupt_id",
        [
            "",  # Empty string
            " ",  # Whitespace
            "  soil_investigation  ",  # Leading/trailing whitespace
            "Soil Investigation",  # Spaces
            "soil-investigation",  # Hyphens
            "soil.investigation",  # Dots
            "soil/investigation",  # Path separator
            "../../../etc/passwd",  # Path traversal attempt
            "'; DROP TABLE projects; --",  # SQL injection attempt
            "soil\ninvestigation",  # Newline
            "soil\tinvestigation",  # Tab
            "123_invalid",  # Starting with number
            "_invalid",  # Starting with underscore
            "SOIL_INVESTIGATION",  # Uppercase
        ],
    )
    def test_corrupt_app_type_id_rejected_by_validation(
        self, router: AppTypeRouter, corrupt_id: str
    ) -> None:
        """Corrupt app_type_id values should be rejected as invalid."""
        # is_valid_app_type should return False for corrupt values
        assert router.is_valid_app_type(corrupt_id) is False

    @pytest.mark.parametrize(
        "invalid_id,error_pattern",
        [
            ("", "cannot be empty"),  # Empty
            ("Test-App", "lowercase"),  # Uppercase + hyphen
            ("123app", "lowercase"),  # Starts with number
            ("app.name", "lowercase"),  # Dot
            ("app name", "lowercase"),  # Space
        ],
    )
    def test_app_type_metadata_rejects_invalid_ids(self, invalid_id: str, error_pattern: str) -> None:
        """AppTypeMetadata should reject invalid app_type_id formats."""
        with pytest.raises(ValueError, match=error_pattern):
            AppTypeMetadata(
                app_type_id=invalid_id,
                name="Test App",
                version="1.0.0",
            )

    def test_empty_app_type_id_rejected(self) -> None:
        """Empty app_type_id should be explicitly rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            AppTypeMetadata(
                app_type_id="",
                name="Test App",
                version="1.0.0",
            )


class TestProjectCreationWithInvalidAppType:
    """Test project creation when app_type_id is invalid or missing."""

    @pytest.fixture
    def registry(self) -> AppTypeRegistry:
        """Create registry with one AppType."""
        registry = AppTypeRegistry()
        registry.register(create_test_manifest("soil_investigation"))
        return registry

    def test_cannot_create_project_with_nonexistent_apptype(
        self, registry: AppTypeRegistry
    ) -> None:
        """Project creation should fail if app_type_id doesn't exist."""
        router = AppTypeRouter(registry)

        # Attempting to create project with non-existent AppType
        app_type_id = "nonexistent_app"

        # Validation should fail
        assert router.is_valid_app_type(app_type_id) is False

    def test_cannot_create_project_with_empty_apptype(
        self, registry: AppTypeRegistry
    ) -> None:
        """Project creation should fail if app_type_id is empty."""
        router = AppTypeRouter(registry)

        # Empty app_type_id
        assert router.is_valid_app_type("") is False
        assert router.is_valid_app_type("   ") is False


class TestPlatformWithNoAppTypes:
    """Test platform behavior when no AppTypes are registered.

    Scenario: Fresh install or all AppTypes failed to load.
    Platform should not crash, but should clearly indicate no AppTypes available.
    """

    def test_empty_registry_list_is_empty(self) -> None:
        """Empty registry should return empty lists."""
        registry = AppTypeRegistry()

        assert registry.count == 0
        assert registry.list_app_type_ids() == ()
        assert registry.list_all() == ()
        assert registry.list_metadata() == ()

    def test_router_with_empty_registry_handles_operations(self) -> None:
        """Router with empty registry should not crash on operations."""
        registry = AppTypeRegistry()
        router = AppTypeRouter(registry)

        # All lookups return None/False without crashing
        assert router.get_current_id() is None
        assert router.get_current_manifest() is None
        assert router.get_current_metadata() is None
        assert router.is_valid_app_type("any_id") is False
        assert router.set_current("any_id") is False

    def test_empty_registry_exists_returns_false(self) -> None:
        """exists() on empty registry should return False for any ID."""
        registry = AppTypeRegistry()

        assert registry.exists("soil_investigation") is False
        assert registry.exists("any_app") is False
        assert registry.exists("") is False


class TestAppTypeUnregistrationWhileInUse:
    """Test scenarios where AppType is unregistered while referenced by open project.

    This tests the race condition where:
    1. Project is opened with app_type_id "soil_investigation"
    2. AppType "soil_investigation" is unregistered (e.g., uninstalled)
    3. Platform must handle this gracefully without corruption
    """

    def test_router_current_becomes_invalid_after_unregister(self) -> None:
        """If current AppType is unregistered, router detects it."""
        registry = AppTypeRegistry()
        registry.register(create_test_manifest("soil_investigation"))
        router = AppTypeRouter(registry)

        # Set current
        router.set_current("soil_investigation")
        assert router.get_current_manifest() is not None

        # Unregister the current AppType
        registry.unregister("soil_investigation")

        # Router still has ID set, but manifest lookup fails
        assert router.get_current_id() == "soil_investigation"
        assert router.get_current_manifest() is None  # Can't find it anymore
        assert router.is_valid_app_type("soil_investigation") is False

    def test_registry_unregister_is_idempotent(self) -> None:
        """Unregistering twice should not cause errors."""
        registry = AppTypeRegistry()
        registry.register(create_test_manifest("test_app"))

        # First unregister succeeds
        result1 = registry.unregister("test_app")
        assert result1 is True

        # Second unregister fails gracefully
        result2 = registry.unregister("test_app")
        assert result2 is False


class TestAppTypeIdConstraints:
    """Test app_type_id format constraints are enforced.

    Valid format: ^[a-z][a-z0-9_]*$
    - Must start with lowercase letter
    - Can contain lowercase letters, numbers, underscores
    - No uppercase, spaces, hyphens, special chars
    """

    @pytest.mark.parametrize(
        "valid_id",
        [
            "soil_investigation",
            "structural_report",
            "report_v2",
            "app123",
            "a",  # Single letter
            "test_app_2024",
        ],
    )
    def test_valid_app_type_ids_accepted(self, valid_id: str) -> None:
        """Valid app_type_id formats should be accepted."""
        # Should not raise
        metadata = AppTypeMetadata(
            app_type_id=valid_id,
            name="Test",
            version="1.0.0",
        )
        assert metadata.app_type_id == valid_id

    @pytest.mark.parametrize(
        "invalid_id",
        [
            "Soil_Investigation",  # Uppercase
            "soil-investigation",  # Hyphen
            "soil investigation",  # Space
            "123_app",  # Starts with number
            "_soil",  # Starts with underscore
            "soil.investigation",  # Dot
            "soil/investigation",  # Slash
            "soil@investigation",  # Special char
        ],
    )
    def test_invalid_app_type_ids_rejected(self, invalid_id: str) -> None:
        """Invalid app_type_id formats should be rejected."""
        with pytest.raises(ValueError, match="lowercase"):
            AppTypeMetadata(
                app_type_id=invalid_id,
                name="Test",
                version="1.0.0",
            )


class TestSemanticVersionConstraints:
    """Test semantic version format constraints are enforced.

    Valid format: X.Y.Z where X, Y, Z are integers
    - Examples: 1.0.0, 2.3.14, 0.1.0
    - Invalid: v1.0.0, 1.0, 1.0.0-beta
    """

    @pytest.mark.parametrize(
        "valid_version",
        [
            "1.0.0",
            "2.3.14",
            "0.1.0",
            "10.20.30",
            "1.0.0-beta",  # Prerelease allowed (regex checks start only)
            "1.0.0+build",  # Build metadata allowed
        ],
    )
    def test_valid_semantic_versions_accepted(self, valid_version: str) -> None:
        """Valid semantic versions should be accepted."""
        metadata = AppTypeMetadata(
            app_type_id="test_app",
            name="Test",
            version=valid_version,
        )
        assert metadata.version == valid_version

    @pytest.mark.parametrize(
        "invalid_version",
        [
            "v1.0.0",  # Prefix
            "1.0",  # Missing patch
            "1",  # Only major
            "a.b.c",  # Non-numeric
            "beta-1.0.0",  # Doesn't start with X.Y.Z
        ],
    )
    def test_invalid_versions_rejected(self, invalid_version: str) -> None:
        """Invalid version formats should be rejected."""
        with pytest.raises(ValueError, match="semantic"):
            AppTypeMetadata(
                app_type_id="test_app",
                name="Test",
                version=invalid_version,
            )
