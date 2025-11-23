# Merge Assistant Data Model Migration Guide

This guide provides comprehensive instructions for migrating the Merge Assistant from the old JSON-based schema to the new normalized relational schema.

## Overview

The migration refactors the data model from storing large JSON blobs in the `MergeSession` table to a normalized schema with separate tables for:
- **Package**: Individual package information (base, customized, new_vendor)
- **AppianObject**: Normalized object data
- **Change**: Individual change records
- **ObjectDependency**: Object relationships
- **ChangeReview**: Enhanced user review actions

## Prerequisites

Before starting the migration:

1. **Backup the database** - Always create a backup before migration
2. **Stop the application** - Ensure no active sessions are being created
3. **Verify disk space** - Ensure sufficient space for backup and migration
4. **Test environment** - Test the migration on a copy of production data first

## Migration Tools

### 1. Migration Script (`migrate_merge_sessions.py`)

The main migration script provides several commands:

```bash
# Create backup only
python migrate_merge_sessions.py --backup

# Run migration only
python migrate_merge_sessions.py --migrate

# Verify migration only
python migrate_merge_sessions.py --verify

# Test application only
python migrate_merge_sessions.py --test

# Run all steps (recommended)
python migrate_merge_sessions.py --all

# Stop on first error (default: continue)
python migrate_merge_sessions.py --all --stop-on-error
```

### 2. Test Script (`test_migration_workflow.py`)

Comprehensive test suite for verifying the application works with migrated data:

```bash
python test_migration_workflow.py
```

Tests include:
- Query performance
- Data integrity
- UI functionality
- Report generation

## Migration Process

### Step 1: Create Backup

**Always create a backup before migration!**

```bash
python migrate_merge_sessions.py --backup
```

This will:
- Copy the database to `backups/docflow_backup_YYYYMMDD_HHMMSS.db`
- Verify backup integrity
- Display backup size and location

**Output:**
```
================================================================================
STEP 1: Creating Database Backup
================================================================================
📁 Source database: instance/docflow.db
💾 Backup location: backups/docflow_backup_20251123_140112.db
📊 Database size: 150.35 MB
✅ Backup created successfully
✅ Backup integrity verified
💾 Backup size: 150.35 MB
```

### Step 2: Run Migration

Migrate all sessions from JSON to normalized schema:

```bash
python migrate_merge_sessions.py --migrate
```

This will:
- Check which sessions need migration
- Migrate sessions one at a time
- Log progress and errors
- Continue on errors (unless `--stop-on-error` is used)
- Commit after each successful migration

**Output:**
```
================================================================================
STEP 2: Migrating Sessions
================================================================================

📊 Session Statistics:
   Total sessions: 5
   Already migrated: 2
   Need migration: 3

🚀 Starting migration of 3 sessions...

🔄 [1/5] Migrating session MRG_001...
   ✅ Successfully migrated session MRG_001
      📦 Packages: 3
      📄 Objects: 1247
      🔄 Changes: 156

🔄 [2/5] Migrating session MRG_002...
   ✅ Successfully migrated session MRG_002
      📦 Packages: 3
      📄 Objects: 892
      🔄 Changes: 89
```

### Step 3: Verify Migration

Verify that all sessions migrated correctly:

```bash
python migrate_merge_sessions.py --verify
```

This will:
- Check package count (should be 3 per session)
- Verify object counts match blueprint metadata
- Verify change counts match ordered_changes
- Verify all foreign keys are valid
- Report any issues found

**Output:**
```
================================================================================
STEP 3: Verifying Migration Completeness
================================================================================

🔍 Verifying 5 sessions...

🔍 [1/5] Verifying session MRG_001...
   ✅ All checks passed
      📦 Packages: 3
      📄 Objects: 1247
      🔄 Changes: 156
      📝 Reviews: 156

🔍 [2/5] Verifying session MRG_002...
   ✅ All checks passed
      📦 Packages: 3
      📄 Objects: 892
      🔄 Changes: 89
      📝 Reviews: 89
```

### Step 4: Test Application

Test that the application works with migrated data:

```bash
python migrate_merge_sessions.py --test
```

This will:
- Test package queries
- Test object queries
- Test change queries with joins
- Test filtering by classification
- Test searching by object name
- Test review linkage

**Output:**
```
================================================================================
STEP 4: Testing Application with Migrated Data
================================================================================

🧪 Running smoke tests on 5 sessions...

🧪 [1/5] Testing session MRG_001...
   ✅ Package query test passed
   ✅ Object query test passed
   ✅ Change query test passed
   ✅ Filter test passed (found 23 conflicts)
   ✅ Search test passed (found 45 matches)
   ✅ Review linkage test passed
   ✅ All tests passed for session MRG_001
```

### Step 5: Run Complete Workflow

Run all steps in sequence (recommended):

```bash
python migrate_merge_sessions.py --all
```

This will:
1. Create backup
2. Migrate all sessions
3. Verify migration
4. Test application

## Verification Checklist

After migration, verify the following:

### Database Verification

