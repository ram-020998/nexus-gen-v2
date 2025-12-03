---
inclusion: always
---

# NexusGen - Complete AI Development Guide

**Version:** 5.0.0  
**Port:** 5002  
**Database:** SQLite at `instance/docflow.db`  
**Framework:** Flask 2.3+ with Python 3.8+  
**Last Updated:** December 3, 2025

---

## 🎯 Project Overview

NexusGen is a comprehensive Flask-based platform combining three major capabilities:

1. **Document Intelligence**: Spec breakdown, design verification, design creation, SQL conversion, AI chat
2. **Appian Application Analyzer**: Version comparison with SAIL code diff visualization
3. **Three-Way Merge Assistant**: Package comparison, conflict detection, and merge guidance

The application follows **Clean Architecture** principles with strict separation of concerns across controllers, services, domain, repositories, and core layers.

---

## 🏗️ Architecture & Design Principles

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTROLLERS                               │
│  Flask routes, request/response handling                     │
│  - breakdown_controller.py                                   │
│  - verify_controller.py                                      │
│  - create_controller.py                                      │
│  - merge_assistant_controller.py                             │
│  - chat_controller.py                                        │
│  - process_controller.py                                     │
│  - settings_controller.py                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     SERVICES                                 │
│  Business logic, orchestration                               │
│  - three_way_merge_orchestrator.py (main workflow)          │
│  - package_extraction_service.py                             │
│  - delta_comparison_service.py                               │
│  - customer_comparison_service.py                            │
│  - classification_service.py                                 │
│  - merge_guidance_service.py                                 │
│  - merge_summary_service.py                                  │
│  - comparison_persistence_service.py                         │
│  - change_navigation_service.py                              │
│  - change_action_service.py                                  │
│  - session_statistics_service.py                             │
│  - report_generation_service.py                              │
│  - bedrock_service.py (AI)                                   │
│  - q_agent_service.py (AI)                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                              │
│  Business entities, enums, strategies                        │
│  - entities.py (ObjectIdentity, DeltaChange, etc.)           │
│  - enums.py (PackageType, Classification, etc.)              │
│  - comparison_strategies.py                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   REPOSITORIES                               │
│  Data access layer                                           │
│  - object_lookup_repository.py                               │
│  - change_repository.py                                      │
│  - delta_comparison_repository.py                            │
│  - customer_comparison_repository.py                         │
│  - package_object_mapping_repository.py                      │
│  - request_repository.py                                     │
│  - chat_session_repository.py                                │
│  - [40+ object-specific repositories]                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     CORE LAYER                               │
│  Infrastructure, DI, exceptions                              │
│  - dependency_container.py (DI container)                    │
│  - base_service.py                                           │
│  - base_repository.py                                        │
│  - exceptions.py                                             │
│  - logger.py                                                 │
│  - cache.py                                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   MODELS (ORM)                               │
│  SQLAlchemy database models                                  │
│  - models.py (50+ tables)                                    │
└─────────────────────────────────────────────────────────────┘
```

### Core Design Principles

#### 1. Dependency Injection
- **Container:** `core/dependency_container.py` manages all service/repository instances
- **Singleton Pattern:** Services and repositories are singletons
- **Lazy Initialization:** Dependencies created on first access
- **Testability:** Easy to mock dependencies in tests

```python
# Using DI Container
from core.dependency_container import DependencyContainer

container = DependencyContainer.get_instance()
orchestrator = container.get_service(ThreeWayMergeOrchestrator)
```

#### 2. Base Classes
- **BaseService:** All services inherit from this, provides `_get_service()` and `_get_repository()`
- **BaseRepository:** Generic CRUD operations for all repositories
- **Type Safety:** Generic types ensure compile-time safety

```python
class MyService(BaseService):
    def _initialize_dependencies(self):
        self.my_repo = self._get_repository(MyRepository)
        self.other_service = self._get_service(OtherService)
