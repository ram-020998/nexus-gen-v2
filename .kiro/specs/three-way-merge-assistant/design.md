# Design Document: Three-Way Merge Assistant

## Overview

The Three-Way Merge Assistant is a comprehensive feature that enables Appian application customers to upgrade from their customized version to a new vendor release while preserving their customizations. The system performs a three-way analysis comparing the base vendor version (A), the customer's customized version (B), and the new vendor release (C) to identify conflicts and provide guided merge assistance.

### Key Design Principles

1. **Customer Customizations First**: The customer's customized version (B) is treated as the primary version, with vendor changes (A→C) being incorporated into it
2. **Manual Merge with Intelligent Guidance**: The system provides detailed analysis and recommendations but leaves final merge decisions to the user
3. **Progressive Disclosure**: Start with simple, non-conflicting changes to build user confidence before tackling complex conflicts
4. **Session Persistence**: All progress is saved to enable resumption and provide audit trails
5. **Reuse Existing Infrastructure**: Leverage the existing AppianAnalyzer and comparison services

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Interface Layer                      │
│  (Upload UI, Summary View, Workflow UI, Report Generation)   │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                  Controller Layer                            │
│              (merge_assistant_controller.py)                 │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                   Service Layer                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ThreeWayMergeService (Orchestration)                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  BlueprintGenerationService                          │   │
│  │  (Reuses AppianAnalyzer)                             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ThreeWayComparisonService                           │   │
│  │  (A→B, A→C comparisons, conflict detection)          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ChangeClassificationService                         │   │
│  │  (NO_CONFLICT, CONFLICT, CUSTOMER_ONLY, etc.)        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MergeGuidanceService                                │   │
│  │  (Generate merge strategies and recommendations)     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DependencyAnalysisService                           │   │
│  │  (Topological sort, circular dependency detection)   │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                  Data Layer                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MergeSession (Database Model)                       │   │
│  │  - Session metadata                                  │   │
│  │  - Three blueprints (A, B, C)                        │   │
│  │  - Comparison results                                │   │
│  │  - Classification results                            │   │
│  │  - User progress and notes                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Upload → Controller → ThreeWayMergeService
                              ↓
                    BlueprintGenerationService (A, B, C)
                              ↓
                    ThreeWayComparisonService (A→B, A→C)
                              ↓
                    ChangeClassificationService
                              ↓
                    DependencyAnalysisService (ordering)
                              ↓
                    MergeGuidanceService (recommendations)
                              ↓
                    Save to MergeSession
                              ↓
                    Return to User (Summary View)
```

## Components and Interfaces

### 1. Database Models

#### MergeSession Model

```python
class MergeSession(db.Model):
    """Stores three-way merge session data"""
    __tablename__ = 'merge_sessions'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(20), unique=True)  # MRG_001
    
    # Package information
    base_package_name = db.Column(db.String(255))  # A
    customized_package_name = db.Column(db.String(255))  # B
    new_vendor_package_name = db.Column(db.String(255))  # C
    
    # Status tracking
    status = db.Column(db.String(20))  # 'processing', 'ready', 'in_progress', 'completed', 'error'
    current_change_index = db.Column(db.Integer, default=0)
    
    # Analysis results (JSON strings)
    base_blueprint = db.Column(db.Text)  # Blueprint A
    customized_blueprint = db.Column(db.Text)  # Blueprint B
    new_vendor_blueprint = db.Column(db.Text)  # Blueprint C
    
    vendor_changes = db.Column(db.Text)  # A→C comparison results
    customer_changes = db.Column(db.Text)  # A→B comparison results
    classification_results = db.Column(db.Text)  # Classified changes
    ordered_changes = db.Column(db.Text)  # Smart-ordered change list
    
    # Progress tracking
    total_changes = db.Column(db.Integer)
    reviewed_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    total_time = db.Column(db.Integer)  # seconds
    error_log = db.Column(db.Text)
    
    # Relationships
    change_reviews = db.relationship('ChangeReview', backref='session', lazy=True)
```

#### ChangeReview Model

```python
class ChangeReview(db.Model):
    """Stores user review actions for each change"""
    __tablename__ = 'change_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'))
    
    # Change identification
    object_uuid = db.Column(db.String(255))
    object_name = db.Column(db.String(255))
    object_type = db.Column(db.String(50))
    classification = db.Column(db.String(50))  # NO_CONFLICT, CONFLICT, etc.
    
    # Review status
    review_status = db.Column(db.String(20))  # 'pending', 'reviewed', 'skipped'
    user_notes = db.Column(db.Text)
    
    # Timestamps
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 2. Service Layer Components

