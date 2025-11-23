# Merge Assistant Normalized Schema Documentation

## Overview

The Merge Assistant feature uses a fully normalized relational database schema to store three-way merge session data. This document describes the final schema structure after the data model refactoring completed in November 2023.

## Schema Architecture

### Entity Relationship Overview

```
MergeSession (1) ----< (3) Package
    |
    |
    +----< (many) Change
              |
              +----< (1) ChangeReview
              |
              +----< (1) MergeGuidance
                      |
                      +----< (many) MergeConflict
                      |
                      +----< (many) MergeChange

Package (1) ----< (many) AppianObject
    |                      |
    |                      +----< (1) ProcessModelMetadata
    |                                  |
    |                                  +----< (many) ProcessModelNode
    |                                  |
    |                                  +----< (many) ProcessModelFlow
    |
    +----< (many) PackageObjectTypeCount
    |
    +----< (many) ObjectDependency
```

## Core Tables

### MergeSession

Stores session-level metadata without any JSON blobs.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `reference_id` (VARCHAR(20), UNIQUE, INDEXED) - Human-readable ID (e.g., MRG_001)
- `base_package_name` (VARCHAR(255)) - Name of base package (A)
- `customized_package_name` (VARCHAR(255)) - Name of customized package (B)
- `new_vendor_package_name` (VARCHAR(255)) - Name of new vendor package (C)
- `status` (VARCHAR(20), INDEXED) - Session status (processing, ready, in_progress, completed, error)
- `current_change_index` (INTEGER) - Current position in change list
- `total_changes` (INTEGER) - Total number of changes
- `reviewed_count` (INTEGER) - Number of reviewed changes
- `skipped_count` (INTEGER) - Number of skipped changes
- `created_at` (DATETIME) - Creation timestamp
- `updated_at` (DATETIME) - Last update timestamp
- `completed_at` (DATETIME) - Completion timestamp
- `total_time` (INTEGER) - Total processing time in seconds
- `error_log` (TEXT) - Error messages if any

**Relationships:**
- One-to-many with Package (3 packages per session)
- One-to-many with Change
- One-to-many with ChangeReview

**Indexes:**
- `idx_merge_sessions_reference_id` on `reference_id`

### Package

Stores individual package information (A, B, or C).

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `session_id` (INTEGER, FK, INDEXED) - Foreign key to MergeSession
- `package_type` (VARCHAR(20)) - Type: 'base', 'customized', or 'new_vendor'
- `package_name` (VARCHAR(255)) - Package name
- `total_objects` (INTEGER) - Total number of objects in package
- `generation_time` (FLOAT) - Time taken to generate blueprint
- `created_at` (DATETIME) - Creation timestamp

**Relationships:**
- Many-to-one with MergeSession
- One-to-many with AppianObject
- One-to-many with PackageObjectTypeCount
- One-to-many with ObjectDependency

**Indexes:**
- `idx_package_session_type` on `(session_id, package_type)`

### AppianObject

Stores normalized Appian object data.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `package_id` (INTEGER, FK, INDEXED) - Foreign key to Package
- `uuid` (VARCHAR(255), INDEXED) - Appian object UUID
- `name` (VARCHAR(500), INDEXED) - Object name
- `object_type` (VARCHAR(50), INDEXED) - Object type (Interface, Process Model, etc.)
- `sail_code` (TEXT) - SAIL code for interfaces and expression rules
- `fields` (TEXT) - JSON string of field definitions
- `properties` (TEXT) - JSON string of object properties
- `object_metadata` (TEXT) - JSON string of additional metadata
- `version_uuid` (VARCHAR(255), INDEXED) - Version UUID
- `created_at` (DATETIME) - Creation timestamp

**Relationships:**
- Many-to-one with Package
- One-to-one with ProcessModelMetadata (for process models only)
- One-to-many with ObjectDependency (as parent)
- One-to-many with ObjectDependency (as child)

**Indexes:**
- `uq_package_object` unique constraint on `(package_id, uuid)`
- `idx_object_type_name` on `(object_type, name)`
- `idx_object_uuid` on `uuid`

### Change

