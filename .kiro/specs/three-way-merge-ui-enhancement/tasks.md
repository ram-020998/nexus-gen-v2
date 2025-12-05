# Implementation Plan

- [x] 1. Database schema updates and migrations
  - [x] 1.1 Create migration script to add new columns to changes table (status, notes, reviewed_at, reviewed_by)
    - Add status column with default 'pending'
    - Add notes TEXT column
    - Add reviewed_at TIMESTAMP column
    - Add reviewed_by VARCHAR(255) column
    - _Requirements: 3.5, 3.6, 3.7_
  
  - [x] 1.2 Create migration script to add new columns to merge_sessions table (reviewed_count, skipped_count, estimated_complexity, estimated_time_hours)
    - Add reviewed_count INTEGER with default 0
    - Add skipped_count INTEGER with default 0
    - Add estimated_complexity VARCHAR(20)
    - Add estimated_time_hours FLOAT
    - _Requirements: 3.5, 3.6, 4.3, 4.4, 5.5_
  
  - [x] 1.3 Create indexes for performance optimization
    - Create index on changes(session_id, status)
    - Create index on changes(reviewed_at)
    - _Requirements: Performance optimization_
  
  - [x] 1.4 Update models.py with new fields
    - Update Change model with new fields
    - Update MergeSession model with new fields
    - Update to_dict() methods
    - _Requirements: 3.5, 3.6, 3.7, 4.3, 4.4, 5.5_

- [x] 2. Implement Change Navigation Service
  - [x] 2.1 Create ChangeNavigationService class in services/change_navigation_service.py
    - Implement get_change_detail() method
    - Implement get_next_change() method
    - Implement get_previous_change() method
    - Implement get_change_position() method
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [ ]* 2.2 Write property test for change position calculation
    - **Property 1: Change position display accuracy**
    - **Validates: Requirements 1.2**
  
  - [ ]* 2.3 Write property test for navigation button presence
    - **Property 2: Navigation buttons presence**
    - **Validates: Requirements 1.3**
  
  - [ ]* 2.4 Write property test for progress percentage calculation
    - **Property 3: Progress percentage calculation**
    - **Validates: Requirements 1.6**
  
  - [x] 2.5 Implement get_object_versions() method to retrieve versions from all three packages
    - Query ObjectVersion table for base, customized, and new_vendor packages
    - Return dict with version data for each package
    - _Requirements: 2.1_

- [x] 3. Implement Change Action Service
  - [x] 3.1 Create ChangeActionService class in services/change_action_service.py
    - Implement mark_as_reviewed() method
    - Implement skip_change() method
    - Implement save_notes() method
    - Implement undo_action() method
    - _Requirements: 3.5, 3.6, 3.7_
  
  - [ ]* 3.2 Write property test for mark as reviewed state transition
    - **Property 10: Mark as reviewed state transition**
    - **Validates: Requirements 3.5**
  
  - [ ]* 3.3 Write property test for skip state transition
    - **Property 11: Skip state transition**
    - **Validates: Requirements 3.6**
  
  - [ ]* 3.4 Write property test for notes persistence
    - **Property 12: Notes persistence**
    - **Validates: Requirements 3.7**

- [x] 4. Implement Session Statistics Service
  - [x] 4.1 Create SessionStatisticsService class in services/session_statistics_service.py
    - Implement calculate_complexity() method
    - Implement estimate_review_time() method
    - Implement get_progress_metrics() method
    - _Requirements: 5.5, 4.3, 4.4_
  
  - [ ]* 4.2 Write property test for summary statistics accuracy
    - **Property 14: Summary statistics accuracy**
    - **Validates: Requirements 5.2, 5.3**
  
  - [ ]* 4.3 Write property test for object type breakdown accuracy
    - **Property 15: Object type breakdown accuracy**
    - **Validates: Requirements 5.4**
  
  - [x] 4.4 Implement caching for statistics (5-minute cache)
    - Use Flask-Caching or simple in-memory cache
    - Invalidate cache on change updates
    - _Requirements: Performance optimization_

