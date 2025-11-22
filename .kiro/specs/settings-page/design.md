# Design Document

## Overview

The Settings page is a new administrative interface for the NexusGen application that consolidates system-wide configuration options. It provides centralized access to theme management, database cleanup operations, and backup functionality. The design follows the existing Flask blueprint architecture and maintains visual consistency with the current NexusGen interface.

The Settings page will be accessible from the sidebar navigation and will replace the floating theme toggle button that currently appears on all pages. This centralization improves user experience by providing a single, predictable location for administrative tasks.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Client)                      │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Settings  │  │    Theme     │  │   Local         │ │
│  │  Page UI   │◄─┤    Toggle    │◄─┤   Storage       │ │
│  └─────┬──────┘  └──────────────┘  └─────────────────┘ │
└────────┼────────────────────────────────────────────────┘
         │ HTTP Requests
         ▼
┌─────────────────────────────────────────────────────────┐
│              Flask Application (Server)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │         settings_controller.py                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │  │
│  │  │ Settings │  │  Cleanup │  │    Backup      │ │  │
│  │  │  Route   │  │  Route   │  │    Route       │ │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬───────────┘ │  │
│  └───────┼─────────────┼─────────────┼──────────────┘  │
│          │             │             │                  │
│          │             ▼             ▼                  │
│          │    ┌────────────────────────────────┐       │
│          │    │   settings_service.py          │       │
│          │    │  ┌──────────┐  ┌────────────┐ │       │
│          │    │  │ Cleanup  │  │   Backup   │ │       │
│          │    │  │ Service  │  │  Service   │ │       │
│          │    │  └────┬─────┘  └────┬───────┘ │       │
│          │    └───────┼─────────────┼─────────┘       │
│          │            │             │                  │
│          ▼            ▼             ▼                  │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Database Layer                       │ │
│  │  ┌──────────────────────────────────────────┐   │ │
│  │  │  SQLAlchemy ORM (models.py)              │   │ │
│  │  │  - MergeSession                          │   │ │
│  │  │  - ChangeReview                          │   │ │
│  │  │  - ComparisonRequest                     │   │ │
│  │  │  - Request                               │   │ │
│  │  └──────────────────┬───────────────────────┘   │ │
│  └─────────────────────┼───────────────────────────┘ │
└────────────────────────┼─────────────────────────────┘
                         ▼
              ┌──────────────────────┐
              │  SQLite Database     │
              │  instance/docflow.db │
              └──────────────────────┘
```

### Component Interaction Flow

1. **Theme Toggle Flow:**
   - User clicks theme toggle → JavaScript updates DOM attribute → localStorage saves preference → CSS variables update appearance

2. **Data Cleanup Flow:**
   - User clicks cleanup button → Confirmation dialog → POST to `/settings/cleanup` → Service deletes records → Response with count → UI notification

3. **Backup Flow:**
   - User clicks backup button → POST to `/settings/backup` → Service generates SQL export → File download triggered → UI notification

## Components and Interfaces

### 1. Settings Controller (`controllers/settings_controller.py`)

**Purpose:** Handle HTTP requests for the Settings page and coordinate with the settings service.

**Routes:**
- `GET /settings` - Display the settings page
- `POST /settings/cleanup` - Execute database cleanup
- `POST /settings/backup` - Generate and download database backup
- `POST /settings/restore` - Restore database from uploaded SQL file

**Interface:**
```python
from flask import Blueprint, render_template, jsonify, send_file, request
from services.settings_service import SettingsService

settings_bp = Blueprint('settings', __name__)
settings_service = SettingsService()

@settings_bp.route('/settings')
def settings_page() -> str:
    """Render the settings page"""
    pass

@settings_bp.route('/settings/cleanup', methods=['POST'])
def cleanup_database() -> dict:
    """Execute database cleanup and return results"""
    pass

@settings_bp.route('/settings/backup', methods=['POST'])
def backup_database() -> Response:
    """Generate SQL backup and trigger download"""
    pass

@settings_bp.route('/settings/restore', methods=['POST'])
def restore_database() -> dict:
    """Restore database from uploaded SQL file"""
    pass
