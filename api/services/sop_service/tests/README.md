# SOP Service Integration Tests

This directory contains comprehensive integration tests for the SOP service functionality.

## Test Overview

The tests demonstrate the complete workflow of creating and managing SOP documents using the block-based system:

### What the Tests Cover

1. **Document Creation**
   - Creating a document with metadata
   - Adding different types of blocks (title, description, section header, steps)
   - Using structured content for step blocks

2. **Block Operations (CRUD)**
   - Adding blocks with specific positions
   - Retrieving blocks (all and individual)
   - Updating block content
   - Duplicating blocks
   - Reordering blocks
   - Deleting blocks

3. **Document Assembly**
   - Converting documents to multiple formats:
     - HTML (with styling)
     - Markdown
     - Plain Text
     - JSON
   - Including table of contents
   - Including metadata

4. **Document Validation**
   - Validating document structure
   - Checking required vs optional blocks
   - Block type analysis

5. **Service Integration**
   - SOP service initialization
   - Block service operations
   - Document assembler functionality

### Test Document Structure

The test creates a simple "Laboratory Safety Procedures" document with:

1. **Title Block**: "Laboratory Safety Procedures"
2. **Description Block**: Overview of the document
3. **Section Header**: "Pre-Entry Procedures"
4. **Step 1**: "Check safety equipment" (with PPE required)
5. **Step 2**: "Review hazard assessment" (no PPE required)

## Running the Tests

**Important:**
- On Windows, you should run all test scripts using the Python interpreter from your virtual environment to ensure dependencies are correct. For example:

```bash
# From the project root or test directory
.venv\Scripts\python.exe run_test.py
```

Or, for the main test script:

```bash
.venv\Scripts\python.exe test.py
```

This ensures you are using the correct environment and all dependencies are available.

### Option 1: Run the Simple Test Runner

```bash
cd api/services/sop_service/tests
.venv\Scripts\python.exe run_test.py
```

### Option 2: Run Individual Test Methods

```python
from test_sop_service_integration import TestSopServiceIntegration

# Create test instance
test = TestSopServiceIntegration()

# Run specific tests
test.test_create_document_with_blocks()
test.test_block_operations()
test.test_document_assembly()
test.test_document_validation()
test.test_sop_service_integration()

# Or run all tests
test.run_all_tests()
```

### Option 3: Run with pytest

```bash
cd api/services/sop_service/tests
.venv\Scripts\python.exe -m pytest test_sop_service_integration.py -v
```

## .cursor File (Optional)

If you are using the Cursor editor, you may want to add a `.cursor` file to your project root to store workspace-specific settings, such as preferred Python interpreter paths or test runner configurations. This can help ensure consistency for all contributors using Cursor.

Example `.cursor` snippet:

```
[python]
interpreter = ".venv/Scripts/python.exe"
```

This is optional, but can be useful for teams or when sharing the project.

## Test Database

The tests use an in-memory SQLite database that is created and destroyed for each test run. This ensures:

- Clean test environment for each run
- No external database dependencies
- Fast test execution
- No data persistence between tests

## Expected Output

When running the tests successfully, you should see output like:

```
🚀 Starting SOP Service Integration Tests
==================================================

=== Testing Document Creation with Blocks ===
✅ Created document: Laboratory Safety Procedures
   - Document ID: 1
   - Document Key: 1001
   - Type: sop
   - Status: draft
✅ Added title block: Laboratory Safety Procedures
✅ Added description block: This document outlines the safety procedures...
✅ Added section header: Pre-Entry Procedures
✅ Added step 1: Check safety equipment
   - PPE Required: True
✅ Added step 2: Review hazard assessment
   - PPE Required: False

=== Testing Block Operations ===
✅ Retrieved 5 blocks for document
   1. title: Laboratory Safety Procedures
   2. description: This document outlines the safety procedures...
   3. section_header: Pre-Entry Procedures
   4. step: Check safety equipment
   5. step: Review hazard assessment
...

=== Testing Document Assembly ===
--- Testing HTML Assembly ---
✅ Assembled as HTML
   - Content length: 2847 characters
   - Format: html
   - Block count: 5
   - Preview: <!DOCTYPE html><html><head><meta charset="UTF-8">...

--- Testing Markdown Assembly ---
✅ Assembled as Markdown
   - Content length: 892 characters
   - Format: markdown
   - Block count: 5
   - Preview: # Laboratory Safety Procedures...

==================================================
✅ All tests completed successfully!
📋 Summary:
   - Document creation with blocks ✓
   - Block operations (CRUD) ✓
   - Document assembly in multiple formats ✓
   - Document validation ✓
   - SOP service integration ✓
```

## Dependencies

The tests require the following Python packages:
- `sqlalchemy`
- `pydantic`
- `pytest` (optional, for pytest runner)

## Troubleshooting

### Import Errors
If you encounter import errors, make sure you're running from the correct directory and that the Python path includes the project root.

### Database Errors
The tests use SQLite in-memory database, so no external database setup is required. If you see database errors, check that SQLAlchemy is properly installed.

### Model Errors
If you see model-related errors, ensure that all the required models are properly imported and that the database schema is correctly defined.

## Extending the Tests

To add more test cases:

1. Add new test methods to the `TestSopServiceIntegration` class
2. Follow the existing pattern of setup/teardown
3. Use the existing services (`block_service`, `document_assembler`)
4. Add your new test to the `run_all_tests()` method

Example:
```python
def test_new_feature(self):
    """Test a new feature"""
    print("\n=== Testing New Feature ===")
    
    # Your test code here
    document = self.test_create_document_with_blocks()
    
    # Test your new functionality
    result = self.block_service.your_new_method(document.id)
    
    print(f"✅ New feature test passed: {result}")
``` 