- [x] 5. Implement Report Generation Service
  - [x] 5.1 Create ReportGenerationService class in services/report_generation_service.py
    - Implement generate_report() method
    - Implement _generate_pdf_report() method using ReportLab
    - Implement _generate_docx_report() method using python-docx
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 5.2 Write property test for report generation completeness
    - **Property 23: Report generation completeness**
    - **Validates: Requirements 8.2, 8.3, 8.4**
  
  - [ ]* 5.3 Write property test for report format validity
    - **Property 24: Report format validity**
    - **Validates: Requirements 8.5**
  
  - [x] 5.4 Add report caching (1-hour cache)
    - Cache generated reports by session_id and format
    - Store in outputs/reports directory
    - _Requirements: Performance optimization_

- [x] 6. Enhance Merge Assistant Controller with new routes
  - [x] 6.1 Add change detail route: GET /<reference_id>/changes/<change_id>
    - Use ChangeNavigationService to get change details
    - Render change detail template
    - Handle 404 for non-existent changes
    - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 6.2 Add change action routes: POST /<reference_id>/changes/<change_id>/review, /skip, /notes
    - Use ChangeActionService for actions
    - Return JSON responses
    - Handle validation errors
    - _Requirements: 3.5, 3.6, 3.7_
  
  - [x] 6.3 Add report generation route: POST /<reference_id>/report
    - Use ReportGenerationService
    - Return file download response
    - Handle generation errors
    - _Requirements: 8.1, 8.2_
  
  - [x] 6.4 Add object type detail route: GET /<reference_id>/objects/<object_type>
    - Query changes filtered by object type
    - Return JSON with object details
    - _Requirements: 5.4_

- [x] 7. Create change detail template
  - [x] 7.1 Create templates/merge/change_detail.html
    - Display change position and progress bar
    - Display object information (name, type, UUID, description)
    - Display classification badge
    - Display vendor and customer change types
    - Display SAIL code if available
    - Include Previous/Next navigation buttons
    - Include action buttons (Mark as Reviewed, Skip, Save Notes)
    - Include notes textarea
    - Include session info panel
    - _Requirements: 1.2, 1.3, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 7.2 Write property test for change detail template rendering
    - **Property 4-9: SAIL code, classification, change types, metadata, action buttons, notes textarea display**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4**
  
  - [x] 7.3 Add JavaScript for action buttons
    - Handle Mark as Reviewed button click
    - Handle Skip button click
    - Handle Save Notes button click
    - Show loading states
    - Show success/error messages
    - Update session info panel after actions
    - _Requirements: 3.5, 3.6, 3.7_
  
  - [x] 7.4 Add edge case handling for first/last change
    - Disable Previous button on first change
    - Disable Next button on last change
    - _Requirements: 1.4, 1.5_

- [x] 8. Enhance summary template
  - [x] 8.1 Update templates/merge/summary.html with new features
    - Add "What's in the Merge Workflow?" explanation section
    - Add estimated complexity display
    - Add estimated time display
    - Update statistics cards with proper counts
    - _Requirements: 5.5, 5.7_
  
  - [x] 8.2 Add expandable object type breakdown with grid
    - Make object type items clickable
    - Add collapse/expand functionality
    - Display grid with columns: Object Name, UUID, Classification, Complexity
    - Fetch object details via AJAX when expanded
    - _Requirements: 5.4_
  
  - [ ]* 8.3 Write property test for object type expansion
    - **Property 15a: Object type expansion displays objects**
    - **Validates: Requirements 5.4**
  
  - [x] 8.4 Add Generate Report button
    - Add button to header
    - Handle click to trigger report generation
    - Show loading indicator
    - Download file when ready
    - _Requirements: 8.1_
  
  - [x] 8.5 Update "Start Merge Workflow" button to navigate to first change
    - Change link to point to first change detail page instead of workflow list
    - _Requirements: 5.6_

