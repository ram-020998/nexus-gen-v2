# Implementation Plan

- [x] 1. Set up database models and migrations
  - Create MergeSession and ChangeReview database models with all required fields
  - Create database migration script to add new tables with proper indexes and foreign keys
  - Add configuration parameters for merge assistant (upload folder, file size limits, session timeout)
  - _Requirements: 16.1, 16.2, 16.3_

- [x] 1.1 Write property test for session metadata persistence
  - **Property 33: Session metadata persistence**
  - **Validates: Requirements 16.1**

- [x] 1.2 Write property test for blueprint persistence
  - **Property 34: Blueprint persistence**
  - **Validates: Requirements 16.2**

- [x] 2. Implement BlueprintGenerationService
  - Create BlueprintGenerationService class that wraps existing AppianAnalyzer
  - Implement generate_blueprint() method for single package analysis
  - Implement generate_all_blueprints() method with parallel processing for A, B, C packages
  - Add error handling for blueprint generation failures
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2.1 Write property test for blueprint generation completeness
  - **Property 4: Blueprint generation completeness**
  - **Validates: Requirements 2.1, 2.2**

- [x] 2.2 Write property test for blueprint failure handling
  - **Property 5: Blueprint failure handling**
  - **Validates: Requirements 2.3**

- [x] 3. Implement ThreeWayComparisonService
  - Create ThreeWayComparisonService class using EnhancedVersionComparator
  - Implement compare_vendor_changes() method for A→C comparison
  - Implement compare_customer_changes() method for A→B comparison
  - Implement perform_three_way_comparison() method that orchestrates both comparisons
  - Ensure change details include SAIL code, fields, properties, and business logic differences
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4_

- [x] 3.1 Write property test for vendor change identification
  - **Property 7: Vendor change identification**
  - **Validates: Requirements 3.2**

- [x] 3.2 Write property test for change detail capture
  - **Property 8: Change detail capture**
  - **Validates: Requirements 3.4, 4.4**

- [x] 3.3 Write property test for customer change identification
  - **Property 9: Customer change identification**
  - **Validates: Requirements 4.2**

- [x] 4. Implement ChangeClassificationService
  - Create ChangeClassificationService class
  - Implement classify_changes() method that categorizes all objects into NO_CONFLICT, CONFLICT, CUSTOMER_ONLY, or REMOVED_BUT_CUSTOMIZED
  - Implement _is_conflict() helper method to detect conflicting changes
  - Implement _classify_single_object() helper method for individual object classification
  - Ensure each object receives exactly one classification
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 4.1 Write property test for conflict detection accuracy
  - **Property 10: Conflict detection accuracy**
  - **Validates: Requirements 5.1**

- [x] 4.2 Write property test for classification completeness
  - **Property 11: Classification completeness**
  - **Validates: Requirements 5.2**

- [x] 5. Implement DependencyAnalysisService
  - Create DependencyAnalysisService class
  - Implement build_dependency_graph() method to extract object dependencies from blueprints
  - Implement topological_sort() method with circular dependency detection and cycle breaking
  - Implement order_changes() method that orders changes: NO_CONFLICT first (grouped by type), then CONFLICT (by dependencies), then REMOVED_BUT_CUSTOMIZED
  - Implement get_dependencies() method to retrieve parent and child dependencies for an object
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 14.1, 14.2_

- [x] 5.1 Write property test for change ordering correctness
  - **Property 14: Change ordering correctness**
  - **Validates: Requirements 7.1**

- [x] 5.2 Write property test for object type grouping
  - **Property 15: Object type grouping**
  - **Validates: Requirements 7.2**

- [x] 5.3 Write property test for dependency ordering
  - **Property 16: Dependency ordering**
  - **Validates: Requirements 7.3**

- [x] 5.4 Write property test for dependency display completeness
  - **Property 29: Dependency display completeness**
  - **Validates: Requirements 14.1, 14.2**

- [x] 6. Implement MergeGuidanceService
  - Create MergeGuidanceService class
  - Implement generate_guidance() method that produces merge strategies and recommendations for each change
  - Implement _identify_vendor_additions() method to find new code/features added by vendor
  - Implement _identify_vendor_modifications() method to find vendor modifications to existing code
  - Implement _identify_conflict_sections() method to find sections modified by both parties
  - Implement _generate_merge_strategy() method to determine appropriate merge approach
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 6.1 Write property test for vendor addition identification
  - **Property 31: Vendor addition identification**
  - **Validates: Requirements 15.1**

- [x] 6.2 Write property test for vendor modification identification
  - **Property 32: Vendor modification identification**
  - **Validates: Requirements 15.2**

- [x] 6.3 Write property test for merge strategy recommendations
  - **Property 36: Merge strategy recommendations**
  - **Validates: Requirements 17.1**

