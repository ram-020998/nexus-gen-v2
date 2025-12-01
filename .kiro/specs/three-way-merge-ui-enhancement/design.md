# Design Document

## Overview

This document describes the design for enhancing the three-way merge application UI to provide a comprehensive, user-friendly interface for reviewing and managing merge sessions. The design focuses on creating detailed change navigation, progress tracking, session management, and reporting capabilities that match the functionality of the legacy version while maintaining the clean architecture principles of the rebuild.

## Architecture

The enhancement follows the existing clean architecture pattern with clear separation between:

1. **Controllers**: Handle HTTP requests/responses and route to services
2. **Services**: Contain business logic and orchestrate operations
3. **Repositories**: Handle data access and database operations
4. **Models**: Define database schema and relationships
5. **Templates**: Render HTML views with Jinja2

### New Components

1. **Change Navigation Service**: Manages sequential navigation through changes
2. **Change Action Service**: Handles user actions (mark reviewed, skip, save notes)
3. **Report Generation Service**: Creates downloadable merge reports
4. **Session Statistics Service**: Calculates and caches session metrics

### Enhanced Components

1. **Merge Assistant Controller**: Add new routes for change detail, actions, and reports
2. **Change Model**: Add fields for status, notes, and timestamps
3. **Templates**: Create new templates and enhance existing ones

## Components and Interfaces

### 1. Change Model Enhancement

```python
class Change(db.Model):
    """Working set of classified changes for user review"""
    __tablename__ = 'changes'

    # Existing fields
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'))
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id'))
    classification = db.Column(db.String(50), nullable=False)
    vendor_change_type = db.Column(db.String(20))
    customer_change_type = db.Column(db.String(20))
    display_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NEW FIELDS
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, skipped
    notes = db.Column(db.Text)  # User notes about the change
    reviewed_at = db.Column(db.DateTime)  # When marked as reviewed
    reviewed_by = db.Column(db.String(255))  # Who reviewed (future: user auth)
```

### 2. MergeSession Model Enhancement

```python
class MergeSession(db.Model):
    """Merge sessions for three-way merge analysis"""
    __tablename__ = 'merge_sessions'

    # Existing fields
    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default='processing')
    total_changes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NEW FIELDS
    reviewed_count = db.Column(db.Integer, default=0)  # Count of reviewed changes
    skipped_count = db.Column(db.Integer, default=0)  # Count of skipped changes
    estimated_complexity = db.Column(db.String(20))  # Low, Medium, High
    estimated_time_hours = db.Column(db.Float)  # Estimated review time
```

### 3. Change Navigation Service

```python
class ChangeNavigationService(BaseService):
    """Service for navigating through changes in a session"""
    
    def get_change_detail(
        self,
        reference_id: str,
        change_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific change.
        
        Returns:
            Dict containing:
            - change: Change information
            - object: Object details
            - session: Session information
            - navigation: Previous/next change IDs
            - position: Current position (e.g., "1 of 6")
            - progress_percent: Percentage complete
            - versions: Object versions from all three packages
        """
        pass
    
    def get_next_change(
        self,
        reference_id: str,
        current_change_id: int
    ) -> Optional[int]:
        """Get ID of next change in sequence"""
        pass
    
    def get_previous_change(
        self,
        reference_id: str,
        current_change_id: int
    ) -> Optional[int]:
        """Get ID of previous change in sequence"""
        pass
    
    def get_change_position(
        self,
        reference_id: str,
        change_id: int
    ) -> Tuple[int, int]:
        """
        Get position of change in workflow.
        
        Returns:
            Tuple of (current_position, total_changes)
            e.g., (1, 6) means "Change 1 of 6"
        """
        pass
```

### 4. Change Action Service

