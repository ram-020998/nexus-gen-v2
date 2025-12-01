# Design Document

## Overview

This design addresses critical defects in the NexusGen Three-Way Merge Assistant that prevent complete object extraction, comparison result persistence, and detailed UI display. The fixes ensure all Appian object types are fully extracted with their structural details, comparison results are persisted to enable efficient retrieval, and the merge workflow UI displays comprehensive object information.

The design follows the existing clean architecture pattern with parsers, services, repositories, and controllers. We will fix existing parsers, implement missing parsers, enhance comparison services to persist results, modify the database schema to support dual object tracking, and wire the UI to display detailed comparison data.

## Architecture

### System Context

The Three-Way Merge Assistant follows an 8-step workflow:
1. Create session record
2. Extract Package A (Base Version)
3. Extract Package B (Customer Version)
4. Extract Package C (New Vendor Version)
5. Perform delta comparison (A→C)
6. Perform customer comparison (delta vs B)
7. Classify changes (apply 7 rules)
8. Generate merge guidance

The defects occur in steps 2-4 (extraction), steps 5-6 (comparison), and step 8 (display).

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  merge_assistant_controller.py               │
│  - Handles HTTP requests                                     │
│  - Renders UI with comparison data                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            three_way_merge_orchestrator.py                   │
│  - Coordinates 8-step workflow                               │
│  - Calls extraction, comparison, classification services     │
└─────────────────────────────────────────────────────────────┐
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              package_extraction_service.py                   │
│  - Extracts packages using xml_parser_factory                │
│  - Calls object-specific parsers                             │
│  - FIX: Invoke expression_rule_parser, record_type_parser   │
│  - FIX: Invoke cdt_parser, data_store_parser                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Object Parsers                            │
│  - expression_rule_parser.py (NEW/FIX)                       │
│  - record_type_parser.py (NEW/FIX)                           │
│  - cdt_parser.py (NEW/FIX)                                   │
│  - process_model_parser.py (FIX - add nodes/flows/vars)     │
│  - interface_parser.py (existing)                            │
│  - constant_parser.py (existing)                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Repositories                              │
│  - object_lookup_repository.py (find_or_create)             │
│  - expression_rule_repository.py (NEW)                       │
│  - record_type_repository.py (NEW)                           │
│  - cdt_repository.py (existing - enhance)                    │
│  - process_model_repository.py (existing - enhance)          │
│  - comparison repositories (FIX - add persistence)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              delta_comparison_service.py                     │
│  - Compares A→C                                              │
│  - FIX: Persist comparison results to comparison tables      │
│  - FIX: Generate detailed diffs (SAIL, fields, nodes)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│           customer_comparison_service.py                     │
│  - Compares delta vs B                                       │
│  - FIX: Persist comparison results                           │
│  - FIX: Track both vendor and customer object IDs            │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Component Status Summary

**Already Exists (Need to Fix/Enhance):**
- Parsers: expression_rule_parser.py, record_type_parser.py, cdt_parser.py, process_model_parser.py
- Repositories: expression_rule_repository.py, record_type_repository.py, cdt_repository.py, process_model_repository.py
- Comparison Repositories: interface_comparison_repository.py, process_model_comparison_repository.py, record_type_comparison_repository.py
- Database Models: ExpressionRule, ExpressionRuleInput, RecordType, RecordTypeField, RecordTypeRelationship, RecordTypeView, RecordTypeAction, CDT, CDTField, ProcessModel, ProcessModelNode, ProcessModelFlow, ProcessModelVariable
- Comparison Models: InterfaceComparison, ProcessModelComparison, RecordTypeComparison

**Need to Create:**
- Parsers: data_store_parser.py (if not exists)
- Repositories: data_store_repository.py (if not exists)
- Comparison Repositories: expression_rule_comparison_repository.py, cdt_comparison_repository.py, constant_comparison_repository.py
- Database Models: DataStore, DataStoreEntity, ExpressionRuleComparison, CDTComparison, ConstantComparison
- Changes table: Add vendor_object_id and customer_object_id columns

**Key Issue:** Most parsers and repositories exist but are either:
1. Not being invoked by PackageExtractionService
2. Not fully implemented (missing child entity extraction)
3. Not persisting data correctly

### 1. Parser Components

#### BaseParser (existing - no changes needed)
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, xml_path: str, package_id: int) -> None:
        pass
```

#### ExpressionRuleParser (EXISTS - FIX)
```python
class ExpressionRuleParser(BaseParser):
    # File: services/parsers/expression_rule_parser.py
    # Status: EXISTS but may be incomplete or not invoked
    
    def __init__(self, 
                 object_lookup_repo: ObjectLookupRepository,
                 expression_rule_repo: ExpressionRuleRepository):
        self.object_lookup_repo = object_lookup_repo
        self.expression_rule_repo = expression_rule_repo
    
    def parse(self, xml_path: str, package_id: int) -> None:
        # FIX: Ensure complete parsing of expressionRule.xml
        # Extract: name, uuid, version_uuid, description, return_type, definition
        # Extract inputs: name, type, description, required
        # FIX: Call object_lookup_repo.find_or_create()
        # FIX: Store in expression_rules and expression_rule_inputs tables
        # FIX: Store version in object_versions
