"""
Parser for Appian Record Type objects
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ..models import RecordType
from .base_parser import XMLParser


class RecordTypeParser(XMLParser):
    """Parser for Record Type objects"""
    
    def can_parse(self, file_path: str) -> bool:
        return 'recordType/' in file_path
    
    def parse(self, root: ET.Element, file_path: str) -> Optional[RecordType]:
        record_elem = root.find('recordType')
        if record_elem is None:
            return None
        
        uuid = record_elem.get('{http://www.appian.com/ae/types/2009}uuid')
        name = record_elem.get('name')
        desc_elem = record_elem.find('a:description', self.namespaces)
        description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
        
        if not uuid or not name:
            return None
        
        record = RecordType(uuid=uuid, name=name, object_type="Record Type", description=description)
        record.fields = self._parse_fields(record_elem)
        record.relationships = self._parse_relationships(record_elem)
        record.actions = self._parse_actions(record_elem)
        record.views = self._parse_views(record_elem)
        record.security = {"roles": []}  # Simplified
        
        # Extract raw XML and all elements
        record.raw_xml = self.extract_raw_xml(root)
        record.raw_xml_data = self.extract_all_elements(root)
        
        # Extract version information
        record.version_uuid = self.extract_current_version_uuid(root)
        record.version_history = self.extract_version_history(root)
        
        return record
    
    def _parse_fields(self, record_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse record fields"""
        fields = []
        for field_elem in record_elem.findall('.//a:field', self.namespaces):
            field_data = {
                "name": self._get_element_text(field_elem, 'a:name'),
                "type": self._get_element_text(field_elem, 'a:type'),
                "required": self._get_element_text(field_elem, 'a:required') == 'true',
                "primary_key": self._get_element_text(field_elem, 'a:primaryKey') == 'true'
            }
            fields.append(field_data)
        return fields
    
    def _parse_relationships(self, record_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse record relationships"""
        relationships = []
        for rel_elem in record_elem.findall('.//a:recordRelationshipCfg', self.namespaces):
            # Relationship elements are direct children without namespace prefix
            uuid_elem = rel_elem.find('uuid')
            name_elem = rel_elem.find('relationshipName')
            target_elem = rel_elem.find('targetRecordTypeUuid')
            type_elem = rel_elem.find('relationshipType')
            
            rel_data = {
                "uuid": uuid_elem.text if uuid_elem is not None else "",
                "name": name_elem.text if name_elem is not None else "",
                "target_record": {
                    "uuid": target_elem.text if target_elem is not None else "",
                    "name": "Unknown"
                },
                "type": type_elem.text if type_elem is not None else ""
            }
            relationships.append(rel_data)
        return relationships
    
    def _parse_actions(self, record_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse record actions (both related actions and record list actions)"""
        actions = []
        
        # Parse related actions (actions on individual records)
        for action_elem in record_elem.findall('.//a:relatedActionCfg', self.namespaces):
            target_elem = action_elem.find('a:target', self.namespaces)
            target_uuid = target_elem.get('{http://www.appian.com/ae/types/2009}uuid') if target_elem is not None else None
            
            action_data = {
                "uuid": action_elem.get('{http://www.appian.com/ae/types/2009}uuid'),
                "title": self._get_element_text(action_elem, 'a:titleExpr'),
                "description": self._get_element_text(action_elem, 'a:descriptionExpr'),
                "type": "Related Action",
                "target_process": {"uuid": target_uuid, "name": "Unknown"},
                "context": self._get_element_text(action_elem, 'a:contextExpr'),
                "visibility": self._get_element_text(action_elem, 'a:visibilityExpr'),
                "security": {}
            }
            actions.append(action_data)
        
        # Parse record list actions (actions on record lists, like Create)
        for action_elem in record_elem.findall('.//a:recordListActionCfg', self.namespaces):
            target_elem = action_elem.find('a:target', self.namespaces)
            target_uuid = target_elem.get('{http://www.appian.com/ae/types/2009}uuid') if target_elem is not None else None
            
            action_data = {
                "uuid": action_elem.get('{http://www.appian.com/ae/types/2009}uuid'),
                "title": self._get_element_text(action_elem, 'a:titleExpr'),
                "description": self._get_element_text(action_elem, 'a:staticDescription'),
                "type": "Record List Action",
                "target_process": {"uuid": target_uuid, "name": "Unknown"},
                "context": self._get_element_text(action_elem, 'a:contextExpr'),
                "visibility": self._get_element_text(action_elem, 'a:visibilityExpr'),
                "icon": self._get_element_text(action_elem, 'a:iconId'),
                "security": {}
            }
            actions.append(action_data)
        
        return actions
    
    def _parse_views(self, record_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse record views"""
        views = []
        for view_elem in record_elem.findall('.//a:recordView', self.namespaces):
            view_data = {
                "name": self._get_element_text(view_elem, 'a:name'),
                "type": self._get_element_text(view_elem, 'a:type')
            }
            views.append(view_data)
        return views
