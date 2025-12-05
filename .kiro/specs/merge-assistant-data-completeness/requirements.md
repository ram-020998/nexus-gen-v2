# Requirements Document

## Introduction

This specification addresses critical defects in the NexusGen Three-Way Merge Assistant workflow that prevent effective merge conflict resolution. The current implementation has multiple data extraction, storage, and display failures that were discovered during production use. These bugs cause incomplete object analysis, missing comparison data, and insufficient information in the merge workflow UI, making it impossible for analysts to make informed merge decisions. This specification documents the defects and defines the correct behavior required to fix them.

## Glossary

- **Merge Assistant**: The NexusGen three-way merge workflow system that compares Base (A), Customized (B), and New Vendor (C) Appian packages
- **Object Extraction**: The process of parsing Appian package XML files and storing object data in the database
- **Comparison Results**: Detailed analysis of differences between object versions stored in object-specific comparison tables
- **Working Set**: The collection of changes displayed in the merge workflow (stored in the changes table)
- **Expression Rule**: An Appian object type that contains reusable business logic with inputs and return values
- **Record Type**: An Appian object type that defines data structures with fields, relationships, views, and actions
- **CDT**: Custom Data Type - An Appian object type that defines structured data with typed fields
- **Data Store**: An Appian object type that provides database connectivity and entity mappings
- **Process Model**: An Appian object type that defines workflows with nodes, flows, and variables
- **Interface**: An Appian object type that defines UI components with SAIL code and parameters
- **Constant**: An Appian object type that stores immutable configuration values
- **SAIL Code**: Appian's expression language used in interfaces and other objects
- **Object Version**: A package-specific version of an object stored in the object_versions table
- **Delta Comparison**: The A→C comparison that identifies changes between Base and New Vendor versions
- **Customer Comparison**: The comparison between delta objects and Customer version to detect conflicts

## Requirements

### Requirement 1: Expression Rules Not Being Extracted

**Defect Description:** The package extraction service completely skips Expression Rule objects during package processing. When analysts upload packages containing Expression Rules, these objects are not parsed, not stored in the expression_rules table, and do not appear in the merge workflow. This causes the system to miss critical business logic changes and incorrectly report that packages have fewer objects than they actually contain.

**User Story:** As a merge analyst, I need Expression Rules to be extracted and stored during package processing, so that I can identify conflicts in business logic and make informed merge decisions.

#### Acceptance Criteria

1. WHEN the system extracts Package A, B, or C containing Expression Rule XML files THEN the system SHALL parse all Expression Rule files and store each rule in the expression_rules table with object_id linking to object_lookup
2. WHEN an Expression Rule is parsed THEN the system SHALL extract and store the rule name, UUID, version UUID, description, return type, and rule definition
3. WHEN an Expression Rule has input parameters THEN the system SHALL extract and store all inputs in the expression_rule_inputs table with parameter name, data type, description, and required flag
4. WHEN an Expression Rule is stored THEN the system SHALL create a corresponding entry in object_lookup using find_or_create to prevent duplicates
5. WHEN an Expression Rule exists in multiple packages THEN the system SHALL store one entry in object_lookup and separate version entries in object_versions for each package containing the rule

### Requirement 2: Record Types Not Being Extracted

**Defect Description:** The package extraction service fails to parse Record Type objects, resulting in no data being stored in the record_types, record_type_fields, record_type_relationships, record_type_views, or record_type_actions tables. During testing with real Appian packages, analysts discovered that Record Types (UUID: 57318b79-0bfd-45c4-a07e-ceae8277e0fb and others) were completely missing from the merge workflow despite being present in the uploaded packages. This prevents analysis of critical data model changes.

**User Story:** As a merge analyst, I need Record Types to be fully extracted with all their fields, relationships, views, and actions, so that I can understand data model changes and their impact on the application.

#### Acceptance Criteria

1. WHEN the system extracts Package A, B, or C containing Record Type XML files THEN the system SHALL parse all Record Type files and store each record type in the record_types table with complete metadata
2. WHEN a Record Type is parsed THEN the system SHALL extract and store all fields in the record_type_fields table with field name, data type, required flag, field configuration, and display order
3. WHEN a Record Type has relationships THEN the system SHALL extract and store all relationships in the record_type_relationships table with relationship type, target record type UUID, cardinality, and cascade behavior
4. WHEN a Record Type has views THEN the system SHALL extract and store all views in the record_type_views table with view name, view type, column configuration, and filter definitions
5. WHEN a Record Type has actions THEN the system SHALL extract and store all actions in the record_type_actions table with action name, action type, process model reference, and visibility rules
6. WHEN a Record Type is stored THEN the system SHALL create entries in object_lookup and object_versions following the standard no-duplication pattern

