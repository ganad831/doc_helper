# Doc Helper Developer Guide

## Architecture Overview

Doc Helper follows Clean Architecture principles with strict layer separation:

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                   │
│   (PyQt6 Views, ViewModels, Widgets)                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                     │
│   (Commands, Queries, Services)                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                     Domain Layer                        │
│   (Entities, Value Objects, Business Rules)            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                   │
│   (SQLite, File Storage, Document Adapters)            │
└─────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Domain Layer (`src/doc_helper/domain/`)
**Purpose**: Pure business logic with zero dependencies

**Contents**:
- **Entities**: Objects with identity and lifecycle (Project, ControlRule, etc.)
- **Value Objects**: Immutable objects defined by their values (FieldDefinitionId, ValidationResult, etc.)
- **Aggregate Roots**: Entity clusters with consistency boundaries (Project, EntityDefinition)
- **Domain Services**: Business logic that doesn't belong to a single entity
- **Specifications**: Reusable business rule queries

**Rules**:
- NO imports from infrastructure, application, or presentation layers
- NO I/O operations (file access, database, network)
- NO framework dependencies (SQLite, PyQt6, etc.)
- Pure Python logic only
- All logic must be testable in isolation

### Application Layer (`src/doc_helper/application/`)
**Purpose**: Orchestrates business workflows

**Contents**:
- **Commands**: State-changing operations (CreateProjectCommand, UpdateFieldCommand)
- **Queries**: Read-only operations (GetProjectQuery, GetEntityFieldsQuery)
- **Services**: Coordinate multiple domain operations (ValidationService, FormulaService)

**Rules**:
- Commands return Result[T, Error] (CQRS pattern)
- Services are stateless (dependencies injected)
- Transactions managed here
- May depend on domain layer only

### Infrastructure Layer (`src/doc_helper/infrastructure/`)
**Purpose**: External system integration

**Contents**:
- **Persistence**: SQLite repositories (SqliteProjectRepository, SqliteSchemaRepository)
- **Document Adapters**: Word/Excel/PDF generation (WordDocumentAdapter, etc.)
- **File Storage**: Project file management (FileProjectStorage)

**Rules**:
- Implements domain interfaces (IProjectRepository, etc.)
- Handles all I/O operations
- May depend on domain layer
- NO business logic

### Presentation Layer (`src/doc_helper/presentation/`)
**Purpose**: User interface using MVVM pattern

**Contents**:
- **ViewModels**: Presentation logic, property change notifications (framework-agnostic)
- **Views**: PyQt6 UI components (QMainWindow, QDialog, etc.)
- **Widgets**: Field type widgets (TextFieldWidget, NumberFieldWidget, etc.)

**Rules**:
- Views depend on ViewModels, not vice versa
- ViewModels have NO PyQt6 imports
- Use property change notification for data binding
- NO business logic (delegate to application layer)

## Key Design Patterns

### Result Monad (ADR-004)
Instead of exceptions, return Success/Failure:

```python
from doc_helper.domain.common.result import Result, Success, Failure

def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Failure("Division by zero")
    return Success(a / b)

# Usage
result = divide(10, 2)
if isinstance(result, Success):
    print(f"Result: {result.value}")  # 5.0
else:
    print(f"Error: {result.error}")
```

### CQRS Pattern (ADR-003)
Separate reads (queries) from writes (commands):

**Commands** (modify state):
```python
command = CreateProjectCommand(project_repo)
result = command.execute(
    name="New Project",
    entity_definition_id=entity_id
)
```

**Queries** (read-only):
```python
query = GetProjectQuery(project_repo)
result = query.execute(project_id=project_id)
```

### Repository Pattern (ADR-005)
Abstract data access:

```python
class IProjectRepository(ABC):
    @abstractmethod
    def save(self, project: Project) -> Result[None, str]:
        pass

    @abstractmethod
    def get_by_id(self, project_id: ProjectId) -> Result[Project, str]:
        pass
```

### MVVM Pattern (ADR-012)
Separate presentation logic from UI:

