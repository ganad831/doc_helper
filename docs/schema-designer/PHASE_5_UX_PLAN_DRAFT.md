# Phase 5 Execution Plan: UX Polish & Onboarding

**Document Type:** Planning Document
**Phase:** 5 of N
**Scope:** UX Clarity Only — No Behavioral Changes
**Status:** DRAFT FOR APPROVAL

---

## 1. Phase 5 Goals

### 1.1 User Problems to Solve

- **Confusion about Schema Designer purpose:** Users do not understand that Schema Designer edits the *meta-schema* (field definitions, entity structures) rather than project data
- **Unclear relationship to Document apps:** Users may expect Schema Designer to behave like Soil Investigation or other DOCUMENT apps
- **Missing context on minimal UI:** The intentionally sparse interface appears broken or incomplete rather than purposefully focused
- **No explanation of manual workflow:** Users do not know they must manually export the schema and deploy it outside the tool
- **Lack of feedback on successful operations:** Users complete actions but receive no confirmation or next-step guidance

### 1.2 Why Confusion Exists (By Design)

The Schema Designer was implemented with minimal UI to:
- Reduce scope creep during Phases 1-4
- Avoid premature abstraction of workflows not yet validated
- Ship a functional tool without guessing user preferences

Phase 5 addresses the communication gap without changing the tool's actual behavior.

---

## 2. Allowed UX Changes

The following changes are permitted because they alter **presentation and explanation only**, not semantics or persistence:

### 2.1 Text & Labels
- Add descriptive header text explaining Schema Designer's purpose
- Add subtitle clarifying "Edits field and entity definitions, not project data"
- Improve button labels for clarity (e.g., if any are ambiguous)
- Add section headers within panels to group related controls

### 2.2 Empty States
- Display helpful message when no entities exist: "No entities defined. Add an entity to begin."
- Display helpful message when no fields exist: "This entity has no fields. Add fields to define its structure."
- Display helpful message on first launch explaining the tool

### 2.3 Tooltips
- Add tooltips to toolbar buttons explaining their function
- Add tooltips to field type dropdown explaining each type briefly
- Add tooltips to validation rule inputs explaining constraints

### 2.4 Warnings & Confirmations
- Add confirmation dialog before destructive actions (delete entity, delete field)
- Add warning banner if user attempts to close with unsaved changes
- Add success toast/message after export operation completes

### 2.5 Onboarding Elements
- First-launch welcome dialog explaining Schema Designer
- "What is this?" help link or icon in header
- Static help text panel (collapsible) explaining workflow

### 2.6 Status Indicators
- Visual indicator showing unsaved changes exist
- Visual indicator showing current schema file path (if loaded)
- Visual indicator distinguishing TOOL vs DOCUMENT app types

---

## 3. Explicitly Forbidden Actions

The following are **NOT permitted** in Phase 5:

| Forbidden Action | Reason |
|------------------|--------|
| Adding relationship editor UI | New feature, requires schema changes |
| Adding visual schema graph | New feature, significant implementation |
| Adding formula/control editors | New feature, out of scope for TOOL apps |
| Adding output mapping editor | New feature, not applicable to Schema Designer |
| Changing database schema | Phases 1-4 are closed |
| Adding auto-export to app_types | Behavioral change, not UX |
| Adding schema validation logic | Behavioral change |
| Adding migration/upgrade tooling | New feature |
| Refactoring existing code | Out of scope |
| Adding new field types | Frozen in v1 |
| Changing persistence layer | Architectural change |
| Adding undo/redo to Schema Designer | Feature, not UX polish |
| Adding import from existing schema | Feature |
| Modifying how entities/fields are stored | Behavioral change |

**Rationale:** Phase 5 improves understanding of existing behavior. It does not extend, modify, or enhance that behavior.

---

## 4. Onboarding Flow Proposal

### 4.1 First-Time Launch Experience

**Trigger:** User opens Schema Designer for the first time (or after clearing settings)

**Welcome Dialog Content:**

