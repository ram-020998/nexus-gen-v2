# Three-Way Merge UI & Template Specification - Part 3

**Styling Guidelines and JavaScript Interactions**

---

## 6. Styling Guidelines

### 6.1 Color Palette

```css
:root {
    /* Primary Colors */
    --primary-purple: #8b5cf6;
    --primary-teal: #06b6d4;
    
    /* Background Colors */
    --bg-dark: #1a1a2e;
    --bg-darker: #16213e;
    --bg-card: #0f3460;
    
    /* Text Colors */
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    
    /* Classification Colors */
    --color-no-conflict: #10b981;
    --color-conflict: #ef4444;
    --color-new: #3b82f6;
    --color-deleted: #6b7280;
    
    /* Status Colors */
    --color-success: #10b981;
    --color-warning: #f59e0b;
    --color-error: #ef4444;
    --color-info: #3b82f6;
    
    /* Border Colors */
    --border-color: #334155;
    --border-light: #475569;
}
```

---

### 6.2 Typography

```css
/* Headings */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary);
    font-weight: 600;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.75rem; }
h4 { font-size: 1.5rem; }
h5 { font-size: 1.25rem; }
h6 { font-size: 1rem; }

/* Body Text */
body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 1rem;
    line-height: 1.6;
    color: var(--text-primary);
    background-color: var(--bg-dark);
}

/* Code */
code, pre {
    font-family: 'Fira Code', 'Courier New', monospace;
    font-size: 0.875rem;
}
```

---

### 6.3 Card Styles

```css
/* Base Card */
.card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Session Info Card */
.session-info-card {
    background: linear-gradient(135deg, var(--primary-purple), var(--primary-teal));
    color: white;
    padding: 2rem;
    border-radius: 0.75rem;
}

/* Object Header Card */
.object-header-card {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem;
    background-color: var(--bg-card);
    border-radius: 0.5rem;
    border-left: 4px solid var(--primary-purple);
}

/* Comparison Panel */
.comparison-panel {
    background-color: var(--bg-darker);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1.5rem;
}
```

---

### 6.4 Button Styles

```css
/* Primary Button */
.btn-primary {
    background-color: var(--primary-purple);
    border: none;
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.375rem;
    font-weight: 500;
    transition: all 0.2s;
}

.btn-primary:hover {
    background-color: #7c3aed;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

/* Secondary Button */
.btn-secondary {
    background-color: var(--primary-teal);
    border: none;
    color: white;
}

.btn-secondary:hover {
    background-color: #0891b2;
}

/* Outline Button */
.btn-outline {
    background-color: transparent;
    border: 2px solid var(--primary-purple);
    color: var(--primary-purple);
}

.btn-outline:hover {
    background-color: var(--primary-purple);
    color: white;
}

/* Navigation Buttons */
.btn-nav {
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-weight: 500;
}

.btn-nav-prev {
    background-color: var(--bg-card);
    color: var(--text-primary);
}

.btn-nav-next {
    background-color: var(--primary-purple);
    color: white;
}
```

---

### 6.5 Upload Zone Styles

```css
.upload-zone {
    border: 2px dashed var(--border-color);
    border-radius: 0.5rem;
    padding: 3rem 2rem;
    text-align: center;
    background-color: var(--bg-darker);
    transition: all 0.3s;
    cursor: pointer;
}

.upload-zone:hover {
    border-color: var(--primary-purple);
    background-color: rgba(139, 92, 246, 0.05);
}

.upload-zone.dragover {
    border-color: var(--primary-teal);
    background-color: rgba(6, 182, 212, 0.1);
    transform: scale(1.02);
}

.upload-zone.has-file {
    border-color: var(--color-success);
    background-color: rgba(16, 185, 129, 0.05);
}

.upload-icon {
    font-size: 3rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
}

.upload-text {
    color: var(--text-secondary);
    font-size: 0.875rem;
}
```

---

### 6.6 Diff Styles

```css
/* SAIL Code Diff Container */
.sail-diff-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    background-color: var(--bg-darker);
    border-radius: 0.5rem;
    overflow: hidden;
}

/* Diff Side */
.diff-side {
    display: flex;
    flex-direction: column;
}

.diff-side-header {
    padding: 0.75rem 1rem;
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.diff-side-header.before {
    background-color: rgba(239, 68, 68, 0.1);
    color: #fca5a5;
    border-bottom: 2px solid #ef4444;
}

.diff-side-header.after {
    background-color: rgba(16, 185, 129, 0.1);
    color: #6ee7b7;
    border-bottom: 2px solid #10b981;
}

/* Diff Code Content */
.diff-code-content {
    padding: 1rem;
    overflow-x: auto;
    background-color: #0d1117;
}

.diff-code-content pre {
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.6;
}

/* Diff Line Highlighting */
.diff-line-added {
    background-color: rgba(16, 185, 129, 0.15);
    border-left: 3px solid #10b981;
    padding-left: 0.5rem;
}

.diff-line-removed {
    background-color: rgba(239, 68, 68, 0.15);
    border-left: 3px solid #ef4444;
    padding-left: 0.5rem;
}

.diff-line-modified {
    background-color: rgba(245, 158, 11, 0.15);
    border-left: 3px solid #f59e0b;
    padding-left: 0.5rem;
}
```

