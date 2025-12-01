# Implementation Plan

## Summary of Existing vs New Components

**Already Exists (Need to Fix/Enhance):**
- Parsers: expression_rule_parser.py, record_type_parser.py, cdt_parser.py, process_model_parser.py
- Repositories: expression_rule_repository.py, record_type_repository.py, cdt_repository.py
- Comparison Repositories: interface_comparison_repository.py, process_model_comparison_repository.py, record_type_comparison_repository.py
- Models: ExpressionRule, RecordType, CDT, ProcessModel (with child tables)

**Need to Create:**
- Data Store parser and repository (if not exists)
- Comparison repositories: expression_rule_comparison_repository.py, cdt_comparison_repository.py, constant_comparison_repository.py
- Models: DataStore, ExpressionRuleComparison, CDTComparison, ConstantComparison
- Changes table columns: vendor_object_id, customer_object_id

---

- [x] 1. Create database migration for schema changes
  - Create migration script `migrations/migrations_003_data_completeness.py`
  - Add new tables: data_stores, data_store_entities (if not exists)
  - Add comparison tables: expression_rule_comparisons, cdt_comparisons, constant_comparisons
  - Modify changes table: add vendor_object_id and customer_object_id columns
  - Migrate existing data: `UPDATE changes SET vendor_object_id = object_id`
  - Add foreign key constraints with CASCADE behavior
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [ ]* 1.1 Write property test for schema migration safety
  - **Property 14: Schema Migration Safety**
  - **Validates: Requirements 5.5**

- [x] 2. Verify and enhance ExpressionRuleRepository
  - Review existing `repositories/expression_rule_repository.py`
  - Verify `create_expression_rule(object_id, data)` method works correctly
  - Verify `create_expression_rule_input(rule_id, data)` method works correctly
  - Verify `get_by_object_id(object_id)` method with inputs eager loading
  - Fix any missing or incomplete methods
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Fix ExpressionRuleParser to extract all data
  - Review existing `services/parsers/expression_rule_parser.py`
  - Ensure it parses expressionRule.xml files completely
  - Extract: name, uuid, version_uuid, description, return_type, definition
  - Extract input parameters: name, data_type, description, required flag
  - Verify it uses ObjectLookupRepository.find_or_create() to prevent duplicates
  - Verify it stores in expression_rules and expression_rule_inputs tables
  - Verify it stores version in object_versions table
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.2, 8.3, 8.4_

- [ ]* 3.1 Write property test for Expression Rule extraction completeness
  - **Property 1: Extraction Completeness (Expression Rules)**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 3.2 Write property test for Expression Rule input extraction
  - **Property 4: Child Entity Extraction (Expression Rule Inputs)**
  - **Validates: Requirements 1.3**

- [ ]* 3.3 Write property test for Expression Rule no duplicates
  - **Property 2: No Duplicate Objects**
  - **Validates: Requirements 1.4, 8.2**

- [ ] 4. Verify and enhance RecordTypeRepository
  - Review existing `repositories/record_type_repository.py`
  - Verify `create_record_type(object_id, data)` method
  - Verify `create_field(record_type_id, data)` method
  - Verify `create_relationship(record_type_id, data)` method
  - Verify `create_view(record_type_id, data)` method
  - Verify `create_action(record_type_id, data)` method
  - Verify `get_by_object_id(object_id)` with all child entities eager loaded
  - Fix any missing or incomplete methods
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 5. Fix RecordTypeParser to extract all data
  - Review existing `services/parsers/record_type_parser.py`
  - Ensure it parses recordType.xml files completely
  - Extract: name, uuid, version_uuid, description, data_source
  - Extract fields: name, data_type, required, field_configuration, display_order
  - Extract relationships: relationship_type, target_record_type_uuid, cardinality, cascade_behavior
  - Extract views: view_name, view_type, column_configuration, filter_definitions
  - Extract actions: action_name, action_type, process_model_reference, visibility_rules
  - Verify it uses ObjectLookupRepository.find_or_create()
  - Verify it stores in all record_type tables
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.2, 8.3, 8.4_

