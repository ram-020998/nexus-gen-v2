# Three-Way Merge Quick Reference Guide

**For Developers Implementing the New Architecture**

---

## Quick Links

- **Executive Summary**: `three-way-merge-executive-summary.md`
- **Database Schema**: `three-way-merge-database-schema.md`
- **Service Design**: `three-way-merge-service-design.md`
- **Implementation Plan**: `three-way-merge-implementation-plan.md`

---

## Core Concepts

### The Three Packages

- **Package A**: Vendor Base Version (original)
- **Package B**: Customer Customized Version (with customer changes)
- **Package C**: Vendor New Version (latest from vendor)

### The Delta

**Delta = A→C comparison**

Identifies what changed in the vendor package:
- NEW: Objects added in C
- MODIFIED: Objects changed in C
- DEPRECATED: Objects removed in C

### The Working Set

**Working Set = Delta objects classified against B**

Only contains objects from the delta, classified as:
- NO_CONFLICT: Can be auto-merged
- CONFLICT: Requires manual review
- NEW: New vendor object to add
- DELETED: Object removed by customer

---

## Database Tables Cheat Sheet

### Core Tables

```
object_lookup
├── id (PK)
├── uuid (UNIQUE) ← NO package_id!
├── name
├── object_type
└── description

package_object_mappings
├── id (PK)
├── package_id (FK → packages)
├── object_id (FK → object_lookup)
└── UNIQUE(package_id, object_id)

delta_comparison_results
├── id (PK)
├── session_id (FK → merge_sessions)
├── object_id (FK → object_lookup)
├── change_category (NEW, MODIFIED, DEPRECATED)
├── change_type (ADDED, MODIFIED, REMOVED)
├── version_changed (BOOLEAN)
└── content_changed (BOOLEAN)

changes
├── id (PK)
├── session_id (FK → merge_sessions)
├── object_id (FK → object_lookup) ← NEW!
├── classification (NO_CONFLICT, CONFLICT, NEW, DELETED)
├── vendor_change_type
├── customer_change_type
└── display_order
```

---

## Classification Rules Quick Reference

```python
def classify(delta_category, exists_in_customer, customer_modified):
    if delta_category == 'NEW':
        return 'NEW'  # Rule 10d
    
    elif delta_category == 'MODIFIED':
        if not exists_in_customer:
            return 'DELETED'  # Rule 10c
        elif customer_modified:
            return 'CONFLICT'  # Rule 10b
        else:
            return 'NO_CONFLICT'  # Rule 10a
    
    elif delta_category == 'DEPRECATED':
        if not exists_in_customer:
            return 'NO_CONFLICT'  # Rule 10g
        elif customer_modified:
            return 'CONFLICT'  # Rule 10f
        else:
            return 'NO_CONFLICT'  # Rule 10e
```

---

## Common Queries

### Get all objects in a package
```python
objects = (
    db.session.query(ObjectLookup)
    .join(PackageObjectMapping)
    .filter(PackageObjectMapping.package_id == package_id)
    .all()
)
```

### Get all packages containing an object
```python
packages = (
    db.session.query(Package)
    .join(PackageObjectMapping)
    .filter(PackageObjectMapping.object_id == object_id)
    .all()
)
```

### Get delta results for a session
```python
delta_results = (
    DeltaComparisonResult.query
    .filter_by(session_id=session_id)
    .all()
)
```

### Get working set for a session
```python
changes = (
    Change.query
    .filter_by(session_id=session_id)
    .options(joinedload(Change.object_lookup))
    .order_by(Change.display_order)
    .all()
)
```

### Check for duplicates (should return 0)
```python
duplicates = (
    db.session.query(ObjectLookup.uuid, func.count(ObjectLookup.id))
    .group_by(ObjectLookup.uuid)
    .having(func.count(ObjectLookup.id) > 1)
    .all()
)
```

---

## Repository Pattern

### Always use find_or_create for object_lookup