```

#### RecordTypeParser (EXISTS - FIX)
```python
class RecordTypeParser(BaseParser):
    # File: services/parsers/record_type_parser.py
    # Status: EXISTS but may be incomplete or not invoked
    
    def __init__(self,
                 object_lookup_repo: ObjectLookupRepository,
                 record_type_repo: RecordTypeRepository):
        self.object_lookup_repo = object_lookup_repo
        self.record_type_repo = record_type_repo
    
    def parse(self, xml_path: str, package_id: int) -> None:
        # FIX: Ensure complete parsing of recordType.xml
        # Extract: name, uuid, version_uuid, description, data_source
        # Extract fields: name, type, required, config, display_order
        # Extract relationships: type, target_uuid, cardinality, cascade
        # Extract views: name, type, columns, filters
        # Extract actions: name, type, process_model_ref, visibility
        # FIX: Call object_lookup_repo.find_or_create()
        # FIX: Store in record_types, record_type_fields, record_type_relationships,
        #   record_type_views, record_type_actions tables
        # FIX: Store version in object_versions
```

#### CDTParser (EXISTS - FIX)
```python
class CDTParser(BaseParser):
    # File: services/parsers/cdt_parser.py
    # Status: EXISTS but may be incomplete or not invoked
    
    def __init__(self,
                 object_lookup_repo: ObjectLookupRepository,
                 cdt_repo: CDTRepository):
        self.object_lookup_repo = object_lookup_repo
        self.cdt_repo = cdt_repo
    
    def parse(self, xsd_path: str, package_id: int) -> None:
        # FIX: Ensure complete parsing of dataType.xsd
        # Extract: namespace, name, uuid (from annotations)
        # Extract fields: name, type, multiple, namespace, order
        # FIX: Call object_lookup_repo.find_or_create()
        # FIX: Store in cdts and cdt_fields tables
        # FIX: Store version in object_versions
```

#### ProcessModelParser (EXISTS - FIX)
```python
class ProcessModelParser(BaseParser):
    # File: services/parsers/process_model_parser.py
    # Status: EXISTS but incomplete - missing nodes/flows/variables extraction
    
    def __init__(self,
                 object_lookup_repo: ObjectLookupRepository,
                 process_model_repo: ProcessModelRepository):
        self.object_lookup_repo = object_lookup_repo
        self.process_model_repo = process_model_repo
    
    def parse(self, xml_path: str, package_id: int) -> None:
        # Existing: Parse processModel.xml
        # Existing: Extract: name, uuid, version_uuid, description
        # FIX: Extract nodes: uuid, name, type, label, position, config
        # FIX: Extract flows: uuid, source_uuid, target_uuid, condition, label
        # FIX: Extract variables: name, type, multiple, default, parameter
        # Existing: Call object_lookup_repo.find_or_create()
        # FIX: Store in process_model_nodes, process_model_flows,
        #   process_model_variables tables
        # Existing: Store version in object_versions
```

### 2. Repository Components

#### ExpressionRuleRepository (EXISTS - ENHANCE)
```python
class ExpressionRuleRepository(BaseRepository):
    # File: repositories/expression_rule_repository.py
    # Status: EXISTS but may need enhancement
    
    def create_expression_rule(self, object_id: int, data: dict) -> ExpressionRule:
        # VERIFY/FIX: Insert into expression_rules table
        
    def create_expression_rule_input(self, rule_id: int, data: dict) -> ExpressionRuleInput:
        # VERIFY/FIX: Insert into expression_rule_inputs table
        
    def get_by_object_id(self, object_id: int) -> ExpressionRule:
        # VERIFY/FIX: Retrieve with inputs
```

#### RecordTypeRepository (EXISTS - ENHANCE)
```python
class RecordTypeRepository(BaseRepository):
    # File: repositories/record_type_repository.py
    # Status: EXISTS but may need enhancement
    
    def create_record_type(self, object_id: int, data: dict) -> RecordType:
        # VERIFY/FIX: Insert into record_types table
        
    def create_field(self, record_type_id: int, data: dict) -> RecordTypeField:
        # VERIFY/FIX: Insert into record_type_fields table
        
    def create_relationship(self, record_type_id: int, data: dict) -> RecordTypeRelationship:
        # VERIFY/FIX: Insert into record_type_relationships table
        
    def create_view(self, record_type_id: int, data: dict) -> RecordTypeView:
        # VERIFY/FIX: Insert into record_type_views table
        
    def create_action(self, record_type_id: int, data: dict) -> RecordTypeAction:
        # VERIFY/FIX: Insert into record_type_actions table
        
    def get_by_object_id(self, object_id: int) -> RecordType:
        # VERIFY/FIX: Retrieve with fields, relationships, views, actions
```

#### Comparison Repositories (EXISTS - FIX/ADD)
```python
class InterfaceComparisonRepository(BaseRepository):
    # File: repositories/comparison/interface_comparison_repository.py
    # Status: EXISTS but may not persist data
    
    def create_comparison(self, session_id: int, object_id: int, 
                         comparison_data: dict) -> InterfaceComparison:
        # FIX: Actually insert into interface_comparisons table
        # Store: sail_diff, parameter_changes, security_changes
        
    def get_by_session_and_object(self, session_id: int, 
                                  object_id: int) -> InterfaceComparison:
        # Retrieve comparison results

