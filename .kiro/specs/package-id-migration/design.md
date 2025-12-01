# Design Document

## Overview

This document describes the architecture and design for adding `package_id` foreign key columns to all object-specific tables in the NexusGen three-way merge system. Currently, when an object appears in multiple packages (Base, Customized, New Vendor), the object-specific tables store multiple entries with the same `object_id` but no way to distinguish which package each entry belongs to. This creates ambiguity in queries and makes package-specific operations impossible.

The solution adds an explicit `package_id` column to all 13 main object-specific tables, creating a clear link between each entry and its source package. This maintains the existing "no duplication" principle in `object_lookup` (which remains package-agnostic) while enabling package-specific queries on detailed object data.

**Key Design Principles:**
- `object_lookup` remains package-agnostic (NO package_id column there)
- Object-specific tables get package_id to identify version source
- Unique constraint on (object_id, package_id) prevents duplicates
- Child tables inherit package context from parent tables
- Migration uses object_versions as source of truth for package_id values

## Architecture

### Current State (Before Migration)

```
object_lookup (package-agnostic)
├── id: 1, uuid: 'abc-123', name: 'MyInterface'
│
interfaces (ambiguous - which package?)
├── id: 1, object_id: 1, version_uuid: 'v1', sail_code: '...'  ← Base version?
├── id: 2, object_id: 1, version_uuid: 'v2', sail_code: '...'  ← Customized version?
├── id: 3, object_id: 1, version_uuid: 'v1', sail_code: '...'  ← New Vendor version?
```

**Problem:** Query `Interface.query.filter_by(object_id=1).all()` returns 3 rows with no way to know which is which!

### Target State (After Migration)

```
object_lookup (still package-agnostic)
├── id: 1, uuid: 'abc-123', name: 'MyInterface'
│
interfaces (explicit package identification)
├── id: 1, object_id: 1, package_id: 1, version_uuid: 'v1'  ← Base (Package A)
├── id: 2, object_id: 1, package_id: 2, version_uuid: 'v2'  ← Customized (Package B)
├── id: 3, object_id: 1, package_id: 3, version_uuid: 'v1'  ← New Vendor (Package C)
```

**Solution:** Query `Interface.query.filter_by(object_id=1, package_id=2).first()` returns exactly the Customized version!


## Components and Interfaces

### Migration Script

**File:** `migrations/migrations_004_add_package_id_to_objects.py`

```python
class Migration004AddPackageIdToObjects:
    """
    Add package_id column to all object-specific tables.
    
    Affected Tables (13 main tables):
    - interfaces
    - expression_rules
    - process_models
    - record_types
    - cdts
    - integrations
    - web_apis
    - sites
    - groups
    - constants
    - connected_systems
    - data_stores
    - unknown_objects
    
    Child tables (NO changes needed):
    - interface_parameters, interface_security
    - expression_rule_inputs
    - process_model_nodes, process_model_flows, process_model_variables
    - record_type_fields, record_type_relationships, record_type_views, record_type_actions
    - cdt_fields
    - data_store_entities
    """
    
    def upgrade(self, db_session):
        """
        Apply migration.
        
        Steps:
        1. Add package_id column (nullable) to all 13 tables
        2. Create index on package_id for each table
        3. Populate package_id from object_versions table
        4. Verify no NULL values remain
        5. Alter package_id to NOT NULL
        6. Add unique constraint on (object_id, package_id)
        7. Create composite index on (object_id, package_id)
        8. Run ANALYZE to update statistics
        """
        pass
    
    def _add_package_id_column(self, table_name: str):
        """Add package_id column to table."""
        sql = f"""
        ALTER TABLE {table_name}
        ADD COLUMN package_id INTEGER
        REFERENCES packages(id) ON DELETE CASCADE
        """
        pass
    
    def _populate_package_id(self, table_name: str):
        """
        Populate package_id from object_versions.
        
        Logic:
        UPDATE {table_name} t
        SET package_id = (
            SELECT ov.package_id
            FROM object_versions ov
            WHERE ov.object_id = t.object_id
            AND ov.version_uuid = t.version_uuid
            LIMIT 1
        )
        """
        pass
    
    def _add_unique_constraint(self, table_name: str):
        """Add unique constraint on (object_id, package_id)."""
        constraint_name = f"uq_{table_name}_object_package"
        sql = f"""
        ALTER TABLE {table_name}
        ADD CONSTRAINT {constraint_name}
        UNIQUE (object_id, package_id)
        """
        pass
    
    def _create_composite_index(self, table_name: str):
        """Create composite index on (object_id, package_id)."""
        index_name = f"idx_{table_name}_object_package"
        sql = f"""
        CREATE INDEX {index_name}
        ON {table_name} (object_id, package_id)
        """
        pass
```