### Requirement 3: CDTs and Data Stores Not Being Extracted

**Defect Description:** The package extraction service does not process CDT (Custom Data Type) XSD files or Data Store XML files. The cdts, cdt_fields, data_stores, and data_store_entities tables remain empty after package extraction. During production testing, analysts reported that data structure changes were invisible in the merge workflow because CDTs defining the application's data model were not being extracted. This is a critical gap since CDTs are fundamental to Appian applications and changes to them often cause cascading impacts.

**User Story:** As a merge analyst, I need CDTs and Data Stores to be extracted with their complete field definitions and entity mappings, so that I can identify data structure conflicts and understand their impact on the application.

#### Acceptance Criteria

1. WHEN the system extracts Package A, B, or C containing CDT XSD files THEN the system SHALL parse all CDT files and store each CDT in the cdts table with namespace, name, and UUID
2. WHEN a CDT is parsed THEN the system SHALL extract and store all fields in the cdt_fields table with field name, data type, multiple flag, namespace, and field order
3. WHEN the system extracts Package A, B, or C containing Data Store XML files THEN the system SHALL parse all Data Store files and store each data store in the data_stores table
4. WHEN a Data Store is parsed THEN the system SHALL extract and store the data store name, UUID, description, database connection reference, and configuration
5. WHEN a Data Store has entity mappings THEN the system SHALL extract and store all entity mappings in the data_store_entities table with CDT references, table names, and column mappings

### Requirement 4: Comparison Results Not Being Stored in Database

**Defect Description:** The comparison services (delta_comparison_service.py and customer_comparison_service.py) compute detailed object differences but do not persist the results to the database. The object-specific comparison tables (interface_comparisons, process_model_comparisons, record_type_comparisons, expression_rule_comparisons, cdt_comparisons, constant_comparisons) remain empty after the merge workflow completes. This forces the system to re-compute comparisons every time an analyst views a change, causing performance issues and preventing historical analysis. Analysts reported that when they navigate away from a change and return to it, the comparison data is lost.

**User Story:** As a merge analyst, I need all comparison results to be persisted in the database after computation, so that I can review detailed differences quickly without re-computation and maintain a historical record of the analysis.

#### Acceptance Criteria

1. WHEN the system performs Interface comparison during delta or customer comparison THEN the system SHALL store results in the interface_comparisons table with SAIL code differences, parameter changes, security modifications, and diff metadata
2. WHEN the system performs Process Model comparison THEN the system SHALL store results in the process_model_comparisons table with node differences, flow changes, variable modifications, Mermaid diagrams for all three versions, and structural analysis
3. WHEN the system performs Record Type comparison THEN the system SHALL store results in the record_type_comparisons table with field changes, relationship modifications, view updates, action differences, and impact analysis
4. WHEN the system performs Expression Rule comparison THEN the system SHALL store results in the expression_rule_comparisons table with input parameter changes, return type modifications, and logic differences
5. WHEN the system performs CDT comparison THEN the system SHALL store results in the cdt_comparisons table with field type changes, field additions, field removals, and namespace modifications
6. WHEN the system performs Constant comparison THEN the system SHALL store results in the constant_comparisons table with value changes, type modifications, and old/new value pairs
7. WHEN comparison results are stored THEN the system SHALL link results to the session via session_id foreign key and to objects via object_id foreign key for efficient retrieval

### Requirement 5: Changes Table Only Stores Single Object ID

**Defect Description:** The changes table currently has only one object_id column, which stores the object from the delta comparison (A→C). This design flaw makes it impossible to track the customer's version of the object separately. When analysts view a CONFLICT classification, they cannot determine which specific customer object version is involved because the customer_object_id is not stored. This was discovered when analysts tried to compare "what the vendor changed" versus "what the customer changed" and found that the customer object reference was missing. The current schema forces complex joins through package_object_mappings to find customer objects, which is inefficient and error-prone.

**User Story:** As a merge analyst, I need the changes table to store both vendor_object_id and customer_object_id, so that I can directly access both versions involved in a conflict without complex joins.

#### Acceptance Criteria

