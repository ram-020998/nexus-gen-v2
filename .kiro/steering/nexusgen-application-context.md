---
inclusion: always
---

# NexusGen Application Context & Testing Guide

## Application Overview

**NexusGen** is a Flask-based web application for analyzing and comparing Appian applications. It provides document intelligence, SQL conversion, and comprehensive Appian application version comparison capabilities.

### Core Features
1. **Document Breakdown** - Extract and analyze document structures
2. **Design Creation** - Generate design documents
3. **SQL Conversion** - Convert between MariaDB and Oracle SQL
4. **Appian Analyzer** - Compare two versions of Appian applications and identify changes

## Application Architecture

### Technology Stack
- **Backend:** Flask (Python)
- **Database:** SQLite (via SQLAlchemy)
- **Frontend:** HTML/CSS/JavaScript with Bootstrap
- **Port:** 5002 (default)

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
├── app.py                          # Main Flask application
├── controllers/                    # Route controllers
│   ├── analyzer_controller.py      # Appian comparison routes
│   └── ...
├── services/
│   ├── comparison_service.py       # Comparison orchestration
│   └── appian_analyzer/            # Appian analysis engine
│       ├── analyzer.py             # Blueprint generation
│       ├── enhanced_version_comparator.py
│       ├── web_compatibility_layer.py
│       └── models.py
├── templates/                      # Jinja2 templates
│   └── analyzer/
│       ├── home.html
│       ├── request_details.html
│       └── object_details.html
├── models.py                       # Database models
└── applicationArtifacts/           # Test data
    └── Testing Files/
        ├── SourceSelectionv2.4.0.zip
        └── SourceSelectionv2.6.0.zip
```

## How the Application Works

### Appian Comparison Workflow

1. **Upload Phase**
   - User uploads two Appian application ZIP files (old and new versions)
   - Files are temporarily saved to `uploads/` directory

2. **Blueprint Generation Phase**
   - Each ZIP is analyzed by `AppianAnalyzer`
   - Extracts all objects: Sites, Record Types, Process Models, Interfaces, Expression Rules, etc.
   - Builds an `object_lookup` table mapping UUIDs to objects
   - Resolves all UUID references to actual object names
   - Formats SAIL code for readability
   - Generates metadata and complexity assessment

3. **Comparison Phase**
   - Uses `EnhancedComparisonService` with dual-layer comparison:
     - **Layer 1:** Version History Comparison (checks version UUIDs)
     - **Layer 2:** Content Diff Hash Comparison (detects actual changes)
   - Identifies: ADDED, REMOVED, MODIFIED, NOT_CHANGED objects
   - Detects specific changes: SAIL code, business logic, fields, etc.

4. **Storage Phase**
   - Results stored in `ComparisonRequest` database table
   - Includes: blueprints, comparison results, processing time, status

5. **Display Phase**
   - Summary view: Shows all changes by category
   - Detail view: Shows individual object changes with SAIL code diffs

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

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_analyzer.py

# Run with verbose output
pytest -v
```

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

### ComparisonRequest Table
- `id` - Primary key
- `reference_id` - Human-readable ID (e.g., "CMP_007")
- `old_app_name` - Name of old version
- `new_app_name` - Name of new version
- `status` - processing/completed/error
- `old_app_blueprint` - JSON string of old version blueprint
- `new_app_blueprint` - JSON string of new version blueprint
- `comparison_results` - JSON string with all changes
- `total_time` - Processing time in seconds
- `created_at` - Timestamp
- `updated_at` - Timestamp

## Important Code Patterns

### Adding Debug Logging

```python
# In comparison code
print(f"🔍 DEBUG: {variable_name}")
print(f"   Detail: {value}")
```

### Accessing Comparison Data

```python
# In controller
comparison_data = json.loads(comparison_request.comparison_results)

# Structure:
{
    "comparison_summary": {...},
    "changes_by_category": {
        "interfaces": {
            "added": 22,
            "modified": 56,
            "removed": 0,
            "details": [...]
        }
    },
    "detailed_changes": [...]
}
```

### SAIL Code in Change Objects

```python
# Required fields for SAIL code diff display:
change_obj = {
    "uuid": "...",
    "name": "...",
    "type": "Interface",
    "change_type": "MODIFIED",
    "sail_code_before": "...",  # Required for diff
    "sail_code_after": "..."    # Required for diff
}
```

## Quick Reference Commands

