# Requirements Document

## Introduction

This document specifies the requirements for enhancing the Merge Assistant with a pre-merge assessment report generation feature and improved session summary interactions. The enhancement enables users to generate detailed Excel reports containing complexity analysis, time estimates, and change details before starting the merge workflow. Additionally, it improves the breakdown section with interactive object type filtering and restores the customer-only modifications metric.

## Glossary

- **Merge Assistant**: The three-way merge workflow system for Appian application upgrades
- **Session Summary Page**: The page displayed after uploading three packages showing merge statistics
- **Pre-Merge Assessment Report**: An Excel report generated before starting the merge workflow
- **Complexity**: A calculated metric (Low, Medium, High) based on object type and change magnitude
- **Estimated Time**: A calculated time estimate based on complexity thresholds
- **Breakdown Section**: The "Breakdown by Object Type" section showing object counts by category
- **Customer-Only Modifications**: Objects modified only in the customized package (B), not in vendor package (C)
- **Configuration File**: A centralized file storing all thresholds, labels, and calculation rules
- **Change Object**: An individual object that has been modified, added, or removed in the merge
- **SAIL Code**: Appian's expression language code
- **Object Type**: The category of Appian object (Interface, Expression Rule, Constant, Record Type, Process Model)
- **Classification**: The merge category (No Conflict, Conflicting, Deprecated, Customer-Only)

## Requirements

### Requirement 1

**User Story:** As a merge analyst, I want to generate a detailed Excel report from the Session Summary page, so that I can assess the merge effort before starting the workflow.

#### Acceptance Criteria

1. WHEN the Merge Assistant completes processing all three packages THEN the System SHALL display a "Generate Report" button at the top of the Session Summary page
2. WHEN a user clicks the "Generate Report" button THEN the System SHALL generate an Excel file containing all changed objects with their details
3. WHEN the Excel file is generated THEN the System SHALL include columns in this order: S. No, Category, Object Name, Object UUID, Change Description, Actual SAIL Change, Complexity, Estimated Time, Comments
4. WHEN the Excel file is generated THEN the System SHALL make the file available for download to the user
5. WHEN the report generation fails THEN the System SHALL display an error message to the user and log the failure details

### Requirement 2

**User Story:** As a merge analyst, I want complexity calculated based on object type and change magnitude, so that I can understand the difficulty of each change.

#### Acceptance Criteria

1. WHEN calculating complexity for Interface objects THEN the System SHALL classify changes with 1-20 lines as Low complexity
2. WHEN calculating complexity for Interface objects THEN the System SHALL classify changes with 21-60 lines as Medium complexity
3. WHEN calculating complexity for Interface objects THEN the System SHALL classify changes with more than 60 lines as High complexity
4. WHEN calculating complexity for Expression Rule objects THEN the System SHALL apply the same line-based thresholds as Interface objects
5. WHEN calculating complexity for Constant objects THEN the System SHALL always classify them as Low complexity
6. WHEN calculating complexity for Record Type objects THEN the System SHALL apply the same line-based thresholds as Interface objects
7. WHEN calculating complexity for Process Model objects THEN the System SHALL classify changes with 1-3 node modifications as Low complexity
8. WHEN calculating complexity for Process Model objects THEN the System SHALL classify changes with 4-8 node modifications as Medium complexity
9. WHEN calculating complexity for Process Model objects THEN the System SHALL classify changes with more than 8 node modifications as High complexity

### Requirement 3

**User Story:** As a merge analyst, I want estimated time calculated based on complexity, so that I can plan resource allocation for the merge.

#### Acceptance Criteria

1. WHEN calculating estimated time for Low complexity changes THEN the System SHALL assign 20 minutes per change
2. WHEN calculating estimated time for Medium complexity changes THEN the System SHALL assign 40 minutes per change
3. WHEN calculating estimated time for High complexity changes THEN the System SHALL assign 100 minutes per change
4. WHEN displaying estimated time in the report THEN the System SHALL format the time in minutes for values less than 60 minutes
5. WHEN displaying estimated time in the report THEN the System SHALL format the time in hours for values of 60 minutes or more

### Requirement 4

**User Story:** As a system administrator, I want all complexity and time thresholds stored in a configuration file, so that I can update them without modifying core logic.

#### Acceptance Criteria

1. THE System SHALL store all complexity thresholds in a single configuration file
2. THE System SHALL store all time estimate values in the same configuration file
3. THE System SHALL store all complexity labels (Low, Medium, High) in the configuration file
4. WHEN the configuration file is updated THEN the System SHALL apply the new values without requiring code changes
5. THE System SHALL validate configuration values on application startup and log any invalid entries

