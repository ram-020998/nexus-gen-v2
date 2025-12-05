"""
File Upload Service

This is the refactored class-based implementation with dependency injection.
"""
from typing import List, Dict, Any
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from core.base_service import BaseService
from config import Config


class FileService(BaseService):
    """
    Service for handling file upload operations

    Manages file validation, secure storage, and retrieval of uploaded
    files.
    """

    def _initialize_dependencies(self):
        """Initialize service dependencies"""
        self.config = Config
        self.config.init_directories()

    def is_allowed_file(self, filename: str) -> bool:
        """
        Check if file extension is allowed

        Args:
            filename: Name of the file to check

        Returns:
            True if file extension is allowed, False otherwise
        """
        return ('.' in filename and
                filename.rsplit('.', 1)[1].lower() in
                self.config.ALLOWED_EXTENSIONS)

    def save_upload(self, file: FileStorage, request_id: int) -> str:
        """
        Save uploaded file and return path

        Args:
            file: FileStorage object from Flask request
            request_id: ID of the associated request

        Returns:
            Path to the saved file as string

        Raises:
            ValueError: If no file provided or file type not allowed
        """
        if not file or not file.filename:
            raise ValueError("No file provided")

        if not self.is_allowed_file(file.filename):
            allowed = self.config.ALLOWED_EXTENSIONS
            raise ValueError(f"File type not allowed. Supported: {allowed}")

        # Create secure filename with request ID
        filename = secure_filename(file.filename)
        timestamped_filename = f"{request_id}_{filename}"
        file_path = self.config.UPLOAD_FOLDER / timestamped_filename

        # Save file
        file.save(str(file_path))

        return str(file_path)

    def get_recent_uploads(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent uploaded files

        Args:
            limit: Maximum number of files to return

        Returns:
            List of dictionaries containing file information
            (name, size, modified)
        """
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