**ViewModel** (framework-agnostic):
```python
class ProjectViewModel(BaseViewModel):
    def __init__(self, save_command: SaveProjectCommand):
        super().__init__()
        self._save_command = save_command
        self._project_name = ""

    @property
    def project_name(self) -> str:
        return self._project_name

    def set_project_name(self, value: str) -> None:
        self._project_name = value
        self.notify_change("project_name")  # Notify UI
```

**View** (PyQt6):
```python
class ProjectView(BaseView):
    def _build_ui(self) -> None:
        self._name_input = QLineEdit()
        self._name_input.textChanged.connect(self._on_name_changed)

        # Bind to ViewModel
        self._viewmodel.subscribe("project_name", self._on_vm_name_changed)

    def _on_name_changed(self, text: str) -> None:
        self._viewmodel.set_project_name(text)

    def _on_vm_name_changed(self) -> None:
        self._name_input.setText(self._viewmodel.project_name)
```

### Dependency Injection (ADR-006)
Inject dependencies via constructor:

```python
# DON'T: Create dependencies inside class
class BadService:
    def __init__(self):
        self._repo = SqliteProjectRepository("db.sqlite")  # ❌ Hard-coded!

# DO: Inject dependencies
class GoodService:
    def __init__(self, repo: IProjectRepository):  # ✅ Injected!
        self._repo = repo
```

## Domain Entities

### Project (Aggregate Root)
Main entity representing a soil investigation project:

```python
project = Project(
    id=ProjectId(uuid4()),
    name="Site Investigation",
    entity_definition_id=EntityDefinitionId("soil_investigation"),
    field_values={
        FieldDefinitionId("location"): FieldValue(
            field_id=FieldDefinitionId("location"),
            value="123 Main St"
        )
    }
)
```

### EntityDefinition (Aggregate Root)
Defines the schema for an entity type:

```python
entity_def = EntityDefinition(
    id=EntityDefinitionId("soil_investigation"),
    name_key=TranslationKey("entity.soil_investigation"),
    fields={
        FieldDefinitionId("location"): FieldDefinition(
            id=FieldDefinitionId("location"),
            field_type=FieldType.TEXT,
            label_key=TranslationKey("field.location"),
            required=True
        )
    }
)
```

### FieldDefinition (Value Object)
Defines a single field's metadata:

```python
field = FieldDefinition(
    id=FieldDefinitionId("depth"),
    field_type=FieldType.NUMBER,
    label_key=TranslationKey("field.depth"),
    required=True,
    constraints=(
        MinValueConstraint(min_value=0),
        MaxValueConstraint(max_value=100),
    ),
    formula="depth_from + depth_to"  # For calculated fields
)
```

## Formula System

### Syntax
Formulas are strings with Python-like expressions:

```python
"width * height"  # Arithmetic
"depth_from + depth_to"  # Field references
"total > 100"  # Comparison
"is_active and has_data"  # Logical
```

### Evaluation
Use FormulaService to evaluate:

```python
formula_service = FormulaService()
result = formula_service.evaluate_all_formulas(project)

if isinstance(result, Success):
    # All formulas evaluated successfully
    pass
```

### Override System
Users can override calculated values:

```python
# State machine: PENDING → ACCEPTED → SYNCED
project.set_field_override(field_id, override_value)  # PENDING
project.accept_field_override(field_id)  # ACCEPTED
# If input changes, system detects conflict and moves to SYNCED
```

## Control System

### Control Types
- **VISIBILITY**: Show/hide fields based on conditions
- **VALUE_SET**: Automatically set field values
- **ENABLE**: Enable/disable fields

### Example
```python
control_rule = ControlRule(
    id=ControlRuleId("hide_optional"),
    name_key=TranslationKey("rule.hide_optional"),
    condition="required_field == null",  # Formula
    effect=ControlEffect(
        control_type=ControlType.VISIBILITY,
        target_field_id=FieldDefinitionId("optional_field"),
        value=False  # Hide when condition is true
    )
)
```

## Testing

