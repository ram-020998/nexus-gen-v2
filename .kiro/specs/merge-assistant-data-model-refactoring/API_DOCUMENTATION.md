# Merge Assistant API Documentation

## Overview

This document describes the API for the Merge Assistant feature after the data model refactoring. All APIs use the normalized database schema and provide efficient query performance through indexed lookups and JOIN operations.

## Service Layer

### ThreeWayMergeService

The main service class for managing three-way merge sessions.

#### Initialization

```python
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService

service = ThreeWayMergeService()
```

#### Methods

##### create_session

Create a new merge session and initiate analysis.

**Signature:**
```python
def create_session(
    self,
    base_zip_path: str,
    customized_zip_path: str,
    new_vendor_zip_path: str
) -> MergeSession
```

**Parameters:**
- `base_zip_path` (str): Path to base package ZIP file (A)
- `customized_zip_path` (str): Path to customized package ZIP file (B)
- `new_vendor_zip_path` (str): Path to new vendor package ZIP file (C)

**Returns:**
- `MergeSession`: Created session object with status 'ready'

**Raises:**
- `BlueprintGenerationError`: If blueprint generation fails
- `Exception`: For other errors during processing

**Example:**
```python
session = service.create_session(
    base_zip_path='uploads/base_v1.0.zip',
    customized_zip_path='uploads/customized_v1.0.zip',
    new_vendor_zip_path='uploads/vendor_v2.0.zip'
)
print(f"Session created: {session.reference_id}")
print(f"Total changes: {session.total_changes}")
```

**Process:**
1. Creates MergeSession record
2. Generates blueprints for A, B, C packages
3. Normalizes blueprints into Package and AppianObject tables
4. Performs three-way comparison (A→B, A→C)
5. Classifies changes
6. Orders changes by dependencies
7. Generates merge guidance
8. Normalizes changes into Change and ChangeReview tables
9. Updates session status to 'ready'

---

##### get_session

Retrieve session by ID.

**Signature:**
```python
def get_session(self, session_id: int) -> Optional[MergeSession]
```

**Parameters:**
- `session_id` (int): Session ID

**Returns:**
- `MergeSession` or `None`: Session object if found, None otherwise

**Example:**
```python
session = service.get_session(1)
if session:
    print(f"Session: {session.reference_id}")
    print(f"Status: {session.status}")
```

---

##### get_session_by_reference_id

Retrieve session by reference ID.

**Signature:**
```python
def get_session_by_reference_id(
    self,
    reference_id: str
) -> Optional[MergeSession]
```

**Parameters:**
- `reference_id` (str): Reference ID (e.g., 'MRG_001')

**Returns:**
- `MergeSession` or `None`: Session object if found, None otherwise

**Example:**
```python
session = service.get_session_by_reference_id('MRG_001')
if session:
    print(f"Found session {session.id}")
```

---

##### get_summary

Get merge summary with statistics using optimized SQL aggregates.

**Signature:**
```python
def get_summary(self, session_id: int) -> Dict[str, Any]
```

**Parameters:**
- `session_id` (int): Session ID

**Returns:**
- `dict`: Summary information with the following structure:

```python
{
    'session_id': int,
    'reference_id': str,
    'packages': {
        'base': str,           # Base package name
        'customized': str,     # Customized package name
        'new_vendor': str      # New vendor package name
    },
    'statistics': {
        'total_changes': int,
        'no_conflict': int,
        'conflict': int,
        'customer_only': int,
        'removed_but_customized': int
    },
    'breakdown_by_type': {
        'Interface': {
            'no_conflict': int,
            'conflict': int,
            'customer_only': int,
            'removed_but_customized': int
        },
        # ... other object types
    },
    'estimated_complexity': str,  # 'LOW', 'MEDIUM', or 'HIGH'
    'estimated_time_hours': int,
    'status': str,
    'created_at': str,            # ISO format
    'reviewed_count': int,
    'skipped_count': int
}
```

**Example:**
```python
summary = service.get_summary(session_id=1)
print(f"Total changes: {summary['statistics']['total_changes']}")
print(f"Conflicts: {summary['statistics']['conflict']}")
print(f"Complexity: {summary['estimated_complexity']}")
print(f"Estimated time: {summary['estimated_time_hours']} hours")
```