```python
class ChangeActionService(BaseService):
    """Service for handling user actions on changes"""
    
    def mark_as_reviewed(
        self,
        reference_id: str,
        change_id: int,
        user_id: Optional[str] = None
    ) -> Change:
        """
        Mark a change as reviewed.
        
        Updates:
        - change.status = 'reviewed'
        - change.reviewed_at = now
        - change.reviewed_by = user_id
        - session.reviewed_count += 1
        """
        pass
    
    def skip_change(
        self,
        reference_id: str,
        change_id: int
    ) -> Change:
        """
        Mark a change as skipped.
        
        Updates:
        - change.status = 'skipped'
        - session.skipped_count += 1
        """
        pass
    
    def save_notes(
        self,
        reference_id: str,
        change_id: int,
        notes: str
    ) -> Change:
        """
        Save user notes for a change.
        
        Updates:
        - change.notes = notes
        """
        pass
    
    def undo_action(
        self,
        reference_id: str,
        change_id: int
    ) -> Change:
        """
        Undo review/skip action.
        
        Updates:
        - change.status = 'pending'
        - change.reviewed_at = None
        - Decrements appropriate session counter
        """
        pass
```

### 5. Report Generation Service

```python
class ReportGenerationService(BaseService):
    """Service for generating merge reports"""
    
    def generate_report(
        self,
        reference_id: str,
        format: str = 'pdf'
    ) -> str:
        """
        Generate a merge report.
        
        Args:
            reference_id: Session reference ID
            format: Report format ('pdf' or 'docx')
            
        Returns:
            Path to generated report file
            
        Report Contents:
        - Executive Summary
        - Package Information
        - Statistics (by classification, by object type)
        - Detailed Change List
        - Conflict Analysis
        - Recommendations
        """
        pass
    
    def _generate_pdf_report(
        self,
        session: MergeSession,
        data: Dict[str, Any]
    ) -> str:
        """Generate PDF report using ReportLab"""
        pass
    
    def _generate_docx_report(
        self,
        session: MergeSession,
        data: Dict[str, Any]
    ) -> str:
        """Generate Word document using python-docx"""
        pass
```

### 6. Session Statistics Service

```python
class SessionStatisticsService(BaseService):
    """Service for calculating session statistics"""
    
    def calculate_complexity(
        self,
        session_id: int
    ) -> str:
        """
        Calculate estimated complexity (Low, Medium, High).
        
        Based on:
        - Number of conflicts
        - Object types involved
        - Complexity of changes
        """
        pass
    
    def estimate_review_time(
        self,
        session_id: int
    ) -> float:
        """
        Estimate review time in hours.
        
        Based on:
        - Total changes
        - Conflict count
        - Object complexity
        - Historical data (if available)
        """
        pass
    
    def get_progress_metrics(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """
        Get progress metrics for a session.
        
        Returns:
            Dict containing:
            - total_changes: Total number of changes
            - reviewed_count: Number reviewed
            - skipped_count: Number skipped
            - pending_count: Number pending
            - progress_percent: Percentage complete
        """
        pass
```

## Data Models

### Database Schema Changes

```sql
-- Add new columns to changes table
ALTER TABLE changes ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE changes ADD COLUMN notes TEXT;
ALTER TABLE changes ADD COLUMN reviewed_at TIMESTAMP;
ALTER TABLE changes ADD COLUMN reviewed_by VARCHAR(255);

-- Add new columns to merge_sessions table
ALTER TABLE merge_sessions ADD COLUMN reviewed_count INTEGER DEFAULT 0;
ALTER TABLE merge_sessions ADD COLUMN skipped_count INTEGER DEFAULT 0;
ALTER TABLE merge_sessions ADD COLUMN estimated_complexity VARCHAR(20);
ALTER TABLE merge_sessions ADD COLUMN estimated_time_hours FLOAT;

-- Create indexes for performance
CREATE INDEX idx_change_status ON changes(session_id, status);
CREATE INDEX idx_change_reviewed_at ON changes(reviewed_at);
```

### Migration Script

