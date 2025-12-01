# Requirements Document

## Introduction

This document specifies the requirements for adding `package_id` foreign key columns to all object-specific tables in the NexusGen three-way merge system. Currently, object-specific tables (interfaces, expression_rules, process_models, etc.) store multiple entries for the same object when it appears in different packages, but there is no way to identify which package each entry belongs to. This creates ambiguity in queries and makes package-specific operations impossible.

## Glossary

- **Object-Specific Table**: Database tables that store detailed data for specific Appian object types (interfaces, expression_rules, process_models, record_types, cdts, integrations, web_apis, sites, groups, constants, connected_systems, data_stores, unknown_objects)
- **object_lookup**: Global registry table storing each unique object exactly once, package-agnostic
- **package_id**: Foreign key column linking an entry to its source package
- **Package**: A record in the packages table representing Base (A), Customized (B), or New Vendor (C) version
- **object_id**: Foreign key column linking to object_lookup table
- **Unique Constraint**: Database constraint ensuring no duplicate entries for the same object+package combination
- **Migration Script**: Python script that modifies database schema and migrates existing data
- **object_versions**: Table storing package-specific version data for objects
- **Referential Integrity**: Database constraint ensuring foreign keys reference valid records

## Requirements

### Requirement 1: Add package_id Column to Object-Specific Tables

**User Story:** As a developer, I want each entry in object-specific tables to be explicitly linked to its source package, so that I can query package-specific object data without ambiguity.

#### Acceptance Criteria

1. WHEN the migration runs THEN the system SHALL add a package_id column to all 13 main object-specific tables (interfaces, expression_rules, process_models, record_types, cdts, integrations, web_apis, sites, groups, constants, connected_systems, data_stores, unknown_objects)
2. WHEN adding the package_id column THEN the system SHALL define it as a foreign key referencing packages.id with ON DELETE CASCADE
3. WHEN adding the package_id column THEN the system SHALL initially allow NULL values to enable data migration
4. WHEN the package_id column is added THEN the system SHALL create an index on the column for query performance
5. WHEN the package_id column is added THEN the system SHALL NOT modify child tables (interface_parameters, process_model_nodes, etc.) as they inherit package context from their parent

### Requirement 2: Migrate Existing Data

**User Story:** As a system administrator, I want existing object-specific table entries to be populated with correct package_id values, so that no data is lost during the migration.

#### Acceptance Criteria

1. WHEN the migration populates package_id THEN the system SHALL use the object_versions table as the source of truth for matching object_id and version_uuid to package_id
2. WHEN populating package_id for an entry THEN the system SHALL query object_versions WHERE object_id matches AND version_uuid matches to find the correct package_id
3. WHEN the system cannot find a matching package_id THEN the system SHALL log a warning with the object details and skip that entry
4. WHEN all package_id values are populated THEN the system SHALL verify that no NULL values remain in the package_id column
5. WHEN verification passes THEN the system SHALL alter the package_id column to NOT NULL

### Requirement 3: Add Unique Constraints

**User Story:** As a database administrator, I want to prevent duplicate entries for the same object+package combination, so that data integrity is maintained.

#### Acceptance Criteria

1. WHEN the migration adds constraints THEN the system SHALL create a unique constraint on (object_id, package_id) for each object-specific table
2. WHEN creating the unique constraint THEN the system SHALL name it using the pattern 'uq_{table_name}_object_package'
3. WHEN the unique constraint is created THEN the system SHALL create a composite index on (object_id, package_id) for query optimization
4. WHEN the system attempts to insert a duplicate object+package combination THEN the database SHALL reject the insertion with a constraint violation error
5. WHEN querying by object_id and package_id THEN the system SHALL use the composite index for optimal performance

### Requirement 4: Update Package Extraction Service

**User Story:** As a developer, I want the package extraction service to pass package_id when storing object-specific data, so that new extractions populate the package_id column correctly.

#### Acceptance Criteria

1. WHEN the extraction service stores object-specific data THEN the system SHALL pass package_id as a parameter to all _store_*_data() methods
2. WHEN creating Interface records THEN the system SHALL include package_id in the Interface constructor
3. WHEN creating Expression Rule records THEN the system SHALL include package_id in the ExpressionRule constructor
4. WHEN creating Process Model records THEN the system SHALL include package_id in the ProcessModel constructor
5. WHEN creating any object-specific record THEN the system SHALL include package_id to satisfy the NOT NULL constraint

### Requirement 5: Update Object Repositories

**User Story:** As a developer, I want repository methods to accept and use package_id parameters, so that I can create and query package-specific object data.

#### Acceptance Criteria