1. WHEN a change record is created for a delta object THEN the system SHALL store the vendor_object_id column referencing the New Vendor version's object in object_lookup
2. WHEN a change record is created AND the object exists in the Customer package THEN the system SHALL store the customer_object_id column referencing the Customer version's object in object_lookup
3. WHEN a change record is created AND the object does not exist in the Customer package THEN the system SHALL set customer_object_id to NULL to indicate the object is NEW
4. WHEN the system queries changes for display THEN the system SHALL support joining to object_lookup twice using vendor_object_id and customer_object_id to retrieve both object details efficiently
5. WHEN the changes table schema is modified THEN the system SHALL maintain backward compatibility with existing classification, status, display_order, and notes fields without data loss

### Requirement 6: Merge Workflow UI Does Not Show Object Details

**Defect Description:** The merge workflow UI displays only basic object metadata (name, type, classification) but does not show the actual object details needed to understand what changed. Analysts reported that when reviewing a Constant conflict, they cannot see the constant values from each version. When reviewing an Interface conflict, they cannot see the SAIL code differences. When reviewing a Process Model conflict, they cannot see which nodes or flows changed. This forces analysts to manually open the XML files outside the application to understand changes, defeating the purpose of the merge assistant. The UI templates exist but are not wired to retrieve and display the detailed comparison data.

**User Story:** As a merge analyst, I need to see detailed object-specific information directly in the merge workflow UI, so that I can understand what changed and make informed merge decisions without leaving the application.

#### Acceptance Criteria

1. WHEN viewing a Constant change in the merge workflow THEN the system SHALL display the constant value from Base version, Customer version, and New Vendor version in a side-by-side comparison
2. WHEN viewing an Interface change THEN the system SHALL display SAIL code differences with syntax highlighting, line numbers, and side-by-side comparison showing additions, deletions, and modifications
3. WHEN viewing a Process Model change THEN the system SHALL display node differences, flow changes, variable modifications, and visual Mermaid diagrams for Base, Customer, and New Vendor versions
4. WHEN viewing an Expression Rule change THEN the system SHALL display input parameter differences, return type changes, and rule logic modifications in a structured format
5. WHEN viewing a Record Type change THEN the system SHALL display field modifications, relationship changes, view updates, and action differences with old and new values clearly marked
6. WHEN viewing a CDT change THEN the system SHALL display field type changes, field additions, field removals, and namespace modifications in a tabular format
7. WHEN viewing any object change THEN the system SHALL retrieve detailed comparison data from the appropriate object-specific comparison table and render it using the correct template

### Requirement 7: Process Model Nodes and Details Not Being Extracted

**Defect Description:** The Process Model parser extracts only the top-level process model metadata but fails to parse and store the structural details. The process_model_nodes, process_model_flows, and process_model_variables tables remain empty after package extraction. During testing with Process Models (UUIDs: de199b3f-b072-4438-9508-3b6594827eaf and 2c8de7e9-23b9-40d6-afc2-233a963832be), analysts discovered that while the process model object appeared in the merge workflow, they could not see which specific nodes changed, which flows were added or removed, or which variables were modified. This makes it impossible to assess the impact of process model changes and understand workflow modifications.

**User Story:** As a merge analyst, I need all Process Model structural details (nodes, flows, variables) to be extracted and stored, so that I can analyze workflow changes at a granular level and understand their business impact.

#### Acceptance Criteria

1. WHEN a Process Model is parsed THEN the system SHALL extract and store all nodes in the process_model_nodes table with node UUID, node name, node type, label, position coordinates, and configuration JSON
2. WHEN a Process Model is parsed THEN the system SHALL extract and store all flows in the process_model_flows table with flow UUID, source node UUID, target node UUID, condition expression, label, and flow type
3. WHEN a Process Model is parsed THEN the system SHALL extract and store all variables in the process_model_variables table with variable name, data type, multiple flag, default value, and parameter flag
4. WHEN Process Model nodes are stored THEN the system SHALL preserve node attributes including assignment configuration, escalation rules, form references, subprocess references, and timer settings
5. WHEN Process Model flows are stored THEN the system SHALL preserve flow conditions, exception handling paths, and conditional routing logic
6. WHEN the system compares Process Models THEN the system SHALL identify added nodes, removed nodes, modified nodes, added flows, removed flows, modified flows, added variables, removed variables, and modified variables
7. WHEN Process Model comparison results are stored THEN the system SHALL include node-level differences, flow-level differences, and variable-level differences in the process_model_comparisons table with detailed change descriptions

### Requirement 8: Inconsistent Parser Implementation Patterns