### Updated Database Models

**File:** `models.py`

```python
class Interface(db.Model):
    """Interface objects with package identification."""
    __tablename__ = 'interfaces'
    
    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), 
                          nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), 
                           nullable=False, index=True)  # NEW
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    sail_code = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parameters = db.relationship('InterfaceParameter', backref='interface', 
                                lazy='dynamic', cascade='all, delete-orphan')
    security = db.relationship('InterfaceSecurity', backref='interface', 
                              lazy='dynamic', cascade='all, delete-orphan')
    
    # NEW: Unique constraint and composite index
    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_interface_object_package'),
        db.Index('idx_interface_object_package', 'object_id', 'package_id'),
    )
```

**Apply same pattern to all 13 object-specific tables:**
- ExpressionRule
- ProcessModel
- RecordType
- CDT
- Integration
- WebAPI
- Site
- Group
- Constant
- ConnectedSystem
- DataStore
- UnknownObject


### Updated Package Extraction Service

**File:** `services/package_extraction_service.py`

```python
class PackageExtractionService:
    def _store_interface_data(
        self, 
        object_id: int, 
        package_id: int,  # NEW PARAMETER
        data: Dict[str, Any]
    ) -> None:
        """Store Interface-specific data with package identification."""
        from models import Interface, InterfaceParameter, InterfaceSecurity
        
        interface = Interface(
            object_id=object_id,
            package_id=package_id,  # NEW FIELD
            uuid=data['uuid'],
            name=data['name'],
            version_uuid=data.get('version_uuid'),
            sail_code=data.get('sail_code'),
            description=data.get('description')
        )
        db.session.add(interface)
        db.session.flush()
        
        # Store parameters
        for param_data in data.get('parameters', []):
            param = InterfaceParameter(
                interface_id=interface.id,
                name=param_data['name'],
                type=param_data['type'],
                required=param_data.get('required', False),
                default_value=param_data.get('default_value'),
                display_order=param_data.get('display_order', 0)
            )
            db.session.add(param)
        
        # Store security
        for sec_data in data.get('security', []):
            security = InterfaceSecurity(
                interface_id=interface.id,
                role_name=sec_data['role_name'],
                permission_type=sec_data['permission_type']
            )
            db.session.add(security)
    
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
                self._store_interface_data(object_id, package_id, parsed_data)
            elif object_type == 'Expression Rule':
                self._store_expression_rule_data(object_id, package_id, parsed_data)
            elif object_type == 'Process Model':
                self._store_process_model_data(object_id, package_id, parsed_data)
            # ... etc for all 13 types
        except Exception as e:
            self.logger.error(f"Error storing {object_type} data: {e}")
            raise
    
    def _process_object(
        self,
        package_id: int,
        xml_path: str
    ) -> Optional[ObjectLookup]:
        """Process single object from XML file."""
        # ... existing code to parse XML and find/create object_lookup ...
        
        # Step 5c: Store object-specific data WITH package_id
        self._store_object_specific_data(
            obj_lookup.id, 
            package_id,  # PASS package_id
            object_type, 
            parsed_data
        )
        
        return obj_lookup
```

**Update all 13 `_store_*_data()` methods to accept and use package_id parameter.**


### Updated Object Repositories

**File:** `repositories/interface_repository.py` (example - apply to all 13 repositories)

