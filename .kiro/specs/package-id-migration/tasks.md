# Implementation Plan

## Overview

This implementation plan breaks down the package_id migration into discrete, actionable coding tasks. Each task builds incrementally on previous tasks, with property-based tests integrated throughout to catch errors early.

## Task List

- [x] 1. Create migration script structure
  - Create `migrations/migrations_004_add_package_id_to_objects.py`
  - Implement basic migration class with upgrade method
  - Add transaction handling and error logging
  - Add progress logging for each major step
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 2. Implement schema modification methods
  - Implement `_add_package_id_column()` method for adding column to a table
  - Implement `_create_index()` method for creating indexes
  - Implement `_add_unique_constraint()` method for adding constraints
  - Implement `_alter_column_not_null()` method for making column NOT NULL
  - Test each method individually with a single table
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.1, 3.2, 3.3_

- [x] 3. Implement data migration method
  - Implement `_populate_package_id()` method using object_versions as source
  - Add logic to match by object_id and version_uuid
  - Add warning logging for entries with no match
  - Add validation to check for NULL values after population
  - Test with sample data
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4. Implement complete upgrade workflow
  - Implement `upgrade()` method that orchestrates all steps
  - Add package_id column to all 13 object-specific tables
  - Populate package_id for all 13 tables
  - Verify no NULLs remain
  - Alter columns to NOT NULL
  - Add unique constraints to all 13 tables
  - Create composite indexes for all 13 tables
  - Run ANALYZE to update statistics
  - _Requirements: 1.1, 1.2, 1.4, 2.5, 3.1, 3.3, 9.1, 9.4_

- [ ]* 4.1 Write property test for schema structure
  - **Property 1: All object-specific tables have package_id column**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 4.2 Write property test for indexes
  - **Property 2: All package_id columns have indexes**
  - **Validates: Requirements 1.4, 3.3, 9.1**

- [ ]* 4.3 Write property test for child tables
  - **Property 3: Child tables do not have package_id**
  - **Validates: Requirements 1.5, 11.2**

- [ ]* 4.4 Write property test for data migration
  - **Property 4: All package_id values match object_versions**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 4.5 Write property test for NULL values
  - **Property 5: No NULL package_id values after migration**
  - **Validates: Requirements 2.4, 2.5, 7.1**

- [ ]* 4.6 Write property test for unique constraints
  - **Property 6: Unique constraint prevents duplicates**
  - **Validates: Requirements 3.1, 3.4, 7.2**

- [ ]* 4.7 Write property test for constraint naming
  - **Property 7: Unique constraint naming convention**
  - **Validates: Requirements 3.2**

- [x] 5. Run migration script
  - Execute migration on development database
  - Verify all tables modified successfully
  - Check logs for any warnings or errors
  - Run validation queries to verify data integrity
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 5.1 Write property test for referential integrity
  - **Property 8: All package_id values reference valid packages**
  - **Validates: Requirements 7.3**

- [ ]* 5.2 Write property test for mapping consistency
  - **Property 9: Package-object mappings consistency**
  - **Validates: Requirements 7.4**

- [ ] 6. Checkpoint - Verify migration completed successfully
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Update database models
  - Add package_id column to Interface model with FK constraint
  - Add unique constraint and composite index to Interface model
  - Add package_id column to ExpressionRule model with FK constraint
  - Add unique constraint and composite index to ExpressionRule model
  - Add package_id column to ProcessModel model with FK constraint
  - Add unique constraint and composite index to ProcessModel model
  - Add package_id column to RecordType model with FK constraint
  - Add unique constraint and composite index to RecordType model
  - Add package_id column to CDT model with FK constraint
  - Add unique constraint and composite index to CDT model
  - Add package_id column to remaining 8 models (Integration, WebAPI, Site, Group, Constant, ConnectedSystem, DataStore, UnknownObject)
  - Add unique constraints and composite indexes to remaining 8 models
  - _Requirements: 1.1, 1.2, 1.4, 3.1, 3.3_

