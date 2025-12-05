# Three-Way Merge Implementation Plan

**Part of:** Three-Way Merge Clean Architecture Specification  
**Version:** 1.0  
**Date:** 2025-11-30

---

## Implementation Strategy

### Approach: Clean Slate Rebuild

**Why Clean Slate?**
1. Current implementation has fundamental architectural flaws
2. Data duplication issues are pervasive
3. Easier to build correctly than fix incrementally
4. Allows proper OOP design from start
5. Reduces risk of carrying forward bugs

**Migration Strategy:**
1. Build new implementation in parallel
2. Keep old code temporarily (deprecated)
3. Test new implementation thoroughly
4. Switch over when ready
5. Remove old code

---

## Phase 1: Database Schema (Days 1-2)

### Tasks

**1.1 Create Migration Script**
```python
# migrations/004_three_way_merge_clean_schema.py

def upgrade():
    # Already exists: object_lookup, package_object_mappings, delta_comparison_results
    # Already exists: object_versions
    
    # Update changes table
    op.add_column('changes', sa.Column('object_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_changes_object', 'changes', 'object_lookup', ['object_id'], ['id'])
    op.create_index('idx_change_object', 'changes', ['object_id'])
    
    # Add object_id to all object-specific tables
    for table in ['interfaces', 'expression_rules', 'process_models', 'record_types', 
                  'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants', 
                  'connected_systems', 'unknown_objects']:
        op.add_column(table, sa.Column('object_id', sa.Integer(), nullable=True))
        op.create_foreign_key(f'fk_{table}_object', table, 'object_lookup', ['object_id'], ['id'])
        op.create_index(f'idx_{table}_object', table, ['object_id'])

def downgrade():
    # Remove columns and constraints
    pass
```

**1.2 Test Migration**
```bash
# Create test database
python -m pytest tests/test_migrations.py::test_migration_004 -v

# Verify schema
python scripts/verify_schema.py
```

**1.3 Validation Queries**
```sql
-- Verify no duplicates in object_lookup
SELECT uuid, COUNT(*) FROM object_lookup GROUP BY uuid HAVING COUNT(*) > 1;

-- Verify foreign keys
SELECT * FROM pragma_foreign_key_list('changes');
```

---

## Phase 2: Domain Models and Enums (Day 3)

### Tasks

**2.1 Create Enums**
```python
# domain/enums.py

from enum import Enum

class PackageType(Enum):
    BASE = 'base'
    CUSTOMIZED = 'customized'
    NEW_VENDOR = 'new_vendor'

class ChangeCategory(Enum):
    NEW = 'NEW'
    MODIFIED = 'MODIFIED'
    DEPRECATED = 'DEPRECATED'

class Classification(Enum):
    NO_CONFLICT = 'NO_CONFLICT'
    CONFLICT = 'CONFLICT'
    NEW = 'NEW'
    DELETED = 'DELETED'

class ChangeType(Enum):
    ADDED = 'ADDED'
    MODIFIED = 'MODIFIED'
    REMOVED = 'REMOVED'

class SessionStatus(Enum):
    PROCESSING = 'processing'
    READY = 'ready'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ERROR = 'error'
```

**2.2 Create Domain Entities**
```python
# domain/entities.py

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class ObjectIdentity:
    """Represents unique object identity"""
    uuid: str
    name: str
    object_type: str
    description: Optional[str] = None

@dataclass
class DeltaChange:
    """Represents A→C delta change"""
    object_id: int
    change_category: ChangeCategory
    version_changed: bool
    content_changed: bool

@dataclass
class CustomerModification:
    """Represents customer modification to an object"""
    object_id: int
    exists_in_customer: bool
    customer_modified: bool
    version_changed: bool
    content_changed: bool

@dataclass
class ClassifiedChange:
    """Represents classified change for working set"""
    object_id: int
    classification: Classification
    vendor_change_type: ChangeType
    customer_change_type: Optional[ChangeType]
    display_order: int
```

**2.3 Create Comparison Strategies**
```python
# domain/comparison_strategies.py

from abc import ABC, abstractmethod

class ComparisonStrategy(ABC):
    @abstractmethod
    def compare(self, obj_a: Any, obj_b: Any) -> bool:
        """Returns True if objects are different"""
        pass

class VersionComparisonStrategy(ComparisonStrategy):
    def compare(self, version_a: str, version_b: str) -> bool:
        return version_a != version_b

class ContentComparisonStrategy(ComparisonStrategy):
    def compare(self, content_a: str, content_b: str) -> bool:
        # Normalize and compare
        return self._normalize(content_a) != self._normalize(content_b)
    
    def _normalize(self, content: str) -> str:
        # Remove whitespace, comments, etc.
        pass
```