- [ ]* 5.1 Write property test for Record Type extraction completeness
  - **Property 1: Extraction Completeness (Record Types)**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 5.2 Write property test for Record Type child entity extraction
  - **Property 4: Child Entity Extraction (Record Type Fields/Relationships/Views/Actions)**
  - **Validates: Requirements 2.2, 2.3, 2.4, 2.5**

- [ ] 6. Verify and enhance CDTRepository
  - Review existing `repositories/cdt_repository.py`
  - Verify `create_cdt(object_id, data)` method
  - Verify `create_cdt_field(cdt_id, data)` method
  - Verify `get_by_object_id(object_id)` with fields eager loaded
  - Fix any missing or incomplete methods
  - _Requirements: 3.1, 3.2_

- [ ] 7. Fix CDTParser to follow standard pattern
  - Review existing `services/parsers/cdt_parser.py`
  - Ensure it parses dataType.xsd files completely
  - Extract: namespace, name, uuid (from XSD annotations)
  - Extract fields: field_name, data_type, multiple_flag, namespace, field_order
  - Verify it uses ObjectLookupRepository.find_or_create()
  - Verify it stores in cdts and cdt_fields tables
  - Verify it stores version in object_versions table
  - _Requirements: 3.1, 3.2, 8.2, 8.3, 8.4_

- [ ]* 7.1 Write property test for CDT extraction completeness
  - **Property 1: Extraction Completeness (CDTs)**
  - **Validates: Requirements 3.1, 3.2**

- [ ]* 7.2 Write property test for CDT field extraction
  - **Property 4: Child Entity Extraction (CDT Fields)**
  - **Validates: Requirements 3.2**

- [ ] 8. Create or verify DataStoreRepository
  - Check if repository exists, create if needed
  - Implement `create_data_store(object_id, data)` method
  - Implement `create_entity_mapping(data_store_id, data)` method
  - Implement `get_by_object_id(object_id)` with entity mappings
  - _Requirements: 3.3, 3.4, 3.5_

- [ ] 9. Create or verify DataStoreParser
  - Check if parser exists, create if needed
  - Extend BaseParser class
  - Parse dataStore.xml files
  - Extract: name, uuid, description, database_connection_reference, configuration
  - Extract entity mappings: cdt_uuid, table_name, column_mappings
  - Use ObjectLookupRepository.find_or_create()
  - Store in data_stores and data_store_entities tables
  - _Requirements: 3.3, 3.4, 3.5, 8.2, 8.3, 8.4_

- [ ]* 9.1 Write property test for Data Store extraction completeness
  - **Property 1: Extraction Completeness (Data Stores)**
  - **Validates: Requirements 3.3, 3.4**

- [ ]* 9.2 Write property test for Data Store entity mapping extraction
  - **Property 4: Child Entity Extraction (Data Store Entities)**
  - **Validates: Requirements 3.5**

- [ ] 10. Fix ProcessModelParser to extract nodes, flows, and variables
  - Review existing `services/parsers/process_model_parser.py`
  - Add extraction of nodes: node_uuid, node_name, node_type, label, position_coordinates, configuration_json
  - Add extraction of node attributes: assignment_configuration, escalation_rules, form_references, subprocess_references, timer_settings
  - Add extraction of flows: flow_uuid, source_node_uuid, target_node_uuid, condition_expression, label, flow_type
  - Add extraction of flow attributes: flow_conditions, exception_handling_paths, conditional_routing_logic
  - Add extraction of variables: variable_name, data_type, multiple_flag, default_value, parameter_flag
  - Store in process_model_nodes, process_model_flows, process_model_variables tables
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 10.1 Write property test for Process Model structural completeness
  - **Property 11: Process Model Structural Completeness**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

- [ ] 11. Update PackageExtractionService to invoke all parsers
  - Review `services/package_extraction_service.py`
  - Verify expression_rule_parser is invoked for expressionRule.xml files
  - Verify record_type_parser is invoked for recordType.xml files
  - Verify cdt_parser is invoked for dataType.xsd files
  - Verify data_store_parser is invoked for dataStore.xml files (if applicable)
  - Ensure error handling continues processing on parser failures
  - _Requirements: 1.1, 2.1, 3.1, 3.3, 8.5_

- [ ]* 11.1 Write property test for error resilience
  - **Property 13: Error Resilience**
  - **Validates: Requirements 8.5**