class ProcessModelComparisonRepository(BaseRepository):
    # File: repositories/comparison/process_model_comparison_repository.py
    # Status: EXISTS but may not persist data
    
    def create_comparison(self, session_id: int, object_id: int,
                         comparison_data: dict) -> ProcessModelComparison:
        # FIX: Actually insert into process_model_comparisons table
        # Store: node_diffs, flow_diffs, variable_diffs, mermaid_diagrams
        
class RecordTypeComparisonRepository(BaseRepository):
    # File: repositories/comparison/record_type_comparison_repository.py
    # Status: EXISTS but may not persist data
    
    def create_comparison(self, session_id: int, object_id: int,
                         comparison_data: dict) -> RecordTypeComparison:
        # FIX: Actually insert into record_type_comparisons table
        # Store: field_diffs, relationship_diffs, view_diffs, action_diffs

# NEW: Need to create these comparison repositories
class ExpressionRuleComparisonRepository(BaseRepository):
    # File: repositories/comparison/expression_rule_comparison_repository.py
    # Status: DOES NOT EXIST - CREATE NEW
    
class CDTComparisonRepository(BaseRepository):
    # File: repositories/comparison/cdt_comparison_repository.py
    # Status: DOES NOT EXIST - CREATE NEW
    
class ConstantComparisonRepository(BaseRepository):
    # File: repositories/comparison/constant_comparison_repository.py
    # Status: DOES NOT EXIST - CREATE NEW
```

### 3. Service Components

#### PackageExtractionService (FIX existing)
```python
class PackageExtractionService(BaseService):
    def extract_package(self, zip_path: str, package_type: PackageType,
                       session_id: int) -> Package:
        # Existing logic for unzipping and discovering objects
        
        # FIX: Add parser invocations for missing object types
        for obj_file in discovered_objects:
            if obj_file.endswith('expressionRule.xml'):
                self.expression_rule_parser.parse(obj_file, package.id)
            elif obj_file.endswith('recordType.xml'):
                self.record_type_parser.parse(obj_file, package.id)
            elif obj_file.endswith('dataType.xsd'):
                self.cdt_parser.parse(obj_file, package.id)
            elif obj_file.endswith('dataStore.xml'):
                self.data_store_parser.parse(obj_file, package.id)
            # ... existing parsers for interface, constant, etc.
```

#### DeltaComparisonService (FIX existing)
```python
class DeltaComparisonService(BaseService):
    def compare_objects(self, session_id: int, base_package_id: int,
                       new_vendor_package_id: int) -> List[DeltaChange]:
        # Existing logic to identify MODIFIED, NEW, DEPRECATED
        
        # FIX: For each delta object, generate detailed comparison
        for delta_obj in delta_objects:
            if delta_obj.object_type == 'interface':
                comparison = self._compare_interfaces(delta_obj)
                self.interface_comparison_repo.create_comparison(
                    session_id, delta_obj.id, comparison)
            elif delta_obj.object_type == 'processModel':
                comparison = self._compare_process_models(delta_obj)
                self.process_model_comparison_repo.create_comparison(
                    session_id, delta_obj.id, comparison)
            # ... similar for other object types
            
    def _compare_interfaces(self, obj: ObjectIdentity) -> dict:
        # FIX: Generate line-by-line SAIL code diff
        # Return: {sail_diff: [...], parameter_changes: [...], ...}
        
    def _compare_process_models(self, obj: ObjectIdentity) -> dict:
        # FIX: Compare nodes, flows, variables
        # Generate Mermaid diagrams for all versions
        # Return: {node_diffs: [...], flow_diffs: [...], mermaid_base: "...", ...}
```

#### CustomerComparisonService (FIX existing)
```python
class CustomerComparisonService(BaseService):
    def compare_with_customer(self, session_id: int, 
                             delta_objects: List[DeltaChange],
                             customer_package_id: int) -> List[Change]:
        # Existing logic to detect conflicts
        
        # FIX: Track both vendor and customer object IDs
        for delta_obj in delta_objects:
            vendor_object_id = delta_obj.object_id
            customer_object = self._find_customer_object(delta_obj, customer_package_id)
            customer_object_id = customer_object.id if customer_object else None
            
            change = Change(
                session_id=session_id,
                vendor_object_id=vendor_object_id,  # NEW column
                customer_object_id=customer_object_id,  # NEW column
                classification=self._classify(delta_obj, customer_object),
                # ... other fields
            )
            self.change_repo.create(change)
```

### 4. Controller Components

#### MergeAssistantController (FIX existing)
```python
class MergeAssistantController:
    @app.route('/merge/change/<int:change_id>')
    def view_change_detail(change_id: int):
        # Existing logic to retrieve change
        change = self.change_repo.get_by_id(change_id)
        
        # FIX: Retrieve detailed comparison data
        if change.object.object_type == 'constant':
            comparison = self.constant_comparison_repo.get_by_session_and_object(
                change.session_id, change.vendor_object_id)
            return render_template('merge/comparisons/constant_comparison.html',
                                 change=change, comparison=comparison)
        elif change.object.object_type == 'interface':
            comparison = self.interface_comparison_repo.get_by_session_and_object(
                change.session_id, change.vendor_object_id)
            return render_template('merge/comparisons/interface_comparison.html',
                                 change=change, comparison=comparison)
        # ... similar for other object types