```

#### 3. Domain-Driven Design
- **Entities:** Immutable dataclasses in `domain/entities.py`
- **Enums:** Type-safe enumerations in `domain/enums.py`
- **Strategies:** Pluggable comparison strategies in `domain/comparison_strategies.py`
- **No Database Coupling:** Domain layer has NO imports from models.py

#### 4. Exception Hierarchy
```python
NexusGenException (base)
├── ServiceException
│   ├── ValidationException
│   │   └── XMLParsingException
│   └── ThreeWayMergeException
├── RepositoryException
│   └── DatabaseTransactionException
├── TransientException
├── ConcurrencyException
└── ResourceConstraintException
```

---

## 🗄️ Database Schema

### Application-Wide Tables

#### requests - Document processing requests (breakdown, verify, create)
```sql
id INTEGER PRIMARY KEY
action_type VARCHAR(20) NOT NULL  -- 'breakdown', 'verify', 'create'
filename VARCHAR(255)  -- for breakdown (uploaded file)
input_text TEXT  -- for verify/create (pasted content)
status VARCHAR(20) DEFAULT 'processing'  -- 'processing', 'completed', 'error'
rag_query TEXT  -- query sent to RAG
rag_response TEXT  -- RAG API response
final_output TEXT  -- processed result from Q agent
reference_id VARCHAR(20)  -- RQ_ND_001 format
agent_name VARCHAR(50)  -- breakdown-agent, verify-agent, etc.
model_name VARCHAR(100)  -- amazon.nova-pro-v1:0
parameters TEXT  -- JSON string of model parameters
total_time INTEGER  -- Total processing time in seconds
step_durations TEXT  -- JSON string of step timings
raw_agent_output TEXT  -- Raw Q agent response before cleaning
q_agent_prompt TEXT  -- Prompt sent to Q agent
rag_similarity_avg FLOAT  -- Average RAG similarity score
json_valid BOOLEAN DEFAULT TRUE  -- JSON validity flag
error_log TEXT  -- Error messages and retry attempts
export_path VARCHAR(500)  -- Excel file path (breakdown only)
created_at DATETIME
updated_at DATETIME
```

#### chat_sessions - AI chat conversations
```sql
id INTEGER PRIMARY KEY
session_id VARCHAR(36)  -- UUID
question TEXT NOT NULL
rag_response TEXT
answer TEXT
created_at DATETIME
```

### Core Three-Way Merge Tables

#### merge_sessions
```sql
id INTEGER PRIMARY KEY
reference_id VARCHAR(50) UNIQUE NOT NULL  -- Format: MRG_001, MRG_002, etc.
status VARCHAR(20) NOT NULL DEFAULT 'processing'  -- processing, ready, in_progress, completed, error
total_changes INTEGER DEFAULT 0
reviewed_count INTEGER DEFAULT 0
skipped_count INTEGER DEFAULT 0
estimated_complexity VARCHAR(20)
estimated_time_hours FLOAT
created_at DATETIME
updated_at DATETIME
```

#### packages
```sql
id INTEGER PRIMARY KEY
session_id INTEGER FK(merge_sessions.id) ON DELETE CASCADE
package_type VARCHAR(20) NOT NULL  -- 'base', 'customized', 'new_vendor'
filename VARCHAR(500) NOT NULL
total_objects INTEGER DEFAULT 0
created_at DATETIME
```

#### object_lookup (GLOBAL REGISTRY - NO package_id!)
```sql
id INTEGER PRIMARY KEY
uuid VARCHAR(255) UNIQUE NOT NULL  -- Appian object UUID
name VARCHAR(500) NOT NULL
object_type VARCHAR(50) NOT NULL  -- 'Interface', 'Process Model', etc.
description TEXT
created_at DATETIME

-- CRITICAL: NO package_id column! This is package-agnostic!
```

#### package_object_mappings (JUNCTION TABLE)
```sql
id INTEGER PRIMARY KEY
package_id INTEGER FK(packages.id) ON DELETE CASCADE
object_id INTEGER FK(object_lookup.id) ON DELETE CASCADE
created_at DATETIME

