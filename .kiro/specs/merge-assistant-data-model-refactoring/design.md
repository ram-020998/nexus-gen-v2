# Design Document

## Overview

This design refactors the Merge Assistant data model from a denormalized structure with large JSON blobs to a normalized relational database schema. The refactoring will improve query performance, reduce data redundancy, and enable more efficient filtering and searching capabilities.

### Current State

The existing schema consists of two main tables:

1. **MergeSession** - Stores session metadata and large JSON blobs:
   - `base_blueprint` (TEXT) - Complete blueprint JSON for package A
   - `customized_blueprint` (TEXT) - Complete blueprint JSON for package B
   - `new_vendor_blueprint` (TEXT) - Complete blueprint JSON for package C
   - `vendor_changes` (TEXT) - A→C comparison results JSON
   - `customer_changes` (TEXT) - A→B comparison results JSON
   - `classification_results` (TEXT) - Classified changes JSON
   - `ordered_changes` (TEXT) - Smart-ordered changes list JSON

2. **ChangeReview** - Stores user review actions:
   - Links to MergeSession via `session_id`
   - Stores object UUID, name, type, classification
   - Tracks review status and notes

### Target State

The new schema will normalize data into multiple related tables:

1. **MergeSession** - Session metadata only (no JSON blobs)
2. **Package** - Individual package information
3. **AppianObject** - Normalized object data
4. **Change** - Individual change records
5. **ObjectDependency** - Object relationships
6. **ChangeReview** - User review actions (enhanced)

## Architecture

### Database Schema Design

#### Entity Relationship Diagram

```
MergeSession (1) ----< (3) Package
    |
    |
    +----< (many) Change
              |
              +----< (1) ChangeReview
              |
              +----< (many) ObjectDependency

Package (1) ----< (many) AppianObject
                      |
                      +----< (many) ObjectDependency
```

#### Schema Layers

1. **Session Layer**: MergeSession table manages overall merge workflow
2. **Package Layer**: Package and AppianObject tables store blueprint data
3. **Comparison Layer**: Change table stores comparison results
4. **Review Layer**: ChangeReview table tracks user actions
5. **Relationship Layer**: ObjectDependency table manages object references

### Migration Strategy

The migration will follow a phased approach:

1. **Phase 1: Schema Creation**
   - Create new tables with proper indexes and constraints
   - Validate schema structure

2. **Phase 2: Data Migration**
   - Extract data from JSON blobs
   - Insert into normalized tables
   - Verify data integrity

3. **Phase 3: Code Refactoring**
   - Update service layer to use new schema
   - Modify queries to use JOINs instead of JSON parsing
   - Update controllers to work with new data structure

4. **Phase 4: Cleanup**
   - Remove old JSON columns
   - Drop unused indexes
   - Optimize table structure

## Components and Interfaces

### Database Tables

#### 1. MergeSession (Modified)

Stores session-level metadata without JSON blobs.

```python
class MergeSession(db.Model):
    __tablename__ = 'merge_sessions'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='processing', index=True)
    current_change_index = db.Column(db.Integer, default=0)
    
    # Progress tracking
    total_changes = db.Column(db.Integer, default=0)
    reviewed_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    total_time = db.Column(db.Integer)
    error_log = db.Column(db.Text)
    
    # Relationships
    packages = db.relationship('Package', backref='session', lazy=True, cascade='all, delete-orphan')
    changes = db.relationship('Change', backref='session', lazy=True, cascade='all, delete-orphan')
```

#### 2. Package (New)

Stores individual package information (A, B, or C).

```python
class Package(db.Model):
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'), nullable=False, index=True)
    
    # Package identification
    package_type = db.Column(db.String(20), nullable=False)  # 'base', 'customized', 'new_vendor'
    package_name = db.Column(db.String(255), nullable=False)
    
    # Metadata from blueprint
    total_objects = db.Column(db.Integer, default=0)
    object_type_counts = db.Column(db.Text)  # JSON: {"interfaces": 50, "process_models": 20, ...}
    generation_time = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    objects = db.relationship('AppianObject', backref='package', lazy=True, cascade='all, delete-orphan')
    
    # Composite index for efficient lookups
    __table_args__ = (
        db.Index('idx_package_session_type', 'session_id', 'package_type'),
    )
```