```

## Data Models

### Database Schema Changes

#### 1. Changes Table (MODIFY)
```sql
ALTER TABLE changes ADD COLUMN vendor_object_id INTEGER;
ALTER TABLE changes ADD COLUMN customer_object_id INTEGER;

-- Migrate existing data
UPDATE changes SET vendor_object_id = object_id;

-- Add foreign keys
ALTER TABLE changes ADD CONSTRAINT fk_changes_vendor_object 
    FOREIGN KEY (vendor_object_id) REFERENCES object_lookup(id) ON DELETE CASCADE;
ALTER TABLE changes ADD CONSTRAINT fk_changes_customer_object 
    FOREIGN KEY (customer_object_id) REFERENCES object_lookup(id) ON DELETE CASCADE;

-- Keep object_id for backward compatibility but mark as deprecated
```

#### 2. Expression Rules Tables (ALREADY EXISTS)
```sql
-- Tables already exist in models.py
-- ExpressionRule model exists
-- ExpressionRuleInput model exists
-- No migration needed for these tables
```

#### 3. Data Store Tables (NEW - NEED TO CREATE)
```sql
CREATE TABLE data_stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER NOT NULL,
    uuid TEXT NOT NULL,
    name TEXT NOT NULL,
    version_uuid TEXT,
    description TEXT,
    connection_reference TEXT,
    configuration TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
);

CREATE TABLE data_store_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_store_id INTEGER NOT NULL,
    cdt_uuid TEXT NOT NULL,
    table_name TEXT NOT NULL,
    column_mappings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_store_id) REFERENCES data_stores(id) ON DELETE CASCADE
);
```

#### 4. Comparison Tables (ADD MISSING TABLES)
```sql
-- InterfaceComparison, ProcessModelComparison, RecordTypeComparison already exist
-- Need to add these three new comparison tables:

-- Expression Rule Comparisons (NEW)
CREATE TABLE expression_rule_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    input_changes TEXT,  -- JSON
    return_type_change TEXT,
    logic_diff TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    UNIQUE(session_id, object_id)
);

-- CDT Comparisons (NEW)
CREATE TABLE cdt_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    field_changes TEXT,  -- JSON: {added: [], removed: [], modified: []}
    namespace_change TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    UNIQUE(session_id, object_id)
);

-- Constant Comparisons (NEW)
CREATE TABLE constant_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    base_value TEXT,
    customer_value TEXT,
    new_vendor_value TEXT,
    type_change TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    UNIQUE(session_id, object_id)
);
```

### Domain Entities

#### ExpressionRule
```python
@dataclass
class ExpressionRule:
    id: int
    object_id: int
    uuid: str
    name: str
    version_uuid: str
    description: str
    return_type: str
    definition: str
    inputs: List[ExpressionRuleInput]
```

#### RecordType
```python
@dataclass
class RecordType:
    id: int
    object_id: int
    uuid: str
    name: str
    version_uuid: str
    description: str
    data_source: str
    fields: List[RecordTypeField]
    relationships: List[RecordTypeRelationship]
    views: List[RecordTypeView]
    actions: List[RecordTypeAction]
```

#### ComparisonResult
```python
@dataclass
class ComparisonResult:
    session_id: int
    object_id: int
    object_type: str
    comparison_data: dict  # Object-specific comparison details
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated:
- Properties 1.4, 8.2 (duplicate prevention) → Combined into Property 1
- Properties 1.5, 8.3 (multi-version pattern) → Combined into Property 2
- Properties 4.1-4.6 (comparison persistence) → Combined into Property 3
- Properties 6.1-6.6 (UI rendering) → Combined into Property 4
- Properties 8.4 (referential integrity) → Covered by Property 5

### Core Properties

**Property 1: Extraction Completeness**
*For any* Appian package containing objects of any type (Expression Rules, Record Types, CDTs, Data Stores, Process Models, Interfaces, Constants), when the package is extracted, all objects SHALL be stored in object_lookup with correct UUID, name, and object_type, and all object-specific details SHALL be stored in the appropriate tables (expression_rules, record_types, cdts, process_model_nodes, etc.)
**Validates: Requirements 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 7.1, 7.2, 7.3**

**Property 2: No Duplicate Objects**
*For any* object UUID, regardless of how many packages contain that object, there SHALL exist exactly one entry in object_lookup, and the find_or_create method SHALL be idempotent (calling it multiple times with the same UUID produces the same object_lookup entry)
**Validates: Requirements 1.4, 8.2**

**Property 3: Multi-Version Tracking**
*For any* object that exists in multiple packages, there SHALL be one entry in object_lookup and separate entries in object_versions for each package, with package_id and object_id foreign keys correctly linking the versions
**Validates: Requirements 1.5, 8.3**