Stores individual change records from comparison.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `session_id` (INTEGER, FK, INDEXED) - Foreign key to MergeSession
- `object_uuid` (VARCHAR(255), INDEXED) - Object UUID
- `object_name` (VARCHAR(500), INDEXED) - Object name
- `object_type` (VARCHAR(50), INDEXED) - Object type
- `classification` (VARCHAR(50), INDEXED) - Change classification (NO_CONFLICT, CONFLICT, CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED)
- `change_type` (VARCHAR(20)) - Change type (ADDED, MODIFIED, REMOVED)
- `vendor_change_type` (VARCHAR(20)) - A→C change type
- `customer_change_type` (VARCHAR(20)) - A→B change type
- `base_object_id` (INTEGER, FK, INDEXED) - Foreign key to AppianObject (base version)
- `customer_object_id` (INTEGER, FK, INDEXED) - Foreign key to AppianObject (customer version)
- `vendor_object_id` (INTEGER, FK, INDEXED) - Foreign key to AppianObject (vendor version)
- `display_order` (INTEGER, INDEXED) - Order for display (dependency-aware)
- `created_at` (DATETIME) - Creation timestamp

**Relationships:**
- Many-to-one with MergeSession
- Many-to-one with AppianObject (base_object)
- Many-to-one with AppianObject (customer_object)
- Many-to-one with AppianObject (vendor_object)
- One-to-one with MergeGuidance
- One-to-one with ChangeReview

**Indexes:**
- `idx_change_session_classification` on `(session_id, classification)`
- `idx_change_session_type` on `(session_id, object_type)`
- `idx_change_session_order` on `(session_id, display_order)`

### ChangeReview

Stores user review actions for each change.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `session_id` (INTEGER, FK, INDEXED) - Foreign key to MergeSession
- `change_id` (INTEGER, FK, UNIQUE, INDEXED) - Foreign key to Change
- `review_status` (VARCHAR(20), INDEXED) - Status: 'pending', 'reviewed', or 'skipped'
- `user_notes` (TEXT) - Optional user notes
- `reviewed_at` (DATETIME) - Review timestamp
- `created_at` (DATETIME) - Creation timestamp

**Relationships:**
- Many-to-one with MergeSession
- One-to-one with Change

**Indexes:**
- `idx_review_session_status` on `(session_id, review_status)`

## Supporting Tables

### PackageObjectTypeCount

Stores object type counts for each package.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `package_id` (INTEGER, FK, INDEXED) - Foreign key to Package
- `object_type` (VARCHAR(50)) - Object type
- `count` (INTEGER) - Number of objects of this type
- `created_at` (DATETIME) - Creation timestamp

**Indexes:**
- `uq_package_object_type` unique constraint on `(package_id, object_type)`
- `idx_package_type` on `(package_id, object_type)`

### ProcessModelMetadata

Stores process model-specific metadata.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `appian_object_id` (INTEGER, FK, UNIQUE, INDEXED) - Foreign key to AppianObject
- `total_nodes` (INTEGER) - Total number of nodes
- `total_flows` (INTEGER) - Total number of flows
- `complexity_score` (FLOAT) - Calculated complexity score
- `created_at` (DATETIME) - Creation timestamp

**Relationships:**
- One-to-one with AppianObject
- One-to-many with ProcessModelNode
- One-to-many with ProcessModelFlow

### ProcessModelNode

Stores individual process model nodes.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `process_model_id` (INTEGER, FK, INDEXED) - Foreign key to ProcessModelMetadata
- `node_id` (VARCHAR(255)) - Node identifier
- `node_type` (VARCHAR(100)) - Node type
- `node_name` (VARCHAR(500)) - Node name
- `properties` (TEXT) - JSON string of node properties
- `created_at` (DATETIME) - Creation timestamp

**Indexes:**
- `uq_process_model_node` unique constraint on `(process_model_id, node_id)`
- `idx_node_type` on `(process_model_id, node_type)`

### ProcessModelFlow

Stores process model flows (connections between nodes).

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `process_model_id` (INTEGER, FK, INDEXED) - Foreign key to ProcessModelMetadata
- `from_node_id` (INTEGER, FK, INDEXED) - Foreign key to ProcessModelNode (source)
- `to_node_id` (INTEGER, FK, INDEXED) - Foreign key to ProcessModelNode (target)
- `flow_label` (VARCHAR(500)) - Flow label
- `flow_condition` (TEXT) - Flow condition
- `created_at` (DATETIME) - Creation timestamp