```python
def upgrade():
    """Add new columns for UI enhancement"""
    # Changes table
    op.add_column('changes', sa.Column('status', sa.String(20), server_default='pending'))
    op.add_column('changes', sa.Column('notes', sa.Text))
    op.add_column('changes', sa.Column('reviewed_at', sa.DateTime))
    op.add_column('changes', sa.Column('reviewed_by', sa.String(255)))
    
    # MergeSession table
    op.add_column('merge_sessions', sa.Column('reviewed_count', sa.Integer, server_default='0'))
    op.add_column('merge_sessions', sa.Column('skipped_count', sa.Integer, server_default='0'))
    op.add_column('merge_sessions', sa.Column('estimated_complexity', sa.String(20)))
    op.add_column('merge_sessions', sa.Column('estimated_time_hours', sa.Float))
    
    # Indexes
    op.create_index('idx_change_status', 'changes', ['session_id', 'status'])
    op.create_index('idx_change_reviewed_at', 'changes', ['reviewed_at'])
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Change position display accuracy
*For any* change in any session, when rendering the change detail page, the displayed position should equal the change's display_order and the total should equal the session's total_changes
**Validates: Requirements 1.2**

### Property 2: Navigation buttons presence
*For any* change detail page, the rendered HTML should contain both Previous and Next navigation buttons
**Validates: Requirements 1.3**

### Property 3: Progress percentage calculation
*For any* change in a session, the progress percentage should equal (display_order / total_changes) * 100
**Validates: Requirements 1.6**

### Property 4: SAIL code display
*For any* object with SAIL code, when rendering the change detail page, the SAIL code from the vendor version should be present in the rendered output
**Validates: Requirements 2.1**

### Property 5: Classification badge display
*For any* change, when rendering the change detail page, the classification value should be displayed in the rendered output
**Validates: Requirements 2.2**

### Property 6: Change type display
*For any* change with a vendor_change_type, when rendering the change detail page, the vendor change type should be displayed in the rendered output
**Validates: Requirements 2.3, 2.4**

### Property 7: Object metadata display
*For any* change, when rendering the change detail page, both the object's UUID and description should be present in the rendered output
**Validates: Requirements 2.5**

### Property 8: Action buttons presence
*For any* change detail page, the rendered HTML should contain "Mark as Reviewed", "Skip", and "Save Notes" buttons
**Validates: Requirements 3.1, 3.2, 3.4**

### Property 9: Notes textarea presence
*For any* change detail page, the rendered HTML should contain a textarea element for notes
**Validates: Requirements 3.3**

### Property 10: Mark as reviewed state transition
*For any* change with status='pending', when marked as reviewed, the change status should become 'reviewed', reviewed_at should be set, and the session's reviewed_count should increment by 1
**Validates: Requirements 3.5**

### Property 11: Skip state transition
*For any* change with status='pending', when skipped, the change status should become 'skipped' and the session's skipped_count should increment by 1
**Validates: Requirements 3.6**

### Property 12: Notes persistence
*For any* change and any notes text, when notes are saved, retrieving the change from the database should return the same notes text
**Validates: Requirements 3.7**

### Property 13: Session info display
*For any* change detail page, the rendered HTML should contain the session reference_id, status, reviewed_count, and skipped_count
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 14: Summary statistics accuracy
*For any* session, the sum of counts by classification should equal the total_changes
**Validates: Requirements 5.2, 5.3**

### Property 15: Object type breakdown accuracy
*For any* session, the sum of counts by object type should equal the total_changes
**Validates: Requirements 5.4**

### Property 15a: Object type expansion displays objects
*For any* object type in the breakdown, when clicked/expanded, a grid should display showing all objects of that type with their name, UUID, classification, and complexity
**Validates: Requirements 5.4**

### Property 16: Complexity and time metrics presence
*For any* session summary page, the rendered HTML should contain estimated_complexity and estimated_time_hours values
**Validates: Requirements 5.5**

### Property 17: Status filter correctness
*For any* status value, when filtering sessions by that status, all returned sessions should have that status
**Validates: Requirements 6.3**

### Property 18: Search filter correctness
*For any* search term, when filtering sessions, all returned sessions should have the search term in either their reference_id or package filenames
**Validates: Requirements 6.4**

### Property 19: Sort order correctness
*For any* sort option, when sorting sessions, the returned list should be ordered according to the sort criteria
**Validates: Requirements 6.6**

### Property 20: Session card completeness
*For any* session, when rendering a session card, the rendered HTML should contain the reference_id, created_at, and status
**Validates: Requirements 7.1**

### Property 21: Progress format correctness
*For any* session card, the progress display should match the format "X / Y (Z%)" where X = reviewed_count, Y = total_changes, and Z = (X/Y)*100
**Validates: Requirements 7.2**

### Property 22: Action buttons match status
*For any* session card, the action buttons present should correspond to the session's status
**Validates: Requirements 7.3**

### Property 23: Report generation completeness
*For any* session, when generating a report, the report should contain session information, all three package details, classification breakdown, and object type breakdown
**Validates: Requirements 8.2, 8.3, 8.4**

### Property 24: Report format validity
*For any* generated report, the file should be a valid PDF or Word document that can be opened
**Validates: Requirements 8.5**

### Property 25: Jump navigation correctness
*For any* change selected from the jump menu, the navigation should go to that change's detail page
**Validates: Requirements 9.2**

### Property 26: Workflow grouping correctness
*For any* session, when rendering the workflow page, changes should be grouped by their classification value
**Validates: Requirements 9.3**

### Property 27: Classification filter correctness
*For any* classification filter, when applied to the workflow page, only changes with that classification should be displayed
**Validates: Requirements 9.4**

### Property 28: Duplicate submission prevention
*For any* session being processed, attempting to create another session with the same packages should be prevented or queued
**Validates: Requirements 10.5**

## Error Handling

### Error Handling Strategy

1. **404 Errors**: Display user-friendly page with navigation back to appropriate location
2. **Database Errors**: Log technical details, show generic error to user
3. **Validation Errors**: Show specific validation messages to user
4. **File Upload Errors**: Show specific error reason (file too large, invalid format, etc.)
5. **Processing Errors**: Update session status to 'error', log details, allow retry

### Error Response Format

```python
{
    "success": false,
    "error": {
        "code": "SESSION_NOT_FOUND",
        "message": "Session MS_A1B2C3 not found",
        "details": "The requested session does not exist or has been deleted"
    }
}
```

### Error Codes

- `SESSION_NOT_FOUND`: Requested session doesn't exist
- `CHANGE_NOT_FOUND`: Requested change doesn't exist
- `INVALID_STATUS`: Invalid status transition
- `DATABASE_ERROR`: Database operation failed
- `FILE_UPLOAD_ERROR`: File upload failed
- `REPORT_GENERATION_ERROR`: Report generation failed
- `VALIDATION_ERROR`: Input validation failed

## Testing Strategy

### Unit Testing

Unit tests will cover:
- Service methods (navigation, actions, statistics)
- Repository methods (queries, updates)
- Helper functions (complexity calculation, time estimation)
- Template rendering (with mock data)
- Error handling paths

Example unit tests:
```python
def test_mark_as_reviewed_updates_status():
    """Test that marking a change as reviewed updates its status"""
    change = create_test_change(status='pending')
    service.mark_as_reviewed(change.id)
    assert change.status == 'reviewed'
    assert change.reviewed_at is not None

