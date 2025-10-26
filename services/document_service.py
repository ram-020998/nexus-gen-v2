"""
Document Service - Extract content from various file formats
"""
import docx
import re
from pathlib import Path


class DocumentService:
    """Handle document content extraction"""

    def extract_content(self, file_path: str) -> str:
        """Extract text content from document"""
        path = Path(file_path)

        if path.suffix.lower() == '.txt':
            raw_text = self._read_text_file(path)
        elif path.suffix.lower() == '.md':
            raw_text = self._read_text_file(path)
        elif path.suffix.lower() == '.docx':
            raw_text = self._read_docx_file(path)
        else:
            # Fallback to text reading
            raw_text = self._read_text_file(path)
        
        return self._clean_text(raw_text)

    def _clean_text(self, raw_text: str) -> str:
        """Clean and normalize extracted text"""
        if not raw_text or raw_text.startswith("Error reading"):
            return raw_text
            
        # Remove multiple spaces/newlines
        text = re.sub(r'\s+', ' ', raw_text)
        # Remove headers/footers like "Page X of Y"
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        # Strip non-printable characters
        text = re.sub(r'[^\x20-\x7E]+', ' ', text)
        return text.strip()

    def detect_sections(self, text: str) -> dict:
        """Detect and extract common document sections"""
        sections = {}
        
        # Split by common section headers
        patterns = [
            r'(Acceptance Criteria:)',
            r'(User Stories:)',
            r'(Requirements:)',
            r'(Overview:)',
            r'(Background:)'
        ]
        
        for pattern in patterns:
            matches = re.split(pattern, text, flags=re.IGNORECASE)
            if len(matches) > 1:
                section_name = matches[1].replace(':', '').strip().lower()
                if len(matches) > 2:
                    sections[section_name] = matches[2].split('\n')[0:5]  # First 5 lines
        
        return sections

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
