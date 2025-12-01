# Requirements Document

## Introduction

This document specifies the requirements for rebuilding the three-way merge functionality from scratch. The current implementation has fundamental architectural flaws including data duplication, inconsistent references, and poor separation of concerns. This rebuild will create a clean, maintainable architecture following proper OOP design patterns.

## Glossary

- **Package A**: Vendor Base Version - the original vendor package before any customizations
- **Package B**: Customer Customized Version - the package with customer modifications applied to Package A
- **Package C**: Vendor New Version - the latest vendor package with vendor updates
- **Delta**: The set of changes between Package A and Package C (A→C comparison)
- **Working Set**: The classified set of delta objects that require user review
- **Object Lookup**: Global registry table storing each unique object exactly once
- **Package Object Mapping**: Junction table tracking which objects belong to which packages
- **Classification**: The categorization of a change (NO_CONFLICT, CONFLICT, NEW, DELETED)
- **Change Category**: The type of delta change (NEW, MODIFIED, DEPRECATED)
- **SAIL Code**: Appian's expression language code
- **UUID**: Universally Unique Identifier for Appian objects
- **Version UUID**: UUID representing a specific version of an object

## Requirements

### Requirement 1: Upload Packages and Create Session

**User Story:** As a user, I want to upload three Appian packages to create a merge session, so that the system can analyze the differences and prepare a working set for review.

#### Acceptance Criteria

1. WHEN a user accesses the merge upload page THEN the system SHALL display three file upload fields with drag-and-drop support labeled "Base Package (A)", "Customized Package (B)", and "New Vendor Package (C)"
2. WHEN a user selects three ZIP files THEN the system SHALL enable the "Start Analysis" button
3. WHEN a user clicks "Start Analysis" THEN the system SHALL validate that all three files are Appian package ZIP files
4. WHEN the system validates the files THEN the system SHALL create a merge session with a unique reference_id and status='PROCESSING'
5. WHEN the system creates a merge session THEN the system SHALL redirect the user to the session summary page and process the packages asynchronously

### Requirement 1a: View Sessions List

**User Story:** As a user, I want to view a list of all merge sessions, so that I can access previous sessions and track their status.

#### Acceptance Criteria

1. WHEN a user navigates to the sessions page THEN the system SHALL display all merge sessions ordered by creation date (newest first)
2. WHEN the system displays sessions THEN the system SHALL show reference_id, status badge, creation date, total changes count, and action buttons for each session
3. WHEN the system displays sessions THEN the system SHALL provide filter buttons (All, Ready, In Progress, Completed, Error)
4. WHEN a user clicks a filter button THEN the system SHALL show only sessions matching that status
5. WHEN the system displays sessions THEN the system SHALL provide a "New Merge Session" button to create a new session
6. WHEN a user clicks "View Summary" on a session THEN the system SHALL navigate to that session's summary page

### Requirement 1b: View Session Summary

**User Story:** As a user, I want to view a summary of the merge session after packages are processed, so that I can understand the scope of changes before starting the review workflow.

#### Acceptance Criteria

1. WHEN a user views the session summary THEN the system SHALL display session metadata (reference_id, created date, status badge, package names with labels A/B/C)
2. WHEN the system displays the summary THEN the system SHALL show four statistic cards (Total Changes, No Conflicts, Conflicts, Customer Only) with icons and counts
3. WHEN the system displays the summary THEN the system SHALL show package information section with three columns displaying filename and object count for each package
4. WHEN the system displays the summary THEN the system SHALL show "What's in the Merge Workflow?" info panel explaining what changes are included
5. WHEN the system displays the summary THEN the system SHALL show estimated complexity (Low/Medium/High) and estimated time based on change analysis
6. WHEN the system displays the summary THEN the system SHALL show breakdown by object type with expandable sections and counts
7. WHEN the system displays the summary THEN the system SHALL show tabs for filtering by classification (No Conflicts, Conflicts, Customer Only)
8. WHEN the session status is 'READY' or 'IN_PROGRESS' THEN the system SHALL display a "Start Merge Workflow" button
9. WHEN the system displays the summary THEN the system SHALL provide a "Back to Sessions" button
10. WHEN the system displays the summary THEN the system SHALL show breadcrumb navigation (Home > Merge Assistant > Session Reference ID)

### Requirement 1c: Start Guided Merge Workflow

**User Story:** As a user, I want to start a guided merge workflow from the session summary, so that I can review each change step-by-step and make merge decisions.

#### Acceptance Criteria

