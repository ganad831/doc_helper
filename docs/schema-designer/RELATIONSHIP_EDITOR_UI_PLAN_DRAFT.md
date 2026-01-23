# Relationship Editor UI — Phase Planning Document (REVISED)

---

## 1. Goals of the Relationship Editor

- Provide a UI for viewing existing relationships between entities in the meta-schema
- Allow users to create new relationships between entities
- Surface relationship metadata in a clear, understandable format
- Integrate seamlessly with the existing Schema Designer view

---

## 2. User Problems Solved

| Problem | How Relationship Editor Solves It |
|---------|-----------------------------------|
| Users cannot see how entities are connected | Displays all relationships in a dedicated panel |
| Users cannot define parent-child or reference relationships | Provides UI to create relationships between entities |
| Users must manually edit config to define relationships | Eliminates need for manual config editing |
| Unclear which entity is source vs target | Explicit source → target display with direction indicator |

---

## 3. Allowed UI Interactions

### View Operations (Read)
- List all relationships in the current schema
- View relationship details: source entity, target entity, relationship type, name/label
- Filter relationships by entity (show relationships involving selected entity)

### Create Operations (Add)
- Add new relationship via dialog
- Select source entity from existing entities
- Select target entity from existing entities
- Select relationship type from domain-defined types
- Provide relationship name/identifier
- Provide optional description key

### NOT Allowed in This Phase
- Editing existing relationships
- Deleting relationships
- Modifying relationship type after creation
- Changing source or target entity after creation

---

## 4. Explicitly Forbidden Actions

| Action | Reason |
|--------|--------|
| Editing existing relationships | Out of scope for this phase |
| Deleting relationships | Out of scope for this phase |
| Creating new relationship types | Schema frozen |
| Modifying RelationshipDefinition domain model | Domain frozen |
| Adding new columns/fields to relationship storage | Repository frozen |
| Implementing cascade delete behavior | Behavior change |
| Adding relationship validation rules beyond what domain provides | Domain frozen |
| Auto-generating inverse relationships | Behavior change |
| Modifying entity definitions from relationship editor | Out of scope |
| Creating relationships to non-existent entities | Safety constraint |
| Importing/exporting relationships separately | Out of scope |
| Undo/redo for relationship operations | Out of scope |
| Visual graph/diagram rendering | Out of scope |

---

## 5. Relationship Editor Screen Layout (Conceptual)

### Integration Point
- New panel or tab within Schema Designer view
- Accessible when Schema Designer is open
- Does NOT replace existing entity/field panels

### Panel Structure

**Header Section**
- Panel title: "Relationships"
- Add Relationship button (enabled when at least 2 entities exist)
- Optional: Filter dropdown to show relationships for selected entity

**Relationship List Section**
- List of all relationships in schema
- Each list item displays:
  - Relationship name/identifier
  - Source entity name → Target entity name
  - Relationship type (as defined in domain, no assumed badges)
- Empty state message when no relationships defined
- Selection highlight for currently selected relationship (read-only detail view)

**Relationship Detail Section** (Optional, if space permits)
- Shows full details of selected relationship
- Read-only display of:
  - Relationship ID
  - Source entity
  - Target entity
  - Relationship type
  - Description (if any)
  - Any other fields exposed by RelationshipDefinition

### Add Dialog Structure
- Modal dialog
- Form fields:
  - Relationship ID (text input, required)
  - Source Entity (dropdown, required)
  - Target Entity (dropdown, required)
  - Relationship Type (dropdown, required, populated from domain)
  - Description Key (text input, optional)
- Cancel and Add buttons
- Validation messages displayed inline

### Buttons NOT Present
- No Edit button
- No Delete button
- No context menu with edit/delete options

---

## 6. How Relationships Are Selected (Entity A → Entity B)

### Source Entity Selection
- Dropdown populated with all entities in current schema
- Sorted alphabetically by entity name
- Shows entity ID and display name
- Required field — cannot be empty

### Target Entity Selection
- Dropdown populated with all entities in current schema
- Sorted alphabetically by entity name
- Shows entity ID and display name
- Required field — cannot be empty
- MAY include same entity as source (self-referential relationships allowed if domain supports)

### Relationship Type Selection
- Dropdown populated ONLY with types defined in RelationshipDefinition domain model
- No assumed types (1:1, 1:N, N:M) unless explicitly present in domain
- Required field — cannot be empty

### Relationship Direction
- Direction is always Source → Target
- UI displays arrow indicator: `Source Entity → Target Entity`
- No bidirectional relationship creation in single operation
- Inverse relationships must be created separately if needed

### Selection Validation
- Both source and target must be selected before save
- Duplicate relationship check (same source, target, and type)
- Entity existence verified at save time

