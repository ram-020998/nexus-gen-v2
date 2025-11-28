# Implementation Plan

- [x] 1. Create configuration module for complexity and time rules
  - Create `config/report_config.py` with all thresholds, labels, and column definitions
  - Add validation method to check configuration values on startup
  - Add default values as fallback for invalid configuration
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 1.1 Write property test for configuration validation
  - **Property 4: Constant Complexity Invariant** (validates config is used correctly)
  - **Validates: Requirements 2.5**

- [x] 2. Implement ComplexityCalculatorService
  - Create `services/merge_assistant/complexity_calculator_service.py`
  - Implement `calculate_complexity()` method with object type routing
  - Implement `_calculate_line_based_complexity()` for Interface/Expression Rule/Record Type
  - Implement `_calculate_process_model_complexity()` for Process Models
  - Implement `calculate_estimated_time()` method
  - Implement `format_time_display()` method
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 2.1 Write property test for line-based complexity calculation
  - **Property 3: Line-Based Complexity Classification**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6**

- [ ]* 2.2 Write property test for constant complexity invariant
  - **Property 4: Constant Complexity Invariant**
  - **Validates: Requirements 2.5**

- [ ]* 2.3 Write property test for process model complexity
  - **Property 5: Process Model Complexity Classification**
  - **Validates: Requirements 2.7, 2.8, 2.9**

- [ ]* 2.4 Write property test for time estimation
  - **Property 6: Time Estimation Consistency**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ]* 2.5 Write property test for time formatting
  - **Property 7: Time Format Display Rules**
  - **Validates: Requirements 3.4, 3.5**

- [x] 3. Implement MergeReportExcelService
  - Create `services/merge_assistant/merge_report_excel_service.py`
  - Implement `generate_report()` method to orchestrate report generation
  - Implement `_build_report_data()` to enrich changes with complexity and descriptions
  - Implement `_format_excel_file()` to create Excel with proper styling
  - Implement `_generate_change_description()` for human-readable descriptions
  - Implement `_extract_sail_changes()` with truncation logic
  - Implement `_extract_field_changes()` for non-SAIL objects
  - Reuse styling patterns from existing `ExcelService`
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 3.1 Write property test for Excel structure consistency
  - **Property 1: Excel Report Structure Consistency**
  - **Validates: Requirements 1.3**

- [ ]* 3.2 Write property test for report completeness
  - **Property 2: Report Generation Completeness**
  - **Validates: Requirements 1.2, 1.4**

- [ ]* 3.3 Write property test for SAIL code column population
  - **Property 14: SAIL Code Column Population**
  - **Validates: Requirements 9.1, 9.2**

- [ ]* 3.4 Write property test for SAIL code truncation
  - **Property 15: SAIL Code Truncation**
  - **Validates: Requirements 9.4**

- [ ]* 3.5 Write property test for non-SAIL object fallback
  - **Property 16: Non-SAIL Object Fallback**
  - **Validates: Requirements 9.3**

- [ ]* 3.6 Write property test for change description presence
  - **Property 17: Change Description Presence**
  - **Validates: Requirements 10.1**

- [ ]* 3.7 Write property test for conflict description completeness
  - **Property 18: Conflict Description Completeness**
  - **Validates: Requirements 10.5**

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Enhance ThreeWayMergeService with object filtering
  - Add `get_objects_by_type()` method to filter changes by object type
  - Implement pagination logic with page size of 5
  - Add optional classification filter parameter
  - Reuse existing database query patterns with JOIN optimization
  - Add `get_summary_with_complexity()` method to include complexity calculations
  - _Requirements: 6.1, 6.2, 6.3, 7.1, 7.2, 7.4, 7.5_

- [ ]* 5.1 Write property test for object grid field completeness
  - **Property 10: Object Grid Field Completeness**
  - **Validates: Requirements 6.2**

- [ ]* 5.2 Write property test for pagination consistency
  - **Property 11: Pagination Consistency**
  - **Validates: Requirements 6.3**

- [ ]* 5.3 Write property test for summary complexity aggregation
  - **Property 12: Summary Complexity Aggregation**
  - **Validates: Requirements 7.1, 7.4**

- [ ]* 5.4 Write property test for summary time summation
  - **Property 13: Summary Time Summation**
  - **Validates: Requirements 7.2, 7.5**

- [x] 6. Add controller endpoints for report generation and object filtering
  - Add `export_report_excel_handler()` method to `MergeAssistantController`
  - Add route `/merge-assistant/session/<int:session_id>/export/excel-report`
  - Add `get_objects_by_type_handler()` method for AJAX requests
  - Add route `/merge-assistant/api/session/<int:session_id>/objects/<object_type>`
  - Implement error handling for session not found, no changes, and generation failures
  - Follow existing controller patterns for error responses and logging
  - _Requirements: 1.1, 1.2, 1.4, 1.5, 6.1, 8.6, 8.7, 8.8_

- [ ]* 6.1 Write integration test for report generation endpoint
  - Test end-to-end report generation via controller
  - Verify Excel file is created and downloadable
  - Test error handling for invalid session

- [ ]* 6.2 Write integration test for object filtering endpoint
  - Test object filtering by type via API
  - Verify pagination works correctly
  - Test error handling for invalid parameters

- [x] 7. Update Session Summary page UI with Generate Report button
  - Add "Generate Report" button at top of summary page
  - Position button prominently near session information
  - Add loading indicator during report generation
  - Add error message display for generation failures
  - Follow existing UI styling patterns
  - _Requirements: 1.1, 1.5_

- [x] 8. Restore customer-only modifications metric to summary page
  - Update `get_summary()` method to include customer-only count in statistics
  - Add customer-only metric card to summary page template
  - Add explanatory text that customer-only changes are not in workflow
  - Ensure customer-only tab appears in breakdown section
  - Verify customer-only changes are excluded from workflow (existing behavior)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 8.1 Write property test for customer-only count accuracy
  - **Property 8: Customer-Only Count Accuracy**
  - **Validates: Requirements 5.2**

- [ ]* 8.2 Write property test for workflow exclusion
  - **Property 9: Workflow Exclusion of Customer-Only**
  - **Validates: Requirements 5.5**

- [x] 9. Implement interactive breakdown section with object grid
  - Add click handlers to object type cards in breakdown section
  - Create AJAX request to fetch objects by type
  - Render grid below cards with object name, UUID, classification, complexity
  - Implement pagination controls with page size of 5
  - Add close icon to hide grid
  - Add logic to replace grid when different card is clicked
  - Reuse existing grid/table styling components
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 10. Update summary metrics positioning and calculations
  - Move Estimated Complexity and Estimated Time metrics to top of summary section
  - Update metric calculation to use new complexity rules
  - Update metric calculation to use new time estimation rules
  - Ensure metrics aggregate correctly across all workflow changes
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 11. Add JavaScript for breakdown interaction
  - Create JavaScript module for breakdown card interactions
  - Implement click handlers for object type cards
  - Implement AJAX calls to object filtering endpoint
  - Implement grid rendering with pagination
  - Implement close button functionality
  - Add loading indicators during data fetch
  - Add error handling for failed requests
  - _Requirements: 6.1, 6.4, 6.5, 6.6_

- [ ] 12. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 13. Write end-to-end integration test
  - Create test session with known changes of various types
  - Generate report and verify all data is correct
  - Test breakdown interaction with object filtering
  - Test summary metrics match expected values
  - Verify customer-only metric is present and accurate
  - Verify existing merge workflow is not affected
  - _Requirements: 8.6_