---

## Phase 3: Repository Layer (Days 4-5)

### Tasks

**3.1 Create Base Repository**
```python
# repositories/base_repository.py

class BaseRepository(ABC):
    def __init__(self, db_session):
        self.db = db_session
    
    @abstractmethod
    def find_by_id(self, id: int):
        pass
    
    @abstractmethod
    def find_all(self):
        pass
    
    @abstractmethod
    def create(self, entity):
        pass
    
    @abstractmethod
    def update(self, entity):
        pass
    
    @abstractmethod
    def delete(self, id: int):
        pass
```

**3.2 Implement Object Repositories**
```python
# repositories/object_lookup_repository.py

class ObjectLookupRepository(BaseRepository):
    def find_by_uuid(self, uuid: str) -> Optional[ObjectLookup]:
        return ObjectLookup.query.filter_by(uuid=uuid).first()
    
    def find_or_create(
        self,
        uuid: str,
        name: str,
        object_type: str,
        description: Optional[str] = None
    ) -> ObjectLookup:
        """
        Find existing object or create new one
        CRITICAL: Ensures no duplicates
        """
        obj = self.find_by_uuid(uuid)
        if obj:
            return obj
        
        obj = ObjectLookup(
            uuid=uuid,
            name=name,
            object_type=object_type,
            description=description
        )
        self.db.add(obj)
        self.db.flush()
        return obj
    
    def bulk_find_or_create(
        self,
        objects: List[Dict[str, Any]]
    ) -> List[ObjectLookup]:
        """Optimized bulk operation"""
        # Get existing UUIDs
        uuids = [obj['uuid'] for obj in objects]
        existing = ObjectLookup.query.filter(ObjectLookup.uuid.in_(uuids)).all()
        existing_map = {obj.uuid: obj for obj in existing}
        
        # Create new objects
        new_objects = []
        for obj_data in objects:
            if obj_data['uuid'] not in existing_map:
                new_obj = ObjectLookup(**obj_data)
                new_objects.append(new_obj)
        
        if new_objects:
            self.db.bulk_save_objects(new_objects)
            self.db.flush()
        
        # Return all objects
        return existing + new_objects
```

**3.3 Implement Mapping Repository**
```python
# repositories/package_object_mapping_repository.py

class PackageObjectMappingRepository(BaseRepository):
    def create_mapping(
        self,
        package_id: int,
        object_id: int
    ) -> PackageObjectMapping:
        """Create package-object mapping"""
        mapping = PackageObjectMapping(
            package_id=package_id,
            object_id=object_id
        )
        self.db.add(mapping)
        self.db.flush()
        return mapping
    
    def get_objects_in_package(
        self,
        package_id: int
    ) -> List[ObjectLookup]:
        """Get all objects in a package"""
        return (
            self.db.query(ObjectLookup)
            .join(PackageObjectMapping)
            .filter(PackageObjectMapping.package_id == package_id)
            .all()
        )
    
    def get_packages_for_object(
        self,
        object_id: int
    ) -> List[Package]:
        """Get all packages containing an object"""
        return (
            self.db.query(Package)
            .join(PackageObjectMapping)
            .filter(PackageObjectMapping.object_id == object_id)
            .all()
        )
    
    def bulk_create_mappings(
        self,
        mappings: List[Dict[str, int]]
    ) -> None:
        """Optimized bulk creation"""
        objects = [
            PackageObjectMapping(**mapping)
            for mapping in mappings
        ]
        self.db.bulk_save_objects(objects)
        self.db.flush()
```

**3.4 Implement Delta Comparison Repository**
```python
# repositories/delta_comparison_repository.py

class DeltaComparisonRepository(BaseRepository):
    def create_result(
        self,
        session_id: int,
        object_id: int,
        change_category: str,
        change_type: str,
        version_changed: bool,
        content_changed: bool
    ) -> DeltaComparisonResult:
        result = DeltaComparisonResult(
            session_id=session_id,
            object_id=object_id,
            change_category=change_category,
            change_type=change_type,
            version_changed=version_changed,
            content_changed=content_changed
        )
        self.db.add(result)
        self.db.flush()
        return result
    
    def bulk_create(
        self,
        results: List[DeltaComparisonResult]
    ) -> None:
        self.db.bulk_save_objects(results)
        self.db.flush()
    
    def get_by_session(
        self,
        session_id: int
    ) -> List[DeltaComparisonResult]:
        return (
            DeltaComparisonResult.query
            .filter_by(session_id=session_id)
            .all()
        )
    
    def get_by_category(
        self,
        session_id: int,
        category: str
    ) -> List[DeltaComparisonResult]:
        return (
            DeltaComparisonResult.query
            .filter_by(session_id=session_id, change_category=category)
            .all()
        )
```

