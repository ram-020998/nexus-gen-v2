/**
 * Settings Page JavaScript
 */

const SettingsPage = {
    /**
     * Initialize all settings page functionality
     */
    init: function() {
        this.initThemeToggle();
        this.initCleanupButton();
        this.initBackupButton();
        this.initRestoreButton();
    },
    
    /**
     * Initialize theme toggle functionality
     * Handles theme switching with localStorage persistence
     * Updates UI immediately without page reload
     */
    initThemeToggle: function() {
        const themeToggleBtn = document.getElementById('themeToggleBtn');
        if (!themeToggleBtn) return;
        
        const themeOptions = themeToggleBtn.querySelectorAll('.theme-option');
        
        // Get current theme from localStorage or default to 'dark'
        // Handle localStorage unavailable (private browsing)
        let currentTheme = 'dark';
        try {
            currentTheme = localStorage.getItem('theme') || 'dark';
        } catch (e) {
            console.warn('localStorage unavailable, using session-only theme storage:', e);
            // Fall back to session storage or in-memory storage
            currentTheme = sessionStorage.getItem('theme') || 'dark';
        }
        
        // Update UI to show current theme
        this.updateThemeUI(currentTheme, themeOptions);
        
        // Add click handlers to theme options
        themeOptions.forEach(option => {
            option.addEventListener('click', () => {
                const selectedTheme = option.getAttribute('data-theme');
                
                // Update document theme attribute
                document.documentElement.setAttribute('data-theme', selectedTheme);
                
                // Save to localStorage with fallback to sessionStorage
                try {
                    localStorage.setItem('theme', selectedTheme);
                } catch (e) {
                    console.warn('localStorage unavailable, using sessionStorage:', e);
                    try {
                        sessionStorage.setItem('theme', selectedTheme);
                        DocFlow.showNotification(
                            `Theme changed to ${selectedTheme} mode (session only - private browsing detected)`,
                            'success'
                        );
                        return;
                    } catch (sessionError) {
                        console.error('Both localStorage and sessionStorage unavailable:', sessionError);
                        DocFlow.showNotification(
                            `Theme changed to ${selectedTheme} mode (not persisted - storage unavailable)`,
                            'success'
                        );
                        return;
                    }
                }
                
                // Update UI
                this.updateThemeUI(selectedTheme, themeOptions);
                
                // Show notification
                DocFlow.showNotification(`Theme changed to ${selectedTheme} mode`, 'success');
            });
        });
    },
    
    /**
     * Update theme toggle UI to reflect current theme
     * @param {string} theme - Current theme ('dark' or 'light')
     * @param {NodeList} themeOptions - Theme option elements
     */
    updateThemeUI: function(theme, themeOptions) {
        themeOptions.forEach(option => {
            if (option.getAttribute('data-theme') === theme) {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });
    },
    
    /**
     * Initialize cleanup button functionality
     * Shows confirmation dialog before cleanup
     */
    initCleanupButton: function() {
        const cleanupBtn = document.getElementById('cleanupBtn');
        if (!cleanupBtn) return;
        
        cleanupBtn.addEventListener('click', () => {
            this.showConfirmDialog(
                'Are you sure you want to clean up the database? This will delete all data and uploaded files. This action cannot be undone.',
                () => this.executeCleanup()
            );
        });
    },
    
    /**
     * Execute database cleanup
     */
    executeCleanup: function() {
        const cleanupBtn = document.getElementById('cleanupBtn');
        DocFlow.showLoading(cleanupBtn);
        
        fetch('/settings/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `Server error: ${response.status}`);
                }).catch(jsonError => {
                    // If response is not JSON, throw generic error
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            DocFlow.hideLoading(cleanupBtn);
            
            if (data.success) {
                DocFlow.showNotification(
                    `Database cleaned successfully. Deleted ${data.deleted_records} records and ${data.deleted_files || 0} files.`,
                    'success'
                );
            } else {
                DocFlow.showNotification(
                    `Cleanup failed: ${data.error || 'Unknown error'}`,
                    'error'
                );
            }
        })
        .catch(error => {
            DocFlow.hideLoading(cleanupBtn);
            console.error('Cleanup error:', error);
            DocFlow.showNotification(
                `Failed to clean up database: ${error.message || 'Network error'}`,
                'error'
            );
        });
    },
    
    /**
     * Initialize backup button functionality
     */
    initBackupButton: function() {
        const backupBtn = document.getElementById('backupBtn');
        if (!backupBtn) return;
        
        backupBtn.addEventListener('click', () => {
            this.executeBackup();
        });
    },
    
    /**
     * Execute database backup
     */
    executeBackup: function() {
        const backupBtn = document.getElementById('backupBtn');
        DocFlow.showLoading(backupBtn);
        
        fetch('/settings/backup', {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Backup failed');
                }).catch(jsonError => {
                    // If response is not JSON, throw generic error
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                });
            }
            
            // Get filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'nexusgen_backup.sql';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }
            
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            DocFlow.hideLoading(backupBtn);
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            DocFlow.showNotification('Database backup downloaded successfully', 'success');
        })
        .catch(error => {
            DocFlow.hideLoading(backupBtn);
            console.error('Backup error:', error);
            
            // Provide specific error messages for common issues
            let errorMessage = error.message || 'Failed to backup database';
            if (errorMessage.includes('sqlite3') || errorMessage.includes('SQLite tools')) {
                errorMessage = 'Backup failed: SQLite tools not available on server. Please contact administrator.';
            }
            
            DocFlow.showNotification(errorMessage, 'error');
        });
    },
    
    /**
     * Initialize restore button functionality
     */
    initRestoreButton: function() {
        const restoreBtn = document.getElementById('restoreBtn');
        const restoreFile = document.getElementById('restoreFile');
        if (!restoreBtn || !restoreFile) return;
        
        // Add file size validation on file selection
        restoreFile.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Check file size (max 100MB)
                const maxSize = 100 * 1024 * 1024; // 100MB in bytes
                if (file.size > maxSize) {
                    DocFlow.showNotification(
                        `File too large (${DocFlow.formatFileSize(file.size)}). Maximum size is 100MB.`,
                        'error'
                    );
                    e.target.value = ''; // Clear the file input
                    return;
                }
                
                // Validate file extension
                if (!this.validateSqlFile(file)) {
                    DocFlow.showNotification('Invalid file. Please select a .sql file', 'error');
                    e.target.value = ''; // Clear the file input
                    return;
                }
            }
        });
        
        restoreBtn.addEventListener('click', () => {
            const file = restoreFile.files[0];
            
            if (!file) {
                DocFlow.showNotification('Please select a SQL file to restore', 'error');
                return;
            }
            
            if (!this.validateSqlFile(file)) {
                DocFlow.showNotification('Invalid file. Please select a .sql file', 'error');
                return;
            }
            
            // Check file size again before upload
            const maxSize = 100 * 1024 * 1024; // 100MB
            if (file.size > maxSize) {
                DocFlow.showNotification(
                    `File too large (${DocFlow.formatFileSize(file.size)}). Maximum size is 100MB.`,
                    'error'
                );
                return;
            }
            
            this.showConfirmDialog(
                'Are you sure you want to restore the database? This will replace all current data with the backup. This action cannot be undone.',
                () => this.executeRestore(file)
            );
        });
    },
    
    /**
     * Validate SQL file
     * @param {File} file - File to validate
     * @returns {boolean} - True if valid
     */
    validateSqlFile: function(file) {
        return file.name.toLowerCase().endsWith('.sql');
    },
    
    /**
     * Execute database restore
     * @param {File} file - SQL file to restore
     */
    executeRestore: function(file) {
        const restoreBtn = document.getElementById('restoreBtn');
        DocFlow.showLoading(restoreBtn);
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/settings/restore', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `Server error: ${response.status}`);
                }).catch(jsonError => {
                    // If response is not JSON, throw generic error
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            DocFlow.hideLoading(restoreBtn);
            
            if (data.success) {
                DocFlow.showNotification(
                    `Database restored successfully. Restored ${data.restored_records} records.`,
                    'success'
                );
                
                // Clear file input
                document.getElementById('restoreFile').value = '';
            } else {
                DocFlow.showNotification(
                    `Restore failed: ${data.error || 'Unknown error'}`,
                    'error'
                );
            }
        })
        .catch(error => {
            DocFlow.hideLoading(restoreBtn);
            console.error('Restore error:', error);
            
            // Provide specific error messages for common issues
            let errorMessage = error.message || 'Failed to restore database';
            if (errorMessage.includes('sqlite3') || errorMessage.includes('SQLite tools')) {
                errorMessage = 'Restore failed: SQLite tools not available on server. Please contact administrator.';
            } else if (errorMessage.includes('Invalid SQL')) {
                errorMessage = 'Restore failed: Invalid SQL file content. Please ensure the file is a valid database backup.';
            } else if (errorMessage.includes('file format')) {
                errorMessage = 'Restore failed: Invalid file format. Only .sql files are accepted.';
            }
            
            DocFlow.showNotification(errorMessage, 'error');
        });
    },
    
    /**
     * Show confirmation dialog
     * @param {string} message - Confirmation message
     * @param {Function} onConfirm - Callback when confirmed
     */
    showConfirmDialog: function(message, onConfirm) {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="confirmModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content" style="background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color);">
                        <div class="modal-header" style="border-bottom: 1px solid var(--border-color);">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i>
                                Confirm Action
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" style="filter: invert(1);"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer" style="border-top: 1px solid var(--border-color);">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-danger" id="confirmBtn">Confirm</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('confirmModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Get modal element
        const modalElement = document.getElementById('confirmModal');
        const modal = new bootstrap.Modal(modalElement);
        
        // Add confirm button handler
        document.getElementById('confirmBtn').addEventListener('click', () => {
            modal.hide();
            onConfirm();
        });
        
        // Clean up modal after it's hidden
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
        
        // Show modal
        modal.show();
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    SettingsPage.init();
});
