"""
Document Service - Extract content from various file formats
"""
import docx
from pathlib import Path


class DocumentService:
    """Handle document content extraction"""

    def extract_content(self, file_path: str) -> str:
        """Extract text content from document"""
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
        """Read plain text file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, 'r', encoding='latin-1') as f:
                return f.read()

    def _read_docx_file(self, path: Path) -> str:
        """Read DOCX file content"""
        try:
            doc = docx.Document(path)
            content = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)

            return '\n'.join(content)
        except Exception as e:

            return f"Error reading document: {str(e)}"
