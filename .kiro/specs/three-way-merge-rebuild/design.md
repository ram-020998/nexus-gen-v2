# Design Document

## Overview

This document describes the architecture and design for rebuilding the three-way merge functionality. The system will follow clean architecture principles with clear separation between data access (repositories), business logic (services), and presentation (controllers). The core design eliminates data duplication by using a global object registry and explicit package-object mappings.

**Reference Documents:**
- Database Schema: `.kiro/specs/three-way-merge-database-schema.md`
- Service Design: `.kiro/specs/three-way-merge-service-design.md`
- Implementation Plan: `.kiro/specs/three-way-merge-implementation-plan.md`
- Quick Reference: `.kiro/specs/three-way-merge-quick-reference.md`
- Architecture Diagrams: `.kiro/specs/three-way-merge-architecture-diagrams.md`
- UI Templates: `.kiro/specs/three-way-merge-ui-templates.md` (Parts 1-3)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   Controllers    │  │    Templates     │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         ThreeWayMergeOrchestrator                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │  Package     │ │    Delta     │ │  Customer        │  │
│  │  Extraction  │ │  Comparison  │ │  Comparison      │  │
│  └──────────────┘ └──────────────┘ └──────────────────┘  │
│  ┌──────────────┐ ┌──────────────┐                       │
│  │Classification│ │    Merge     │                       │
│  │   Service    │ │   Guidance   │                       │
│  └──────────────┘ └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Repository Layer                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │   Object     │ │   Package    │ │     Delta        │  │
│  │   Lookup     │ │   Object     │ │   Comparison     │  │
│  │   Repo       │ │   Mapping    │ │     Repo         │  │
│  └──────────────┘ └──────────────┘ └──────────────────┘  │
│  ┌──────────────┐ ┌──────────────┐                       │
│  │    Change    │ │   Object     │                       │
│  │     Repo     │ │  Specific    │                       │
│  │              │ │    Repos     │                       │
│  └──────────────┘ └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │   object_    │ │   package_   │ │     delta_       │  │
│  │   lookup     │ │   object_    │ │   comparison_    │  │
│  │              │ │   mappings   │ │    results       │  │
│  └──────────────┘ └──────────────┘ └──────────────────┘  │
│  ┌──────────────┐ ┌──────────────┐                       │
│  │   changes    │ │   Object     │                       │
│  │              │ │  Specific    │                       │
│  │              │ │   Tables     │                       │
│  └──────────────┘ └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns

1. **Repository Pattern**: All database access through repository classes
2. **Service Layer Pattern**: Business logic in service classes
3. **Factory Pattern**: XMLParserFactory creates appropriate parsers
4. **Strategy Pattern**: Comparison strategies for version and content comparison
5. **Dependency Injection**: Services receive dependencies via constructor
6. **Orchestrator Pattern**: ThreeWayMergeOrchestrator coordinates workflow

## Components and Interfaces

### Domain Layer

#### Enums

```python
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

#### Domain Entities

```python
@dataclass
class ObjectIdentity:
    uuid: str
    name: str
    object_type: str
    description: Optional[str] = None

@dataclass
class DeltaChange:
    object_id: int
    change_category: ChangeCategory
    version_changed: bool
    content_changed: bool

@dataclass
class CustomerModification:
    object_id: int
    exists_in_customer: bool
    customer_modified: bool
    version_changed: bool
    content_changed: bool

@dataclass
class ClassifiedChange:
    object_id: int
    classification: Classification
    vendor_change_type: ChangeType
    customer_change_type: Optional[ChangeType]
    display_order: int
```

### Repository Layer

#### BaseRepository

```python
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

#### ObjectLookupRepository

```python
class ObjectLookupRepository(BaseRepository):
    def find_by_uuid(self, uuid: str) -> Optional[ObjectLookup]:
        """Find object by UUID"""
        pass
    
    def find_or_create(
        self,
        uuid: str,
        name: str,
        object_type: str,
        description: Optional[str] = None
    ) -> ObjectLookup:
        """
        Find existing object or create new one.
        CRITICAL: Ensures no duplicates in object_lookup.
        """
        pass
    
    def bulk_find_or_create(
        self,
        objects: List[Dict[str, Any]]
    ) -> List[ObjectLookup]:
        """Optimized bulk operation"""
        pass
```

