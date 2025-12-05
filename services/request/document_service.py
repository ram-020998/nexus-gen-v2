"""
Document Service - Extract content from various file formats

This is the refactored class-based implementation with dependency injection.
"""
from pathlib import Path
import docx
from core.base_service import BaseService


class DocumentService(BaseService):
    """
    Service for handling document content extraction

    Supports extraction from various file formats including text,
    markdown, and DOCX.
    """

    def _initialize_dependencies(self):
        """Initialize service dependencies"""
        pass  # No dependencies needed for this service

    def extract_content(self, file_path: str) -> str:
        """
        Extract text content from document

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content as string
        """
        path = Path(file_path)

        if path.suffix.lower() == '.txt':
            return self._read_text_file(path)
        elif path.suffix.lower() == '.md':
            return self._read_text_file(path)
        elif path.suffix.lower() == '.docx':
            return self._read_docx_file(path)
        else:
            # Fallback to text reading
            return self._read_text_file(path)

    def _read_text_file(self, path: Path) -> str:
        """
        Read plain text file

        Args:
            path: Path object pointing to the text file

        Returns:
            File content as string
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, 'r', encoding='latin-1') as f:
                return f.read()

    def _read_docx_file(self, path: Path) -> str:
        """
        Read DOCX file content

        Args:
            path: Path object pointing to the DOCX file

        Returns:
            Extracted text content as string
        """
        try:
            doc = docx.Document(path)
            content = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)

            return '\n'.join(content)
        except Exception as e:
            return f"Error reading document: {str(e)}"
