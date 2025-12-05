# Three-Way Merge Service Layer Design

**Part of:** Three-Way Merge Clean Architecture Specification  
**Version:** 1.0  
**Date:** 2025-11-30

---

## Service Layer Architecture

### Design Principles

1. **Single Responsibility**: Each service has one clear purpose
2. **Dependency Injection**: Services receive dependencies via constructor
3. **Interface-Based**: Services implement interfaces for testability
4. **Stateless**: Services don't maintain state between calls
5. **Transaction Management**: Services handle database transactions
6. **Error Handling**: Consistent error handling with custom exceptions

---

## Service Hierarchy

```
ThreeWayMergeOrchestrator (Main Coordinator)
├── PackageExtractionService
│   ├── ZipExtractorService
│   ├── XMLParserFactory
│   │   ├── InterfaceParser
│   │   ├── ExpressionRuleParser
│   │   ├── ProcessModelParser
│   │   ├── RecordTypeParser
│   │   ├── CDTParser
│   │   ├── ... (other parsers)
│   │   └── UnknownObjectParser
│   └── SAILCodeCleanerService
│
├── DeltaComparisonService
│   ├── VersionComparisonStrategy
│   └── ContentComparisonStrategy
│
├── CustomerComparisonService
│   ├── VersionComparisonStrategy
│   └── ContentComparisonStrategy
│
├── ClassificationService
│   └── ClassificationRuleEngine
│
├── MergeGuidanceService
│   ├── ConflictAnalyzer
│   └── RecommendationEngine
│
├── DependencyAnalysisService
│   └── DependencyGraphBuilder
│
└── ReportGeneratorService
    ├── ExcelReportBuilder
    └── SummaryStatisticsCalculator
```

---

## Core Services

### 1. ThreeWayMergeOrchestrator

**Purpose**: Main entry point that coordinates the entire merge workflow

**Responsibilities:**
- Create merge session
- Coordinate all sub-services
- Manage transactions
- Handle errors and rollback
- Update session status
- Log progress

**Interface:**
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
        Create and process a new merge session
        
        Steps:
        1. Create session record
        2. Extract all three packages
        3. Perform delta comparison (A→C)
        4. Perform customer comparison (delta vs B)
        5. Classify changes
        6. Generate merge guidance
        7. Analyze dependencies
        8. Update session status to 'ready'
        
        Returns:
            MergeSession object with reference_id
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

**Workflow:**
```python
def create_merge_session(self, base_zip, customized_zip, new_vendor_zip):
    try:
        # 1. Create session
        session = self._create_session_record(base_zip, customized_zip, new_vendor_zip)
        logger.info(f"Created session {session.reference_id}")
        
        # 2. Extract packages (transactional)
        with db.session.begin_nested():
            pkg_a = self.package_extraction_service.extract_package(
                session.id, base_zip, 'base'
            )
            pkg_b = self.package_extraction_service.extract_package(
                session.id, customized_zip, 'customized'
            )
            pkg_c = self.package_extraction_service.extract_package(
                session.id, new_vendor_zip, 'new_vendor'
            )
        
        # 3. Delta comparison (A→C)
        delta_results = self.delta_comparison_service.compare(
            session.id, pkg_a.id, pkg_c.id
        )
        logger.info(f"Delta: {len(delta_results)} changes")
        
        # 4. Customer comparison (delta vs B)
        customer_results = self.customer_comparison_service.compare(
            session.id, pkg_a.id, pkg_b.id, delta_results
        )
        
        # 5. Classify changes
        changes = self.classification_service.classify(
            session.id, delta_results, customer_results
        )
        logger.info(f"Classified: {len(changes)} changes")
        
        # 6. Generate merge guidance
        self.merge_guidance_service.generate_guidance(session.id, changes)
        
        # 7. Analyze dependencies
        self.dependency_analysis_service.analyze(session.id, changes)
        
        # 8. Update session
        session.status = 'ready'
        session.total_changes = len(changes)
        db.session.commit()
        
        return session
        
    except Exception as e:
        db.session.rollback()
        session.status = 'error'
        session.error_log = str(e)
        db.session.commit()
        raise
```

---

### 2. PackageExtractionService

**Purpose**: Extract and parse Appian packages, store objects without duplication

**Responsibilities:**
- Extract ZIP files
- Parse XML objects
- Store in object_lookup (find_or_create)
- Create package_object_mappings
- Store object-specific data
- Clean SAIL code