**Performance:**
- Uses single GROUP BY query with CASE statements
- Leverages `idx_change_session_classification` index
- Typical execution time: < 10ms for sessions with 1000+ changes

---

##### get_ordered_changes

Get smart-ordered list of changes using SQL JOIN with optional pagination.

**Signature:**
```python
def get_ordered_changes(
    self,
    session_id: int,
    page: Optional[int] = None,
    page_size: Optional[int] = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `session_id` (int): Session ID
- `page` (int, optional): Page number (1-indexed) for pagination
- `page_size` (int, optional): Number of results per page

**Returns:**
- `list`: List of change dictionaries with enriched data

**Change Dictionary Structure:**
```python
{
    'id': int,
    'uuid': str,
    'name': str,
    'type': str,
    'classification': str,
    'change_type': str,
    'vendor_change_type': str,
    'customer_change_type': str,
    'display_order': int,
    'base_object': {
        'uuid': str,
        'name': str,
        'type': str,
        'sail_code': str,
        'fields': dict,
        'properties': dict
    },
    'customer_object': {...},  # Same structure as base_object
    'vendor_object': {...},    # Same structure as base_object
    'merge_guidance': {
        'recommendation': str,
        'reason': str,
        'conflicts': [
            {
                'field_name': str,
                'conflict_type': str,
                'description': str
            }
        ],
        'changes': [
            {
                'field_name': str,
                'description': str,
                'old_value': str,
                'new_value': str
            }
        ]
    },
    'review_status': str,      # 'pending', 'reviewed', or 'skipped'
    'user_notes': str,
    'reviewed_at': str         # ISO format or None
}
```

**Example:**
```python
# Get all changes
changes = service.get_ordered_changes(session_id=1)
print(f"Total changes: {len(changes)}")

# Get first page (50 changes)
changes = service.get_ordered_changes(session_id=1, page=1, page_size=50)
print(f"Page 1: {len(changes)} changes")

# Iterate through changes
for change in changes:
    print(f"{change['display_order']}: {change['name']} ({change['classification']})")
```

**Performance:**
- Uses eager loading with `joinedload` for related objects
- Leverages `idx_change_session_order` index
- Typical execution time: < 50ms for 1000 changes without pagination
- Pagination reduces memory usage for large sessions

---

##### filter_changes

Filter changes using SQL WHERE clauses with optimized indexed queries.

**Signature:**
```python
def filter_changes(
    self,
    session_id: int,
    classification: Optional[str] = None,
    object_type: Optional[str] = None,
    review_status: Optional[str] = None,
    search_term: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    use_cache: bool = False
) -> List[Dict[str, Any]]
```

**Parameters:**
- `session_id` (int): Session ID
- `classification` (str, optional): Filter by classification ('NO_CONFLICT', 'CONFLICT', 'CUSTOMER_ONLY', 'REMOVED_BUT_CUSTOMIZED')
- `object_type` (str, optional): Filter by object type ('Interface', 'Process Model', etc.)
- `review_status` (str, optional): Filter by review status ('pending', 'reviewed', 'skipped')
- `search_term` (str, optional): Search by object name (case-insensitive)
- `page` (int, optional): Page number (1-indexed)
- `page_size` (int, optional): Number of results per page
- `use_cache` (bool): Whether to use query result caching (default: False)

**Returns:**
- `list`: Filtered list of change dictionaries (same structure as `get_ordered_changes`)

**Example:**
```python
# Get all conflicts
conflicts = service.filter_changes(
    session_id=1,
    classification='CONFLICT'
)
print(f"Found {len(conflicts)} conflicts")

# Get unreviewed interface changes
interfaces = service.filter_changes(
    session_id=1,
    object_type='Interface',
    review_status='pending'
)

# Search for objects containing "vendor"
vendor_changes = service.filter_changes(
    session_id=1,
    search_term='vendor'
)

