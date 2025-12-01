---
inclusion: always
---

# NexusGen - Complete Development Guide

**Application Version:** 5.0.0  
**Port:** 5002  
**Database:** SQLite at `instance/docflow.db`  
**Framework:** Flask 2.3+ with Python 3.8+

## Project Overview

NexusGen is a comprehensive Flask-based platform for document intelligence, AI-powered analysis, and advanced Appian application comparison. The application combines three major capabilities:

1. **Document Intelligence**: Spec breakdown, design verification, design creation, SQL conversion, and AI chat
2. **Appian Application Analyzer**: Version comparison with SAIL code diff visualization
3. **Three-Way Merge Assistant**: Package comparison, conflict detection, and merge guidance

The three-way merge functionality follows clean architecture principles with no data duplication, analyzing three Appian packages (Base, Customized, New Vendor) to identify conflicts and generate merge guidance.

### Key Design Principles

1. **No Duplication:** Each object stored once in `object_lookup`
2. **Package-Agnostic:** `object_lookup` has NO `package_id` column
3. **Explicit Mapping:** `package_object_mappings` tracks membership
4. **Delta-Driven:** Working set contains only A→C delta objects
5. **Referential Integrity:** All foreign keys enforced with CASCADE

## Architecture

### Technology Stack
- **Backend:** Flask 2.3+, Python 3.8+
- **Database:** SQLite + SQLAlchemy ORM with connection pooling
- **AI Services:** AWS Bedrock RAG, Amazon Q CLI Agents
- **Frontend:** Bootstrap 5, Font Awesome 6, Custom Dark Theme
- **Document Processing:** python-docx, openpyxl, PyPDF2
- **Port:** 5002

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Controllers                             │
│  (Flask routes, request/response handling)                   │
│  - breakdown_controller.py                                   │
│  - verify_controller.py                                      │
│  - create_controller.py                                      │
│  - merge_assistant_controller.py                             │
│  - chat_controller.py                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       Services                               │
│  (Business logic, orchestration)                             │
│  - three_way_merge_orchestrator.py                           │
│  - package_extraction_service.py                             │
│  - delta_comparison_service.py                               │
│  - customer_comparison_service.py                            │
│  - classification_service.py                                 │
│  - merge_guidance_service.py                                 │
│  - bedrock_service.py (AI)                                   │
│  - q_agent_service.py (AI)                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  (Business entities, enums, strategies)                      │
│  - entities.py (ObjectIdentity, DeltaChange, etc.)           │
│  - enums.py (PackageType, Classification, etc.)              │
│  - comparison_strategies.py                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Repositories                             │
│  (Data access layer)                                         │
│  - object_lookup_repository.py                               │
│  - change_repository.py                                      │
│  - delta_comparison_repository.py                            │
│  - package_object_mapping_repository.py                      │
│  - request_repository.py                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                              │
│  (Infrastructure, DI, exceptions)                            │
│  - dependency_container.py (DI container)                    │
│  - base_service.py                                           │
│  - base_repository.py                                        │
│  - exceptions.py                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Models (ORM)                            │
│  (SQLAlchemy database models)                                │
│  - models.py (40+ tables)                                    │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Injection

The application uses a custom DI container (`core/dependency_container.py`) that:
- Manages singleton instances of services and repositories
- Supports lazy initialization
- Enables testability through dependency injection
- Registered in `app.py` during application startup

Example:
```python
from core.dependency_container import DependencyContainer

container = DependencyContainer.get_instance()
orchestrator = container.get_service(ThreeWayMergeOrchestrator)
```

## Database Schema

### Application-Wide Tables

**requests** - Document processing requests (breakdown, verify, create)
```python
id, action_type, filename, input_text, status, rag_query, rag_response,
final_output, reference_id, agent_name, model_name, total_time,
step_durations, rag_similarity_avg, json_valid, error_log, created_at
```

**chat_sessions** - AI chat conversations
```python
id, session_id (UUID), question, rag_response, answer, created_at
```

### Three-Way Merge Tables

**merge_sessions** - Merge session tracking
```python
id, reference_id (UNIQUE), status, total_changes, reviewed_count,
skipped_count, estimated_complexity, estimated_time_hours, created_at
```

**packages** - Uploaded packages
```python
id, session_id (FK), package_type (base/customized/new_vendor),
filename, total_objects, created_at
```

