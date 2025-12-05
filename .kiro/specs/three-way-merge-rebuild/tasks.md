# Implementation Plan

- [x] 1. Database Schema and Models
  - Create migration script for new schema
  - Add object_id column to all object-specific tables
  - Update models.py with new relationships
  - Run validation queries to ensure no duplicates
  - _Requirements: 2.1, 2.2, 2.3, 13.1, 13.2, 13.3_

- [ ]* 1.1 Write property test for no duplicates in object_lookup
  - **Property 1: No duplicate objects in object_lookup**
  - **Validates: Requirements 2.2, 2.3**

- [x] 2. Domain Layer - Enums and Entities
  - Create domain/enums.py with PackageType, ChangeCategory, Classification, ChangeType, SessionStatus
  - Create domain/entities.py with ObjectIdentity, DeltaChange, CustomerModification, ClassifiedChange
  - Create domain/comparison_strategies.py with VersionComparisonStrategy and ContentComparisonStrategy
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 3. Repository Layer - Base and Core Repositories
  - Create repositories/base_repository.py with BaseRepository abstract class
  - Implement repositories/object_lookup_repository.py with find_or_create method
  - Implement repositories/package_object_mapping_repository.py with bulk operations
  - Implement repositories/delta_comparison_repository.py
  - Implement repositories/change_repository.py
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 3.1 Write property test for find_or_create idempotence
  - **Property 18: find_or_create idempotence**
  - **Validates: Requirements 1.5, 2.2, 10.2**

- [ ]* 3.2 Write property test for package-object mappings consistency
  - **Property 2: Package-object mappings are consistent**
  - **Validates: Requirements 2.3, 2.4**

- [x] 4. Parser Layer - Base Parser and Factory
  - Create services/parsers/base_parser.py with BaseParser abstract class
  - Create services/parsers/xml_parser_factory.py with XMLParserFactory
  - Implement _extract_basic_info, _get_text, _clean_sail_code methods
  - _Requirements: 12.1_

- [x] 5. Parser Layer - Object-Specific Parsers
  - Implement services/parsers/interface_parser.py (extract SAIL code, parameters, security)
  - Implement services/parsers/process_model_parser.py (extract nodes, flows, variables, calculate complexity)
  - Implement services/parsers/record_type_parser.py (extract fields, relationships, views, actions)
  - Implement services/parsers/expression_rule_parser.py (extract SAIL code, inputs, output type)
  - Implement services/parsers/cdt_parser.py (extract namespace, fields)
  - Implement parsers for Integration, Web API, Site, Group, Constant, Connected System
  - Implement services/parsers/unknown_object_parser.py for unrecognized types
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 12.2, 12.3, 12.4, 12.5_

- [ ]* 5.1 Test InterfaceParser with real XML
  - Test with applicationArtifacts/ObjectSpecificXml /interface.xml
  - **Property 15: Complete object data extraction**
  - **Validates: Requirements 7.1**

- [ ]* 5.2 Test ProcessModelParser with real XML
  - Test with applicationArtifacts/ObjectSpecificXml /processModel.xml
  - **Property 16: Complete Process Model extraction**
  - **Validates: Requirements 7.2**

- [ ]* 5.3 Test RecordTypeParser with real XML
  - Test with applicationArtifacts/ObjectSpecificXml /recordType.xml
  - Verify all fields, relationships, views, actions extracted
  - **Validates: Requirements 7.3**

- [x] 6. Service Layer - Package Extraction Service
  - Implement services/package_extraction_service.py
  - Implement extract_package method with 7-step workflow
  - Implement _process_object method
  - Integrate with ZipExtractorService, XMLParserFactory, SAILCodeCleanerService
  - Use find_or_create to prevent duplicates
  - Create package_object_mappings for each object
  - Store object-specific data in object tables
  - Store version data in object_versions
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1_

- [ ]* 6.1 Test package extraction with real packages
  - Test with applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip
  - Verify no duplicates created
  - Verify all objects extracted
  - **Property 1: No duplicate objects**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

- [x] 7. Service Layer - Delta Comparison Service
  - Implement services/delta_comparison_service.py
  - Implement compare method to identify NEW, MODIFIED, DEPRECATED objects
  - Implement _compare_versions method for version and content comparison
  - Store results in delta_comparison_results table
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 11.2_

- [ ]* 7.1 Test delta comparison NEW detection
  - **Property 5: NEW objects are correctly identified**
  - **Validates: Requirements 3.1, 5.1**