**3.5 Write Repository Tests**
```python
# tests/repositories/test_object_lookup_repository.py

def test_find_or_create_new_object(db_session):
    repo = ObjectLookupRepository(db_session)
    
    obj = repo.find_or_create(
        uuid='test-uuid-123',
        name='Test Object',
        object_type='Interface'
    )
    
    assert obj.id is not None
    assert obj.uuid == 'test-uuid-123'

def test_find_or_create_existing_object(db_session):
    repo = ObjectLookupRepository(db_session)
    
    # Create first time
    obj1 = repo.find_or_create(
        uuid='test-uuid-123',
        name='Test Object',
        object_type='Interface'
    )
    
    # Find second time
    obj2 = repo.find_or_create(
        uuid='test-uuid-123',
        name='Test Object',
        object_type='Interface'
    )
    
    # Should be same object
    assert obj1.id == obj2.id

def test_no_duplicates_in_object_lookup(db_session):
    repo = ObjectLookupRepository(db_session)
    
    # Create multiple times
    for i in range(5):
        repo.find_or_create(
            uuid='test-uuid-123',
            name='Test Object',
            object_type='Interface'
        )
    
    # Verify only one entry
    count = ObjectLookup.query.filter_by(uuid='test-uuid-123').count()
    assert count == 1
```

---

## Phase 4: Parser Layer (Days 6-7)

### Tasks

**4.1 Create Base Parser**
```python
# services/parsers/base_parser.py

class BaseParser(ABC):
    def __init__(self, sail_cleaner: SAILCodeCleanerService):
        self.sail_cleaner = sail_cleaner
    
    @abstractmethod
    def parse(self, xml_path: str) -> Dict[str, Any]:
        pass
    
    def _extract_basic_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract common fields"""
        return {
            'uuid': root.get('uuid'),
            'name': root.get('name'),
            'version_uuid': root.get('versionUuid'),
            'description': self._get_text(root, 'description')
        }
    
    def _get_text(self, element: ET.Element, path: str) -> Optional[str]:
        """Safely get text from XML element"""
        elem = element.find(path)
        return elem.text if elem is not None else None
    
    def _clean_sail_code(self, sail_code: str) -> str:
        """Clean SAIL code"""
        return self.sail_cleaner.clean(sail_code)
```

**4.2 Implement Object-Specific Parsers**

Each parser must extract ALL relevant data from XML. Reference the XML samples in `applicationArtifacts/ObjectSpecificXml/`.

```python
# services/parsers/interface_parser.py

class InterfaceParser(BaseParser):
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        data = self._extract_basic_info(root)
        
        # SAIL code
        sail_elem = root.find('.//definition')
        if sail_elem is not None:
            data['sail_code'] = self._clean_sail_code(sail_elem.text)
        
        # Parameters
        data['parameters'] = []
        for param in root.findall('.//parameter'):
            data['parameters'].append({
                'name': param.get('name'),
                'type': param.get('type'),
                'required': param.get('required') == 'true',
                'default_value': param.get('defaultValue'),
                'display_order': int(param.get('order', 0))
            })
        
        # Security
        data['security'] = []
        for role in root.findall('.//security/role'):
            data['security'].append({
                'role_name': role.get('name'),
                'permission_type': role.get('permission')
            })
        
        return data
```

**4.3 Implement Process Model Parser**

Process models are complex - must extract nodes, flows, variables:

```python
# services/parsers/process_model_parser.py

class ProcessModelParser(BaseParser):
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        data = self._extract_basic_info(root)
        
        # Nodes
        data['nodes'] = []
        for node in root.findall('.//node'):
            data['nodes'].append({
                'node_id': node.get('id'),
                'node_type': node.get('type'),
                'node_name': node.get('name'),
                'properties': self._extract_node_properties(node)
            })
        
        # Flows
        data['flows'] = []
        for flow in root.findall('.//flow'):
            data['flows'].append({
                'from_node_id': flow.get('from'),
                'to_node_id': flow.get('to'),
                'flow_label': flow.get('label'),
                'flow_condition': flow.get('condition')
            })
        
        # Variables
        data['variables'] = []
        for var in root.findall('.//variable'):
            data['variables'].append({
                'variable_name': var.get('name'),
                'variable_type': var.get('type'),
                'is_parameter': var.get('parameter') == 'true',
                'default_value': var.get('defaultValue')
            })
        
        # Calculate complexity
        data['total_nodes'] = len(data['nodes'])
        data['total_flows'] = len(data['flows'])
        data['complexity_score'] = self._calculate_complexity(data)
        
        return data
```