```python
class InterfaceRepository(BaseRepository):
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
        """
        Create interface with package identification.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID (NEW)
            uuid: Interface UUID
            name: Interface name
            version_uuid: Version UUID
            sail_code: SAIL code
            description: Description
            parameters: List of parameter dicts
            security: List of security dicts
        
        Returns:
            Interface object
        """
        interface = Interface(
            object_id=object_id,
            package_id=package_id,  # NEW
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            sail_code=sail_code,
            description=description
        )
        self.db.session.add(interface)
        self.db.session.flush()
        
        # Add parameters and security...
        
        return interface
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[Interface]:
        """
        Get interface by object_lookup ID and package ID.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            Interface or None if not found
        """
        return Interface.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def get_all_by_object_id(self, object_id: int) -> List[Interface]:
        """
        Get all interfaces for an object across all packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of Interface objects (one per package)
        """
        return Interface.query.filter_by(object_id=object_id).all()
    
    def get_by_package(self, package_id: int) -> List[Interface]:
        """
        Get all interfaces in a package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of Interface objects
        """
        return Interface.query.filter_by(package_id=package_id).all()
```

**Apply same pattern to all 13 repositories:**
- InterfaceRepository
- ExpressionRuleRepository
- ProcessModelRepository
- RecordTypeRepository
- CDTRepository
- IntegrationRepository
- WebAPIRepository
- SiteRepository
- GroupRepository
- ConstantRepository
- ConnectedSystemRepository
- DataStoreRepository
- UnknownObjectRepository


### Updated Export Scripts

**File:** `export_merge_session.py`

```python
def export_object_details(
    object_id: int, 
    object_type: str, 
    package_id: Optional[int] = None  # NEW PARAMETER
) -> Optional[Dict[str, Any]]:
    """
    Export detailed object information.
    
    Args:
        object_id: Object lookup ID
        object_type: Object type
        package_id: Optional package ID to get specific version
    
    Returns:
        Dict with object details or None if not found
    """
    if object_type == 'interface':
        if package_id:
            # Get specific package version
            interface = Interface.query.filter_by(
                object_id=object_id,
                package_id=package_id
            ).first()
        else:
            # Get first version (or could get all versions)
            interface = Interface.query.filter_by(object_id=object_id).first()
        
        return export_interface_details(interface.id) if interface else None
    
    # ... apply to all object types
```

**File:** `export_session_flat.py`

```python
def export_session_flat(session_id: int, output_path: str):
    """Export session data with package identification."""
    session = MergeSession.query.get(session_id)
    changes = Change.query.filter_by(session_id=session_id).all()
    
    export_data = {
        'session': serialize_model(session),
        'changes': [],
        'objects': {}
    }
    
    for change in changes:
        object_id = change.object_id
        object_type = change.object.object_type.lower().replace(' ', '')
        
        # Export all package versions with package identification
        if object_type == 'interface':
            interfaces = Interface.query.filter_by(object_id=object_id).all()
            for interface in interfaces:
                package = Package.query.get(interface.package_id)
                export_data['objects'].setdefault(object_id, []).append({
                    **serialize_model(interface),
                    'package_type': package.package_type,  # NEW
                    'package_filename': package.filename   # NEW
                })
        
        # ... apply to all object types
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
```


## Data Models

### Object-Specific Tables (After Migration)

All 13 main object-specific tables will have this structure:

```sql
CREATE TABLE interfaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,  -- NEW
    uuid VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    version_uuid VARCHAR(255),
    sail_code TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,  -- NEW
    
    CONSTRAINT uq_interface_object_package UNIQUE (object_id, package_id),  -- NEW
    
    INDEX idx_interface_object (object_id),
    INDEX idx_interface_package (package_id),  -- NEW
    INDEX idx_interface_object_package (object_id, package_id)  -- NEW
);
```

**Tables to modify:**
1. interfaces
2. expression_rules
3. process_models
4. record_types
5. cdts
6. integrations
7. web_apis
8. sites
9. groups
10. constants
11. connected_systems
12. data_stores
13. unknown_objects

### Child Tables (No Changes)

Child tables inherit package context from parent tables via foreign key:

```sql
-- Example: interface_parameters
CREATE TABLE interface_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interface_id INTEGER NOT NULL,  -- Links to interfaces.id
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255),
    required BOOLEAN DEFAULT 0,
    default_value TEXT,
    display_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (interface_id) REFERENCES interfaces(id) ON DELETE CASCADE
);

-- To get package_id for a parameter, join to parent:
SELECT p.*, i.package_id
FROM interface_parameters p
JOIN interfaces i ON i.id = p.interface_id
WHERE i.package_id = 2;
```

