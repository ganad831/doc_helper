"""Schema commands for schema designer operations.

Phase 2 Step 2: Entity and field creation
Phase 2 Step 3: Entity and field update/delete
Phase SD-2: Constraint management
Phase F-14: Field option management
Phase 6A: Relationship management
Phase 3+: Import/export
"""

# Phase 2 Step 2: Entity and field creation
from doc_helper.application.commands.schema.create_entity_command import (
    CreateEntityCommand,
)
from doc_helper.application.commands.schema.add_field_command import AddFieldCommand

# Phase 2 Step 3: Entity and field update/delete
from doc_helper.application.commands.schema.update_entity_command import (
    UpdateEntityCommand,
)
from doc_helper.application.commands.schema.delete_entity_command import (
    DeleteEntityCommand,
)
from doc_helper.application.commands.schema.update_field_command import (
    UpdateFieldCommand,
)
from doc_helper.application.commands.schema.delete_field_command import (
    DeleteFieldCommand,
)

# Phase SD-2: Constraint management
from doc_helper.application.commands.schema.add_field_constraint_command import (
    AddFieldConstraintCommand,
)

# Phase F-14: Field option management
from doc_helper.application.commands.schema.add_field_option_command import (
    AddFieldOptionCommand,
)
from doc_helper.application.commands.schema.update_field_option_command import (
    UpdateFieldOptionCommand,
)
from doc_helper.application.commands.schema.delete_field_option_command import (
    DeleteFieldOptionCommand,
)
from doc_helper.application.commands.schema.reorder_field_options_command import (
    ReorderFieldOptionsCommand,
)

# Phase 6A: Relationship management (ADR-022)
from doc_helper.application.commands.schema.create_relationship_command import (
    CreateRelationshipCommand,
)

# Phase 3+: Import/export
from doc_helper.application.commands.schema.import_schema_command import (
    ImportSchemaCommand,
)
from doc_helper.application.commands.schema.export_schema_command import (
    ExportSchemaCommand,
)

__all__ = [
    # Phase 2 Step 2
    "CreateEntityCommand",
    "AddFieldCommand",
    # Phase 2 Step 3
    "UpdateEntityCommand",
    "DeleteEntityCommand",
    "UpdateFieldCommand",
    "DeleteFieldCommand",
    # Phase SD-2
    "AddFieldConstraintCommand",
    # Phase F-14
    "AddFieldOptionCommand",
    "UpdateFieldOptionCommand",
    "DeleteFieldOptionCommand",
    "ReorderFieldOptionsCommand",
    # Phase 6A
    "CreateRelationshipCommand",
    # Phase 3+
    "ImportSchemaCommand",
    "ExportSchemaCommand",
]