```

### 2. Settings Service (`services/settings_service.py`)

**Purpose:** Implement business logic for cleanup and backup operations.

**Interface:**
```python
class SettingsService:
    def cleanup_database(self) -> dict:
        """
        Clean up all database tables and uploaded files.
        
        Returns:
            dict: {
                'success': bool,
                'deleted_records': int,
                'deleted_files': int,
                'details': dict
            }
        """
        pass
    
    def backup_database(self, output_path: str) -> str:
        """
        Generate SQL export of the database.
        
        Args:
            output_path: Path where backup file should be saved
            
        Returns:
            str: Path to the generated backup file
            
        Raises:
            Exception: If backup generation fails
        """
        pass
    
    def restore_database(self, sql_file_path: str) -> dict:
        """
        Restore database from SQL backup file.
        
        Args:
            sql_file_path: Path to the SQL backup file
            
        Returns:
            dict: {
                'success': bool,
                'restored_records': int,
                'details': dict
            }
            
        Raises:
            Exception: If restore fails or SQL is invalid
        """
        pass
    
    def _delete_table_records(self, model_class) -> int:
        """Delete all records from a table"""
        pass
    
    def _delete_uploaded_files(self) -> int:
        """Delete uploaded files except .gitkeep"""
        pass
    
    def _generate_sql_export(self, db_path: str, output_path: str) -> None:
        """Generate SQL dump using sqlite3 command"""
        pass
    
    def _validate_sql_file(self, file_path: str) -> bool:
        """Validate SQL file format and content"""
        pass
    
    def _execute_sql_file(self, db_path: str, sql_file_path: str) -> None:
        """Execute SQL file against database"""
        pass
```

### 3. Settings Template (`templates/settings/index.html`)

**Purpose:** Render the settings page UI with theme toggle, cleanup, and backup sections.

**Structure:**
```html
{% extends "base.html" %}

{% block content %}
<div class="settings-container">
    <!-- Theme Section -->
    <div class="settings-section">
        <div class="section-header">
            <i class="fas fa-palette"></i>
            <h3>Theme</h3>
        </div>
        <div class="section-content">
            <div class="theme-toggle-container">
                <label>Appearance</label>
                <button id="themeToggleBtn" class="theme-switch">
                    <span class="theme-option" data-theme="dark">Dark</span>
                    <span class="theme-option" data-theme="light">Light</span>
                </button>
            </div>
        </div>
    </div>
    
    <!-- Data Cleanup Section -->
    <div class="settings-section">
        <div class="section-header">
            <i class="fas fa-trash-alt"></i>
            <h3>Data Cleanup</h3>
        </div>
        <div class="section-content">
            <p>Remove all data from the database and uploaded files.</p>
            <button id="cleanupBtn" class="btn btn-danger">
                <i class="fas fa-exclamation-triangle"></i>
                Clean Up Database
            </button>
        </div>
    </div>
    
    <!-- Backup Section -->
    <div class="settings-section">
        <div class="section-header">
            <i class="fas fa-download"></i>
            <h3>Data Backup</h3>
        </div>
        <div class="section-content">
            <p>Download a SQL backup of the database.</p>
            <button id="backupBtn" class="btn btn-primary">
                <i class="fas fa-database"></i>
                Download Backup
            </button>
        </div>
    </div>
    
    <!-- Restore Section -->
    <div class="settings-section">
        <div class="section-header">
            <i class="fas fa-upload"></i>
            <h3>Data Restore</h3>
        </div>
        <div class="section-content">
            <p>Restore database from a SQL backup file.</p>
            <input type="file" id="restoreFile" accept=".sql" class="form-control mb-2">
            <button id="restoreBtn" class="btn btn-warning">
                <i class="fas fa-undo"></i>
                Restore Database
            </button>
        </div>
    </div>