- [x] 7. Implement ThreeWayMergeService (orchestration)
  - Create ThreeWayMergeService class that orchestrates the entire workflow
  - Implement create_session() method that coordinates blueprint generation, comparison, classification, ordering, and guidance
  - Implement get_session() method to retrieve session by ID
  - Implement get_summary() method to generate merge summary with statistics
  - Implement get_ordered_changes() method to retrieve smart-ordered change list
  - Implement update_progress() method to track user review actions
  - Implement generate_report() method to create final merge report
  - Add comprehensive error handling for each phase
  - _Requirements: 1.4, 2.4, 3.5, 4.5, 6.1, 6.2, 6.3, 6.5, 10.1, 10.2, 10.3, 10.4, 10.5, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 7.1 Write property test for workflow progression after blueprints
  - **Property 6: Workflow progression after blueprints**
  - **Validates: Requirements 2.4**

- [x] 7.2 Write property test for summary statistics accuracy
  - **Property 12: Summary statistics accuracy**
  - **Validates: Requirements 6.2**

- [x] 7.3 Write property test for breakdown accuracy
  - **Property 13: Breakdown accuracy**
  - **Validates: Requirements 6.3**

- [x] 7.4 Write property test for progress tracking accuracy
  - **Property 22: Progress tracking accuracy**
  - **Validates: Requirements 10.2, 10.3**

- [x] 7.5 Write property test for session persistence round-trip
  - **Property 23: Session persistence round-trip**
  - **Validates: Requirements 10.5**

- [x] 7.6 Write property test for report generation completeness
  - **Property 24: Report generation completeness**
  - **Validates: Requirements 12.2**

- [x] 7.7 Write property test for report detail completeness
  - **Property 25: Report detail completeness**
  - **Validates: Requirements 12.3**

- [x] 7.8 Write property test for real-time state updates
  - **Property 35: Real-time state updates**
  - **Validates: Requirements 16.4, 16.5**

- [x] 8. Implement package validation utilities
  - Create package validation functions to verify ZIP file structure and Appian package validity
  - Implement validation for required Appian files (application.properties, etc.)
  - Add file size limit checks
  - Implement clear error message generation for validation failures
  - _Requirements: 1.2, 1.5_

- [x] 8.1 Write property test for package validation correctness
  - **Property 1: Package validation correctness**
  - **Validates: Requirements 1.2**

- [x] 8.2 Write property test for error message clarity
  - **Property 3: Error message clarity**
  - **Validates: Requirements 1.5**

- [x] 9. Implement merge assistant controller routes
  - Create merge_assistant_controller.py with all required routes
  - Implement GET /merge-assistant route for upload page
  - Implement POST /merge-assistant/upload route for three-package upload and session creation
  - Implement GET /merge-assistant/session/<id>/summary route for merge summary display
  - Implement GET /merge-assistant/session/<id>/workflow route to start guided workflow
  - Implement GET /merge-assistant/session/<id>/change/<index> route for change detail view
  - Implement POST /merge-assistant/session/<id>/change/<index>/review route for review actions
  - Implement GET /merge-assistant/session/<id>/report route for report generation
  - Implement GET /merge-assistant/sessions route to list all sessions
  - Add proper error handling and user-friendly error messages
  - _Requirements: 1.1, 1.3, 1.4, 8.6, 8.7, 8.8, 11.4_

- [x] 9.1 Write property test for session creation atomicity
  - **Property 2: Session creation atomicity**
  - **Validates: Requirements 1.4**

- [x] 10. Create upload page template
  - Create templates/merge_assistant/upload.html
  - Implement three distinct upload sections for Base Package (A), Customized Package (B), and New Vendor Package (C)
  - Add file upload controls with drag-and-drop support
  - Implement "Start Analysis" button that enables only when all three packages are uploaded
  - Add progress indicators for upload and analysis
  - Display validation errors clearly indicating which package failed and why
  - _Requirements: 1.1, 1.3, 1.5, 2.5_

- [x] 11. Create merge summary page template
  - Create templates/merge_assistant/summary.html
  - Display session information (reference ID, package names, timestamps)
  - Show statistics for each classification category (NO_CONFLICT, CONFLICT, CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED)
  - Display breakdown by object type for each category
  - Show estimated complexity and time
  - Add "Start Merge Workflow" button to begin guided process
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 12. Create change detail view template
  - Create templates/merge_assistant/change_detail.html
  - Display object name, type, and classification category
  - For NO_CONFLICT changes: show vendor changes with guidance
  - For CONFLICT changes: display three-way diff (Base A, Customer B, Vendor C) side-by-side
  - Highlight vendor additions that need incorporation into customer version
  - Display "Suggested Merge Strategy" section with recommendations
  - Show dependency information (parents and children) with review status
  - Add action buttons: "Mark as Reviewed", "Skip", "Add Notes"
  - Implement "Previous" and "Next" navigation buttons
  - Add progress indicator showing current position
  - Provide sidebar/dropdown to jump to specific changes
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.1, 11.1, 11.2, 11.3, 11.5, 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 12.1 Write property test for change detail display completeness
  - **Property 17: Change detail display completeness**
  - **Validates: Requirements 8.1**