1. WHEN creating an object-specific record THEN the repository create method SHALL accept package_id as a required parameter
2. WHEN the repository provides a get_by_object_and_package method THEN the system SHALL query using both object_id and package_id
3. WHEN the repository provides a get_all_by_object_id method THEN the system SHALL return all package versions of that object
4. WHEN querying without package_id THEN the system SHALL return all versions across all packages
5. WHEN querying with package_id THEN the system SHALL return only the version for that specific package

### Requirement 6: Update Export Scripts

**User Story:** As a user, I want export scripts to correctly identify which package version of an object is being exported, so that exported data is accurate and unambiguous.

#### Acceptance Criteria

1. WHEN exporting object details THEN the system SHALL accept an optional package_id parameter to specify which version to export
2. WHEN package_id is provided THEN the system SHALL query object-specific tables filtering by both object_id and package_id
3. WHEN package_id is not provided THEN the system SHALL export the first version found or all versions with package identification
4. WHEN exporting all versions THEN the system SHALL include package_type (base/customized/new_vendor) in the exported data
5. WHEN exporting session data THEN the system SHALL clearly identify which package each object version belongs to

### Requirement 7: Validate Data Integrity

**User Story:** As a database administrator, I want validation queries to verify data integrity after migration, so that I can confirm the migration was successful.

#### Acceptance Criteria

1. WHEN validation runs THEN the system SHALL verify that all object-specific entries have non-NULL package_id values
2. WHEN validation runs THEN the system SHALL verify that no duplicate (object_id, package_id) combinations exist
3. WHEN validation runs THEN the system SHALL verify that all package_id values reference valid packages
4. WHEN validation runs THEN the system SHALL verify that package_object_mappings entries exist for all (object_id, package_id) combinations in object-specific tables
5. WHEN validation runs THEN the system SHALL count objects per package and verify the distribution is reasonable

### Requirement 8: Update Test Suite

**User Story:** As a developer, I want all tests to be updated to use package_id correctly, so that the test suite validates the new schema.

#### Acceptance Criteria

1. WHEN tests create object-specific records THEN the system SHALL include package_id in the creation
2. WHEN tests query object-specific records THEN the system SHALL filter by both object_id and package_id
3. WHEN tests assert object existence THEN the system SHALL verify the package_id matches the expected package
4. WHEN property-based tests run THEN the system SHALL verify that package_id constraints are enforced
5. WHEN integration tests run THEN the system SHALL verify the complete workflow with package_id populated correctly

### Requirement 9: Performance Optimization

**User Story:** As a user, I want queries to remain fast after adding package_id, so that system performance is not degraded.

#### Acceptance Criteria

1. WHEN the migration creates indexes THEN the system SHALL create a composite index on (object_id, package_id) for each table
2. WHEN queries filter by object_id and package_id THEN the database SHALL use the composite index
3. WHEN queries filter by package_id only THEN the database SHALL use the package_id index
4. WHEN the migration completes THEN the system SHALL run ANALYZE to update query planner statistics
5. WHEN performance testing runs THEN the system SHALL verify that query times are within acceptable limits

### Requirement 10: Migration Script Structure

**User Story:** As a database administrator, I want a well-structured migration script that follows best practices, so that the migration is reliable and maintainable.

#### Acceptance Criteria

1. WHEN the migration script is created THEN the system SHALL name it migrations_004_add_package_id_to_objects.py
2. WHEN the migration script runs THEN the system SHALL use database transactions to ensure atomicity
3. WHEN the migration script encounters an error THEN the system SHALL rollback all changes and log the error
4. WHEN the migration script runs THEN the system SHALL log progress messages for each major step
5. WHEN the migration script completes THEN the system SHALL log a summary of changes made

### Requirement 11: Child Table Inheritance

**User Story:** As a developer, I want child tables to inherit package context from their parent tables, so that I don't need to add package_id to every child table.

#### Acceptance Criteria

1. WHEN querying child tables THEN the system SHALL join to the parent table to obtain package_id
2. WHEN the parent table has package_id THEN child tables SHALL NOT require their own package_id column
3. WHEN CASCADE DELETE is triggered on a parent THEN the system SHALL automatically delete all child records
4. WHEN querying interface_parameters THEN the system SHALL join to interfaces to filter by package_id
5. WHEN querying process_model_nodes THEN the system SHALL join to process_models to filter by package_id

### Requirement 12: Comparison Service Compatibility

**User Story:** As a developer, I want comparison services to work correctly with the new schema, so that three-way merge functionality is not disrupted.

#### Acceptance Criteria

1. WHEN delta comparison service queries objects THEN the system SHALL continue using object_versions for version-specific data
2. WHEN customer comparison service queries objects THEN the system SHALL use package_id to identify which package version to compare
3. WHEN merge guidance service generates recommendations THEN the system SHALL use package_id to retrieve correct object versions
4. WHEN comparison services need detailed object data THEN the system SHALL query object-specific tables with package_id filter
5. WHEN comparison results are stored THEN the system SHALL maintain compatibility with existing comparison result tables
