"""
Parser for Appian content objects (interfaces, rules, constants, etc.)
"""
import xml.etree.ElementTree as ET
from typing import Optional
from ..models import SimpleObject
from .base_parser import XMLParser


class ContentParser(XMLParser):
    """Parser for content objects (interfaces, rules, constants, etc.)"""
    
    def can_parse(self, file_path: str) -> bool:
        return 'content/' in file_path
    
    def parse(self, root: ET.Element, file_path: str) -> Optional[SimpleObject]:
        for child in root:
            if child.tag.endswith('Haul') or child.tag in ['versionUuid', 'roleMap', 'history', 'migrationVersion']:
                continue
            
            # Check for child elements (newer format)
            uuid_elem = child.find('uuid')
            name_elem = child.find('name')
            desc_elem = child.find('description')
            
            if uuid_elem is not None and name_elem is not None:
                uuid = uuid_elem.text
                name = name_elem.text
                description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                object_type = self._determine_content_type(child.tag)
                
                # Extract SAIL code from definition tag for interfaces and rules, typedValue for constants
                sail_code = ""
                if object_type in ['Interface', 'Expression Rule']:
                    definition_elem = child.find('definition')
                    if definition_elem is not None and definition_elem.text:
                        sail_code = definition_elem.text.strip()
                elif object_type == 'Constant':
                    typed_value_elem = child.find('typedValue')
                    if typed_value_elem is not None:
                        # Check for direct text content
                        if typed_value_elem.text and typed_value_elem.text.strip():
                            sail_code = typed_value_elem.text.strip()
                        else:
                            # Check for nested structure
                            type_elem = typed_value_elem.find('type')
                            value_elem = typed_value_elem.find('value')
                            
                            if type_elem is not None:
                                type_name = type_elem.find('name')
                                type_name_text = type_name.text if type_name is not None else ""
                                
                                if value_elem is not None:
                                    # Extract value based on type
                                    if value_elem.text:
                                        sail_code = f"Type: {type_name_text}, Value: {value_elem.text}"
                                    elif value_elem.get('id'):
                                        sail_code = f"Type: {type_name_text}, ID: {value_elem.get('id')}"
                                    else:
                                        sail_code = f"Type: {type_name_text}"
                
                obj = SimpleObject(
                    uuid=uuid, 
                    name=name, 
                    object_type=object_type, 
                    description=description,
                    sail_code=sail_code
                )
                
                # Extract raw XML and all elements
                obj.raw_xml = self.extract_raw_xml(root)
                obj.raw_xml_data = self.extract_all_elements(root)
                
                # Extract version information
                obj.version_uuid = self.extract_current_version_uuid(root)
                obj.version_history = self.extract_version_history(root)
                
                return obj
        
        return None
    
    def _determine_content_type(self, tag: str) -> str:
        """Determine content object type"""
        type_mapping = {
            'interface': 'Interface',
            'rule': 'Expression Rule',
            'constant': 'Constant',
            'datatype': 'Data Type',
            'decision': 'Decision',
            'queryRule': 'Query Rule',
            'document': 'Document',
            'folder': 'Folder',
            'rulesFolder': 'Rules Folder',
            'communityKnowledgeCenter': 'Knowledge Center',
            'contentFreeformRule': 'Content Rule'
        }
        clean_tag = tag.split('}')[-1] if '}' in tag else tag
        return type_mapping.get(clean_tag, clean_tag)
