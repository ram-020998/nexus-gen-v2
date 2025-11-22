# Requirements Document

## Introduction

This document specifies the requirements for a centralized Settings page in the NexusGen application. The Settings page will consolidate application-wide configuration options including theme management, data cleanup operations, and database backup functionality. This feature aims to improve user experience by providing a single location for system administration tasks and removing the theme toggle from individual pages.

## Glossary

- **NexusGen Application**: The Flask-based web application for analyzing and comparing Appian applications
- **Theme Toggle**: A UI control that switches between dark and light visual themes
- **Data Cleanup**: The process of truncating all database tables and removing uploaded files
- **Database Backup**: The process of exporting the SQLite database to a SQL file format
- **Settings Page**: A dedicated web page for managing application-wide configuration and administrative tasks
- **SQLite Database**: The database system used by NexusGen, stored at `instance/docflow.db`
- **SQL Export**: A text file containing SQL statements that can recreate the database structure and data

## Requirements

### Requirement 1

**User Story:** As a user, I want to access a centralized Settings page from the navigation menu, so that I can manage application configuration in one place.

#### Acceptance Criteria

1. WHEN the application loads THEN the Settings Page SHALL appear as a menu item in the sidebar navigation
2. WHEN a user clicks the Settings menu item THEN the System SHALL navigate to the Settings page
3. WHEN the Settings page loads THEN the System SHALL display a page header with title "Settings" and subtitle describing the page purpose
4. WHEN the Settings page is active THEN the System SHALL highlight the Settings menu item in the sidebar

### Requirement 2

**User Story:** As a user, I want to toggle between dark and light themes from the Settings page, so that I can customize the visual appearance of the application.

#### Acceptance Criteria

1. WHEN the Settings page loads THEN the System SHALL display a Theme section with the current theme state
2. WHEN a user clicks the theme toggle control THEN the System SHALL switch between dark and light themes immediately
3. WHEN the theme is changed THEN the System SHALL persist the theme preference to browser local storage
4. WHEN the theme is changed THEN the System SHALL update the visual appearance of all UI elements without requiring a page reload
5. WHEN a user returns to the application THEN the System SHALL load the previously saved theme preference

### Requirement 3

**User Story:** As a user, I want the theme toggle removed from other pages, so that theme management is centralized in the Settings page.

#### Acceptance Criteria

1. WHEN any page other than Settings loads THEN the System SHALL NOT display the floating theme toggle button
2. WHEN the base template is rendered THEN the System SHALL exclude the theme toggle button from the page structure
3. WHEN theme changes are made in Settings THEN the System SHALL apply the theme across all pages in the application

### Requirement 4

**User Story:** As an administrator, I want to perform database cleanup from the Settings page, so that I can reset the application to a clean state during testing or maintenance.

#### Acceptance Criteria

1. WHEN the Settings page loads THEN the System SHALL display a Data Cleanup section with a cleanup button
2. WHEN a user clicks the cleanup button THEN the System SHALL display a confirmation dialog warning about data deletion
3. WHEN a user confirms the cleanup action THEN the System SHALL execute the cleanup script to delete all database records
4. WHEN the cleanup executes THEN the System SHALL delete all records from MergeSession, ChangeReview, ComparisonRequest, and Request tables
5. WHEN the cleanup executes THEN the System SHALL delete all uploaded files except .gitkeep files
6. WHEN the cleanup completes successfully THEN the System SHALL display a success notification with the count of deleted records
7. WHEN the cleanup encounters an error THEN the System SHALL display an error notification and rollback any partial changes
8. WHEN a user cancels the confirmation dialog THEN the System SHALL abort the cleanup operation without making changes

### Requirement 5

**User Story:** As an administrator, I want to backup the database from the Settings page, so that I can preserve application data before performing maintenance or testing operations.

#### Acceptance Criteria

1. WHEN the Settings page loads THEN the System SHALL display a Data Backup section with a backup button
2. WHEN a user clicks the backup button THEN the System SHALL generate a SQL export file from the SQLite database
3. WHEN the backup is generated THEN the System SHALL include all table structures and data in the SQL export
4. WHEN the backup is generated THEN the System SHALL create a filename with timestamp format "nexusgen_backup_YYYYMMDD_HHMMSS.sql"
5. WHEN the backup completes successfully THEN the System SHALL trigger a browser download of the SQL file
6. WHEN the backup completes successfully THEN the System SHALL display a success notification
7. WHEN the backup encounters an error THEN the System SHALL display an error notification with details
8. WHEN the SQL export is created THEN the System SHALL ensure it contains valid SQL statements that can be imported into SQLite

### Requirement 6

**User Story:** As an administrator, I want to restore the database from a backup file, so that I can recover data after cleanup or system issues.

#### Acceptance Criteria

1. WHEN the Settings page loads THEN the System SHALL display a Data Restore section with a file upload control
2. WHEN a user selects a SQL backup file THEN the System SHALL validate the file has a .sql extension
3. WHEN a user clicks the restore button THEN the System SHALL display a confirmation dialog warning about data replacement
4. WHEN a user confirms the restore action THEN the System SHALL execute the SQL file to restore database records
5. WHEN the restore executes THEN the System SHALL clear existing data before importing the backup
6. WHEN the restore completes successfully THEN the System SHALL display a success notification with the count of restored records
7. WHEN the restore encounters an error THEN the System SHALL display an error notification with details and rollback any partial changes
8. WHEN a user cancels the confirmation dialog THEN the System SHALL abort the restore operation without making changes
9. WHEN the SQL file contains invalid SQL statements THEN the System SHALL reject the file and display an error notification

### Requirement 7

**User Story:** As a developer, I want the Settings page to follow the existing application design patterns, so that it maintains consistency with the rest of the NexusGen interface.

#### Acceptance Criteria

1. WHEN the Settings page is implemented THEN the System SHALL use the base.html template for consistent layout
2. WHEN the Settings page is implemented THEN the System SHALL follow the existing Flask blueprint pattern for routing
3. WHEN the Settings page is implemented THEN the System SHALL use the existing CSS variables and styling from docflow.css
4. WHEN the Settings page displays sections THEN the System SHALL use card-based layouts consistent with other pages
5. WHEN the Settings page displays buttons THEN the System SHALL use the existing button styles and color schemes
