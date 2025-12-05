# Requirements Document

## Introduction

This document specifies the requirements for enhancing the three-way merge application UI to match the functionality and user experience of the legacy version (port 5000). The current rebuild (port 5002) has basic functionality but lacks several critical features including detailed change navigation, progress tracking, action buttons, and comprehensive session management.

## Glossary

- **Three-Way Merge System**: The application that analyzes three Appian packages (Base, Customized, New Vendor) to identify conflicts and generate merge guidance
- **Merge Session**: A single analysis instance containing three packages and their comparison results
- **Working Set**: The collection of changes that require review in a merge session
- **Change**: A single object that has been modified, added, or deleted between package versions
- **Classification**: The categorization of a change (NO_CONFLICT, CONFLICT, NEW, DELETED)
- **Change Detail View**: A page showing comprehensive information about a single change with navigation controls
- **Summary Page**: An overview page showing session statistics, package information, and breakdown by object type
- **Workflow Page**: A page listing all changes in the working set for review
- **Sessions Page**: A page listing all merge sessions with filtering and search capabilities

## Requirements

### Requirement 1

**User Story:** As a merge reviewer, I want to navigate through changes one at a time with detailed information, so that I can systematically review each change in the merge workflow.

#### Acceptance Criteria

1. WHEN a user clicks on a change in the workflow page THEN the system SHALL display a dedicated change detail page showing comprehensive information about that specific change
2. WHEN viewing a change detail page THEN the system SHALL display the change's position in the workflow (e.g., "Change 1 of 6")
3. WHEN viewing a change detail page THEN the system SHALL provide Previous and Next navigation buttons to move between changes
4. WHEN a user is on the first change THEN the system SHALL disable the Previous button
5. WHEN a user is on the last change THEN the system SHALL disable the Next button
6. WHEN viewing a change detail page THEN the system SHALL display a progress indicator showing percentage completion (e.g., "16%")

### Requirement 2

**User Story:** As a merge reviewer, I want to see detailed change information including SAIL code and version-specific data, so that I can understand exactly what changed between versions.

#### Acceptance Criteria

1. WHEN viewing a change detail page for an object with SAIL code THEN the system SHALL display the full SAIL code from the vendor version
2. WHEN viewing a change detail page THEN the system SHALL display the object's classification badge (NO_CONFLICT, CONFLICT, NEW, DELETED)
3. WHEN viewing a change detail page THEN the system SHALL display the vendor change type (MODIFIED, NEW, DEPRECATED)
4. WHEN viewing a change detail page THEN the system SHALL display the customer change type when applicable
5. WHEN viewing a change detail page THEN the system SHALL display the object's description and UUID

### Requirement 3

**User Story:** As a merge reviewer, I want to mark changes as reviewed or skipped and add notes, so that I can track my progress and document merge decisions.

#### Acceptance Criteria

1. WHEN viewing a change detail page THEN the system SHALL provide a "Mark as Reviewed" button
2. WHEN viewing a change detail page THEN the system SHALL provide a "Skip" button
3. WHEN viewing a change detail page THEN the system SHALL provide a notes textarea for adding comments
4. WHEN viewing a change detail page THEN the system SHALL provide a "Save Notes" button
5. WHEN a user clicks "Mark as Reviewed" THEN the system SHALL update the change status and increment the reviewed count
6. WHEN a user clicks "Skip" THEN the system SHALL update the change status and increment the skipped count
7. WHEN a user clicks "Save Notes" THEN the system SHALL persist the notes to the database

### Requirement 4

**User Story:** As a merge reviewer, I want to see session progress information on the change detail page, so that I can track how many changes I have reviewed and skipped.

#### Acceptance Criteria

1. WHEN viewing a change detail page THEN the system SHALL display a session info panel showing the session reference ID
2. WHEN viewing a change detail page THEN the system SHALL display the current session status
3. WHEN viewing a change detail page THEN the system SHALL display the count of reviewed changes
4. WHEN viewing a change detail page THEN the system SHALL display the count of skipped changes
5. WHEN the session status or counts change THEN the system SHALL update the display without requiring a page refresh

### Requirement 5

**User Story:** As a merge reviewer, I want to see a comprehensive summary page with statistics and breakdowns, so that I can understand the scope of the merge before starting.

#### Acceptance Criteria

