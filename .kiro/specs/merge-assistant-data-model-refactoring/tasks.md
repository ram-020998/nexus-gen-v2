# Implementation Plan

- [x] 1. Create database schema for normalized tables
- [x] 1.1 Create Package and PackageObjectTypeCount models
  - Define Package model with relationships
  - Define PackageObjectTypeCount model with foreign keys
  - Add indexes for efficient queries
  - _Requirements: 1.1, 6.1_

- [x] 1.2 Create AppianObject model without JSON properties
  - Define AppianObject model with basic fields
  - Add relationships to Package
  - Add indexes on uuid, name, object_type
  - _Requirements: 1.1, 6.2_

- [x] 1.3 Create Process Model normalization tables
  - Define ProcessModelMetadata model
  - Define ProcessModelNode model with foreign keys
  - Define ProcessModelFlow model with node relationships
  - Add indexes for efficient node and flow queries
  - _Requirements: 1.1, 6.2_

- [x] 1.4 Create Change model without JSON fields
  - Define Change model with object foreign keys
  - Add classification and change_type columns
  - Add display_order for maintaining sequence
  - Add indexes on session_id, classification, object_type
  - _Requirements: 1.2, 1.3, 6.3_

- [x] 1.5 Create MergeGuidance normalization tables
  - Define MergeGuidance model with recommendation and reason
  - Define MergeConflict model for individual conflicts
  - Define MergeChange model for individual changes
  - Add foreign keys and indexes
  - _Requirements: 1.3, 6.3_

- [x] 1.6 Create ObjectDependency model
  - Define ObjectDependency model with parent/child UUIDs
  - Add foreign keys to Package
  - Add indexes on parent_uuid and child_uuid
  - _Requirements: 1.5, 6.5_

- [x] 1.7 Update ChangeReview model to link to Change
  - Modify ChangeReview to use change_id foreign key
  - Remove duplicate object information columns
  - Add indexes for efficient queries
  - _Requirements: 6.4_

- [x] 1.8 Generate and test database migration script
  - Create Alembic migration for new tables
  - Test migration on development database
  - Verify all tables, indexes, and constraints created
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 5.1, 5.3_

- [x] 2. Implement PackageService for blueprint normalization
- [x] 2.1 Create PackageService class
  - Implement create_package_from_blueprint method
  - Extract metadata from blueprint
  - Create Package record
  - _Requirements: 1.1, 6.1_

- [x] 2.2 Implement object extraction and normalization
  - Extract objects from blueprint['object_lookup']
  - Create AppianObject records in batch
  - Handle SAIL code, fields, and metadata
  - _Requirements: 1.1, 6.2_

- [x] 2.3 Implement object type count extraction
  - Extract object_type_counts from blueprint metadata
  - Create PackageObjectTypeCount records
  - _Requirements: 1.1_

- [x] 2.4 Implement process model normalization
  - Extract process_model_data from object properties
  - Create ProcessModelMetadata records
  - Create ProcessModelNode records for each node
  - Create ProcessModelFlow records for each flow
  - _Requirements: 1.1, 6.2_

- [x] 2.5 Implement dependency extraction
  - Extract dependencies from object references
  - Create ObjectDependency records
  - Handle interface references, rule references, etc.
  - _Requirements: 1.5, 6.5_

- [x] 2.6 Implement batch insert optimization
  - Use bulk_insert_mappings for large object sets
  - Implement transaction management
  - Add error handling and rollback
  - _Requirements: 1.1, 1.2, 1.5_

- [x] 2.7 Write property test for blueprint normalization
  - **Property 1: Blueprint data normalization**
  - **Validates: Requirements 1.1**

- [x] 2.8 Write unit tests for PackageService
  - Test create_package_from_blueprint
  - Test object extraction
  - Test process model normalization
  - Test dependency extraction
  - _Requirements: 1.1, 1.2, 1.5_

- [x] 3. Implement ChangeService for comparison normalization
- [x] 3.1 Create ChangeService class
  - Implement create_changes_from_comparison method
  - Handle classification results
  - Maintain display_order
  - _Requirements: 1.2, 1.3_

- [x] 3.2 Implement change record creation
  - Look up object IDs from AppianObject table
  - Create Change records with foreign keys
  - Set classification and change types
  - _Requirements: 1.2, 6.3_

- [x] 3.3 Implement merge guidance normalization
  - Extract guidance from change data
  - Create MergeGuidance records
  - Create MergeConflict records for conflicts
  - Create MergeChange records for changes
  - _Requirements: 1.3_

- [x] 3.4 Implement change review creation
  - Create ChangeReview records linked to Change
  - Set initial status to 'pending'
  - _Requirements: 6.4_