**Interface:**
```python
class PackageExtractionService:
    def __init__(
        self,
        zip_extractor: ZipExtractorService,
        parser_factory: XMLParserFactory,
        sail_cleaner: SAILCodeCleanerService,
        object_lookup_repo: ObjectLookupRepository,
        package_object_mapping_repo: PackageObjectMappingRepository,
        object_repositories: Dict[str, BaseObjectRepository],
        logger: Logger
    ):
        pass
    
    def extract_package(
        self,
        session_id: int,
        zip_path: str,
        package_type: str  # 'base', 'customized', 'new_vendor'
    ) -> Package:
        """
        Extract package and store all objects
        
        Steps:
        1. Create package record
        2. Extract ZIP to temp directory
        3. Find all XML files
        4. Parse each XML file
        5. For each object:
           a. Find or create in object_lookup
           b. Create package_object_mapping
           c. Store object-specific data
        6. Update package statistics
        7. Clean up temp directory
        
        Returns:
            Package object
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

**Workflow:**
```python
def extract_package(self, session_id, zip_path, package_type):
    # 1. Create package record
    package = Package(
        session_id=session_id,
        package_type=package_type,
        package_name=os.path.basename(zip_path),
        extraction_status='processing'
    )
    db.session.add(package)
    db.session.flush()
    
    # 2. Extract ZIP
    temp_dir = self.zip_extractor.extract(zip_path)
    
    try:
        # 3. Find all XML files
        xml_files = self._find_xml_files(temp_dir)
        logger.info(f"Found {len(xml_files)} XML files")
        
        # 4. Parse each file
        for xml_path in xml_files:
            object_type = self._detect_object_type(xml_path)
            parser = self.parser_factory.get_parser(object_type)
            
            # Parse XML
            parsed_data = parser.parse(xml_path)
            
            # 5a. Find or create in object_lookup
            obj_lookup = self.object_lookup_repo.find_or_create(
                uuid=parsed_data['uuid'],
                name=parsed_data['name'],
                object_type=object_type,
                description=parsed_data.get('description')
            )
            
            # 5b. Create package_object_mapping
            self.package_object_mapping_repo.create(
                package_id=package.id,
                object_id=obj_lookup.id
            )
            
            # 5c. Store object-specific data
            repo = self.object_repositories[object_type]
            repo.create_or_update(
                object_id=obj_lookup.id,
                package_id=package.id,
                data=parsed_data
            )
        
        # 6. Update package statistics
        package.total_objects = len(xml_files)
        package.extraction_status = 'completed'
        db.session.commit()
        
        return package
        
    finally:
        # 7. Clean up
        self.zip_extractor.cleanup(temp_dir)
```

---

### 3. DeltaComparisonService

**Purpose**: Compare base package (A) with new vendor package (C) to identify vendor delta

**Responsibilities:**
- Compare A→C using version + content comparison
- Identify NEW, MODIFIED, DEPRECATED objects
- Store results in delta_comparison_results
- Return delta set for classification

**Interface:**
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
        Compare A→C to identify vendor delta
        
        Steps:
        1. Get objects in package A
        2. Get objects in package C
        3. Identify NEW objects (in C, not in A)
        4. Identify DEPRECATED objects (in A, not in C)
        5. Identify MODIFIED objects (in both A and C)
           a. Compare version UUIDs
           b. If version changed, mark as MODIFIED
           c. If version same, compare content
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
        Compare versions of an object
        
        Returns:
            (version_changed, content_changed)
        """
        pass
```

**Comparison Logic:**
```python
def compare(self, session_id, base_pkg_id, new_vendor_pkg_id):
    # 1. Get objects in A
    objects_a = self.package_object_mapping_repo.get_objects_in_package(base_pkg_id)
    objects_a_uuids = {obj.uuid for obj in objects_a}
    
    # 2. Get objects in C
    objects_c = self.package_object_mapping_repo.get_objects_in_package(new_vendor_pkg_id)
    objects_c_uuids = {obj.uuid for obj in objects_c}
    
    results = []
    
    # 3. NEW objects (in C, not in A)
    new_uuids = objects_c_uuids - objects_a_uuids
    for uuid in new_uuids:
        obj = self.object_lookup_repo.find_by_uuid(uuid)
        result = DeltaComparisonResult(
            session_id=session_id,
            object_id=obj.id,
            change_category='NEW',
            change_type='ADDED',
            version_changed=False,
            content_changed=False
        )
        results.append(result)
    
    # 4. DEPRECATED objects (in A, not in C)
    deprecated_uuids = objects_a_uuids - objects_c_uuids
    for uuid in deprecated_uuids:
        obj = self.object_lookup_repo.find_by_uuid(uuid)
        result = DeltaComparisonResult(
            session_id=session_id,
            object_id=obj.id,
            change_category='DEPRECATED',
            change_type='REMOVED',
            version_changed=False,
            content_changed=False
        )
        results.append(result)
    
    # 5. MODIFIED objects (in both A and C)
    common_uuids = objects_a_uuids & objects_c_uuids
    for uuid in common_uuids:
        obj = self.object_lookup_repo.find_by_uuid(uuid)
        version_changed, content_changed = self._compare_versions(
            obj, base_pkg_id, new_vendor_pkg_id
        )
        
        if version_changed or content_changed:
            result = DeltaComparisonResult(
                session_id=session_id,
                object_id=obj.id,
                change_category='MODIFIED',
                change_type='MODIFIED',
                version_changed=version_changed,
                content_changed=content_changed
            )
            results.append(result)
    
    # 6. Store results
    self.delta_comparison_repo.bulk_create(results)
    
    return results
```