```bash
# Start app
python app.py

# Run tests
pytest

# Check syntax
python -m py_compile <file.py>

# Database shell
python
>>> from app import create_app
>>> from models import db
>>> app = create_app()
>>> with app.app_context():
...     # database operations

# View logs
tail -f logs/*.log  # if logging to file
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


## Recent Enhancements (2025-11-21)

### Logging System
A comprehensive logging system has been implemented for the Appian analyzer:

**Features:**
- Request-specific tracking with automatic request ID tagging (e.g., [CMP_013])
- Stage tracking (Upload, Analysis, Comparison)
- Metrics logging (total_changes, impact_level, object counts)
- Completion logging with elapsed time
- Dual output: detailed file logs (DEBUG) + console logs (INFO)
- Automatic file rotation (10MB per file, 5 backups)

**Location:** `logs/appian_analyzer.log`

**Usage:**
```python
from services.appian_analyzer.logger import create_request_logger, get_logger

# For request-specific logging
logger = create_request_logger(request.reference_id)
logger.info("Starting comparison")
logger.log_stage("Analysis", {"objects": 1000})
logger.log_metrics({"total_changes": 50, "impact_level": "MEDIUM"})
logger.log_completion(status='success', total_changes=50)

# For general logging
logger = get_logger()
logger.info("General message")
```

### SAIL Code Formatter
The SAIL formatter now properly formats code in comparison results:

**Features:**
- Replaces UUID references with readable object names
- Converts internal Appian functions to public names
- Cleans up escape sequences and formatting

**Examples:**
- `#"SYSTEM_SYSRULES_headerContentLayout"` → `a!headerContentLayout`
- `#"_a-uuid"` → `rule!ObjectName`
- `cons!uuid` → `cons!ConstantName`

**Location:** `services/appian_analyzer/sail_formatter.py`

### UI/UX Improvements

#### Application Comparison Page
- **Pagination:** 10 rows per page with navigation
- **Horizontal Layout:** Applications displayed side-by-side (Old → New)
- **Pagination Info:** Shows "Showing X to Y of Z entries"

#### Comparison Results Page
- **Grid Layout:** Table format instead of cards
- **Default Display:** All data shown by default
- **Filters:** Additional filtering on top of displayed data
- **Pagination:** 10 rows per page
- **Improved Colors:** Better text visibility and contrast

#### Object Details Page
- **Clean Header:** No duplicate object names
- **Type Display:** Shows "ObjectName (Type)" format
- **Removed Duplicates:** Change type badge only in Basic Information section
- **Better Colors:** Improved text visibility throughout

### Key Files

**Logging:**
- `services/appian_analyzer/logger.py` - Logger implementation
- `LOGGING_IMPLEMENTATION_GUIDE.md` - Usage guide

**SAIL Formatting:**
- `services/appian_analyzer/sail_formatter.py` - Formatter implementation
- `services/appian_analyzer/analyzer.py` - Integration point

**UI Templates:**
- `templates/analyzer/home.html` - Application comparison page
- `templates/analyzer/request_details.html` - Comparison results page
- `templates/analyzer/object_details.html` - Object details page

### Testing Workflow

1. **Check for existing instances:**
   ```bash
   listProcesses
   lsof -i :5002
   ```

2. **Start fresh instance:**
   ```bash
   controlBashProcess(action="stop", processId=<id>)
   controlBashProcess(action="start", command="python3.13 app.py")
   ```

3. **Upload test files:**
   - Navigate to `http://localhost:5002/analyzer`
   - Upload `applicationArtifacts/Testing Files/SourceSelectionv2.4.0.zip`
   - Upload `applicationArtifacts/Testing Files/SourceSelectionv2.6.0.zip`
   - Click "Start Comparison"

4. **Verify results:**
   - Check pagination on home page
   - View comparison results (grid layout)
   - Check object details (SAIL code formatting)
   - Review logs at `logs/appian_analyzer.log`

### Performance Notes

**Typical Processing Times:**
- Small applications (< 500 objects): 2-3 seconds
- Medium applications (500-1500 objects): 4-5 seconds
- Large applications (1500+ objects): 6-8 seconds

**Database:**
- SQLite database at `instance/nexusgen.db`
- Stores comparison requests, blueprints, and results
- No manual cleanup needed (managed by application)

### Troubleshooting

**Issue: SAIL code shows UUIDs instead of names**
- Solution: This was fixed on 2025-11-21. Ensure you're using CMP_014 or later requests.

**Issue: Pagination not working**
- Solution: Clear browser cache and reload page

**Issue: Colors not visible**
- Solution: Check if using dark theme. All colors have been optimized for dark background.

**Issue: Multiple app instances**
- Solution: Always check `listProcesses` and `lsof -i :5002` before starting new instance
