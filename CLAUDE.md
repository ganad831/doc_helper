## This plan in @plan.md is approved and frozen.

**For non-negotiable execution rules, see [AGENT_RULES.md](AGENT_RULES.md)**

**For hardened undo/redo specifications, see [unified_upgrade_plan_FINAL.md](unified_upgrade_plan_FINAL.md)**

You must:
- Follow v1 scope strictly (see AGENT_RULES.md Section 1: VERSION & SCOPE LOCK)
- Not implement any v2+ features (see AGENT_RULES.md Section 10: FORBIDDEN IN V1)
- Respect domain purity rules (see AGENT_RULES.md Section 2: ARCHITECTURAL LAYERS)
- Follow DTO-only MVVM pattern (see AGENT_RULES.md Section 3: DTO-ONLY MVVM)
- Follow undo/redo rules (see AGENT_RULES.md Section 6 + unified_upgrade_plan_FINAL.md H1-H5)
- Use command-based undo model only (see unified_upgrade_plan_FINAL.md H1)
- Separate UndoState DTOs from UI DTOs (see unified_upgrade_plan_FINAL.md H2, ADR-021)
- Mappers are one-way only: Domain → DTO (see unified_upgrade_plan_FINAL.md H3)
- Stop and ask if any requirement is unclear (see AGENT_RULES.md Section 11: DECISION PRECEDENCE)
- Provide compliance checklist after implementation (see AGENT_RULES.md Section 12: EXECUTION DISCIPLINE)


## Python Environment
- Always use `.venv/Scripts/python` for running Python commands
- Always use `.venv/Scripts/pip` for installing packages
- Never use system Python
