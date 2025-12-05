/**
 * DocFlow - Main JavaScript
 */

// Common utilities
const DocFlow = {
    // Show loading state
    showLoading: function(element) {
        if (element) {
            element.dataset.originalText = element.innerHTML;
            element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            element.disabled = true;
        }
    },
    
    // Hide loading state
    hideLoading: function(element, originalText = null) {
        if (element) {
            const text = originalText || element.dataset.originalText || 'Submit';
            element.innerHTML = text;
            element.disabled = false;
        }
    },
    
    // Show notification
    showNotification: function(message, type = 'info') {
        // Remove existing notifications
        document.querySelectorAll('.notification').forEach(n => n.remove());
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    },
    
    // Format timestamp
    formatTimestamp: function(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    },
    
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Validate file type
    validateFileType: function(filename, allowedTypes = ['txt', 'md', 'docx', 'pdf']) {
        const extension = filename.split('.').pop().toLowerCase();
        return allowedTypes.includes(extension);
    },
    
    // Handle API errors
    handleApiError: function(error, defaultMessage = 'An error occurred') {
        console.error('API Error:', error);
        
        let message = defaultMessage;
        if (error.response && error.response.data && error.response.data.error) {
            message = error.response.data.error;
        } else if (error.message) {
            message = error.message;
        }
        
        this.showNotification(message, 'error');
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    DocFlow.showNotification('An unexpected error occurred', 'error');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    DocFlow.showNotification('An unexpected error occurred', 'error');
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DocFlow initialized');
    
    // Initialize sidebar toggle
    initSidebarToggle();
    
    // Add loading states to all forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                DocFlow.showLoading(submitButton);
            }
        });
    });
    
    // Add file validation to file inputs
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            // Skip validation for analyzer file inputs
            if (this.id === 'file' && window.location.pathname.includes('/analyzer')) return;
            if (this.id === 'old_file' || this.id === 'new_file') return;
            // Skip validation for merge assistant file inputs
            if (this.id === 'basePackage' || this.id === 'customizedPackage' || this.id === 'newVendorPackage') return;
            if (window.location.pathname.includes('/merge-assistant')) return;
            
            if (file && !DocFlow.validateFileType(file.name)) {
                DocFlow.showNotification('Invalid file type. Please select a TXT, MD, DOCX, or PDF file.', 'error');
                e.target.value = '';
            }
        });
    });
});

// Sidebar toggle functionality
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    
    if (sidebarToggle && sidebar && mainContent) {
        // Disable transitions temporarily
        sidebar.classList.add('no-transition');
        mainContent.classList.add('no-transition');
        
        // Load saved state immediately
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('collapsed');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('collapsed');
        }
        
        // Re-enable transitions after a brief delay
        setTimeout(() => {
            sidebar.classList.remove('no-transition');
            mainContent.classList.remove('no-transition');
        }, 50);
        
        // Toggle functionality
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const willBeCollapsed = !sidebar.classList.contains('collapsed');
            
            if (willBeCollapsed) {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('collapsed');
            } else {
                sidebar.classList.remove('collapsed');
                mainContent.classList.remove('collapsed');
            }
            
            // Save state
            localStorage.setItem('sidebarCollapsed', willBeCollapsed);
        });
    }

    // Theme initialization - load saved theme on page load
    // Handle localStorage unavailable (private browsing)
    let savedTheme = 'dark';
    try {
        savedTheme = localStorage.getItem('theme') || 'dark';
    } catch (e) {
        console.warn('localStorage unavailable, using default theme:', e);
        try {
            savedTheme = sessionStorage.getItem('theme') || 'dark';
        } catch (sessionError) {
            console.warn('sessionStorage also unavailable, using default theme');
        }
    }
    document.documentElement.setAttribute('data-theme', savedTheme);
}

/**
 * Enhanced Loading Indicators and Animations
 * For Three-Way Merge UI Enhancement
 */