**Child tables (no package_id needed):**
- interface_parameters
- interface_security
- expression_rule_inputs
- process_model_nodes
- process_model_flows
- process_model_variables
- record_type_fields
- record_type_relationships
- record_type_views
- record_type_actions
- cdt_fields
- data_store_entities


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: All object-specific tables have package_id column

*For any* object-specific table in the set {interfaces, expression_rules, process_models, record_types, cdts, integrations, web_apis, sites, groups, constants, connected_systems, data_stores, unknown_objects}, the table schema should include a package_id column with foreign key constraint to packages.id.

**Validates: Requirements 1.1, 1.2**

### Property 2: All package_id columns have indexes

*For any* object-specific table with package_id column, there should exist both a single-column index on package_id and a composite index on (object_id, package_id).

**Validates: Requirements 1.4, 3.3, 9.1**

### Property 3: Child tables do not have package_id

*For any* child table in the set {interface_parameters, interface_security, expression_rule_inputs, process_model_nodes, process_model_flows, process_model_variables, record_type_fields, record_type_relationships, record_type_views, record_type_actions, cdt_fields, data_store_entities}, the table schema should NOT include a package_id column.

**Validates: Requirements 1.5, 11.2**

### Property 4: All package_id values match object_versions

*For any* entry in an object-specific table, the package_id value should match the package_id in object_versions where object_id and version_uuid match.

**Validates: Requirements 2.1, 2.2**

### Property 5: No NULL package_id values after migration

*For any* entry in an object-specific table after migration completes, the package_id column should have a non-NULL value.

**Validates: Requirements 2.4, 2.5, 7.1**

### Property 6: Unique constraint prevents duplicates

*For any* object-specific table, attempting to insert a second entry with the same (object_id, package_id) combination should fail with a constraint violation error.

**Validates: Requirements 3.1, 3.4, 7.2**

### Property 7: Unique constraint naming convention

*For any* object-specific table, the unique constraint on (object_id, package_id) should be named following the pattern 'uq_{table_name}_object_package'.

**Validates: Requirements 3.2**

### Property 8: All package_id values reference valid packages

*For any* entry in an object-specific table, the package_id value should reference an existing record in the packages table.

**Validates: Requirements 7.3**

### Property 9: Package-object mappings consistency

*For any* entry in an object-specific table with (object_id, package_id), there should exist a corresponding entry in package_object_mappings with the same (object_id, package_id) combination.

**Validates: Requirements 7.4**

### Property 10: Extraction service passes package_id

*For any* object extracted from a package, when the extraction service stores object-specific data, it should pass the package_id parameter to the storage method.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 11: Repository create methods accept package_id

*For any* object-specific repository, the create method should accept package_id as a required parameter and include it when creating the database record.

**Validates: Requirements 5.1**

### Property 12: Query by object and package returns single result

*For any* valid (object_id, package_id) combination, querying an object-specific repository with both parameters should return exactly one result or None.

**Validates: Requirements 5.2, 5.5**

### Property 13: Query by object_id returns all package versions

*For any* object_id that exists in multiple packages, querying an object-specific repository by object_id alone should return all package versions of that object.

**Validates: Requirements 5.3, 5.4**

### Property 14: Export with package_id returns correct version

*For any* object that exists in multiple packages, exporting with a specific package_id should return only the data for that package version.

**Validates: Requirements 6.2**

### Property 15: Export includes package identification

*For any* exported object data, when exporting all versions, the export should include package_type or package identification for each version.

**Validates: Requirements 6.4, 6.5**

### Property 16: Child table queries join to parent for package_id

*For any* child table record, querying with package_id filter should join to the parent table to obtain the package_id value.

**Validates: Requirements 11.1, 11.4, 11.5**

### Property 17: CASCADE DELETE removes child records

*For any* parent table record with child records, deleting the parent should automatically delete all associated child records due to CASCADE DELETE constraint.

**Validates: Requirements 11.3**

### Property 18: Comparison services use package_id correctly

*For any* comparison operation that needs package-specific object data, the comparison service should query object-specific tables using package_id to retrieve the correct version.

**Validates: Requirements 12.2, 12.3, 12.4**

### Property 19: Comparison services maintain object_versions compatibility

*For any* comparison operation, the delta and customer comparison services should continue using object_versions as the primary source for version-specific comparisons.