</div>
{% endblock %}
```

### 4. Settings JavaScript (`static/js/settings.js`)

**Purpose:** Handle client-side interactions for theme toggle, cleanup confirmation, and backup download.

**Interface:**
```javascript
const SettingsPage = {
    init: function() {
        this.initThemeToggle();
        this.initCleanupButton();
        this.initBackupButton();
        this.initRestoreButton();
    },
    
    initThemeToggle: function() {
        // Handle theme switching with visual feedback
    },
    
    initCleanupButton: function() {
        // Show confirmation dialog and execute cleanup
    },
    
    initBackupButton: function() {
        // Trigger backup download
    },
    
    initRestoreButton: function() {
        // Validate file selection and execute restore
    },
    
    showConfirmDialog: function(message, onConfirm) {
        // Display Bootstrap modal for confirmation
    },
    
    validateSqlFile: function(file) {
        // Validate file extension and basic format
    }
};
```

## Data Models

### Existing Models (No Changes Required)

The Settings page uses existing database models without modification:

- **Request**: Stores breakdown, verify, and create action requests
- **ComparisonRequest**: Stores Appian application comparison data
- **MergeSession**: Stores three-way merge session data
- **ChangeReview**: Stores user review actions for merge changes

### Backup File Format

**SQL Export Structure:**
```sql
-- NexusGen Database Backup
-- Generated: 2024-11-22 14:30:00
-- Database: docflow.db

BEGIN TRANSACTION;

-- Table: requests
CREATE TABLE IF NOT EXISTS requests (...);
INSERT INTO requests VALUES (...);

-- Table: comparison_requests
CREATE TABLE IF NOT EXISTS comparison_requests (...);
INSERT INTO comparison_requests VALUES (...);

-- Table: merge_sessions
CREATE TABLE IF NOT EXISTS merge_sessions (...);
INSERT INTO merge_sessions VALUES (...);

-- Table: change_reviews
CREATE TABLE IF NOT EXISTS change_reviews (...);
INSERT INTO change_reviews VALUES (...);

COMMIT;
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After reviewing all testable criteria from the prework, several properties can be consolidated:

- **Theme persistence properties (2.3, 2.5)** can be combined into a single round-trip property
- **Cleanup table deletion (4.3, 4.4)** can be combined since 4.4 is more specific than 4.3
- **Backup success feedback (5.5, 5.6)** can be combined as they both verify successful completion
- **UI element existence checks (1.1, 1.3, 1.4, 2.1, 4.1, 5.1, 6.4, 6.5)** are examples, not properties requiring multiple test cases

The remaining properties provide unique validation value and should be retained.

### Correctness Properties

**Property 1: Settings navigation works from any page**
*For any* page in the application, clicking the Settings menu item should navigate to the /settings URL
**Validates: Requirements 1.2**

**Property 2: Theme toggle switches between states**
*For any* current theme state (dark or light), clicking the theme toggle should switch to the opposite theme
**Validates: Requirements 2.2**

**Property 3: Theme preference round-trip**
*For any* theme selection (dark or light), saving to localStorage and then reading back should return the same theme value
**Validates: Requirements 2.3, 2.5**

**Property 4: Theme changes apply without reload**
*For any* theme change, the document's data-theme attribute should update immediately without a page reload event
**Validates: Requirements 2.4**

**Property 5: Theme toggle absent from non-settings pages**
*For any* page except /settings, the rendered HTML should not contain the floating theme toggle button element
**Validates: Requirements 3.1**

**Property 6: Theme persists across navigation**
*For any* theme set in Settings, navigating to any other page should maintain that theme setting
**Validates: Requirements 3.3**

**Property 7: Cleanup requires confirmation**
*For any* click on the cleanup button, a confirmation dialog should be displayed before any database operations occur
**Validates: Requirements 4.2**

**Property 8: Cleanup empties all tables**
*For any* database state, executing cleanup should result in zero records in MergeSession, ChangeReview, ComparisonRequest, and Request tables
**Validates: Requirements 4.3, 4.4**

**Property 9: Cleanup preserves gitkeep files**
*For any* set of files in upload directories, cleanup should delete all files except those named .gitkeep
**Validates: Requirements 4.5**