#### PackageObjectMappingRepository

```python
class PackageObjectMappingRepository(BaseRepository):
    def create_mapping(
        self,
        package_id: int,
        object_id: int
    ) -> PackageObjectMapping:
        """Create package-object mapping"""
        pass
    
    def get_objects_in_package(
        self,
        package_id: int
    ) -> List[ObjectLookup]:
        """Get all objects in a package"""
        pass
    
    def get_packages_for_object(
        self,
        object_id: int
    ) -> List[Package]:
        """Get all packages containing an object"""
        pass
    
    def bulk_create_mappings(
        self,
        mappings: List[Dict[str, int]]
    ) -> None:
        """Optimized bulk creation"""
        pass
```

### Service Layer

#### ThreeWayMergeOrchestrator

**Reference**: See `.kiro/specs/three-way-merge-service-design.md` section 1 for complete implementation.

```python
class ThreeWayMergeOrchestrator:
    def __init__(
        self,
        package_extraction_service: PackageExtractionService,
        delta_comparison_service: DeltaComparisonService,
        customer_comparison_service: CustomerComparisonService,
        classification_service: ClassificationService,
        merge_guidance_service: MergeGuidanceService,
        dependency_analysis_service: DependencyAnalysisService,
        merge_session_repository: MergeSessionRepository,
        logger: Logger
    ):
        pass
    
    def create_merge_session(
        self,
        base_zip_path: str,
        customized_zip_path: str,
        new_vendor_zip_path: str
    ) -> MergeSession:
        """
        Create and process a new merge session.
        
        Workflow:
        1. Create session record
        2. Extract all three packages (transactional)
        3. Perform delta comparison (A→C)
        4. Perform customer comparison (delta vs B)
        5. Classify changes (apply 7 rules)
        6. Generate merge guidance
        7. Analyze dependencies
        8. Update session status to 'ready'
        
        Returns:
            MergeSession with reference_id and total_changes
        """
        pass
    
    def get_session_status(self, reference_id: str) -> Dict[str, Any]:
        """Get current status of merge session"""
        pass
    
    def get_working_set(
        self,
        reference_id: str,
        classification_filter: Optional[List[str]] = None
    ) -> List[Change]:
        """Get working set of changes for review"""
        pass
```

#### PackageExtractionService

**Reference**: See `.kiro/specs/three-way-merge-service-design.md` section 2 for complete implementation.

```python
class PackageExtractionService:
    def __init__(
        self,
        zip_extractor: ZipExtractorService,
        parser_factory: XMLParserFactory,
        sail_cleaner: SAILCodeCleanerService,
        object_lookup_repo: ObjectLookupRepository,
        package_object_mapping_repo: PackageObjectMappingRepository,
        object_version_repo: ObjectVersionRepository,
        object_repositories: Dict[str, BaseObjectRepository],
        logger: Logger
    ):
        pass
    
    def extract_package(
        self,
        session_id: int,
        zip_path: str,
        package_type: str
    ) -> Package:
        """
        Extract package and store all objects.
        
        Steps:
        1. Create package record
        2. Extract ZIP to temp directory
        3. Find all XML files
        4. Parse each XML file
        5. For each object:
           a. Find or create in object_lookup (NO DUPLICATES!)
           b. Create package_object_mapping
           c. Store object-specific data in object tables
           d. Store version data in object_versions
        6. Update package statistics
        7. Clean up temp directory
        
        Returns:
            Package object with total_objects count
        """
        pass
    
    def _process_object(
        self,
        package_id: int,
        xml_path: str,
        object_type: str
    ) -> ObjectLookup:
        """Process single object from XML"""
        pass
```

#### DeltaComparisonService

**Reference**: See `.kiro/specs/three-way-merge-service-design.md` section 3 for complete implementation.

