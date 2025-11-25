# Design Document

## Overview

This design document specifies the architecture and implementation approach for enhancing the Merge Assistant with pre-merge assessment report generation capabilities. The enhancement adds an Excel report generation feature accessible from the Session Summary page, implements configurable complexity and time estimation logic, restores the customer-only modifications metric, and adds interactive object type filtering in the breakdown section.

The design follows the existing OOP architecture, reuses established patterns from the codebase, and ensures zero impact on the existing merge workflow.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Session Summary Page                      │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │ Generate Report    │  │ Interactive Breakdown Cards  │  │
│  │ Button             │  │ with Object Grid             │  │
│  └────────┬───────────┘  └──────────────┬───────────────┘  │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────┐      ┌──────────────────────────┐
│ MergeAssistant        │      │ ThreeWayMergeService     │
│ Controller            │      │                          │
│ - export_report_excel │      │ - get_summary (enhanced) │
│ - get_objects_by_type │      │ - get_objects_by_type    │
└───────────┬───────────┘      └──────────┬───────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────┐      ┌──────────────────────────┐
│ MergeReportExcel      │      │ ComplexityCalculator     │
│ Service               │      │ Service                  │
│ - generate_report     │      │ - calculate_complexity   │
│ - format_excel        │      │ - calculate_time         │
└───────────┬───────────┘      └──────────┬───────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────┐      ┌──────────────────────────┐
│ ReportConfig          │      │ Database Models          │
│ - complexity_rules    │      │ - Change                 │
│ - time_estimates      │      │ - AppianObject           │
│ - column_definitions  │      │ - MergeSession           │
└───────────────────────┘      └──────────────────────────┘
```

### Component Interaction Flow

1. **Report Generation Flow**:
   - User clicks "Generate Report" button on Session Summary page
   - Controller receives request with session_id
   - Controller calls MergeReportExcelService.generate_report()
   - Service retrieves all changes from database via ThreeWayMergeService
   - Service calculates complexity and time for each change via ComplexityCalculatorService
   - Service formats data into Excel using openpyxl
   - Controller returns Excel file as download

2. **Breakdown Interaction Flow**:
   - User clicks object type card
   - JavaScript makes AJAX request to get_objects_by_type endpoint
   - Controller calls ThreeWayMergeService.get_objects_by_type()
   - Service queries database with filters and pagination
   - Controller returns JSON with objects and pagination info
   - JavaScript renders grid below cards with pagination controls

## Components and Interfaces

### 1. ReportConfig (Configuration Module)

**Purpose**: Centralized configuration for complexity and time calculation rules

**Location**: `config/report_config.py`

**Structure**:
```python
class ReportConfig:
    # Complexity thresholds for line-based objects
    LINE_BASED_LOW_MAX = 20
    LINE_BASED_MEDIUM_MAX = 60
    
    # Complexity thresholds for Process Models (node count)
    PROCESS_MODEL_LOW_MAX = 3
    PROCESS_MODEL_MEDIUM_MAX = 8
    
    # Time estimates (in minutes)
    TIME_LOW_COMPLEXITY = 20
    TIME_MEDIUM_COMPLEXITY = 40
    TIME_HIGH_COMPLEXITY = 100
    
    # Complexity labels
    COMPLEXITY_LOW = "Low"
    COMPLEXITY_MEDIUM = "Medium"
    COMPLEXITY_HIGH = "High"
    
    # Object types that use line-based complexity
    LINE_BASED_TYPES = ["Interface", "Expression Rule", "Record Type"]
    
    # Object types that are always low complexity
    ALWAYS_LOW_TYPES = ["Constant"]
    
    # Excel column definitions
    EXCEL_COLUMNS = [
        "S. No",
        "Category",
        "Object Name",
        "Object UUID",
        "Change Description",
        "Actual SAIL Change",
        "Complexity",
        "Estimated Time",
        "Comments"
    ]
    
    # SAIL code truncation limit
    SAIL_CODE_MAX_LENGTH = 500
