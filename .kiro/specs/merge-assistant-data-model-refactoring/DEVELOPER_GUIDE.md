# Merge Assistant Developer Guide

## Overview

This guide provides information for developers working with the Merge Assistant feature after the data model refactoring. It covers common development tasks, best practices, and troubleshooting tips.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Common Development Tasks](#common-development-tasks)
4. [Best Practices](#best-practices)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.8+
- Flask
- SQLAlchemy
- SQLite

### Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```bash
   python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

### Project Structure

```
nexus-gen-v2/
├── app.py                          # Flask application
├── models.py                       # Database models
├── services/
│   └── merge_assistant/
│       ├── three_way_merge_service.py
│       ├── package_service.py
│       ├── change_service.py
│       ├── migration_service.py
│       └── ...
├── controllers/
│   └── merge_assistant_controller.py
├── templates/
│   └── merge_assistant/
│       ├── upload.html
│       ├── summary.html
│       └── ...
└── tests/
    ├── test_merge_assistant_integration.py
    ├── test_merge_assistant_properties.py
    └── ...
```

## Architecture Overview

### Service Layer Architecture

```
Controller Layer
    ↓
ThreeWayMergeService (Orchestrator)
    ↓
    ├── BlueprintGenerationService
    ├── PackageService
    ├── ThreeWayComparisonService
    ├── ChangeClassificationService
    ├── DependencyAnalysisService
    ├── MergeGuidanceService
    └── ChangeService
    ↓
Database Layer (SQLAlchemy Models)
```

### Data Flow

1. **Upload Phase**: User uploads 3 ZIP files
2. **Blueprint Generation**: Extract and analyze Appian packages
3. **Normalization**: Store blueprints in normalized tables
4. **Comparison**: Compare A→B and A→C
5. **Classification**: Classify changes into categories
6. **Ordering**: Order changes by dependencies
7. **Guidance**: Generate merge guidance
8. **Storage**: Store changes in normalized tables
9. **Review**: User reviews changes
10. **Report**: Generate final merge report

## Common Development Tasks

### Adding a New Object Type

1. **Update AppianObject model** (if needed):
   ```python
   # models.py - No changes needed, object_type is a string field
   ```

2. **Update blueprint generation**:
   ```python
   # services/appian_analyzer/analyzer.py
   def extract_objects(self, zip_path):
       # Add extraction logic for new object type
       pass
   ```

3. **Update comparison logic** (if special handling needed):
   ```python
   # services/merge_assistant/three_way_comparison_service.py
   def _compare_objects(self, base_obj, target_obj):
       if obj_type == 'NewObjectType':
           # Special comparison logic
           pass
   ```

### Adding a New Filter

1. **Update filter_changes method**:
   ```python
   # services/merge_assistant/three_way_merge_service.py
   def filter_changes(
       self,
       session_id: int,
       # ... existing filters
       new_filter: Optional[str] = None
   ):
       query = db.session.query(Change)...
       
       if new_filter:
           query = query.filter(Change.new_field == new_filter)
       
       return query.all()
   ```

2. **Add index if needed**:
   ```python
   # models.py
   class Change(db.Model):
       new_field = db.Column(db.String(50), index=True)
   ```

3. **Update controller**:
   ```python
   # controllers/merge_assistant_controller.py
   @bp.route('/changes/filter')
   def filter_changes():
       new_filter = request.args.get('new_filter')
       changes = service.filter_changes(
           session_id,
           new_filter=new_filter
       )
       return render_template('changes.html', changes=changes)
   ```

### Adding a New Statistic

1. **Update get_summary method**:
   ```python
   # services/merge_assistant/three_way_merge_service.py
   def get_summary(self, session_id: int):
       # Add new statistic calculation
       new_stat = db.session.query(func.count(Change.id))\
           .filter(Change.session_id == session_id)\
           .filter(Change.new_field == 'value')\
           .scalar()
       
       return {
           'statistics': {
               # ... existing stats
               'new_stat': new_stat
           }
       }
   ```

2. **Update template**:
   ```html
   <!-- templates/merge_assistant/summary.html -->
   <div class="stat">
       <span class="label">New Stat:</span>
       <span class="value">{{ summary.statistics.new_stat }}</span>
   </div>
   ```

### Migrating Old Sessions

If you have sessions in the old JSON format:

```bash
# Run migration script
python migrate_merge_sessions.py

# Verify migration
python -c "from services.merge_assistant.migration_service import MigrationService; from app import create_app; app = create_app(); app.app_context().push(); service = MigrationService(); print(service.verify_migration(1))"
```

## Best Practices

### Database Queries

1. **Always use indexes for filters**:
   ```python
   # Good: Uses idx_change_session_classification
   changes = db.session.query(Change)\
       .filter(Change.session_id == session_id)\
       .filter(Change.classification == 'CONFLICT')\
       .all()
   
   # Bad: No index on custom field
   changes = db.session.query(Change)\
       .filter(Change.custom_field == 'value')\
       .all()
   ```

2. **Use eager loading for related objects**:
   ```python
   # Good: Single query with JOINs
   changes = db.session.query(Change)\
       .options(
           joinedload(Change.base_object),
           joinedload(Change.customer_object),
           joinedload(Change.vendor_object)
       )\
       .all()
   
   # Bad: N+1 queries
   changes = db.session.query(Change).all()
   for change in changes:
       base_obj = change.base_object  # Separate query!
   ```

3. **Use pagination for large result sets**:
   ```python
   # Good: Paginated query
   changes = db.session.query(Change)\
       .filter(Change.session_id == session_id)\
       .limit(50)\
       .offset(0)\
       .all()
   
   # Bad: Loading all records
   changes = db.session.query(Change)\
       .filter(Change.session_id == session_id)\
       .all()  # May load 1000+ records
   ```

4. **Use aggregates for statistics**:
   ```python
   # Good: SQL aggregate
   count = db.session.query(func.count(Change.id))\
       .filter(Change.session_id == session_id)\
       .scalar()
   
   # Bad: Loading all records to count
   changes = db.session.query(Change)\
       .filter(Change.session_id == session_id)\
       .all()
   count = len(changes)
   ```

### Error Handling

1. **Always use transactions for multi-step operations**:
   ```python
   try:
       # Multiple database operations
       package = Package(...)
       db.session.add(package)
       
       for obj_data in objects:
           obj = AppianObject(...)
           db.session.add(obj)
       
       db.session.commit()
   except Exception as e:
       db.session.rollback()
       logger.error(f"Error creating package: {str(e)}")
       raise
   ```

2. **Validate input before database operations**:
   ```python
   def update_progress(self, session_id, change_index, review_status):
       # Validate inputs
       if review_status not in ['reviewed', 'skipped']:
           raise ValueError(f"Invalid review_status: {review_status}")
       
       session = self.get_session(session_id)
       if not session:
           raise ValueError(f"Session {session_id} not found")
       
       # Proceed with update
       ...
   ```

3. **Log errors with context**:
   ```python
   try:
       service.create_session(base_path, customized_path, vendor_path)
   except BlueprintGenerationError as e:
       logger.error(
           f"Blueprint generation failed",
           extra={
               'base_path': base_path,
               'customized_path': customized_path,
               'vendor_path': vendor_path,
               'error': str(e)
           }
       )
       raise
   ```

### Code Organization

1. **Keep service methods focused**:
   ```python
   # Good: Single responsibility
   def get_ordered_changes(self, session_id):
       return self._query_changes(session_id).all()
   
   def filter_changes(self, session_id, **filters):
       query = self._query_changes(session_id)
       query = self._apply_filters(query, filters)
       return query.all()
   
   # Bad: Doing too much
   def get_changes(self, session_id, filters=None, page=None):
       # Complex logic mixing concerns
       ...
   ```

2. **Use helper methods for common operations**:
   ```python
   def _build_change_dict(self, change):
       """Convert Change model to dictionary"""
       return {
           'id': change.id,
           'uuid': change.object_uuid,
           # ... other fields
       }
   
   def get_ordered_changes(self, session_id):
       changes = self._query_changes(session_id).all()
       return [self._build_change_dict(c) for c in changes]
   ```

3. **Document complex logic**:
   ```python
   def order_changes(self, classification_results, dependency_graph):
       """
       Order changes by dependencies using topological sort.
       
       This ensures that:
       1. Parent objects are reviewed before children
       2. Dependencies are resolved in correct order
       3. Circular dependencies are detected and handled
       
       Args:
           classification_results: Dict of classified changes
           dependency_graph: Dict mapping UUIDs to dependencies
           
       Returns:
           List of changes in dependency order
       """
       # Implementation
       ...
   ```

## Testing

### Unit Tests

Test individual service methods:

```python
# tests/test_merge_assistant_integration.py
def test_create_session(app, test_zip_files):
    with app.app_context():
        service = ThreeWayMergeService()
        session = service.create_session(
            test_zip_files['base'],
            test_zip_files['customized'],
            test_zip_files['vendor']
        )
        
        assert session.status == 'ready'
        assert session.total_changes > 0
        
        # Verify packages created
        packages = Package.query.filter_by(session_id=session.id).all()
        assert len(packages) == 3
```

### Property-Based Tests

Test universal properties:

```python
# tests/test_merge_assistant_properties.py
from hypothesis import given, strategies as st

@given(st.integers(min_value=1, max_value=100))
def test_filter_result_consistency(session_id):
    """Property 9: Filter result consistency"""
    service = ThreeWayMergeService()
    
    # Get all changes
    all_changes = service.get_ordered_changes(session_id)
    
    # Filter by classification
    for classification in ['NO_CONFLICT', 'CONFLICT']:
        filtered = service.filter_changes(
            session_id,
            classification=classification
        )
        
        # All filtered changes should have correct classification
        assert all(c['classification'] == classification for c in filtered)
        
        # Filtered count should match manual count
        manual_count = sum(
            1 for c in all_changes 
            if c['classification'] == classification
        )
        assert len(filtered) == manual_count
```

### Integration Tests

Test complete workflows:

```python
def test_complete_merge_workflow(app, test_zip_files):
    with app.app_context():
        service = ThreeWayMergeService()
        
        # 1. Create session
        session = service.create_session(
            test_zip_files['base'],
            test_zip_files['customized'],
            test_zip_files['vendor']
        )
        
        # 2. Get summary
        summary = service.get_summary(session.id)
        assert summary['statistics']['total_changes'] > 0
        
        # 3. Filter conflicts
        conflicts = service.filter_changes(
            session.id,
            classification='CONFLICT'
        )
        
        # 4. Review changes
        for i, change in enumerate(conflicts):
            service.update_progress(
                session.id,
                change['display_order'],
                'reviewed'
            )
        
        # 5. Generate report
        report = service.generate_report(session.id)
        assert report['statistics']['reviewed'] == len(conflicts)
```

### Running Tests

```bash
# Run all tests
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test file
python -m pytest tests/test_merge_assistant_integration.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run with verbose output
python -m pytest -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test
python -m pytest tests/test_merge_assistant_properties.py::test_filter_result_consistency -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

## Debugging

### Logging

Enable detailed logging:

```python
# services/merge_assistant/logger.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Detailed debug message")
```

### Query Analysis

Analyze query performance:

```python
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService

service = ThreeWayMergeService()

# Analyze query plan
plan = service.analyze_query_plan(session_id=1, query_type='filter_changes')
for step in plan:
    print(f"Step {step['id']}: {step['detail']}")

# Verify index usage
index_usage = service.verify_index_usage(session_id=1)
for index_name, is_used in index_usage.items():
    print(f"{index_name}: {'✅' if is_used else '❌'}")
```

### Database Inspection

Inspect database state:

```python
from app import create_app
from models import db, MergeSession, Change

app = create_app()
with app.app_context():
    # Get session
    session = MergeSession.query.first()
    print(f"Session: {session.reference_id}")
    print(f"Status: {session.status}")
    print(f"Total changes: {session.total_changes}")
    
    # Get changes
    changes = Change.query.filter_by(session_id=session.id).all()
    print(f"Changes in DB: {len(changes)}")
    
    # Check for orphaned records
    orphaned = Change.query.filter(
        Change.base_object_id.is_(None),
        Change.customer_object_id.is_(None),
        Change.vendor_object_id.is_(None)
    ).all()
    print(f"Orphaned changes: {len(orphaned)}")
```

## Performance Optimization

### Query Optimization

1. **Use EXPLAIN QUERY PLAN**:
   ```python
   from sqlalchemy import text
   
   result = db.session.execute(text("""
       EXPLAIN QUERY PLAN
       SELECT * FROM changes
       WHERE session_id = 1
       AND classification = 'CONFLICT'
   """))
   
   for row in result:
       print(row)
   ```

2. **Add missing indexes**:
   ```python
   # models.py
   class Change(db.Model):
       # Add index for frequently filtered column
       new_field = db.Column(db.String(50), index=True)
   ```

3. **Use query result caching**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def get_cached_summary(session_id):
       return service.get_summary(session_id)
   ```

### Database Optimization

Run VACUUM and ANALYZE periodically:

```bash
python optimize_database.py
```

### Memory Optimization

Use pagination for large result sets:

```python
# Process changes in batches
page_size = 100
page = 1

while True:
    changes = service.get_ordered_changes(
        session_id,
        page=page,
        page_size=page_size
    )
    
    if not changes:
        break
    
    # Process batch
    for change in changes:
        process_change(change)
    
    page += 1
```

## Troubleshooting

### Common Issues

#### Issue: Slow queries

**Symptoms**: Queries taking > 1 second

**Solution**:
1. Check if indexes are being used:
   ```python
   index_usage = service.verify_index_usage(session_id)
   ```
2. Analyze query plan:
   ```python
   plan = service.analyze_query_plan(session_id, 'filter_changes')
   ```
3. Add missing indexes if needed

#### Issue: Memory errors with large sessions

**Symptoms**: Out of memory errors when loading changes

**Solution**:
1. Use pagination:
   ```python
   changes = service.get_ordered_changes(session_id, page=1, page_size=50)
   ```
2. Process in batches instead of loading all at once

#### Issue: Orphaned records

**Symptoms**: Changes without related objects

**Solution**:
1. Check for orphaned records:
   ```python
   orphaned = Change.query.filter(
       Change.base_object_id.is_(None),
       Change.customer_object_id.is_(None),
       Change.vendor_object_id.is_(None)
   ).all()
   ```
2. Re-run migration if needed:
   ```bash
   python migrate_merge_sessions.py
   ```

#### Issue: Foreign key constraint violations

**Symptoms**: IntegrityError when creating records

**Solution**:
1. Verify parent records exist before creating child records
2. Use transactions to ensure atomicity
3. Check cascade delete settings

### Debug Checklist

When debugging issues:

- [ ] Check application logs
- [ ] Verify database integrity: `PRAGMA integrity_check`
- [ ] Check for orphaned records
- [ ] Verify index usage
- [ ] Analyze query plans
- [ ] Check memory usage
- [ ] Verify foreign key constraints
- [ ] Check transaction isolation level
- [ ] Verify data migration completed
- [ ] Check for concurrent access issues

## Additional Resources

- [Schema Documentation](SCHEMA_DOCUMENTATION.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [Design Document](design.md)
- [Requirements Document](requirements.md)
- [Performance Report](PERFORMANCE_REPORT.md)

## Contributing

When contributing to the Merge Assistant feature:

1. Follow the existing code style
2. Add tests for new functionality
3. Update documentation
4. Run all tests before submitting
5. Use meaningful commit messages
6. Add logging for important operations
7. Handle errors gracefully
8. Optimize queries for performance

## Support

For questions or issues:

1. Check this developer guide
2. Review the API documentation
3. Check existing tests for examples
4. Review the design document for architecture details
