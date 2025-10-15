"""
File Upload Service
"""
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from config import Config

class FileService:
    """Handle file upload operations"""
    
    def __init__(self):
        self.config = Config
        self.config.init_directories()
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in self.config.ALLOWED_EXTENSIONS)
    
    def save_upload(self, file: FileStorage, request_id: int) -> str:
        """Save uploaded file and return path"""
        if not file or not file.filename:
            raise ValueError("No file provided")
        
        if not self.is_allowed_file(file.filename):
            raise ValueError(f"File type not allowed. Supported: {self.config.ALLOWED_EXTENSIONS}")
        
        # Create secure filename with request ID
        filename = secure_filename(file.filename)
        timestamped_filename = f"{request_id}_{filename}"
        file_path = self.config.UPLOAD_FOLDER / timestamped_filename
        
        # Save file
        file.save(str(file_path))
        
        return str(file_path)
    
    def get_recent_uploads(self, limit: int = 5) -> list:
        """Get recent uploaded files"""
        if not self.config.UPLOAD_FOLDER.exists():
            return []
        
        files = []
        for file_path in self.config.UPLOAD_FOLDER.iterdir():
            if file_path.is_file():
                files.append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime
                })
        
        # Sort by modification time, newest first
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files[:limit]