---

### 6.7 Statistics Cards

```css
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background-color: var(--bg-card);
    border-radius: 0.5rem;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid var(--border-color);
    transition: all 0.3s;
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.stat-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
}

.stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}

.stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Classification-specific colors */
.stat-card.conflict .stat-icon { color: var(--color-conflict); }
.stat-card.no-conflict .stat-icon { color: var(--color-no-conflict); }
.stat-card.new .stat-icon { color: var(--color-new); }
.stat-card.deleted .stat-icon { color: var(--color-deleted); }
```

---

## 7. JavaScript Interactions

### 7.1 File Upload

```javascript
// File upload with drag & drop
class FileUploader {
    constructor(zoneId, inputId, packageType) {
        this.zone = document.getElementById(zoneId);
        this.input = document.getElementById(inputId);
        this.packageType = packageType;
        this.file = null;
        
        this.init();
    }
    
    init() {
        // Click to browse
        this.zone.addEventListener('click', () => this.input.click());
        
        // File input change
        this.input.addEventListener('change', (e) => {
            this.handleFile(e.target.files[0]);
        });
        
        // Drag & drop
        this.zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.zone.classList.add('dragover');
        });
        
        this.zone.addEventListener('dragleave', () => {
            this.zone.classList.remove('dragover');
        });
        
        this.zone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.zone.classList.remove('dragover');
            this.handleFile(e.dataTransfer.files[0]);
        });
    }
    
    handleFile(file) {
        // Validate file
        if (!file) return;
        
        if (!file.name.endsWith('.zip')) {
            showError('Please upload a ZIP file');
            return;
        }
        
        if (file.size > 16 * 1024 * 1024) {
            showError('File size must be less than 16MB');
            return;
        }
        
        // Store file
        this.file = file;
        
        // Update UI
        this.zone.classList.add('has-file');
        this.zone.innerHTML = `
            <div class="file-info">
                <i class="fas fa-file-archive"></i>
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
                <button class="btn-remove" onclick="removeFile('${this.packageType}')">
                    <i class="fas fa-times"></i> Remove
                </button>
            </div>
        `;
        
        // Check if all files uploaded
        checkAllFilesUploaded();
    }
}

// Initialize uploaders
const uploaderA = new FileUploader('uploadZoneA', 'fileInputA', 'base');
const uploaderB = new FileUploader('uploadZoneB', 'fileInputB', 'customized');
const uploaderC = new FileUploader('uploadZoneC', 'fileInputC', 'new_vendor');
```

---

### 7.2 Form Submission

```javascript
// Submit merge analysis form
document.getElementById('mergeUploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate all files uploaded
    if (!uploaderA.file || !uploaderB.file || !uploaderC.file) {
        showError('Please upload all three packages');
        return;
    }
    
    // Create FormData
    const formData = new FormData();
    formData.append('base_package', uploaderA.file);
    formData.append('customized_package', uploaderB.file);
    formData.append('new_vendor_package', uploaderC.file);
    
    // Show loading
    showLoading('Analyzing packages...');
    
    try {
        // Submit form
        const response = await fetch('/merge/create', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirect to summary
            window.location.href = `/merge/${data.reference_id}/summary`;
        } else {
            showError(data.error || 'Analysis failed');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideLoading();
    }
});
```

---

### 7.3 Navigation

```javascript
// Navigate between changes
function navigateToChange(direction) {
    const currentIndex = parseInt(document.getElementById('currentIndex').value);
    const totalChanges = parseInt(document.getElementById('totalChanges').value);
    const sessionId = document.getElementById('sessionId').value;
    
    let newIndex;
    if (direction === 'next') {
        newIndex = Math.min(currentIndex + 1, totalChanges - 1);
    } else if (direction === 'prev') {
        newIndex = Math.max(currentIndex - 1, 0);
    }
    
    // Navigate to change
    window.location.href = `/merge/${sessionId}/change/${newIndex}`;
}

// Jump to specific change
function jumpToChange(index) {
    const sessionId = document.getElementById('sessionId').value;
    window.location.href = `/merge/${sessionId}/change/${index}`;
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
        navigateToChange('prev');
    } else if (e.key === 'ArrowRight') {
        navigateToChange('next');
    }
});
```

