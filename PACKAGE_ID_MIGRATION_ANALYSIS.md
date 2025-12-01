# Package ID Migration Analysis

## Problem Statement

**Issue Identified:** Object-specific tables (interfaces, expression_rules, process_models, etc.) currently store multiple entries for the same object when it appears in different packages, but there's no way to identify which package each entry belongs to.

**Current Behavior:**
```sql
-- Object stored once in object_lookup
SELECT * FROM object_lookup WHERE uuid = 'abc-123';
-- Returns: id=1, uuid='abc-123', name='MyInterface', object_type='Interface'

-- But object-specific table has 3 entries (one per package)
SELECT * FROM interfaces WHERE object_id = 1;
-- Returns 3 rows with identical object_id but different data from each package
-- Problem: No way to know which row belongs to which package!
```

**Impact:**
- Queries like `Interface.query.filter_by(object_id=1).all()` return 3 rows
- No way to distinguish which row is from Base, Customized, or New Vendor package
- Makes package-specific queries impossible
- Export and comparison logic becomes ambiguous

## Solution: Add package_id Column

Add `package_id` foreign key to all object-specific tables to explicitly link each entry to its source package.

**New Behavior:**
```sql
-- Object-specific table with package_id
SELECT * FROM interfaces WHERE object_id = 1;
-- Returns 3 rows:
-- id=1, object_id=1, package_id=1 (Base)
-- id=2, object_id=1, package_id=2 (Customized)  
-- id=3, object_id=1, package_id=3 (New Vendor)

-- Now we can query package-specific data
SELECT * FROM interfaces WHERE object_id = 1 AND package_id = 2;
-- Returns only the Customized version
```

---

## Architecture Impact Analysis

### Design Principle Changes

**BEFORE:**
- ❌ Object-specific tables had NO package identification
- ❌ Relied on implicit ordering or external context
- ❌ Queries returned all versions without distinction

**AFTER:**
- ✅ Object-specific tables explicitly linked to packages
- ✅ Package-specific queries become straightforward
- ✅ Maintains "no duplication" principle in object_lookup
- ✅ Explicit package membership via both package_object_mappings AND object-specific tables

**Key Principle Maintained:**
- `object_lookup` remains package-agnostic (NO package_id there!)
- Package membership tracked via `package_object_mappings` junction table
- Object-specific tables now also track package_id for version-specific data

---

## Files Requiring Changes

### 1. Database Models (models.py)

**Tables to Modify (13 main tables + 8 child tables):**

#### Main Object Tables (Add package_id + unique constraint):
1. `interfaces` - Add package_id, unique(object_id, package_id)
2. `expression_rules` - Add package_id, unique(object_id, package_id)
3. `process_models` - Add package_id, unique(object_id, package_id)
4. `record_types` - Add package_id, unique(object_id, package_id)
5. `cdts` - Add package_id, unique(object_id, package_id)
6. `integrations` - Add package_id, unique(object_id, package_id)
7. `web_apis` - Add package_id, unique(object_id, package_id)
8. `sites` - Add package_id, unique(object_id, package_id)
9. `groups` - Add package_id, unique(object_id, package_id)
10. `constants` - Add package_id, unique(object_id, package_id)
11. `connected_systems` - Add package_id, unique(object_id, package_id)
12. `data_stores` - Add package_id, unique(object_id, package_id)
13. `unknown_objects` - Add package_id, unique(object_id, package_id)

#### Child Tables (NO changes needed):
- `interface_parameters` - Links to interfaces.id (cascade handles it)
- `interface_security` - Links to interfaces.id (cascade handles it)
- `expression_rule_inputs` - Links to expression_rules.id (cascade handles it)
- `process_model_nodes` - Links to process_models.id (cascade handles it)
- `process_model_flows` - Links to process_models.id (cascade handles it)
- `process_model_variables` - Links to process_models.id (cascade handles it)
- `record_type_fields` - Links to record_types.id (cascade handles it)
- `record_type_relationships` - Links to record_types.id (cascade handles it)
- `record_type_views` - Links to record_types.id (cascade handles it)
- `record_type_actions` - Links to record_types.id (cascade handles it)
- `cdt_fields` - Links to cdts.id (cascade handles it)
- `data_store_entities` - Links to data_stores.id (cascade handles it)

**Changes Required in models.py:**