#### ThreeWayMergeService

Main orchestration service that coordinates the entire merge workflow.

```python
class ThreeWayMergeService:
    """Orchestrates the three-way merge process"""
    
    def create_session(
        self,
        base_zip_path: str,
        customized_zip_path: str,
        new_vendor_zip_path: str
    ) -> MergeSession:
        """
        Create a new merge session and initiate analysis
        
        Steps:
        1. Create session record
        2. Generate blueprints for A, B, C
        3. Perform comparisons (A→B, A→C)
        4. Classify changes
        5. Order changes intelligently
        6. Generate merge guidance
        7. Update session status to 'ready'
        """
        pass
    
    def get_session(self, session_id: int) -> MergeSession:
        """Retrieve session by ID"""
        pass
    
    def get_summary(self, session_id: int) -> Dict[str, Any]:
        """Get merge summary with statistics"""
        pass
    
    def get_ordered_changes(self, session_id: int) -> List[Dict[str, Any]]:
        """Get smart-ordered list of changes"""
        pass
    
    def update_progress(
        self,
        session_id: int,
        change_index: int,
        review_status: str,
        notes: str = None
    ) -> None:
        """Update user progress on a specific change"""
        pass
    
    def generate_report(self, session_id: int) -> Dict[str, Any]:
        """Generate final merge report"""
        pass
```

#### BlueprintGenerationService

Wraps the existing AppianAnalyzer to generate blueprints for all three packages.

```python
class BlueprintGenerationService:
    """Generates blueprints using existing AppianAnalyzer"""
    
    def generate_blueprint(self, zip_path: str) -> Dict[str, Any]:
        """
        Generate blueprint for a single package
        
        Reuses: AppianAnalyzer.analyze()
        Returns: Blueprint dictionary
        """
        pass
    
    def generate_all_blueprints(
        self,
        base_path: str,
        customized_path: str,
        new_vendor_path: str
    ) -> Tuple[Dict, Dict, Dict]:
        """Generate blueprints for all three packages in parallel"""
        pass
```

#### ThreeWayComparisonService

Performs two-way comparisons (A→B and A→C) using existing comparison infrastructure.

```python
class ThreeWayComparisonService:
    """Performs three-way comparison analysis"""
    
    def __init__(self):
        self.comparator = EnhancedVersionComparator()
    
    def compare_vendor_changes(
        self,
        base_blueprint: Dict,
        new_vendor_blueprint: Dict
    ) -> Dict[str, Any]:
        """
        Compare A→C to identify vendor changes
        
        Returns: {
            'added': [...],
            'modified': [...],
            'removed': [...]
        }
        """
        pass
    
    def compare_customer_changes(
        self,
        base_blueprint: Dict,
        customized_blueprint: Dict
    ) -> Dict[str, Any]:
        """
        Compare A→B to identify customer changes
        
        Returns: {
            'added': [...],
            'modified': [...],
            'removed': [...]
        }
        """
        pass
    
    def perform_three_way_comparison(
        self,
        base_blueprint: Dict,
        customized_blueprint: Dict,
        new_vendor_blueprint: Dict
    ) -> Tuple[Dict, Dict]:
        """
        Perform both comparisons
        
        Returns: (vendor_changes, customer_changes)
        """
        pass
```

#### ChangeClassificationService

Classifies changes into categories based on conflict analysis.

```python
class ChangeClassificationService:
    """Classifies changes based on conflict analysis"""
    
    def classify_changes(
        self,
        vendor_changes: Dict[str, Any],
        customer_changes: Dict[str, Any]
    ) -> Dict[str, List[Dict]]:
        """
        Classify all changes into categories
        
        Returns: {
            'NO_CONFLICT': [...],
            'CONFLICT': [...],
            'CUSTOMER_ONLY': [...],
            'REMOVED_BUT_CUSTOMIZED': [...]
        }
        """
        pass
    
    def _is_conflict(
        self,
        object_uuid: str,
        vendor_changes: Dict,
        customer_changes: Dict
    ) -> bool:
        """Check if object has conflicting changes"""
        pass
    
    def _classify_single_object(
        self,
        object_uuid: str,
        vendor_changes: Dict,
        customer_changes: Dict
    ) -> str:
        """Classify a single object"""
        pass
```