### Requirement 5

**User Story:** As a merge analyst, I want to see customer-only modifications as a metric on the Session Summary page, so that I can track all changes even if they are not in the merge workflow.

#### Acceptance Criteria

1. WHEN displaying the Session Summary page THEN the System SHALL show a metric card for customer-only modifications
2. WHEN calculating the customer-only modifications metric THEN the System SHALL count all objects modified only in the customized package
3. WHEN displaying the customer-only modifications metric THEN the System SHALL indicate that these changes are not included in the merge workflow
4. WHEN a user views the breakdown section THEN the System SHALL include customer-only modifications in the category tabs
5. THE System SHALL exclude customer-only modifications from the Start Merge workflow as per original design

### Requirement 6

**User Story:** As a merge analyst, I want to click on object type cards in the breakdown section, so that I can see a detailed list of objects of that type.

#### Acceptance Criteria

1. WHEN a user clicks an object type card in the breakdown section THEN the System SHALL display a grid below the cards showing objects of that type
2. WHEN the grid is displayed THEN the System SHALL show object name, UUID, classification, and complexity for each object
3. WHEN the grid contains more than 5 objects THEN the System SHALL implement pagination with page size of 5
4. WHEN the grid is displayed THEN the System SHALL show a close icon to hide the grid
5. WHEN a user clicks the close icon THEN the System SHALL hide the grid and return to the card view
6. WHEN a user clicks a different object type card THEN the System SHALL replace the current grid with objects of the newly selected type

### Requirement 7

**User Story:** As a merge analyst, I want the summary metrics to reflect the new complexity and time calculations, so that I see accurate estimates on the summary page.

#### Acceptance Criteria

1. WHEN displaying the Session Summary page THEN the System SHALL calculate Estimated Complexity using the new complexity rules
2. WHEN displaying the Session Summary page THEN the System SHALL calculate Estimated Time using the new time estimate rules
3. WHEN displaying the Session Summary page THEN the System SHALL position the Estimated Complexity and Estimated Time metrics at the top of the summary section
4. WHEN calculating summary metrics THEN the System SHALL aggregate complexity across all changes in the workflow
5. WHEN calculating summary metrics THEN the System SHALL sum estimated time across all changes in the workflow

### Requirement 8

**User Story:** As a developer, I want all new functionality to follow the existing OOP architecture, so that the codebase remains maintainable and consistent.

#### Acceptance Criteria

1. THE System SHALL implement all new services using the existing service class patterns
2. THE System SHALL reuse existing domain models without creating duplicate data structures
3. THE System SHALL reuse existing data loaders and repository patterns
4. THE System SHALL reuse existing UI components and styling patterns
5. THE System SHALL maintain separation of concerns between controllers, services, and repositories
6. THE System SHALL not modify or break the existing merge workflow functionality
7. THE System SHALL follow the same error handling patterns as existing services
8. THE System SHALL use the existing logging infrastructure for all new operations

### Requirement 9

**User Story:** As a merge analyst, I want the Excel report to include actual SAIL code changes, so that I can review the specific code modifications.

#### Acceptance Criteria

1. WHEN generating the Excel report for Interface objects THEN the System SHALL include the SAIL code differences in the "Actual SAIL Change" column
2. WHEN generating the Excel report for Expression Rule objects THEN the System SHALL include the SAIL code differences in the "Actual SAIL Change" column
3. WHEN generating the Excel report for objects without SAIL code THEN the System SHALL display a summary of field changes in the "Actual SAIL Change" column
4. WHEN SAIL code differences exceed 500 characters THEN the System SHALL truncate the text and append an ellipsis
5. WHEN no SAIL code changes exist for an object THEN the System SHALL display "No SAIL code changes" in the "Actual SAIL Change" column

### Requirement 10

**User Story:** As a merge analyst, I want the report to include change descriptions, so that I understand what was modified in each object.

#### Acceptance Criteria

1. WHEN generating the Excel report THEN the System SHALL populate the "Change Description" column with a human-readable summary
2. WHEN an object is added THEN the System SHALL describe it as "New object added in vendor release"
3. WHEN an object is modified THEN the System SHALL describe the specific fields or properties that changed
4. WHEN an object is removed THEN the System SHALL describe it as "Object removed in vendor release"
5. WHEN an object has conflicts THEN the System SHALL describe the conflicting changes from both vendor and customer
