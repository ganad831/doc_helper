"""Create minimal schema database for test_report AppType.

This script creates a minimal config.db with:
- 1 entity: report_info (singleton)
- 3 fields: title (TEXT), date (DATE), summary (TEXTAREA)
- No formulas, no controls, no overrides

Usage:
    python scripts/create_test_report_schema.py
"""

import sqlite3
from pathlib import Path


def create_test_report_schema() -> None:
    """Create minimal test_report config.db."""

    # Target path
    config_db_path = Path("src/doc_helper/app_types/test_report/config.db")

    # Remove existing if present
    if config_db_path.exists():
        config_db_path.unlink()

    # Create database
    conn = sqlite3.connect(config_db_path)
    cursor = conn.cursor()

    # Create entities table
    cursor.execute("""
        CREATE TABLE entities (
            entity_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            entity_type TEXT CHECK(entity_type IN ('SINGLETON', 'COLLECTION')) DEFAULT 'SINGLETON',
            icon TEXT,
            display_order INTEGER DEFAULT 0
        )
    """)

    # Create fields table
    cursor.execute("""
        CREATE TABLE fields (
            field_id TEXT PRIMARY KEY,
            entity_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            field_type TEXT CHECK(field_type IN (
                'TEXT', 'TEXTAREA', 'NUMBER', 'DATE', 'DROPDOWN',
                'CHECKBOX', 'RADIO', 'CALCULATED', 'LOOKUP',
                'FILE', 'IMAGE', 'TABLE'
            )) NOT NULL,
            default_value TEXT,
            is_required INTEGER DEFAULT 0,
            is_readonly INTEGER DEFAULT 0,
            display_order INTEGER DEFAULT 0,
            FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
        )
    """)

    # Create validation_rules table
    cursor.execute("""
        CREATE TABLE validation_rules (
            rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            rule_value TEXT,
            error_message TEXT,
            FOREIGN KEY (field_id) REFERENCES fields(field_id)
        )
    """)

    # Create formulas table (empty for minimal schema)
    cursor.execute("""
        CREATE TABLE formulas (
            formula_id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id TEXT NOT NULL,
            formula_expression TEXT NOT NULL,
            FOREIGN KEY (field_id) REFERENCES fields(field_id)
        )
    """)

    # Create control_relations table (empty for minimal schema)
    cursor.execute("""
        CREATE TABLE control_relations (
            relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_field_id TEXT NOT NULL,
            target_field_id TEXT NOT NULL,
            effect_type TEXT NOT NULL,
            source_value TEXT,
            target_value TEXT,
            FOREIGN KEY (source_field_id) REFERENCES fields(field_id),
            FOREIGN KEY (target_field_id) REFERENCES fields(field_id)
        )
    """)

    # Insert report_info entity
    cursor.execute("""
        INSERT INTO entities (entity_id, name, description, entity_type, display_order)
        VALUES ('report_info', 'Report Information', 'Basic report metadata', 'SINGLETON', 0)
    """)

    # Insert title field
    cursor.execute("""
        INSERT INTO fields (
            field_id, entity_id, name, description, field_type,
            is_required, is_readonly, display_order
        )
        VALUES (
            'title', 'report_info', 'Report Title', 'Title of the report',
            'TEXT', 1, 0, 0
        )
    """)

    # Insert date field
    cursor.execute("""
        INSERT INTO fields (
            field_id, entity_id, name, description, field_type,
            is_required, is_readonly, display_order
        )
        VALUES (
            'date', 'report_info', 'Report Date', 'Date of the report',
            'DATE', 1, 0, 1
        )
    """)

    # Insert summary field
    cursor.execute("""
        INSERT INTO fields (
            field_id, entity_id, name, description, field_type,
            is_required, is_readonly, display_order
        )
        VALUES (
            'summary', 'report_info', 'Summary', 'Brief summary of the report',
            'TEXTAREA', 0, 0, 2
        )
    """)

    # Commit and close
    conn.commit()
    conn.close()

    print(f"✓ Created minimal schema: {config_db_path}")
    print("  - 1 entity: report_info (SINGLETON)")
    print("  - 3 fields: title (TEXT, required), date (DATE, required), summary (TEXTAREA)")


if __name__ == "__main__":
    create_test_report_schema()