```

### 2. ComplexityCalculatorService

**Purpose**: Calculate complexity and estimated time for changes

**Location**: `services/merge_assistant/complexity_calculator_service.py`

**Methods**:

```python
class ComplexityCalculatorService:
    def __init__(self, config: ReportConfig = None):
        """Initialize with optional custom config"""
        
    def calculate_complexity(
        self,
        change: Dict[str, Any],
        base_object: Optional[Dict],
        customer_object: Optional[Dict],
        vendor_object: Optional[Dict]
    ) -> str:
        """
        Calculate complexity for a change
        
        Returns: "Low", "Medium", or "High"
        """
        
    def calculate_estimated_time(self, complexity: str) -> int:
        """
        Calculate estimated time in minutes based on complexity
        
        Returns: Time in minutes
        """
        
    def format_time_display(self, minutes: int) -> str:
        """
        Format time for display
        
        Returns: "X minutes" or "Y hours"
        """
        
    def _calculate_line_based_complexity(
        self,
        base_sail: Optional[str],
        new_sail: Optional[str]
    ) -> str:
        """Calculate complexity based on SAIL code line differences"""
        
    def _calculate_process_model_complexity(
        self,
        base_pm_data: Optional[Dict],
        new_pm_data: Optional[Dict]
    ) -> str:
        """Calculate complexity based on node modifications"""
        
    def _count_modified_nodes(
        self,
        base_nodes: List[Dict],
        new_nodes: List[Dict]
    ) -> int:
        """Count number of modified nodes in process model"""
```

### 3. MergeReportExcelService

**Purpose**: Generate Excel reports with change details

**Location**: `services/merge_assistant/merge_report_excel_service.py`

**Methods**:

```python
class MergeReportExcelService:
    def __init__(
        self,
        complexity_calculator: ComplexityCalculatorService,
        config: ReportConfig = None
    ):
        """Initialize with dependencies"""
        
    def generate_report(
        self,
        session_id: int,
        merge_service: ThreeWayMergeService
    ) -> str:
        """
        Generate Excel report for a merge session
        
        Returns: Path to generated Excel file
        """
        
    def _build_report_data(
        self,
        changes: List[Dict[str, Any]],
        merge_service: ThreeWayMergeService
    ) -> List[Dict[str, Any]]:
        """Build enriched data for report"""
        
    def _format_excel_file(
        self,
        workbook: openpyxl.Workbook,
        report_data: List[Dict[str, Any]]
    ) -> None:
        """Apply formatting to Excel file"""
        
    def _generate_change_description(
        self,
        change: Dict[str, Any]
    ) -> str:
        """Generate human-readable change description"""
        
    def _extract_sail_changes(
        self,
        base_sail: Optional[str],
        new_sail: Optional[str]
    ) -> str:
        """Extract and format SAIL code changes"""
        
    def _extract_field_changes(
        self,
        base_fields: Optional[Dict],
        new_fields: Optional[Dict]
    ) -> str:
        """Extract and format field changes"""
```

### 4. ThreeWayMergeService (Enhanced)

**Purpose**: Add methods for object type filtering and enhanced summary

**Location**: `services/merge_assistant/three_way_merge_service.py`

**New Methods**:

```python
class ThreeWayMergeService:
    # ... existing methods ...
    
    def get_objects_by_type(
        self,
        session_id: int,
        object_type: str,
        classification: Optional[str] = None,
        page: int = 1,
        page_size: int = 5
    ) -> Dict[str, Any]:
        """
        Get objects filtered by type with pagination
        
        Returns: {
            'objects': List[Dict],
            'total': int,
            'page': int,
            'page_size': int,
            'total_pages': int
        }
        """
        
    def get_summary_with_complexity(
        self,
        session_id: int,
        complexity_calculator: ComplexityCalculatorService
    ) -> Dict[str, Any]:
        """
        Get summary with enhanced complexity and time calculations
        
        Returns: Enhanced summary dict with new metrics
        """
```

### 5. MergeAssistantController (Enhanced)

**Purpose**: Add endpoints for report generation and object filtering

**Location**: `controllers/merge_assistant_controller.py`

**New Methods**:

```python
class MergeAssistantController(BaseController):
    # ... existing methods ...
    
    def export_report_excel_handler(self, session_id: int):
        """Generate and download Excel report"""
        
    def get_objects_by_type_handler(self, session_id: int):
        """API endpoint for filtered object list"""
