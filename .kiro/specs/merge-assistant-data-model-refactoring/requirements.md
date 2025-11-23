# Requirements Document

## Introduction

The Merge Assistant feature currently stores all data in two main tables: `MergeSession` and `ChangeReview`. While functional, this design has several issues:

1. **Denormalization**: Large JSON blobs are stored in TEXT columns (blueprints, comparison results, classification results, ordered changes)
2. **Inefficient Queries**: Filtering and searching requires parsing JSON strings
3. **Data Redundancy**: Object information is duplicated across multiple JSON structures
4. **Scalability Issues**: Large merge sessions create massive database rows
5. **Maintenance Complexity**: Changes to data structure require JSON parsing/serialization throughout the codebase

This refactoring will normalize the database schema while maintaining backward compatibility and ensuring no existing functionality is affected.

## Glossary

- **MergeSession**: A three-way merge analysis session comparing base (A), customized (B), and new vendor (C) Appian packages
- **Blueprint**: Complete analysis result of an Appian package including all objects and metadata
- **Object**: An Appian application component (Interface, Process Model, Record Type, etc.)
- **Change**: A modification detected between package versions (ADDED, MODIFIED, REMOVED)
- **Classification**: Categorization of changes (NO_CONFLICT, CONFLICT, CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED)
- **Dependency**: Relationship between Appian objects where one references another
- **Review**: User action on a change (reviewed, skipped, pending)
- **Normalization**: Database design principle of organizing data to reduce redundancy
- **Migration**: Process of transforming existing data to new schema structure

## Requirements

### Requirement 1

**User Story:** As a developer, I want the database schema to be normalized, so that queries are efficient and data is not duplicated.

#### Acceptance Criteria

1. WHEN storing blueprint data THEN the system SHALL create separate tables for packages, objects, and metadata
2. WHEN storing comparison results THEN the system SHALL create separate tables for changes with proper foreign key relationships
3. WHEN storing classification results THEN the system SHALL use normalized tables instead of JSON blobs
4. WHEN querying objects THEN the system SHALL use SQL joins instead of JSON parsing
5. WHEN storing dependencies THEN the system SHALL create a separate relationship table with proper indexing

### Requirement 2

**User Story:** As a system administrator, I want to migrate existing data safely, so that no information is lost during the refactoring.

#### Acceptance Criteria

1. WHEN migration starts THEN the system SHALL create a backup of existing data
2. WHEN migrating sessions THEN the system SHALL preserve all session metadata and relationships
3. WHEN migrating blueprints THEN the system SHALL extract and normalize all JSON data
4. WHEN migrating changes THEN the system SHALL maintain the correct ordering and classification
5. WHEN migration completes THEN the system SHALL verify data integrity by comparing record counts
6. IF migration fails THEN the system SHALL rollback changes and restore from backup

### Requirement 3

**User Story:** As a user, I want all existing functionality to work exactly as before the refactoring, so that the changes are transparent to me.

#### Acceptance Criteria

1. WHEN viewing merge sessions THEN the system SHALL display the same information as before refactoring
2. WHEN navigating changes THEN the system SHALL maintain the same ordering and filtering capabilities
3. WHEN reviewing changes THEN the system SHALL record actions with the same behavior
4. WHEN generating reports THEN the system SHALL produce identical output format
5. WHEN exporting data THEN the system SHALL include all the same information

### Requirement 4

**User Story:** As a developer, I want improved query performance, so that large merge sessions load faster.

#### Acceptance Criteria

1. WHEN filtering changes by classification THEN the system SHALL use indexed columns instead of JSON parsing
2. WHEN searching by object name THEN the system SHALL use SQL LIKE queries on indexed columns
3. WHEN loading change details THEN the system SHALL use JOIN queries instead of multiple JSON deserializations
4. WHEN counting statistics THEN the system SHALL use aggregate SQL queries instead of loading all data
5. WHEN querying dependencies THEN the system SHALL use indexed foreign keys for efficient lookups

### Requirement 5

**User Story:** As a database administrator, I want proper indexing and constraints, so that data integrity is maintained automatically.

#### Acceptance Criteria

1. WHEN creating tables THEN the system SHALL define foreign key constraints for all relationships
2. WHEN inserting objects THEN the system SHALL enforce unique constraints on UUID fields
3. WHEN querying frequently THEN the system SHALL use indexes on commonly filtered columns
4. WHEN deleting sessions THEN the system SHALL cascade delete all related records automatically
5. WHEN updating records THEN the system SHALL maintain referential integrity through constraints

### Requirement 6

**User Story:** As a developer, I want clear separation of concerns, so that blueprint data, comparison data, and review data are independent.

#### Acceptance Criteria

1. WHEN storing packages THEN the system SHALL create separate Package table with metadata
2. WHEN storing objects THEN the system SHALL create separate AppianObject table linked to packages
3. WHEN storing changes THEN the system SHALL create separate Change table linked to objects
4. WHEN storing reviews THEN the system SHALL keep ChangeReview table but link to Change table
5. WHEN storing dependencies THEN the system SHALL create separate ObjectDependency table

### Requirement 7

**User Story:** As a developer, I want comprehensive tests, so that I can verify the refactoring doesn't break existing functionality.

#### Acceptance Criteria

1. WHEN running tests THEN the system SHALL verify all CRUD operations work on new schema
2. WHEN running tests THEN the system SHALL verify migration produces correct data
3. WHEN running tests THEN the system SHALL verify backward compatibility layer works
4. WHEN running tests THEN the system SHALL verify query performance improvements
5. WHEN running tests THEN the system SHALL verify all API endpoints return correct data

### Requirement 8

**User Story:** As a developer, I want the new schema to support future enhancements, so that we can add features without major refactoring.

#### Acceptance Criteria

1. WHEN designing tables THEN the system SHALL use extensible structure for adding new object types
2. WHEN designing tables THEN the system SHALL support additional metadata fields without schema changes
3. WHEN designing tables THEN the system SHALL allow for versioning of objects and changes
4. WHEN designing tables THEN the system SHALL support audit trails for user actions
5. WHEN designing tables THEN the system SHALL enable efficient reporting and analytics queries
