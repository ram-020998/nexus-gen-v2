# Implementation Plan

- [x] 1. Set up Settings page structure and routing
  - Create `controllers/settings_controller.py` with Flask blueprint
  - Register settings blueprint in `app.py`
  - Create `templates/settings/index.html` extending base.html
  - Add Settings menu item to sidebar in `base.html`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.1, 7.2_

- [x] 2. Implement theme management in Settings page
  - [x] 2.1 Remove floating theme toggle from base.html
    - Remove `<button class="theme-toggle">` element from base template
    - Keep theme initialization code in `main.js` for loading saved theme
    - _Requirements: 3.1, 3.2_

  - [x] 2.2 Create theme toggle UI in Settings page
    - Add Theme section to settings template with toggle control
    - Display current theme state (dark/light)
    - Style theme toggle using existing CSS patterns
    - _Requirements: 2.1, 7.4, 7.5_

  - [x] 2.3 Implement theme toggle JavaScript
    - Create `static/js/settings.js` with SettingsPage object
    - Implement `initThemeToggle()` method
    - Handle theme switching with localStorage persistence
    - Update UI immediately without page reload
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 3.3_

  - [x] 2.4 Write property test for theme toggle
    - **Property 2: Theme toggle switches between states**
    - **Validates: Requirements 2.2**

  - [x] 2.5 Write property test for theme persistence
    - **Property 3: Theme preference round-trip**
    - **Validates: Requirements 2.3, 2.5**

  - [x] 2.6 Write property test for theme application
    - **Property 4: Theme changes apply without reload**
    - **Validates: Requirements 2.4**

- [x] 3. Implement database cleanup functionality
  - [x] 3.1 Create SettingsService class
    - Create `services/settings_service.py`
    - Implement `cleanup_database()` method
    - Reuse logic from `cleanup_database.py` script
    - Return structured results with counts
    - _Requirements: 4.3, 4.4, 4.5_

  - [x] 3.2 Implement cleanup controller endpoint
    - Add `POST /settings/cleanup` route
    - Call settings service cleanup method
    - Handle errors and return JSON response
    - _Requirements: 4.3, 4.6, 4.7_

  - [x] 3.3 Create cleanup UI and confirmation dialog
    - Add Data Cleanup section to settings template
    - Implement `initCleanupButton()` in settings.js
    - Show Bootstrap confirmation modal before cleanup
    - Display loading state during operation
    - Show success/error notifications with counts
    - _Requirements: 4.1, 4.2, 4.6, 4.7, 4.8_

  - [x] 3.4 Write property test for cleanup confirmation
    - **Property 7: Cleanup requires confirmation**
    - **Validates: Requirements 4.2**

  - [x] 3.5 Write property test for cleanup deletion
    - **Property 8: Cleanup empties all tables**
    - **Validates: Requirements 4.3, 4.4**

  - [x] 3.6 Write property test for gitkeep preservation
    - **Property 9: Cleanup preserves gitkeep files**
    - **Validates: Requirements 4.5**

  - [x] 3.7 Write property test for cleanup rollback
    - **Property 11: Cleanup rollback on error**
    - **Validates: Requirements 4.7**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement database backup functionality
  - [x] 5.1 Implement backup service method
    - Add `backup_database()` method to SettingsService
    - Use subprocess to execute `sqlite3 .dump` command
    - Generate timestamped filename
    - Save backup to outputs/backups/ directory
    - _Requirements: 5.2, 5.3, 5.4_

  - [x] 5.2 Implement backup controller endpoint
    - Add `POST /settings/backup` route
    - Call settings service backup method
    - Return file download using `send_file`
    - Handle errors and return JSON response
    - _Requirements: 5.2, 5.5, 5.6, 5.7_

  - [x] 5.3 Create backup UI
    - Add Data Backup section to settings template
    - Implement `initBackupButton()` in settings.js
    - Trigger file download on success
    - Show success/error notifications
    - _Requirements: 5.1, 5.5, 5.6, 5.7_

  - [x] 5.4 Write property test for backup generation
    - **Property 13: Backup generates SQL file**
    - **Validates: Requirements 5.2**

  - [x] 5.5 Write property test for backup completeness
    - **Property 14: Backup includes all data**
    - **Validates: Requirements 5.3**

  - [x] 5.6 Write property test for backup filename
    - **Property 15: Backup filename format**
    - **Validates: Requirements 5.4**

  - [x] 5.7 Write property test for backup round-trip
    - **Property 18: Backup round-trip**
    - **Validates: Requirements 5.8**

- [x] 6. Implement database restore functionality
  - [x] 6.1 Implement restore service method
    - Add `restore_database()` method to SettingsService
    - Add `_validate_sql_file()` helper method
    - Validate file extension and SQL content
    - Clear existing data before import
    - Use subprocess to execute SQL file
    - Count and return restored records
    - _Requirements: 6.2, 6.4, 6.5, 6.9_

  - [x] 6.2 Implement restore controller endpoint
    - Add `POST /settings/restore` route
    - Handle file upload from request
    - Save uploaded file temporarily
    - Call settings service restore method
    - Clean up temporary file
    - Handle errors and return JSON response
    - _Requirements: 6.4, 6.6, 6.7_

  - [x] 6.3 Create restore UI and confirmation dialog
    - Add Data Restore section to settings template
    - Add file input with .sql accept filter
    - Implement `initRestoreButton()` in settings.js
    - Validate file selection before upload
    - Show Bootstrap confirmation modal before restore
    - Display loading state during operation
    - Show success/error notifications with counts
    - _Requirements: 6.1, 6.2, 6.3, 6.6, 6.7, 6.8_

  - [x] 6.4 Write property test for restore confirmation
    - **Property 19: Restore requires confirmation**
    - **Validates: Requirements 6.3**

  - [x] 6.5 Write property test for restore clear-then-import
    - **Property 20: Restore clears then imports**
    - **Validates: Requirements 6.5**

  - [x] 6.6 Write property test for restore rollback
    - **Property 22: Restore rollback on error**
    - **Validates: Requirements 6.7**

  - [x] 6.7 Write property test for invalid SQL rejection
    - **Property 24: Restore rejects invalid SQL**
    - **Validates: Requirements 6.9**

- [x] 7. Add CSS styling for Settings page
  - Add settings-specific styles to `docflow.css`
  - Style settings sections with card layout
  - Style theme toggle control
  - Style file upload control
  - Ensure consistency with existing design patterns
  - _Requirements: 7.3, 7.4, 7.5_

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Integration testing and polish
  - [ ] 9.1 Test complete workflows
    - Test theme toggle workflow across pages
    - Test cleanup workflow with confirmation
    - Test backup download workflow
    - Test restore upload workflow
    - Test backup-restore round-trip
    - _Requirements: All_

  - [ ] 9.2 Write integration tests
    - Write test for settings page navigation
    - Write test for theme persistence across navigation
    - Write test for cleanup workflow
    - Write test for backup-restore round-trip
    - _Requirements: All_

  - [x] 9.3 Add error handling and edge cases
    - Handle localStorage unavailable (private browsing)
    - Handle missing sqlite3 command
    - Handle file upload errors
    - Handle large file uploads
    - Add appropriate error messages
    - _Requirements: 4.7, 5.7, 6.7_

  - [x] 9.4 Add logging
    - Log all cleanup operations
    - Log all backup operations
    - Log all restore operations
    - Include timestamps and operation results
    - _Requirements: 4.3, 5.2, 6.4_