- [ ]* 7.2 Test delta comparison DEPRECATED detection
  - **Property 6: DEPRECATED objects are correctly identified**
  - **Validates: Requirements 3.3**

- [ ]* 7.3 Test delta comparison MODIFIED detection
  - **Property 7: MODIFIED objects are correctly identified**
  - **Validates: Requirements 3.2, 3.4**

- [x] 8. Service Layer - Customer Comparison Service
  - Implement services/customer_comparison_service.py
  - Implement compare method to check customer modifications
  - Compare delta objects against Package B
  - Return comparison data (exists_in_customer, customer_modified, version_changed, content_changed)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 11.3_

- [x] 9. Service Layer - Classification Service
  - Implement services/classification_service.py
  - Implement ClassificationRuleEngine with classify method
  - Apply all 7 classification rules (10a-10g)
  - Create Change records with object_id reference
  - Set display_order for consistent presentation
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 6.1, 6.2, 6.3, 6.4, 6.5, 11.4_

- [ ]* 9.1 Test classification rule 10a (NO_CONFLICT for unmodified)
  - **Property 8: Classification Rule 10a**
  - **Validates: Requirements 5.2**

- [ ]* 9.2 Test classification rule 10b (CONFLICT for modified)
  - **Property 9: Classification Rule 10b**
  - **Validates: Requirements 5.3**

- [ ]* 9.3 Test classification rule 10c (DELETED for removed)
  - **Property 10: Classification Rule 10c**
  - **Validates: Requirements 5.4**

- [ ]* 9.4 Test classification rule 10d (NEW)
  - **Property 5: NEW objects classification**
  - **Validates: Requirements 5.1**

- [ ]* 9.5 Test classification rule 10e (NO_CONFLICT for deprecated unmodified)
  - **Property 11: Classification Rule 10e**
  - **Validates: Requirements 5.5**

- [ ]* 9.6 Test classification rule 10f (CONFLICT for deprecated modified)
  - **Property 12: Classification Rule 10f**
  - **Validates: Requirements 5.6**

- [ ]* 9.7 Test classification rule 10g (NO_CONFLICT for deprecated removed)
  - **Property 13: Classification Rule 10g**
  - **Validates: Requirements 5.7**

- [ ]* 9.8 Test delta-driven working set
  - **Property 3: Delta-driven working set**
  - **Validates: Requirements 6.1, 6.5**

- [ ]* 9.9 Test all delta objects are classified
  - **Property 4: All delta objects are classified**
  - **Validates: Requirements 5.1-5.7, 6.2**

- [x] 10. Service Layer - Merge Guidance Service
  - Implement services/merge_guidance_service.py
  - Implement generate_guidance method
  - Analyze conflicts and generate recommendations
  - Create MergeGuidance records
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 11. Service Layer - Three Way Merge Orchestrator
  - Implement services/three_way_merge_orchestrator.py
  - Implement create_merge_session method with 8-step workflow
  - Coordinate all sub-services (extraction, delta, customer, classification, guidance)
  - Handle transactions and rollback on errors
  - Update session status (PROCESSING → READY or ERROR)
  - Implement get_session_status and get_working_set methods
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 11.5_

- [ ]* 11.1 Test session status transitions
  - **Property 17: Session status transitions**
  - **Validates: Requirements 9.2**

- [x] 12. Integration Testing - End-to-End Workflow
  - Test complete workflow with real packages from applicationArtifacts/Three Way Testing Files/V2/
  - Upload Test Application - Base Version.zip (Package A)
  - Upload Test Application Customer Version.zip (Package B)
  - Upload Test Application Vendor New Version.zip (Package C)
  - Verify session created with reference_id
  - Verify all packages extracted
  - Verify delta comparison results stored
  - Verify customer comparison completed
  - Verify all changes classified
  - Verify merge guidance generated
  - Verify session status = 'ready'
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ]* 12.1 Verify no duplicates in object_lookup
  - Run validation query: SELECT uuid, COUNT(*) FROM object_lookup GROUP BY uuid HAVING COUNT(*) > 1
  - Should return 0 rows
  - **Property 1: No duplicates**
  - **Validates: Requirements 2.2, 15.2**

- [ ]* 12.2 Verify delta-driven working set
  - Verify COUNT(delta_comparison_results) == COUNT(changes)
  - **Property 3: Delta-driven**
  - **Validates: Requirements 6.1, 6.5, 15.4**

- [ ]* 12.3 Verify referential integrity
  - **Property 14: Referential integrity for changes**
  - **Validates: Requirements 6.2, 13.5**