**Indexes:**
- `idx_flow_from` on `(process_model_id, from_node_id)`
- `idx_flow_to` on `(process_model_id, to_node_id)`

### ObjectDependency

Stores relationships between Appian objects.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `package_id` (INTEGER, FK, INDEXED) - Foreign key to Package
- `parent_uuid` (VARCHAR(255), INDEXED) - Parent object UUID
- `child_uuid` (VARCHAR(255), INDEXED) - Child object UUID
- `dependency_type` (VARCHAR(50)) - Dependency type (reference, contains, etc.)
- `created_at` (DATETIME) - Creation timestamp

**Indexes:**
- `idx_dependency_parent` on `(package_id, parent_uuid)`
- `idx_dependency_child` on `(package_id, child_uuid)`
- `uq_dependency` unique constraint on `(package_id, parent_uuid, child_uuid)`

### MergeGuidance

Stores merge guidance for a change.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `change_id` (INTEGER, FK, UNIQUE, INDEXED) - Foreign key to Change
- `recommendation` (VARCHAR(100)) - Recommendation (ACCEPT_VENDOR, MANUAL_MERGE, etc.)
- `reason` (TEXT) - Reason for recommendation
- `created_at` (DATETIME) - Creation timestamp

**Relationships:**
- One-to-one with Change
- One-to-many with MergeConflict
- One-to-many with MergeChange

### MergeConflict

Stores individual conflicts within merge guidance.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `guidance_id` (INTEGER, FK, INDEXED) - Foreign key to MergeGuidance
- `field_name` (VARCHAR(255)) - Field name
- `conflict_type` (VARCHAR(100)) - Conflict type
- `description` (TEXT) - Conflict description
- `created_at` (DATETIME) - Creation timestamp

### MergeChange

Stores individual changes within merge guidance.

**Columns:**
- `id` (INTEGER, PK) - Primary key
- `guidance_id` (INTEGER, FK, INDEXED) - Foreign key to MergeGuidance
- `field_name` (VARCHAR(255)) - Field name
- `change_description` (TEXT) - Change description
- `old_value` (TEXT) - Old value
- `new_value` (TEXT) - New value
- `created_at` (DATETIME) - Creation timestamp

## Query Patterns

### Get All Changes for a Session (Ordered)

```sql
SELECT c.*, 
       ao_base.*, 
       ao_customer.*, 
       ao_vendor.*,
       mg.*,
       cr.*
FROM changes c
LEFT JOIN appian_objects ao_base ON c.base_object_id = ao_base.id
LEFT JOIN appian_objects ao_customer ON c.customer_object_id = ao_customer.id
LEFT JOIN appian_objects ao_vendor ON c.vendor_object_id = ao_vendor.id
LEFT JOIN merge_guidance mg ON c.id = mg.change_id
LEFT JOIN change_reviews cr ON c.id = cr.change_id
WHERE c.session_id = ?
ORDER BY c.display_order
```

### Filter Changes by Classification

```sql
SELECT c.*
FROM changes c
WHERE c.session_id = ?
  AND c.classification = ?
ORDER BY c.display_order
```

### Get Session Statistics

```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN classification = 'NO_CONFLICT' THEN 1 ELSE 0 END) as no_conflict,
    SUM(CASE WHEN classification = 'CONFLICT' THEN 1 ELSE 0 END) as conflict,
    SUM(CASE WHEN classification = 'CUSTOMER_ONLY' THEN 1 ELSE 0 END) as customer_only,
    SUM(CASE WHEN classification = 'REMOVED_BUT_CUSTOMIZED' THEN 1 ELSE 0 END) as removed_but_customized
FROM changes
WHERE session_id = ?
```

### Search Changes by Object Name

```sql
SELECT c.*
FROM changes c
WHERE c.session_id = ?
  AND c.object_name LIKE ?
ORDER BY c.display_order
```

## Performance Characteristics

### Index Usage

All queries use appropriate indexes for optimal performance:

- Session-based queries use `idx_change_session_*` indexes
- Classification filters use `idx_change_session_classification`
- Object type filters use `idx_change_session_type`
- Ordering uses `idx_change_session_order`
- Review status filters use `idx_review_session_status`

### Query Performance

Compared to the old JSON-based schema:

- **Filter operations**: 10x faster (uses indexed columns instead of JSON parsing)
- **Search operations**: 20x faster (uses indexed LIKE queries)
- **Report generation**: 5x faster (uses SQL aggregates)
- **Change loading**: 3x faster (uses JOIN queries with eager loading)

### Database Size

The normalized schema reduces database size by approximately 30-40% compared to the JSON-based schema due to:

- Elimination of duplicate data in JSON blobs
- More efficient storage of structured data
- Better compression of normalized tables

## Migration Notes

### Migration Process

1. All existing sessions were migrated from JSON columns to normalized tables
2. Data integrity was verified for each session
3. Old JSON columns were dropped after successful migration
4. Application was tested to ensure all functionality works with new schema

### Backward Compatibility

The migration maintains full backward compatibility:

- All API endpoints return the same data structure
- All UI components work identically
- All functionality is preserved

### Verification

Migration verification checks:

- Package count equals 3 for each session
- Object counts match blueprint metadata
- Change counts match ordered changes length
- All foreign keys are valid
- No orphaned records exist

## API Usage

### Creating a Session

```python
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService

service = ThreeWayMergeService()
session = service.create_session(
    base_zip_path='path/to/base.zip',
    customized_zip_path='path/to/customized.zip',
    new_vendor_zip_path='path/to/new_vendor.zip'
)
```

### Getting Changes

```python
# Get all changes
changes = service.get_ordered_changes(session.id)

# Get changes with pagination
changes = service.get_ordered_changes(session.id, page=1, page_size=50)

# Filter changes
changes = service.filter_changes(
    session.id,
    classification='CONFLICT',
    object_type='Interface',
    search_term='vendor'
)
```

### Getting Summary

```python
summary = service.get_summary(session.id)
# Returns: {
#     'session_id': int,
#     'reference_id': str,
#     'packages': {...},
#     'statistics': {...},
#     'breakdown_by_type': {...},
#     'estimated_complexity': str,
#     'estimated_time_hours': int
# }
```

### Updating Progress

```python
service.update_progress(
    session_id=session.id,
    change_index=0,
    review_status='reviewed',
    notes='Looks good'
)
```

### Generating Report

```python
report = service.generate_report(session.id)
# Returns complete merge report with all changes and statistics
```

## Maintenance

### Database Optimization

Run VACUUM periodically to reclaim space and optimize performance:

```sql
VACUUM;
ANALYZE;
```

### Index Maintenance

Indexes are automatically maintained by SQLite. No manual maintenance required.

### Backup

Regular backups should be performed before major operations:

```bash
python -c "from app import create_app; from models import db; import shutil; app = create_app(); shutil.copy('instance/docflow.db', 'backups/docflow_backup.db')"
```

## Troubleshooting

### Slow Queries

Use EXPLAIN QUERY PLAN to analyze query performance:

```python
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService

service = ThreeWayMergeService()
plan = service.analyze_query_plan(session_id, 'filter_changes')
```

### Missing Data

Verify data integrity:

```python
from services.merge_assistant.migration_service import MigrationService

migration_service = MigrationService()
verification = migration_service.verify_migration(session_id)
```

### Performance Issues

Check index usage:

```python
index_usage = service.verify_index_usage(session_id)
# Returns which indexes are being used by queries
```

## Future Enhancements

The normalized schema supports future enhancements:

1. **Versioning**: Track changes to objects over time
2. **Audit Trails**: Record all user actions
3. **Advanced Analytics**: Complex reporting queries
4. **Caching**: Query result caching for repeated queries
5. **Partitioning**: Partition large tables by session_id

## References

- Design Document: `.kiro/specs/merge-assistant-data-model-refactoring/design.md`
- Requirements Document: `.kiro/specs/merge-assistant-data-model-refactoring/requirements.md`
- Migration Guide: `MIGRATION_GUIDE.md`
- Performance Report: `.kiro/specs/merge-assistant-data-model-refactoring/PERFORMANCE_REPORT.md`