---

## 7. Validation Rules Surfaced in UI

### Add Dialog Validation (Enforced by UI)
| Rule | UI Behavior |
|------|-------------|
| Relationship ID required | Disable Add until provided |
| Relationship ID format (alphanumeric + underscore) | Inline error message |
| Relationship ID uniqueness | Error on save if duplicate |
| Source entity required | Disable Add until selected |
| Target entity required | Disable Add until selected |
| Relationship type required | Disable Add until selected |

### Read-Only Information (Displayed from Domain)
| Data | UI Display |
|------|------------|
| Relationship types available | Dropdown options from domain |
| Existing relationship details | Read-only detail panel |

### Validation Not Surfaced
- Deep referential integrity checks (handled by domain/repository)
- Circular dependency detection (if not in domain, not in UI)

---

## 8. Safety Constraints to Prevent Invalid Relationships

### Pre-Save Validation
- Relationship ID must not be empty
- Relationship ID must be unique within schema
- Source entity must exist in current schema
- Target entity must exist in current schema
- Relationship type must be a valid domain type

### Duplicate Prevention
- Check for existing relationship with same (source, target, type) combination
- Show error message if duplicate detected
- Do NOT auto-rename or auto-suffix

### Self-Referential Constraints
- Allow self-referential relationships ONLY if domain permits
- If domain forbids, disable target dropdown option matching source
- Clear error message: "Self-referential relationships not allowed for this type"

### Immutability After Creation
- Once a relationship is created, it cannot be modified through this UI
- Once a relationship is created, it cannot be deleted through this UI
- Users must use other means (manual config editing) to modify or remove relationships

---

## 9. Unsaved Changes Behavior

### Actions That Mark Schema as Dirty
- Successfully adding a new relationship

### Actions That Do NOT Affect Dirty State
- Viewing relationships (read-only)
- Selecting a relationship in the list
- Opening and canceling the Add dialog
- Filtering the relationship list

### Indicator Integration
- If Schema Designer already has unsaved changes indicator, relationship ADD should trigger it
- No separate dirty tracking for relationships alone

---

## 10. Phase Completion Criteria

### Functional Requirements
- [ ] Relationship list displays all relationships in schema
- [ ] Empty state shown when no relationships exist
- [ ] Add Relationship button opens dialog
- [ ] Add dialog allows selection of source entity, target entity, relationship type
- [ ] Add dialog validates all required fields
- [ ] Add dialog prevents duplicate relationships
- [ ] Successful add creates relationship and refreshes list
- [ ] Relationship list refreshes after add operation
- [ ] Adding a relationship marks schema as having unsaved changes

### Integration Requirements
- [ ] Relationship panel integrates into Schema Designer view
- [ ] Relationship panel follows existing Schema Designer styling
- [ ] Tooltips provided for all interactive elements
- [ ] Empty state messaging matches Phase 5 UX patterns

### Safety Requirements
- [ ] Cannot create relationship with non-existent entities
- [ ] Cannot create duplicate relationships
- [ ] Invalid input prevented at UI level
- [ ] No edit or delete functionality exposed

### Out of Scope (Explicit Exclusions)
- [ ] NO editing of existing relationships
- [ ] NO deletion of relationships
- [ ] NO visual relationship graph/diagram
- [ ] NO drag-and-drop relationship creation
- [ ] NO auto-generation of inverse relationships
- [ ] NO relationship reordering
- [ ] NO bulk operations
- [ ] NO export/import of relationships separately

---

## Appendix: Prerequisites

The following MUST exist before this phase can be implemented:

| Prerequisite | Description | Status |
|--------------|-------------|--------|
| RelationshipDefinition in domain | Domain entity representing a relationship | VERIFY |
| Relationship repository read method | Ability to list existing relationships | VERIFY |
| Relationship repository create method | Ability to persist new relationships | VERIFY |
| Relationship type enumeration | List of valid relationship types from domain | VERIFY |
| CreateRelationshipCommand (or equivalent) | Application layer command to create relationship | VERIFY |

**IMPORTANT**: If any prerequisite does not exist, it must be created in the application layer BEFORE this UI phase begins. This phase does NOT create new domain or repository capabilities.

---

## Appendix: Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| RelationshipDefinition in domain | VERIFY | Must exist, frozen |
| Entity list in Schema Designer | EXISTS | Used for dropdowns |
| Schema Designer ViewModel | EXISTS | Will need relationship properties added |
| Add Relationship Dialog | NEW | Must be created |
| Relationship panel in Schema Designer | NEW | Must be created |

---

**Document Status**: DRAFT (REVISED)
**Phase Status**: NOT STARTED
**Blocking Issues**: Prerequisites must be verified before implementation