1. WHEN a user clicks "Start Merge Workflow" from the session summary THEN the system SHALL navigate to the first change in the working set
2. WHEN the system starts the workflow THEN the system SHALL update the session status to 'IN_PROGRESS'
3. WHEN the system displays a change THEN the system SHALL show progress indicator with percentage and "Change X of Y" text
4. WHEN the system displays a change THEN the system SHALL show object icon, name, type badge, classification badge, and review status badge
5. WHEN the system displays a change THEN the system SHALL show breadcrumb navigation (Home > Merge Assistant > Session ID > Change X of Y)
6. WHEN the system displays a change THEN the system SHALL provide a "Jump to Change" dropdown to navigate to any change directly

### Requirement 1c: Review Individual Changes

**User Story:** As a user, I want to review each change individually with detailed object-specific comparison information, so that I can make informed merge decisions.

#### Acceptance Criteria

1. WHEN a user views a change detail page THEN the system SHALL display the object name, type, classification, and current review status
2. WHEN a user views a change detail page THEN the system SHALL display object-specific comparison based on object type (see Requirement 1e)
3. WHEN a user views a change detail page THEN the system SHALL provide a notes textbox for adding merge decisions or concerns
4. WHEN a user views a change detail page THEN the system SHALL provide quick actions (Mark as Reviewed, Skip, Save Notes)
5. WHEN a user views a change detail page THEN the system SHALL provide navigation (Previous, Next, Back to Summary)

### Requirement 1e: Object-Specific Comparison Display

**User Story:** As a user, I want to see detailed comparisons tailored to each object type, so that I can understand exactly what changed in a format appropriate for that object.

#### Acceptance Criteria

1. WHEN viewing an Interface change THEN the system SHALL display SAIL code side-by-side diff, parameters added/removed/modified, and security changes
2. WHEN viewing an Expression Rule change THEN the system SHALL display SAIL code diff, inputs added/removed/modified, and output type changes
3. WHEN viewing a Process Model change THEN the system SHALL display summary statistics, Mermaid diagram with tabs (Base/Customer/Vendor/Diff), nodes added/removed/modified, flows added/removed/modified, and variables changed
4. WHEN viewing a Record Type change THEN the system SHALL display fields added/removed/modified, relationships added/removed, views modified, and actions added/removed
5. WHEN viewing a CDT change THEN the system SHALL display namespace changes and fields added/removed/modified with type and list indicators

### Requirement 1f: Additional Object Type Comparisons

**User Story:** As a user, I want to see appropriate comparisons for all Appian object types, so that I can review changes regardless of object type.

#### Acceptance Criteria

1. WHEN viewing an Integration change THEN the system SHALL display SAIL code diff, connection changes, authentication changes, and endpoint changes
2. WHEN viewing a Web API change THEN the system SHALL display SAIL code diff, endpoint changes, and HTTP methods (GET, POST, PUT, DELETE)
3. WHEN viewing a Site change THEN the system SHALL display page hierarchy tree view with added/removed/modified pages
4. WHEN viewing a Group change THEN the system SHALL display members added/removed and parent group changes
5. WHEN viewing a Constant change THEN the system SHALL display value before/after, type changes, and scope changes

### Requirement 1d: Navigate Through Working Set

**User Story:** As a user, I want to navigate through the working set sequentially, so that I can review all changes systematically.

#### Acceptance Criteria

1. WHEN a user clicks "Next" THEN the system SHALL navigate to the next change in the working set
2. WHEN a user clicks "Previous" THEN the system SHALL navigate to the previous change in the working set
3. WHEN a user is on the first change THEN the system SHALL disable the "Previous" button
4. WHEN a user is on the last change THEN the system SHALL change "Next" button to "Complete Review"
5. WHEN a user clicks "Back to Summary" THEN the system SHALL return to the session summary page preserving review progress

### Requirement 2: Package Upload and Extraction

**User Story:** As a system, I want to extract and parse all objects from uploaded packages, so that I can store them without duplication for comparison.

#### Acceptance Criteria

1. WHEN the system receives three package ZIP files THEN the system SHALL extract all XML files from each package
2. WHEN the system extracts packages THEN the system SHALL parse each XML file to identify object type, UUID, name, and version
3. WHEN the system parses objects THEN the system SHALL store each unique object exactly once in the object_lookup table
4. WHEN the system stores objects THEN the system SHALL create package_object_mappings to track which objects belong to which packages
5. WHEN the system encounters an object that already exists THEN the system SHALL reuse the existing object_lookup entry and create only the mapping

### Requirement 3: Global Object Registry

**User Story:** As a system architect, I want a single source of truth for all objects, so that there is no data duplication and objects can be referenced consistently.

#### Acceptance Criteria