- [x] 8. Update PackageExtractionService
  - Update `_store_interface_data()` to accept and use package_id parameter
  - Update `_store_expression_rule_data()` to accept and use package_id parameter
  - Update `_store_process_model_data()` to accept and use package_id parameter
  - Update `_store_record_type_data()` to accept and use package_id parameter
  - Update `_store_cdt_data()` to accept and use package_id parameter
  - Update remaining 8 `_store_*_data()` methods to accept and use package_id parameter
  - Update `_store_object_specific_data()` to pass package_id to all storage methods
  - Update `_process_object()` to pass package_id to `_store_object_specific_data()`
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 8.1 Write property test for extraction service
  - **Property 10: Extraction service passes package_id**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [x] 9. Update InterfaceRepository
  - Update `create_interface()` to accept package_id as required parameter
  - Add `get_by_object_and_package()` method
  - Add `get_all_by_object_id()` method
  - Add `get_by_package()` method
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 10. Update ExpressionRuleRepository
  - Update `create_expression_rule()` to accept package_id as required parameter
  - Add `get_by_object_and_package()` method
  - Add `get_all_by_object_id()` method
  - Add `get_by_package()` method
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 11. Update ProcessModelRepository
  - Update `create_process_model()` to accept package_id as required parameter
  - Add `get_by_object_and_package()` method
  - Add `get_all_by_object_id()` method
  - Add `get_by_package()` method
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 12. Update RecordTypeRepository
  - Update `create_record_type()` to accept package_id as required parameter
  - Add `get_by_object_and_package()` method
  - Add `get_all_by_object_id()` method
  - Add `get_by_package()` method
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 13. Update CDTRepository
  - Update `create_cdt()` to accept package_id as required parameter
  - Add `get_by_object_and_package()` method
  - Add `get_all_by_object_id()` method
  - Add `get_by_package()` method
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 14. Update remaining 8 repositories
  - Update IntegrationRepository with package_id support
  - Update WebAPIRepository with package_id support
  - Update SiteRepository with package_id support
  - Update GroupRepository with package_id support
  - Update ConstantRepository with package_id support
  - Update ConnectedSystemRepository with package_id support
  - Update DataStoreRepository with package_id support (create if not exists)
  - Update UnknownObjectRepository with package_id support
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 14.1 Write property test for repository create methods
  - **Property 11: Repository create methods accept package_id**
  - **Validates: Requirements 5.1**

- [ ]* 14.2 Write property test for repository query methods
  - **Property 12: Query by object and package returns single result**
  - **Validates: Requirements 5.2, 5.5**

- [ ]* 14.3 Write property test for repository query all versions
  - **Property 13: Query by object_id returns all package versions**
  - **Validates: Requirements 5.3, 5.4**

- [ ] 15. Checkpoint - Verify repositories work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Update export_merge_session.py
  - Update `export_object_details()` to accept optional package_id parameter
  - Add logic to query by package_id when provided
  - Add logic to export all versions when package_id not provided
  - Update all object type exports (interfaces, expression_rules, process_models, etc.)
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 17. Update export_session_flat.py
  - Update export logic to include package_type for each object version
  - Update export logic to include package_filename for each object version
  - Ensure all object versions are exported with clear package identification
  - _Requirements: 6.4, 6.5_

- [ ]* 17.1 Write property test for export with package_id
  - **Property 14: Export with package_id returns correct version**
  - **Validates: Requirements 6.2**

- [ ]* 17.2 Write property test for export package identification
  - **Property 15: Export includes package identification**
  - **Validates: Requirements 6.4, 6.5**

- [x] 18. Update test fixtures and utilities
  - Update `tests/test_utilities/database_fixtures.py` to include package_id when creating objects
  - Update test helper functions to accept package_id parameter
  - Update test data creation to use package_id
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 19. Update test_package_extraction_service.py
  - Update tests to verify package_id is set correctly
  - Update assertions to check package_id matches expected package
  - Add test for multiple packages with same object
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 20. Update test_repositories.py
  - Update tests to include package_id in object creation
  - Update query tests to filter by package_id
  - Add tests for new repository methods (get_by_object_and_package, get_all_by_object_id)
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 21. Update test_three_way_merge_orchestrator.py
  - Update integration tests to verify package_id is populated
  - Add assertions to check package_id in extracted objects
  - Verify unique constraints work in end-to-end workflow
  - _Requirements: 8.4, 8.5_

- [ ]* 21.1 Write property test for child table queries
  - **Property 16: Child table queries join to parent for package_id**
  - **Validates: Requirements 11.1, 11.4, 11.5**

- [ ]* 21.2 Write property test for CASCADE DELETE
  - **Property 17: CASCADE DELETE removes child records**
  - **Validates: Requirements 11.3**

- [x] 22. Review and update comparison services
  - Review DeltaComparisonService to ensure it uses object_versions correctly
  - Review CustomerComparisonService to ensure it uses package_id when needed
  - Review MergeGuidanceService to ensure it uses package_id for retrieving object data
  - Update any queries that need package_id filtering
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 22.1 Write property test for comparison services
  - **Property 18: Comparison services use package_id correctly**
  - **Validates: Requirements 12.2, 12.3, 12.4**

- [ ]* 22.2 Write property test for object_versions compatibility
  - **Property 19: Comparison services maintain object_versions compatibility**
  - **Validates: Requirements 12.1, 12.5**

- [x] 23. Update validation scripts
  - Update `verify_schema.py` to check for package_id columns
  - Update `check_schema.py` to verify unique constraints
  - Add validation queries to check data integrity
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 24. Run complete end-to-end test
  - Truncate all tables to start fresh
  - Run complete three-way merge workflow with real packages
  - Verify all object-specific tables have package_id populated
  - Verify no duplicate (object_id, package_id) combinations
  - Verify all package_id values reference valid packages
  - Verify package_object_mappings consistency
  - Run all property-based tests
  - _Requirements: 8.4, 8.5_

- [ ] 25. Final Checkpoint - All tests passing
  - Ensure all tests pass, ask the user if questions arise.