```python
class DeltaComparisonService:
    def __init__(
        self,
        object_lookup_repo: ObjectLookupRepository,
        package_object_mapping_repo: PackageObjectMappingRepository,
        delta_comparison_repo: DeltaComparisonRepository,
        object_version_repo: ObjectVersionRepository,
        version_comparison_strategy: VersionComparisonStrategy,
        content_comparison_strategy: ContentComparisonStrategy,
        logger: Logger
    ):
        pass
    
    def compare(
        self,
        session_id: int,
        base_package_id: int,
        new_vendor_package_id: int
    ) -> List[DeltaComparisonResult]:
        """
        Compare A→C to identify vendor delta.
        
        Steps:
        1. Get objects in package A (via package_object_mappings)
        2. Get objects in package C (via package_object_mappings)
        3. Identify NEW objects (in C, not in A) → change_category='NEW'
        4. Identify DEPRECATED objects (in A, not in C) → change_category='DEPRECATED'
        5. Identify MODIFIED objects (in both A and C):
           a. Compare version UUIDs
           b. If version changed, mark version_changed=True
           c. If version same, compare content
           d. If content changed, mark content_changed=True
        6. Store results in delta_comparison_results
        
        Returns:
            List of DeltaComparisonResult objects
        """
        pass
    
    def _compare_versions(
        self,
        obj_lookup: ObjectLookup,
        base_package_id: int,
        new_package_id: int
    ) -> Tuple[bool, bool]:
        """
        Compare versions of an object.
        
        Returns:
            (version_changed, content_changed)
        """
        pass
```

#### ClassificationService

**Reference**: See `.kiro/specs/three-way-merge-service-design.md` section 5 for complete implementation.

```python
class ClassificationService:
    def __init__(
        self,
        change_repository: ChangeRepository,
        classification_rule_engine: ClassificationRuleEngine,
        logger: Logger
    ):
        pass
    
    def classify(
        self,
        session_id: int,
        delta_results: List[DeltaComparisonResult],
        customer_comparison: Dict[int, Dict[str, Any]]
    ) -> List[Change]:
        """
        Classify changes using 7 rules.
        
        For each delta object:
        1. Get delta change category (NEW, MODIFIED, DEPRECATED)
        2. Get customer comparison data (exists_in_customer, customer_modified)
        3. Apply classification rule (see ClassificationRuleEngine)
        4. Create Change record with object_id reference
        5. Set display_order for consistent presentation
        
        Returns:
            List of Change objects (count should equal delta_results count)
        """
        pass
```

#### ClassificationRuleEngine

**Reference**: See `.kiro/specs/three-way-merge-quick-reference.md` for classification rules.

```python
class ClassificationRuleEngine:
    def classify(
        self,
        delta_category: str,
        customer_data: Dict[str, Any]
    ) -> str:
        """
        Apply 7 classification rules:
        
        Rule 10a: MODIFIED in delta AND not modified in customer → NO_CONFLICT
        Rule 10b: MODIFIED in delta AND modified in customer → CONFLICT
        Rule 10c: MODIFIED in delta AND removed in customer → DELETED
        Rule 10d: NEW in delta → NEW
        Rule 10e: DEPRECATED in delta AND not modified in customer → NO_CONFLICT
        Rule 10f: DEPRECATED in delta AND modified in customer → CONFLICT
        Rule 10g: DEPRECATED in delta AND removed in customer → NO_CONFLICT
        
        Returns:
            Classification: NO_CONFLICT, CONFLICT, NEW, or DELETED
        """
        exists_in_customer = customer_data.get('exists_in_customer', False)
        customer_modified = customer_data.get('customer_modified', False)
        
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
        
        else:
            raise ValueError(f"Unknown delta category: {delta_category}")
```

### Parser Layer

**Reference**: See `.kiro/specs/three-way-merge-implementation-plan.md` Phase 4 for parser implementation details.

**XML Samples**: Use files in `applicationArtifacts/ObjectSpecificXml/` for testing parsers.

#### XMLParserFactory

```python
class XMLParserFactory:
    def __init__(self, sail_cleaner: SAILCodeCleanerService):
        self.sail_cleaner = sail_cleaner
        self.parsers = {
            'Interface': InterfaceParser(sail_cleaner),
            'Expression Rule': ExpressionRuleParser(sail_cleaner),
            'Process Model': ProcessModelParser(sail_cleaner),
            'Record Type': RecordTypeParser(sail_cleaner),
            'CDT': CDTParser(sail_cleaner),
            'Integration': IntegrationParser(sail_cleaner),
            'Web API': WebAPIParser(sail_cleaner),
            'Site': SiteParser(sail_cleaner),
            'Group': GroupParser(sail_cleaner),
            'Constant': ConstantParser(sail_cleaner),
            'Connected System': ConnectedSystemParser(sail_cleaner),
        }
    
    def get_parser(self, object_type: str) -> BaseParser:
        return self.parsers.get(object_type, UnknownObjectParser(self.sail_cleaner))
```