**Property 4: Child Entity Extraction**
*For any* object with child entities (Expression Rule inputs, Record Type fields/relationships/views/actions, CDT fields, Process Model nodes/flows/variables, Data Store entities), all child entities SHALL be extracted and stored in their respective tables with foreign keys linking to the parent object
**Validates: Requirements 1.3, 2.2, 2.3, 2.4, 2.5, 3.2, 3.5, 7.1, 7.2, 7.3**

**Property 5: Referential Integrity**
*For any* stored object and its related entities, all foreign key constraints SHALL be satisfied (object_id references object_lookup, package_id references packages, parent_id references parent tables), and CASCADE deletes SHALL propagate correctly
**Validates: Requirements 8.4**

**Property 6: Comparison Result Persistence**
*For any* delta object that is compared, the comparison results SHALL be stored in the appropriate object-specific comparison table (interface_comparisons, process_model_comparisons, record_type_comparisons, expression_rule_comparisons, cdt_comparisons, constant_comparisons) with session_id and object_id foreign keys
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7**

**Property 7: Detailed Diff Generation**
*For any* object comparison, the system SHALL generate detailed differences: line-by-line SAIL code diffs for Interfaces and Expression Rules, field-level changes for Record Types and CDTs, node/flow/variable changes for Process Models, and value changes for Constants
**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

**Property 8: Dual Object Tracking in Changes**
*For any* change record created, the vendor_object_id SHALL reference the New Vendor version's object, and the customer_object_id SHALL reference the Customer version's object if it exists, or be NULL if the object is NEW
**Validates: Requirements 5.1, 5.2, 5.3**

**Property 9: Efficient Change Queries**
*For any* change query, the system SHALL support joining to object_lookup twice using vendor_object_id and customer_object_id to retrieve both vendor and customer object details in a single query
**Validates: Requirements 5.4**

**Property 10: UI Data Completeness**
*For any* object change viewed in the merge workflow UI, the system SHALL retrieve and display object-specific details from the appropriate comparison table: constant values for Constants, SAIL code diffs for Interfaces, node/flow/variable diffs and Mermaid diagrams for Process Models, input parameter diffs for Expression Rules, field/relationship/view/action diffs for Record Types, and field diffs for CDTs
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7**

**Property 11: Process Model Structural Completeness**
*For any* Process Model, all nodes SHALL be stored with UUID, name, type, label, position, and configuration, all flows SHALL be stored with UUID, source, target, condition, and label, and all variables SHALL be stored with name, type, multiple flag, default value, and parameter flag
**Validates: Requirements 7.4, 7.5**

**Property 12: Process Model Comparison Completeness**
*For any* Process Model comparison, the system SHALL identify and store all change types: added/removed/modified nodes, added/removed/modified flows, and added/removed/modified variables
**Validates: Requirements 7.6, 7.7**

**Property 13: Error Resilience**
*For any* malformed XML or parsing error encountered during extraction, the system SHALL log the error with object UUID and filename, continue processing remaining objects, and not fail the entire extraction process
**Validates: Requirements 8.5**

**Property 14: Schema Migration Safety**
*For any* existing database with change records, when the schema is modified to add vendor_object_id and customer_object_id columns, all existing data SHALL be preserved without loss, and the object_id column SHALL be migrated to vendor_object_id
**Validates: Requirements 5.5**

## Error Handling

### Parser Error Handling

**Strategy:** Fail-safe parsing with detailed error logging

```python
class BaseParser:
    def parse(self, xml_path: str, package_id: int) -> None:
        try:
            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract object data
            object_data = self._extract_object_data(root)
            
            # Store in database
            self._store_object(object_data, package_id)
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in {xml_path}: {e}")
            # Continue processing other objects
        except Exception as e:
            logger.error(f"Unexpected error parsing {xml_path}: {e}", exc_info=True)
            # Continue processing other objects
```

### Comparison Error Handling

**Strategy:** Graceful degradation with partial results

```python
class DeltaComparisonService:
    def compare_objects(self, session_id: int, base_package_id: int,
                       new_vendor_package_id: int) -> List[DeltaChange]:
        delta_objects = self._identify_delta_objects(base_package_id, new_vendor_package_id)
        
        for delta_obj in delta_objects:
            try:
                comparison = self._generate_comparison(delta_obj)
                self._persist_comparison(session_id, delta_obj.id, comparison)
            except Exception as e:
                logger.error(f"Comparison failed for object {delta_obj.uuid}: {e}")
                # Store minimal comparison result indicating error
                self._persist_error_comparison(session_id, delta_obj.id, str(e))
```

### UI Error Handling

**Strategy:** Display partial data with error indicators

```python
@app.route('/merge/change/<int:change_id>')
def view_change_detail(change_id: int):
    try:
        change = change_repo.get_by_id(change_id)
        comparison = comparison_repo.get_by_session_and_object(
            change.session_id, change.vendor_object_id)
        
        if not comparison:
            # Comparison data missing - show basic info with warning
            return render_template('merge/change_detail.html',
                                 change=change,
                                 comparison=None,
                                 warning="Detailed comparison data not available")
        
        return render_template('merge/change_detail.html',
                             change=change,
                             comparison=comparison)
    except Exception as e:
        logger.error(f"Error loading change {change_id}: {e}")
        return render_template('errors/500.html', error=str(e)), 500
```