#### DependencyAnalysisService

Analyzes object dependencies and provides smart ordering.

```python
class DependencyAnalysisService:
    """Analyzes dependencies and provides smart ordering"""
    
    def build_dependency_graph(
        self,
        blueprint: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Build dependency graph from blueprint
        
        Returns: {object_uuid: [parent_uuid1, parent_uuid2, ...]}
        """
        pass
    
    def topological_sort(
        self,
        objects: List[str],
        dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """
        Sort objects by dependency order (parents before children)
        
        Handles circular dependencies by breaking cycles
        """
        pass
    
    def order_changes(
        self,
        classified_changes: Dict[str, List[Dict]],
        dependency_graph: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Order changes intelligently:
        1. NO_CONFLICT changes first (grouped by type)
        2. CONFLICT changes (ordered by dependencies)
        3. REMOVED_BUT_CUSTOMIZED changes last
        """
        pass
    
    def get_dependencies(
        self,
        object_uuid: str,
        dependency_graph: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Get dependency information for an object
        
        Returns: {
            'parents': [...],  # Objects this depends on
            'children': [...]  # Objects that depend on this
        }
        """
        pass
```

#### MergeGuidanceService

Generates merge strategies and recommendations for each change.

```python
class MergeGuidanceService:
    """Generates merge guidance and recommendations"""
    
    def generate_guidance(
        self,
        change: Dict[str, Any],
        base_object: Dict,
        customer_object: Dict,
        vendor_object: Dict
    ) -> Dict[str, Any]:
        """
        Generate merge guidance for a change
        
        Returns: {
            'strategy': 'INCORPORATE_VENDOR_ADDITIONS',
            'recommendations': [...],
            'vendor_additions': [...],
            'vendor_modifications': [...],
            'conflict_sections': [...]
        }
        """
        pass
    
    def _identify_vendor_additions(
        self,
        base_object: Dict,
        vendor_object: Dict,
        customer_object: Dict
    ) -> List[Dict]:
        """Identify new code/features added by vendor"""
        pass
    
    def _identify_vendor_modifications(
        self,
        base_object: Dict,
        vendor_object: Dict
    ) -> List[Dict]:
        """Identify modifications made by vendor"""
        pass
    
    def _identify_conflict_sections(
        self,
        base_object: Dict,
        customer_object: Dict,
        vendor_object: Dict
    ) -> List[Dict]:
        """Identify sections modified by both parties"""
        pass
    
    def _generate_merge_strategy(
        self,
        classification: str,
        vendor_additions: List,
        conflict_sections: List
    ) -> str:
        """Determine appropriate merge strategy"""
        pass
```

### 3. Controller Layer

#### MergeAssistantController

```python
# controllers/merge_assistant_controller.py

@app.route('/merge-assistant', methods=['GET'])
def merge_assistant_home():
    """Display upload page for three packages"""
    pass

@app.route('/merge-assistant/upload', methods=['POST'])
def upload_packages():
    """
    Handle three package uploads and create session
    
    Expected form data:
    - base_package: ZIP file (A)
    - customized_package: ZIP file (B)
    - new_vendor_package: ZIP file (C)
    """
    pass

@app.route('/merge-assistant/session/<int:session_id>/summary', methods=['GET'])
def view_summary(session_id):
    """Display merge summary with statistics"""
    pass

@app.route('/merge-assistant/session/<int:session_id>/workflow', methods=['GET'])
def start_workflow(session_id):
    """Start the guided merge workflow"""
    pass

@app.route('/merge-assistant/session/<int:session_id>/change/<int:change_index>', methods=['GET'])
def view_change(session_id, change_index):
    """Display specific change with three-way diff"""
    pass

@app.route('/merge-assistant/session/<int:session_id>/change/<int:change_index>/review', methods=['POST'])
def review_change(session_id, change_index):
    """
    Record user review action
    
    Expected JSON:
    {
        'action': 'reviewed' | 'skipped',
        'notes': 'optional user notes'
    }
    """
    pass

@app.route('/merge-assistant/session/<int:session_id>/report', methods=['GET'])
def generate_report(session_id):
    """Generate and display final merge report"""
    pass

@app.route('/merge-assistant/sessions', methods=['GET'])
def list_sessions():
    """List all merge sessions"""
    pass
```

## Data Models

### Change Classification Types