**Property 10: Cleanup notification matches deleted count**
*For any* cleanup operation, the success notification should display the actual count of deleted records
**Validates: Requirements 4.6**

**Property 11: Cleanup rollback on error**
*For any* error during cleanup, the database should be rolled back to its pre-cleanup state
**Validates: Requirements 4.7**

**Property 12: Cleanup cancellation preserves state**
*For any* database state, canceling the cleanup confirmation should leave all records and files unchanged
**Validates: Requirements 4.8**

**Property 13: Backup generates SQL file**
*For any* database state, clicking the backup button should create a .sql file
**Validates: Requirements 5.2**

**Property 14: Backup includes all data**
*For any* database state with N records across all tables, the generated SQL backup should contain N INSERT statements
**Validates: Requirements 5.3**

**Property 15: Backup filename format**
*For any* backup operation, the generated filename should match the pattern nexusgen_backup_YYYYMMDD_HHMMSS.sql
**Validates: Requirements 5.4**

**Property 16: Backup triggers download and notification**
*For any* successful backup operation, both a file download and a success notification should occur
**Validates: Requirements 5.5, 5.6**

**Property 17: Backup error notification**
*For any* backup operation that fails, an error notification with details should be displayed
**Validates: Requirements 5.7**

**Property 18: Backup round-trip**
*For any* database state, creating a backup and then importing it into a fresh database should produce an equivalent state
**Validates: Requirements 5.8**

**Property 19: Restore requires confirmation**
*For any* click on the restore button with a valid SQL file selected, a confirmation dialog should be displayed before any database operations occur
**Validates: Requirements 6.3**

**Property 20: Restore clears then imports**
*For any* database state and valid SQL backup file, executing restore should first delete all existing records then import the backup data
**Validates: Requirements 6.5**

**Property 21: Restore notification matches imported count**
*For any* restore operation, the success notification should display the actual count of restored records
**Validates: Requirements 6.6**

**Property 22: Restore rollback on error**
*For any* error during restore, the database should be rolled back to its pre-restore state
**Validates: Requirements 6.7**

**Property 23: Restore cancellation preserves state**
*For any* database state, canceling the restore confirmation should leave all records unchanged
**Validates: Requirements 6.8**

**Property 24: Restore rejects invalid SQL**
*For any* file that does not contain valid SQL statements, the restore operation should reject the file and display an error
**Validates: Requirements 6.9**

**Property 25: Restore file extension validation**
*For any* file selected for restore, the system should only accept files with .sql extension
**Validates: Requirements 6.2**

## Error Handling

### Client-Side Error Handling

**Theme Toggle Errors:**
- If localStorage is unavailable (private browsing), fall back to session-only theme storage
- If theme value is corrupted, default to 'dark' theme
- Log errors to console for debugging

**Network Errors:**
- Display user-friendly error notifications for failed API calls
- Implement retry logic with exponential backoff for transient failures
- Provide clear error messages indicating whether the issue is client or server-side

**Validation Errors:**
- Prevent cleanup/backup button clicks while operations are in progress
- Disable buttons and show loading state during operations
- Re-enable buttons after operation completes or fails

### Server-Side Error Handling

**Database Cleanup Errors:**
```python
try:
    # Delete records
    db.session.commit()
except Exception as e:
    db.session.rollback()
    logger.error(f"Cleanup failed: {str(e)}")
    return jsonify({'success': False, 'error': str(e)}), 500
```

**Backup Generation Errors:**
```python
try:
    # Generate SQL export
    subprocess.run(['sqlite3', db_path, '.dump'], 
                   stdout=output_file, check=True)
except subprocess.CalledProcessError as e:
    logger.error(f"Backup failed: {str(e)}")
    return jsonify({'success': False, 'error': 'Backup generation failed'}), 500
except FileNotFoundError:
    logger.error("sqlite3 command not found")
    return jsonify({'success': False, 'error': 'SQLite tools not available'}), 500
```

**File System Errors:**
- Handle permission errors when deleting files
- Handle disk space errors when creating backups
- Clean up partial files on failure

### Error Response Format