UNIQUE(package_id, object_id)
INDEX(package_id, object_id)
```

#### delta_comparison_results (Set D: A→C)
```sql
id INTEGER PRIMARY KEY
session_id INTEGER FK(merge_sessions.id) ON DELETE CASCADE
object_id INTEGER FK(object_lookup.id) ON DELETE CASCADE
change_category VARCHAR(20) NOT NULL  -- 'NEW', 'MODIFIED', 'DEPRECATED'
change_type VARCHAR(20) NOT NULL  -- 'ADDED', 'MODIFIED', 'REMOVED'
version_changed BOOLEAN DEFAULT FALSE
content_changed BOOLEAN DEFAULT FALSE
created_at DATETIME

UNIQUE(session_id, object_id)
INDEX(session_id, change_category)
```

#### customer_comparison_results (Set E: A→B)
```sql
id INTEGER PRIMARY KEY
session_id INTEGER FK(merge_sessions.id) ON DELETE CASCADE
object_id INTEGER FK(object_lookup.id) ON DELETE CASCADE
change_category VARCHAR(20) NOT NULL  -- 'NEW', 'MODIFIED', 'DEPRECATED'
change_type VARCHAR(20) NOT NULL  -- 'ADDED', 'MODIFIED', 'REMOVED'
version_changed BOOLEAN DEFAULT FALSE
content_changed BOOLEAN DEFAULT FALSE
created_at DATETIME

UNIQUE(session_id, object_id)
INDEX(session_id, change_category)
```

#### changes (WORKING SET - references object_lookup via object_id)
```sql
id INTEGER PRIMARY KEY
session_id INTEGER FK(merge_sessions.id) ON DELETE CASCADE
object_id INTEGER FK(object_lookup.id) ON DELETE CASCADE
classification VARCHAR(50) NOT NULL  -- 'NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED'
vendor_change_type VARCHAR(20)  -- 'ADDED', 'MODIFIED', 'REMOVED'
customer_change_type VARCHAR(20)  -- 'ADDED', 'MODIFIED', 'REMOVED'
display_order INTEGER NOT NULL
status VARCHAR(20) DEFAULT 'pending'  -- 'pending', 'reviewed', 'skipped'
notes TEXT
reviewed_at DATETIME
reviewed_by VARCHAR(255)
ai_summary TEXT
ai_summary_status VARCHAR(20) DEFAULT 'pending'  -- 'pending', 'processing', 'completed', 'failed'
ai_summary_generated_at DATETIME
created_at DATETIME

-- Dual Object Tracking (for customer-only objects)
vendor_object_id INTEGER FK(object_lookup.id) ON DELETE CASCADE
customer_object_id INTEGER FK(object_lookup.id) ON DELETE CASCADE

INDEX(session_id, classification)
INDEX(session_id, object_id)
INDEX(session_id, display_order)
INDEX(session_id, status)
```

#### object_versions (PACKAGE-SPECIFIC VERSIONS)
```sql
id INTEGER PRIMARY KEY
object_id INTEGER FK(object_lookup.id) ON DELETE CASCADE
package_id INTEGER FK(packages.id) ON DELETE CASCADE
version_uuid VARCHAR(255)
sail_code TEXT
fields TEXT  -- JSON string
properties TEXT  -- JSON string
raw_xml TEXT
created_at DATETIME