- [ ] 12. Checkpoint - Ensure all extraction tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Create new comparison result repositories
  - Create `repositories/comparison/expression_rule_comparison_repository.py`
  - Create `repositories/comparison/cdt_comparison_repository.py`
  - Create `repositories/comparison/constant_comparison_repository.py`
  - Each repository implements `create_comparison(session_id, object_id, comparison_data)` method
  - Each repository implements `get_by_session_and_object(session_id, object_id)` method
  - _Requirements: 4.4, 4.5, 4.6_

- [ ] 14. Fix InterfaceComparisonRepository to persist results
  - Review `repositories/comparison/interface_comparison_repository.py`
  - Ensure `create_comparison()` method actually inserts into database
  - Store: sail_diff, parameter_changes, security_changes, diff_metadata
  - Link to session via session_id foreign key
  - Link to object via object_id foreign key
  - _Requirements: 4.1, 4.7_

- [ ] 15. Fix ProcessModelComparisonRepository to persist results
  - Review `repositories/comparison/process_model_comparison_repository.py`
  - Ensure `create_comparison()` method actually inserts into database
  - Store: node_diffs, flow_diffs, variable_diffs, mermaid_diagrams (base, customer, new_vendor), structural_analysis
  - Link to session and object via foreign keys
  - _Requirements: 4.2, 4.7_

- [ ] 16. Fix RecordTypeComparisonRepository to persist results
  - Review `repositories/comparison/record_type_comparison_repository.py`
  - Ensure `create_comparison()` method actually inserts into database
  - Store: field_changes, relationship_modifications, view_updates, action_differences, impact_analysis
  - Link to session and object via foreign keys
  - _Requirements: 4.3, 4.7_

- [ ] 17. Enhance DeltaComparisonService to generate and persist detailed diffs
  - Update `services/delta_comparison_service.py`
  - Implement `_compare_interfaces()` method to generate line-by-line SAIL code diffs
  - Implement `_compare_process_models()` method to compare nodes, flows, variables
  - Implement `_compare_record_types()` method to compare fields, relationships, views, actions
  - Implement `_compare_expression_rules()` method to compare inputs and logic
  - Implement `_compare_cdts()` method to compare fields
  - Implement `_compare_constants()` method to compare values
  - Call appropriate comparison repository to persist results
  - Mark additions in green, deletions in red, modifications in yellow
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 9.1, 9.2, 9.3, 9.4_

- [ ]* 17.1 Write property test for detailed diff generation
  - **Property 7: Detailed Diff Generation**
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

- [ ]* 17.2 Write property test for comparison result persistence
  - **Property 6: Comparison Result Persistence**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7**

- [ ] 18. Update CustomerComparisonService to track dual object IDs
  - Update `services/customer_comparison_service.py`
  - Modify change creation to populate vendor_object_id (from delta object)
  - Modify change creation to populate customer_object_id (from customer package lookup)
  - Set customer_object_id to NULL for NEW objects
  - Ensure both IDs are stored in changes table
  - _Requirements: 5.1, 5.2, 5.3_

- [ ]* 18.1 Write property test for dual object tracking
  - **Property 8: Dual Object Tracking in Changes**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [ ]* 18.2 Write property test for efficient change queries
  - **Property 9: Efficient Change Queries**
  - **Validates: Requirements 5.4**

- [ ] 19. Checkpoint - Ensure all comparison tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Create UI template for Constant comparison
  - Create `templates/merge/comparisons/constant_comparison.html`
  - Display base_value, customer_value, new_vendor_value in side-by-side format
  - Highlight value differences
  - Show type changes if applicable
  - _Requirements: 6.1_

- [ ] 21. Create UI template for Expression Rule comparison
  - Create `templates/merge/comparisons/expression_rule_comparison.html`
  - Display input parameter differences in tabular format
  - Display return type changes
  - Display rule logic modifications with diff highlighting
  - _Requirements: 6.4_

- [ ] 22. Create UI template for Record Type comparison
  - Create `templates/merge/comparisons/record_type_comparison.html`
  - Display field modifications with old/new values
  - Display relationship changes
  - Display view updates
  - Display action differences
  - Use tabular format with clear change indicators
  - _Requirements: 6.5_