#### 3. AppianObject (New)

Stores normalized Appian object data.

```python
class AppianObject(db.Model):
    __tablename__ = 'appian_objects'
    
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False, index=True)
    
    # Object identification
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False, index=True)
    object_type = db.Column(db.String(50), nullable=False, index=True)
    
    # Object content
    sail_code = db.Column(db.Text)  # For interfaces, expression rules
    fields = db.Column(db.Text)  # JSON: field definitions
    properties = db.Column(db.Text)  # JSON: object properties
    metadata = db.Column(db.Text)  # JSON: additional metadata
    
    # Version information
    version_uuid = db.Column(db.String(255), index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    dependencies_as_parent = db.relationship(
        'ObjectDependency',
        foreign_keys='ObjectDependency.parent_uuid',
        backref='parent_object',
        lazy=True
    )
    dependencies_as_child = db.relationship(
        'ObjectDependency',
        foreign_keys='ObjectDependency.child_uuid',
        backref='child_object',
        lazy=True
    )
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('package_id', 'uuid', name='uq_package_object'),
        db.Index('idx_object_type_name', 'object_type', 'name'),
    )
```

#### 4. Change (New)

Stores individual change records from comparison.

```python
class Change(db.Model):
    __tablename__ = 'changes'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'), nullable=False, index=True)
    
    # Object identification
    object_uuid = db.Column(db.String(255), nullable=False, index=True)
    object_name = db.Column(db.String(500), nullable=False, index=True)
    object_type = db.Column(db.String(50), nullable=False, index=True)
    
    # Change classification
    classification = db.Column(db.String(50), nullable=False, index=True)
    # Values: NO_CONFLICT, CONFLICT, CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED
    
    # Change details
    change_type = db.Column(db.String(20))  # ADDED, MODIFIED, REMOVED
    vendor_change_type = db.Column(db.String(20))  # A→C change type
    customer_change_type = db.Column(db.String(20))  # A→B change type
    
    # Object references (foreign keys to AppianObject)
    base_object_id = db.Column(db.Integer, db.ForeignKey('appian_objects.id'))
    customer_object_id = db.Column(db.Integer, db.ForeignKey('appian_objects.id'))
    vendor_object_id = db.Column(db.Integer, db.ForeignKey('appian_objects.id'))
    
    # Merge guidance
    merge_guidance = db.Column(db.Text)  # JSON: guidance information
    
    # Ordering
    display_order = db.Column(db.Integer, nullable=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    review = db.relationship('ChangeReview', backref='change', uselist=False, cascade='all, delete-orphan')
    
    # Composite indexes for efficient queries
    __table_args__ = (
        db.Index('idx_change_session_classification', 'session_id', 'classification'),
        db.Index('idx_change_session_type', 'session_id', 'object_type'),
        db.Index('idx_change_session_order', 'session_id', 'display_order'),
    )
```

#### 5. ObjectDependency (New)

Stores relationships between Appian objects.

```python
class ObjectDependency(db.Model):
    __tablename__ = 'object_dependencies'
    
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False, index=True)
    
    # Dependency relationship
    parent_uuid = db.Column(db.String(255), nullable=False, index=True)
    child_uuid = db.Column(db.String(255), nullable=False, index=True)
    
    # Dependency type
    dependency_type = db.Column(db.String(50))  # 'reference', 'contains', etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite indexes
    __table_args__ = (
        db.Index('idx_dependency_parent', 'package_id', 'parent_uuid'),
        db.Index('idx_dependency_child', 'package_id', 'child_uuid'),
        db.UniqueConstraint('package_id', 'parent_uuid', 'child_uuid', name='uq_dependency'),
    )
```

#### 6. ChangeReview (Modified)

Enhanced to link to Change table instead of duplicating data.

