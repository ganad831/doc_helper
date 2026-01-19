# ADR-012: Registry-Based Factory for Extensibility

**Status**: Accepted

**Context**: The old FieldFactory had hard-coded type→widget mappings. Adding a new field type required modifying the factory class, violating Open/Closed Principle.

**Decision**: Use registry-based factories where new types can be registered without modifying factory code. Factory.register(field_type, widget_class) adds new types. Factory.create(field_type) looks up and instantiates.

**Consequences**:
- (+) Open for extension, closed for modification
- (+) Third-party extensions possible
- (+) Runtime registration for plugin systems
- (+) Easy to add new field/transformer/validator types
- (-) Runtime errors if type not registered
- (-) Less discoverable than hard-coded mappings