UNIQUE(object_id, package_id)
INDEX(object_id, package_id)
```

### Object-Specific Tables (40+ tables)

All follow this pattern:
```sql
CREATE TABLE <object_type>s (
    id INTEGER PRIMARY KEY,
    object_id INTEGER FK(object_lookup.id) ON DELETE CASCADE,
    package_id INTEGER FK(packages.id) ON DELETE CASCADE,
    uuid VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    version_uuid VARCHAR(255),
    <object_specific_fields>,
    created_at DATETIME,
    
    UNIQUE(object_id, package_id),
    INDEX(object_id, package_id)
);
```

**Supported Object Types:**
- interfaces + interface_parameters + interface_security
- expression_rules + expression_rule_inputs
- process_models + process_model_nodes + process_model_flows + process_model_variables
- record_types + record_type_fields + record_type_relationships + record_type_views + record_type_actions
- cdts + cdt_fields
- integrations
- web_apis
- sites
- groups
- constants
- connected_systems
- data_stores
- unknown_objects

### Comparison Result Tables

- **interface_comparisons** - Interface-specific comparison results
- **process_model_comparisons** - Process model comparison with Mermaid diagrams
- **record_type_comparisons** - Record type comparison results

---

## 🔄 Three-Way Merge Workflow

### 10-Step Workflow

```
1. Create session record (status='PROCESSING')
2. Extract Package A (Base Version)
3. Extract Package B (Customer Version)
4. Extract Package C (New Vendor Version)
5. Perform delta comparison (A→C, Set D)
6. Perform customer comparison (A→B, Set E)
7. Classify changes (set-based: D ∩ E, D \ E, E \ D)
8. Persist detailed comparisons
9. Generate merge guidance
10. Trigger AI summary generation (async)
11. Update session status to 'READY'
12. Commit transaction
```

**Key Workflow Characteristics:**
- **Transactional:** All operations in a single transaction
- **Rollback on error:** Any failure rolls back entire session
- **Status tracking:** Session status updated at each step
- **Error handling:** Comprehensive error handling with logging
- **Idempotent:** Can be retried safely

### Set-Based Classification Logic

```
Set D = Vendor changes (A→C delta)
Set E = Customer changes (A→B delta)

D ∩ E = Objects changed by both parties
D \ E = Objects changed by vendor only
E \ D = Objects changed by customer only

For objects in D ∩ E:
  - Compare B vs C content
  - If B == C: NO_CONFLICT (same changes)
  - If B != C: CONFLICT (different changes)

For objects in D \ E:
  - NO_CONFLICT (vendor only)

For objects in E \ D:
  - Not in working set (customer-only changes)
```

### Classification Rules

```python
# Rule 10a: MODIFIED in delta AND not modified in customer → NO_CONFLICT
# Rule 10b: MODIFIED in delta AND modified in customer → CONFLICT (if B != C)
# Rule 10c: MODIFIED in delta AND removed in customer → DELETED
# Rule 10d: NEW in delta → NEW
# Rule 10e: DEPRECATED in delta AND not modified in customer → NO_CONFLICT
# Rule 10f: DEPRECATED in delta AND modified in customer → CONFLICT
# Rule 10g: DEPRECATED in delta AND removed in customer → NO_CONFLICT
```

### 4 Classifications

```python
class Classification(Enum):
    NO_CONFLICT = 'NO_CONFLICT'  # Auto-merge safe
    CONFLICT = 'CONFLICT'         # Manual review required
    NEW = 'NEW'                   # New vendor object
    DELETED = 'DELETED'           # Customer removed, vendor modified
```

---

## 🚀 Development Workflow

### Application Startup

#### ⚠️ CRITICAL: Always Check for Existing Instances First

```bash
# 1. Check if app is already running
lsof -i :5002
ps aux | grep "app.py"
curl -s http://localhost:5002/ | head -5

# 2. If running, stop it first
lsof -ti :5002 | xargs kill -9

# 3. Start the app
python app.py

# OR use controlBashProcess for background
controlBashProcess(action="start", command="python app.py")
getProcessOutput(processId=<id>, lines=50)
```

### Environment Setup

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

# Initialize database
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Database Management

```bash
# Create three-way merge schema
python create_three_way_merge_schema.py

# Verify schema
python verify_schema.py

# Check schema structure
python check_schema.py

# Check for duplicates (should return 0)
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    result = db.session.execute('''
        SELECT uuid, COUNT(*) as count 
        FROM object_lookup 
        GROUP BY uuid 
        HAVING count > 1
    ''')
    print(f'Duplicates: {len(result.fetchall())}')
