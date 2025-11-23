---
inclusion: always
---

# NexusGen Application Context & Testing Guide

**Version:** 4.0.0  
**Port:** 5002  
**Database:** SQLite at `instance/docflow.db`

## Application Overview

Flask-based platform for document intelligence and Appian application analysis with SAIL code diff visualization.

### Core Features
1. **Document Intelligence** - Breakdown, verification, creation with AI
2. **Appian Analyzer** - Version comparison with SAIL code diffs
3. **Three-Way Merge** - Package comparison and conflict resolution
4. **SQL Conversion** - MariaDB ↔ Oracle conversion

## Architecture

### Technology Stack
- **Backend:** Flask 2.3+, Python 3.8+
- **Database:** SQLite + SQLAlchemy ORM
- **AI:** AWS Bedrock, Amazon Q CLI Agents
- **Frontend:** Bootstrap 5, Font Awesome 6
- **Port:** 5002

## Starting the Application

### ⚠️ IMPORTANT: Always Check for Existing Instances First

Before starting the application, **ALWAYS** check if it's already running to avoid multiple instances:

```bash
# Check if app is already running on port 5002
lsof -i :5002

# Or check for python processes running app.py
ps aux | grep "app.py"

# Or use curl to test if the app responds
curl -s http://localhost:5002/analyzer | head -5
```

### Starting the App

**Option 1: Using controlBashProcess (Recommended for development)**
```bash
# Check for existing background processes first
listProcesses

# If app is running, stop it first
controlBashProcess(action="stop", processId=<id>)

# Start the app as a background process
controlBashProcess(action="start", command="python3.13 app.py")

# Check process output
getProcessOutput(processId=<id>, lines=50)
```

**Option 2: Manual Terminal (For production/testing)**
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Start Flask app
python app.py
```

### Stopping the App

```bash
# If using controlBashProcess
controlBashProcess(action="stop", processId=<id>)

# If running manually, use Ctrl+C in the terminal

# Or kill by port
lsof -ti :5002 | xargs kill -9
```

### Troubleshooting

**Problem: "Address already in use" error**
```bash
# Find and kill the process using port 5002
lsof -ti :5002 | xargs kill -9

# Then restart the app
```

**Problem: Multiple instances running**
```bash
# List all background processes
listProcesses

# Stop all instances
ps aux | grep "app.py" | grep -v grep | awk '{print $2}' | xargs kill -9

# Verify port is free
lsof -i :5002
```

### Key Directories
```
nexus-gen-v2/
├── app.py                          # Main Flask app with DI container
├── config.py                       # Configuration
├── models.py                       # SQLAlchemy models
├── controllers/                    # Route handlers
│   ├── analyzer_controller.py      # Appian analyzer routes
│   ├── merge_assistant_controller.py  # Three-way merge routes
│   ├── breakdown_controller.py     # Document breakdown
│   └── base_controller.py          # Base controller
├── services/
│   ├── ai/                         # AI integrations
│   │   ├── bedrock_service.py      # AWS Bedrock RAG
│   │   └── q_agent_service.py      # Amazon Q CLI agents
│   ├── appian_analyzer/            # Appian analysis engine
│   │   ├── analyzer.py             # Main analyzer (OOP)
│   │   ├── parsers.py              # XML parsers
│   │   ├── sail_formatter.py       # SAIL code formatter
│   │   ├── enhanced_comparison_service.py  # Dual-layer comparison
│   │   ├── logger.py               # Request-specific logging
│   │   └── models.py               # Appian object models
│   ├── comparison/                 # Comparison orchestration
│   │   ├── comparison_service.py   # Main workflow
│   │   ├── blueprint_analyzer.py   # Blueprint generation
│   │   └── comparison_engine.py    # Comparison logic
│   ├── merge/                      # Three-way merge
│   │   ├── three_way_merge_service.py
│   │   ├── package_service.py
│   │   └── change_service.py
│   └── request/                    # Request management
│       ├── request_service.py
│       ├── file_service.py
│       └── document_service.py
├── repositories/                   # Data access layer
│   ├── comparison_repository.py
│   ├── request_repository.py
│   └── merge_session_repository.py
├── core/                           # Clean architecture
│   ├── dependency_container.py     # DI container
│   ├── interfaces.py               # Abstract base classes
│   ├── exceptions.py               # Custom exceptions
│   └── base_service.py             # Base service
├── templates/                      # Jinja2 templates
├── static/                         # CSS, JS, images
├── logs/                           # Application logs
└── applicationArtifacts/Testing Files/  # Test data
    ├── SourceSelectionv2.4.0.zip
    └── SourceSelectionv2.6.0.zip