```python
class ChangeReview(db.Model):
    __tablename__ = 'change_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'), nullable=False, index=True)
    change_id = db.Column(db.Integer, db.ForeignKey('changes.id'), nullable=False, unique=True, index=True)
    
    # Review status
    review_status = db.Column(db.String(20), default='pending', index=True)
    user_notes = db.Column(db.Text)
    
    # Timestamps
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite index
    __table_args__ = (
        db.Index('idx_review_session_status', 'session_id', 'review_status'),
    )
```

### Service Layer Interfaces

#### 1. ThreeWayMergeService (Modified)

Updated to work with normalized schema.

```python
class ThreeWayMergeService:
    def create_session(
        self,
        base_zip_path: str,
        customized_zip_path: str,
        new_vendor_zip_path: str
    ) -> MergeSession:
        """
        Create session and populate normalized tables
        
        Steps:
        1. Create MergeSession record
        2. Generate blueprints and create Package records
        3. Extract objects and create AppianObject records
        4. Extract dependencies and create ObjectDependency records
        5. Perform comparisons and create Change records
        6. Create ChangeReview records
        """
        pass
    
    def get_ordered_changes(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Get changes using SQL JOIN instead of JSON parsing
        
        Query:
        SELECT c.*, ao_base.*, ao_customer.*, ao_vendor.*
        FROM changes c
        LEFT JOIN appian_objects ao_base ON c.base_object_id = ao_base.id
        LEFT JOIN appian_objects ao_customer ON c.customer_object_id = ao_customer.id
        LEFT JOIN appian_objects ao_vendor ON c.vendor_object_id = ao_vendor.id
        WHERE c.session_id = ?
        ORDER BY c.display_order
        """
        pass
    
    def filter_changes(
        self,
        session_id: int,
        classification: Optional[str] = None,
        object_type: Optional[str] = None,
        review_status: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter changes using SQL WHERE clauses instead of Python filtering
        
        Query uses indexed columns for efficient filtering
        """
        pass
```

#### 2. PackageService (New)

Service for managing Package and AppianObject records.

```python
class PackageService:
    def create_package_from_blueprint(
        self,
        session_id: int,
        package_type: str,
        blueprint_result: Dict[str, Any]
    ) -> Package:
        """
        Create Package and AppianObject records from blueprint
        
        Steps:
        1. Create Package record with metadata
        2. Extract objects from blueprint['object_lookup']
        3. Create AppianObject records in batch
        4. Extract dependencies and create ObjectDependency records
        """
        pass
    
    def get_object_by_uuid(
        self,
        package_id: int,
        uuid: str
    ) -> Optional[AppianObject]:
        """
        Get object by UUID using indexed query
        """
        pass
    
    def get_objects_by_type(
        self,
        package_id: int,
        object_type: str
    ) -> List[AppianObject]:
        """
        Get all objects of specific type
        """
        pass
```

#### 3. ChangeService (New)

Service for managing Change records.

```python
class ChangeService:
    def create_changes_from_comparison(
        self,
        session_id: int,
        classification_results: Dict[str, List[Dict]],
        ordered_changes: List[Dict[str, Any]]
    ) -> List[Change]:
        """
        Create Change records from comparison results
        
        Steps:
        1. Iterate through ordered_changes
        2. Look up object IDs from AppianObject table
        3. Create Change records with proper foreign keys
        4. Set display_order for maintaining order
        """
        pass
    
    def get_change_with_objects(
        self,
        change_id: int
    ) -> Dict[str, Any]:
        """
        Get change with all related objects using JOIN
        
        Returns complete change information without JSON parsing
        """
        pass
```

## Data Models

### Data Flow

#### 1. Session Creation Flow

```
User uploads 3 ZIP files
    ↓
ThreeWayMergeService.create_session()
    ↓
Generate blueprints (existing AppianAnalyzer)
    ↓
PackageService.create_package_from_blueprint() × 3
    ├─ Create Package records
    ├─ Create AppianObject records (batch insert)
    └─ Create ObjectDependency records (batch insert)
    ↓
Perform comparisons (existing services)
    ↓
ChangeService.create_changes_from_comparison()
    ├─ Create Change records (batch insert)
    └─ Create ChangeReview records (batch insert)
    ↓
Session ready for user review
```

#### 2. Change Viewing Flow

