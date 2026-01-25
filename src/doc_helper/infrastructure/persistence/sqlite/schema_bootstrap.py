"""Schema Database Bootstrap - Infrastructure Level.

PHASE B-1: Schema Database Bootstrap

PURPOSE:
    Guarantees config.db exists with proper schema before any schema repository
    is constructed. This is an infrastructure-level component that MUST be
    invoked from the composition root BEFORE any repository construction.

BEHAVIOR:
    - Check if config.db exists at given path
    - If NOT: Create file and ALL authoritative schema tables
    - If YES: Do nothing (idempotent - safe to call multiple times)

FAILURE MODE:
    - If database creation fails: FATAL error (no silent recovery)
    - If table creation fails: FATAL error (no partial creation)
    - Exception propagates to caller for handling

ARCHITECTURAL RULES:
    - Infrastructure layer ONLY
    - Called from composition root (main.py) ONLY
    - MUST be invoked BEFORE any schema repository construction
    - Repository constructors MUST NOT create tables
    - NO silent recovery, NO fallback, NO auto-repair

AUTHORITATIVE SCHEMA:
    Tables defined here match exactly what SqliteSchemaRepository expects.
    See: docs/schema-designer/schema_db_init.sql for reference.
"""

import sqlite3
from pathlib import Path


class SchemaBootstrapError(Exception):
    """Fatal error during schema database bootstrap.

    This exception indicates bootstrap failed and the application
    MUST NOT continue. The error message contains details about
    what went wrong.
    """
    pass


# ============================================================================
# AUTHORITATIVE SCHEMA DDL
# ============================================================================
# These CREATE TABLE statements define the exact schema expected by
# SqliteSchemaRepository. Any changes here MUST be coordinated with
# the repository implementation.

ENTITIES_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,                    -- Entity ID (e.g., "soil_sample")
    name_key TEXT NOT NULL,                 -- Translation key for name
    description_key TEXT,                   -- Translation key for description (optional)
    is_root_entity INTEGER NOT NULL DEFAULT 0,  -- 1 for root entities, 0 for child
    parent_entity_id TEXT,                  -- Parent entity ID (for child entities)
    display_order INTEGER NOT NULL DEFAULT 0,   -- Display ordering

    -- Foreign key constraint
    FOREIGN KEY (parent_entity_id) REFERENCES entities(id) ON DELETE SET NULL
);
"""

ENTITIES_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_entities_parent ON entities(parent_entity_id);
CREATE INDEX IF NOT EXISTS idx_entities_root ON entities(is_root_entity);
"""

FIELDS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS fields (
    id TEXT PRIMARY KEY,                    -- Field ID (e.g., "sample_depth")
    entity_id TEXT NOT NULL,                -- Entity this field belongs to
    field_type TEXT NOT NULL,               -- Field type (TEXT, NUMBER, etc.)
    label_key TEXT NOT NULL,                -- Translation key for label
    help_text_key TEXT,                     -- Translation key for help text (optional)
    required INTEGER NOT NULL DEFAULT 0,    -- 1 if required, 0 if optional
    default_value TEXT,                     -- Default value (optional)
    display_order INTEGER NOT NULL DEFAULT 0,  -- Display ordering within entity

    -- Formula-related columns (Phase 2.2)
    formula TEXT,                           -- Formula expression (for CALCULATED fields)

    -- Lookup-related columns
    lookup_entity_id TEXT,                  -- Entity to lookup from (for LOOKUP fields)
    lookup_display_field TEXT,              -- Field to display from lookup

    -- Table-related columns
    child_entity_id TEXT,                   -- Child entity reference (for TABLE fields)

    -- Foreign key constraints
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (lookup_entity_id) REFERENCES entities(id) ON DELETE SET NULL,
    FOREIGN KEY (child_entity_id) REFERENCES entities(id) ON DELETE SET NULL,

    -- Constraints
    CHECK (field_type IN ('TEXT', 'TEXTAREA', 'NUMBER', 'DATE', 'DROPDOWN', 'CHECKBOX', 'RADIO', 'CALCULATED', 'LOOKUP', 'FILE', 'IMAGE', 'TABLE'))
);
"""

FIELDS_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_fields_entity ON fields(entity_id);
CREATE INDEX IF NOT EXISTS idx_fields_type ON fields(field_type);
"""

RELATIONSHIPS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,                    -- Relationship ID (e.g., "project_contains_boreholes")
    source_entity_id TEXT NOT NULL,         -- Source entity ID (where relationship originates)
    target_entity_id TEXT NOT NULL,         -- Target entity ID (where relationship points)
    relationship_type TEXT NOT NULL,        -- Semantic type (CONTAINS, REFERENCES, ASSOCIATES)
    name_key TEXT NOT NULL,                 -- Translation key for relationship name
    description_key TEXT,                   -- Translation key for description (optional)
    inverse_name_key TEXT,                  -- Translation key for inverse name (optional)

    -- Foreign key constraints
    FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE RESTRICT,
    FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE RESTRICT,

    -- Constraints
    CHECK (relationship_type IN ('CONTAINS', 'REFERENCES', 'ASSOCIATES')),
    CHECK (source_entity_id != target_entity_id)  -- Self-references not allowed
);
"""

RELATIONSHIPS_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);
"""

# Field Options table (for DROPDOWN, RADIO fields)
FIELD_OPTIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS field_options (
    id TEXT PRIMARY KEY,                    -- Option ID (e.g., "soil_type_clay")
    field_id TEXT NOT NULL,                 -- Field this option belongs to
    value TEXT NOT NULL,                    -- Option value
    label_key TEXT NOT NULL,                -- Translation key for label
    display_order INTEGER NOT NULL DEFAULT 0,  -- Display ordering

    -- Foreign key constraints
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);
"""

FIELD_OPTIONS_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_field_options_field ON field_options(field_id);
"""