```

## How the Application Works

### Appian Comparison Workflow

**1. Upload Phase**
- User uploads two ZIP files (old/new versions) via `/analyzer`
- Files saved to `uploads/` temporarily
- Controller: `analyzer_controller.py::compare_versions()`

**2. Blueprint Generation Phase**
- Service: `AppianAnalyzer` (services/appian_analyzer/analyzer.py)
- Parses XML objects: Sites, Records, Process Models, Interfaces, Rules, etc.
- Builds `object_lookup` table (UUID → object mapping)
- Resolves UUID references to readable names
- Formats SAIL code via `SAILFormatter`
- Generates metadata and complexity assessment

**3. Comparison Phase**
- Service: `EnhancedComparisonService` with dual-layer comparison
  - **Layer 1:** Version History (checks version UUIDs)
  - **Layer 2:** Content Diff Hash (detects actual changes)
- Identifies: ADDED, REMOVED, MODIFIED, NOT_CHANGED
- Detects specific changes: SAIL code, business logic, fields

**4. Storage Phase**
- Stored in `comparison_requests` table
- Fields: blueprints (JSON), comparison_results (JSON), processing time, status
- Reference ID format: `CMP_001`, `CMP_002`, etc.

**5. Display Phase**
- Summary: `/analyzer/request/<id>` - All changes by category
- Detail: `/analyzer/object/<id>/<uuid>` - SAIL code diffs with highlighting

### Service Layer Architecture

**Dependency Injection:**
- Container: `core/dependency_container.py`
- Services registered in `app.py::_register_services()`
- Repositories registered in `app.py::_register_repositories()`

**Key Services:**
- `ComparisonService` - Orchestrates comparison workflow
- `BlueprintAnalyzer` - Wraps AppianAnalyzer for web use
- `ComparisonRequestManager` - Manages database operations
- `BedrockRAGService` - AWS Bedrock integration
- `QAgentService` - Amazon Q CLI agent integration

## Testing the Application

### Pre-Testing Checklist

**ALWAYS perform these checks before starting any testing:**

1. **Check for existing app instances:**
   ```bash
   # List background processes
   listProcesses
   
   # Check port 5002
   lsof -i :5002
   
   # Test if app responds
   curl -s http://localhost:5002/analyzer | head -5
   ```

2. **Stop existing instances if found:**
   ```bash
   # Stop background process
   controlBashProcess(action="stop", processId=<id>)
   
   # Or kill by port
   lsof -ti :5002 | xargs kill -9
   ```

3. **Start fresh instance:**
   ```bash
   # Start as background process
   controlBashProcess(action="start", command="python3.13 app.py")
   
   # Wait a few seconds for startup
   sleep 3
   
   # Verify it's running
   curl -s http://localhost:5002/analyzer | head -5
   ```

The app runs on `http://localhost:5002`

### Using Chrome DevTools for Testing

**Available Chrome DevTools MCP Tools:**
- `mcp_chrome_devtools_navigate_page` - Navigate to URLs or reload
- `mcp_chrome_devtools_take_snapshot` - Get page content structure
- `mcp_chrome_devtools_click` - Click elements
- `mcp_chrome_devtools_upload_file` - Upload files to file inputs
- `mcp_chrome_devtools_fill` - Fill form fields
- `mcp_chrome_devtools_list_pages` - List open browser tabs

**Common Testing Workflow:**

1. **Navigate to analyzer page:**
   ```
   navigate_page(url="http://localhost:5002/analyzer")
   ```

2. **Take snapshot to get element UIDs:**
   ```
   take_snapshot()
   ```

3. **Upload test files:**
   ```
   upload_file(uid="<file_input_uid>", 
               filePath="applicationArtifacts/Testing Files/SourceSelectionv2.4.0.zip")
   ```

4. **Click compare button:**
   ```
   click(uid="<button_uid>")
   ```

5. **Check results:**
   ```
   navigate_page(url="http://localhost:5002/analyzer/object/<request_id>/<object_uuid>")
   ```

### Test Data Location

Test ZIP files are located in:
```
applicationArtifacts/Testing Files/
├── SourceSelectionv2.4.0.zip  # Old version
└── SourceSelectionv2.6.0.zip  # New version
```

### Key Test Objects

**Test Interface:** `AS_GSS_HCL_vendorsTab`
- UUID: `_a-0001ed6e-54f1-8000-9df6-011c48011c48_15269031`
- Type: Interface
- Has SAIL code changes between versions
- Good for testing SAIL code diff display

### Verifying Fixes

**To verify SAIL code diffs are working:**

1. Run a comparison (creates a new request ID)
2. Navigate to: `http://localhost:5002/analyzer/object/<request_id>/_a-0001ed6e-54f1-8000-9df6-011c48011c48_15269031`
3. Check for:
   - "SAIL Code Comparison" section is visible
   - "Before" and "After" columns are displayed
   - Diff highlighting shows added/removed lines