**Validates: Requirements 12.1, 12.5**


## Error Handling

### Migration Errors

**Scenario:** Migration script encounters an error during execution

**Handling:**
1. Catch exception and log detailed error message
2. Rollback database transaction to undo all changes
3. Log rollback completion
4. Re-raise exception to halt migration
5. Provide clear error message to administrator

**Example:**
```python
try:
    with db.session.begin():
        self._add_package_id_columns()
        self._populate_package_ids()
        self._add_constraints()
        self._create_indexes()
        db.session.commit()
        logger.info("Migration completed successfully")
except Exception as e:
    logger.error(f"Migration failed: {e}")
    db.session.rollback()
    logger.info("All changes rolled back")
    raise
```

### Missing package_id Mapping

**Scenario:** Object-specific entry has no matching record in object_versions

**Handling:**
1. Log warning with object details (object_id, version_uuid, table_name)
2. Skip that entry (leave package_id as NULL temporarily)
3. Continue processing other entries
4. After migration, report all entries with NULL package_id
5. Administrator must manually investigate and fix

**Example:**
```python
result = db.session.execute("""
    UPDATE interfaces
    SET package_id = (
        SELECT ov.package_id
        FROM object_versions ov
        WHERE ov.object_id = interfaces.object_id
        AND ov.version_uuid = interfaces.version_uuid
        LIMIT 1
    )
""")

# Check for NULLs
null_count = db.session.execute("""
    SELECT COUNT(*) FROM interfaces WHERE package_id IS NULL
""").scalar()

if null_count > 0:
    logger.warning(f"{null_count} interfaces have NULL package_id - manual review required")
```

### Constraint Violations

**Scenario:** Attempting to insert duplicate (object_id, package_id) combination

**Handling:**
1. Database raises IntegrityError
2. Application catches exception
3. Log error with object details
4. Return error to caller
5. Caller decides whether to update existing or skip

**Example:**
```python
try:
    interface = Interface(
        object_id=obj_id,
        package_id=pkg_id,
        uuid=uuid,
        name=name
    )
    db.session.add(interface)
    db.session.commit()
except IntegrityError as e:
    logger.error(f"Duplicate interface: object_id={obj_id}, package_id={pkg_id}")
    db.session.rollback()
    raise DuplicateObjectError(f"Interface already exists for this package")
```

### Query Errors

**Scenario:** Query for non-existent package_id

**Handling:**
1. Query returns None or empty list
2. Caller checks for None/empty
3. Handle gracefully (return default, raise NotFoundError, etc.)
4. Log if unexpected

**Example:**
```python
interface = Interface.query.filter_by(
    object_id=obj_id,
    package_id=pkg_id
).first()

if interface is None:
    logger.warning(f"Interface not found: object_id={obj_id}, package_id={pkg_id}")
    raise ObjectNotFoundError(f"No interface found for package {pkg_id}")
```


## Testing Strategy

### Unit Testing

**Framework:** pytest

**Test Files to Update:**
- `tests/test_package_extraction_service.py`
- `tests/test_repositories.py`
- `tests/test_object_parsers.py`
- `tests/test_three_way_merge_orchestrator.py`

**Unit Test Examples:**