### Database Error Handling

**Strategy:** Transaction rollback with retry logic

```python
class BaseRepository:
    def create_with_retry(self, model_instance, max_retries=3):
        for attempt in range(max_retries):
            try:
                db.session.add(model_instance)
                db.session.commit()
                return model_instance
            except IntegrityError as e:
                db.session.rollback()
                if "UNIQUE constraint failed" in str(e):
                    # Handle duplicate - may be expected
                    logger.warning(f"Duplicate entry detected: {e}")
                    return self._find_existing(model_instance)
                else:
                    raise
            except Exception as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    logger.warning(f"Database error, retrying: {e}")
                    time.sleep(0.1 * (attempt + 1))
                else:
                    logger.error(f"Database error after {max_retries} attempts: {e}")
                    raise
```

## Testing Strategy

### Unit Testing

**Scope:** Individual parser, repository, and service methods

**Approach:**
- Test each parser with sample XML files
- Test each repository method with in-memory SQLite database
- Test each service method with mocked dependencies
- Focus on edge cases: empty inputs, malformed data, missing fields

**Example:**
```python
def test_expression_rule_parser_extracts_all_fields():
    # Given: Sample Expression Rule XML
    xml_path = "test_data/sample_expression_rule.xml"
    
    # When: Parser processes the XML
    parser.parse(xml_path, package_id=1)
    
    # Then: All fields are extracted
    rule = expression_rule_repo.get_by_uuid("test-uuid")
    assert rule.name == "Expected Name"
    assert rule.return_type == "Text"
    assert len(rule.inputs) == 2
```

### Property-Based Testing

**Framework:** pytest with real Appian packages from `applicationArtifacts/Three Way Testing Files/V2/`

**Configuration:**
- Use real packages: Base, Customer, New Vendor
- Run complete end-to-end workflow
- Verify properties after each phase
- Clean database between tests

**Property Tests:**

**Test 1: Property 1 - Extraction Completeness**
```python
def test_property_1_extraction_completeness():
    """
    For any Appian package, all objects SHALL be extracted and stored
    **Validates: Requirements 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 7.1, 7.2, 7.3**
    """
    # Given: Real Appian packages
    base_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip"
    
    # When: Package is extracted
    orchestrator.extract_package(base_path, PackageType.BASE, session_id=1)
    
    # Then: All objects are in object_lookup
    expected_objects = count_objects_in_zip(base_path)
    actual_objects = db.session.query(ObjectLookup).count()
    assert actual_objects == expected_objects
    
    # And: Object-specific tables are populated
    assert db.session.query(ExpressionRule).count() > 0
    assert db.session.query(RecordType).count() > 0
    assert db.session.query(CDT).count() > 0
    assert db.session.query(ProcessModelNode).count() > 0
```

**Test 2: Property 2 - No Duplicate Objects**
```python
def test_property_2_no_duplicate_objects():
    """
    For any object UUID, there SHALL be exactly one object_lookup entry
    **Validates: Requirements 1.4, 8.2**
    """
    # Given: Three packages with shared objects
    base_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip"
    customer_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip"
    new_vendor_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip"
    
    # When: All packages are extracted
    orchestrator.extract_package(base_path, PackageType.BASE, session_id=1)
    orchestrator.extract_package(customer_path, PackageType.CUSTOMIZED, session_id=1)
    orchestrator.extract_package(new_vendor_path, PackageType.NEW_VENDOR, session_id=1)
    
    # Then: No duplicate UUIDs in object_lookup
    duplicates = db.session.execute("""
        SELECT uuid, COUNT(*) as count 
        FROM object_lookup 
        GROUP BY uuid 
        HAVING count > 1
    """).fetchall()
    assert len(duplicates) == 0
```

**Test 3: Property 3 - Multi-Version Tracking**
```python
def test_property_3_multi_version_tracking():
    """
    For any object in multiple packages, one object_lookup entry with multiple object_versions
    **Validates: Requirements 1.5, 8.3**
    """
    # Given: Three packages with shared objects
    # When: All packages are extracted
    orchestrator.create_merge_session(base_path, customer_path, new_vendor_path)
    
    # Then: Shared objects have one object_lookup entry
    shared_object = db.session.query(ObjectLookup).filter_by(
        uuid="de199b3f-b072-4438-9508-3b6594827eaf").first()
    assert shared_object is not None
    
    # And: Multiple object_versions entries
    versions = db.session.query(ObjectVersion).filter_by(
        object_id=shared_object.id).all()
    assert len(versions) == 3  # Base, Customer, New Vendor
```

**Test 4: Property 4 - Child Entity Extraction**
```python
def test_property_4_child_entity_extraction():
    """
    For any object with child entities, all children SHALL be extracted
    **Validates: Requirements 1.3, 2.2, 2.3, 2.4, 2.5, 3.2, 3.5, 7.1, 7.2, 7.3**
    """
    # Given: Package with complex objects
    # When: Package is extracted
    orchestrator.extract_package(base_path, PackageType.BASE, session_id=1)
    
    # Then: Expression Rule inputs are extracted
    rule = db.session.query(ExpressionRule).first()
    assert len(rule.inputs) > 0
    
    # And: Record Type fields are extracted
    record_type = db.session.query(RecordType).first()
    assert len(record_type.fields) > 0
    
    # And: Process Model nodes are extracted
    process_model = db.session.query(ProcessModel).first()
    nodes = db.session.query(ProcessModelNode).filter_by(
        process_model_id=process_model.id).all()
    assert len(nodes) > 0
```