**Defect Description:** The existing object parsers (interface_parser.py, constant_parser.py, etc.) have inconsistent implementation patterns. Some parsers create object_lookup entries correctly while others skip this step. Some parsers store object_versions while others do not. The Expression Rule, Record Type, and CDT parsers are either missing entirely or incomplete. This inconsistency makes the codebase difficult to maintain and has directly contributed to the extraction failures described in Requirements 1-3. Code review revealed that parsers do not consistently use the find_or_create pattern, leading to potential duplicate object issues.

**User Story:** As a developer, I need all object parsers to follow a consistent, well-defined pattern, so that I can fix existing parsers, add missing parsers, and maintain the codebase effectively.

#### Acceptance Criteria

1. WHEN any object parser is implemented or updated THEN the system SHALL extend the BaseParser class and implement the parse method following the established pattern
2. WHEN a parser extracts object data THEN the system SHALL use the ObjectLookupRepository find_or_create method to prevent duplicate objects in object_lookup
3. WHEN a parser stores object-specific data THEN the system SHALL create entries in object_versions with package_id and object_id foreign keys to support multi-version tracking
4. WHEN a parser stores related entities THEN the system SHALL use foreign keys to link child records to parent objects and maintain referential integrity
5. WHEN a parser encounters malformed XML or parsing errors THEN the system SHALL log the error with object UUID and filename, continue processing remaining objects, and not fail the entire extraction process

### Requirement 9: Comparison Services Generate But Do Not Persist Detailed Diffs

**Defect Description:** The comparison services (delta_comparison_service.py and customer_comparison_service.py) contain logic to generate detailed diffs, but this logic is either incomplete or not being invoked. Code inspection revealed that while the services compute high-level change categories (MODIFIED, NEW, DEPRECATED), they do not generate line-by-line SAIL code diffs, field-level data structure changes, or node-level process model differences. Even when diff data is computed in memory, it is not persisted to the comparison tables. This was discovered when analysts reported that the UI showed "MODIFIED" but provided no details about what specifically changed.

**User Story:** As a merge analyst, I need comparison services to generate and persist detailed diff information for all object types, so that I can understand exactly what changed between versions and make informed merge decisions.

#### Acceptance Criteria

1. WHEN comparing SAIL code in Interfaces or Expression Rules THEN the system SHALL generate line-by-line differences with additions marked in green, deletions marked in red, and modifications marked in yellow
2. WHEN comparing structured data in Record Types or CDTs THEN the system SHALL identify field-level changes with old values, new values, and change type (added, removed, modified)
3. WHEN comparing Process Model nodes THEN the system SHALL match nodes by UUID, identify property changes, and generate node-level diff descriptions
4. WHEN comparing collections THEN the system SHALL identify added items, removed items, and modified items with detailed change descriptions for each
5. WHEN comparison results are generated THEN the system SHALL serialize results to JSON format and store them in the appropriate comparison table with session_id and object_id foreign keys for efficient retrieval

### Requirement 10: Missing Test Coverage for Extraction and Comparison Logic

**Defect Description:** The test suite does not adequately cover object extraction and comparison logic, which allowed the bugs in Requirements 1-9 to reach production. The existing tests in test_three_way_merge_orchestrator.py focus on high-level workflow orchestration but do not verify that Expression Rules, Record Types, CDTs, Process Model nodes, and comparison results are actually stored in the database. There are no property-based tests that validate extraction completeness across diverse package structures. This lack of test coverage means that when parsers fail to extract objects, the tests still pass, giving false confidence in the implementation.

**User Story:** As a developer, I need comprehensive property-based tests for all extraction and comparison logic, so that I can detect data completeness issues before they reach production and ensure correctness across diverse package structures.

#### Acceptance Criteria

1. WHEN testing object extraction with real packages THEN the system SHALL verify that all objects in the package are stored in object_lookup with correct UUID, name, and object_type
2. WHEN testing object extraction THEN the system SHALL verify that all object-specific details are stored in the appropriate tables (expression_rules, record_types, cdts, process_model_nodes, etc.)
3. WHEN testing comparison logic THEN the system SHALL verify that comparison results are stored for all delta objects in the appropriate comparison tables
4. WHEN testing the changes table after schema modification THEN the system SHALL verify that both vendor_object_id and customer_object_id are correctly populated based on object presence in packages
5. WHEN testing UI data retrieval THEN the system SHALL verify that all required object details can be retrieved from comparison tables and rendered in the UI without errors