```python
# ✅ CORRECT
obj = object_lookup_repo.find_or_create(
    uuid='abc-123',
    name='My Object',
    object_type='Interface'
)

# ❌ WRONG - Creates duplicates
obj = ObjectLookup(uuid='abc-123', name='My Object', object_type='Interface')
db.session.add(obj)
```

### Always create package_object_mapping

```python
# After creating/finding object
mapping = package_object_mapping_repo.create_mapping(
    package_id=package.id,
    object_id=obj.id
)
```

---

## Parser Pattern

### Base Parser Structure

```python
class MyObjectParser(BaseParser):
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 1. Extract basic info
        data = self._extract_basic_info(root)
        
        # 2. Extract object-specific fields
        data['field1'] = self._get_text(root, 'field1')
        data['field2'] = self._extract_complex_field(root)
        
        # 3. Clean SAIL code if applicable
        if 'sail_code' in data:
            data['sail_code'] = self._clean_sail_code(data['sail_code'])
        
        return data
```

---

## Service Pattern

### Service Constructor

```python
class MyService:
    def __init__(
        self,
        repo1: Repository1,
        repo2: Repository2,
        logger: Logger
    ):
        self.repo1 = repo1
        self.repo2 = repo2
        self.logger = logger
```

### Service Method

```python
def process(self, session_id: int) -> Result:
    try:
        self.logger.info(f"Processing session {session_id}")
        
        # 1. Get data
        data = self.repo1.get_data(session_id)
        
        # 2. Process
        result = self._process_data(data)
        
        # 3. Store
        self.repo2.save(result)
        
        self.logger.info("Processing complete")
        return result
        
    except Exception as e:
        self.logger.error(f"Error: {e}")
        raise
```

---

## Testing Patterns

### Repository Test

```python
def test_find_or_create_no_duplicates(db_session):
    repo = ObjectLookupRepository(db_session)
    
    # Create multiple times
    for i in range(5):
        obj = repo.find_or_create(
            uuid='test-uuid',
            name='Test',
            object_type='Interface'
        )
    
    # Verify only one entry
    count = ObjectLookup.query.filter_by(uuid='test-uuid').count()
    assert count == 1
```

### Service Test

```python
def test_service_with_mocks():
    # Mock dependencies
    mock_repo = Mock(spec=Repository)
    mock_repo.get_data.return_value = test_data
    
    # Create service
    service = MyService(mock_repo, logger)
    
    # Test
    result = service.process(session_id=1)
    
    # Verify
    assert result is not None
    mock_repo.get_data.assert_called_once_with(1)
```

### Integration Test

```python
def test_e2e_with_real_packages():
    # Use real test packages
    base_zip = 'applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip'
    
    # Run workflow
    orchestrator = ThreeWayMergeOrchestrator(...)
    session = orchestrator.create_merge_session(base_zip, customer_zip, vendor_zip)
    
    # Verify invariants
    assert_no_duplicates(session.id)
    assert_delta_driven(session.id)
    assert_all_rules_applied(session.id)
```

---

## Common Pitfalls

### ❌ DON'T: Add package_id to object_lookup

```python
# ❌ WRONG
class ObjectLookup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer)  # NO!
    uuid = db.Column(db.String(255))
```

### ✅ DO: Use package_object_mappings

```python
# ✅ CORRECT
class ObjectLookup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(255), unique=True)
    # NO package_id!

class PackageObjectMapping(db.Model):
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'))
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id'))
```

### ❌ DON'T: Include customer-only in working set

```python
# ❌ WRONG
if object_only_in_customer:
    change = Change(classification='CUSTOMER_ONLY')  # NO!
```

### ✅ DO: Only include delta objects

```python
# ✅ CORRECT
# Only process objects from delta_comparison_results
for delta_result in delta_results:
    change = classify(delta_result, customer_data)
    # change will be NO_CONFLICT, CONFLICT, NEW, or DELETED
```

### ❌ DON'T: Store duplicate data in changes table