```python
class ChangeClassification(Enum):
    NO_CONFLICT = "NO_CONFLICT"  # Only vendor changed
    CONFLICT = "CONFLICT"  # Both changed
    CUSTOMER_ONLY = "CUSTOMER_ONLY"  # Only customer changed
    REMOVED_BUT_CUSTOMIZED = "REMOVED_BUT_CUSTOMIZED"  # Vendor removed, customer modified
```

### Change Object Structure

```python
{
    "uuid": "object_uuid",
    "name": "Object Name",
    "type": "Interface",
    "classification": "CONFLICT",
    "base_object": {...},  # Object from A
    "customer_object": {...},  # Object from B
    "vendor_object": {...},  # Object from C
    "vendor_changes": {
        "added_sections": [...],
        "modified_sections": [...],
        "removed_sections": [...]
    },
    "customer_changes": {
        "added_sections": [...],
        "modified_sections": [...],
        "removed_sections": [...]
    },
    "conflict_sections": [...],
    "merge_guidance": {
        "strategy": "INCORPORATE_VENDOR_ADDITIONS",
        "recommendations": [...],
        "priority": "HIGH"
    },
    "dependencies": {
        "parents": [...],
        "children": [...]
    }
}
```

### Merge Summary Structure

```python
{
    "session_id": 1,
    "reference_id": "MRG_001",
    "packages": {
        "base": "GSS 1.0.0",
        "customized": "GSS 1.0.0 CUS 1.0",
        "new_vendor": "GSS 2.0.0"
    },
    "statistics": {
        "total_changes": 150,
        "no_conflict": 80,
        "conflict": 50,
        "customer_only": 15,
        "removed_but_customized": 5
    },
    "breakdown_by_type": {
        "interfaces": {"no_conflict": 20, "conflict": 15, ...},
        "process_models": {...},
        "record_types": {...}
    },
    "estimated_complexity": "MEDIUM",
    "estimated_time_hours": 8
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Package validation correctness
*For any* uploaded ZIP file, the validation function should correctly identify whether it is a valid Appian application package based on the presence of required files and structure.
**Validates: Requirements 1.2**

### Property 2: Session creation atomicity
*For any* three valid packages, clicking "Start Analysis" should create exactly one merge session with a unique reference ID stored in the database.
**Validates: Requirements 1.4**

### Property 3: Error message clarity
*For any* invalid package upload, the system should display an error message that identifies which specific package (A, B, or C) is invalid and includes the validation failure reason.
**Validates: Requirements 1.5**

### Property 4: Blueprint generation completeness
*For any* merge session, the system should generate blueprints for all three packages (A, B, C) and store them with the session.
**Validates: Requirements 2.1, 2.2**

### Property 5: Blueprint failure handling
*For any* package that causes blueprint generation to fail, the session status should be marked as 'failed' and error details should be stored.
**Validates: Requirements 2.3**

### Property 6: Workflow progression after blueprints
*For any* session where all three blueprints are successfully generated, the system should automatically proceed to the comparison phase.
**Validates: Requirements 2.4**

### Property 7: Vendor change identification
*For any* two blueprints (A and C), the comparison should correctly identify all objects that are ADDED, MODIFIED, or REMOVED in C relative to A.
**Validates: Requirements 3.2**

### Property 8: Change detail capture
*For any* modified object, the comparison results should include specific change details (SAIL code differences, field changes, property changes).
**Validates: Requirements 3.4, 4.4**

### Property 9: Customer change identification
*For any* two blueprints (A and B), the comparison should correctly identify all objects that are ADDED, MODIFIED, or REMOVED in B relative to A.
**Validates: Requirements 4.2**

### Property 10: Conflict detection accuracy
*For any* object UUID, if the object is modified in both vendor changes (A→C) and customer changes (A→B), it should be classified as CONFLICT.
**Validates: Requirements 5.1**

### Property 11: Classification completeness
*For any* object in the union of vendor changes and customer changes, the system should assign exactly one classification from {NO_CONFLICT, CONFLICT, CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED}.
**Validates: Requirements 5.2**

### Property 12: Summary statistics accuracy
*For any* merge session, the displayed summary counts for each classification category should match the actual number of objects in each category from the classification results.
**Validates: Requirements 6.2**

### Property 13: Breakdown accuracy
*For any* merge session, the breakdown by object type should correctly count objects of each type within each classification category.
**Validates: Requirements 6.3**

### Property 14: Change ordering correctness
*For any* classified change set, the ordered change list should present NO_CONFLICT changes first, then CONFLICT changes, then REMOVED_BUT_CUSTOMIZED changes.
**Validates: Requirements 7.1**

### Property 15: Object type grouping
*For any* set of NO_CONFLICT changes, objects of the same type should be grouped together in the ordered list.
**Validates: Requirements 7.2**

### Property 16: Dependency ordering
*For any* set of CONFLICT changes with dependencies, parent objects should appear before their child objects in the ordered list.
**Validates: Requirements 7.3**

### Property 17: Change detail display completeness
*For any* change being viewed, the display should include the object name, type, and classification category.
**Validates: Requirements 8.1**

### Property 18: Three-way diff display
*For any* CONFLICT change, the display should show three columns containing Base (A), Customer (B), and Vendor (C) versions.
**Validates: Requirements 8.3**

### Property 19: Vendor change highlighting
*For any* CONFLICT change, the diff should highlight which specific vendor changes (A→C) need to be incorporated into the customer version (B).
**Validates: Requirements 8.4**

### Property 20: SAIL code formatting
*For any* SAIL code displayed in diffs, UUIDs should be replaced with readable object names and code should be properly indented.
**Validates: Requirements 9.3**

### Property 21: Merge strategy provision
*For any* CONFLICT change, the system should provide a "Suggested Merge Strategy" section with recommendations.
**Validates: Requirements 9.6**

### Property 22: Progress tracking accuracy
*For any* user action (mark as reviewed or skip), the progress counter should increment and the session state should be updated in the database.
**Validates: Requirements 10.2, 10.3**

### Property 23: Session persistence round-trip
*For any* merge session, if a user navigates away and returns, the restored session state should match the saved state including current change index and review statuses.
**Validates: Requirements 10.5**

### Property 24: Report generation completeness
*For any* completed merge workflow, the generated report should include summary statistics (total changes, reviewed count, skipped count, conflict count).
**Validates: Requirements 12.2**

### Property 25: Report detail completeness
*For any* generated report, all changes should be listed with their classification, review status, and any user notes.
**Validates: Requirements 12.3**

### Property 26: Filter correctness
*For any* applied filter (classification, object type, or review status), the filtered change list should contain only changes that match the filter criteria.
**Validates: Requirements 13.2**

### Property 27: Search functionality
*For any* search query, the system should highlight all changes whose object names contain the search term.
**Validates: Requirements 13.4**

### Property 28: Ordering preservation after filtering
*For any* filtered change list, the smart ordering (NO_CONFLICT, CONFLICT, REMOVED_BUT_CUSTOMIZED) should be maintained within the filtered results.
**Validates: Requirements 13.5**

### Property 29: Dependency display completeness
*For any* change being viewed, the system should display both parent objects (dependencies) and child objects (reverse dependencies).
**Validates: Requirements 14.1, 14.2**

### Property 30: Dependency status indication
*For any* displayed dependency, the system should show its review status (reviewed, pending, or skipped).
**Validates: Requirements 14.3**

### Property 31: Vendor addition identification
*For any* CONFLICT change, the system should identify specific vendor additions (new functions, fields, logic) that do not exist in the customer version.
**Validates: Requirements 15.1**

### Property 32: Vendor modification identification
*For any* CONFLICT change, the system should identify vendor modifications to sections that exist in both base and customer versions.
**Validates: Requirements 15.2**

### Property 33: Session metadata persistence
*For any* created merge session, the database should store session metadata including session ID, timestamps, and all three package names.
**Validates: Requirements 16.1**

### Property 34: Blueprint persistence
*For any* merge session with generated blueprints, all three blueprints (A, B, C) should be stored in the database with the session.
**Validates: Requirements 16.2**

### Property 35: Real-time state updates
*For any* user review action, the session state in the database should be updated immediately (within the same request cycle).
**Validates: Requirements 16.4, 16.5**

### Property 36: Merge strategy recommendations
*For any* CONFLICT change, the system should provide merge strategy recommendations appropriate to the type of conflict.
**Validates: Requirements 17.1**

## Error Handling

### Error Categories

1. **Upload Errors**
   - Invalid ZIP file format
   - Missing required Appian package files
   - Corrupted package files
   - File size limits exceeded

2. **Blueprint Generation Errors**
   - XML parsing failures
   - Missing object definitions
   - Invalid object references
   - Unsupported Appian version

3. **Comparison Errors**
   - Blueprint structure mismatches
   - Missing object lookup data
   - Invalid UUID references

4. **Database Errors**
   - Session creation failures
   - Data persistence failures
   - Transaction rollback scenarios

5. **Workflow Errors**
   - Invalid session state
   - Missing change data
   - Circular dependency resolution failures

### Error Handling Strategies

#### Upload Phase
```python
try:
    validate_package(zip_file)
