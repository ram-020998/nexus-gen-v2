# Requirements Document

## Introduction

This specification defines enhancements to the Appian Analyzer's extraction and comparison capabilities. The current system performs preliminary XML extraction and basic object comparison. This enhancement will implement comprehensive XML extraction and adopt Appian's proven dual-layer comparison methodology (version history + content-based diff hashing) to provide more accurate and robust change detection.

## Glossary

- **Analyzer**: The Appian Application Analyzer system that parses Appian ZIP exports
- **Blueprint**: The JSON representation of an Appian application's structure and objects
- **Parser**: Component responsible for extracting data from XML files
- **Object Lookup**: UUID-to-name mapping table for all Appian objects
- **Version Comparator**: Component that compares two application versions
- **SAIL Code**: Appian's expression language used in interfaces, rules, and process models
- **Diff Hash**: SHA-512 hash of normalized XML content used for content comparison
- **Import Change Status**: Classification of object changes (NEW, CHANGED, CONFLICT_DETECTED, NOT_CHANGED, etc.)
- **Haul**: Container for transporting specific object types during import/export
- **UUID**: Universally Unique Identifier for Appian objects
- **Version UUID**: Unique identifier for a specific version of an object

## Requirements

### Requirement 1: Comprehensive XML Extraction

**User Story:** As a developer analyzing Appian applications, I want complete XML data extraction so that I can access all object metadata and properties for detailed analysis.

#### Acceptance Criteria

1. WHEN the Analyzer parses an XML file THEN the system SHALL extract all XML elements and attributes into the blueprint
2. WHEN storing extracted data THEN the system SHALL preserve the original XML structure in a normalized JSON format
3. WHEN an XML element contains nested structures THEN the system SHALL recursively extract all nested content
4. WHEN the blueprint is generated THEN the system SHALL include both the current extracted fields and a new "raw_xml_data" section containing complete XML content
5. WHEN comparing object sizes THEN the system SHALL handle XML files up to 10MB without performance degradation

### Requirement 2: Dual-Layer Object Comparison

**User Story:** As a deployment manager, I want accurate object change detection so that I can identify real modifications versus version-only changes.

#### Acceptance Criteria

1. WHEN comparing two application versions THEN the system SHALL implement version history comparison as the primary detection method
2. WHEN version UUIDs differ THEN the system SHALL perform content-based diff hash comparison as secondary validation
3. WHEN generating diff hashes THEN the system SHALL normalize XML content by removing version-specific metadata
4. WHEN both versions have identical content THEN the system SHALL classify the change as NOT_CHANGED_NEW_VUUID
5. WHEN content differs THEN the system SHALL classify the change as CHANGED or CONFLICT_DETECTED based on version history

### Requirement 3: Import Change Status Classification

**User Story:** As an analyst reviewing version differences, I want detailed change classifications so that I can understand the nature and impact of each modification.

#### Acceptance Criteria

1. WHEN an object exists only in the new version THEN the system SHALL classify it as NEW
2. WHEN an object's target version appears in the import history THEN the system SHALL classify it as CHANGED
3. WHEN an object's target version does not appear in the import history THEN the system SHALL classify it as CONFLICT_DETECTED
4. WHEN version UUIDs match exactly THEN the system SHALL classify it as NOT_CHANGED
5. WHEN version UUIDs differ but content hashes match THEN the system SHALL classify it as NOT_CHANGED_NEW_VUUID
6. WHEN an object exists only in the old version THEN the system SHALL classify it as REMOVED
7. WHEN version information is missing or incomplete THEN the system SHALL classify it as UNKNOWN

### Requirement 4: Version History Tracking

**User Story:** As a system administrator, I want version history tracking so that I can trace object evolution across deployments.

#### Acceptance Criteria

1. WHEN extracting objects THEN the system SHALL capture version history from XML metadata
2. WHEN storing version information THEN the system SHALL include version UUID, timestamp, and author for each version
3. WHEN comparing versions THEN the system SHALL use version history to determine if changes are legitimate updates
4. WHEN version history is unavailable THEN the system SHALL fall back to content-based comparison only
5. WHEN displaying comparison results THEN the system SHALL show version lineage for modified objects

