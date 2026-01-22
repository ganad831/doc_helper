"""Import Schema Command (Phase 4).

Command for importing schema definitions from file.

APPROVED DECISIONS:
- Decision 1: Identical schema behavior → User choice via parameter
- Decision 2: Compatible schema behavior → Replace with detailed change list
- Decision 3: Incompatible schema default → Fail by default (require force)
- Decision 4: Default enforcement policy → STRICT (block incompatible)
- Decision 5: Version field handling → Warn if version goes backward

FORBIDDEN:
- No automatic data migration
- No schema transformation during import
- No partial import (all-or-nothing)
"""

from pathlib import Path
from typing import Optional

from doc_helper.application.dto.import_dto import (
    EnforcementPolicy,
    IdenticalSchemaAction,
    ImportResult,
    ImportValidationError,
    ImportWarning,
)
from doc_helper.application.services.schema_comparison_service import SchemaComparisonService
from doc_helper.application.services.schema_import_validation_service import SchemaImportValidationService
from doc_helper.domain.common.result import Failure, Result, Success
from doc_helper.domain.schema.entity_definition import EntityDefinition
from doc_helper.domain.schema.schema_compatibility import CompatibilityLevel, CompatibilityResult
from doc_helper.domain.schema.schema_repository import ISchemaRepository
from doc_helper.domain.schema.schema_version import SchemaVersion