```
User navigates to change
    ↓
Controller calls ThreeWayMergeService.get_ordered_changes()
    ↓
SQL JOIN query:
    changes
    LEFT JOIN appian_objects (base)
    LEFT JOIN appian_objects (customer)
    LEFT JOIN appian_objects (vendor)
    LEFT JOIN change_reviews
    ↓
Return enriched change data
    ↓
Render template with complete information
```

#### 3. Filtering Flow

```
User applies filters
    ↓
Controller calls ThreeWayMergeService.filter_changes()
    ↓
Build SQL query with WHERE clauses:
    - classification = ?
    - object_type = ?
    - review_status = ?
    - name LIKE ?
    ↓
Execute indexed query
    ↓
Return filtered results (fast)
```

### Migration Data Model

#### Migration Script Structure

```python
class MigrationService:
    def migrate_session(self, session_id: int) -> bool:
        """
        Migrate single session from old to new schema
        
        Steps:
        1. Load MergeSession record
        2. Parse JSON blobs
        3. Create Package records
        4. Create AppianObject records
        5. Create Change records
        6. Update ChangeReview records
        7. Verify data integrity
        8. Clear old JSON columns
        """
        pass
    
    def verify_migration(self, session_id: int) -> Dict[str, bool]:
        """
        Verify migration correctness
        
        Checks:
        - Package count = 3
        - Object count matches blueprint metadata
        - Change count matches ordered_changes length
        - Review count matches changes count
        - All foreign keys valid
        """
        pass
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Blueprint data normalization

*For any* blueprint result with objects and metadata, storing it should create exactly one Package record and N AppianObject records where N equals the number of objects in the blueprint, with no blueprint JSON remaining in the session table.

**Validates: Requirements 1.1**

### Property 2: Change foreign key validity

*For any* comparison result that creates Change records, all Change records should have valid foreign keys to AppianObject records (base_object_id, customer_object_id, or vendor_object_id must reference existing objects).

**Validates: Requirements 1.2**

### Property 3: Classification normalization

*For any* classification result, after storing, the Change table should contain classification values in the classification column and the session's classification_results JSON column should be null or empty.

**Validates: Requirements 1.3**

### Property 4: Dependency table population

*For any* blueprint with dependency information, storing it should create ObjectDependency records with valid package_id and object UUID references.

**Validates: Requirements 1.5**

### Property 5: Session metadata preservation

*For any* session with metadata fields (reference_id, status, timestamps, counts), migrating the session should preserve all metadata values identically.

**Validates: Requirements 2.2**

### Property 6: Blueprint migration round-trip

*For any* session with blueprint JSON data, after migration, reconstructing the blueprint from normalized tables (Package + AppianObject) should produce equivalent object data (same UUIDs, names, types, and content).

**Validates: Requirements 2.3**

### Property 7: Change ordering preservation

*For any* session with ordered changes, after migration, querying Change records by display_order should return changes in the same sequence with the same classifications.

**Validates: Requirements 2.4**

### Property 8: Migration record count verification

*For any* migrated session, the verification should confirm that Package count equals 3, AppianObject count matches sum of blueprint metadata total_objects, and Change count matches ordered_changes length.

**Validates: Requirements 2.5**

### Property 9: Filter result consistency

*For any* filter criteria (classification, object_type, review_status, search_term), applying the filter should return the same set of changes regardless of whether data is in JSON format or normalized tables.

**Validates: Requirements 3.2**

### Property 10: Review action equivalence

*For any* review action (reviewed or skipped with notes), recording the action should update the ChangeReview record and session counts (reviewed_count, skipped_count) identically to the old implementation.

**Validates: Requirements 3.3**

### Property 11: Export data completeness

*For any* session, exporting data should include all fields present in the original JSON-based export (session info, packages, changes, reviews, statistics).

**Validates: Requirements 3.5**

### Property 12: Object name search correctness

*For any* search term, searching by object name should return all changes where the object name contains the search term (case-insensitive).

**Validates: Requirements 4.2**

### Property 13: Statistics calculation accuracy

*For any* session, calculating statistics (total_changes, no_conflict count, conflict count, etc.) should produce the same values whether computed from JSON or from aggregated SQL queries.

**Validates: Requirements 4.4**

### Property 14: Dependency query correctness

*For any* object UUID, querying its dependencies should return all parent and child relationships that exist in the ObjectDependency table.

**Validates: Requirements 4.5**

### Property 15: UUID uniqueness enforcement

*For any* attempt to insert an AppianObject with a duplicate UUID within the same package, the database should reject the insertion with a constraint violation.

**Validates: Requirements 5.2**

### Property 16: Cascade delete completeness

*For any* session with related records (packages, objects, changes, reviews, dependencies), deleting the session should remove all related records, leaving no orphaned data.

**Validates: Requirements 5.4**

### Property 17: Referential integrity enforcement

*For any* attempt to create a Change record with an invalid object_id foreign key, the database should reject the insertion with a constraint violation.

**Validates: Requirements 5.5**

### Property 18: Package storage correctness

*For any* package data with metadata, storing it should create a Package record with correct session_id, package_type, package_name, and metadata fields.

**Validates: Requirements 6.1**

### Property 19: Object-package linkage

*For any* AppianObject record, it should have a valid package_id that references an existing Package record.

**Validates: Requirements 6.2**

### Property 20: Change-object linkage

*For any* Change record, at least one of its object foreign keys (base_object_id, customer_object_id, vendor_object_id) should reference an existing AppianObject record.

**Validates: Requirements 6.3**

### Property 21: Review-change linkage

*For any* ChangeReview record, it should have a valid change_id that references an existing Change record.

**Validates: Requirements 6.4**

### Property 22: Dependency storage correctness

*For any* dependency relationship between two objects, it should be stored in the ObjectDependency table with valid package_id, parent_uuid, and child_uuid.

**Validates: Requirements 6.5**

## Error Handling

### Database Errors

1. **Constraint Violations**
   - Foreign key violations: Log error with details about which constraint failed
   - Unique constraint violations: Return user-friendly message about duplicate data
   - Not null violations: Validate data before insertion

2. **Transaction Failures**
   - Wrap all multi-table operations in transactions
   - Rollback on any error to maintain consistency
   - Log transaction failures with full context

3. **Migration Errors**
   - Validate JSON structure before parsing
   - Handle missing or malformed data gracefully
   - Provide detailed error messages for debugging
   - Implement retry logic for transient failures

### Data Validation Errors

1. **Blueprint Validation**
   - Verify blueprint structure before processing
   - Check for required fields (uuid, name, type)
   - Validate data types and formats
   - Reject invalid blueprints with clear error messages

2. **Change Validation**
   - Verify object UUIDs exist before creating changes
   - Validate classification values against enum
   - Check display_order for duplicates
   - Ensure at least one object reference exists

3. **Review Validation**
   - Verify change_id exists before creating review
   - Validate review_status against allowed values
   - Check for duplicate reviews on same change

### Service Layer Error Handling

```python
class DataModelError(Exception):
    """Base exception for data model errors"""
    pass