**object_lookup** - Global Object Registry (NO package_id!)
```python
id, uuid (UNIQUE), name, object_type, description, created_at
```

**package_object_mappings** - Junction table
```python
id, package_id (FK), object_id (FK), created_at
UNIQUE(package_id, object_id)
```

**delta_comparison_results** - A→C comparison
```python
id, session_id (FK), object_id (FK), change_category, change_type,
version_changed, content_changed, created_at
UNIQUE(session_id, object_id)
```

**changes** - Working Set (references object_lookup via object_id)
```python
id, session_id (FK), object_id (FK), classification,
vendor_change_type, customer_change_type, display_order,
status (pending/reviewed/skipped), notes, reviewed_at, reviewed_by, created_at
```

**object_versions** - Package-specific versions
```python
id, object_id (FK), package_id (FK), version_uuid, sail_code,
fields (JSON), properties (JSON), raw_xml, created_at
UNIQUE(object_id, package_id)
```

### Object-Specific Tables (40+ tables)

All object tables follow this pattern:
```python
id, object_id (FK to object_lookup), uuid, name, version_uuid,
<object_specific_fields>, created_at
```

**Supported Object Types:**
- **interfaces** + interface_parameters + interface_security
- **expression_rules** + expression_rule_inputs
- **process_models** + process_model_nodes + process_model_flows + process_model_variables
- **record_types** + record_type_fields + record_type_relationships + record_type_views + record_type_actions
- **cdts** + cdt_fields
- **integrations**
- **web_apis**
- **sites**
- **groups**
- **constants**
- **connected_systems**
- **unknown_objects**

### Comparison Result Tables

- **interface_comparisons** - Interface-specific comparison results
- **process_model_comparisons** - Process model comparison with Mermaid diagrams
- **record_type_comparisons** - Record type comparison results

## Testing Requirements

### ⚠️ CRITICAL: MANDATORY TEST EXECUTION PATTERN

**YOU MUST ALWAYS USE THIS EXACT PATTERN WHEN RUNNING PYTEST:**

```bash
# MANDATORY: Redirect output to file and then cat it
python -m pytest <test_path> <options> > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**WHY THIS IS MANDATORY:**
- Direct pytest execution returns "TY=not a tty" error and Exit Code: -1
- This prevents you from seeing actual test results
- The redirect-and-cat pattern is the ONLY way to see test output properly
- Without this, you cannot verify if tests pass or fail

**EXAMPLES:**

```bash
# Run all tests
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test file
python -m pytest tests/test_three_way_merge.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run with verbose output
python -m pytest -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test by name
python -m pytest tests/test_file.py::TestClass::test_method -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run tests matching a pattern
python -m pytest -k "test_property_1" -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**NEVER USE THESE (THEY WILL FAIL):**
```bash
# ❌ WRONG - Will not show output
pytest tests/test_file.py

# ❌ WRONG - Will not show output
python -m pytest tests/test_file.py

# ❌ WRONG - Will not show output
python -m pytest tests/test_file.py -v
```

### Test Data Location

Test packages are located in:
```
applicationArtifacts/Three Way Testing Files/V2/
├── Test Application - Base Version.zip       (Package A)
├── Test Application Customer Version.zip     (Package B)
└── Test Application Vendor New Version.zip   (Package C)
```

**Known Test UUIDs:**
```python
PROCESS_MODEL_UUID_1 = "de199b3f-b072-4438-9508-3b6594827eaf"
PROCESS_MODEL_UUID_2 = "2c8de7e9-23b9-40d6-afc2-233a963832be"
RECORD_TYPE_UUID = "57318b79-0bfd-45c4-a07e-ceae8277e0fb"
```

### Property-Based Testing

**Framework:** pytest with real Appian packages (no hypothesis library)

**Test Configuration:**
- Use real packages from `applicationArtifacts/Three Way Testing Files/V2/`
- Run complete end-to-end workflow
- Verify all properties after each phase
- Clean database between tests

**Property Tests to Implement:**
1. Property 1: No duplicate objects in object_lookup
2. Property 2: Package-object mappings are consistent
3. Property 3: Delta-driven working set (delta_count == change_count)
4. Property 4: All delta objects are classified
5. Property 5-7: NEW, DEPRECATED, MODIFIED detection
6. Property 8-13: All 7 classification rules
7. Property 14: Referential integrity
8. Property 18: find_or_create idempotence

