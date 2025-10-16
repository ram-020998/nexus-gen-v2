/**
 * Upload functionality with drag & drop
 */

document.addEventListener('DOMContentLoaded', function() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const uploadContent = document.getElementById('uploadContent');
    const processingContent = document.getElementById('processingContent');
    const processingText = document.getElementById('processingText');
    
    // Drag and drop handlers
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);
    
    // Click handler for upload zone (but not button)
    uploadZone.addEventListener('click', (e) => {
        // Only trigger if clicking on the zone itself, not the button
        if (e.target === uploadZone || e.target.closest('.upload-content')) {
            if (!uploadZone.classList.contains('processing') && !e.target.closest('button')) {
                fileInput.click();
            }
        }
    });
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    function handleDragOver(e) {
        e.preventDefault();
        if (!uploadZone.classList.contains('processing')) {
            uploadZone.classList.add('dragover');
        }
    }
    
    function handleDragLeave(e) {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        if (!uploadZone.classList.contains('processing')) {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                uploadFile(files[0]);
            }
        }
    }
    
    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
        // Reset file input to allow selecting the same file again
        e.target.value = '';
    }
    
    function uploadFile(file) {
        // Prevent multiple uploads
        if (uploadZone.classList.contains('processing')) {
            return;
        }
        
        // Show processing state
        showProcessing(file.name);
        
        const formData = new FormData();
        formData.append('file', file);
        
        // Simulate progress steps
        const steps = [
            { text: 'Uploading file...', delay: 500 },
            { text: 'Extracting content...', delay: 1000 },
            { text: 'Querying knowledge base...', delay: 1500 },
            { text: 'Generating breakdown...', delay: 2000 },
            { text: 'Finalizing results...', delay: 2500 }
        ];
        
        let stepIndex = 0;
        const progressInterval = setInterval(() => {
            if (stepIndex < steps.length) {
                processingText.textContent = steps[stepIndex].text;
                stepIndex++;
            }
        }, 600);
        
        fetch('/breakdown/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            if (data.success) {
                showSuccess();
                DocFlow.showNotification('File uploaded and processed successfully!', 'success');
                
                // Redirect to results page after a short delay
                setTimeout(() => {
                    window.location.href = `/breakdown/results/${data.request_id}`;
                }, 1500);
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            console.error('Upload error:', error);
            DocFlow.showNotification(error.message, 'error');
            resetUpload();
        });
    }
    
    function showProcessing(filename) {
        uploadZone.classList.add('processing');
        uploadContent.style.display = 'none';
        processingContent.style.display = 'block';
        processingText.textContent = `Processing ${filename}...`;
    }
    
    function showSuccess() {
        processingContent.innerHTML = `
            <div class="processing-icon">
                <i class="fas fa-check-circle text-success" style="font-size: 3rem;"></i>
            </div>
            <h3 class="text-success">Processing Complete!</h3>
            <p>Breakdown generated successfully. Redirecting to results...</p>
        `;
    }
    
    function resetUpload() {
        uploadZone.classList.remove('processing');
        uploadContent.style.display = 'block';
        processingContent.style.display = 'none';
        // Reset file input
        fileInput.value = '';
    }
});