1. THE system SHALL maintain an object_lookup table with no package_id column
2. WHEN storing an object THEN the system SHALL ensure each UUID appears exactly once in object_lookup
3. WHEN an object exists in multiple packages THEN the system SHALL create separate package_object_mappings entries for each package
4. WHEN querying objects in a package THEN the system SHALL join object_lookup with package_object_mappings
5. THE system SHALL enforce referential integrity with foreign key constraints and CASCADE deletes

### Requirement 4: Delta Comparison (A→C)

**User Story:** As a user, I want the system to identify what changed in the vendor package, so that I know what vendor updates are available.

#### Acceptance Criteria

1. WHEN the system compares Package A to Package C THEN the system SHALL identify all NEW objects (in C but not in A)
2. WHEN the system compares Package A to Package C THEN the system SHALL identify all MODIFIED objects (in both but with differences)
3. WHEN the system compares Package A to Package C THEN the system SHALL identify all DEPRECATED objects (in A but not in C)
4. WHEN the system detects a MODIFIED object THEN the system SHALL determine if the version changed and if the content changed
5. WHEN the system completes delta comparison THEN the system SHALL store all results in delta_comparison_results table

### Requirement 5: Customer Comparison (Delta vs B)

**User Story:** As a user, I want the system to check if I modified the same objects that the vendor changed, so that I can identify potential conflicts.

#### Acceptance Criteria

1. WHEN the system analyzes delta objects THEN the system SHALL check if each object exists in Package B
2. WHEN an object exists in Package B THEN the system SHALL compare it to Package A to detect customer modifications
3. WHEN comparing objects THEN the system SHALL check both version changes and content changes
4. WHEN the system detects customer modifications THEN the system SHALL record the modification status for classification
5. THE system SHALL only analyze objects that appear in the delta (not all objects in Package B)

### Requirement 6: Classification Rules

**User Story:** As a user, I want the system to automatically classify changes, so that I can focus on conflicts and understand what can be auto-merged.

#### Acceptance Criteria

1. WHEN an object is NEW in the delta THEN the system SHALL classify it as NEW
2. WHEN an object is MODIFIED in the delta AND not modified by customer THEN the system SHALL classify it as NO_CONFLICT
3. WHEN an object is MODIFIED in the delta AND modified by customer THEN the system SHALL classify it as CONFLICT
4. WHEN an object is MODIFIED in the delta AND removed by customer THEN the system SHALL classify it as DELETED
5. WHEN an object is DEPRECATED in the delta AND not modified by customer THEN the system SHALL classify it as NO_CONFLICT
6. WHEN an object is DEPRECATED in the delta AND modified by customer THEN the system SHALL classify it as CONFLICT
7. WHEN an object is DEPRECATED in the delta AND removed by customer THEN the system SHALL classify it as NO_CONFLICT

### Requirement 7: Working Set Generation

**User Story:** As a user, I want to see only the changes that require my attention, so that I can efficiently review and make merge decisions.

#### Acceptance Criteria

1. WHEN the system generates the working set THEN the system SHALL include only objects from the delta
2. WHEN the system creates change records THEN the system SHALL reference object_lookup via object_id
3. WHEN the system creates change records THEN the system SHALL store classification, vendor_change_type, and customer_change_type
4. WHEN the system generates the working set THEN the system SHALL assign display_order for consistent presentation
5. THE system SHALL ensure the count of delta_comparison_results equals the count of changes for each session

### Requirement 8: Object-Specific Data Extraction

**User Story:** As a user, I want complete object data extracted from XML files, so that I can see detailed comparisons and make informed decisions.

#### Acceptance Criteria

1. WHEN parsing Interface objects THEN the system SHALL extract UUID, name, version, SAIL code, parameters, and security settings
2. WHEN parsing Process Model objects THEN the system SHALL extract UUID, name, version, nodes, flows, variables, and calculate complexity
3. WHEN parsing Record Type objects THEN the system SHALL extract UUID, name, version, fields, relationships, views, and actions
4. WHEN parsing Expression Rule objects THEN the system SHALL extract UUID, name, version, SAIL code, output type, and inputs
5. WHEN parsing CDT objects THEN the system SHALL extract UUID, name, version, namespace, and field definitions
6. WHEN parsing any object with SAIL code THEN the system SHALL clean and normalize the SAIL code for comparison

### Requirement 9: Detailed Comparison Storage

**User Story:** As a user, I want to see detailed differences for each changed object, so that I understand exactly what changed and can make informed merge decisions.

#### Acceptance Criteria