#### BaseParser

```python
class BaseParser(ABC):
    def __init__(self, sail_cleaner: SAILCodeCleanerService):
        self.sail_cleaner = sail_cleaner
    
    @abstractmethod
    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse XML file and extract object data.
        
        Must extract ALL relevant data from XML.
        
        Returns:
            Dict with keys:
            - uuid: str
            - name: str
            - version_uuid: str
            - description: str
            - <object_specific_fields>
        """
        pass
    
    def _extract_basic_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract common fields (uuid, name, version_uuid)"""
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
        """Clean SAIL code for comparison"""
        return self.sail_cleaner.clean(sail_code)
```

#### InterfaceParser

**Reference**: Test with `applicationArtifacts/ObjectSpecificXml /interface.xml`

```python
class InterfaceParser(BaseParser):
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        data = self._extract_basic_info(root)
        
        # Extract SAIL code
        sail_elem = root.find('.//definition')
        if sail_elem is not None:
            data['sail_code'] = self._clean_sail_code(sail_elem.text)
        
        # Extract parameters
        data['parameters'] = []
        for param in root.findall('.//parameter'):
            data['parameters'].append({
                'name': param.get('name'),
                'type': param.get('type'),
                'required': param.get('required') == 'true',
                'default_value': param.get('defaultValue'),
                'display_order': int(param.get('order', 0))
            })
        
        # Extract security
        data['security'] = []
        for role in root.findall('.//security/role'):
            data['security'].append({
                'role_name': role.get('name'),
                'permission_type': role.get('permission')
            })
        
        return data
```

#### ProcessModelParser

**Reference**: Test with `applicationArtifacts/ObjectSpecificXml /processModel.xml`

```python
class ProcessModelParser(BaseParser):
    def parse(self, xml_path: str) -> Dict[str, Any]:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        data = self._extract_basic_info(root)
        
        # Extract nodes
        data['nodes'] = []
        for node in root.findall('.//node'):
            data['nodes'].append({
                'node_id': node.get('id'),
                'node_type': node.get('type'),
                'node_name': node.get('name'),
                'properties': self._extract_node_properties(node)
            })
        
        # Extract flows
        data['flows'] = []
        for flow in root.findall('.//flow'):
            data['flows'].append({
                'from_node_id': flow.get('from'),
                'to_node_id': flow.get('to'),
                'flow_label': flow.get('label'),
                'flow_condition': flow.get('condition')
            })
        
        # Extract variables
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
    
    def _calculate_complexity(self, data: Dict) -> float:
        """Calculate process model complexity score"""
        # McCabe complexity: nodes + flows - 2
        return data['total_nodes'] + data['total_flows'] - 2
```

## Data Models

**Reference**: See `.kiro/specs/three-way-merge-database-schema.md` for complete schema details.

### Core Tables

#### object_lookup (Global Object Registry)

**Purpose**: Single source of truth for all unique objects across all packages

```sql
CREATE TABLE object_lookup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_uuid (uuid),
    INDEX idx_name (name),
    INDEX idx_type (object_type)
);
```

**Key Design Decision**: ❌ NO `package_id` column - package-agnostic!

#### package_object_mappings

**Purpose**: Track which objects belong to which packages

```sql
CREATE TABLE package_object_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    
    UNIQUE (package_id, object_id),
    INDEX idx_pom_package (package_id),
    INDEX idx_pom_object (object_id)
);
```

#### delta_comparison_results

**Purpose**: Store A→C comparison results (vendor delta)