```python
def test_interface_creation_with_package_id(db_session):
    """Test creating interface with package_id."""
    # Setup
    obj_lookup = ObjectLookup(uuid='test-uuid', name='TestInterface', object_type='Interface')
    db_session.add(obj_lookup)
    
    package = Package(session_id=1, package_type='base', filename='base.zip')
    db_session.add(package)
    db_session.flush()
    
    # Create interface with package_id
    interface = Interface(
        object_id=obj_lookup.id,
        package_id=package.id,
        uuid='test-uuid',
        name='TestInterface',
        version_uuid='v1'
    )
    db_session.add(interface)
    db_session.commit()
    
    # Verify
    assert interface.package_id == package.id
    assert interface.object_id == obj_lookup.id

def test_duplicate_object_package_rejected(db_session):
    """Test unique constraint prevents duplicates."""
    # Setup
    obj_lookup = ObjectLookup(uuid='test-uuid', name='TestInterface', object_type='Interface')
    package = Package(session_id=1, package_type='base', filename='base.zip')
    db_session.add_all([obj_lookup, package])
    db_session.flush()
    
    # Create first interface
    interface1 = Interface(
        object_id=obj_lookup.id,
        package_id=package.id,
        uuid='test-uuid',
        name='TestInterface'
    )
    db_session.add(interface1)
    db_session.commit()
    
    # Attempt to create duplicate
    interface2 = Interface(
        object_id=obj_lookup.id,
        package_id=package.id,  # Same object_id + package_id
        uuid='test-uuid',
        name='TestInterface'
    )
    db_session.add(interface2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_repository_get_by_object_and_package(db_session):
    """Test repository method returns correct version."""
    # Setup: Create same object in 3 packages
    obj_lookup = ObjectLookup(uuid='test-uuid', name='TestInterface', object_type='Interface')
    db_session.add(obj_lookup)
    db_session.flush()
    
    packages = [
        Package(session_id=1, package_type='base', filename='base.zip'),
        Package(session_id=1, package_type='customized', filename='custom.zip'),
        Package(session_id=1, package_type='new_vendor', filename='vendor.zip')
    ]
    db_session.add_all(packages)
    db_session.flush()
    
    interfaces = [
        Interface(object_id=obj_lookup.id, package_id=packages[0].id, 
                 uuid='test-uuid', name='TestInterface', version_uuid='v1'),
        Interface(object_id=obj_lookup.id, package_id=packages[1].id, 
                 uuid='test-uuid', name='TestInterface', version_uuid='v2'),
        Interface(object_id=obj_lookup.id, package_id=packages[2].id, 
                 uuid='test-uuid', name='TestInterface', version_uuid='v1')
    ]
    db_session.add_all(interfaces)
    db_session.commit()
    
    # Test: Get customized version
    repo = InterfaceRepository(db_session)
    result = repo.get_by_object_and_package(obj_lookup.id, packages[1].id)
    
    assert result is not None
    assert result.package_id == packages[1].id
    assert result.version_uuid == 'v2'
```

### Property-Based Testing

**Framework:** pytest with real Appian packages

**Test Configuration:**
- Use packages from `applicationArtifacts/Three Way Testing Files/V2/`
- Run complete end-to-end workflow
- Verify properties after migration
- Clean database between tests

**Property Test Examples:**