1. WHEN comparing Interface objects THEN the system SHALL identify SAIL code differences, parameter changes, and security changes
2. WHEN comparing Process Model objects THEN the system SHALL identify node changes, flow changes, and variable changes
3. WHEN comparing Record Type objects THEN the system SHALL identify field changes, relationship changes, view changes, and action changes
4. WHEN the system identifies differences THEN the system SHALL store them in object-specific comparison tables
5. WHEN the system stores comparisons THEN the system SHALL link them to the changes table via change_id

### Requirement 10: Session Management

**User Story:** As a user, I want to save my merge session and resume later, so that I can work on complex merges over multiple sessions.

#### Acceptance Criteria

1. WHEN a user starts a merge THEN the system SHALL create a merge_session with a unique reference_id
2. WHEN the system processes packages THEN the system SHALL update session status (PROCESSING, READY, IN_PROGRESS, COMPLETED, ERROR)
3. WHEN the system completes extraction and classification THEN the system SHALL store total_changes count in the session
4. WHEN a user returns to a session THEN the system SHALL retrieve all session data from the database
5. THE system SHALL maintain referential integrity by cascading deletes when a session is removed

### Requirement 11: Repository Pattern Implementation

**User Story:** As a developer, I want all database access through repositories, so that the codebase is maintainable and testable.

#### Acceptance Criteria

1. THE system SHALL implement a BaseRepository with standard CRUD operations
2. THE system SHALL implement ObjectLookupRepository with find_or_create method to prevent duplicates
3. THE system SHALL implement PackageObjectMappingRepository with bulk operations for performance
4. THE system SHALL implement DeltaComparisonRepository with session-based queries
5. THE system SHALL implement ChangeRepository with classification-based filtering

### Requirement 12: Service Layer Architecture

**User Story:** As a developer, I want business logic in service classes, so that the code is organized and follows single responsibility principle.

#### Acceptance Criteria

1. THE system SHALL implement PackageExtractionService to handle package parsing and storage
2. THE system SHALL implement DeltaComparisonService to handle A→C comparison logic
3. THE system SHALL implement CustomerComparisonService to handle delta vs B comparison logic
4. THE system SHALL implement ClassificationService to apply the 7 classification rules
5. THE system SHALL implement ThreeWayMergeOrchestrator to coordinate the entire workflow

### Requirement 13: Parser Architecture

**User Story:** As a developer, I want dedicated parsers for each object type, so that all object data is extracted correctly and consistently.

#### Acceptance Criteria

1. THE system SHALL implement a BaseParser with common XML parsing utilities
2. THE system SHALL implement InterfaceParser to extract all Interface-specific data
3. THE system SHALL implement ProcessModelParser to extract all Process Model-specific data
4. THE system SHALL implement RecordTypeParser to extract all Record Type-specific data
5. THE system SHALL implement parsers for all other Appian object types (Expression Rules, CDTs, Integrations, Web APIs, Sites, Groups, Constants, Connected Systems)

### Requirement 14: Data Integrity and Validation

**User Story:** As a system administrator, I want the system to maintain data integrity, so that the database remains consistent and reliable.

#### Acceptance Criteria

1. THE system SHALL enforce unique constraint on object_lookup.uuid
2. THE system SHALL enforce unique constraint on package_object_mappings (package_id, object_id)
3. THE system SHALL enforce unique constraint on delta_comparison_results (session_id, object_id)
4. THE system SHALL enforce CHECK constraints on classification and change_category enums
5. THE system SHALL provide validation queries to detect duplicates and verify delta-driven working set

### Requirement 15: Performance Optimization

**User Story:** As a user, I want fast query performance, so that I can work efficiently with large packages.

#### Acceptance Criteria

1. THE system SHALL create indexes on object_lookup (uuid, name, object_type)
2. THE system SHALL create indexes on package_object_mappings (package_id, object_id)
3. THE system SHALL create indexes on delta_comparison_results (session_id, change_category)
4. THE system SHALL create indexes on changes (session_id, classification, display_order)
5. THE system SHALL use bulk operations for inserting multiple records

### Requirement 16: Testing with Real Packages

**User Story:** As a developer, I want to test with real Appian packages, so that I can verify the system works with actual data.

#### Acceptance Criteria

1. WHEN running tests THEN the system SHALL use packages from applicationArtifacts/Three Way Testing Files/V2/
2. WHEN testing extraction THEN the system SHALL verify no duplicates in object_lookup
3. WHEN testing delta comparison THEN the system SHALL verify all change categories are identified
4. WHEN testing classification THEN the system SHALL verify all 7 rules are applied correctly
5. WHEN testing end-to-end THEN the system SHALL verify delta_count equals change_count