# Complex filter with pagination
results = service.filter_changes(
    session_id=1,
    classification='CONFLICT',
    object_type='Interface',
    review_status='pending',
    page=1,
    page_size=20
)
```

**Performance:**
- Uses indexed columns for all filters
- Filters applied in order of selectivity
- Typical execution time: < 20ms for filtered queries
- Index usage:
  - `idx_change_session_classification` for classification filter
  - `idx_change_session_type` for object_type filter
  - `idx_review_session_status` for review_status filter
  - `idx_object_type_name` for search_term filter

---

##### update_progress

Update user progress on a specific change using normalized tables.

**Signature:**
```python
def update_progress(
    self,
    session_id: int,
    change_index: int,
    review_status: str,
    notes: Optional[str] = None
) -> None
```

**Parameters:**
- `session_id` (int): Session ID
- `change_index` (int): Index of the change in ordered list (0-based)
- `review_status` (str): 'reviewed' or 'skipped'
- `notes` (str, optional): Optional user notes

**Raises:**
- `ValueError`: If session not found or invalid parameters

**Example:**
```python
# Mark first change as reviewed
service.update_progress(
    session_id=1,
    change_index=0,
    review_status='reviewed',
    notes='Looks good, accepting vendor changes'
)

# Skip a change
service.update_progress(
    session_id=1,
    change_index=5,
    review_status='skipped',
    notes='Will review later'
)
```

**Side Effects:**
- Creates or updates ChangeReview record
- Updates session.current_change_index
- Updates session.reviewed_count and session.skipped_count
- Sets session.status to 'completed' if all changes reviewed/skipped
- Logs user action

---

##### generate_report

Generate final merge report using JOIN queries.

**Signature:**
```python
def generate_report(self, session_id: int) -> Dict[str, Any]
```

**Parameters:**
- `session_id` (int): Session ID

**Returns:**
- `dict`: Complete merge report with the following structure:

```python
{
    'summary': {
        # Same as get_summary() output
    },
    'changes': [
        # List of all changes with complete data
        # Same structure as get_ordered_changes() output
    ],
    'changes_by_category': {
        'NO_CONFLICT': [...],
        'CONFLICT': [...],
        'CUSTOMER_ONLY': [...],
        'REMOVED_BUT_CUSTOMIZED': [...]
    },
    'statistics': {
        'total_changes': int,
        'reviewed': int,
        'skipped': int,
        'pending': int,
        'conflicts': int,
        'processing_time_seconds': int,
        'completed_at': str  # ISO format or None
    },
    'session': {
        'reference_id': str,
        'base_package_name': str,
        'customized_package_name': str,
        'new_vendor_package_name': str,
        'status': str,
        'created_at': str,
        'updated_at': str
    }
}
```

**Example:**
```python
report = service.generate_report(session_id=1)

# Export to JSON
import json
with open('merge_report.json', 'w') as f:
    json.dump(report, f, indent=2)