# Validation Rules table
VALIDATION_RULES_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS validation_rules (
    id TEXT PRIMARY KEY,                    -- Rule ID
    field_id TEXT NOT NULL,                 -- Field this rule applies to
    rule_type TEXT NOT NULL,                -- Rule type (REQUIRED, MIN, MAX, PATTERN, etc.)
    rule_value TEXT,                        -- Rule value/parameter
    error_message_key TEXT,                 -- Translation key for error message

    -- Foreign key constraints
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);
"""

VALIDATION_RULES_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_validation_rules_field ON validation_rules(field_id);
"""

# Control Relations table (inter-field dependencies)
CONTROL_RELATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS control_relations (
    id TEXT PRIMARY KEY,                    -- Relation ID
    source_entity_id TEXT NOT NULL,         -- Source entity
    source_field_id TEXT NOT NULL,          -- Source field (trigger)
    target_entity_id TEXT NOT NULL,         -- Target entity
    target_field_id TEXT NOT NULL,          -- Target field (affected)
    control_type TEXT NOT NULL,             -- Control type (VALUE_SET, VISIBILITY, ENABLE)
    condition_value TEXT,                   -- Condition value for triggering
    effect_value TEXT,                      -- Effect value to apply

    -- Foreign key constraints
    FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE CASCADE
);
"""

CONTROL_RELATIONS_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_control_relations_source ON control_relations(source_entity_id, source_field_id);
CREATE INDEX IF NOT EXISTS idx_control_relations_target ON control_relations(target_entity_id, target_field_id);
"""

# Output Mappings table (document generation mappings)
OUTPUT_MAPPINGS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS output_mappings (
    id TEXT PRIMARY KEY,                    -- Mapping ID
    entity_id TEXT NOT NULL,                -- Entity this mapping belongs to
    field_id TEXT NOT NULL,                 -- Field being mapped
    output_type TEXT NOT NULL,              -- Output type (WORD, EXCEL, PDF)
    target_tag TEXT NOT NULL,               -- Target tag/cell in template
    transformer_id TEXT,                    -- Optional transformer to apply

    -- Foreign key constraints
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);
"""

OUTPUT_MAPPINGS_INDEXES_DDL = """
CREATE INDEX IF NOT EXISTS idx_output_mappings_entity ON output_mappings(entity_id);
CREATE INDEX IF NOT EXISTS idx_output_mappings_field ON output_mappings(field_id);
"""


def bootstrap_schema_database(db_path: Path) -> None:
    """Bootstrap schema database if it does not exist.

    This function MUST be called from the composition root BEFORE any
    schema repository is constructed. It guarantees that config.db
    exists with proper schema.

    Args:
        db_path: Path to the schema database file (config.db)

    Raises:
        SchemaBootstrapError: If database creation fails (FATAL)

    Example:
        from doc_helper.infrastructure.persistence.sqlite.schema_bootstrap import (
            bootstrap_schema_database,
        )

        # In composition root (main.py), BEFORE repository construction:
        config_db_path = Path("app_types/soil_investigation/config.db")
        bootstrap_schema_database(config_db_path)

        # Now safe to create schema repository
        schema_repository = SqliteSchemaRepository(db_path=config_db_path)
    """
    # Check if database already exists
    if db_path.exists() and db_path.stat().st_size > 0:
        # Database exists and is not empty - do nothing (idempotent)
        return

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Create database and tables
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")

        cursor = conn.cursor()

        # Create all tables in dependency order
        # 1. entities (no dependencies)
        cursor.executescript(ENTITIES_TABLE_DDL)
        cursor.executescript(ENTITIES_INDEXES_DDL)

        # 2. fields (depends on entities)
        cursor.executescript(FIELDS_TABLE_DDL)
        cursor.executescript(FIELDS_INDEXES_DDL)

        # 3. relationships (depends on entities)
        cursor.executescript(RELATIONSHIPS_TABLE_DDL)
        cursor.executescript(RELATIONSHIPS_INDEXES_DDL)

        # 4. field_options (depends on fields)
        cursor.executescript(FIELD_OPTIONS_TABLE_DDL)
        cursor.executescript(FIELD_OPTIONS_INDEXES_DDL)

        # 5. validation_rules (depends on fields)
        cursor.executescript(VALIDATION_RULES_TABLE_DDL)
        cursor.executescript(VALIDATION_RULES_INDEXES_DDL)

        # 6. control_relations (depends on entities)
        cursor.executescript(CONTROL_RELATIONS_TABLE_DDL)
        cursor.executescript(CONTROL_RELATIONS_INDEXES_DDL)

        # 7. output_mappings (depends on entities, fields)
        cursor.executescript(OUTPUT_MAPPINGS_TABLE_DDL)
        cursor.executescript(OUTPUT_MAPPINGS_INDEXES_DDL)

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        # Fatal error - clean up partial file if created
        if db_path.exists():
            try:
                db_path.unlink()
            except OSError:
                pass
        raise SchemaBootstrapError(
            f"Failed to bootstrap schema database at {db_path}: {e}"
        ) from e
    except Exception as e:
        # Any other error is also fatal
        if db_path.exists():
            try:
                db_path.unlink()
            except OSError:
                pass
        raise SchemaBootstrapError(
            f"Unexpected error bootstrapping schema database at {db_path}: {e}"
        ) from e