def test_calculate_progress_percentage():
    """Test progress percentage calculation"""
    assert calculate_progress(1, 6) == 16.67
    assert calculate_progress(6, 6) == 100.0
    assert calculate_progress(0, 6) == 0.0
```

### Property-Based Testing

Property-based tests will use pytest with real database and test packages. Each property test will:
1. Create test sessions with varying characteristics
2. Execute the operation being tested
3. Verify the property holds

Example property tests:
```python
def test_property_10_mark_as_reviewed_state_transition():
    """
    Property 10: Mark as reviewed state transition
    For any change with status='pending', when marked as reviewed,
    the change status should become 'reviewed', reviewed_at should be set,
    and the session's reviewed_count should increment by 1
    """
    # Create test session with changes
    session = create_test_session_with_changes(num_changes=10)
    change = session.changes[0]
    initial_reviewed_count = session.reviewed_count
    
    # Mark as reviewed
    service.mark_as_reviewed(session.reference_id, change.id)
    
    # Verify property
    db.session.refresh(change)
    db.session.refresh(session)
    assert change.status == 'reviewed'
    assert change.reviewed_at is not None
    assert session.reviewed_count == initial_reviewed_count + 1

def test_property_14_summary_statistics_accuracy():
    """
    Property 14: Summary statistics accuracy
    For any session, the sum of counts by classification should equal
    the total_changes
    """
    # Create test session
    session = create_test_session_with_changes(num_changes=20)
    
    # Get statistics
    stats = service.get_session_statistics(session.reference_id)
    
    # Verify property
    total_by_classification = sum(stats['by_classification'].values())
    assert total_by_classification == session.total_changes