- [x] 3.5 Write property test for change foreign key validity
  - **Property 2: Change foreign key validity**
  - **Validates: Requirements 1.2**

- [x] 3.6 Write property test for classification normalization
  - **Property 3: Classification normalization**
  - **Validates: Requirements 1.3**

- [x] 3.7 Write unit tests for ChangeService
  - Test create_changes_from_comparison
  - Test merge guidance normalization
  - Test change review creation
  - _Requirements: 1.2, 1.3_

- [-] 4. Update ThreeWayMergeService to use normalized schema
- [x] 4.1 Update create_session method
  - Call PackageService for each blueprint
  - Call ChangeService for comparison results
  - Remove JSON serialization code
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 4.2 Update get_ordered_changes method
  - Implement SQL JOIN query instead of JSON parsing
  - Use joinedload for eager loading
  - Return enriched change data
  - _Requirements: 3.2, 4.2_

- [x] 4.3 Update filter_changes method
  - Implement SQL WHERE clauses for filtering
  - Use indexed columns for performance
  - Remove Python-based filtering
  - _Requirements: 3.2, 4.2_

- [x] 4.4 Update get_summary method
  - Use SQL aggregates for statistics
  - Query PackageObjectTypeCount for type breakdown
  - Remove JSON parsing
  - _Requirements: 4.4_

- [x] 4.5 Update update_progress method
  - Work with Change and ChangeReview tables
  - Update counts using SQL queries
  - _Requirements: 3.3_

- [x] 4.6 Update generate_report method
  - Use JOIN queries for complete data
  - Remove JSON deserialization
  - _Requirements: 3.5_

- [x] 4.7 Write property test for filter result consistency
  - **Property 9: Filter result consistency**
  - **Validates: Requirements 3.2**

- [x] 4.8 Write property test for review action equivalence
  - **Property 10: Review action equivalence**
  - **Validates: Requirements 3.3**

- [x] 4.9 Write unit tests for updated ThreeWayMergeService
  - Test create_session with normalized schema
  - Test get_ordered_changes with JOINs
  - Test filter_changes with SQL
  - Test get_summary with aggregates
  - _Requirements: 3.2, 3.3, 4.2, 4.4_

- [x] 5. Implement data migration service
- [x] 5.1 Create MigrationService class
  - Implement migrate_session method
  - Implement verify_migration method
  - Add progress tracking
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [x] 5.2 Implement blueprint migration
  - Parse base_blueprint JSON
  - Call PackageService to normalize
  - Repeat for customized and new_vendor blueprints
  - _Requirements: 2.3_

- [x] 5.3 Implement comparison migration
  - Parse vendor_changes and customer_changes JSON
  - Parse classification_results JSON
  - Parse ordered_changes JSON
  - Call ChangeService to normalize
  - _Requirements: 2.4_

- [x] 5.4 Implement verification logic
  - Verify package count equals 3
  - Verify object counts match blueprint metadata
  - Verify change count matches ordered_changes length
  - Verify all foreign keys are valid
  - _Requirements: 2.5_

- [x] 5.5 Implement error handling and rollback
  - Wrap migration in transaction
  - Rollback on any error
  - Log detailed error messages
  - _Requirements: 2.2_

- [x] 5.6 Write property test for session metadata preservation
  - **Property 5: Session metadata preservation**
  - **Validates: Requirements 2.2**

- [x] 5.7 Write property test for blueprint migration round-trip
  - **Property 6: Blueprint migration round-trip**
  - **Validates: Requirements 2.3**

- [x] 5.8 Write property test for change ordering preservation
  - **Property 7: Change ordering preservation**
  - **Validates: Requirements 2.4**

- [x] 5.9 Write property test for migration record count verification
  - **Property 8: Migration record count verification**
  - **Validates: Requirements 2.5**

- [x] 5.10 Write unit tests for MigrationService
  - Test migrate_session
  - Test verify_migration
  - Test error handling
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [x] 6. Update controllers to use new schema
- [x] 6.1 Update merge_assistant_controller.py
  - Update upload_packages to use new service methods
  - Update view_change to use JOIN queries
  - Update review_change to work with new schema
  - Remove JSON parsing code
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 6.2 Test all controller endpoints
  - Test upload and session creation
  - Test change viewing
  - Test filtering
  - Test review recording
  - Test report generation
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [x] 6.3 Write integration tests for controllers
  - Test complete upload-to-report workflow
  - Test filtering and searching
  - Test review workflow
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 7. Implement query optimization
- [x] 7.1 Add query optimization for change loading
  - Use joinedload for eager loading
  - Implement pagination for large result sets
  - Add query plan analysis
  - _Requirements: 4.2, 4.3_