except InvalidPackageError as e:
    return {
        'error': True,
        'package': package_name,  # A, B, or C
        'message': str(e),
        'details': e.validation_errors
    }
```

#### Blueprint Generation Phase
```python
try:
    blueprint = analyzer.analyze(zip_path)
except BlueprintGenerationError as e:
    session.status = 'failed'
    session.error_log = json.dumps({
        'phase': 'blueprint_generation',
        'package': package_name,
        'error': str(e),
        'traceback': traceback.format_exc()
    })
    db.session.commit()
    raise
```

#### Comparison Phase
```python
try:
    vendor_changes = comparator.compare(base, new_vendor)
except ComparisonError as e:
    session.status = 'failed'
    session.error_log = json.dumps({
        'phase': 'comparison',
        'comparison_type': 'vendor_changes',
        'error': str(e)
    })
    db.session.commit()
    raise
```

#### Circular Dependency Handling
```python
def topological_sort_with_cycle_detection(objects, dependencies):
    """
    Perform topological sort with cycle detection
    
    If cycles detected:
    1. Identify strongly connected components
    2. Break cycles by removing lowest-priority edges
    3. Log warning about circular dependencies
    4. Continue with best-effort ordering
    """
    try:
        return topological_sort(objects, dependencies)
    except CircularDependencyError as e:
        logger.warning(f"Circular dependency detected: {e.cycle}")
        # Break cycle and retry
        broken_deps = break_cycle(dependencies, e.cycle)
        return topological_sort(objects, broken_deps)
