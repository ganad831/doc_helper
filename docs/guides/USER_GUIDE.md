# Doc Helper User Guide

## Overview

Doc Helper is a document generation platform designed to automate the creation of technical reports. The v1 release focuses on Soil Investigation Reports.

## Features

### Project Management
- Create new soil investigation projects
- Save and load existing projects
- Track recent projects for quick access

### Data Entry
- Dynamic forms based on configurable schema
- 12 field types supported:
  - TEXT: Single-line text input
  - TEXTAREA: Multi-line text input
  - NUMBER: Numeric values (integers and decimals)
  - DATE: Date selection
  - DROPDOWN: Single selection from predefined options
  - CHECKBOX: Boolean true/false
  - RADIO: Single selection with radio buttons
  - CALCULATED: Formula-driven read-only values
  - LOOKUP: Reference to another entity/record
  - FILE: File attachment
  - IMAGE: Image attachment with preview
  - TABLE: Nested tabular data

### Validation
- Real-time field validation
- Pre-generation validation checklist
- Constraint enforcement (required fields, min/max values, patterns)

### Formula System
- Automatic calculation of derived fields
- Dependency tracking
- Circular dependency detection
- Manual override capability with state management (PENDING → ACCEPTED → SYNCED)

### Control Rules
- Dynamic field visibility based on conditions
- Automatic value setting based on rules
- Field enable/disable based on conditions

### Document Generation
- Generate Word documents (.docx) from templates
- Generate Excel workbooks (.xlsx) from templates
- Export to PDF
- Content control mapping
- 15+ built-in transformers for data formatting

## Getting Started

### Installation

1. Ensure Python 3.11+ is installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### First Steps

1. **Launch the application**:
   ```bash
   python -m doc_helper.main
   ```

2. **Create a new project**:
   - Click "Create New Project" on the welcome screen
   - Enter project name and details
   - Fill in the dynamic form fields

3. **Save your project**:
   - Use Ctrl+S or File → Save
   - Projects are saved in .dhproj format

4. **Generate a document**:
   - Complete all required fields (marked with *)
   - Click "Generate Document" or use File → Generate Document
   - Select template and output format
   - Review pre-generation validation checklist
   - Click "Generate"

## Keyboard Shortcuts

- **Ctrl+S**: Save project
- **Ctrl+Z**: Undo last change
- **Ctrl+Y**: Redo change

## Field Types Guide

### TEXT
Single-line text input for short values like names, titles, or codes.

**Example**: Project Name, Site Location

### TEXTAREA
Multi-line text input for longer descriptions or notes.

**Example**: Project Description, Observations

### NUMBER
Numeric input with optional decimal places.

**Example**: Depth (m), Temperature (°C), Quantity

### DATE
Date picker for selecting dates.

**Example**: Investigation Date, Report Date

### DROPDOWN
Select one option from a predefined list.

**Example**: Soil Type (Clay, Sand, Silt), Weather Conditions

### CHECKBOX
Boolean field for yes/no or true/false values.

**Example**: Contains Groundwater, Is Contaminated

### RADIO
Single selection displayed as radio buttons.

**Example**: Investigation Method (Boring, Trenching, Test Pit)

### CALCULATED
Read-only field computed from a formula.

**Example**: Total Depth = Depth From + Depth To

**Override**: You can manually override calculated values if needed.

### LOOKUP
Reference to a value from another entity or record.

**Example**: Lab Test Reference, Previous Investigation

### FILE
Attach files to the project.

**Example**: Lab Report PDF, Photos

### IMAGE
Attach images with preview capability.

**Example**: Site Photos, Diagrams

### TABLE
Nested tabular data with rows and columns.

**Example**: Borehole Logs, Lab Test Results

## Formulas

### Syntax
Formulas use a simple expression syntax:
- Arithmetic: `+`, `-`, `*`, `/`
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `and`, `or`, `not`
- Field references: Use field ID (e.g., `depth_from`, `width`)

### Examples
```
total_depth = depth_from + depth_to
area = width * height
volume = length * width * height
density_ratio = dry_density / wet_density
is_deep = total_depth > 10
```

### Overrides
You can override formula results:
1. Click on a calculated field
2. Enter manual value
3. System shows PENDING state
4. Click "Accept" to apply override
5. Override persists even if input values change

## Control Rules

Control rules dynamically change field behavior based on conditions.

### Types

**VISIBILITY**: Show/hide fields
```
Show "Contamination Details" when "Is Contaminated" is checked
```

**VALUE_SET**: Automatically set values
```
Set "Status" to "N/A" when "Enable Details" is unchecked
```

**ENABLE**: Enable/disable fields
```
Enable "Comments" when "Has Comments" is checked
```

## Document Generation

### Templates

Templates are Word or Excel files with placeholders:
- Word: Use Content Controls with field IDs as tags
- Excel: Use cell references with field IDs

### Transformers

Transformers format data before inserting into templates:
- **direct**: No transformation (default)
- **uppercase**: Convert to uppercase
- **lowercase**: Convert to lowercase
- **title_case**: Convert to title case
- **date_short**: Format date as MM/DD/YYYY
- **date_long**: Format date as Month DD, YYYY
- **number_2dp**: Format number with 2 decimal places
- **currency_usd**: Format as US dollar currency
- And more...

### Process

1. Complete all required fields
2. Select File → Generate Document
3. Choose template file
4. Select output format (Word/Excel/PDF)
5. Choose output location
6. Review validation checklist
7. Click Generate

## Validation

### Field-Level Validation
- Required fields cannot be empty
- Numeric fields must be valid numbers
- Min/max values enforced
- Pattern matching for formatted text

### Pre-Generation Validation
Before generating a document, the system checks:
- All required fields are filled
- All field values are valid
- No validation errors exist

Fix any errors before generating the document.

## Troubleshooting

### "Validation errors - ready to generate" message shows errors
- Review the validation checklist
- Fix all fields marked with errors
- Ensure required fields (marked with *) are filled

### Formula not calculating
- Check that all referenced fields have values
- Verify formula syntax is correct
- Look for circular dependencies (A depends on B, B depends on A)

### Document generation fails
- Ensure template file exists and is accessible
- Verify template has correct content controls/cell references
- Check that all required fields are filled
- Review validation checklist

### Cannot override calculated value
- Click on the calculated field first
- Enter the override value
- Click "Accept" button to apply

## Tips

- **Save frequently**: Use Ctrl+S to save your work
- **Use formulas**: Let the system calculate derived values automatically
- **Override when needed**: You can always override calculated values if the formula doesn't fit your specific case
- **Validate before generating**: Always review the validation checklist before generating documents
- **Create templates carefully**: Ensure your templates have correct field mappings

## Support

For issues or questions:
- Check this user guide
- Review developer documentation (DEVELOPER_GUIDE.md)
- Report bugs at: https://github.com/ganad831/doc_helper/issues

## Version

Doc Helper v1.0