**Test 5: Property 6 - Comparison Result Persistence**
```python
def test_property_6_comparison_result_persistence():
    """
    For any delta object, comparison results SHALL be stored
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7**
    """
    # Given: Complete merge session
    session = orchestrator.create_merge_session(base_path, customer_path, new_vendor_path)
    
    # Then: Comparison tables are populated
    interface_comparisons = db.session.query(InterfaceComparison).filter_by(
        session_id=session.id).count()
    assert interface_comparisons > 0
    
    process_model_comparisons = db.session.query(ProcessModelComparison).filter_by(
        session_id=session.id).count()
    assert process_model_comparisons > 0
    
    # And: All delta objects have comparison results
    delta_count = db.session.query(DeltaComparisonResult).filter_by(
        session_id=session.id).count()
    total_comparisons = (interface_comparisons + process_model_comparisons + 
                        # ... other comparison counts)
    assert total_comparisons == delta_count
```

**Test 6: Property 8 - Dual Object Tracking**
```python
def test_property_8_dual_object_tracking():
    """
    For any change, vendor_object_id and customer_object_id SHALL be tracked
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    # Given: Complete merge session
    session = orchestrator.create_merge_session(base_path, customer_path, new_vendor_path)
    
    # Then: All changes have vendor_object_id
    changes = db.session.query(Change).filter_by(session_id=session.id).all()
    for change in changes:
        assert change.vendor_object_id is not None
        
        # And: CONFLICT changes have customer_object_id
        if change.classification == Classification.CONFLICT:
            assert change.customer_object_id is not None
        
        # And: NEW changes have NULL customer_object_id
        if change.classification == Classification.NEW:
            assert change.customer_object_id is None
```

**Test 7: Property 10 - UI Data Completeness**
```python
def test_property_10_ui_data_completeness():
    """
    For any change viewed in UI, object-specific details SHALL be displayed
    **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7**
    """
    # Given: Complete merge session with changes
    session = orchestrator.create_merge_session(base_path, customer_path, new_vendor_path)
    
    # When: Viewing a Constant change
    constant_change = db.session.query(Change).join(ObjectLookup).filter(
        Change.session_id == session.id,
        ObjectLookup.object_type == 'constant'
    ).first()
    
    # Then: Constant comparison data can be retrieved
    comparison = db.session.query(ConstantComparison).filter_by(
        session_id=session.id,
        object_id=constant_change.vendor_object_id
    ).first()
    assert comparison is not None
    assert comparison.base_value is not None
    assert comparison.new_vendor_value is not None
```

**Test 8: Property 11 - Process Model Structural Completeness**
```python
def test_property_11_process_model_structural_completeness():
    """
    For any Process Model, all nodes, flows, and variables SHALL be stored
    **Validates: Requirements 7.4, 7.5**
    """
    # Given: Package with Process Models
    orchestrator.extract_package(base_path, PackageType.BASE, session_id=1)
    
    # Then: Process Model nodes have all attributes
    node = db.session.query(ProcessModelNode).first()
    assert node.uuid is not None
    assert node.name is not None
    assert node.node_type is not None
    assert node.configuration is not None  # JSON
    
    # And: Process Model flows have all attributes
    flow = db.session.query(ProcessModelFlow).first()
    assert flow.uuid is not None
    assert flow.source_node_uuid is not None
    assert flow.target_node_uuid is not None
    
    # And: Process Model variables have all attributes
    variable = db.session.query(ProcessModelVariable).first()
    assert variable.name is not None
    assert variable.data_type is not None
```

**Test 9: Property 13 - Error Resilience**
```python
def test_property_13_error_resilience():
    """
    For any malformed XML, parser SHALL continue processing
    **Validates: Requirements 8.5**
    """
    # Given: Package with one malformed XML file
    # (Create test package with intentionally malformed XML)
    
    # When: Package is extracted
    with pytest.raises(Exception) as exc_info:
        orchestrator.extract_package(malformed_package_path, PackageType.BASE, session_id=1)
    
    # Then: Extraction does not fail completely
    # (Some objects should still be extracted)
    extracted_count = db.session.query(ObjectLookup).count()
    assert extracted_count > 0
    
    # And: Error is logged
    # (Check log file for error message)
```

**Test 10: Property 14 - Schema Migration Safety**
```python
def test_property_14_schema_migration_safety():
    """
    For any existing database, schema migration SHALL preserve data
    **Validates: Requirements 5.5**
    """
    # Given: Database with existing change records (old schema)
    # Create changes with old schema (only object_id column)
    old_change = Change(
        session_id=1,
        object_id=1,
        classification=Classification.CONFLICT,
        status='pending'
    )
    db.session.add(old_change)
    db.session.commit()
    
    # When: Migration is applied
    run_migration("add_vendor_customer_object_ids")
    
    # Then: Existing data is preserved
    migrated_change = db.session.query(Change).filter_by(id=old_change.id).first()
    assert migrated_change.classification == Classification.CONFLICT
    assert migrated_change.status == 'pending'
    
    # And: object_id is migrated to vendor_object_id
    assert migrated_change.vendor_object_id == old_change.object_id
```