> **Welcome to Schema Designer**
>
> Schema Designer is a **meta-schema editor**. It allows you to define:
> - **Entities** (e.g., "Project Info", "Boreholes", "Samples")
> - **Fields** within entities (e.g., "Project Name", "Depth", "Sample Date")
> - **Validation rules** for each field
>
> **Important:** This tool does NOT edit project data. It defines the *structure* that project data will follow.
>
> **Manual Workflow Required:**
> After designing your schema, you must:
> 1. Export your schema (e.g., JSON format)
> 2. Manually deploy the exported schema to your target app type
> 3. Restart the main application to use the new schema
>
> [Got it] [Don't show again]

### 4.2 Persistent Header Explanation

**Location:** Top of Schema Designer main window, below toolbar

**Content:**

> **Schema Designer** — Define entity structures and field definitions for document app types.
> This tool edits metadata, not project data. Export and deploy manually when complete.

**Style:** Muted text, collapsible, dismissible per session

### 4.3 What Schema Designer Edits (Clarification Text)

To be displayed in help panel or tooltip:

> Schema Designer edits the **meta-schema**: the definition of what fields exist, what types they are, and what validation rules apply.
>
> It does NOT:
> - Edit actual project data
> - Connect to existing projects
> - Auto-deploy changes to the application
>
> Think of it as designing a form template, not filling out the form.

### 4.4 Manual Export Responsibility

To be displayed after export or in help:

> **Next Steps After Exporting:**
> 1. Locate your exported schema file
> 2. Deploy it to your target app type location
> 3. Restart Doc Helper to load the updated schema
>
> Schema Designer does not automatically deploy schemas. Import and deployment are manual processes outside this tool.

---

## 5. UX Components Inventory

| Component | Purpose | Why It Does Not Alter Semantics |
|-----------|---------|--------------------------------|
| **Welcome Dialog** | Explain tool purpose on first launch | Display-only, no data changes |
| **Header Subtitle** | Persistent reminder of tool scope | Static text |
| **Empty State: No Entities** | Guide user when entity list is empty | Conditional text display |
| **Empty State: No Fields** | Guide user when field list is empty | Conditional text display |
| **Tooltips: Toolbar** | Explain button functions | Hover text only |
| **Tooltips: Field Types** | Explain each field type briefly | Hover text only |
| **Unsaved Changes Indicator** | Show asterisk or dot when dirty | Visual indicator, no logic change |
| **Delete Confirmation Dialog** | Confirm before destructive action | User confirmation, action unchanged |
| **Export Success Toast** | Confirm export completed | Post-action feedback |
| **Help Panel (Collapsible)** | Explain workflow and limitations | Static content |
| **"What is this?" Link** | Open help panel or show tooltip | Navigation only |
| **TOOL Badge** | Distinguish from DOCUMENT apps visually | Label only |

**Total new UI elements:** 12
**Elements that change behavior:** 0

---

## 6. Phase 5 Completion Criteria

Phase 5 is considered **DONE** when:

### 6.1 Onboarding Clarity
- [ ] First-time users see welcome dialog explaining Schema Designer purpose
- [ ] Users can dismiss welcome dialog permanently
- [ ] Header or subtitle persistently identifies the tool's scope

### 6.2 Empty State Guidance
- [ ] Empty entity list displays helpful message
- [ ] Empty field list displays helpful message
- [ ] Messages guide user to appropriate next action

### 6.3 Action Feedback
- [ ] Export operation displays success confirmation
- [ ] Delete operations require confirmation
- [ ] Unsaved changes are visually indicated

### 6.4 Contextual Help
- [ ] All toolbar buttons have tooltips
- [ ] Field type selector has explanatory tooltips
- [ ] Help content explains manual export and deployment workflow

### 6.5 User Comprehension (Qualitative)
- [ ] A new user can understand Schema Designer is NOT for project data within 30 seconds
- [ ] A new user can understand they must manually export and deploy the schema
- [ ] A new user does not mistake Schema Designer for a broken/incomplete DOCUMENT app

### 6.6 No Regressions
- [ ] All existing functionality works identically
- [ ] No new features were added
- [ ] No schema or persistence changes were made

---

## 7. Risks & Mitigations

### 7.1 Risk: Users Expect Auto-Deployment

**Description:** Onboarding text mentions manual export, but users may still expect automatic deployment after reading quickly.

**Mitigation:**
- Repeat manual export requirement in multiple locations (welcome dialog, help panel, post-export message)
- Use explicit language: "You must manually export and deploy..."
- Avoid phrases like "deploy" or "publish" that imply automation
- Clarify that import and deployment are outside the tool

### 7.2 Risk: Onboarding Text Ignored

**Description:** Users skip or dismiss welcome dialog without reading.

**Mitigation:**
- Keep welcome dialog concise (scannable in 10 seconds)
- Include persistent header subtitle that cannot be dismissed mid-session
- Provide "What is this?" access point for users who skipped onboarding

### 7.3 Risk: Tooltips Create False Confidence

**Description:** Brief tooltips may oversimplify field types, leading to misconfiguration.

**Mitigation:**
- Tooltips state what type does, not how to use it
- Tooltips do not promise capabilities (e.g., no "supports formulas" for types that don't)
- Link to documentation for complex types (TABLE, LOOKUP)

### 7.4 Risk: Minimal UI Still Perceived as Broken

**Description:** Even with explanations, users may expect more features.

**Mitigation:**
- Explicitly state in help panel: "Schema Designer is intentionally minimal"
- List what is NOT included and why (e.g., "Relationship editor planned for future release")
- Frame limitations as scope decisions, not bugs

### 7.5 Risk: Confirmation Dialogs Annoy Power Users

**Description:** Delete confirmations may frustrate experienced users.

**Mitigation:**
- Keep confirmation dialogs minimal (one click to confirm)
- Do NOT add "Don't ask again" checkbox (maintains safety)
- Confirmation only for destructive actions, not routine operations

---

## Summary

Phase 5 addresses **user comprehension** without altering **system behavior**. All changes are textual, visual, or navigational. No persistence, schema, or logic modifications are permitted.

**Deliverable:** UX improvements that help users understand:
1. What Schema Designer is
2. What Schema Designer is NOT
3. What users must do manually after using it (export and deploy outside the tool)

**Out of Scope:** Everything else.

---

*End of Phase 5 Execution Plan*