**Working Example:** Request 2 (old system) and Request 12+ (fixed new system)
**Broken Example:** Requests 7-11 (before fix)

## Common Development Tasks

### Running Tests

## ⚠️ CRITICAL: MANDATORY TEST EXECUTION PATTERN ⚠️

**YOU MUST ALWAYS USE THIS EXACT PATTERN WHEN RUNNING PYTEST COMMANDS:**

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
python -m pytest tests/test_analyzer.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run with verbose output
python -m pytest -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test by name
python -m pytest tests/test_file.py::TestClass::test_method -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run tests matching a pattern
python -m pytest -k "test_property_7" -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
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

**ALWAYS ADD TIMEOUT:**
```bash
# Always include timeout parameter (120000ms = 2 minutes is good default)
<parameter name="timeout">120000

### Checking Diagnostics

```bash
# Use getDiagnostics tool for syntax/type errors
getDiagnostics(paths=["services/appian_analyzer/web_compatibility_layer.py"])
```

### Debugging

**Flask logs:** Check the terminal where `python app.py` is running

**Process output:** If using `controlBashProcess`, use:
```
getProcessOutput(processId=<id>, lines=100)
```

**Database inspection:**
```python
# In Python shell
from models import db, ComparisonRequest
from app import create_app

app = create_app()
with app.app_context():
    requests = ComparisonRequest.query.all()
    for req in requests:
        print(f"{req.reference_id}: {req.status}")
```

## Known Issues & Solutions

### Issue: SAIL Code Diffs Not Showing

**Symptom:** Object details page shows "Basic Information" but no "SAIL Code Comparison" section

**Root Cause:** `WebCompatibilityLayer` was checking `content_diff` for "SAIL code" string, but comparison wasn't generating it

**Solution:** Modified `_build_change_object()` to always include SAIL code if both objects have the attribute (fixed in commit with SAIL_CODE_DIFF_FIX.md)

### Issue: Process Output Not Showing

**Symptom:** `getProcessOutput()` returns empty or minimal output

**Solution:** Flask buffers output. Use `print()` statements and check immediately after operations complete.

## Database Schema

### comparison_requests
```python
id: INTEGER PRIMARY KEY
reference_id: VARCHAR(20)           # CMP_001, CMP_002, etc.
old_app_name: VARCHAR(255)
new_app_name: VARCHAR(255)
status: VARCHAR(20)                 # processing/completed/error
old_app_blueprint: TEXT             # JSON blueprint
new_app_blueprint: TEXT             # JSON blueprint
comparison_results: TEXT            # JSON comparison data
total_time: INTEGER                 # Seconds
created_at: DATETIME
updated_at: DATETIME
```

### requests
```python
id: INTEGER PRIMARY KEY
action_type: VARCHAR(20)            # breakdown/verify/create
filename: VARCHAR(255)
input_text: TEXT
status: VARCHAR(20)
rag_query: TEXT
rag_response: TEXT
final_output: TEXT                  # JSON format
reference_id: VARCHAR(20)           # RQ_BR_001, etc.
total_time: INTEGER
created_at: DATETIME
updated_at: DATETIME
```

### merge_sessions
```python
id: INTEGER PRIMARY KEY
session_id: VARCHAR(36)             # UUID
base_package_name: VARCHAR(255)
source_package_name: VARCHAR(255)
target_package_name: VARCHAR(255)
status: VARCHAR(20)
merge_results: TEXT                 # JSON
created_at: DATETIME
```

### chat_sessions
```python
id: INTEGER PRIMARY KEY
session_id: VARCHAR(36)             # UUID
question: TEXT
rag_response: TEXT
answer: TEXT
created_at: DATETIME
```

## Important Code Patterns

### Request-Specific Logging
```python
from services.appian_analyzer.logger import create_request_logger

logger = create_request_logger(request.reference_id)
logger.info("Starting comparison")
logger.log_stage("Analysis", {"objects": 1000})
logger.log_metrics({"total_changes": 50, "impact_level": "MEDIUM"})
logger.log_completion(status='success', total_changes=50)
```

### Accessing Services via DI
```python
from core.dependency_container import DependencyContainer

container = DependencyContainer.get_instance()
comparison_service = container.get_service(ComparisonService)
```

### Accessing Comparison Data
```python
comparison_data = json.loads(comparison_request.comparison_results)