// Loading Overlay Manager
const LoadingManager = {
    // Show full-screen loading overlay
    showOverlay: function(message = 'Processing...') {
        // Remove existing overlay if any
        this.hideOverlay();
        
        const overlay = document.createElement('div');
        overlay.className = 'spinner-overlay fade-in';
        overlay.id = 'loadingOverlay';
        overlay.innerHTML = `
            <div class="spinner-container">
                <div class="spinner"></div>
                <div class="spinner-text">${message}</div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        document.body.style.overflow = 'hidden';
    },
    
    // Hide full-screen loading overlay
    hideOverlay: function() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.remove();
            document.body.style.overflow = '';
        }
    },
    
    // Update overlay message
    updateMessage: function(message) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            const textElement = overlay.querySelector('.spinner-text');
            if (textElement) {
                textElement.textContent = message;
            }
        }
    },
    
    // Show button loading state
    showButtonLoading: function(button) {
        if (!button) return;
        
        button.dataset.originalContent = button.innerHTML;
        button.classList.add('btn-loading');
        button.disabled = true;
    },
    
    // Hide button loading state
    hideButtonLoading: function(button) {
        if (!button) return;
        
        button.classList.remove('btn-loading');
        button.disabled = false;
        
        if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
            delete button.dataset.originalContent;
        }
    }
};

// Toast Notification Manager
const ToastManager = {
    container: null,
    
    // Initialize toast container
    init: function() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    
    // Show toast notification
    show: function(title, message, type = 'info', duration = 5000) {
        this.init();
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${icons[type]} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                ${message ? `<div class="toast-message">${message}</div>` : ''}
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        this.container.appendChild(toast);
        
        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.style.animation = 'slideIn 0.3s ease reverse';
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }
        
        return toast;
    },
    
    // Convenience methods
    success: function(title, message, duration) {
        return this.show(title, message, 'success', duration);
    },
    
    error: function(title, message, duration) {
        return this.show(title, message, 'error', duration);
    },
    
    warning: function(title, message, duration) {
        return this.show(title, message, 'warning', duration);
    },
    
    info: function(title, message, duration) {
        return this.show(title, message, 'info', duration);
    }
};

// Animation Utilities
const AnimationUtils = {
    // Smooth expand/collapse
    expandElement: function(element, duration = 300) {
        if (!element) return;
        
        element.style.display = 'block';
        const height = element.scrollHeight;
        element.style.height = '0px';
        element.style.overflow = 'hidden';
        element.style.transition = `height ${duration}ms ease`;
        
        requestAnimationFrame(() => {
            element.style.height = height + 'px';
        });
        
        setTimeout(() => {
            element.style.height = '';
            element.style.overflow = '';
            element.style.transition = '';
        }, duration);
    },
    
    collapseElement: function(element, duration = 300) {
        if (!element) return;
        
        const height = element.scrollHeight;
        element.style.height = height + 'px';
        element.style.overflow = 'hidden';
        element.style.transition = `height ${duration}ms ease`;
        
        requestAnimationFrame(() => {
            element.style.height = '0px';
        });
        
        setTimeout(() => {
            element.style.display = 'none';
            element.style.height = '';
            element.style.overflow = '';
            element.style.transition = '';
        }, duration);
    },
    
    // Fade in element
    fadeIn: function(element, duration = 300) {
        if (!element) return;
        
        element.style.opacity = '0';
        element.style.display = 'block';
        element.style.transition = `opacity ${duration}ms ease`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '1';
        });
        
        setTimeout(() => {
            element.style.transition = '';
        }, duration);
    },
    
    // Fade out element
    fadeOut: function(element, duration = 300) {
        if (!element) return;
        
        element.style.opacity = '1';
        element.style.transition = `opacity ${duration}ms ease`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '0';
        });
        
        setTimeout(() => {
            element.style.display = 'none';
            element.style.transition = '';
        }, duration);
    },
    
    // Slide down
    slideDown: function(element, duration = 300) {
        if (!element) return;
        element.classList.add('slide-down');
        setTimeout(() => element.classList.remove('slide-down'), duration);
    }
};

// Report Generation Handler
function handleReportGeneration(button, sessionId) {
    LoadingManager.showButtonLoading(button);
    LoadingManager.showOverlay('Generating report...');
    
    fetch(`/merge-assistant/${sessionId}/report`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Report generation failed');
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `merge-report-${sessionId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        
        ToastManager.success('Success', 'Report generated successfully');
    })
    .catch(error => {
        console.error('Report generation error:', error);
        ToastManager.error('Error', 'Failed to generate report');
    })
    .finally(() => {
        LoadingManager.hideButtonLoading(button);
        LoadingManager.hideOverlay();
    });
}

// Change Action Handlers
function handleMarkAsReviewed(button, sessionId, changeId) {
    LoadingManager.showButtonLoading(button);
    
    fetch(`/merge-assistant/${sessionId}/changes/${changeId}/review`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastManager.success('Success', 'Change marked as reviewed');
            updateSessionInfo(data.session);
            
            // Navigate to next change if available
            if (data.next_change_id) {
                setTimeout(() => {
                    window.location.href = `/merge-assistant/${sessionId}/changes/${data.next_change_id}`;
                }, 1000);
            }
        } else {
            throw new Error(data.error || 'Failed to mark as reviewed');
        }
    })
    .catch(error => {
        console.error('Mark as reviewed error:', error);
        ToastManager.error('Error', error.message || 'Failed to mark as reviewed');
    })
    .finally(() => {
        LoadingManager.hideButtonLoading(button);
    });
}