**4.4 Write Parser Tests**

Test with REAL XML files from `applicationArtifacts/ObjectSpecificXml/`:

```python
# tests/parsers/test_interface_parser.py

def test_interface_parser_with_real_xml():
    parser = InterfaceParser(sail_cleaner)
    xml_path = 'applicationArtifacts/ObjectSpecificXml /interface.xml'
    
    data = parser.parse(xml_path)
    
    # Verify all fields extracted
    assert data['uuid'] is not None
    assert data['name'] is not None
    assert data['version_uuid'] is not None
    assert data['sail_code'] is not None
    assert len(data['parameters']) > 0
    assert len(data['security']) >= 0

def test_process_model_parser_with_real_xml():
    parser = ProcessModelParser(sail_cleaner)
    xml_path = 'applicationArtifacts/ObjectSpecificXml /processModel.xml'
    
    data = parser.parse(xml_path)
    
    # Verify all fields extracted
    assert data['uuid'] is not None
    assert data['name'] is not None
    assert len(data['nodes']) > 0
    assert len(data['flows']) > 0
    assert data['total_nodes'] == len(data['nodes'])
    assert data['complexity_score'] > 0
```

---

## Phase 5: Service Layer (Days 8-10)

### Tasks

**5.1 Implement PackageExtractionService**

See service design document for full implementation.

**5.2 Implement DeltaComparisonService**

See service design document for full implementation.

**5.3 Implement CustomerComparisonService**

See service design document for full implementation.

**5.4 Implement ClassificationService**

See service design document for full implementation.

**5.5 Implement ThreeWayMergeOrchestrator**

See service design document for full implementation.

**5.6 Write Service Tests**

```python
# tests/services/test_package_extraction_service.py

def test_extract_package_no_duplicates(test_packages):
    service = PackageExtractionService(...)
    
    # Extract same package twice
    pkg1 = service.extract_package(session_id, test_zip, 'base')
    pkg2 = service.extract_package(session_id, test_zip, 'base')
    
    # Verify no duplicates in object_lookup
    duplicates = (
        db.session.query(ObjectLookup.uuid, func.count(ObjectLookup.id))
        .group_by(ObjectLookup.uuid)
        .having(func.count(ObjectLookup.id) > 1)
        .all()
    )
    assert len(duplicates) == 0

def test_delta_comparison_service(test_packages):
    service = DeltaComparisonService(...)
    
    results = service.compare(session_id, pkg_a_id, pkg_c_id)
    
    # Verify results stored
    assert len(results) > 0
    
    # Verify categories
    categories = {r.change_category for r in results}
    assert 'NEW' in categories or 'MODIFIED' in categories or 'DEPRECATED' in categories
```

---

## Phase 6: Integration Testing (Days 11-12)

### Tasks

**6.1 End-to-End Test with Real Packages**

```python
# tests/integration/test_three_way_merge_e2e.py

def test_complete_merge_workflow():
    """Test complete workflow with real test packages"""
    
    # Paths to test packages
    base_zip = 'applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip'
    customer_zip = 'applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip'
    vendor_zip = 'applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip'
    
    # Create orchestrator
    orchestrator = ThreeWayMergeOrchestrator(...)
    
    # Run workflow
    session = orchestrator.create_merge_session(base_zip, customer_zip, vendor_zip)
    
    # Verify session created
    assert session.reference_id is not None
    assert session.status == 'ready'
    
    # Verify no duplicates
    duplicates = (
        db.session.query(ObjectLookup.uuid, func.count(ObjectLookup.id))
        .group_by(ObjectLookup.uuid)
        .having(func.count(ObjectLookup.id) > 1)
        .all()
    )
    assert len(duplicates) == 0
    
    # Verify delta-driven working set
    delta_count = DeltaComparisonResult.query.filter_by(session_id=session.id).count()
    change_count = Change.query.filter_by(session_id=session.id).count()
    assert delta_count == change_count
    
    # Verify known objects exist
    known_uuids = [
        'de199b3f-b072-4438-9508-3b6594827eaf',  # Process Model 1
        '2c8de7e9-23b9-40d6-afc2-233a963832be',  # Process Model 2
        '57318b79-0bfd-45c4-a07e-ceae8277e0fb',  # Record Type
    ]
    for uuid in known_uuids:
        obj = ObjectLookup.query.filter_by(uuid=uuid).first()
        assert obj is not None
    
    # Verify classifications
    classifications = (
        db.session.query(Change.classification, func.count(Change.id))
        .filter_by(session_id=session.id)
        .group_by(Change.classification)
        .all()
    )
    assert len(classifications) > 0
```