```

### Integration Testing

Integration tests will verify:
- Complete workflows (create session → navigate changes → mark reviewed → generate report)
- Database transactions and rollbacks
- Template rendering with real data
- File generation (reports)

### Browser Testing

Browser tests (using Selenium or Playwright) will verify:
- Navigation flows
- Button clicks and form submissions
- Filter and search functionality
- Responsive design
- Accessibility

## Performance Considerations

### Caching Strategy

1. **Session Statistics**: Cache for 5 minutes, invalidate on change updates
2. **Object Type Breakdown**: Cache for 10 minutes
3. **Report Generation**: Cache generated reports for 1 hour

### Database Optimization

1. **Indexes**: Add indexes on frequently queried columns
   - `changes(session_id, status)`
   - `changes(session_id, display_order)`
   - `changes(reviewed_at)`

2. **Query Optimization**: Use eager loading for relationships
   ```python
   changes = db.session.query(Change).options(
       joinedload(Change.object),
       joinedload(Change.session)
   ).filter_by(session_id=session_id).all()
   ```

3. **Pagination**: Implement pagination for large change lists
   - Default page size: 20 changes
   - Load more on scroll or pagination controls

### Frontend Optimization

1. **Lazy Loading**: Load change details on demand
2. **Debouncing**: Debounce search input (300ms)
3. **Caching**: Cache rendered templates in browser
4. **Compression**: Enable gzip compression for responses

## Security Considerations

### Input Validation

1. **Reference IDs**: Validate format (MS_XXXXXX)
2. **Change IDs**: Validate as positive integers
3. **Notes**: Sanitize HTML, limit length (10,000 characters)
4. **Search Terms**: Sanitize to prevent SQL injection
5. **File Uploads**: Validate file type, size, and content

### Authorization

1. **Session Access**: Verify user has access to session (future: multi-user)
2. **Change Modification**: Verify user can modify change
3. **Report Generation**: Rate limit to prevent abuse

### Data Protection

1. **SQL Injection**: Use parameterized queries
2. **XSS**: Escape all user input in templates
3. **CSRF**: Use CSRF tokens for all forms
4. **File Upload**: Scan uploaded files for malware

## Deployment Considerations

### Database Migration

1. Run migration script to add new columns
2. Backfill existing sessions with default values
3. Update indexes
4. Verify data integrity

### Rollback Plan

1. Keep migration script reversible
2. Backup database before migration
3. Test rollback procedure
4. Document rollback steps

### Monitoring

1. **Error Tracking**: Log all errors with context
2. **Performance Metrics**: Track page load times
3. **Usage Metrics**: Track feature usage
4. **Alert Thresholds**: Alert on error rate > 5%

## Future Enhancements

1. **Real-time Updates**: WebSocket support for live progress updates
2. **Collaborative Review**: Multiple users reviewing same session
3. **Change Comments**: Discussion threads on changes
4. **Approval Workflow**: Require approval before completing merge
5. **Audit Trail**: Track all actions with timestamps and users
6. **Export Options**: Export to Excel, CSV, JSON
7. **Custom Reports**: User-defined report templates
8. **AI Assistance**: AI-powered merge recommendations
9. **Diff Visualization**: Side-by-side diff view for SAIL code
10. **Conflict Resolution**: Guided conflict resolution wizard