```

## Data Models

### Enhanced Change Model

No schema changes required. The existing `Change` model already contains all necessary fields:
- `object_uuid`, `object_name`, `object_type`
- `classification`, `change_type`
- Relationships to `base_object`, `customer_object`, `vendor_object`
- `display_order` for ordering

### Report Data Structure

```python
{
    "serial_number": int,
    "category": str,  # NO_CONFLICT, CONFLICT, etc.
    "object_name": str,
    "object_uuid": str,
    "change_description": str,
    "sail_changes": str,
    "complexity": str,  # Low, Medium, High
    "estimated_time": str,  # "20 minutes" or "2 hours"
    "comments": str  # Empty for now, reserved for future use
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Excel Report Structure Consistency
*For any* generated Excel report, the columns SHALL appear in the exact order: S. No, Category, Object Name, Object UUID, Change Description, Actual SAIL Change, Complexity, Estimated Time, Comments
**Validates: Requirements 1.3**

### Property 2: Report Generation Completeness
*For any* merge session with changes, generating a report SHALL produce an Excel file containing all changes from the session
**Validates: Requirements 1.2, 1.4**

### Property 3: Line-Based Complexity Classification
*For any* Interface, Expression Rule, or Record Type object, the complexity SHALL be Low when line changes are 1-20, Medium when 21-60, and High when greater than 60
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6**

### Property 4: Constant Complexity Invariant
*For any* Constant object, the complexity SHALL always be Low regardless of any other properties
**Validates: Requirements 2.5**

### Property 5: Process Model Complexity Classification
*For any* Process Model object, the complexity SHALL be Low when node modifications are 1-3, Medium when 4-8, and High when greater than 8
**Validates: Requirements 2.7, 2.8, 2.9**

### Property 6: Time Estimation Consistency
*For any* change, the estimated time SHALL be 20 minutes for Low complexity, 40 minutes for Medium complexity, and 100 minutes for High complexity
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 7: Time Format Display Rules
*For any* time value, it SHALL be formatted as minutes when less than 60, and as hours when 60 or greater
**Validates: Requirements 3.4, 3.5**

### Property 8: Customer-Only Count Accuracy
*For any* merge session, the customer-only modifications count SHALL equal the number of changes with classification "CUSTOMER_ONLY"
**Validates: Requirements 5.2**

### Property 9: Workflow Exclusion of Customer-Only
*For any* merge workflow, the changes list SHALL NOT contain any changes with classification "CUSTOMER_ONLY"
**Validates: Requirements 5.5**

### Property 10: Object Grid Field Completeness
*For any* object displayed in the breakdown grid, it SHALL include object name, UUID, classification, and complexity fields
**Validates: Requirements 6.2**

### Property 11: Pagination Consistency
*For any* object type with more than 5 objects, requesting page N SHALL return at most 5 objects starting at offset (N-1) * 5
**Validates: Requirements 6.3**

### Property 12: Summary Complexity Aggregation
*For any* merge session, the summary estimated complexity SHALL be calculated by aggregating individual change complexities according to the defined rules
**Validates: Requirements 7.1, 7.4**

### Property 13: Summary Time Summation
*For any* merge session, the summary estimated time SHALL equal the sum of estimated times for all changes in the workflow
**Validates: Requirements 7.2, 7.5**

### Property 14: SAIL Code Column Population
*For any* Interface or Expression Rule object in the report, the "Actual SAIL Change" column SHALL contain SAIL code differences if they exist
**Validates: Requirements 9.1, 9.2**

### Property 15: SAIL Code Truncation
*For any* SAIL code difference exceeding 500 characters, the displayed text SHALL be truncated to 500 characters with an ellipsis appended
**Validates: Requirements 9.4**

### Property 16: Non-SAIL Object Fallback
*For any* object without SAIL code, the "Actual SAIL Change" column SHALL contain a summary of field changes
**Validates: Requirements 9.3**

### Property 17: Change Description Presence
*For any* change in the report, the "Change Description" column SHALL contain a non-empty human-readable summary
**Validates: Requirements 10.1**

### Property 18: Conflict Description Completeness
*For any* change with classification "CONFLICT", the change description SHALL mention both vendor and customer modifications
**Validates: Requirements 10.5**

## Error Handling

### Report Generation Errors

1. **Session Not Found**
   - Validation: Check session exists before generation
   - Response: Return 404 with error message
   - Logging: Log session_id that was not found

2. **No Changes in Session**
   - Validation: Check session has changes
   - Response: Return 400 with message "No changes to report"
   - Logging: Log session_id with zero changes

3. **Excel Generation Failure**
   - Validation: Wrap openpyxl operations in try-catch
   - Response: Return 500 with error message
   - Logging: Log full exception stack trace
   - Cleanup: Delete partial Excel file if created

4. **Database Query Failure**
   - Validation: Wrap database queries in try-catch
   - Response: Return 500 with error message
   - Logging: Log query details and exception

### Configuration Errors

1. **Invalid Threshold Values**
   - Validation: Check thresholds are positive integers
   - Response: Log warning and use default values
   - Startup: Validate on application startup

2. **Missing Configuration**
   - Validation: Check all required config keys exist
   - Response: Log error and use default values
   - Startup: Validate on application startup

### Object Filtering Errors

1. **Invalid Object Type**
   - Validation: Check object_type against known types
   - Response: Return 400 with error message
   - Logging: Log invalid object_type value

2. **Invalid Pagination Parameters**
   - Validation: Check page and page_size are positive integers
   - Response: Return 400 with error message
   - Logging: Log invalid parameters

## Testing Strategy

### Unit Testing

**Complexity Calculator Tests**:
- Test line-based complexity calculation with various line counts
- Test process model complexity with various node counts
- Test constant complexity always returns Low
- Test time estimation for each complexity level
- Test time formatting for various minute values
- Test configuration loading and validation

**Report Generation Tests**:
- Test Excel file creation with mock data
- Test column ordering and headers
- Test SAIL code extraction and truncation
- Test field change extraction
- Test change description generation for each change type
- Test error handling for missing data

**Object Filtering Tests**:
- Test filtering by object type
- Test filtering by classification
- Test pagination with various page sizes
- Test empty result handling
- Test invalid parameter handling

### Property-Based Testing

The property-based testing library for Python is **Hypothesis**. All property tests SHALL run a minimum of 100 iterations.

**Property Test 1: Excel Column Order**
- **Feature: merge-assistant-report-generation, Property 1: Excel Report Structure Consistency**
- Generate: Random merge sessions with varying numbers of changes
- Test: Verify Excel columns are in correct order
- Iterations: 100

**Property Test 2: Report Completeness**
- **Feature: merge-assistant-report-generation, Property 2: Report Generation Completeness**
- Generate: Random merge sessions with 1-100 changes
- Test: Verify all changes appear in report
- Iterations: 100

**Property Test 3: Line-Based Complexity**
- **Feature: merge-assistant-report-generation, Property 3: Line-Based Complexity Classification**
- Generate: Random Interface/Expression Rule/Record Type objects with 1-200 line changes
- Test: Verify complexity matches thresholds
- Iterations: 100

**Property Test 4: Constant Complexity Invariant**
- **Feature: merge-assistant-report-generation, Property 4: Constant Complexity Invariant**
- Generate: Random Constant objects with varying properties
- Test: Verify complexity is always Low
- Iterations: 100

**Property Test 5: Process Model Complexity**
- **Feature: merge-assistant-report-generation, Property 5: Process Model Complexity Classification**
- Generate: Random Process Model objects with 1-20 node modifications
- Test: Verify complexity matches node count thresholds
- Iterations: 100

**Property Test 6: Time Estimation**
- **Feature: merge-assistant-report-generation, Property 6: Time Estimation Consistency**
- Generate: Random changes with Low/Medium/High complexity
- Test: Verify time matches complexity
- Iterations: 100

**Property Test 7: Time Formatting**
- **Feature: merge-assistant-report-generation, Property 7: Time Format Display Rules**
- Generate: Random time values from 1-500 minutes
- Test: Verify format is minutes (<60) or hours (>=60)
- Iterations: 100

**Property Test 8: Customer-Only Count**
- **Feature: merge-assistant-report-generation, Property 8: Customer-Only Count Accuracy**
- Generate: Random merge sessions with mixed classifications
- Test: Verify customer-only count matches CUSTOMER_ONLY classification count
- Iterations: 100

**Property Test 9: Workflow Exclusion**
- **Feature: merge-assistant-report-generation, Property 9: Workflow Exclusion of Customer-Only**
- Generate: Random merge sessions with customer-only changes
- Test: Verify workflow list contains no CUSTOMER_ONLY changes
- Iterations: 100

**Property Test 10: Grid Field Completeness**
- **Feature: merge-assistant-report-generation, Property 10: Object Grid Field Completeness**
- Generate: Random objects of various types
- Test: Verify all required fields present in grid data
- Iterations: 100

**Property Test 11: Pagination**
- **Feature: merge-assistant-report-generation, Property 11: Pagination Consistency**
- Generate: Random object lists with 6-50 objects, random page numbers
- Test: Verify page contains correct objects and count
- Iterations: 100

**Property Test 12: Summary Complexity**
- **Feature: merge-assistant-report-generation, Property 12: Summary Complexity Aggregation**
- Generate: Random merge sessions with mixed complexity changes
- Test: Verify summary complexity matches aggregation rules
- Iterations: 100

**Property Test 13: Summary Time**
- **Feature: merge-assistant-report-generation, Property 13: Summary Time Summation**
- Generate: Random merge sessions with various changes
- Test: Verify summary time equals sum of individual times
- Iterations: 100

**Property Test 14: SAIL Code Population**
- **Feature: merge-assistant-report-generation, Property 14: SAIL Code Column Population**
- Generate: Random Interface/Expression Rule objects with SAIL code
- Test: Verify SAIL changes appear in correct column
- Iterations: 100

**Property Test 15: SAIL Truncation**
- **Feature: merge-assistant-report-generation, Property 15: SAIL Code Truncation**
- Generate: Random SAIL code strings of 400-1000 characters
- Test: Verify strings >500 chars are truncated with ellipsis
- Iterations: 100

**Property Test 16: Non-SAIL Fallback**
- **Feature: merge-assistant-report-generation, Property 16: Non-SAIL Object Fallback**
- Generate: Random objects without SAIL code but with field changes
- Test: Verify field changes appear in SAIL column
- Iterations: 100

**Property Test 17: Description Presence**
- **Feature: merge-assistant-report-generation, Property 17: Change Description Presence**
- Generate: Random changes of all types
- Test: Verify description is non-empty
- Iterations: 100

**Property Test 18: Conflict Description**
- **Feature: merge-assistant-report-generation, Property 18: Conflict Description Completeness**
- Generate: Random conflict changes with vendor and customer modifications
- Test: Verify description mentions both sides
- Iterations: 100

### Integration Testing

**End-to-End Report Generation**:
- Create test session with known changes
- Generate report via controller
- Verify Excel file exists and is valid
- Verify all data is correct
- Clean up test files

**Breakdown Interaction**:
- Create test session with multiple object types
- Request objects by type via API
- Verify pagination works correctly
- Verify filtering works correctly

**Summary Metrics**:
- Create test session with known complexity distribution
- Request summary via API
- Verify metrics match expected values
- Verify customer-only metric is present

## Implementation Notes

1. **Reuse Existing Excel Service**: The `ExcelService` class already exists and handles Excel generation. The new `MergeReportExcelService` should follow the same patterns for consistency.

2. **Configuration Validation**: Add a validation method that runs on application startup to ensure all configuration values are valid. Log warnings for invalid values and use defaults.

3. **Complexity Calculation Caching**: Consider caching complexity calculations in the database to avoid recalculating on every report generation. Add a `complexity` and `estimated_time` column to the `Change` model.

4. **SAIL Code Diff Algorithm**: Reuse the existing SAIL code diff logic from the comparison service. The `enhanced_comparison_service.py` already has diff generation logic.

5. **UI Component Reuse**: The breakdown grid should reuse the existing table/grid components from other pages. Follow the same styling patterns as the change detail page.

6. **Async Report Generation**: For large sessions (>1000 changes), consider making report generation asynchronous with a progress indicator. This can be added in a future iteration.

7. **Excel Styling**: Follow the same styling patterns as the existing `ExcelService` - use the purple theme color (#8B5CF6) for headers and maintain consistent formatting.

8. **Error Messages**: Use the existing flash message system for user-facing errors. Follow the same patterns as other controllers.

9. **Logging**: Use the existing `create_merge_session_logger` for all logging. Log report generation start, completion, and any errors.

10. **Database Queries**: Use the existing optimized queries from `ThreeWayMergeService`. The service already has efficient JOIN queries and pagination support.