```sql
CREATE TABLE delta_comparison_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    change_category VARCHAR(20) NOT NULL,  -- NEW, MODIFIED, DEPRECATED
    change_type VARCHAR(20) NOT NULL,      -- ADDED, MODIFIED, REMOVED
    version_changed BOOLEAN DEFAULT 0,
    content_changed BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    
    UNIQUE (session_id, object_id),
    INDEX idx_delta_session (session_id),
    INDEX idx_delta_category (session_id, change_category),
    
    CHECK (change_category IN ('NEW', 'MODIFIED', 'DEPRECATED')),
    CHECK (change_type IN ('ADDED', 'MODIFIED', 'REMOVED'))
);
```

#### changes (Working Set)

**Purpose**: Store classified changes for user review

```sql
CREATE TABLE changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,  -- References object_lookup
    
    classification VARCHAR(50) NOT NULL,  -- NO_CONFLICT, CONFLICT, NEW, DELETED
    vendor_change_type VARCHAR(20),
    customer_change_type VARCHAR(20),
    display_order INTEGER NOT NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    
    INDEX idx_change_session_classification (session_id, classification),
    INDEX idx_change_session_order (session_id, display_order),
    
    CHECK (classification IN ('NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED'))
);
```

**Key Design Decision**: ❌ NO object_uuid, object_name, object_type columns (redundant - use join to object_lookup)

#### object_versions

**Purpose**: Store package-specific versions of objects

```sql
CREATE TABLE object_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    version_uuid VARCHAR(255),
    sail_code TEXT,
    fields TEXT,        -- JSON string
    properties TEXT,    -- JSON string
    raw_xml TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    
    UNIQUE (object_id, package_id),
    INDEX idx_objver_object (object_id),
    INDEX idx_objver_package (package_id)
);
```

### Object-Specific Tables

**Reference**: See `.kiro/specs/three-way-merge-database-schema.md` sections 6-10 for complete schemas.

Each object type has its own table with child tables for complex data:

1. **interfaces** + interface_parameters + interface_security
2. **expression_rules** + expression_rule_inputs
3. **process_models** + process_model_nodes + process_model_flows + process_model_variables
4. **record_types** + record_type_fields + record_type_relationships + record_type_views + record_type_actions
5. **cdts** + cdt_fields
6. **integrations**
7. **web_apis**
8. **sites**
9. **groups**
10. **constants**
11. **connected_systems**
12. **unknown_objects**

All reference object_lookup via object_id (FK).

### Comparison Result Tables

**Reference**: See `.kiro/specs/three-way-merge-database-schema.md` section 11-12.

Object-specific comparison tables store detailed differences:

1. **interface_comparisons**: sail_code_diff, parameters_added/removed/modified, security_changes
2. **process_model_comparisons**: nodes_added/removed/modified, flows_added/removed/modified, variables_changed, mermaid_diagram
3. **record_type_comparisons**: fields_changed, relationships_changed, views_changed, actions_changed

All link to changes table via change_id (FK).

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: No duplicate objects in object_lookup

*For any* merge session, after extracting all packages, each UUID should appear exactly once in the object_lookup table.

**Validates: Requirements 2.2, 2.3**

### Property 2: Package-object mappings are consistent

*For any* object in object_lookup, the number of package_object_mappings entries should equal the number of packages containing that object.

**Validates: Requirements 2.3, 2.4**

### Property 3: Delta-driven working set

*For any* merge session, the count of delta_comparison_results should equal the count of changes.

**Validates: Requirements 6.1, 6.5**

### Property 4: All delta objects are classified

*For any* object in delta_comparison_results, there should exist exactly one corresponding entry in the changes table with a valid classification.

**Validates: Requirements 5.1-5.7, 6.2**

### Property 5: NEW objects are correctly identified

*For any* object that exists in Package C but not in Package A, the delta_comparison_results should have change_category='NEW' and the changes table should have classification='NEW'.

**Validates: Requirements 3.1, 5.1**

### Property 6: DEPRECATED objects are correctly identified

*For any* object that exists in Package A but not in Package C, the delta_comparison_results should have change_category='DEPRECATED'.

**Validates: Requirements 3.3**

### Property 7: MODIFIED objects are correctly identified

*For any* object that exists in both Package A and Package C with different versions or content, the delta_comparison_results should have change_category='MODIFIED'.

**Validates: Requirements 3.2, 3.4**

### Property 8: Classification Rule 10a (NO_CONFLICT for unmodified customer objects)