### Integration Testing

**Scope:** End-to-end workflow with real packages

**Test Scenarios:**
1. Complete merge workflow with all object types
2. Package extraction with missing object types
3. Comparison with identical objects (no changes)
4. Comparison with all change types (NEW, MODIFIED, DEPRECATED)
5. UI rendering for all object types

### Performance Testing

**Metrics:**
- Package extraction time (target: < 30 seconds for 100 objects)
- Comparison computation time (target: < 60 seconds for 100 objects)
- UI page load time (target: < 2 seconds)
- Database query time (target: < 100ms for change retrieval)

**Load Testing:**
- Test with large packages (500+ objects)
- Test with complex Process Models (50+ nodes)
- Test with large SAIL code files (1000+ lines)

## Implementation Notes

### Parser Implementation Pattern

All parsers MUST follow this pattern:

```python
class ObjectTypeParser(BaseParser):
    def __init__(self, object_lookup_repo, object_type_repo):
        self.object_lookup_repo = object_lookup_repo
        self.object_type_repo = object_type_repo
    
    def parse(self, xml_path: str, package_id: int) -> None:
        # 1. Parse XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 2. Extract object metadata
        uuid = root.find('.//uuid').text
        name = root.find('.//name').text
        # ... other fields
        
        # 3. Find or create object_lookup entry
        object_lookup = self.object_lookup_repo.find_or_create(
            uuid=uuid,
            name=name,
            object_type='objectType'
        )
        
        # 4. Store object-specific data
        object_data = self.object_type_repo.create(
            object_id=object_lookup.id,
            # ... object-specific fields
        )
        
        # 5. Store object version
        self.object_lookup_repo.create_version(
            object_id=object_lookup.id,
            package_id=package_id,
            version_uuid=version_uuid,
            # ... version-specific data
        )
        
        # 6. Store child entities
        for child in root.findall('.//child'):
            self.object_type_repo.create_child(
                parent_id=object_data.id,
                # ... child fields
            )
```

### Comparison Service Pattern

All comparison services MUST follow this pattern:

```python
def compare_object_type(self, session_id: int, object_id: int) -> dict:
    # 1. Retrieve object versions
    base_version = self._get_version(object_id, PackageType.BASE)
    customer_version = self._get_version(object_id, PackageType.CUSTOMIZED)
    new_vendor_version = self._get_version(object_id, PackageType.NEW_VENDOR)
    
    # 2. Generate detailed diff
    diff = self._generate_diff(base_version, new_vendor_version)
    
    # 3. Persist comparison result
    comparison = self.comparison_repo.create_comparison(
        session_id=session_id,
        object_id=object_id,
        comparison_data=diff
    )
    
    return comparison
```

### Database Migration Strategy

1. Create migration script: `migrations/migrations_003_data_completeness.py`
2. Add new tables: expression_rules, data_stores, comparison tables
3. Modify changes table: add vendor_object_id, customer_object_id
4. Migrate existing data: `UPDATE changes SET vendor_object_id = object_id`
5. Add foreign key constraints
6. Test migration with existing data

### UI Template Pattern

All object-specific comparison templates MUST follow this pattern:

```html
<!-- templates/merge/comparisons/object_type_comparison.html -->
{% extends "merge/_base_comparison.html" %}

{% block comparison_content %}
<div class="comparison-container">
    <div class="version-column">
        <h4>Base Version</h4>
        <!-- Display base version details -->
    </div>
    
    <div class="version-column">
        <h4>Customer Version</h4>
        <!-- Display customer version details -->
    </div>
    
    <div class="version-column">
        <h4>New Vendor Version</h4>
        <!-- Display new vendor version details -->
    </div>
</div>

<div class="diff-container">
    <!-- Display detailed diff -->
</div>
{% endblock %}
```

## Dependencies

### External Libraries
- `lxml` or `xml.etree.ElementTree` - XML parsing
- `difflib` - Text diff generation
- `pygments` - Syntax highlighting for SAIL code
- `pytest` - Testing framework
- `SQLAlchemy` - ORM

### Internal Dependencies
- `core/dependency_container.py` - DI container
- `repositories/object_lookup_repository.py` - Object management
- `services/package_extraction_service.py` - Package processing
- `services/delta_comparison_service.py` - Comparison logic
- `models.py` - Database models

## Deployment Considerations

### Database Migration
1. Backup existing database before migration
2. Run migration script in transaction
3. Verify data integrity after migration
4. Rollback plan: restore from backup

### Backward Compatibility
- Keep `object_id` column in changes table for backward compatibility
- Deprecate but don't remove old comparison logic
- Support both old and new UI templates during transition

### Performance Impact
- New parsers will increase extraction time by ~20%
- Comparison result persistence will increase comparison time by ~10%
- UI rendering will be faster due to pre-computed comparisons

### Monitoring
- Log parser execution times
- Log comparison execution times
- Monitor database table sizes
- Track UI page load times
- Alert on parsing errors