- [x] 9. Enhance sessions template
  - [x] 9.1 Update templates/merge/sessions.html with filtering and search
    - Add status filter buttons (All, Processing, Ready, In Progress, Completed, Error)
    - Add search input field
    - Add sort dropdown
    - Add Clear Filters button
    - _Requirements: 6.1, 6.2, 6.5, 6.7_
  
  - [x] 9.2 Add JavaScript for filtering and search
    - Implement status filter logic
    - Implement search filter logic
    - Implement sort logic
    - Implement clear filters logic
    - _Requirements: 6.3, 6.4, 6.6_
  
  - [ ]* 9.3 Write property test for status filter correctness
    - **Property 17: Status filter correctness**
    - **Validates: Requirements 6.3**
  
  - [ ]* 9.4 Write property test for search filter correctness
    - **Property 18: Search filter correctness**
    - **Validates: Requirements 6.4**
  
  - [ ]* 9.5 Write property test for sort order correctness
    - **Property 19: Sort order correctness**
    - **Validates: Requirements 6.6**
  
  - [x] 9.6 Update session cards with progress display
    - Display progress as "X / Y (Z%)"
    - Update action buttons based on status
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ]* 9.7 Write property test for session card completeness
    - **Property 20-22: Session card completeness, progress format, action buttons**
    - **Validates: Requirements 7.1, 7.2, 7.3**

- [x] 10. Enhance workflow template
  - [x] 10.1 Update templates/merge/workflow.html with jump navigation
    - Add "Jump to Change" dropdown
    - Populate with all changes
    - Handle selection to navigate
    - _Requirements: 9.1, 9.2_
  
  - [ ]* 10.2 Write property test for jump navigation correctness
    - **Property 25: Jump navigation correctness**
    - **Validates: Requirements 9.2**
  
  - [x] 10.3 Add classification grouping
    - Group changes by classification
    - Add visual indicators for groups
    - _Requirements: 9.3_
  
  - [ ]* 10.4 Write property test for workflow grouping correctness
    - **Property 26: Workflow grouping correctness**
    - **Validates: Requirements 9.3**
  
  - [x] 10.5 Add classification filter buttons
    - Add filter buttons for each classification
    - Implement filter logic
    - _Requirements: 9.4_
  
  - [ ]* 10.6 Write property test for classification filter correctness
    - **Property 27: Classification filter correctness**
    - **Validates: Requirements 9.4**

- [x] 11. Add error handling and 404 pages
  - [x] 11.1 Create templates/errors/404.html
    - Display user-friendly 404 message
    - Add navigation back to sessions or workflow
    - _Requirements: 10.1, 10.2_
  
  - [x] 11.2 Add error handlers to merge_assistant_controller.py
    - Handle session not found (404)
    - Handle change not found (404)
    - Handle database errors (500)
    - Handle file upload errors (400)
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  
  
  - [ ]* 11.4 Write property test for duplicate submission prevention
    - **Property 28: Duplicate submission prevention**
    - **Validates: Requirements 10.5**

- [x] 12. Add CSS styling and responsive design
  - [x] 12.1 Update static/css/docflow.css with new styles
    - Style change detail page
    - Style expandable object type grids
    - Style filter and search controls
    - Style progress indicators
    - Style action buttons
    - Ensure responsive design for mobile
    - _Requirements: All UI requirements_
  
  - [x] 12.2 Add loading indicators and animations
    - Add spinner for report generation
    - Add spinner for action buttons
    - Add smooth transitions for expand/collapse
    - _Requirements: User experience_

- [ ] 13. Integration testing and bug fixes
  - [ ] 13.1 Test complete workflow end-to-end
    - Create session → View summary → Navigate changes → Mark reviewed → Generate report
    - Test with real test packages
    - Verify all features work together
    - _Requirements: All requirements_
  
  - [ ] 13.2 Test error scenarios
    - Test 404 pages
    - Test validation errors
    - Test database errors
    - Test file upload errors
    - _Requirements: 10.1, 10.2, 10.3, 10.4_
  
  - [ ] 13.3 Test browser compatibility
    - Test in Chrome, Firefox, Safari, Edge
    - Test responsive design on mobile
    - Test accessibility with screen readers
    - _Requirements: User experience_
  
  - [ ] 13.4 Fix any bugs discovered during testing
    - Document bugs
    - Prioritize fixes
    - Implement fixes
    - Retest
    - _Requirements: All requirements_

- [ ] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Documentation and deployment
  - [ ] 15.1 Update README.md with new features
    - Document change navigation
    - Document action buttons
    - Document report generation
    - Document filtering and search
    - _Requirements: Documentation_
  
  - [ ] 15.2 Update API documentation
    - Document new routes
    - Document request/response formats
    - Document error codes
    - _Requirements: Documentation_
  
  - [ ] 15.3 Create deployment checklist
    - Run migrations
    - Update dependencies
    - Test in staging environment
    - Deploy to production
    - _Requirements: Deployment_