```python
# ❌ WRONG
change = Change(
    object_id=obj.id,
    object_uuid=obj.uuid,  # Redundant!
    object_name=obj.name,  # Redundant!
    object_type=obj.object_type  # Redundant!
)
```

### ✅ DO: Reference object_lookup

```python
# ✅ CORRECT
change = Change(
    object_id=obj.id  # Only reference
)
# Get name/type via: change.object_lookup.name
```

---

## Debugging Tips

### Check for duplicates

```python
from sqlalchemy import func

duplicates = (
    db.session.query(ObjectLookup.uuid, func.count(ObjectLookup.id))
    .group_by(ObjectLookup.uuid)
    .having(func.count(ObjectLookup.id) > 1)
    .all()
)
print(f"Duplicates: {duplicates}")
```

### Verify delta-driven

```python
delta_count = DeltaComparisonResult.query.filter_by(session_id=session_id).count()
change_count = Change.query.filter_by(session_id=session_id).count()
print(f"Delta: {delta_count}, Changes: {change_count}")
assert delta_count == change_count
```

### Check object mappings

```python
# How many packages contain this object?
mapping_count = (
    PackageObjectMapping.query
    .filter_by(object_id=obj.id)
    .count()
)
print(f"Object {obj.uuid} in {mapping_count} packages")
```

---

## Test Package Locations

```
applicationArtifacts/
├── Three Way Testing Files/
│   └── V2/
│       ├── Test Application - Base Version.zip (A)
│       ├── Test Application Customer Version.zip (B)
│       └── Test Application Vendor New Version.zip (C)
└── ObjectSpecificXml /
    ├── interface.xml
    ├── expressionRule.xml
    ├── processModel.xml
    ├── recordType.xml
    ├── dataType.xsd
    ├── integration.xml
    ├── webApi.xml
    ├── site.xml
    ├── group.xml
    ├── constant.xml
    └── connectedSystem.xml
```

---

## Running Tests

```bash
# All tests
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Specific test file
python -m pytest tests/test_file.py -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Specific test
python -m pytest tests/test_file.py::test_name -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# With coverage
python -m pytest --cov=services --cov-report=html > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

---

## Key Files

```
services/
├── merge/
│   ├── three_way_merge_orchestrator.py ← Main entry point
│   ├── package_extraction_service.py
│   ├── delta_comparison_service.py
│   ├── customer_comparison_service.py
│   ├── classification_service.py
│   └── merge_guidance_service.py
├── parsers/
│   ├── base_parser.py
│   ├── interface_parser.py
│   ├── process_model_parser.py
│   └── ... (other parsers)
└── comparison_strategies/
    ├── version_comparison_strategy.py
    └── content_comparison_strategy.py

repositories/
├── object_lookup_repository.py
├── package_object_mapping_repository.py
├── delta_comparison_repository.py
├── change_repository.py
└── extraction/
    ├── interface_repository.py
    ├── process_model_repository.py
    └── ... (other object repositories)

domain/
├── enums.py
├── entities.py
└── comparison_strategies.py

models.py ← Database models
```

---

## Workflow Summary

```
1. Upload packages (A, B, C)
   ↓
2. Extract packages
   - Parse XML
   - find_or_create in object_lookup
   - Create package_object_mappings
   - Store object-specific data
   ↓
3. Delta comparison (A→C)
   - Identify NEW, MODIFIED, DEPRECATED
   - Store in delta_comparison_results
   ↓
4. Customer comparison (delta vs B)
   - Check existence in B
   - Check modifications in B
   ↓
5. Classify changes
   - Apply 7 rules
   - Create Change records
   ↓
6. Generate guidance
   - Analyze conflicts
   - Create recommendations
   ↓
7. User reviews working set
```

---

## Remember

1. **NO duplicates** - Use `find_or_create()`
2. **NO package_id in object_lookup** - It's global!
3. **NO customer-only** - Only delta objects
4. **ALL 7 rules** - No shortcuts
5. **Test with real packages** - No mocks for integration tests

---

*Quick Reference Guide - Keep this handy while implementing!*