### UI/Frontend Testing with Chrome DevTools

**⚠️ IMPORTANT: Use Chrome DevTools MCP for UI Testing**

When testing the web interface, use the Chrome DevTools MCP tools instead of manual browser testing. This provides programmatic access to the browser and enables automated testing.

**Available Chrome DevTools MCP Tools:**

```bash
# Navigation
mcp_chrome_devtools_navigate_page(url="http://localhost:5002", type="url")
mcp_chrome_devtools_list_pages()
mcp_chrome_devtools_select_page(pageIdx=0)

# Page Inspection
mcp_chrome_devtools_take_snapshot()  # Get text-based page structure
mcp_chrome_devtools_take_screenshot()  # Visual screenshot

# Interaction
mcp_chrome_devtools_click(uid="element-uid")
mcp_chrome_devtools_fill(uid="input-uid", value="text")
mcp_chrome_devtools_fill_form(elements=[...])
mcp_chrome_devtools_upload_file(uid="file-input-uid", filePath="/path/to/file")

# Network & Console
mcp_chrome_devtools_list_network_requests()
mcp_chrome_devtools_get_network_request(reqid=123)
mcp_chrome_devtools_list_console_messages()
mcp_chrome_devtools_get_console_message(msgid=456)

# JavaScript Execution
mcp_chrome_devtools_evaluate_script(function="() => { return document.title }")
```

**Example UI Test Workflow:**

```python
# 1. Start the application
controlBashProcess(action="start", command="python app.py")

# 2. Wait for app to start
import time
time.sleep(3)

# 3. Navigate to the application
mcp_chrome_devtools_navigate_page(url="http://localhost:5002")

# 4. Take snapshot to see page structure
snapshot = mcp_chrome_devtools_take_snapshot()

# 5. Test navigation to merge assistant
mcp_chrome_devtools_click(uid="merge-assistant-link")

# 6. Upload test packages
mcp_chrome_devtools_upload_file(
    uid="base-package-input",
    filePath="applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip"
)

# 7. Check network requests
requests = mcp_chrome_devtools_list_network_requests()

# 8. Check console for errors
console_msgs = mcp_chrome_devtools_list_console_messages(types=["error", "warn"])

# 9. Take screenshot of results
mcp_chrome_devtools_take_screenshot(filePath="test_results.png")
```

**Common UI Testing Scenarios:**

1. **Test Document Upload Flow:**
```python
# Navigate to breakdown page
mcp_chrome_devtools_navigate_page(url="http://localhost:5002/breakdown")

# Upload document
mcp_chrome_devtools_upload_file(
    uid="file-input",
    filePath="test_document.pdf"
)

# Click process button
mcp_chrome_devtools_click(uid="process-btn")

# Wait and check results
mcp_chrome_devtools_wait_for(text="Processing complete")
snapshot = mcp_chrome_devtools_take_snapshot()
```

2. **Test Three-Way Merge Workflow:**
```python
# Navigate to merge assistant
mcp_chrome_devtools_navigate_page(url="http://localhost:5002/merge")

# Fill form with all three packages
mcp_chrome_devtools_fill_form(elements=[
    {"uid": "base-input", "value": "path/to/base.zip"},
    {"uid": "customized-input", "value": "path/to/customized.zip"},
    {"uid": "new-vendor-input", "value": "path/to/new_vendor.zip"}
])

# Start analysis
mcp_chrome_devtools_click(uid="analyze-btn")

# Monitor network requests
requests = mcp_chrome_devtools_list_network_requests(
    resourceTypes=["xhr", "fetch"]
)

# Check for errors
console_errors = mcp_chrome_devtools_list_console_messages(types=["error"])
```

3. **Test Chat Interface:**
```python
# Navigate to chat
mcp_chrome_devtools_navigate_page(url="http://localhost:5002/chat")

# Send message
mcp_chrome_devtools_fill(uid="chat-input", value="What is three-way merge?")
mcp_chrome_devtools_click(uid="send-btn")

# Wait for response
mcp_chrome_devtools_wait_for(text="Three-way merge", timeout=10000)

# Verify response
snapshot = mcp_chrome_devtools_take_snapshot()
```