### Unit Tests
Test domain logic in isolation:

```python
def test_project_name_validation():
    # Arrange
    project = Project(
        id=ProjectId(uuid4()),
        name="Test",
        entity_definition_id=EntityDefinitionId("test"),
        field_values={}
    )

    # Act
    result = project.set_name("")

    # Assert
    assert isinstance(result, Failure)
    assert "empty" in result.error.lower()
```

### Integration Tests
Test multiple layers together:

```python
def test_create_and_save_project(temp_db: Path):
    # Create repository
    repo = SqliteProjectRepository(temp_db)

    # Create project
    project_id = ProjectId(uuid4())
    project = Project(...)

    # Save
    save_result = repo.save(project)
    assert isinstance(save_result, Success)

    # Load
    load_result = repo.get_by_id(project_id)
    assert isinstance(load_result, Success)
    assert load_result.value.name == "Test Project"
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src/doc_helper --cov-report=term-missing

# Specific module
pytest tests/unit/domain/

# Verbose
pytest -v
```

## Database Schema

### Projects Table
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_definition_id TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Field Values Table
```sql
CREATE TABLE field_values (
    project_id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    value TEXT,
    is_computed BOOLEAN,
    computed_from TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    PRIMARY KEY (project_id, field_id)
);
```

## Document Generation

### Word Documents
Uses python-docx library:

```python
adapter = WordDocumentAdapter()
result = adapter.generate(
    template_path=Path("template.docx"),
    output_path=Path("output.docx"),
    field_values=field_values,
    transformers=transformers
)
```

Templates use Content Controls with field IDs as tags.

### Excel Workbooks
Uses xlwings library:

```python
adapter = ExcelDocumentAdapter()
result = adapter.generate(
    template_path=Path("template.xlsx"),
    output_path=Path("output.xlsx"),
    field_values=field_values,
    transformers=transformers
)
```

Templates use cell references with field IDs.

### PDF Export
Uses PyMuPDF library:

```python
adapter = PdfExportAdapter()
result = adapter.export_to_pdf(
    source_path=Path("document.docx"),
    output_path=Path("output.pdf")
)
```

## Transformers

Built-in transformers for data formatting:

```python
class DirectTransformer(ITransformer):
    """No transformation."""
    def transform(self, value: Any) -> Result[Any, str]:
        return Success(value)

class UppercaseTransformer(ITransformer):
    """Convert to uppercase."""
    def transform(self, value: Any) -> Result[str, str]:
        if not isinstance(value, str):
            return Failure("Value must be string")
        return Success(value.upper())
```

Register transformers:
```python
transformer_registry = TransformerRegistry()
transformer_registry.register("direct", DirectTransformer())
transformer_registry.register("uppercase", UppercaseTransformer())
```

## Project Structure

```
doc_helper/
├── src/doc_helper/
│   ├── domain/              # Business logic (pure Python)
│   │   ├── common/          # Shared abstractions
│   │   ├── validation/      # Validation domain
│   │   ├── schema/          # Schema domain
│   │   ├── formula/         # Formula domain
│   │   ├── control/         # Control domain
│   │   ├── project/         # Project domain
│   │   ├── override/        # Override domain
│   │   └── document/        # Document domain
│   ├── application/         # Use cases
│   │   ├── commands/        # State-changing operations
│   │   ├── queries/         # Read-only operations
│   │   └── services/        # Coordination logic
│   ├── infrastructure/      # External integrations
│   │   ├── persistence/     # SQLite repositories
│   │   ├── filesystem/      # File storage
│   │   └── document/        # Document adapters
│   └── presentation/        # UI (MVVM)
│       ├── viewmodels/      # Presentation logic
│       ├── views/           # PyQt6 UI
│       └── widgets/         # Field widgets
├── tests/
│   ├── unit/                # Unit tests (by layer)
│   └── integration/         # Integration tests
├── docs/                    # Documentation
└── app_types/               # App type configurations
    └── soil_investigation/  # v1: Soil Investigation
        ├── config.db        # Schema definition
        └── templates/       # Word/Excel templates
```