---

### 4. CustomerComparisonService

**Purpose**: Compare delta objects against customer package (B) to identify customer modifications

**Responsibilities:**
- Compare delta objects against package B
- Identify customer modifications
- Return comparison data for classification

**Interface:**
```python
class CustomerComparisonService:
    def __init__(
        self,
        object_lookup_repo: ObjectLookupRepository,
        package_object_mapping_repo: PackageObjectMappingRepository,
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
        customized_package_id: int,
        delta_results: List[DeltaComparisonResult]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Compare delta objects against customer package
        
        For each object in delta:
        1. Check if object exists in B
        2. If exists, compare A→B
           a. Compare version UUIDs
           b. Compare content
        3. Return comparison data
        
        Returns:
            Dict mapping object_id to comparison data:
            {
                object_id: {
                    'exists_in_customer': bool,
                    'customer_modified': bool,
                    'version_changed': bool,
                    'content_changed': bool
                }
            }
        """
        pass
```

---

### 5. ClassificationService

**Purpose**: Apply 7 classification rules to determine change classification

**Responsibilities:**
- Apply classification rules
- Create Change records
- Link to object_lookup
- Set display_order

**Interface:**
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
        Classify changes using 7 rules
        
        For each delta object:
        1. Get delta change category (NEW, MODIFIED, DEPRECATED)
        2. Get customer comparison data
        3. Apply classification rule
        4. Create Change record
        5. Set display_order
        
        Returns:
            List of Change objects
        """
        pass
```

**Classification Rules:**
```python
class ClassificationRuleEngine:
    def classify(
        self,
        delta_category: str,
        customer_data: Dict[str, Any]
    ) -> str:
        """
        Apply classification rules
        
        Rules:
        10a: MODIFIED in delta AND not modified in customer → NO_CONFLICT
        10b: MODIFIED in delta AND modified in customer → CONFLICT
        10c: MODIFIED in delta AND removed in customer → DELETED
        10d: NEW in delta → NEW
        10e: DEPRECATED in delta AND not modified in customer → NO_CONFLICT
        10f: DEPRECATED in delta AND modified in customer → CONFLICT
        10g: DEPRECATED in delta AND removed in customer → NO_CONFLICT
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

---

### 6. MergeGuidanceService

**Purpose**: Generate merge recommendations and identify conflicts

**Responsibilities:**
- Analyze each change
- Generate recommendations
- Identify specific conflicts
- Create MergeGuidance records

**Interface:**
```python
class MergeGuidanceService:
    def __init__(
        self,
        merge_guidance_repository: MergeGuidanceRepository,
        conflict_analyzer: ConflictAnalyzer,
        recommendation_engine: RecommendationEngine,
        logger: Logger
    ):
        pass
    
    def generate_guidance(
        self,
        session_id: int,
        changes: List[Change]
    ) -> List[MergeGuidance]:
        """
        Generate merge guidance for each change
        
        For each change:
        1. Analyze conflicts (if CONFLICT classification)
        2. Generate recommendation
        3. Create MergeGuidance record
        4. Create MergeConflict records
        5. Create MergeChange records
        
        Returns:
            List of MergeGuidance objects
        """
        pass
```

---

## Parser Design

### XMLParserFactory

**Purpose**: Create appropriate parser for each object type

```python
class XMLParserFactory:
    def __init__(self):
        self.parsers = {
            'Interface': InterfaceParser(),
            'Expression Rule': ExpressionRuleParser(),
            'Process Model': ProcessModelParser(),
            'Record Type': RecordTypeParser(),
            'CDT': CDTParser(),
            'Integration': IntegrationParser(),
            'Web API': WebAPIParser(),
            'Site': SiteParser(),
            'Group': GroupParser(),
            'Constant': ConstantParser(),
            'Connected System': ConnectedSystemParser(),
        }
    
    def get_parser(self, object_type: str) -> BaseParser:
        return self.parsers.get(object_type, UnknownObjectParser())
```

### BaseParser

```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse XML file and extract object data
        
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
        pass
```

### InterfaceParser Example

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
        data['parameters'] = self._extract_parameters(root)
        
        # Extract security
        data['security'] = self._extract_security(root)
        
        return data
    
    def _extract_parameters(self, root: ET.Element) -> List[Dict]:
        parameters = []
        for param in root.findall('.//parameter'):
            parameters.append({
                'name': param.get('name'),
                'type': param.get('type'),
                'required': param.get('required') == 'true',
                'default_value': param.get('defaultValue')
            })
        return parameters
```

---

*Continued in implementation plan...*