```python
def test_property_1_all_tables_have_package_id(db_session):
    """
    Property 1: All object-specific tables have package_id column.
    Validates: Requirements 1.1, 1.2
    """
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    for table in object_tables:
        # Check column exists
        result = db_session.execute(f"PRAGMA table_info({table})")
        columns = {row[1]: row for row in result}
        
        assert 'package_id' in columns, f"Missing package_id in {table}"
        
        # Check foreign key constraint
        result = db_session.execute(f"PRAGMA foreign_key_list({table})")
        fks = list(result)
        package_fk = [fk for fk in fks if fk[3] == 'package_id']
        
        assert len(package_fk) > 0, f"Missing FK constraint on package_id in {table}"
        assert package_fk[0][2] == 'packages', f"FK should reference packages table"

def test_property_5_no_null_package_ids(db_session):
    """
    Property 5: No NULL package_id values after migration.
    Validates: Requirements 2.4, 2.5, 7.1
    """
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    for table in object_tables:
        result = db_session.execute(
            f"SELECT COUNT(*) FROM {table} WHERE package_id IS NULL"
        )
        null_count = result.scalar()
        
        assert null_count == 0, f"Found {null_count} NULL package_ids in {table}"

def test_property_6_unique_constraint_prevents_duplicates(db_session):
    """
    Property 6: Unique constraint prevents duplicates.
    Validates: Requirements 3.1, 3.4, 7.2
    """
    # Setup
    obj_lookup = ObjectLookup(uuid='test-uuid', name='Test', object_type='Interface')
    package = Package(session_id=1, package_type='base', filename='base.zip')
    db_session.add_all([obj_lookup, package])
    db_session.flush()
    
    # Create first entry
    interface1 = Interface(
        object_id=obj_lookup.id,
        package_id=package.id,
        uuid='test-uuid',
        name='Test'
    )
    db_session.add(interface1)
    db_session.commit()
    
    # Attempt duplicate
    interface2 = Interface(
        object_id=obj_lookup.id,
        package_id=package.id,
        uuid='test-uuid',
        name='Test'
    )
    db_session.add(interface2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_property_9_package_object_mappings_consistency(db_session):
    """
    Property 9: Package-object mappings consistency.
    Validates: Requirements 7.4
    """
    # Run complete extraction
    orchestrator = ThreeWayMergeOrchestrator(...)
    session = orchestrator.create_merge_session(
        base_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip",
        customized_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip",
        new_vendor_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip"
    )
    
    # Check each object-specific table
    object_tables = ['interfaces', 'expression_rules', 'process_models', ...]
    
    for table in object_tables:
        # Get all (object_id, package_id) from object-specific table
        result = db_session.execute(
            f"SELECT DISTINCT object_id, package_id FROM {table}"
        )
        table_pairs = set(result.fetchall())
        
        # Get all (object_id, package_id) from package_object_mappings
        result = db_session.execute("""
            SELECT object_id, package_id 
            FROM package_object_mappings
            WHERE object_id IN (SELECT object_id FROM {table})
        """)
        mapping_pairs = set(result.fetchall())
        
        # Every pair in object-specific table should exist in mappings
        missing = table_pairs - mapping_pairs
        assert len(missing) == 0, f"Missing mappings for {table}: {missing}"

def test_property_12_query_by_object_and_package_returns_single_result(db_session):
    """
    Property 12: Query by object and package returns single result.
    Validates: Requirements 5.2, 5.5
    """
    # Setup: Create object in 3 packages
    obj_lookup = ObjectLookup(uuid='test-uuid', name='Test', object_type='Interface')
    db_session.add(obj_lookup)
    db_session.flush()
    
    packages = [
        Package(session_id=1, package_type='base', filename='base.zip'),
        Package(session_id=1, package_type='customized', filename='custom.zip'),
        Package(session_id=1, package_type='new_vendor', filename='vendor.zip')
    ]
    db_session.add_all(packages)
    db_session.flush()
    
    for pkg in packages:
        interface = Interface(
            object_id=obj_lookup.id,
            package_id=pkg.id,
            uuid='test-uuid',
            name='Test'
        )
        db_session.add(interface)
    db_session.commit()
    
    # Test: Query each package
    repo = InterfaceRepository(db_session)
    for pkg in packages:
        result = repo.get_by_object_and_package(obj_lookup.id, pkg.id)
        assert result is not None
        assert result.package_id == pkg.id
        
        # Verify only one result
        all_results = Interface.query.filter_by(
            object_id=obj_lookup.id,
            package_id=pkg.id
        ).all()
        assert len(all_results) == 1
```

### Integration Testing

**Test Complete Workflow:**

```python
def test_end_to_end_with_package_id(db_session):
    """Test complete three-way merge workflow with package_id."""
    # 1. Create merge session and extract packages
    orchestrator = ThreeWayMergeOrchestrator(...)
    session = orchestrator.create_merge_session(
        base_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip",
        customized_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip",
        new_vendor_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip"
    )
    
    # 2. Verify packages created
    packages = Package.query.filter_by(session_id=session.id).all()
    assert len(packages) == 3
    
    # 3. Verify all object-specific entries have package_id
    for table in ['interfaces', 'expression_rules', 'process_models']:
        result = db_session.execute(
            f"SELECT COUNT(*) FROM {table} WHERE package_id IS NULL"
        )
        assert result.scalar() == 0
    
    # 4. Verify unique constraints work
    # Try to create duplicate - should fail
    interface = Interface.query.first()
    duplicate = Interface(
        object_id=interface.object_id,
        package_id=interface.package_id,
        uuid=interface.uuid,
        name=interface.name
    )
    db_session.add(duplicate)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # 5. Verify queries work correctly
    repo = InterfaceRepository(db_session)
    
    # Get specific version
    specific = repo.get_by_object_and_package(
        interface.object_id,
        interface.package_id
    )
    assert specific is not None
    assert specific.id == interface.id
    
    # Get all versions
    all_versions = repo.get_all_by_object_id(interface.object_id)
    assert len(all_versions) >= 1
```

### Test Execution

**Run all tests:**
```bash
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**Run specific test file:**
```bash
python -m pytest tests/test_package_id_migration.py -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**Run property tests only:**
```bash
python -m pytest -k "test_property" -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