- [ ]* 12.4 Verify known objects exist
  - Check for PROCESS_MODEL_UUID_1, PROCESS_MODEL_UUID_2, RECORD_TYPE_UUID
  - **Validates: Requirements 15.1**

- [x] 13. Object-Specific Repositories
  - Implement repositories/extraction/interface_repository.py
  - Implement repositories/extraction/process_model_repository.py
  - Implement repositories/extraction/record_type_repository.py
  - Implement repositories for all other object types
  - Each repository should handle object-specific data storage
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 14. Comparison Result Storage
  - Implement repositories/comparison/interface_comparison_repository.py
  - Implement repositories/comparison/process_model_comparison_repository.py
  - Implement repositories/comparison/record_type_comparison_repository.py
  - Store detailed differences in comparison tables
  - Link to changes table via change_id
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 15. Controller Layer
  - Update controllers/merge_assistant_controller.py
  - Implement create_merge_session endpoint (POST /merge/create)
  - Implement get_merge_summary endpoint (GET /merge/<reference_id>/summary)
  - Implement get_working_set endpoint (GET /merge/<reference_id>/changes)
  - Implement get_change_detail endpoint (GET /merge/<reference_id>/changes/<change_id>)
  - Handle file uploads for 3 packages
  - Return JSON responses with session data
  - _Requirements: 1.1, 9.1, 9.3, 9.4_

- [x] 16. Template Layer - Core Pages
  - Update templates/merge/upload.html for 3-package upload with drag-and-drop
  - Update templates/merge/sessions.html to list sessions with filters and status
  - Update templates/merge/summary.html to show statistics, breakdown by type, "Start Merge Workflow" button
  - Create templates/merge/_base_comparison.html as base template for all comparisons
  - Remove customer-only sections from templates
  - Use new data model (object_lookup, changes with object_id)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1a.1, 1a.2, 1a.3, 1a.4, 1a.5_

- [x] 17. Template Layer - Object-Specific Comparisons (Part 1)
  - Create templates/merge/comparisons/interface_comparison.html (SAIL code diff, parameters, security)
  - Create templates/merge/comparisons/expression_rule_comparison.html (SAIL code diff, inputs, output type)
  - Create templates/merge/comparisons/process_model_comparison.html (summary stats, Mermaid diagram, nodes, flows, variables)
  - Create templates/merge/comparisons/record_type_comparison.html (fields, relationships, views, actions)
  - Create templates/merge/comparisons/cdt_comparison.html (namespace, fields)
  - _Requirements: 1e.1, 1e.2, 1e.3, 1e.4, 1e.5_

- [x] 18. Template Layer - Object-Specific Comparisons (Part 2)
  - Create templates/merge/comparisons/integration_comparison.html (SAIL code, connection, auth, endpoint)
  - Create templates/merge/comparisons/web_api_comparison.html (SAIL code, endpoint, HTTP methods)
  - Create templates/merge/comparisons/site_comparison.html (page hierarchy tree)
  - Create templates/merge/comparisons/group_comparison.html (members, parent group)
  - Create templates/merge/comparisons/constant_comparison.html (value, type, scope)
  - Create templates/merge/comparisons/connected_system_comparison.html (system type, properties)
  - _Requirements: 1f.1, 1f.2, 1f.3, 1f.4, 1f.5_

- [x] 19. Template Layer - UI Components
  - Create classification badges component (NO_CONFLICT, CONFLICT, NEW, DELETED)
  - Create object type icons component (all 11 object types)
  - Create progress bar component
  - Create SAIL code diff component with syntax highlighting
  - Create navigation buttons component (Previous, Next, Back to Summary)
  - Create notes section component
  - _Requirements: 1c.1, 1c.3, 1c.4, 1c.5, 1d.1, 1d.2, 1d.3, 1d.4, 1d.5_

- [x] 20. Performance Optimization
  - Add database indexes (already in schema)
  - Implement bulk operations in repositories
  - Use eager loading (joinedload) for related objects
  - Add caching for frequently accessed objects
  - Verify all queries complete in < 200ms
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Documentation
  - Update README with new architecture
  - Document API endpoints
  - Update development log
  - Document validation queries
  - _Requirements: All_

- [ ] 23. Cleanup and Deployment
  - Remove deprecated code (BlueprintGenerationService, old three_way_merge_service.py)
  - Remove CUSTOMER_ONLY logic
  - Remove old object_lookup with package_id
  - Run all tests one final time
  - Deploy to production
  - _Requirements: All_