```

### User-Facing Error Messages

All error messages should follow this format:
```python
{
    'title': 'Short error title',
    'message': 'User-friendly explanation',
    'technical_details': 'Technical information for debugging',
    'suggested_action': 'What the user should do next'
}
```

Example:
```python
{
    'title': 'Invalid Package',
    'message': 'The Base Package (A) you uploaded is not a valid Appian application package.',
    'technical_details': 'Missing required file: application.properties',
    'suggested_action': 'Please ensure you uploaded the correct ZIP file exported from Appian.'
}
```

## Testing Strategy

### Unit Testing

Unit tests will verify individual components and functions:

1. **Package Validation Tests**
   - Test valid Appian packages are accepted
   - Test invalid packages are rejected with appropriate errors
   - Test edge cases (empty ZIP, corrupted files, missing metadata)

2. **Blueprint Generation Tests**
   - Test blueprint generation for various package sizes
   - Test error handling for malformed packages
   - Test blueprint storage and retrieval

3. **Comparison Logic Tests**
   - Test two-way comparison (A→B, A→C)
   - Test change identification (ADDED, MODIFIED, REMOVED)
   - Test change detail extraction

4. **Classification Tests**
   - Test NO_CONFLICT classification
   - Test CONFLICT classification
   - Test CUSTOMER_ONLY classification
   - Test REMOVED_BUT_CUSTOMIZED classification

5. **Dependency Analysis Tests**
   - Test dependency graph construction
   - Test topological sorting
   - Test circular dependency detection and resolution

6. **Merge Guidance Tests**
   - Test vendor addition identification
   - Test vendor modification identification
   - Test conflict section identification
   - Test merge strategy generation

### Property-Based Testing

Property-based tests will use **Hypothesis** (Python) to verify correctness properties across many randomly generated inputs.

#### Test Configuration
- Minimum 100 iterations per property test
- Use custom generators for Appian objects and blueprints
- Tag each test with the property number from the design document

#### Key Property Tests

1. **Classification Completeness Property**
```python
@given(vendor_changes=blueprint_changes(), customer_changes=blueprint_changes())
def test_classification_completeness(vendor_changes, customer_changes):
    """
    Feature: three-way-merge-assistant, Property 11: Classification completeness
    
    For any object in the union of vendor and customer changes,
    exactly one classification should be assigned.
    """
    classifier = ChangeClassificationService()
    results = classifier.classify_changes(vendor_changes, customer_changes)
    
    all_objects = set(vendor_changes.keys()) | set(customer_changes.keys())
    classified_objects = set()
    
    for category in results.values():
        for obj in category:
            assert obj['uuid'] not in classified_objects, "Object classified multiple times"
            classified_objects.add(obj['uuid'])
    
    assert classified_objects == all_objects, "Not all objects were classified"