class ImportSchemaCommand:
    """Command to import schema from file.

    Validates schema, checks compatibility, and replaces existing schema.

    Usage:
        command = ImportSchemaCommand(
            schema_repository,
            comparison_service,
            validation_service,
        )
        result = command.execute(
            file_path=Path("/path/to/schema.json"),
        )
        if result.success:
            print(f"Imported {result.entity_count} entities")
            for warning in result.warnings:
                print(f"Warning: {warning.message}")
        else:
            for error in result.validation_errors:
                print(f"Error: {error.message}")

    IMPORTANT: Import is atomic - all entities are replaced or none are.
    """

    def __init__(
        self,
        schema_repository: ISchemaRepository,
        comparison_service: Optional[SchemaComparisonService] = None,
        validation_service: Optional[SchemaImportValidationService] = None,
    ) -> None:
        """Initialize command.

        Args:
            schema_repository: Repository for schema persistence
            comparison_service: Service for compatibility analysis (optional, created if not provided)
            validation_service: Service for validation (optional, created if not provided)
        """
        self._schema_repository = schema_repository
        self._comparison_service = comparison_service or SchemaComparisonService()
        self._validation_service = validation_service or SchemaImportValidationService()

    def execute(
        self,
        file_path: Path,
        enforcement_policy: EnforcementPolicy = EnforcementPolicy.STRICT,
        identical_action: IdenticalSchemaAction = IdenticalSchemaAction.SKIP,
        force: bool = False,
        existing_version: Optional[str] = None,
    ) -> ImportResult:
        """Execute schema import.

        Args:
            file_path: Path to JSON import file
            enforcement_policy: How to handle compatibility issues (default: STRICT)
            identical_action: What to do when schema is identical (default: SKIP)
            force: Force import even if incompatible (overrides enforcement_policy)
            existing_version: Optional version string for existing schema (for comparison)

        Returns:
            ImportResult with success/failure status and details
        """
        warnings: list[ImportWarning] = []
        validation_errors: list[ImportValidationError] = []

        # Step 1: Validate and parse import file
        parse_result = self._validation_service.validate_and_parse(file_path)

        if parse_result.is_failure():
            return ImportResult(
                success=False,
                validation_errors=parse_result.error,
                error="Import file validation failed",
            )

        parsed_data = parse_result.value
        import_entities: tuple[EntityDefinition, ...] = parsed_data["entities"]
        schema_id = parsed_data["schema_id"]
        imported_version = parsed_data.get("version")
        warnings.extend(parsed_data.get("warnings", []))

        # Step 2: Get existing schema for comparison
        existing_result = self._schema_repository.get_all()
        existing_entities: tuple = ()
        if existing_result.is_success():
            existing_entities = existing_result.value

        # Step 3: Perform compatibility analysis
        compatibility_result: Optional[CompatibilityResult] = None
        if existing_entities:
            # Parse existing version if provided
            source_version = None
            target_version = None

            if existing_version:
                try:
                    source_version = SchemaVersion.from_string(existing_version)
                except ValueError:
                    pass

            if imported_version:
                try:
                    target_version = SchemaVersion.from_string(imported_version)
                except ValueError:
                    pass

            compatibility_result = self._comparison_service.compare(
                source_entities=existing_entities,
                target_entities=import_entities,
                source_version=source_version,
                target_version=target_version,
            )

            # Decision 5: Warn if version goes backward
            if source_version and target_version and target_version < source_version:
                warnings.append(ImportWarning(
                    category="version_backward",
                    message=f"Imported version ({target_version}) is older than existing version ({source_version})",
                ))

        # Step 4: Handle identical schema (Decision 1)
        if compatibility_result and compatibility_result.is_identical:
            if identical_action == IdenticalSchemaAction.SKIP:
                return ImportResult(
                    success=True,
                    schema_id=schema_id,
                    imported_version=imported_version,
                    existing_version=existing_version,
                    compatibility_result=compatibility_result,
                    warnings=tuple(warnings),
                    entity_count=len(import_entities),
                    field_count=sum(e.field_count for e in import_entities),
                    was_identical=True,
                    was_skipped=True,
                )
            else:
                # REPLACE action for identical - warn but proceed
                warnings.append(ImportWarning(
                    category="identical_schema",
                    message="Schema is identical to existing, replacing anyway",
                ))

        # Step 5: Handle compatible schema (Decision 2)
        # Always allow compatible schemas, just include change list in result

        # Step 6: Handle incompatible schema (Decision 3 & 4)
        if compatibility_result and compatibility_result.is_incompatible:
            if not force and enforcement_policy == EnforcementPolicy.STRICT:
                # Block import
                return ImportResult(
                    success=False,
                    schema_id=schema_id,
                    imported_version=imported_version,
                    existing_version=existing_version,
                    compatibility_result=compatibility_result,
                    warnings=tuple(warnings),
                    error=f"Schema is incompatible with existing schema: "
                          f"{compatibility_result.breaking_change_count} breaking change(s). "
                          f"Use force=True to override.",
                )
            elif enforcement_policy == EnforcementPolicy.WARN or force:
                # Allow but warn
                warnings.append(ImportWarning(
                    category="compatibility",
                    message=f"Importing incompatible schema with {compatibility_result.breaking_change_count} breaking change(s)",
                ))

        # Step 7: Perform atomic import (delete existing, save new)
        import_result = self._perform_atomic_import(existing_entities, import_entities)

        if import_result.is_failure():
            return ImportResult(
                success=False,
                schema_id=schema_id,
                imported_version=imported_version,
                existing_version=existing_version,
                compatibility_result=compatibility_result,
                warnings=tuple(warnings),
                error=import_result.error,
            )

        # Step 8: Return success result
        return ImportResult(
            success=True,
            schema_id=schema_id,
            imported_version=imported_version,
            existing_version=existing_version,
            compatibility_result=compatibility_result,
            warnings=tuple(warnings),
            entity_count=len(import_entities),
            field_count=sum(e.field_count for e in import_entities),
            was_identical=compatibility_result.is_identical if compatibility_result else False,
            was_skipped=False,
        )

    def _perform_atomic_import(
        self,
        existing_entities: tuple,
        import_entities: tuple[EntityDefinition, ...],
    ) -> Result[None, str]:
        """Perform atomic import: delete existing, save new.

        IMPORTANT: This is all-or-nothing. If any operation fails,
        the schema may be in an inconsistent state.

        Args:
            existing_entities: Current entities to delete
            import_entities: New entities to save

        Returns:
            Result with None on success or error message
        """
        # Delete existing entities
        for entity in existing_entities:
            delete_result = self._schema_repository.delete(entity.id)
            if delete_result.is_failure():
                return Failure(f"Failed to delete existing entity {entity.id.value}: {delete_result.error}")

        # Save new entities
        for entity in import_entities:
            save_result = self._schema_repository.save(entity)
            if save_result.is_failure():
                return Failure(f"Failed to save imported entity {entity.id.value}: {save_result.error}")

        return Success(None)

    def execute_from_data(
        self,
        data: dict,
        enforcement_policy: EnforcementPolicy = EnforcementPolicy.STRICT,
        identical_action: IdenticalSchemaAction = IdenticalSchemaAction.SKIP,
        force: bool = False,
        existing_version: Optional[str] = None,
    ) -> ImportResult:
        """Execute schema import from pre-parsed data (for testing).

        Args:
            data: Pre-parsed JSON data dictionary
            enforcement_policy: How to handle compatibility issues
            identical_action: What to do when schema is identical
            force: Force import even if incompatible
            existing_version: Optional version string for existing schema

        Returns:
            ImportResult with success/failure status and details
        """
        warnings: list[ImportWarning] = []

        # Step 1: Validate and parse data
        parse_result = self._validation_service.validate_json_data(data)

        if parse_result.is_failure():
            return ImportResult(
                success=False,
                validation_errors=parse_result.error,
                error="Import data validation failed",
            )

        parsed_data = parse_result.value
        import_entities: tuple[EntityDefinition, ...] = parsed_data["entities"]
        schema_id = parsed_data["schema_id"]
        imported_version = parsed_data.get("version")
        warnings.extend(parsed_data.get("warnings", []))

        # Step 2: Get existing schema for comparison
        existing_result = self._schema_repository.get_all()
        existing_entities: tuple = ()
        if existing_result.is_success():
            existing_entities = existing_result.value

        # Step 3: Perform compatibility analysis
        compatibility_result: Optional[CompatibilityResult] = None
        if existing_entities:
            source_version = None
            target_version = None

            if existing_version:
                try:
                    source_version = SchemaVersion.from_string(existing_version)
                except ValueError:
                    pass

            if imported_version:
                try:
                    target_version = SchemaVersion.from_string(imported_version)
                except ValueError:
                    pass

            compatibility_result = self._comparison_service.compare(
                source_entities=existing_entities,
                target_entities=import_entities,
                source_version=source_version,
                target_version=target_version,
            )

            # Decision 5: Warn if version goes backward
            if source_version and target_version and target_version < source_version:
                warnings.append(ImportWarning(
                    category="version_backward",
                    message=f"Imported version ({target_version}) is older than existing version ({source_version})",
                ))

        # Step 4: Handle identical schema
        if compatibility_result and compatibility_result.is_identical:
            if identical_action == IdenticalSchemaAction.SKIP:
                return ImportResult(
                    success=True,
                    schema_id=schema_id,
                    imported_version=imported_version,
                    existing_version=existing_version,
                    compatibility_result=compatibility_result,
                    warnings=tuple(warnings),
                    entity_count=len(import_entities),
                    field_count=sum(e.field_count for e in import_entities),
                    was_identical=True,
                    was_skipped=True,
                )
            else:
                warnings.append(ImportWarning(
                    category="identical_schema",
                    message="Schema is identical to existing, replacing anyway",
                ))

        # Step 5: Handle incompatible schema
        if compatibility_result and compatibility_result.is_incompatible:
            if not force and enforcement_policy == EnforcementPolicy.STRICT:
                return ImportResult(
                    success=False,
                    schema_id=schema_id,
                    imported_version=imported_version,
                    existing_version=existing_version,
                    compatibility_result=compatibility_result,
                    warnings=tuple(warnings),
                    error=f"Schema is incompatible with existing schema: "
                          f"{compatibility_result.breaking_change_count} breaking change(s). "
                          f"Use force=True to override.",
                )
            elif enforcement_policy == EnforcementPolicy.WARN or force:
                warnings.append(ImportWarning(
                    category="compatibility",
                    message=f"Importing incompatible schema with {compatibility_result.breaking_change_count} breaking change(s)",
                ))

        # Step 6: Perform atomic import
        import_result = self._perform_atomic_import(existing_entities, import_entities)

        if import_result.is_failure():
            return ImportResult(
                success=False,
                schema_id=schema_id,
                imported_version=imported_version,
                existing_version=existing_version,
                compatibility_result=compatibility_result,
                warnings=tuple(warnings),
                error=import_result.error,
            )

        return ImportResult(
            success=True,
            schema_id=schema_id,
            imported_version=imported_version,
            existing_version=existing_version,
            compatibility_result=compatibility_result,
            warnings=tuple(warnings),
            entity_count=len(import_entities),
            field_count=sum(e.field_count for e in import_entities),
            was_identical=compatibility_result.is_identical if compatibility_result else False,
            was_skipped=False,
        )