**Debugging with Chrome DevTools:**

```python
# Check JavaScript errors
console_msgs = mcp_chrome_devtools_list_console_messages(types=["error"])
for msg in console_msgs:
    details = mcp_chrome_devtools_get_console_message(msgid=msg['msgid'])
    print(f"Error: {details}")

# Inspect failed network requests
requests = mcp_chrome_devtools_list_network_requests()
for req in requests:
    if req['status'] >= 400:
        details = mcp_chrome_devtools_get_network_request(reqid=req['reqid'])
        print(f"Failed request: {details}")

# Execute custom JavaScript for debugging
result = mcp_chrome_devtools_evaluate_script(
    function="""() => {
        return {
            sessionId: window.sessionId,
            currentPage: window.location.pathname,
            formData: document.querySelector('form') ? 
                new FormData(document.querySelector('form')) : null
        }
    }"""
)
```

**Performance Testing:**

```python
# Start performance trace
mcp_chrome_devtools_performance_start_trace(reload=True, autoStop=False)

# Perform actions
mcp_chrome_devtools_click(uid="heavy-operation-btn")

# Wait for completion
time.sleep(5)

# Stop trace and get insights
mcp_chrome_devtools_performance_stop_trace()

# Analyze specific insights
mcp_chrome_devtools_performance_analyze_insight(
    insightSetId="...",
    insightName="LCPBreakdown"
)
```

**Best Practices for UI Testing:**

1. **Always take snapshots first** - Use `take_snapshot()` to understand page structure before interacting
2. **Check console messages** - Monitor for JavaScript errors during testing
3. **Verify network requests** - Ensure API calls complete successfully
4. **Use wait_for()** - Wait for dynamic content to load before assertions
5. **Take screenshots on failure** - Capture visual state when tests fail
6. **Clean up** - Close pages and stop processes after testing

**Integration with pytest:**

```python
import pytest
from mcp_tools import chrome_devtools

@pytest.fixture
def browser():
    """Setup browser for testing"""
    chrome_devtools.new_page(url="http://localhost:5002")
    yield
    # Cleanup handled automatically

def test_merge_workflow(browser):
    """Test complete three-way merge workflow"""
    # Navigate
    chrome_devtools.navigate_page(url="http://localhost:5002/merge")
    
    # Upload packages
    chrome_devtools.upload_file(uid="base-input", filePath="...")
    
    # Verify results
    snapshot = chrome_devtools.take_snapshot()
    assert "Session created" in snapshot
    
    # Check for errors
    errors = chrome_devtools.list_console_messages(types=["error"])
    assert len(errors) == 0
```

## Starting the Application

### ⚠️ IMPORTANT: Always Check for Existing Instances First

Before starting the application, **ALWAYS** check if it's already running:

```bash
# Check if app is already running on port 5002
lsof -i :5002

# Or check for python processes running app.py
ps aux | grep "app.py"

# Or use curl to test if the app responds
curl -s http://localhost:5002/ | head -5
```

### Starting the App

**Option 1: Using controlBashProcess (Recommended for development)**
```bash
# Check for existing background processes first
listProcesses

# If app is running, stop it first
controlBashProcess(action="stop", processId=<id>)

# Start the app as a background process
controlBashProcess(action="start", command="python app.py")

# Check process output
getProcessOutput(processId=<id>, lines=50)
```

**Option 2: Manual Terminal (For production/testing)**
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux

# Start Flask app
python app.py
```

### Stopping the App

```bash
# If using controlBashProcess
controlBashProcess(action="stop", processId=<id>)

# Or kill by port
lsof -ti :5002 | xargs kill -9
```

## Development Workflow

### 1. Application Initialization

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AWS_REGION=us-east-1
export BEDROCK_KB_ID=WAQ6NJLGKN
export SECRET_KEY=your-secret-key-here

# Initialize database (creates all tables)
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 2. Schema Management

```bash
# Create three-way merge schema
python create_three_way_merge_schema.py

# Verify schema
python verify_schema.py

# Check schema structure
python check_schema.py
```

### 3. Running Validation Queries

```python
from app import create_app
from models import db

