/**
 * Upload functionality with drag & drop
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const previewPanel = document.getElementById('previewPanel');
    
    // Drag and drop handlers
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);
    uploadZone.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    function handleDragOver(e) {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    }
    
    function handleDragLeave(e) {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    }
    
    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    }
    
    function uploadFile(file) {
        // Show processing state
        showProcessing();
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/breakdown/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showPreview(data.breakdown_data);
                DocFlow.showNotification('File uploaded and processed successfully!', 'success');
                
                // Redirect to results page after a short delay
                setTimeout(() => {
                    window.location.href = `/breakdown/results/${data.request_id}`;
                }, 2000);
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            DocFlow.showNotification(error.message, 'error');
            resetPreview();
        });
    }
    
    function showProcessing() {
        previewPanel.innerHTML = `
            <div class="processing">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h4 class="mt-3">Processing Document</h4>
                <p>Analyzing content and generating breakdown...</p>
            </div>
        `;
    }
    
    function showPreview(breakdownData) {
        previewPanel.innerHTML = `
            <div class="breakdown-preview">
                <div class="preview-icon">
                    <i class="fas fa-check-circle text-success"></i>
                </div>
                <h4>Breakdown Generated</h4>
                <p><strong>Epic:</strong> ${breakdownData.epic}</p>
                <table class="breakdown-table">
                    <thead>
                        <tr>
                            <th>Story Name</th>
                            <th>Issue Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${breakdownData.stories.map(story => `
                            <tr>
                                <td>${story.story_name}</td>
                                <td>${story.issue_type}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <p class="mt-2 text-success">
                    <i class="fas fa-info-circle"></i> 
                    Redirecting to full results...
                </p>
            </div>
        `;
    }
    
    function resetPreview() {
        previewPanel.innerHTML = `
            <div class="preview-icon">
                <i class="fas fa-table"></i>
            </div>
            <h4>Parsed Data Preview</h4>
            <p>Upload a document to see parsed data</p>
        `;
    }
});