class MigrationError(DataModelError):
    """Raised when migration fails"""
    pass

class ValidationError(DataModelError):
    """Raised when data validation fails"""
    pass

class IntegrityError(DataModelError):
    """Raised when referential integrity is violated"""
    pass
```

### Error Recovery Strategies

1. **Partial Migration Failure**
   - Rollback transaction for failed session
   - Continue with remaining sessions
   - Log all failures for manual review
   - Provide migration report with success/failure counts

2. **Query Failures**
   - Retry transient database errors (max 3 attempts)
   - Fall back to alternative query strategies
   - Cache results to reduce repeated queries
   - Log slow queries for optimization

3. **Data Inconsistency**
   - Implement verification checks after operations
   - Provide repair utilities for fixing inconsistencies
   - Alert administrators of data integrity issues
   - Maintain audit log of all data modifications

## Testing Strategy

### Unit Testing

Unit tests will verify individual components work correctly:

1. **Model Tests**
   - Test table creation and schema structure
   - Verify foreign key constraints are enforced
   - Test unique constraints prevent duplicates
   - Verify cascade deletes work correctly
   - Test indexes exist on expected columns

2. **Service Tests**
   - Test PackageService creates records correctly
   - Test ChangeService handles all change types
   - Test MigrationService extracts JSON correctly
   - Test query methods return expected results
   - Test error handling for invalid inputs

3. **Integration Tests**
   - Test complete session creation flow
   - Test migration of real session data
   - Test filtering and searching functionality
   - Test report generation with new schema
   - Test export functionality produces correct output

### Property-Based Testing

Property-based tests will verify universal properties hold across all inputs using the **Hypothesis** library for Python:

1. **Data Normalization Properties**
   - Property 1: Blueprint normalization (Requirements 1.1)
   - Property 2: Change foreign key validity (Requirements 1.2)
   - Property 3: Classification normalization (Requirements 1.3)
   - Property 4: Dependency table population (Requirements 1.5)

2. **Migration Properties**
   - Property 5: Session metadata preservation (Requirements 2.2)
   - Property 6: Blueprint migration round-trip (Requirements 2.3)
   - Property 7: Change ordering preservation (Requirements 2.4)
   - Property 8: Migration record count verification (Requirements 2.5)

3. **Functional Equivalence Properties**
   - Property 9: Filter result consistency (Requirements 3.2)
   - Property 10: Review action equivalence (Requirements 3.3)
   - Property 11: Export data completeness (Requirements 3.5)

4. **Query Correctness Properties**
   - Property 12: Object name search correctness (Requirements 4.2)
   - Property 13: Statistics calculation accuracy (Requirements 4.4)
   - Property 14: Dependency query correctness (Requirements 4.5)

5. **Data Integrity Properties**
   - Property 15: UUID uniqueness enforcement (Requirements 5.2)
   - Property 16: Cascade delete completeness (Requirements 5.4)
   - Property 17: Referential integrity enforcement (Requirements 5.5)

6. **Schema Structure Properties**
   - Property 18: Package storage correctness (Requirements 6.1)
   - Property 19: Object-package linkage (Requirements 6.2)
   - Property 20: Change-object linkage (Requirements 6.3)
   - Property 21: Review-change linkage (Requirements 6.4)
   - Property 22: Dependency storage correctness (Requirements 6.5)

### Test Configuration

Each property-based test will:
- Run a minimum of 100 iterations to ensure thorough coverage
- Use Hypothesis strategies to generate valid test data
- Be tagged with the format: `**Feature: merge-assistant-data-model-refactoring, Property N: [property text]**`
- Reference the specific correctness property from this design document

### Test Data Generators

Custom Hypothesis strategies will be created for:

1. **Blueprint Generator**
   - Generates valid blueprint structures with random objects
   - Includes various object types (interfaces, process models, etc.)
   - Creates realistic dependency relationships
   - Produces valid metadata

2. **Session Generator**
   - Generates complete session data with 3 packages
   - Creates random but valid comparison results
   - Produces classification data with all categories
   - Generates ordered changes with dependencies

3. **Change Generator**
   - Creates changes with valid classifications
   - Generates all change types (ADDED, MODIFIED, REMOVED)
   - Produces realistic object references
   - Creates valid merge guidance

### Performance Testing

Performance tests will verify query improvements:

1. **Baseline Measurements**
   - Measure JSON parsing time for large sessions
   - Measure filter operation time with JSON
   - Measure search operation time with JSON
   - Measure report generation time with JSON

2. **Optimized Measurements**
   - Measure JOIN query time for same sessions
   - Measure indexed filter operation time
   - Measure indexed search operation time
   - Measure report generation with SQL aggregates

3. **Performance Targets**
   - Filter operations: 10x faster than JSON parsing
   - Search operations: 20x faster than JSON parsing
   - Report generation: 5x faster than JSON parsing
   - Change loading: 3x faster than JSON deserialization

### Test Execution

Tests will be executed in the following order:

1. **Schema Tests** - Verify database structure
2. **Unit Tests** - Verify individual components
3. **Property Tests** - Verify universal properties
4. **Integration Tests** - Verify complete workflows
5. **Performance Tests** - Verify speed improvements
6. **Migration Tests** - Verify data migration correctness

All tests must pass before the refactoring is considered complete.

## Implementation Notes

### Batch Operations

For performance, use batch operations when possible:

```python
# Batch insert objects
db.session.bulk_insert_mappings(AppianObject, object_dicts)
db.session.commit()