# Structure:
{
    "comparison_summary": {
        "total_changes": 78,
        "impact_level": "MEDIUM"
    },
    "changes_by_category": {
        "interfaces": {
            "added": 22,
            "modified": 56,
            "removed": 0,
            "details": [...]
        }
    }
}
```

### SAIL Code Diff Requirements
```python
# Required fields for SAIL code diff display:
change_obj = {
    "uuid": "...",
    "name": "...",
    "type": "Interface",
    "change_type": "MODIFIED",
    "sail_code_before": "...",  # Required
    "sail_code_after": "..."    # Required
}
```

### Repository Pattern
```python
from repositories.comparison_repository import ComparisonRepository

repo = ComparisonRepository(container)
request = repo.find_by_id(request_id)
all_requests = repo.find_all()
```

## Quick Reference Commands

```bash
# Start app
python app.py  # Runs on port 5002

# Check if running
lsof -i :5002
curl -s http://localhost:5002/analyzer | head -5

# Stop app
lsof -ti :5002 | xargs kill -9

# Run tests (MANDATORY PATTERN)
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Check diagnostics
getDiagnostics(paths=["services/appian_analyzer/analyzer.py"])

# Database shell
python
>>> from app import create_app
>>> from models import db, ComparisonRequest
>>> app = create_app()
>>> with app.app_context():
...     requests = ComparisonRequest.query.all()
...     for req in requests:
...         print(f"{req.reference_id}: {req.status}")

# View logs
tail -f logs/appian_analyzer.log
```

## Development Log

**Location:** `.kiro/DEVELOPMENT_LOG.md`

This is a running log of all development activities, issues, and fixes. When working on issues or implementing features:

1. **Add entries to the log** with timestamp and summary
2. **Include:** Issue description, investigation steps, root cause, solution, files modified, verification steps
3. **Keep it updated** so future sessions can understand what was worked on and where to continue
4. **Don't create separate .md files** for summaries - add them to the development log instead
5. **Format:** Use markdown with clear sections and timestamps (YYYY-MM-DD format)

This keeps the repository clean and provides a single source of truth for development history.

### Log Entry Template
```markdown
## YYYY-MM-DD - [Feature/Issue Name]

### Issue
Brief description of the problem or feature

### Investigation
Steps taken to understand the issue

### Root Cause
What was causing the problem

### Solution
How it was fixed

### Files Modified
- List of files changed

### Verification
How the fix was tested

### Status
✅ RESOLVED / ⚠️ IN PROGRESS / ❌ BLOCKED
```

## Contact & Resources

- Application runs on: `http://localhost:5002`
- Test files: `applicationArtifacts/Testing Files/`
- Development log: `.kiro/DEVELOPMENT_LOG.md`
- Documentation: `SAIL_CODE_DIFF_FIX.md`, `QUICK_TEST_GUIDE.md`


## Key Technical Details

### Logging System
- **Location:** `logs/appian_analyzer.log`
- **Features:** Request-specific tracking, stage logging, metrics, auto-rotation (10MB, 5 backups)
- **Usage:** `create_request_logger(reference_id)` for request-specific logs

### SAIL Code Formatter
- **Location:** `services/appian_analyzer/sail_formatter.py`
- **Features:** UUID → name resolution, internal → public function names
- **Examples:**
  - `#"SYSTEM_SYSRULES_headerContentLayout"` → `a!headerContentLayout`
  - `#"_a-uuid"` → `rule!ObjectName`
  - `cons!uuid` → `cons!ConstantName`

### Dual-Layer Comparison
- **Layer 1:** Version History (checks version UUIDs)
- **Layer 2:** Content Diff Hash (detects actual changes)
- **Service:** `EnhancedComparisonService`
- **Fallback:** Basic comparison if enhanced fails

### Performance Benchmarks
- Small apps (<500 objects): 2-3 seconds
- Medium apps (500-1500 objects): 4-5 seconds
- Large apps (1500+ objects): 6-8 seconds

### Clean Architecture
- **DI Container:** `core/dependency_container.py`
- **Base Classes:** `BaseService`, `BaseController`, `RepositoryInterface`
- **Exception Hierarchy:** `NexusGenException` → `ServiceException`, `ValidationException`
- **Pattern:** Repository → Service → Controller

### Critical Files
- `app.py` - Main app with DI registration
- `services/comparison/comparison_service.py` - Comparison orchestration
- `services/appian_analyzer/analyzer.py` - Main analyzer (OOP design)
- `services/appian_analyzer/enhanced_comparison_service.py` - Dual-layer comparison
- `controllers/analyzer_controller.py` - Analyzer routes
- `repositories/comparison_repository.py` - Data access

### Environment Variables
```bash
AWS_REGION=us-east-1
BEDROCK_KB_ID=WAQ6NJLGKN
SECRET_KEY=<secret>
SQLALCHEMY_DATABASE_URI=sqlite:///instance/docflow.db
MAX_CONTENT_LENGTH=16777216  # 16MB
```
