#!/usr/bin/env python
"""Verify three-way merge schema with package_id validation"""

import sqlite3
import os
import sys

# Connect to database
db_path = 'instance/docflow.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"Total tables: {len(tables)}\n")

# Check for three-way merge tables
merge_tables = [
    'merge_sessions',
    'packages',
    'object_lookup',
    'package_object_mappings',
    'delta_comparison_results',
    'changes',
    'object_versions',
    'interfaces',
    'expression_rules',
    'process_models',
    'record_types',
    'cdts',
    'integrations',
    'web_apis',
    'sites',
    'groups',
    'constants',
    'connected_systems',
    'data_stores',
    'unknown_objects'
]

print("Three-way merge tables:")
for table in merge_tables:
    if table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  ✅ {table}: {count} rows")
    else:
        print(f"  ❌ {table}: NOT FOUND")

# Validate package_id columns in object-specific tables
print("\n" + "="*60)
print("PACKAGE_ID COLUMN VALIDATION")
print("="*60)

object_tables = [
    'interfaces', 'expression_rules', 'process_models', 'record_types',
    'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
    'connected_systems', 'data_stores', 'unknown_objects'
]

validation_passed = True

for table in object_tables:
    if table not in tables:
        print(f"\n❌ {table}: TABLE NOT FOUND")
        validation_passed = False
        continue
    
    print(f"\n{table}:")
    
    # Check if package_id column exists
    cursor.execute(f"PRAGMA table_info({table})")
    columns = {row[1]: row for row in cursor.fetchall()}
    
    if 'package_id' not in columns:
        print(f"  ❌ package_id column NOT FOUND")
        validation_passed = False
        continue
    else:
        col_info = columns['package_id']
        print(f"  ✅ package_id column exists (type: {col_info[2]}, nullable: {col_info[3] == 0})")
    
    # Check foreign key constraint
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    fks = list(cursor.fetchall())
    package_fk = [fk for fk in fks if fk[3] == 'package_id']
    
    if not package_fk:
        print(f"  ❌ Foreign key constraint on package_id NOT FOUND")
        validation_passed = False
    else:
        fk = package_fk[0]
        print(f"  ✅ Foreign key: package_id -> {fk[2]}.{fk[4]} (ON DELETE {fk[6]})")
    
    # Check for NULL values (Requirement 7.1)
    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE package_id IS NULL")
    null_count = cursor.fetchone()[0]
    
    if null_count > 0:
        print(f"  ⚠️  WARNING: {null_count} rows have NULL package_id")
        validation_passed = False
    else:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        total_count = cursor.fetchone()[0]
        if total_count > 0:
            print(f"  ✅ No NULL package_id values ({total_count} rows)")
        else:
            print(f"  ℹ️  Table is empty")
    
    # Check index on package_id
    cursor.execute(f"PRAGMA index_list({table})")
    indexes = list(cursor.fetchall())
    package_indexes = [idx for idx in indexes if 'package' in idx[1].lower()]
    
    if package_indexes:
        print(f"  ✅ Indexes found: {', '.join([idx[1] for idx in package_indexes])}")
    else:
        print(f"  ⚠️  WARNING: No indexes found on package_id")

# Verify object_lookup does NOT have package_id
print("\n" + "="*60)
print("OBJECT_LOOKUP VALIDATION (should NOT have package_id)")
print("="*60)

if 'object_lookup' in tables:
    cursor.execute("PRAGMA table_info(object_lookup)")
    columns = {row[1]: row for row in cursor.fetchall()}
    
    if 'package_id' in columns:
        print("❌ CRITICAL: object_lookup has package_id column (should be package-agnostic!)")
        validation_passed = False
    else:
        print("✅ object_lookup is package-agnostic (no package_id column)")

conn.close()

# Now create missing tables if needed
from app import create_app
from models import db

app = create_app()
with app.app_context():
    print("\n" + "="*60)
    print("ENSURING ALL TABLES EXIST")
    print("="*60)
    db.create_all()
    print("✅ All tables created/verified!")

# Final summary
print("\n" + "="*60)
print("VALIDATION SUMMARY")
print("="*60)

if validation_passed:
    print("✅ All validations PASSED")
    sys.exit(0)
else:
    print("❌ Some validations FAILED - see details above")
    sys.exit(1)