```

2. **Dependency Ordering Property**
```python
@given(changes=conflict_changes_with_dependencies())
def test_dependency_ordering(changes):
    """
    Feature: three-way-merge-assistant, Property 16: Dependency ordering
    
    For any set of CONFLICT changes with dependencies,
    parent objects should appear before children in ordered list.
    """
    dependency_service = DependencyAnalysisService()
    dependency_graph = dependency_service.build_dependency_graph(changes['blueprint'])
    ordered = dependency_service.order_changes(changes, dependency_graph)
    
    seen = set()
    for change in ordered:
        if change['classification'] == 'CONFLICT':
            parents = dependency_graph.get(change['uuid'], [])
            for parent in parents:
                assert parent in seen, f"Parent {parent} appears after child {change['uuid']}"
            seen.add(change['uuid'])
```

3. **Session Persistence Round-Trip Property**
```python
@given(session_data=merge_session_data())
def test_session_persistence_round_trip(session_data):
    """
    Feature: three-way-merge-assistant, Property 23: Session persistence round-trip
    
    For any merge session, saving and restoring should preserve all state.
    """
    service = ThreeWayMergeService()
    
    # Create and save session
    session = service.create_session(**session_data)
    original_state = {
        'current_change_index': session.current_change_index,
        'reviewed_count': session.reviewed_count,
        'skipped_count': session.skipped_count,
        'status': session.status
    }
    
    # Simulate navigation away and return
    session_id = session.id
    db.session.expunge_all()  # Clear session cache
    
    # Restore session
    restored_session = service.get_session(session_id)
    restored_state = {
        'current_change_index': restored_session.current_change_index,
        'reviewed_count': restored_session.reviewed_count,
        'skipped_count': restored_session.skipped_count,
        'status': restored_session.status
    }
    
    assert original_state == restored_state, "Session state not preserved"
```

4. **Filter Correctness Property**
```python
@given(changes=classified_changes(), filter_criteria=filter_criteria())
def test_filter_correctness(changes, filter_criteria):
    """
    Feature: three-way-merge-assistant, Property 26: Filter correctness
    
    For any applied filter, filtered results should only contain matching changes.
    """
    service = ThreeWayMergeService()
    filtered = service.filter_changes(changes, filter_criteria)
    
    for change in filtered:
        if 'classification' in filter_criteria:
            assert change['classification'] == filter_criteria['classification']
        if 'object_type' in filter_criteria:
            assert change['type'] == filter_criteria['object_type']
        if 'review_status' in filter_criteria:
            assert change['review_status'] == filter_criteria['review_status']
```

5. **Summary Statistics Accuracy Property**
```python
@given(classification_results=classification_results())
def test_summary_statistics_accuracy(classification_results):
    """
    Feature: three-way-merge-assistant, Property 12: Summary statistics accuracy
    
    For any classification results, summary counts should match actual counts.
    """
    service = ThreeWayMergeService()
    summary = service.generate_summary(classification_results)
    
    assert summary['no_conflict'] == len(classification_results['NO_CONFLICT'])
    assert summary['conflict'] == len(classification_results['CONFLICT'])
    assert summary['customer_only'] == len(classification_results['CUSTOMER_ONLY'])
    assert summary['removed_but_customized'] == len(classification_results['REMOVED_BUT_CUSTOMIZED'])
    assert summary['total_changes'] == sum([
        len(classification_results['NO_CONFLICT']),
        len(classification_results['CONFLICT']),
        len(classification_results['CUSTOMER_ONLY']),
        len(classification_results['REMOVED_BUT_CUSTOMIZED'])
    ])
```

### Integration Testing

Integration tests will verify end-to-end workflows:

1. **Full Merge Workflow Test**
   - Upload three packages
   - Generate blueprints
   - Perform comparisons
   - Classify changes
   - Navigate through workflow
   - Generate report

2. **Session Persistence Test**
   - Create session
   - Review some changes
   - Simulate browser close
   - Restore session
   - Verify state preserved

3. **Error Recovery Test**
   - Trigger various error conditions
   - Verify appropriate error handling
   - Verify session state remains consistent

### Test Data

Test data will include:
- Sample Appian packages of various sizes (small, medium, large)
- Packages with known differences for comparison testing
- Packages with circular dependencies
- Malformed packages for error testing

Test packages should be stored in:
```
tests/fixtures/three_way_merge/
├── base_packages/
│   ├── small_app_v1.zip
│   ├── medium_app_v1.zip
│   └── large_app_v1.zip
├── customized_packages/
│   ├── small_app_v1_custom.zip
│   ├── medium_app_v1_custom.zip
│   └── large_app_v1_custom.zip
├── new_vendor_packages/
│   ├── small_app_v2.zip
│   ├── medium_app_v2.zip
│   └── large_app_v2.zip
└── invalid_packages/
    ├── corrupted.zip
    ├── empty.zip
    └── missing_metadata.zip
