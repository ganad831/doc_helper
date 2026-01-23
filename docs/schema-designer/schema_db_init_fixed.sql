-- Schema Designer Database Initialization (FIXED - Matches Repository Expectations)
--
-- This script creates tables compatible with SqliteSchemaRepository.
-- Run this script on config.db to initialize the schema storage.
--
-- Usage:
--   sqlite3 config.db < schema_db_init_fixed.sql
--
-- Column mapping to repository expectations:
--   entities.name       -> repository reads entity_row["name"]
--   entities.entity_type -> repository checks WHERE entity_type = 'root'
--   entities.sort_order -> repository uses ORDER BY sort_order
--   fields.name         -> repository reads row['name']
--   fields.sort_order   -> repository uses ORDER BY sort_order

-- ============================================================================
-- ENTITIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,                    -- Entity ID (e.g., "soil_sample")
    name TEXT NOT NULL,                     -- Display name (used in TranslationKey)
    description TEXT,                       -- Description text
    entity_type TEXT NOT NULL DEFAULT 'collection',  -- 'root' or 'collection'
    parent_entity_id TEXT,                  -- Parent entity ID (for child entities)
    sort_order INTEGER NOT NULL DEFAULT 0,  -- Display ordering

    -- Foreign key constraint
    FOREIGN KEY (parent_entity_id) REFERENCES entities(id) ON DELETE SET NULL
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_entities_parent ON entities(parent_entity_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_sort ON entities(sort_order);

-- ============================================================================
-- FIELDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS fields (
    id TEXT PRIMARY KEY,                    -- Field ID (e.g., "sample_depth")
    entity_id TEXT NOT NULL,                -- Entity this field belongs to
    name TEXT NOT NULL,                     -- Display name (used in TranslationKey)
    field_type TEXT NOT NULL,               -- Field type (TEXT, NUMBER, etc.)
    sort_order INTEGER NOT NULL DEFAULT 0,  -- Display ordering within entity

    -- Foreign key constraints
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,

    -- Constraints (lowercase to match FieldType enum)
    CHECK (field_type IN ('text', 'textarea', 'number', 'date', 'dropdown', 'checkbox', 'radio', 'calculated', 'lookup', 'file', 'image', 'table'))
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_fields_entity ON fields(entity_id);
CREATE INDEX IF NOT EXISTS idx_fields_type ON fields(field_type);
CREATE INDEX IF NOT EXISTS idx_fields_sort ON fields(sort_order);

-- ============================================================================
-- VALIDATION_RULES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS validation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id TEXT NOT NULL UNIQUE,          -- One rule set per field
    required INTEGER DEFAULT 0,             -- 1 if required, 0 if optional
    min_value REAL,                         -- Minimum numeric value
    max_value REAL,                         -- Maximum numeric value
    min_length INTEGER,                     -- Minimum text length
    max_length INTEGER,                     -- Maximum text length
    pattern TEXT,                           -- Regex pattern

    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_validation_rules_field ON validation_rules(field_id);

-- ============================================================================
-- FORMULAS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS formulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id TEXT NOT NULL UNIQUE,          -- One formula per field
    expression TEXT NOT NULL,               -- Formula expression e.g. "{{field_a}} + {{field_b}}"

    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_formulas_field ON formulas(field_id);

-- ============================================================================
-- FIELD_OPTIONS TABLE (for DROPDOWN, RADIO fields)
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id TEXT NOT NULL UNIQUE,          -- One options config per field
    inline_options TEXT,                    -- JSON array of options e.g. '["opt1","opt2"]'
    dropdown_id TEXT,                       -- Reference to shared dropdown

    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_field_options_field ON field_options(field_id);
CREATE INDEX IF NOT EXISTS idx_field_options_dropdown ON field_options(dropdown_id);

-- ============================================================================
-- DROPDOWN_OPTIONS TABLE (shared dropdowns)
-- ============================================================================

CREATE TABLE IF NOT EXISTS dropdown_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dropdown_id TEXT NOT NULL,              -- Shared dropdown ID
    value TEXT NOT NULL,                    -- Option value
    sort_order INTEGER NOT NULL DEFAULT 0,  -- Display ordering

    UNIQUE(dropdown_id, value)
);

CREATE INDEX IF NOT EXISTS idx_dropdown_options_dropdown ON dropdown_options(dropdown_id);
CREATE INDEX IF NOT EXISTS idx_dropdown_options_sort ON dropdown_options(sort_order);

-- ============================================================================
-- SAMPLE DATA (Meta-Schema)
-- ============================================================================
-- Insert the 4 meta-schema entities that describe the schema itself

-- 1. EntityDefinition entity
INSERT OR REPLACE INTO entities (id, name, description, entity_type, sort_order)
VALUES (
    'entity_definition',
    'entity_definition',
    'Defines an entity in the schema',
    'root',
    1
);

-- Fields for EntityDefinition
INSERT OR REPLACE INTO fields (id, entity_id, name, field_type, sort_order)
VALUES
    ('entity_id', 'entity_definition', 'entity_id', 'text', 1),
    ('entity_name_key', 'entity_definition', 'entity_name_key', 'text', 2),
    ('entity_description_key', 'entity_definition', 'entity_description_key', 'text', 3),
    ('entity_is_root', 'entity_definition', 'entity_is_root', 'checkbox', 4);

-- Validation rules for EntityDefinition fields
INSERT OR REPLACE INTO validation_rules (field_id, required)
VALUES
    ('entity_id', 1),
    ('entity_name_key', 1);

-- 2. FieldDefinition entity
INSERT OR REPLACE INTO entities (id, name, description, entity_type, sort_order)
VALUES (
    'field_definition',
    'field_definition',
    'Defines a field within an entity',
    'collection',
    2
);

-- Fields for FieldDefinition
-- NOTE: field_type is 'text' instead of 'dropdown' because the repository's
-- options loading returns strings but FieldDefinition expects (value, TranslationKey) tuples.
-- This is a known repository issue that needs separate fixing.
INSERT OR REPLACE INTO fields (id, entity_id, name, field_type, sort_order)
VALUES
    ('field_id', 'field_definition', 'field_id', 'text', 1),
    ('field_label_key', 'field_definition', 'field_label_key', 'text', 2),
    ('field_type', 'field_definition', 'field_type', 'text', 3),
    ('field_required', 'field_definition', 'field_required', 'checkbox', 4),
    ('field_default_value', 'field_definition', 'field_default_value', 'text', 5);

-- Validation rules for FieldDefinition fields
INSERT OR REPLACE INTO validation_rules (field_id, required)
VALUES
    ('field_id', 1),
    ('field_label_key', 1),
    ('field_type', 1);

-- 3. ValidationRule entity
INSERT OR REPLACE INTO entities (id, name, description, entity_type, sort_order)
VALUES (
    'validation_rule',
    'validation_rule',
    'Defines validation rules for a field',
    'collection',
    3
);

-- Fields for ValidationRule
INSERT OR REPLACE INTO fields (id, entity_id, name, field_type, sort_order)
VALUES
    ('rule_id', 'validation_rule', 'rule_id', 'text', 1),
    ('rule_field_id', 'validation_rule', 'rule_field_id', 'text', 2),
    ('rule_type', 'validation_rule', 'rule_type', 'text', 3);

-- Validation rules for ValidationRule fields
INSERT OR REPLACE INTO validation_rules (field_id, required)
VALUES
    ('rule_id', 1),
    ('rule_field_id', 1),
    ('rule_type', 1);

-- 4. RelationshipDefinition entity
INSERT OR REPLACE INTO entities (id, name, description, entity_type, sort_order)
VALUES (
    'relationship_definition',
    'relationship_definition',
    'Defines relationships between entities',
    'collection',
    4
);

-- Fields for RelationshipDefinition
INSERT OR REPLACE INTO fields (id, entity_id, name, field_type, sort_order)
VALUES
    ('relationship_id', 'relationship_definition', 'relationship_id', 'text', 1),
    ('source_entity_id', 'relationship_definition', 'source_entity_id', 'text', 2),
    ('target_entity_id', 'relationship_definition', 'target_entity_id', 'text', 3);

-- Validation rules for RelationshipDefinition fields
INSERT OR REPLACE INTO validation_rules (field_id, required)
VALUES
    ('relationship_id', 1),
    ('source_entity_id', 1),
    ('target_entity_id', 1);

-- ============================================================================
-- END OF SCHEMA INITIALIZATION
-- ============================================================================