```python
class Interface(db.Model):
    """Interface objects"""
    __tablename__ = 'interfaces'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)  # NEW
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    sail_code = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    parameters = db.relationship('InterfaceParameter', backref='interface', lazy='dynamic', cascade='all, delete-orphan')
    security = db.relationship('InterfaceSecurity', backref='interface', lazy='dynamic', cascade='all, delete-orphan')
    
    # NEW: Unique constraint
    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_interface_object_package'),
        db.Index('idx_interface_object_package', 'object_id', 'package_id'),
    )
```

**Apply same pattern to all 13 object-specific tables.**

---

### 2. Migration Script (NEW FILE)

**File:** `migrations/migration_004_add_package_id_to_objects.py`

**Purpose:** Add package_id column to all object-specific tables

**Steps:**
1. Add package_id column to each table (nullable initially)
2. Populate package_id from existing data using object_versions table
3. Make package_id NOT NULL
4. Add unique constraint (object_id, package_id)
5. Add index on (object_id, package_id)

**Data Migration Logic:**
```sql
-- For each object-specific table, populate package_id from object_versions
UPDATE interfaces i
SET package_id = (
    SELECT ov.package_id 
    FROM object_versions ov 
    WHERE ov.object_id = i.object_id 
    AND ov.version_uuid = i.version_uuid
    LIMIT 1
);
```

---

### 3. Package Extraction Service

**File:** `services/package_extraction_service.py`

**Changes Required:**

#### Method: `_store_interface_data()`
```python
def _store_interface_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
    """Store Interface-specific data."""
    from models import Interface, InterfaceParameter, InterfaceSecurity
    
    interface = Interface(
        object_id=object_id,
        package_id=package_id,  # NEW PARAMETER
        uuid=data['uuid'],
        name=data['name'],
        version_uuid=data.get('version_uuid'),
        sail_code=data.get('sail_code'),
        description=data.get('description')
    )
    db.session.add(interface)
    db.session.flush()
    # ... rest of method
```

**Apply to all 13 `_store_*_data()` methods:**
- `_store_interface_data()`
- `_store_expression_rule_data()`
- `_store_process_model_data()`
- `_store_record_type_data()`
- `_store_cdt_data()`
- `_store_integration_data()`
- `_store_web_api_data()`
- `_store_site_data()`
- `_store_group_data()`
- `_store_constant_data()`
- `_store_connected_system_data()`
- `_store_unknown_object_data()`

#### Method: `_store_object_specific_data()`
```python
def _store_object_specific_data(
    self,
    object_id: int,
    package_id: int,  # NEW PARAMETER
    object_type: str,
    parsed_data: Dict[str, Any]
) -> None:
    """Store object-specific data in type-specific tables."""
    try:
        if object_type == 'Interface':
            self._store_interface_data(object_id, package_id, parsed_data)  # Pass package_id
        elif object_type == 'Expression Rule':
            self._store_expression_rule_data(object_id, package_id, parsed_data)
        # ... etc for all types
```

#### Method: `_process_object()`
```python
def _process_object(
    self,
    package_id: int,
    xml_path: str
) -> Optional[ObjectLookup]:
    """Process single object from XML file."""
    # ... existing code ...
    
    # Step 5c: Store object-specific data
    self._store_object_specific_data(obj_lookup.id, package_id, object_type, parsed_data)  # Pass package_id
    
    # ... rest of method
```

---

### 4. All Object Repositories (13 files)

**Files to Modify:**
1. `repositories/interface_repository.py`
2. `repositories/expression_rule_repository.py`
3. `repositories/process_model_repository.py`
4. `repositories/record_type_repository.py`
5. `repositories/cdt_repository.py`
6. `repositories/integration_repository.py`
7. `repositories/web_api_repository.py`
8. `repositories/site_repository.py`
9. `repositories/group_repository.py`
10. `repositories/constant_repository.py`
11. `repositories/connected_system_repository.py`
12. `repositories/unknown_object_repository.py`
13. (NEW) `repositories/data_store_repository.py` (if not exists)

**Changes Required:**

#### Add package_id parameter to create methods:
```python
def create_interface(
    self,
    object_id: int,
    package_id: int,  # NEW PARAMETER
    uuid: str,
    name: str,
    version_uuid: Optional[str] = None,
    sail_code: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[List[Dict[str, Any]]] = None,
    security: Optional[List[Dict[str, Any]]] = None
) -> Interface:
    """Create interface with parameters and security settings."""
    interface = Interface(
        object_id=object_id,
        package_id=package_id,  # NEW FIELD
        uuid=uuid,
        name=name,
        version_uuid=version_uuid,
        sail_code=sail_code,
        description=description
    )
    # ... rest of method
```