function handleSkipChange(button, sessionId, changeId) {
    LoadingManager.showButtonLoading(button);
    
    fetch(`/merge-assistant/${sessionId}/changes/${changeId}/skip`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastManager.info('Skipped', 'Change skipped');
            updateSessionInfo(data.session);
            
            // Navigate to next change if available
            if (data.next_change_id) {
                setTimeout(() => {
                    window.location.href = `/merge-assistant/${sessionId}/changes/${data.next_change_id}`;
                }, 1000);
            }
        } else {
            throw new Error(data.error || 'Failed to skip change');
        }
    })
    .catch(error => {
        console.error('Skip change error:', error);
        ToastManager.error('Error', error.message || 'Failed to skip change');
    })
    .finally(() => {
        LoadingManager.hideButtonLoading(button);
    });
}

function handleSaveNotes(button, sessionId, changeId) {
    const notesTextarea = document.getElementById('changeNotes');
    if (!notesTextarea) return;
    
    LoadingManager.showButtonLoading(button);
    
    fetch(`/merge-assistant/${sessionId}/changes/${changeId}/notes`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            notes: notesTextarea.value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastManager.success('Saved', 'Notes saved successfully');
        } else {
            throw new Error(data.error || 'Failed to save notes');
        }
    })
    .catch(error => {
        console.error('Save notes error:', error);
        ToastManager.error('Error', error.message || 'Failed to save notes');
    })
    .finally(() => {
        LoadingManager.hideButtonLoading(button);
    });
}

// Update session info panel
function updateSessionInfo(sessionData) {
    const reviewedCount = document.getElementById('reviewedCount');
    const skippedCount = document.getElementById('skippedCount');
    const sessionStatus = document.getElementById('sessionStatus');
    
    if (reviewedCount && sessionData.reviewed_count !== undefined) {
        reviewedCount.textContent = sessionData.reviewed_count;
    }
    
    if (skippedCount && sessionData.skipped_count !== undefined) {
        skippedCount.textContent = sessionData.skipped_count;
    }
    
    if (sessionStatus && sessionData.status) {
        sessionStatus.textContent = sessionData.status;
        sessionStatus.className = `status-badge ${sessionData.status.toLowerCase().replace(' ', '-')}`;
    }
}

// Object Type Expansion Handler
function toggleObjectType(element) {
    const item = element.closest('.object-type-item');
    if (!item) return;
    
    const content = item.querySelector('.object-type-content');
    const isExpanded = item.classList.contains('expanded');
    
    if (isExpanded) {
        item.classList.remove('expanded');
        AnimationUtils.collapseElement(content);
    } else {
        item.classList.add('expanded');
        AnimationUtils.expandElement(content);
        
        // Load object details if not already loaded
        const objectGrid = content.querySelector('.object-grid');
        if (objectGrid && !objectGrid.dataset.loaded) {
            loadObjectTypeDetails(item);
        }
    }
}

// Load object type details via AJAX
function loadObjectTypeDetails(item) {
    const objectType = item.dataset.objectType;
    const sessionId = item.dataset.sessionId;
    const objectGrid = item.querySelector('.object-grid');
    
    if (!objectType || !sessionId || !objectGrid) return;
    
    objectGrid.innerHTML = '<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
    
    fetch(`/merge-assistant/${sessionId}/objects/${objectType}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.objects) {
                renderObjectGrid(objectGrid, data.objects);
                objectGrid.dataset.loaded = 'true';
            } else {
                throw new Error('Failed to load objects');
            }
        })
        .catch(error => {
            console.error('Load objects error:', error);
            objectGrid.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Failed to load objects</div>';
        });
}

// Render object grid table
function renderObjectGrid(container, objects) {
    if (!objects || objects.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">No objects found</div>';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'object-grid-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>Object Name</th>
                <th>UUID</th>
                <th>Classification</th>
                <th>Complexity</th>
            </tr>
        </thead>
        <tbody>
            ${objects.map(obj => `
                <tr>
                    <td>${obj.name || 'N/A'}</td>
                    <td><span class="uuid-text">${obj.uuid || 'N/A'}</span></td>
                    <td><span class="classification-badge ${(obj.classification || '').toLowerCase().replace('_', '-')}">${obj.classification || 'N/A'}</span></td>
                    <td><span class="complexity-${(obj.complexity || 'low').toLowerCase()}">${obj.complexity || 'Low'}</span></td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    container.innerHTML = '';
    container.appendChild(table);
}

// Export to global scope
window.LoadingManager = LoadingManager;
window.ToastManager = ToastManager;
window.AnimationUtils = AnimationUtils;
window.handleReportGeneration = handleReportGeneration;
window.handleMarkAsReviewed = handleMarkAsReviewed;
window.handleSkipChange = handleSkipChange;
window.handleSaveNotes = handleSaveNotes;
window.toggleObjectType = toggleObjectType;