# Batch insert dependencies
db.session.bulk_insert_mappings(ObjectDependency, dependency_dicts)
db.session.commit()
```

### Query Optimization

Use SQLAlchemy's query optimization features:

```python
# Use joinedload for eager loading
changes = db.session.query(Change)\
    .options(
        joinedload(Change.base_object),
        joinedload(Change.customer_object),
        joinedload(Change.vendor_object),
        joinedload(Change.review)
    )\
    .filter(Change.session_id == session_id)\
    .order_by(Change.display_order)\
    .all()
```

### Index Usage

Ensure queries use indexes by checking query plans:

```python
# Check if index is used
from sqlalchemy import text
result = db.session.execute(
    text("EXPLAIN QUERY PLAN SELECT * FROM changes WHERE session_id = ?"),
    {"session_id": 1}
)
```

### Memory Management

For large sessions, use pagination:

```python
# Paginate large result sets
page_size = 100
offset = 0
while True:
    changes = db.session.query(Change)\
        .filter(Change.session_id == session_id)\
        .order_by(Change.display_order)\
        .limit(page_size)\
        .offset(offset)\
        .all()
    
    if not changes:
        break
    
    # Process changes
    process_changes(changes)
    offset += page_size
```

### Transaction Management

Use context managers for transactions:

```python
from contextlib import contextmanager