#### Add new query methods:
```python
def get_by_object_and_package(self, object_id: int, package_id: int) -> Optional[Interface]:
    """
    Get interface by object_lookup ID and package ID.
    
    Args:
        object_id: Object lookup ID
        package_id: Package ID
    
    Returns:
        Interface or None if not found
    """
    return self.find_one(object_id=object_id, package_id=package_id)

def get_all_by_object_id(self, object_id: int) -> List[Interface]:
    """
    Get all interfaces for an object across all packages.
    
    Args:
        object_id: Object lookup ID
    
    Returns:
        List of Interface objects (one per package)
    """
    return self.find_all(object_id=object_id)
```

**Apply to all 13 repositories.**

---

### 5. Export Scripts (2 files)

**Files to Modify:**
1. `export_merge_session.py`
2. `export_session_flat.py`

**Changes Required:**

#### export_merge_session.py
```python
def export_object_details(object_id, object_type, package_id=None):
    """
    Export detailed object information.
    
    Args:
        object_id: Object lookup ID
        object_type: Object type
        package_id: Optional package ID to get specific version
    """
    # Query the appropriate table based on object type
    if object_type == 'interface':
        if package_id:
            interface = Interface.query.filter_by(
                object_id=object_id, 
                package_id=package_id
            ).first()
        else:
            interface = Interface.query.filter_by(object_id=object_id).first()
        return export_interface_details(interface.id) if interface else None
    
    # ... apply to all object types
```

#### export_session_flat.py
```python
# When exporting, need to specify which package version to export
# OR export all versions with package identification

for change in changes:
    object_id = change.object_id
    object_type = change.object.object_type.lower().replace(' ', '')
    
    if object_type == 'interface':
        # Export all package versions
        interfaces = Interface.query.filter_by(object_id=object_id).all()
        for interface in interfaces:
            export_data['interfaces'].append({
                **serialize_model(interface),
                'package_type': get_package_type(interface.package_id)  # Helper function
            })
```

---

### 6. Comparison Services (Potential Impact)

**Files to Review:**
1. `services/delta_comparison_service.py`
2. `services/customer_comparison_service.py`
3. `services/merge_guidance_service.py`

**Changes Required:**

These services compare objects across packages. They currently use `object_versions` table for version-specific data. With package_id in object-specific tables, they can now directly query:

```python
# OLD WAY: Query object_versions for version-specific data
base_version = ObjectVersion.query.filter_by(
    object_id=object_id,
    package_id=base_package_id
).first()

# NEW WAY: Can also query object-specific table directly
base_interface = Interface.query.filter_by(
    object_id=object_id,
    package_id=base_package_id
).first()
```

