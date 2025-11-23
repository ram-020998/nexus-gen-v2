"""
Base XML parser for Appian objects
"""
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..models import AppianObject
from ..version_history_extractor import VersionHistoryExtractor


class XMLParser(ABC):
    """Abstract base class for XML parsers"""
    
    def __init__(self):
        self.namespaces = {
            'a': 'http://www.appian.com/ae/types/2009',
            'xsd': 'http://www.w3.org/2001/XMLSchema'
        }
        self.version_extractor = VersionHistoryExtractor()
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the file"""
        pass
    
    @abstractmethod
    def parse(self, root: ET.Element, file_path: str) -> Optional[AppianObject]:
        """Parse XML and return Appian object"""
        pass
    
    def _get_element_text(self, parent: ET.Element, xpath: str) -> str:
        """Safely get element text"""
        elem = parent.find(xpath, self.namespaces)
        return elem.text.strip() if elem is not None and elem.text else ""
    
    def extract_raw_xml(self, root: ET.Element) -> str:
        """Extract complete raw XML content"""
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def extract_version_history(self, root: ET.Element):
        """Extract version history from XML metadata"""
        return self.version_extractor.extract_from_xml(root)
    
    def extract_current_version_uuid(self, root: ET.Element) -> str:
        """Extract current version UUID from XML"""
        version_uuid = self.version_extractor.extract_current_version_uuid(root)
        return version_uuid if version_uuid else ""
    
    def extract_all_elements(self, element: ET.Element) -> Dict[str, Any]:
        """Recursively extract all XML elements and attributes"""
        result = {}
        
        # Extract attributes
        if element.attrib:
            result['@attributes'] = dict(element.attrib)
        
        # Extract text content
        if element.text and element.text.strip():
            result['@text'] = element.text.strip()
        
        # Extract child elements
        for child in element:
            tag = child.tag
            # Remove namespace prefix for cleaner keys
            if '}' in tag:
                tag = tag.split('}')[1]
            
            child_data = self.extract_all_elements(child)
            
            # Handle multiple children with same tag
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_data)
            else:
                result[tag] = child_data
        
        return result