*For any* object that is MODIFIED in delta AND not modified in customer package, the classification should be NO_CONFLICT.

**Validates: Requirements 5.2**

### Property 9: Classification Rule 10b (CONFLICT for modified customer objects)

*For any* object that is MODIFIED in delta AND modified in customer package, the classification should be CONFLICT.

**Validates: Requirements 5.3**

### Property 10: Classification Rule 10c (DELETED for removed customer objects)

*For any* object that is MODIFIED in delta AND removed from customer package, the classification should be DELETED.

**Validates: Requirements 5.4**

### Property 11: Classification Rule 10e (NO_CONFLICT for deprecated unmodified)

*For any* object that is DEPRECATED in delta AND not modified in customer package, the classification should be NO_CONFLICT.

**Validates: Requirements 5.5**

### Property 12: Classification Rule 10f (CONFLICT for deprecated modified)

*For any* object that is DEPRECATED in delta AND modified in customer package, the classification should be CONFLICT.

**Validates: Requirements 5.6**

### Property 13: Classification Rule 10g (NO_CONFLICT for deprecated removed)

*For any* object that is DEPRECATED in delta AND removed from customer package, the classification should be NO_CONFLICT.

**Validates: Requirements 5.7**

### Property 14: Referential integrity for changes

*For any* change record, the object_id should reference a valid entry in object_lookup.

**Validates: Requirements 6.2, 13.5**

### Property 15: Complete object data extraction

*For any* Interface object, the parsed data should include uuid, name, version_uuid, sail_code, parameters, and security settings.

**Validates: Requirements 7.1**

### Property 16: Complete Process Model extraction

*For any* Process Model object, the parsed data should include uuid, name, version_uuid, nodes, flows, and variables.

**Validates: Requirements 7.2**

### Property 17: Session status transitions

*For any* merge session, the status should transition from PROCESSING → READY (or ERROR) and never backwards.

**Validates: Requirements 9.2**

### Property 18: find_or_create idempotence

*For any* UUID, calling find_or_create multiple times should return the same object_lookup entry without creating duplicates.

**Validates: Requirements 2.5, 3.2, 11.2**

### Property 19: Object-specific comparison data completeness

*For any* Interface change, the comparison data should include sail_code_diff, parameters_added, parameters_removed, parameters_modified, and security_changes.

**Validates: Requirements 1e.1**

### Property 20: Process Model Mermaid diagram generation

*For any* Process Model change, the comparison data should include a valid Mermaid diagram syntax that can be rendered.

**Validates: Requirements 1e.3**

### Property 21: Navigation state preservation

*For any* change review session, navigating through changes and returning to summary should preserve the review status (reviewed count, skipped count).

**Validates: Requirements 1d.5**

## Error Handling

### Exception Hierarchy

```python
class ThreeWayMergeException(Exception):
    """Base exception for three-way merge"""
    pass

class PackageExtractionException(ThreeWayMergeException):
    """Raised when package extraction fails"""
    pass

class ParsingException(ThreeWayMergeException):
    """Raised when XML parsing fails"""
    pass

class ComparisonException(ThreeWayMergeException):
    """Raised when comparison fails"""
    pass

class ClassificationException(ThreeWayMergeException):
    """Raised when classification fails"""
    pass

class DuplicateObjectException(ThreeWayMergeException):
    """Raised when duplicate object detected"""
    pass
```

### Error Handling Strategy

1. **Service Level**: Catch exceptions, log errors, update session status to ERROR
2. **Repository Level**: Let database exceptions propagate
3. **Parser Level**: Catch XML parsing errors, log warnings, continue with next file
4. **Orchestrator Level**: Catch all exceptions, rollback transaction, update session

## Testing Strategy

### Unit Testing

Unit tests will verify specific functionality of individual components:

- Repository tests: Test find_or_create, bulk operations, queries
- Service tests: Test business logic with mocked dependencies
- Parser tests: Test XML parsing with real XML files from applicationArtifacts/ObjectSpecificXml/
- Classification tests: Test all 7 classification rules

### Property-Based Testing

Property-based tests will verify correctness properties using real test packages from `applicationArtifacts/Three Way Testing Files/V2/`:

**Test Framework**: pytest with real Appian packages (no hypothesis)