All API endpoints return consistent error responses:
```json
{
    "success": false,
    "error": "Human-readable error message",
    "details": {
        "error_code": "CLEANUP_FAILED",
        "timestamp": "2024-11-22T14:30:00Z"
    }
}
```

## Testing Strategy

### Unit Testing

Unit tests will verify specific functionality and edge cases:

**Theme Management Tests:**
- Test theme toggle switches between dark and light
- Test theme persistence to localStorage
- Test theme loading on page initialization
- Test fallback behavior when localStorage is unavailable

**Cleanup Service Tests:**
- Test cleanup deletes all records from each table
- Test cleanup deletes uploaded files except .gitkeep
- Test cleanup rollback on database error
- Test cleanup with empty database
- Test cleanup with large number of records

**Backup Service Tests:**
- Test backup generates valid SQL file
- Test backup filename format with timestamp
- Test backup includes all table structures
- Test backup includes all data records
- Test backup handles empty database
- Test backup error handling for missing sqlite3 command

**Restore Service Tests:**
- Test restore imports data from valid SQL file
- Test restore clears existing data before import
- Test restore validates SQL file extension
- Test restore rejects invalid SQL syntax
- Test restore rollback on error
- Test restore with empty SQL file
- Test restore with large SQL file

**Controller Tests:**
- Test settings page route returns 200 status
- Test cleanup endpoint requires POST method
- Test backup endpoint requires POST method
- Test restore endpoint requires POST method
- Test cleanup endpoint returns correct JSON structure
- Test backup endpoint returns file download
- Test restore endpoint validates file upload
- Test restore endpoint returns correct JSON structure

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using the Hypothesis library for Python:

**Configuration:**
- Minimum 100 iterations per property test
- Use Hypothesis strategies to generate random test data
- Each property test tagged with format: `**Feature: settings-page, Property {number}: {property_text}**`

**Test Data Generators:**
```python
from hypothesis import strategies as st

# Generate random database states
@st.composite
def database_state(draw):
    return {
        'requests': draw(st.lists(st.builds(Request))),
        'comparisons': draw(st.lists(st.builds(ComparisonRequest))),
        'merge_sessions': draw(st.lists(st.builds(MergeSession))),
        'change_reviews': draw(st.lists(st.builds(ChangeReview)))
    }

# Generate random file sets
@st.composite
def file_set(draw):
    num_files = draw(st.integers(min_value=0, max_value=50))
    return [f"file_{i}.zip" for i in range(num_files)]

# Generate random themes
theme_strategy = st.sampled_from(['dark', 'light'])
```

**Property Test Examples:**

*Property 8: Cleanup empties all tables*
```python
@given(database_state())
def test_cleanup_empties_tables(db_state):
    # Setup: Populate database with random data
    # Execute: Run cleanup
    # Assert: All tables have zero records
```

*Property 18: Backup round-trip*
```python
@given(database_state())
def test_backup_roundtrip(db_state):
    # Setup: Create database with random data
    # Execute: Backup then restore
    # Assert: Restored database equals original
```

*Property 20: Restore clears then imports*
```python
@given(database_state(), database_state())
def test_restore_clears_then_imports(initial_state, backup_state):
    # Setup: Create database with initial_state, backup from backup_state
    # Execute: Restore backup
    # Assert: Database matches backup_state, not initial_state
```

*Property 24: Restore rejects invalid SQL*
```python
@given(st.text())
def test_restore_rejects_invalid_sql(invalid_sql):
    # Setup: Create file with invalid SQL
    # Execute: Attempt restore
    # Assert: Error raised, database unchanged
```

### Integration Testing

Integration tests will verify end-to-end workflows:

**Settings Page Integration:**
- Test full cleanup workflow: load page → click cleanup → confirm → verify deletion
- Test full backup workflow: load page → click backup → verify file download
- Test full restore workflow: load page → select file → click restore → confirm → verify import
- Test backup-restore round-trip: backup → cleanup → restore → verify data matches
- Test theme change workflow: change theme → navigate to other page → verify theme persists