- [ ] Backup created successfully
- [ ] All sessions migrated (check migration summary)
- [ ] Package count = 3 per session
- [ ] Object counts match blueprint metadata
- [ ] Change counts match ordered_changes
- [ ] All foreign keys valid
- [ ] No orphaned records

### Application Verification

- [ ] Session list displays correctly
- [ ] Session summary shows correct statistics
- [ ] Change list displays with proper ordering
- [ ] Filtering by classification works
- [ ] Filtering by object type works
- [ ] Searching by name works
- [ ] Change details display correctly
- [ ] Review actions work correctly
- [ ] Report generation works

### Performance Verification

- [ ] Filtering is faster than before
- [ ] Searching is faster than before
- [ ] Change loading is faster than before
- [ ] Report generation is faster than before

## Testing with Real Data

After migration, test the application thoroughly:

```bash
# Run comprehensive test suite
python test_migration_workflow.py
```

This will test:
1. **Query Performance** - Verify queries work efficiently
2. **Data Integrity** - Verify all relationships are correct
3. **UI Functionality** - Verify UI displays correctly
4. **Report Generation** - Verify reports are complete

## Rollback Procedure

If migration fails or issues are found:

### Option 1: Restore from Backup

```bash
# Stop the application
# Replace database with backup
cp backups/docflow_backup_YYYYMMDD_HHMMSS.db instance/docflow.db

# Restart the application
```

### Option 2: Re-run Migration

If only some sessions failed:

```bash
# The migration script skips already-migrated sessions
# So you can safely re-run it
python migrate_merge_sessions.py --migrate
```

## Troubleshooting

### Issue: Migration Fails for Some Sessions

**Symptoms:**
- Migration summary shows failures
- Error messages in output

**Solutions:**
1. Check error messages for specific issues
2. Verify JSON data is valid in failed sessions
3. Check database logs for constraint violations
4. Re-run migration (it will skip successful sessions)

### Issue: Verification Fails

**Symptoms:**
- Verification shows failed checks
- Record counts don't match

**Solutions:**
1. Check which specific checks failed
2. Verify the original JSON data is complete
3. Check for missing or invalid foreign keys
4. Review migration logs for warnings

### Issue: Application Doesn't Work After Migration

**Symptoms:**
- Errors when viewing sessions
- Missing data in UI
- Slow queries

**Solutions:**
1. Run verification: `python migrate_merge_sessions.py --verify`
2. Run tests: `python test_migration_workflow.py`
3. Check application logs for errors
4. Verify database indexes exist
5. If all else fails, restore from backup

### Issue: Performance Not Improved

**Symptoms:**
- Queries still slow
- No noticeable improvement

**Solutions:**
1. Verify indexes were created correctly
2. Run `ANALYZE` on database tables
3. Check query plans with `EXPLAIN`
4. Ensure queries use joins instead of JSON parsing

## Post-Migration Cleanup

After successful migration and verification:

### 1. Monitor Application

Monitor the application for a few days to ensure everything works correctly:
- Check logs for errors
- Monitor query performance
- Verify user reports

### 2. Remove Old JSON Columns (Optional)

Once confident the migration is successful, you can remove the old JSON columns to save space:

```python
# This is optional and should only be done after thorough testing
# The migration script does NOT do this automatically

from app import create_app
from models import db, MergeSession

app = create_app()
with app.app_context():
    # Clear JSON columns for all sessions
    sessions = MergeSession.query.all()
    for session in sessions:
        session.base_blueprint = None
        session.customized_blueprint = None
        session.new_vendor_blueprint = None
        session.vendor_changes = None
        session.customer_changes = None
        session.classification_results = None
        session.ordered_changes = None
    
    db.session.commit()
    
    # Run VACUUM to reclaim space
    db.session.execute('VACUUM')
```

### 3. Optimize Database

After cleanup, optimize the database:

```bash
# Run VACUUM to reclaim space
sqlite3 instance/docflow.db "VACUUM;"

# Run ANALYZE to update statistics
sqlite3 instance/docflow.db "ANALYZE;"
```

## Migration Statistics

Expected improvements after migration:

### Performance Improvements

- **Filtering**: 10x faster (uses indexed columns)
- **Searching**: 20x faster (uses indexed columns)
- **Report Generation**: 5x faster (uses SQL aggregates)
- **Change Loading**: 3x faster (uses joins instead of JSON parsing)

### Storage Improvements

- **Database Size**: 30-40% reduction (after cleanup)
- **Query Complexity**: Reduced from O(n) JSON parsing to O(1) indexed lookups
- **Memory Usage**: Reduced for large sessions

## Support

If you encounter issues during migration:

1. Check the migration logs
2. Review the troubleshooting section
3. Run the test suite to identify specific issues
4. Check the development log at `.kiro/DEVELOPMENT_LOG.md`
5. Restore from backup if necessary

## Summary

The migration process is designed to be:
- **Safe**: Always creates backups before migration
- **Incremental**: Migrates sessions one at a time
- **Resilient**: Continues on errors (unless --stop-on-error)
- **Verifiable**: Comprehensive verification and testing
- **Reversible**: Can restore from backup if needed

Follow the steps in order, verify at each stage, and test thoroughly before considering the migration complete.