# Print summary
print(f"Session: {report['session']['reference_id']}")
print(f"Total changes: {report['statistics']['total_changes']}")
print(f"Reviewed: {report['statistics']['reviewed']}")
print(f"Conflicts: {report['statistics']['conflicts']}")
```

---

##### get_statistics_by_type

Get statistics for a specific object type using optimized aggregation.

**Signature:**
```python
def get_statistics_by_type(
    self,
    session_id: int,
    object_type: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `session_id` (int): Session ID
- `object_type` (str, optional): Object type to filter by (None for all types)

**Returns:**
- `dict`: Statistics dictionary:

```python
{
    'object_type': str,  # Object type or 'all'
    'total': int,
    'no_conflict': int,
    'conflict': int,
    'customer_only': int,
    'removed_but_customized': int
}
```

**Example:**
```python
# Get statistics for all interfaces
interface_stats = service.get_statistics_by_type(
    session_id=1,
    object_type='Interface'
)
print(f"Interface changes: {interface_stats['total']}")
print(f"Interface conflicts: {interface_stats['conflict']}")

# Get overall statistics
overall_stats = service.get_statistics_by_type(session_id=1)
print(f"Total changes: {overall_stats['total']}")
```

---

##### analyze_query_plan

Analyze query execution plan for performance optimization.

**Signature:**
```python
def analyze_query_plan(
    self,
    session_id: int,
    query_type: str = 'get_ordered_changes'
) -> List[Dict[str, Any]]
```

**Parameters:**
- `session_id` (int): Session ID
- `query_type` (str): Type of query to analyze ('get_ordered_changes', 'filter_changes', 'get_summary')

**Returns:**
- `list`: List of query plan steps showing index usage

**Example:**
```python
plan = service.analyze_query_plan(session_id=1, query_type='filter_changes')
for step in plan:
    print(f"Step {step['id']}: {step['detail']}")
```

---

##### verify_index_usage

Verify that queries are using appropriate indexes.

**Signature:**
```python
def verify_index_usage(self, session_id: int) -> Dict[str, bool]
```

**Parameters:**
- `session_id` (int): Session ID

**Returns:**
- `dict`: Dictionary indicating which indexes are being used:

```python
{
    'idx_change_session_classification': bool,
    'idx_change_session_type': bool,
    'idx_change_session_order': bool,
    'idx_review_session_status': bool
}
```

**Example:**
```python
index_usage = service.verify_index_usage(session_id=1)
for index_name, is_used in index_usage.items():
    status = "✅" if is_used else "❌"
    print(f"{status} {index_name}")
```

---

## Supporting Services

### PackageService

Service for managing Package and AppianObject records.

**Methods:**
- `create_package_with_all_data(session_id, package_type, blueprint_result)` - Create package with objects, dependencies, and process models
- `get_object_by_uuid(package_id, uuid)` - Get object by UUID
- `get_objects_by_type(package_id, object_type)` - Get all objects of specific type

### ChangeService

Service for managing Change records.

**Methods:**
- `create_changes_from_comparison(session_id, classification_results, ordered_changes)` - Create change records from comparison
- `get_change_with_objects(change_id)` - Get change with all related objects

### MigrationService

Service for migrating sessions from old JSON schema to normalized schema.

**Methods:**
- `migrate_session(session_id)` - Migrate single session
- `verify_migration(session_id)` - Verify migration correctness
- `migrate_all_sessions()` - Migrate all sessions

---

## Error Handling

All service methods may raise the following exceptions:

### BlueprintGenerationError

Raised when blueprint generation fails.

```python
try:
    session = service.create_session(base_path, customized_path, vendor_path)
except BlueprintGenerationError as e:
    print(f"Blueprint generation failed: {str(e)}")
```

### ValueError

Raised for invalid parameters or missing data.

```python
try:
    changes = service.get_ordered_changes(session_id=999)
except ValueError as e:
    print(f"Invalid session: {str(e)}")
```

### DatabaseError

Raised for database-related errors.

```python
from sqlalchemy.exc import DatabaseError

try:
    service.update_progress(session_id, change_index, review_status)
except DatabaseError as e:
    print(f"Database error: {str(e)}")
    db.session.rollback()
```

---

## Performance Guidelines

### Query Optimization

1. **Use pagination for large result sets:**
   ```python
   # Good: Paginated query
   changes = service.get_ordered_changes(session_id, page=1, page_size=50)
   
   # Avoid: Loading all changes at once for large sessions
   changes = service.get_ordered_changes(session_id)  # May load 1000+ changes
   ```

2. **Use filters to reduce result set:**
   ```python
   # Good: Filtered query
   conflicts = service.filter_changes(session_id, classification='CONFLICT')
   
   # Avoid: Filtering in Python
   all_changes = service.get_ordered_changes(session_id)
   conflicts = [c for c in all_changes if c['classification'] == 'CONFLICT']
   ```

3. **Use aggregates for statistics:**
   ```python
   # Good: SQL aggregate
   summary = service.get_summary(session_id)
   total = summary['statistics']['total_changes']
   
   # Avoid: Counting in Python
   changes = service.get_ordered_changes(session_id)
   total = len(changes)
   ```

### Caching

For repeated queries, consider caching results:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_summary(session_id):
    return service.get_summary(session_id)
```

### Batch Operations

When updating multiple changes, use transactions:

```python
from models import db

try:
    for i, change in enumerate(changes_to_review):
        service.update_progress(session_id, i, 'reviewed')
    db.session.commit()
except Exception as e:
    db.session.rollback()
    raise
```

---

## Migration from Old API

### Old JSON-based API

```python
# OLD: Accessing JSON columns
session = MergeSession.query.get(session_id)
ordered_changes = json.loads(session.ordered_changes)
for change in ordered_changes:
    print(change['name'])
```

### New Normalized API

```python
# NEW: Using service methods
changes = service.get_ordered_changes(session_id)
for change in changes:
    print(change['name'])
```

### Key Differences

1. **No JSON parsing required** - All data is in normalized tables
2. **Eager loading** - Related objects loaded efficiently with JOINs
3. **Indexed queries** - All filters use database indexes
4. **Pagination support** - Handle large result sets efficiently
5. **Type safety** - Proper data types instead of JSON strings

---

## Examples

### Complete Workflow Example

```python
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService

# Initialize service
service = ThreeWayMergeService()

# 1. Create session
session = service.create_session(
    base_zip_path='uploads/base.zip',
    customized_zip_path='uploads/customized.zip',
    new_vendor_zip_path='uploads/vendor.zip'
)
print(f"Session created: {session.reference_id}")

# 2. Get summary
summary = service.get_summary(session.id)
print(f"Total changes: {summary['statistics']['total_changes']}")
print(f"Conflicts: {summary['statistics']['conflict']}")

# 3. Get conflicts
conflicts = service.filter_changes(
    session.id,
    classification='CONFLICT'
)
print(f"Found {len(conflicts)} conflicts")

# 4. Review changes
for i, change in enumerate(conflicts):
    print(f"\nReviewing: {change['name']}")
    print(f"Classification: {change['classification']}")
    print(f"Recommendation: {change['merge_guidance']['recommendation']}")
    
    # Mark as reviewed
    service.update_progress(
        session.id,
        change['display_order'],
        'reviewed',
        notes='Reviewed and approved'
    )

# 5. Generate final report
report = service.generate_report(session.id)
print(f"\nReview complete!")
print(f"Reviewed: {report['statistics']['reviewed']}")
print(f"Skipped: {report['statistics']['skipped']}")
```

### Filtering and Searching Example

```python
# Get all unreviewed interface conflicts
interface_conflicts = service.filter_changes(
    session_id=1,
    classification='CONFLICT',
    object_type='Interface',
    review_status='pending'
)

# Search for changes related to "customer"
customer_changes = service.filter_changes(
    session_id=1,
    search_term='customer'
)

# Get first page of process model changes
pm_changes = service.filter_changes(
    session_id=1,
    object_type='Process Model',
    page=1,
    page_size=20
)
```

### Statistics Example

```python
# Get overall statistics
summary = service.get_summary(session_id=1)
stats = summary['statistics']

print(f"Total: {stats['total_changes']}")
print(f"No Conflict: {stats['no_conflict']}")
print(f"Conflict: {stats['conflict']}")
print(f"Customer Only: {stats['customer_only']}")
print(f"Removed but Customized: {stats['removed_but_customized']}")

# Get statistics by type
for obj_type in ['Interface', 'Process Model', 'Record Type']:
    type_stats = service.get_statistics_by_type(session_id=1, object_type=obj_type)
    print(f"\n{obj_type}:")
    print(f"  Total: {type_stats['total']}")
    print(f"  Conflicts: {type_stats['conflict']}")
```

---

## Testing

### Unit Testing

```python
import pytest
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService

def test_create_session():
    service = ThreeWayMergeService()
    session = service.create_session(
        'test_data/base.zip',
        'test_data/customized.zip',
        'test_data/vendor.zip'
    )
    assert session.status == 'ready'
    assert session.total_changes > 0

def test_filter_changes():
    service = ThreeWayMergeService()
    conflicts = service.filter_changes(1, classification='CONFLICT')
    assert all(c['classification'] == 'CONFLICT' for c in conflicts)
```

### Integration Testing

```python
def test_complete_workflow():
    service = ThreeWayMergeService()
    
    # Create session
    session = service.create_session(
        'test_data/base.zip',
        'test_data/customized.zip',
        'test_data/vendor.zip'
    )
    
    # Get changes
    changes = service.get_ordered_changes(session.id)
    assert len(changes) == session.total_changes
    
    # Review first change
    service.update_progress(session.id, 0, 'reviewed')
    
    # Verify progress
    updated_session = service.get_session(session.id)
    assert updated_session.reviewed_count == 1
```

---

## References

- Schema Documentation: `SCHEMA_DOCUMENTATION.md`
- Migration Guide: `MIGRATION_GUIDE.md`
- Design Document: `design.md`
- Requirements Document: `requirements.md`