"
```

### Running Validation Queries

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

---

## 🧪 Testing Requirements

### ⚠️ MANDATORY TEST EXECUTION PATTERN

**YOU MUST ALWAYS USE THIS EXACT PATTERN:**

```bash
# MANDATORY: Redirect output to file and then cat it
python -m pytest <test_path> <options> > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**WHY THIS IS MANDATORY:**
- Direct pytest execution returns "TY=not a tty" error and Exit Code: -1
- This prevents seeing actual test results
- The redirect-and-cat pattern is the ONLY way to see test output properly

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

**❌ NEVER USE THESE (THEY WILL FAIL):**
```bash
pytest tests/test_file.py  # ❌ WRONG
python -m pytest tests/test_file.py  # ❌ WRONG
python -m pytest tests/test_file.py -v  # ❌ WRONG
```

### Test Data Location

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

**Property Tests:**
1. Property 1: No duplicate objects in object_lookup
2. Property 2: Package-object mappings are consistent
3. Property 3: Delta-driven working set (delta_count == change_count)
4. Property 4: All delta objects are classified
5. Property 5-7: NEW, DEPRECATED, MODIFIED detection
6. Property 8-13: All 7 classification rules
7. Property 14: Referential integrity
8. Property 18: find_or_create idempotence

---

## 🌐 UI/Frontend Testing with Chrome DevTools MCP

### ⚠️ IMPORTANT: Use Chrome DevTools MCP for UI Testing

When testing the web interface, use the Chrome DevTools MCP tools instead of manual browser testing.

**Available Tools:**

```python
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
time.sleep(3)

# 2. Navigate to the application
mcp_chrome_devtools_navigate_page(url="http://localhost:5002")

# 3. Take snapshot to see page structure
snapshot = mcp_chrome_devtools_take_snapshot()

# 4. Test navigation to merge assistant
mcp_chrome_devtools_click(uid="merge-assistant-link")

# 5. Upload test packages
mcp_chrome_devtools_upload_file(
    uid="base-package-input",
    filePath="applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip"
)

# 6. Check network requests
requests = mcp_chrome_devtools_list_network_requests()

# 7. Check console for errors
console_msgs = mcp_chrome_devtools_list_console_messages(types=["error", "warn"])

# 8. Take screenshot of results
mcp_chrome_devtools_take_screenshot(filePath="test_results.png")
```

---

## 📝 Critical Design Decisions

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

### ✅ Transactional workflow
All 10 steps execute in a single database transaction. Rollback on any error.

### ✅ Async AI summaries
AI summary generation happens AFTER commit in a background thread.

---

## 🔧 Common Development Tasks

### Accessing Services via DI

```python
from core.dependency_container import DependencyContainer

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

### Database Inspection

```python
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

### Using getDiagnostics

```python
# Check for syntax/type errors
getDiagnostics(paths=["services/package_extraction_service.py"])

# Check multiple files
getDiagnostics(paths=["models.py", "app.py", "config.py"])
```

---

## 🚨 Known Issues & Solutions

### Issue: Terminal Output Shows "TY=not a tty"

**Symptom:** Commands return "TY=not a tty" and Exit Code: -1

**Solution:** Use the redirect-and-cat pattern for all pytest commands:
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

### Issue: Duplicate Objects in object_lookup

**Symptom:** Multiple objects with same UUID

**Solution:**
```python
# Always use find_or_create
object_lookup = self.object_lookup_repo.find_or_create(
    uuid=obj_uuid,
    name=obj_name,
    object_type=obj_type,
    description=obj_description
)
```

---

## 📚 Quick Reference Commands

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

---

## 🌍 Environment Variables

```bash
AWS_REGION=us-east-1
BEDROCK_KB_ID=WAQ6NJLGKN
SECRET_KEY=<secret>
SQLALCHEMY_DATABASE_URI=sqlite:///instance/docflow.db
MAX_CONTENT_LENGTH=209715200  # 200MB for Appian packages
```