app = create_app()
with app.app_context():
    # Check for duplicates (should return 0)
    result = db.session.execute("""
        SELECT uuid, COUNT(*) as count 
        FROM object_lookup 
        GROUP BY uuid 
        HAVING count > 1
    """)
    duplicates = result.fetchall()
    print(f"Duplicates: {len(duplicates)}")
    
    # Verify delta-driven working set
    result = db.session.execute("""
        SELECT 
            (SELECT COUNT(*) FROM delta_comparison_results WHERE session_id = 1) as delta_count,
            (SELECT COUNT(*) FROM changes WHERE session_id = 1) as change_count
    """)
    counts = result.fetchone()
    print(f"Delta: {counts[0]}, Changes: {counts[1]}")
```

### 4. Checking Diagnostics

```bash
# Use getDiagnostics tool for syntax/type errors
getDiagnostics(paths=["services/package_extraction_service.py"])

# Check multiple files
getDiagnostics(paths=["models.py", "app.py", "config.py"])
```

### 5. Working with Services

```python
# Using dependency injection
from core.dependency_container import DependencyContainer
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator

container = DependencyContainer.get_instance()
orchestrator = container.get_service(ThreeWayMergeOrchestrator)

# Create merge session
session = orchestrator.create_merge_session(
    base_zip_path="path/to/base.zip",
    customized_zip_path="path/to/customized.zip",
    new_vendor_zip_path="path/to/new_vendor.zip"
)

# Get session status
status = orchestrator.get_session_status(session.reference_id)
print(f"Status: {status['status']}, Changes: {status['total_changes']}")

# Get working set
changes = orchestrator.get_working_set(session.reference_id)
```

## Application Features

### 1. Document Intelligence

**Spec Breakdown** (`/breakdown`)
- Upload documents (PDF, DOCX, TXT, MD)
- AI-powered extraction of user stories and acceptance criteria
- Export to Excel with structured format
- Process tracking with reference IDs (RQ_BR_XXX)

**Design Verification** (`/verify`)
- Paste design document content
- AI validation against best practices
- Recommendations and improvements
- RAG-powered analysis

**Design Creation** (`/create`)
- Generate design documents from acceptance criteria
- Comprehensive design templates
- AI-assisted content generation

**SQL Conversion** (`/convert`)
- Convert between MariaDB and Oracle SQL dialects
- Syntax transformation
- Dialect-specific optimizations

**AI Chat Assistant** (`/chat`)
- Interactive chat interface
- Context-aware responses
- Session-based conversations
- RAG integration for accurate answers

### 2. Appian Application Analyzer

**Version Comparison**
- Compare two Appian application versions
- Detailed change tracking by object type
- SAIL code diff visualization
- UUID resolution to readable names
- Business impact analysis

**Supported Object Types:**
- Interfaces (with parameters and security)
- Expression Rules (with inputs)
- Process Models (with nodes, flows, variables)
- Record Types (with fields, relationships, views, actions)
- CDTs (Custom Data Types with fields)
- Integrations
- Web APIs
- Sites
- Groups
- Constants
- Connected Systems

### 3. Three-Way Merge Assistant

**8-Step Workflow:**
1. Create session record
2. Extract Package A (Base Version)
3. Extract Package B (Customer Version)
4. Extract Package C (New Vendor Version)
5. Perform delta comparison (A→C)
6. Perform customer comparison (delta vs B)
7. Classify changes (apply 7 rules)
8. Generate merge guidance

**Features:**
- Conflict detection and classification
- Dependency analysis
- AI-powered merge recommendations
- Change navigation and review
- Session management with reference IDs (MS_XXXXXX)
- Statistics and reporting

### 4. Process Transparency

**Process History** (`/process`)
- Complete request history
- Timeline visualization
- Confidence indicators (RAG similarity, JSON validity)
- Processing time metrics
- Error tracking and recovery

**Settings Management** (`/settings`)
- Configuration management
- AI model selection
- Parameter tuning

## Critical Design Decisions

### ❌ NO package_id in object_lookup
The `object_lookup` table is package-agnostic. It stores each unique object exactly once, regardless of how many packages contain it.

### ❌ NO duplicate objects
Always use `ObjectLookupRepository.find_or_create()` to prevent duplicates.

### ❌ NO customer-only objects in working set
The working set (changes table) contains ONLY objects from the delta (A→C comparison).

### ❌ NO old classifications
Only 4 classifications: NO_CONFLICT, CONFLICT, NEW, DELETED
(Removed: CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED)

### ✅ ALL tests use real packages
No mocking of package data. Use actual ZIP files from `applicationArtifacts/`.

### ✅ ALL 7 classification rules implemented
Rules 10a-10g must all be implemented and tested.

## Classification Rules (Quick Reference)

```python
# Rule 10a: MODIFIED in delta AND not modified in customer → NO_CONFLICT
# Rule 10b: MODIFIED in delta AND modified in customer → CONFLICT
# Rule 10c: MODIFIED in delta AND removed in customer → DELETED
# Rule 10d: NEW in delta → NEW
# Rule 10e: DEPRECATED in delta AND not modified in customer → NO_CONFLICT
# Rule 10f: DEPRECATED in delta AND modified in customer → CONFLICT
# Rule 10g: DEPRECATED in delta AND removed in customer → NO_CONFLICT
```

## Common Development Tasks

### Database Inspection

```python
# In Python shell
from models import db, MergeSession, ObjectLookup, Change
from app import create_app