```

## Performance Considerations

### Expected Performance Targets

- **Blueprint Generation**: < 5 seconds per package for typical applications (< 1000 objects)
- **Comparison**: < 3 seconds for two blueprints
- **Classification**: < 1 second for typical change sets
- **Dependency Analysis**: < 2 seconds for typical dependency graphs
- **Page Load Times**: < 1 second for all UI pages
- **Database Operations**: < 100ms for individual queries

### Optimization Strategies

1. **Parallel Blueprint Generation**
   - Generate blueprints for A, B, C in parallel using threading
   - Expected speedup: 3x for blueprint phase

2. **Caching**
   - Cache blueprint object lookups in memory
   - Cache dependency graphs
   - Cache classification results

3. **Database Indexing**
   - Index on `merge_sessions.reference_id`
   - Index on `change_reviews.session_id`
   - Index on `change_reviews.object_uuid`

4. **Lazy Loading**
   - Load change details on-demand rather than all at once
   - Paginate change lists for large merge sessions

5. **Background Processing**
   - Use background tasks for blueprint generation and comparison
   - Provide real-time progress updates via WebSocket or polling

### Scalability Considerations

- **Large Applications**: Applications with > 2000 objects may require additional optimization
- **Concurrent Sessions**: Support multiple users running merge sessions simultaneously
- **Database Growth**: Implement session cleanup for old completed sessions

## Security Considerations

1. **File Upload Security**
   - Validate ZIP file structure before extraction
   - Limit file sizes (e.g., 100MB max)
   - Scan for malicious content
   - Extract to temporary directories with restricted permissions

2. **Data Privacy**
   - Store session data with appropriate access controls
   - Implement session ownership (user-based access)
   - Provide session deletion capability

3. **Input Validation**
   - Validate all user inputs (notes, filters, search queries)
   - Sanitize data before database storage
   - Prevent SQL injection and XSS attacks

4. **Session Management**
   - Implement session timeouts
   - Require authentication for session access
   - Log all session activities for audit trails

## Deployment Considerations

### Database Migrations

New tables required:
- `merge_sessions`
- `change_reviews`

Migration script should:
1. Create tables with proper indexes
2. Set up foreign key constraints
3. Initialize any required seed data

### Configuration

New configuration parameters:
```python
# config.py additions
MERGE_ASSISTANT_UPLOAD_FOLDER = 'uploads/merge_assistant'
MERGE_ASSISTANT_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MERGE_ASSISTANT_SESSION_TIMEOUT = 24 * 60 * 60  # 24 hours
MERGE_ASSISTANT_ENABLE_PARALLEL_BLUEPRINTS = True
```

### Monitoring

Key metrics to monitor:
- Blueprint generation time
- Comparison processing time
- Session creation rate
- Active session count
- Error rates by phase
- User workflow completion rates

## Future Enhancements

### Phase 2 Enhancements

1. **Automated Merge Suggestions**
   - AI-powered merge recommendations
   - Automatic conflict resolution for simple cases
   - Learning from user merge decisions

2. **Collaborative Merge**
   - Multiple users working on same merge session
   - Comments and discussions on specific changes
   - Approval workflows

3. **Version Control Integration**
   - Export merge results to version control
   - Track merge history across multiple upgrades
   - Diff visualization improvements

4. **Advanced Analytics**
   - Merge complexity scoring
   - Time estimation improvements
   - Impact analysis for changes

5. **Export Capabilities**
   - Export merge instructions as documentation
   - Generate Appian import packages with merged changes
   - Create migration scripts

### Technical Debt Considerations

- Consider refactoring comparison logic to be more modular
- Evaluate performance with very large applications (> 5000 objects)
- Consider moving to asynchronous task processing (Celery) for long-running operations
- Evaluate need for caching layer (Redis) for frequently accessed data