### Requirement 5: Content Normalization for Diff Hash

**User Story:** As a developer, I want content-based comparison that ignores metadata changes so that I can focus on actual functional modifications.

#### Acceptance Criteria

1. WHEN generating diff hashes THEN the system SHALL remove version UUID elements from XML content
2. WHEN generating diff hashes THEN the system SHALL remove version history sections from XML content
3. WHEN generating diff hashes THEN the system SHALL remove XML schema attributes that don't affect functionality
4. WHEN generating diff hashes THEN the system SHALL use SHA-512 algorithm for hash generation
5. WHEN XML content exceeds 500KB THEN the system SHALL skip diff hash generation and rely on version comparison only

### Requirement 6: Enhanced Comparison Results

**User Story:** As a project manager, I want comprehensive comparison reports so that I can assess deployment risks and plan accordingly.

#### Acceptance Criteria

1. WHEN comparison completes THEN the system SHALL provide counts for each Import Change Status category
2. WHEN objects are modified THEN the system SHALL include both version information and content diff details
3. WHEN conflicts are detected THEN the system SHALL provide diagnostic information explaining the conflict
4. WHEN generating reports THEN the system SHALL include impact assessment based on object types and change patterns
5. WHEN displaying results THEN the system SHALL support filtering and sorting by change status, object type, and impact level

### Requirement 7: Parser Enhancement for Raw Data Storage

**User Story:** As a data analyst, I want access to complete raw XML data so that I can perform custom analysis beyond standard extraction.

#### Acceptance Criteria

1. WHEN parsers extract objects THEN the system SHALL store both structured data and raw XML content
2. WHEN storing raw XML THEN the system SHALL preserve original formatting and structure
3. WHEN the blueprint size exceeds reasonable limits THEN the system SHALL provide options to exclude raw XML data
4. WHEN accessing raw XML data THEN the system SHALL provide utility methods for querying and extracting specific elements
5. WHEN raw XML contains sensitive data THEN the system SHALL support optional redaction of specified fields

### Requirement 8: Performance Optimization for Large Applications

**User Story:** As a system operator, I want efficient processing of large applications so that analysis completes in reasonable time.

#### Acceptance Criteria

1. WHEN processing applications with 1000+ objects THEN the system SHALL complete analysis within 5 minutes
2. WHEN generating diff hashes THEN the system SHALL process objects in parallel where possible
3. WHEN memory usage exceeds thresholds THEN the system SHALL implement streaming processing for large objects
4. WHEN comparing versions THEN the system SHALL cache frequently accessed data to reduce redundant operations
5. WHEN analysis completes THEN the system SHALL report performance metrics including processing time and resource usage

### Requirement 9: Backward Compatibility

**User Story:** As an existing user, I want new features to work with existing blueprints so that I don't need to regenerate all my analysis data.

#### Acceptance Criteria

1. WHEN loading existing blueprints THEN the system SHALL continue to support the current JSON structure
2. WHEN new fields are added THEN the system SHALL provide default values for objects without those fields
3. WHEN comparison logic changes THEN the system SHALL maintain compatibility with existing comparison results
4. WHEN API endpoints are modified THEN the system SHALL support both old and new request/response formats
5. WHEN upgrading the system THEN the system SHALL provide migration utilities for existing data

### Requirement 10: Error Handling and Diagnostics

**User Story:** As a troubleshooting engineer, I want detailed error reporting so that I can quickly identify and resolve issues.

#### Acceptance Criteria

1. WHEN XML parsing fails THEN the system SHALL provide specific error messages indicating the file and line number
2. WHEN diff hash generation fails THEN the system SHALL log warnings and fall back to version-only comparison
3. WHEN version history is incomplete THEN the system SHALL report diagnostic warnings without failing the analysis
4. WHEN comparison encounters unexpected data THEN the system SHALL handle gracefully and report the issue
5. WHEN errors occur THEN the system SHALL include context information to aid in debugging