**Browser Testing:**
- Use Selenium or Playwright for automated browser testing
- Test theme toggle visual changes
- Test confirmation dialogs
- Test file downloads
- Test across different browsers (Chrome, Firefox, Safari)

### Test Organization

```
tests/
├── unit/
│   ├── test_settings_service.py
│   ├── test_settings_controller.py
│   └── test_theme_management.py
├── property/
│   ├── test_cleanup_properties.py
│   ├── test_backup_properties.py
│   ├── test_restore_properties.py
│   └── test_theme_properties.py
└── integration/
    ├── test_settings_page_integration.py
    └── test_settings_workflows.py
```

## Implementation Notes

### Theme Toggle Migration

**Current Implementation:**
- Floating button in `base.html` template
- JavaScript in `main.js` handles toggle logic
- Theme stored in localStorage with key 'theme'

**New Implementation:**
- Remove floating button from `base.html`
- Move theme toggle to Settings page only
- Keep existing JavaScript logic in `main.js` for theme application
- Add new JavaScript in `settings.js` for Settings page toggle UI

**Migration Steps:**
1. Remove `<button class="theme-toggle">` from `base.html`
2. Keep theme initialization code in `main.js` (loads saved theme on page load)
3. Create new toggle UI in Settings page template
4. Add Settings-specific toggle handler in `settings.js`

### Database Backup Implementation

**SQLite Dump Command:**
```bash
sqlite3 instance/docflow.db .dump > backup.sql
```

**Python Implementation:**
```python
import subprocess
from datetime import datetime

def backup_database(self, output_path: str) -> str:
    db_path = 'instance/docflow.db'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'nexusgen_backup_{timestamp}.sql'
    full_path = os.path.join(output_path, filename)
    
    with open(full_path, 'w') as f:
        subprocess.run(
            ['sqlite3', db_path, '.dump'],
            stdout=f,
            check=True,
            text=True
        )
    
    return full_path
```

### Cleanup Implementation

**Reuse Existing Logic:**
The existing `cleanup_database.py` script contains the cleanup logic. The service should:
1. Import the cleanup functions from the script
2. Wrap them in a service method
3. Return structured results instead of printing to console
4. Handle errors and rollback appropriately

**Service Wrapper:**
```python
def cleanup_database(self) -> dict:
    deleted_counts = {
        'merge_sessions': 0,
        'change_reviews': 0,
        'comparison_requests': 0,
        'requests': 0,
        'files': 0
    }
    
    try:
        deleted_counts['change_reviews'] = ChangeReview.query.delete()
        deleted_counts['merge_sessions'] = MergeSession.query.delete()
        deleted_counts['comparison_requests'] = ComparisonRequest.query.delete()
        deleted_counts['requests'] = Request.query.delete()
        
        db.session.commit()
        
        deleted_counts['files'] = self._delete_uploaded_files()
        
        total = sum(deleted_counts.values())
        
        return {
            'success': True,
            'deleted_records': total,
            'details': deleted_counts
        }
    except Exception as e:
        db.session.rollback()
        raise
```

### Database Restore Implementation

**SQLite Import Command:**
```bash
sqlite3 instance/docflow.db < backup.sql
```

**Python Implementation:**
```python
import subprocess
import os

def restore_database(self, sql_file_path: str) -> dict:
    db_path = 'instance/docflow.db'
    
    # Validate file
    if not sql_file_path.endswith('.sql'):
        raise ValueError("Invalid file format. Only .sql files are accepted.")
    
    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")
    
    # Validate SQL content
    if not self._validate_sql_file(sql_file_path):
        raise ValueError("Invalid SQL file content")
    
    try:
        # Clear existing data
        cleanup_result = self.cleanup_database()
        
        # Import SQL file
        with open(sql_file_path, 'r') as f:
            subprocess.run(
                ['sqlite3', db_path],
                stdin=f,
                check=True,
                text=True,
                capture_output=True
            )
        
        # Count restored records
        restored_counts = {
            'merge_sessions': MergeSession.query.count(),
            'change_reviews': ChangeReview.query.count(),
            'comparison_requests': ComparisonRequest.query.count(),
            'requests': Request.query.count()
        }
        
        total = sum(restored_counts.values())
        
        return {
            'success': True,
            'restored_records': total,
            'details': restored_counts
        }
    except Exception as e:
        # Rollback handled by SQLAlchemy
        raise

def _validate_sql_file(self, file_path: str) -> bool:
    """Basic validation of SQL file content"""
    try:
        with open(file_path, 'r') as f:
            content = f.read(1000)  # Read first 1000 chars
            # Check for SQL keywords
            sql_keywords = ['CREATE', 'INSERT', 'TABLE', 'BEGIN']
            return any(keyword in content.upper() for keyword in sql_keywords)
    except Exception:
        return False
```