- [ ] 23. Create UI template for CDT comparison
  - Create `templates/merge/comparisons/cdt_comparison.html`
  - Display field type changes in tabular format
  - Display field additions (highlighted in green)
  - Display field removals (highlighted in red)
  - Display namespace modifications
  - _Requirements: 6.6_

- [ ] 24. Enhance Interface comparison UI template
  - Update `templates/merge/comparisons/interface_comparison.html` (if exists)
  - Add syntax highlighting for SAIL code
  - Add line numbers
  - Implement side-by-side comparison view
  - Mark additions in green, deletions in red, modifications in yellow
  - _Requirements: 6.2_

- [ ] 25. Enhance Process Model comparison UI template
  - Update `templates/merge/comparisons/process_model_comparison.html` (if exists)
  - Display node differences in structured format
  - Display flow changes with source/target information
  - Display variable modifications
  - Render Mermaid diagrams for Base, Customer, and New Vendor versions
  - _Requirements: 6.3_

- [ ] 26. Update MergeAssistantController to wire UI templates
  - Update `controllers/merge_assistant_controller.py`
  - Modify `view_change_detail()` route to retrieve comparison data
  - Add logic to select appropriate template based on object_type
  - For constants: retrieve from constant_comparison_repo and render constant_comparison.html
  - For interfaces: retrieve from interface_comparison_repo and render interface_comparison.html
  - For process models: retrieve from process_model_comparison_repo and render process_model_comparison.html
  - For expression rules: retrieve from expression_rule_comparison_repo and render expression_rule_comparison.html
  - For record types: retrieve from record_type_comparison_repo and render record_type_comparison.html
  - For CDTs: retrieve from cdt_comparison_repo and render cdt_comparison.html
  - Handle missing comparison data gracefully with warning message
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [ ]* 26.1 Write property test for UI data completeness
  - **Property 10: UI Data Completeness**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7**

- [ ] 27. Update ChangeRepository to support dual object ID queries
  - Update `repositories/change_repository.py`
  - Modify queries to join object_lookup twice (vendor and customer)
  - Add method `get_with_vendor_and_customer_objects(change_id)` for efficient retrieval
  - Ensure backward compatibility with existing queries
  - _Requirements: 5.4_

- [ ] 28. Register new repositories and parsers in DependencyContainer
  - Update `core/dependency_container.py`
  - Verify ExpressionRuleRepository is registered
  - Verify ExpressionRuleParser is registered
  - Verify RecordTypeRepository is registered
  - Verify RecordTypeParser is registered
  - Register DataStoreRepository (if new)
  - Register DataStoreParser (if new)
  - Register new comparison repositories
  - Ensure all dependencies are properly wired
  - _Requirements: All_

- [ ] 29. Update database models in models.py
  - Update `models.py`
  - Add DataStore model (if not exists)
  - Add DataStoreEntity model (if not exists)
  - Add ExpressionRuleComparison model
  - Add CDTComparison model
  - Add ConstantComparison model
  - Modify Change model to add vendor_object_id and customer_object_id columns
  - Add foreign key relationships with CASCADE behavior
  - _Requirements: All_

- [ ] 30. Run database migration
  - Execute migration script to create new tables and modify existing ones
  - Verify all tables are created correctly
  - Verify foreign key constraints are in place
  - Verify existing data is migrated correctly
  - _Requirements: 5.5_

- [ ] 31. Final Checkpoint - Run complete end-to-end test
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 32. Write comprehensive integration test
  - Test complete merge workflow with real packages
  - Verify all object types are extracted
  - Verify all comparison results are persisted
  - Verify UI displays all object details correctly
  - Use packages from `applicationArtifacts/Three Way Testing Files/V2/`
  - _Requirements: All_

- [ ]* 33. Write property test for multi-version tracking
  - **Property 3: Multi-Version Tracking**
  - **Validates: Requirements 1.5, 8.3**

- [ ]* 34. Write property test for referential integrity
  - **Property 5: Referential Integrity**
  - **Validates: Requirements 8.4**

- [ ]* 35. Write property test for Process Model comparison completeness
  - **Property 12: Process Model Comparison Completeness**
  - **Validates: Requirements 7.6, 7.7**