**Recommendation:** Keep using `object_versions` for comparison logic (it's designed for this), but object-specific tables can now be used for detailed analysis.

---

### 7. Test Files

**Files to Update:**
1. `tests/test_three_way_merge.py`
2. `tests/test_package_extraction.py`
3. `tests/test_repositories.py`
4. Any other test files that create or query object-specific tables

**Changes Required:**

Update test assertions to include package_id:
```python
# OLD
interface = Interface.query.filter_by(object_id=obj_lookup.id).first()
assert interface is not None

# NEW
interface = Interface.query.filter_by(
    object_id=obj_lookup.id,
    package_id=package.id
).first()
assert interface is not None
assert interface.package_id == package.id
```

---

### 8. Debug/Utility Scripts

**Files to Update:**
1. `check_schema.py`
2. `verify_schema.py`
3. `create_test_session.py`
4. Any other utility scripts

**Changes Required:**

Update schema verification to check for package_id column:
```python
# Verify package_id exists in all object-specific tables
object_tables = [
    'interfaces', 'expression_rules', 'process_models', 'record_types',
    'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
    'connected_systems', 'data_stores', 'unknown_objects'
]

for table in object_tables:
    result = db.session.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in result]
    assert 'package_id' in columns, f"Missing package_id in {table}"
```

---

## Migration Strategy

### Phase 1: Schema Changes
1. Create migration script `migration_004_add_package_id_to_objects.py`
2. Add package_id column to all 13 object-specific tables
3. Populate package_id from object_versions table
4. Add unique constraints and indexes
5. Test migration on development database

### Phase 2: Code Changes
1. Update models.py (13 tables)
2. Update package_extraction_service.py (13 methods)
3. Update all repositories (13 files)
4. Update export scripts (2 files)
5. Review comparison services (3 files)

### Phase 3: Testing
1. Update test files
2. Run property-based tests
3. Verify no duplicate entries
4. Verify package-specific queries work
5. Test complete three-way merge workflow

### Phase 4: Documentation
1. Update steering rules (three-way-merge-rebuild.md)
2. Update database schema documentation
3. Update API documentation
4. Update README

---

## Validation Queries

### After Migration - Verify Data Integrity

```sql
-- 1. Verify all object-specific entries have package_id
SELECT COUNT(*) FROM interfaces WHERE package_id IS NULL;
-- Should return 0

-- 2. Verify unique constraint works
SELECT object_id, package_id, COUNT(*) 
FROM interfaces 
GROUP BY object_id, package_id 
HAVING COUNT(*) > 1;
-- Should return 0 rows

-- 3. Verify referential integrity
SELECT COUNT(*) FROM interfaces i
WHERE NOT EXISTS (
    SELECT 1 FROM packages p WHERE p.id = i.package_id
);
-- Should return 0

-- 4. Verify package_object_mappings consistency
SELECT COUNT(*) FROM interfaces i
WHERE NOT EXISTS (
    SELECT 1 FROM package_object_mappings pom
    WHERE pom.object_id = i.object_id
    AND pom.package_id = i.package_id
);
-- Should return 0

-- 5. Count objects per package
SELECT p.package_type, COUNT(DISTINCT i.object_id) as object_count
FROM packages p
LEFT JOIN interfaces i ON i.package_id = p.id
GROUP BY p.package_type;
-- Should show distribution across packages
```

---

## Benefits of This Change

### 1. **Explicit Package Identification**
- No ambiguity about which package an object-specific entry belongs to
- Direct queries for package-specific data

### 2. **Simplified Queries**
```python
# Get Base version of interface
base_interface = Interface.query.filter_by(
    object_id=obj_id,
    package_id=base_package_id
).first()

# Get all versions across packages
all_versions = Interface.query.filter_by(object_id=obj_id).all()
```

### 3. **Better Data Integrity**
- Unique constraint prevents duplicate entries for same object+package
- Foreign key ensures package exists
- Cascade delete cleans up when package is deleted

### 4. **Improved Export Logic**
- Can export specific package version
- Can export all versions with clear package identification
- No confusion about which data belongs where

### 5. **Enhanced Comparison Logic**
- Direct access to package-specific object data
- Can compare specific versions without joining through object_versions
- Clearer code and better performance

---

## Risks and Mitigation

### Risk 1: Data Migration Complexity
**Mitigation:** 
- Use object_versions table as source of truth for package_id
- Test migration on copy of production database first
- Implement rollback in downgrade() method

### Risk 2: Breaking Existing Queries
**Mitigation:**
- Comprehensive grep search for all queries
- Update all queries to include package_id where needed
- Add backward-compatible methods in repositories

### Risk 3: Performance Impact
**Mitigation:**
- Add indexes on (object_id, package_id)
- Composite index improves query performance
- Monitor query performance after migration

### Risk 4: Test Data Inconsistency
**Mitigation:**
- Truncate all tables before running tests
- Use fresh package extraction for each test
- Verify data integrity in test setup

---

## Summary

### Files to Modify: 35+ files

**Critical Files (Must Change):**
1. models.py - 13 table definitions
2. migration_004_add_package_id_to_objects.py - NEW migration script
3. services/package_extraction_service.py - 13 methods
4. repositories/*.py - 13 repository files

**Important Files (Should Change):**
5. export_merge_session.py
6. export_session_flat.py
7. tests/test_three_way_merge.py
8. tests/test_package_extraction.py

**Review Files (May Need Changes):**
9. services/delta_comparison_service.py
10. services/customer_comparison_service.py
11. services/merge_guidance_service.py
12. check_schema.py
13. verify_schema.py

### Estimated Effort
- Schema changes: 2-3 hours
- Code changes: 8-10 hours
- Testing: 4-6 hours
- Documentation: 2-3 hours
- **Total: 16-22 hours**

### Priority: HIGH
This change addresses a fundamental data integrity issue and should be implemented before adding more features that depend on object-specific tables.