---

## 📋 Critical Reminders

1. **NO package_id in object_lookup** - It's global!
2. **NO duplicate objects** - Use `find_or_create()`
3. **NO customer-only in working set** - Only delta objects
4. **NO old classifications** - Only 4 types: NO_CONFLICT, CONFLICT, NEW, DELETED
5. **ALL tests use real packages** - From `applicationArtifacts/Three Way Testing Files/V2/`
6. **ALL 7 rules implemented** - No shortcuts
7. **ALWAYS use redirect-and-cat for pytest** - Direct execution fails
8. **ALWAYS check for existing app instances** - Before starting new ones
9. **ALWAYS use Chrome DevTools MCP for UI testing** - Not manual browser testing
10. **ALWAYS commit before async AI summaries** - Background thread needs committed data

---

## 🎨 Frontend Stack

- **Framework:** Bootstrap 5.3
- **Icons:** Font Awesome 6
- **Theme:** Custom dark theme (Appian colors)
- **JavaScript:** Vanilla JS (no frameworks)
- **Templates:** Jinja2

---

## 📊 Application Features

### 1. Document Intelligence

- **Spec Breakdown** (`/breakdown`): Upload documents, extract user stories
- **Design Verification** (`/verify`): AI validation of design documents
- **Design Creation** (`/create`): Generate design from acceptance criteria
- **SQL Conversion** (`/convert`): MariaDB ↔ Oracle conversion
- **AI Chat** (`/chat`): Interactive assistant

### 2. Appian Application Analyzer

- Version comparison with SAIL diff
- Object-level analysis
- UUID resolution
- Business impact summaries

### 3. Three-Way Merge Assistant

- **Upload** (`/merge/upload`): Upload 3 packages
- **Sessions** (`/merge/sessions`): View all sessions
- **Summary** (`/merge/<ref_id>/summary`): Session overview
- **Workflow** (`/merge/<ref_id>/workflow`): Review changes
- **API Endpoints:** RESTful API for all operations

---

## 🔗 Resources

- Application: `http://localhost:5002`
- Test files: `applicationArtifacts/Three Way Testing Files/V2/`
- Spec documents: `.kiro/specs/three-way-merge-rebuild/`
- Database schema: `.kiro/specs/three-way-merge-database-schema.md`
- Service design: `.kiro/specs/three-way-merge-service-design.md`
- Database: `instance/docflow.db`
- Logs: `logs/merge_assistant.log`, `logs/nexusgen.log`

---

## 📦 Technology Stack Details

### Backend
- **Flask:** 2.3+
- **Python:** 3.8+
- **Database:** SQLite + SQLAlchemy ORM with connection pooling
- **AI Services:** AWS Bedrock RAG, Amazon Q CLI Agents

### Frontend
- **Framework:** Bootstrap 5.3
- **Icons:** Font Awesome 6
- **Theme:** Custom dark theme (Appian colors)
- **JavaScript:** Vanilla JS (no frameworks)
- **Templates:** Jinja2

### Document Processing
- **python-docx:** Word document handling
- **openpyxl:** Excel file generation
- **PyPDF2:** PDF processing

---

## 🎯 Key Design Principles Summary

1. **No Duplication:** Each object stored once in `object_lookup`
2. **Package-Agnostic:** `object_lookup` has NO `package_id` column
3. **Explicit Mapping:** `package_object_mappings` tracks membership
4. **Delta-Driven:** Working set contains only A→C delta objects
5. **Referential Integrity:** All foreign keys enforced with CASCADE
6. **Clean Architecture:** Strict separation of concerns across layers
7. **Dependency Injection:** Centralized DI container for all services
8. **Domain-Driven Design:** Domain layer has NO database coupling
9. **Transactional Workflow:** All operations in single transaction
10. **Async AI Processing:** AI summaries generated after commit

---

**Last Updated:** December 3, 2025  
**Maintained By:** AI Development Team