@contextmanager
def transaction():
    try:
        yield
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

# Usage
with transaction():
    # Multiple operations
    create_package(...)
    create_objects(...)
    create_dependencies(...)
```

### Migration Best Practices

1. **Incremental Migration**
   - Migrate sessions one at a time
   - Commit after each successful migration
   - Continue on failure (don't stop entire process)

2. **Verification**
   - Verify each session after migration
   - Log verification results
   - Flag sessions that fail verification

3. **Rollback Strategy**
   - Keep old JSON columns until verification complete
   - Only drop columns after all sessions verified
   - Maintain backup of database before migration

4. **Progress Tracking**
   - Log migration progress (X of Y sessions)
   - Estimate time remaining
   - Provide detailed error messages

## Deployment Plan

### Phase 1: Schema Creation (Week 1)

1. Create migration script for new tables
2. Run migration on development database
3. Verify schema structure
4. Create indexes and constraints
5. Test schema with sample data

### Phase 2: Service Implementation (Week 2-3)

1. Implement PackageService
2. Implement ChangeService
3. Update ThreeWayMergeService
4. Write unit tests for all services
5. Write property-based tests

### Phase 3: Migration Implementation (Week 4)

1. Implement MigrationService
2. Test migration with sample sessions
3. Verify migration correctness
4. Optimize migration performance
5. Write migration tests

### Phase 4: Integration (Week 5)

1. Update controllers to use new services
2. Update templates if needed
3. Run integration tests
4. Test all API endpoints
5. Verify UI functionality

### Phase 5: Testing & Validation (Week 6)

1. Run complete test suite
2. Perform performance testing
3. Test with large sessions
4. Fix any issues found
5. Document any changes

### Phase 6: Production Migration (Week 7)

1. Backup production database
2. Run migration script
3. Verify all sessions migrated
4. Test production functionality
5. Monitor for issues

### Phase 7: Cleanup (Week 8)

1. Drop old JSON columns
2. Remove unused code
3. Update documentation
4. Optimize database (VACUUM)
5. Final verification

## Success Criteria

The refactoring will be considered successful when:

1. ✅ All 22 correctness properties pass with 100+ iterations each
2. ✅ All unit tests pass (100% coverage of new code)
3. ✅ All integration tests pass
4. ✅ Performance improvements meet targets (10x filter, 20x search, 5x reports)
5. ✅ All existing functionality works identically
6. ✅ Migration completes successfully for all sessions
7. ✅ Data integrity verification passes for all sessions
8. ✅ No orphaned data remains after cleanup
9. ✅ Database size reduced by at least 30% (due to normalization)
10. ✅ Query response times improved by at least 5x on average