## Code Style

### Naming Conventions
- Classes: PascalCase (`ProjectRepository`)
- Functions/methods: snake_case (`get_project()`)
- Constants: UPPER_SNAKE_CASE (`MAX_DEPTH`)
- Private: Leading underscore (`_internal_method()`)

### Type Hints
Always use type hints:

```python
def calculate_total(a: float, b: float) -> float:
    return a + b

def get_project(project_id: ProjectId) -> Result[Project, str]:
    ...
```

### Docstrings
Use Google-style docstrings:

```python
def create_project(name: str, entity_id: EntityDefinitionId) -> Result[Project, str]:
    """Create a new project.

    Args:
        name: Project name
        entity_id: Entity definition ID

    Returns:
        Success(project) if created, Failure(error) otherwise

    Example:
        result = create_project("Test", EntityDefinitionId("soil"))
        if isinstance(result, Success):
            project = result.value
    """
```

## Common Tasks

### Adding a New Field Type

1. **Add enum value** (`domain/schema/field_type.py`):
   ```python
   class FieldType(str, Enum):
       # ... existing types
       MY_NEW_TYPE = "my_new_type"
   ```

2. **Add validator** (`domain/validation/validators.py`):
   ```python
   class MyNewTypeValidator(FieldValidator):
       def validate(self, value: Any) -> ValidationResult:
           # Validation logic
           pass
   ```

3. **Add widget** (`presentation/widgets/my_new_type_widget.py`):
   ```python
   class MyNewTypeFieldWidget(IFieldWidget):
       def _build_ui(self) -> QWidget:
           # PyQt6 UI for this field type
           pass
   ```

### Adding a New Command

1. **Create command** (`application/commands/my_command.py`):
   ```python
   class MyCommand:
       def __init__(self, repo: IRepository):
           self._repo = repo

       def execute(self, param: str) -> Result[None, str]:
           # Command logic
           pass
   ```

2. **Add tests** (`tests/unit/application/commands/test_my_command.py`)

### Adding a New Transformer

1. **Create transformer** (`domain/document/transformers/my_transformer.py`):
   ```python
   class MyTransformer(ITransformer):
       def transform(self, value: Any) -> Result[Any, str]:
           # Transformation logic
           return Success(transformed_value)
   ```

2. **Register** in transformer registry

## Architectural Rules (CRITICAL)

These rules MUST be enforced:

1. **Domain Isolation**: Domain layer NEVER imports from other layers
2. **No Global State**: No global variables for behavior control
3. **No Logic in Constructors**: `__init__` only assigns dependencies
4. **IO at Edges**: File/DB/Network access only in Infrastructure layer
5. **Single Responsibility**: One reason to change per class
6. **Explicit DI**: Dependencies passed via constructor
7. **No Hidden Side Effects**: Functions do what their name implies
8. **Explicit Configuration**: No hidden config sources

Violations of these rules will break the architecture.

## Debugging Tips

### Enable SQL Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Print Domain Events
```python
project = ...
for event in project.domain_events:
    print(f"Event: {event}")
```

### Validate Architecture
Run architectural tests to verify layer boundaries are respected.

## Deployment

### Build
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Check coverage
pytest --cov=src/doc_helper
```

### Distribution
Package as executable using PyInstaller or similar.

## v2+ Roadmap

Future enhancements (NOT in v1):
- Multi-app-type support (manifest.json, discovery)
- Extension system (custom transformers per app type)
- Dark mode
- Auto-save
- Field history UI
- Quick search (Ctrl+F)
- Import/Export/Clone operations
- Document versioning

## References

- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- CQRS Pattern: https://martinfowler.com/bliki/CQRS.html
- Result Monad: https://fsharpforfunandprofit.com/rop/
- MVVM Pattern: https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93viewmodel

## Support

- GitHub Issues: https://github.com/ganad831/doc_helper/issues
- Documentation: `docs/` folder
- ADRs: `adrs/` folder (Architecture Decision Records)