---

### 7.4 Review Actions

```javascript
// Mark change as reviewed
async function markAsReviewed(changeId, notes) {
    try {
        const response = await fetch(`/merge/change/${changeId}/review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                review_status: 'reviewed',
                user_notes: notes
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('Change marked as reviewed');
            navigateToChange('next');
        } else {
            showError(data.error);
        }
    } catch (error) {
        showError('Failed to save review: ' + error.message);
    }
}

// Skip change
async function skipChange(changeId) {
    try {
        const response = await fetch(`/merge/change/${changeId}/review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                review_status: 'skipped'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            navigateToChange('next');
        } else {
            showError(data.error);
        }
    } catch (error) {
        showError('Failed to skip: ' + error.message);
    }
}
```

---

### 7.5 Report Generation

```javascript
// Generate Excel report
async function generateReport(sessionId) {
    const btn = document.getElementById('generateReportBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    
    try {
        const response = await fetch(`/merge/${sessionId}/report`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Download file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `merge_report_${sessionId}.xlsx`;
            a.click();
            
            showSuccess('Report generated successfully');
        } else {
            const data = await response.json();
            showError(data.error || 'Failed to generate report');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-file-excel"></i> Generate Report';
    }
}
```

---

### 7.6 Syntax Highlighting

```javascript
// Initialize Prism.js for SAIL code highlighting
document.addEventListener('DOMContentLoaded', () => {
    // Highlight all code blocks
    Prism.highlightAll();
    
    // Custom SAIL language definition
    Prism.languages.sail = {
        'comment': /\/\*[\s\S]*?\*\/|\/\/.*/,
        'string': /(["'])(?:\\(?:\r\n|[\s\S])|(?!\1)[^\\\r\n])*\1/,
        'keyword': /\b(?:a!localVariables|a!sectionLayout|a!textField|a!buttonWidget|if|then|else|null|true|false)\b/,
        'function': /\b[a-z_]\w*(?=\()/i,
        'number': /\b0x[\da-f]+\b|(?:\b\d+\.?\d*|\B\.\d+)(?:e[+-]?\d+)?/i,
        'operator': /[<>]=?|[!=]=?=?|--?|\+\+?|&&?|\|\|?|[?*/~^%]/,
        'punctuation': /[{}[\];(),.:]/
    };
});
```

---

### 7.7 Mermaid Diagrams

```javascript
// Initialize Mermaid for process model diagrams
document.addEventListener('DOMContentLoaded', () => {
    mermaid.initialize({
        startOnLoad: true,
        theme: 'dark',
        themeVariables: {
            primaryColor: '#8b5cf6',
            primaryTextColor: '#e2e8f0',
            primaryBorderColor: '#06b6d4',
            lineColor: '#64748b',
            secondaryColor: '#0f3460',
            tertiaryColor: '#1a1a2e'
        }
    });
});

// Render process model diagram
function renderProcessModelDiagram(mermaidSyntax, elementId) {
    const element = document.getElementById(elementId);
    mermaid.render('diagram-' + elementId, mermaidSyntax, (svg) => {
        element.innerHTML = svg;
    });
}
```

---

### 7.8 Utility Functions

```javascript
// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${getIconForType(type)}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showSuccess(message) { showToast(message, 'success'); }
function showError(message) { showToast(message, 'error'); }
function showWarning(message) { showToast(message, 'warning'); }
function showInfo(message) { showToast(message, 'info'); }

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Show/hide loading overlay
function showLoading(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i>
            <div class="loading-message">${message}</div>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.remove();
}
```

---

## 8. Data Binding

### 8.1 Template Variables

**Session Data**:
```python
{
    'session': {
        'id': int,
        'reference_id': str,
        'status': str,
        'base_package_name': str,
        'customized_package_name': str,
        'new_vendor_package_name': str,
        'total_changes': int,
        'created_at': datetime,
        'updated_at': datetime,
        'total_time': int
    }
}
```

**Change Data**:
```python
{
    'change': {
        'id': int,
        'object_id': int,
        'name': str,
        'type': str,  # Interface, Process Model, etc.
        'classification': str,  # NO_CONFLICT, CONFLICT, NEW, DELETED
        'vendor_change_type': str,
        'customer_change_type': str,
        'review_status': str
    }
}
```

**Comparison Data** (object-specific):
```python
{
    'interface_comparison': {
        'sail_code_diff': str,
        'parameters_added': list,
        'parameters_removed': list,
        'parameters_modified': list,
        'security_changes': list
    }
}
```

---

*End of UI/Template Specification*