- [x] 12.2 Write property test for three-way diff display
  - **Property 18: Three-way diff display**
  - **Validates: Requirements 8.3**

- [x] 12.3 Write property test for vendor change highlighting
  - **Property 19: Vendor change highlighting**
  - **Validates: Requirements 8.4**

- [x] 12.4 Write property test for SAIL code formatting
  - **Property 20: SAIL code formatting**
  - **Validates: Requirements 9.3**

- [x] 12.5 Write property test for merge strategy provision
  - **Property 21: Merge strategy provision**
  - **Validates: Requirements 9.6**

- [x] 12.6 Write property test for dependency status indication
  - **Property 30: Dependency status indication**
  - **Validates: Requirements 14.3**

- [x] 13. Create merge report page template
  - Create templates/merge_assistant/report.html
  - Display summary statistics (total changes, reviewed, skipped, conflicts)
  - List all changes grouped by category and object type
  - Show classification, review status, and user notes for each change
  - Provide download options (PDF, JSON)
  - Add link to return to session or start new merge
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 14. Create session list page template
  - Create templates/merge_assistant/sessions.html
  - Display table of all merge sessions with reference ID, package names, status, and timestamps
  - Add filters for status (processing, ready, in_progress, completed, error)
  - Provide links to resume in-progress sessions or view completed reports
  - Add pagination for large session lists
  - _Requirements: General UI requirement_

- [x] 15. Implement filtering and search functionality
  - Add filter_changes() method to ThreeWayMergeService
  - Implement filtering by classification category, object type, and review status
  - Implement search by object name
  - Ensure smart ordering is maintained within filtered results
  - Add filter and search UI controls to change list views
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 15.1 Write property test for filter correctness
  - **Property 26: Filter correctness**
  - **Validates: Requirements 13.2**

- [x] 15.2 Write property test for search functionality
  - **Property 27: Search functionality**
  - **Validates: Requirements 13.4**

- [x] 15.3 Write property test for ordering preservation after filtering
  - **Property 28: Ordering preservation after filtering**
  - **Validates: Requirements 13.5**

- [x] 16. Add navigation and routing
  - Update app.py to register merge assistant controller routes
  - Add navigation links to main application menu
  - Implement breadcrumb navigation for merge workflow
  - Add session state management for navigation
  - _Requirements: General navigation requirement_

- [x] 17. Implement report export functionality
  - Create report generation utilities for PDF and JSON formats
  - Implement PDF export with proper formatting and styling
  - Implement JSON export with complete session data
  - Add download endpoints to controller
  - _Requirements: 12.5_

- [x] 18. Add logging and monitoring
  - Integrate with existing logging system (services/appian_analyzer/logger.py)
  - Add request-specific logging for merge sessions
  - Log stage transitions (Upload, Blueprint Generation, Comparison, Classification, Workflow)
  - Log metrics (processing times, change counts, user actions)
  - Add error logging with full context
  - _Requirements: General monitoring requirement_

- [x] 19. Create test fixtures
  - Create test Appian packages (small, medium, large) for A, B, C scenarios
  - Create packages with known differences for comparison testing
  - Create packages with circular dependencies
  - Create malformed packages for error testing
  - Store in tests/fixtures/three_way_merge/ directory
  - _Requirements: Testing requirement_

- [x] 20. Write integration tests
  - Test full merge workflow end-to-end (upload → blueprints → comparison → classification → workflow → report)
  - Test session persistence and restoration
  - Test error recovery scenarios
  - Test concurrent session handling
  - _Requirements: Testing requirement_

- [x] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Performance optimization
  - Implement parallel blueprint generation using threading
  - Add caching for blueprint object lookups and dependency graphs
  - Add database indexes for merge_sessions.reference_id and change_reviews.session_id
  - Implement lazy loading for change details
  - Add pagination for large change lists
  - _Requirements: Performance requirement_

- [ ] 23. Security hardening
  - Implement ZIP file validation and size limits
  - Add file extraction security (restricted permissions, temporary directories)
  - Implement session ownership and access controls
  - Add input sanitization for user notes and search queries
  - Implement session timeouts
  - _Requirements: Security requirement_

- [ ] 24. Documentation
  - Create user guide for merge assistant workflow
  - Document API endpoints and request/response formats
  - Add inline code documentation for all services
  - Create troubleshooting guide for common issues
  - _Requirements: Documentation requirement_

- [ ] 25. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