1. WHEN viewing the summary page THEN the system SHALL display package information for all three packages (Base, Customized, New Vendor)
2. WHEN viewing the summary page THEN the system SHALL display the total count of changes
3. WHEN viewing the summary page THEN the system SHALL display counts broken down by classification (NO_CONFLICT, CONFLICT, NEW, DELETED)
4. WHEN viewing the summary page THEN the system SHALL display a breakdown by object type with expandable sections
5. WHEN a user clicks on an object type in the breakdown THEN the system SHALL expand and display a grid showing all objects of that type with columns for object name, UUID, classification, and complexity
6. WHEN viewing the summary page THEN the system SHALL display estimated complexity and time metrics
7. WHEN viewing the summary page THEN the system SHALL provide a "Start Merge Workflow" button that navigates to the first change
8. WHEN viewing the summary page THEN the system SHALL display a "What's in the Merge Workflow?" explanation section

### Requirement 6

**User Story:** As a merge reviewer, I want to filter and search sessions on the sessions page, so that I can quickly find specific merge sessions.

#### Acceptance Criteria

1. WHEN viewing the sessions page THEN the system SHALL provide status filter buttons (All, Processing, Ready, In Progress, Completed, Error)
2. WHEN viewing the sessions page THEN the system SHALL provide a search input field
3. WHEN a user clicks a status filter button THEN the system SHALL display only sessions matching that status
4. WHEN a user types in the search field THEN the system SHALL filter sessions by reference ID or package names
5. WHEN viewing the sessions page THEN the system SHALL provide a sort dropdown with options (Newest First, Oldest First, Reference ID A-Z, Reference ID Z-A, Status A-Z)
6. WHEN a user selects a sort option THEN the system SHALL reorder the sessions accordingly
7. WHEN viewing the sessions page THEN the system SHALL display a "Clear Filters" button that resets all filters

### Requirement 7

**User Story:** As a merge reviewer, I want to see detailed session cards with progress indicators, so that I can quickly assess the status of each merge session.

#### Acceptance Criteria

1. WHEN viewing the sessions page THEN the system SHALL display each session as a card with reference ID, creation date, and status badge
2. WHEN viewing a session card THEN the system SHALL display the progress as "X / Y (Z%)" where X is reviewed, Y is total, and Z is percentage
3. WHEN viewing a session card THEN the system SHALL provide action buttons appropriate to the session status
4. WHEN a session status is "Ready" or "In Progress" THEN the system SHALL display "View Summary" and "Resume Workflow" buttons
5. WHEN a session status is "Completed" THEN the system SHALL display a "View Results" button
6. WHEN a session status is "Error" THEN the system SHALL display a disabled "Failed" button

### Requirement 8

**User Story:** As a merge reviewer, I want to generate reports from the summary page, so that I can document the merge analysis results.

#### Acceptance Criteria

1. WHEN viewing the summary page THEN the system SHALL provide a "Generate Report" button
2. WHEN a user clicks "Generate Report" THEN the system SHALL create a downloadable report containing session information, statistics, and change details
3. WHEN generating a report THEN the system SHALL include package information for all three packages
4. WHEN generating a report THEN the system SHALL include the breakdown by classification and object type
5. WHEN generating a report THEN the system SHALL format the report in a readable format (PDF or Word document)

### Requirement 9

**User Story:** As a merge reviewer, I want to jump to specific changes from the workflow page, so that I can quickly navigate to changes of interest.

#### Acceptance Criteria

1. WHEN viewing the workflow page THEN the system SHALL provide a "Jump to Change" dropdown or modal
2. WHEN a user selects a change from the jump menu THEN the system SHALL navigate directly to that change's detail page
3. WHEN viewing the workflow page THEN the system SHALL display changes grouped by classification with visual indicators
4. WHEN viewing the workflow page THEN the system SHALL provide filter buttons to show only specific classifications

### Requirement 10

**User Story:** As a system administrator, I want all pages to handle errors gracefully, so that users receive helpful feedback when issues occur.

#### Acceptance Criteria

1. WHEN a requested session does not exist THEN the system SHALL display a 404 error page with a link back to sessions
2. WHEN a requested change does not exist THEN the system SHALL display a 404 error page with a link back to the workflow
3. WHEN a database error occurs THEN the system SHALL display a user-friendly error message and log the technical details
4. WHEN a file upload fails THEN the system SHALL display the specific error reason to the user
5. WHEN the system is processing packages THEN the system SHALL display a loading indicator and prevent duplicate submissions