### Security Considerations

**Cleanup Operation:**
- Require confirmation dialog to prevent accidental deletion
- Consider adding authentication/authorization for production use
- Log all cleanup operations with timestamp and user (if auth is added)

**Backup Operation:**
- Ensure backup files are not accessible via web server
- Store backups in secure location outside web root
- Consider encrypting backups if they contain sensitive data
- Implement rate limiting to prevent abuse

**Restore Operation:**
- Validate SQL file extension and content before execution
- Sanitize file paths to prevent directory traversal
- Limit file size to prevent DoS attacks (max 100MB)
- Require confirmation dialog to prevent accidental data replacement
- Log all restore operations with timestamp and user
- Consider adding checksum validation for backup files
- Reject SQL files with DROP DATABASE or other dangerous commands

**File Downloads:**
- Validate file paths to prevent directory traversal attacks
- Use `send_file` with `as_attachment=True` to force download
- Clean up temporary files after download

**File Uploads:**
- Validate file extension (.sql only)
- Limit file size (max 100MB)
- Store uploaded files in secure temporary location
- Clean up uploaded files after processing
- Scan for malicious SQL injection patterns

### Performance Considerations

**Cleanup Performance:**
- For large databases (>10,000 records), cleanup may take several seconds
- Show loading indicator during operation
- Consider adding progress updates for very large datasets
- Use database transactions to ensure atomicity

**Backup Performance:**
- Backup time scales with database size
- For databases >100MB, consider streaming the backup
- Show progress indicator during backup generation
- Consider implementing background job for large backups

**Restore Performance:**
- Restore time scales with SQL file size
- For files >50MB, show progress indicator
- Consider implementing background job for large restores
- Validate file size before upload (reject files >100MB)
- Stream large SQL files instead of loading into memory

**UI Responsiveness:**
- Use AJAX for cleanup, backup, and restore operations to avoid page reload
- Disable buttons during operations to prevent duplicate requests
- Show loading spinners and progress indicators
- Implement timeout handling for long-running operations
- Provide real-time feedback during restore process

## Dependencies

### Python Dependencies
- Flask (existing)
- SQLAlchemy (existing)
- subprocess (standard library)
- datetime (standard library)
- os (standard library)
- pathlib (standard library)

### JavaScript Dependencies
- Bootstrap 5 (existing) - for modals and styling
- Font Awesome (existing) - for icons
- No additional libraries required

### System Dependencies
- sqlite3 command-line tool (for backup generation)
- Should be available on most systems with SQLite installed

### Testing Dependencies
- pytest (existing)
- hypothesis (for property-based testing)
- pytest-flask (for Flask testing)
- selenium or playwright (for browser testing)

## Deployment Considerations

### Configuration
- No new environment variables required
- Backup directory should be configurable via Config class
- Default backup location: `outputs/backups/`

### Database Migrations
- No database schema changes required
- No migrations needed

### File System Requirements
- Write permissions for backup directory
- Write permissions for upload directories (for cleanup)
- Sufficient disk space for backup files

### Monitoring
- Log all cleanup operations
- Log all backup operations
- Monitor backup file sizes
- Alert on cleanup/backup failures

### Rollback Plan
If issues arise after deployment:
1. Theme toggle can be re-added to base.html
2. Settings page can be disabled by removing route registration
3. No database changes to rollback
4. No data loss risk (cleanup requires confirmation)
