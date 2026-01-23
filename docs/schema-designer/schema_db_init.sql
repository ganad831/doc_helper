-- Schema Designer Database Initialization (Phase 2 Step 2)
--
-- This script creates the necessary tables for storing schema definitions.
-- Run this script on config.db to initialize the schema storage.
--
-- Usage:
--   sqlite3 config.db < schema_db_init.sql

-- ============================================================================
-- ENTITIES TABLE
-- ============================================================================

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

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_entities_parent ON entities(parent_entity_id);
CREATE INDEX IF NOT EXISTS idx_entities_root ON entities(is_root_entity);

-- ============================================================================
-- FIELDS TABLE
-- ============================================================================

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

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_fields_entity ON fields(entity_id);
CREATE INDEX IF NOT EXISTS idx_fields_type ON fields(field_type);

-- ============================================================================
-- FIELD_OPTIONS TABLE (for DROPDOWN, RADIO fields)
-- ============================================================================
-- Phase 2 Step 3: Will add options for choice fields

-- ============================================================================
-- VALIDATION_RULES TABLE
-- ============================================================================
-- Phase 2 Step 3: Will add validation rule storage

-- ============================================================================
-- RELATIONSHIPS TABLE (Phase 6A - ADR-022)
-- ============================================================================
-- Stores explicit semantic relationships between entities.
-- ADD-ONLY semantics: relationships can be created but not updated or deleted.

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

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);

-- ============================================================================
-- SAMPLE DATA (Meta-Schema)
-- ============================================================================
-- Insert the 4 meta-schema entities that describe the schema itself

-- 1. EntityDefinition entity
INSERT OR REPLACE INTO entities (id, name_key, description_key, is_root_entity, display_order)
VALUES (
    'entity_definition',
    'entity.entity_definition',
    'entity.entity_definition.description',
    1,  -- Root entity
    1
);

-- Fields for EntityDefinition
INSERT OR REPLACE INTO fields (id, entity_id, field_type, label_key, help_text_key, required, display_order)
VALUES
    ('entity_id', 'entity_definition', 'TEXT', 'field.entity_id', 'field.entity_id.help', 1, 1),
    ('entity_name_key', 'entity_definition', 'TEXT', 'field.entity_name_key', 'field.entity_name_key.help', 1, 2),
    ('entity_description_key', 'entity_definition', 'TEXT', 'field.entity_description_key', NULL, 0, 3),
    ('entity_is_root', 'entity_definition', 'CHECKBOX', 'field.entity_is_root', 'field.entity_is_root.help', 0, 4);

-- 2. FieldDefinition entity
INSERT OR REPLACE INTO entities (id, name_key, description_key, is_root_entity, display_order)
VALUES (
    'field_definition',
    'entity.field_definition',
    'entity.field_definition.description',
    0,  -- NOT root entity
    2
);

-- Fields for FieldDefinition
INSERT OR REPLACE INTO fields (id, entity_id, field_type, label_key, help_text_key, required, display_order)
VALUES
    ('field_id', 'field_definition', 'TEXT', 'field.field_id', 'field.field_id.help', 1, 1),
    ('field_label_key', 'field_definition', 'TEXT', 'field.field_label_key', 'field.field_label_key.help', 1, 2),
    ('field_type', 'field_definition', 'DROPDOWN', 'field.field_type', 'field.field_type.help', 1, 3),
    ('field_required', 'field_definition', 'CHECKBOX', 'field.field_required', NULL, 0, 4),
    ('field_default_value', 'field_definition', 'TEXT', 'field.field_default_value', NULL, 0, 5);

-- 3. ValidationRule entity
INSERT OR REPLACE INTO entities (id, name_key, description_key, is_root_entity, display_order)
VALUES (
    'validation_rule',
    'entity.validation_rule',
    'entity.validation_rule.description',
    0,  -- NOT root entity
    3
);

-- Fields for ValidationRule (minimal for Phase 2 Step 2)
INSERT OR REPLACE INTO fields (id, entity_id, field_type, label_key, required, display_order)
VALUES
    ('rule_id', 'validation_rule', 'TEXT', 'field.rule_id', 1, 1),
    ('rule_field_id', 'validation_rule', 'TEXT', 'field.rule_field_id', 1, 2),
    ('rule_type', 'validation_rule', 'TEXT', 'field.rule_type', 1, 3);

-- 4. RelationshipDefinition entity
INSERT OR REPLACE INTO entities (id, name_key, description_key, is_root_entity, display_order)
VALUES (
    'relationship_definition',
    'entity.relationship_definition',
    'entity.relationship_definition.description',
    0,  -- NOT root entity
    4
);

-- Fields for RelationshipDefinition (minimal for Phase 2 Step 2)
INSERT OR REPLACE INTO fields (id, entity_id, field_type, label_key, required, display_order)
VALUES
    ('relationship_id', 'relationship_definition', 'TEXT', 'field.relationship_id', 1, 1),
    ('source_entity_id', 'relationship_definition', 'TEXT', 'field.source_entity_id', 1, 2),
    ('target_entity_id', 'relationship_definition', 'TEXT', 'field.target_entity_id', 1, 3);

-- ============================================================================
-- END OF SCHEMA INITIALIZATION
-- ============================================================================
