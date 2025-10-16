"""
Word Document Service - Generate Word documents for design exports
"""
from pathlib import Path
from config import Config
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

class WordService:
    """Handle Word document generation"""
    
    def __init__(self):
        self.config = Config
    
    def create_design_document(self, request_id: int, design_data: dict) -> str:
        """Create Word document for design data"""
        # Create output directory
        output_dir = self.config.OUTPUT_FOLDER / str(request_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Word document
        doc = Document()
        
        # Add title
        title = doc.add_heading('Design Document', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add overview section
        if 'design_document' in design_data and 'overview' in design_data['design_document']:
            doc.add_heading('Overview', level=1)
            doc.add_paragraph(design_data['design_document']['overview'])
        
        # Add objects section
        if 'design_document' in design_data and 'objects' in design_data['design_document']:
            doc.add_heading('Objects & Components', level=1)
            
            for obj in design_data['design_document']['objects']:
                # Object name as heading
                doc.add_heading(obj.get('name', 'Unknown Object'), level=2)
                
                # Object details
                doc.add_paragraph(f"Type: {obj.get('type', 'N/A')}")
                doc.add_paragraph(f"Description: {obj.get('description', 'No description')}")
                
                # Methods
                if obj.get('methods'):
                    doc.add_paragraph("Methods:")
                    for method in obj['methods']:
                        p = doc.add_paragraph(f"• {method}")
                        p.style = 'List Bullet'
        
        # Add implementation notes
        if 'design_document' in design_data and 'implementation_notes' in design_data['design_document']:
            doc.add_heading('Implementation Notes', level=1)
            for note in design_data['design_document']['implementation_notes']:
                p = doc.add_paragraph(f"• {note}")
                p.style = 'List Bullet'
        
        # Add dependencies
        if 'design_document' in design_data and 'dependencies' in design_data['design_document']:
            doc.add_heading('Dependencies', level=1)
            for dep in design_data['design_document']['dependencies']:
                p = doc.add_paragraph(f"• {dep}")
                p.style = 'List Bullet'
        
        # Save document
        filename = f"design_document_{request_id}.docx"
        file_path = output_dir / filename
        doc.save(str(file_path))
        
        return str(file_path)