**6.2 Property-Based Tests**

```python
# tests/integration/test_invariants.py

def test_no_duplicates_invariant(db_session):
    """Property: No UUID should appear more than once in object_lookup"""
    duplicates = (
        db_session.query(ObjectLookup.uuid, func.count(ObjectLookup.id))
        .group_by(ObjectLookup.uuid)
        .having(func.count(ObjectLookup.id) > 1)
        .all()
    )
    assert len(duplicates) == 0, f"Found duplicates: {duplicates}"

def test_delta_driven_invariant(db_session, session_id):
    """Property: Working set should only contain delta objects"""
    delta_object_ids = {
        r.object_id 
        for r in DeltaComparisonResult.query.filter_by(session_id=session_id).all()
    }
    
    change_object_ids = {
        c.object_id 
        for c in Change.query.filter_by(session_id=session_id).all()
    }
    
    # All changes should be in delta
    assert change_object_ids.issubset(delta_object_ids)

def test_referential_integrity_invariant(db_session, session_id):
    """Property: All object_id references should be valid"""
    # Check changes table
    invalid_changes = (
        db_session.query(Change)
        .outerjoin(ObjectLookup, Change.object_id == ObjectLookup.id)
        .filter(ObjectLookup.id.is_(None))
        .filter(Change.session_id == session_id)
        .count()
    )
    assert invalid_changes == 0
```

---

## Phase 7: Controller and UI Updates (Days 13-14)

### Tasks

**7.1 Update Controller**

```python
# controllers/new_merge_assistant_controller.py

@merge_bp.route('/merge/create', methods=['POST'])
def create_merge_session():
    """Create new merge session"""
    try:
        # Get uploaded files
        base_file = request.files['base_package']
        customer_file = request.files['customized_package']
        vendor_file = request.files['new_vendor_package']
        
        # Save files
        base_path = save_upload(base_file)
        customer_path = save_upload(customer_file)
        vendor_path = save_upload(vendor_file)
        
        # Create orchestrator
        orchestrator = container.get_service(ThreeWayMergeOrchestrator)
        
        # Run workflow
        session = orchestrator.create_merge_session(
            base_path, customer_path, vendor_path
        )
        
        return jsonify({
            'success': True,
            'reference_id': session.reference_id,
            'total_changes': session.total_changes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@merge_bp.route('/merge/<reference_id>/summary')
def get_merge_summary(reference_id):
    """Get merge session summary"""
    session = MergeSession.query.filter_by(reference_id=reference_id).first_or_404()
    
    # Get statistics
    stats = (
        db.session.query(
            Change.classification,
            func.count(Change.id).label('count')
        )
        .filter_by(session_id=session.id)
        .group_by(Change.classification)
        .all()
    )
    
    return render_template(
        'merge/summary.html',
        session=session,
        statistics=stats
    )
```

**7.2 Update Templates**

Remove customer-only sections, update to use new data model.

---

## Phase 8: Performance Optimization (Days 15-16)

### Tasks

**8.1 Add Database Indexes**

Already included in schema design.

**8.2 Optimize Queries**

```python
# Use eager loading
changes = (
    Change.query
    .filter_by(session_id=session_id)
    .options(joinedload(Change.object_lookup))
    .all()
)

# Use bulk operations
repo.bulk_create_mappings(mappings)
```

**8.3 Add Caching**

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_object_by_uuid(uuid: str) -> ObjectLookup:
    return ObjectLookup.query.filter_by(uuid=uuid).first()
```

---

## Phase 9: Documentation (Day 17)

### Tasks

**9.1 Update README**
**9.2 Create API Documentation**
**9.3 Update Development Log**

---

## Phase 10: Deployment (Days 18-19)

### Tasks

**10.1 Run All Tests**
```bash
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**10.2 Deploy to Staging**
**10.3 Manual Testing**
**10.4 Deploy to Production**
**10.5 Remove Deprecated Code**

---

## Success Criteria

✅ **Zero Data Duplication**: Each object stored exactly once  
✅ **100% Rule Coverage**: All 7 classification rules implemented  
✅ **Delta-Driven**: Working set contains only delta objects  
✅ **Performance**: All queries < 200ms  
✅ **Test Coverage**: >80% for all new code  
✅ **Zero Deprecated Code**: All deprecated services removed  

---

*End of Implementation Plan*