**Property Tests**:

1. **Property 1 Test**: After extracting all packages, verify no duplicates in object_lookup
2. **Property 3 Test**: Verify delta_count == change_count for each session
3. **Property 4 Test**: Verify all delta objects have corresponding changes
4. **Property 5-7 Tests**: Verify NEW, DEPRECATED, MODIFIED detection
5. **Property 8-13 Tests**: Verify all 7 classification rules
6. **Property 14 Test**: Verify referential integrity
7. **Property 18 Test**: Verify find_or_create idempotence

**Test Configuration**:
- Use real packages: Test Application - Base Version.zip, Test Application Customer Version.zip, Test Application Vendor New Version.zip
- Run complete end-to-end workflow
- Verify all properties after each phase
- Clean database between tests

### Integration Testing

Integration tests will verify the complete workflow:

1. **End-to-End Test**: Upload 3 packages, verify complete workflow
2. **Database Integrity Test**: Verify all foreign keys, constraints
3. **Performance Test**: Verify queries complete in < 200ms

### Test Execution

All tests will use the mandatory pattern:
```bash
python -m pytest <test_path> > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

### Test Packages

**Location**: `applicationArtifacts/Three Way Testing Files/V2/`

1. **Test Application - Base Version.zip** (Package A)
2. **Test Application Customer Version.zip** (Package B)
3. **Test Application Vendor New Version.zip** (Package C)

**Contents**: ~27 objects each
- 2 Groups
- 3 CDTs
- 1 Data Store
- 14 Content objects (Constants, Expression Rules, Interfaces)
- 1 Process Model Folder
- 2 Process Models
- 1 Record Type

**Known Test UUIDs**:
```python
PROCESS_MODEL_UUID_1 = "de199b3f-b072-4438-9508-3b6594827eaf"
PROCESS_MODEL_UUID_2 = "2c8de7e9-23b9-40d6-afc2-233a963832be"
RECORD_TYPE_UUID = "57318b79-0bfd-45c4-a07e-ceae8277e0fb"
```

## Validation Queries

**Reference**: See `.kiro/specs/three-way-merge-database-schema.md` for complete validation queries.

### Check for Duplicates (should return 0)
```sql
SELECT uuid, COUNT(*) as count 
FROM object_lookup 
GROUP BY uuid 
HAVING count > 1;
```

### Verify Delta-Driven Working Set (should be equal)
```sql
SELECT COUNT(*) FROM delta_comparison_results WHERE session_id = ?;
SELECT COUNT(*) FROM changes WHERE session_id = ?;
```

### Verify Package Mappings
```sql
SELECT ol.uuid, ol.name, ol.object_type
FROM object_lookup ol
JOIN package_object_mappings pom ON ol.id = pom.object_id
WHERE pom.package_id = ?;
```

### Get Object Across All Packages
```sql
SELECT p.package_type, ov.version_uuid, ov.sail_code
FROM object_versions ov
JOIN packages p ON ov.package_id = p.id
WHERE ov.object_id = ?;
```

## Performance Considerations

**Reference**: See `.kiro/specs/three-way-merge-implementation-plan.md` Phase 8 for optimization details.

1. **Indexes**: All foreign keys and frequently queried columns are indexed
2. **Bulk Operations**: Use bulk_save_objects for inserting multiple records
3. **Eager Loading**: Use joinedload for related objects
4. **Caching**: Cache frequently accessed objects (e.g., object_lookup by UUID)
5. **Query Optimization**: All queries should complete in < 200ms

## Migration Strategy

**Reference**: See `.kiro/specs/three-way-merge-database-schema.md` for migration details.

1. **Phase 1**: Add object_id column to all object tables (nullable)
2. **Phase 2**: Populate object_id from object_lookup
3. **Phase 3**: Make object_id NOT NULL
4. **Phase 4**: Remove deprecated columns (package_id, uuid, name from object tables)

## UI/Template Design

**Reference**: See `.kiro/specs/three-way-merge-ui-templates.md` (Parts 1-3) for complete UI specification.

### Key UI Pages

1. **Upload Page** (`merge/upload.html`): Upload 3 packages with drag-and-drop
2. **Sessions Page** (`merge/sessions.html`): List all merge sessions with filters
3. **Summary Page** (`merge/summary.html`): Show statistics, breakdown by type, "Start Merge Workflow" button
4. **Change Detail Page** (`merge/change_detail.html`): Show object-specific comparisons with navigation

### Object-Specific Comparison Templates

**Reference**: See `.kiro/specs/three-way-merge-ui-templates-part2.md` for detailed specifications.

Each object type has a dedicated comparison template that extends `_base_comparison.html`:

#### 1. Interface Comparison (`interface_comparison.html`)
- **SAIL Code**: Side-by-side diff with syntax highlighting
- **Parameters**: Added/Removed/Modified sections with type, required, default value
- **Security**: Added/Removed roles with permissions

#### 2. Expression Rule Comparison (`expression_rule_comparison.html`)
- **SAIL Code**: Side-by-side diff
- **Inputs**: Added/Removed/Modified with type, required, default value
- **Output Type**: Before/After comparison

#### 3. Process Model Comparison (`process_model_comparison.html`)
- **Summary Statistics**: Nodes count (+/-), Flows count (+/-), Variables count (+/-)
- **Mermaid Diagram**: Tabs for Base/Customer/Vendor/Diff with visual flow diagram
- **Nodes**: Added/Removed/Modified with node type and properties
- **Flows**: Added/Removed/Modified with from/to nodes and conditions
- **Variables**: Added/Removed/Modified with type and parameter flag

#### 4. Record Type Comparison (`record_type_comparison.html`)
- **Fields**: Added/Removed/Modified with type, required, primary key
- **Relationships**: Added/Removed with relationship type and target
- **Views**: Modified views with configuration changes
- **Actions**: Added/Removed actions

#### 5. CDT Comparison (`cdt_comparison.html`)
- **Namespace**: Before/After comparison
- **Fields**: Added/Removed/Modified with type, list indicator, required flag

#### 6. Integration Comparison (`integration_comparison.html`)
- **SAIL Code**: Side-by-side diff
- **Connection**: Changes to connection settings
- **Authentication**: Changes to auth configuration
- **Endpoint**: Changes to endpoint URL

#### 7. Web API Comparison (`web_api_comparison.html`)
- **SAIL Code**: Side-by-side diff
- **Endpoint**: Changes to API endpoint
- **HTTP Methods**: GET, POST, PUT, DELETE changes

#### 8. Site Comparison (`site_comparison.html`)
- **Page Hierarchy**: Tree view with added/removed/modified pages

#### 9. Group Comparison (`group_comparison.html`)
- **Members**: Added/Removed members
- **Parent Group**: Changes to parent group

#### 10. Constant Comparison (`constant_comparison.html`)
- **Value**: Before/After comparison
- **Type**: Type changes
- **Scope**: Scope changes (Application/System)

#### 11. Connected System Comparison (`connected_system_comparison.html`)
- **System Type**: Type changes
- **Properties**: Added/Removed/Modified properties

### UI Components

**Reference**: See `.kiro/specs/three-way-merge-ui-templates-part2.md` section 5 for component specifications.

#### Classification Badges
- NO_CONFLICT: Green with check icon
- CONFLICT: Red with warning icon
- NEW: Blue with plus icon
- DELETED: Gray with trash icon

#### Object Type Icons
- Interface: window-maximize
- Expression Rule: function
- Process Model: project-diagram
- Record Type: database
- CDT: cube
- Integration: plug
- Web API: globe
- Site: sitemap
- Group: users
- Constant: hashtag
- Connected System: server

#### Progress Bar
- Shows current change / total changes
- Percentage indicator
- Visual progress bar

#### SAIL Code Diff
- Side-by-side comparison
- Before (left) / After (right)
- Syntax highlighting
- Line-by-line diff with +/- indicators

## Critical Reminders

1. **NO package_id in object_lookup** - It's global!
2. **NO duplicate objects** - Use `find_or_create()`
3. **NO customer-only in working set** - Only delta objects
4. **NO old classifications** - Only 4 types: NO_CONFLICT, CONFLICT, NEW, DELETED
5. **ALL tests use real packages** - From `applicationArtifacts/Three Way Testing Files/V2/`
6. **ALL 7 rules implemented** - No shortcuts
