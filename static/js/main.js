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