- [x] 7.2 Add query optimization for filtering
  - Ensure indexes are used
  - Optimize WHERE clauses
  - Add query caching if needed
  - _Requirements: 4.2_

- [x] 7.3 Add query optimization for statistics
  - Use SQL aggregates instead of loading all data
  - Optimize GROUP BY queries
  - _Requirements: 4.4_

- [x] 7.4 Write property test for object name search correctness
  - **Property 12: Object name search correctness**
  - **Validates: Requirements 4.2**

- [x] 7.5 Write property test for statistics calculation accuracy
  - **Property 13: Statistics calculation accuracy**
  - **Validates: Requirements 4.4**

- [x] 7.6 Write property test for dependency query correctness
  - **Property 14: Dependency query correctness**
  - **Validates: Requirements 4.5**

- [x] 8. Implement data integrity constraints
- [x] 8.1 Verify foreign key constraints
  - Test that invalid foreign keys are rejected
  - Test cascade deletes work correctly
  - _Requirements: 5.1, 5.4, 5.5_

- [x] 8.2 Verify unique constraints
  - Test that duplicate UUIDs are rejected
  - Test that duplicate package/object combinations are rejected
  - _Requirements: 5.2_

- [x] 8.3 Test referential integrity
  - Test that orphaned records cannot be created
  - Test that updates maintain integrity
  - _Requirements: 5.5_

- [x] 8.4 Write property test for UUID uniqueness enforcement
  - **Property 15: UUID uniqueness enforcement**
  - **Validates: Requirements 5.2**

- [x] 8.5 Write property test for cascade delete completeness
  - **Property 16: Cascade delete completeness**
  - **Validates: Requirements 5.4**

- [x] 8.6 Write property test for referential integrity enforcement
  - **Property 17: Referential integrity enforcement**
  - **Validates: Requirements 5.5**

- [-] 9. Write remaining property-based tests
- [x] 9.1 Write property test for dependency table population
  - **Property 4: Dependency table population**
  - **Validates: Requirements 1.5**

- [x] 9.2 Write property test for export data completeness
  - **Property 11: Export data completeness**
  - **Validates: Requirements 3.5**

- [x] 9.3 Write property test for package storage correctness
  - **Property 18: Package storage correctness**
  - **Validates: Requirements 6.1**

- [x] 9.4 Write property test for object-package linkage
  - **Property 19: Object-package linkage**
  - **Validates: Requirements 6.2**

- [x] 9.5 Write property test for change-object linkage
  - **Property 20: Change-object linkage**
  - **Validates: Requirements 6.3**

- [ ] 9.6 Write property test for review-change linkage
  - **Property 21: Review-change linkage**
  - **Validates: Requirements 6.4**

- [ ] 9.7 Write property test for dependency storage correctness
  - **Property 22: Dependency storage correctness**
  - **Validates: Requirements 6.5**

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Run migration on existing data
- [x] 11.1 Create backup of production database
  - Export current database
  - Verify backup integrity
  - _Requirements: 2.1_

- [x] 11.2 Run migration script on all sessions
  - Migrate sessions one at a time
  - Log progress and errors
  - Verify each session after migration
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [x] 11.3 Verify migration completeness
  - Check that all sessions migrated successfully
  - Verify record counts match expectations
  - Test querying migrated data
  - _Requirements: 2.5_

- [x] 11.4 Test application with migrated data
  - Test all functionality with real data
  - Verify UI displays correctly
  - Test filtering and searching
  - Test report generation
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [x] 12. Performance testing and optimization
- [x] 12.1 Measure baseline performance with old schema
  - Measure filter operation time
  - Measure search operation time
  - Measure report generation time
  - Measure change loading time
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 12.2 Measure performance with new schema
  - Measure same operations with normalized schema
  - Compare against baseline
  - Verify performance targets met
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 12.3 Optimize slow queries
  - Identify slow queries using EXPLAIN
  - Add missing indexes if needed
  - Optimize JOIN queries
  - _Requirements: 4.2, 4.3_

- [x] 12.4 Test with large sessions
  - Test with sessions containing 1000+ changes
  - Verify pagination works correctly
  - Verify memory usage is acceptable
  - _Requirements: 4.2_

- [x] 13. Cleanup and finalization
- [x] 13.1 Remove old JSON columns from MergeSession
  - Create migration to drop JSON columns
  - Test that application still works
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 13.2 Remove unused code
  - Remove JSON parsing code
  - Remove old query methods
  - Update documentation
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 13.3 Optimize database
  - Run VACUUM to reclaim space
  - Analyze tables for query planner
  - Verify database size reduction
  - _Requirements: 4.1_

- [x] 13.4 Update documentation
  - Document new schema structure
  - Update API documentation
  - Update developer guide
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [ ] 14. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