app = create_app()
with app.app_context():
    # Check sessions
    sessions = MergeSession.query.all()
    for session in sessions:
        print(f"{session.reference_id}: {session.status}")
    
    # Check objects
    objects = ObjectLookup.query.limit(10).all()
    for obj in objects:
        print(f"{obj.uuid}: {obj.name} ({obj.object_type})")
    
    # Check changes
    changes = Change.query.filter_by(session_id=1).all()
    for change in changes:
        print(f"{change.classification}: {change.object.name}")
```

### Accessing Services via DI

```python
from core.dependency_container import DependencyContainer

container = DependencyContainer.get_instance()
orchestrator = container.get_service(ThreeWayMergeOrchestrator)
```

## Known Issues & Solutions

### Issue: Terminal Output Shows "TY=not a tty"

**Symptom:** Commands return "TY=not a tty" and Exit Code: -1

**Solution:** This is a terminal compatibility issue. Use the redirect-and-cat pattern for all pytest commands:
```bash
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

### Issue: Multiple App Instances Running

**Symptom:** "Address already in use" error

**Solution:**
```bash
# Find and kill all instances
ps aux | grep "app.py" | grep -v grep | awk '{print $2}' | xargs kill -9

# Verify port is free
lsof -i :5002
```

## Quick Reference Commands

```bash
# Start app
python app.py  # Runs on port 5002

# Check if running
lsof -i :5002
curl -s http://localhost:5002/ | head -5

# Stop app
lsof -ti :5002 | xargs kill -9

# Run tests (MANDATORY PATTERN)
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Check diagnostics
getDiagnostics(paths=["models.py"])

# Database shell
python
>>> from app import create_app
>>> from models import db, MergeSession
>>> app = create_app()
>>> with app.app_context():
...     sessions = MergeSession.query.all()
...     for s in sessions:
...         print(f"{s.reference_id}: {s.status}")

# Create schema
python create_three_way_merge_schema.py

# Verify schema
python verify_schema.py
```

## Environment Variables

```bash
AWS_REGION=us-east-1
BEDROCK_KB_ID=WAQ6NJLGKN
SECRET_KEY=<secret>
SQLALCHEMY_DATABASE_URI=sqlite:///instance/docflow.db
MAX_CONTENT_LENGTH=209715200  # 200MB for Appian packages
```

## Contact & Resources

- Application runs on: `http://localhost:5002`
- Test files: `applicationArtifacts/Three Way Testing Files/V2/`
- Spec documents: `.kiro/specs/three-way-merge-rebuild/`
- Database schema: `.kiro/specs/three-way-merge-database-schema.md`
- Service design: `.kiro/specs/three-way-merge-service-design.md`

## Critical Reminders

1. **NO package_id in object_lookup** - It's global!
2. **NO duplicate objects** - Use `find_or_create()`
3. **NO customer-only in working set** - Only delta objects
4. **NO old classifications** - Only 4 types: NO_CONFLICT, CONFLICT, NEW, DELETED
5. **ALL tests use real packages** - From `applicationArtifacts/Three Way Testing Files/V2/`
6. **ALL 7 rules implemented** - No shortcuts
7. **ALWAYS use redirect-and-cat for pytest** - Direct execution fails
8. **ALWAYS check for existing app instances** - Before starting new ones
