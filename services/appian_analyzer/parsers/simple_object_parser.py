"""
Parser for simple Appian objects (groups, connected systems, web APIs, reports)
"""
import xml.etree.ElementTree as ET
from typing import Optional
from ..models import SimpleObject
from .base_parser import XMLParser


class SimpleObjectParser(XMLParser):
    """Parser for simple objects (groups, connected systems, etc.)"""
    
    def __init__(self, object_type: str, path_pattern: str):
        super().__init__()
        self.object_type = object_type
        self.path_pattern = path_pattern
    
    def can_parse(self, file_path: str) -> bool:
        return self.path_pattern in file_path
    
    def parse(self, root: ET.Element, file_path: str) -> Optional[SimpleObject]:
        if self.object_type == "Security Group":
            return self._parse_group(root)
        elif self.object_type == "Connected System":
            return self._parse_connected_system(root)
        elif self.object_type == "Web API":
            return self._parse_web_api(root)
        elif self.object_type == "Report":
            return self._parse_report(root)
        return None
    
    def _parse_group(self, root: ET.Element) -> Optional[SimpleObject]:
        group_elem = root.find('group')
        if group_elem is None:
            return None
        
        uuid_elem = group_elem.find('uuid')
        name_elem = group_elem.find('name')
        desc_elem = group_elem.find('description')
        
        if uuid_elem is None or name_elem is None:
            return None
        
        obj = SimpleObject(
            uuid=uuid_elem.text,
            name=name_elem.text,
            object_type="Security Group",
            description=desc_elem.text if desc_elem is not None and desc_elem.text else ""
        )
        
        # Extract raw XML and all elements
        obj.raw_xml = self.extract_raw_xml(root)
        obj.raw_xml_data = self.extract_all_elements(root)
        
        # Extract version information
        obj.version_uuid = self.extract_current_version_uuid(root)
        obj.version_history = self.extract_version_history(root)
        
        return obj
    
    def _parse_connected_system(self, root: ET.Element) -> Optional[SimpleObject]:
        cs_elem = root.find('connectedSystem')
        if cs_elem is None:
            return None
        
        uuid = cs_elem.get('{http://www.appian.com/ae/types/2009}uuid')
        name = cs_elem.get('name')
        desc_elem = cs_elem.find('a:description', self.namespaces)
        description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
        
        # Extract integration type and configuration
        integration_type_elem = cs_elem.find('integrationType')
        integration_type = integration_type_elem.text if integration_type_elem is not None and integration_type_elem.text else ""
        
        sail_code = f"Integration Type: {integration_type}" if integration_type else ""
        
        if not uuid or not name:
            return None
        
        obj = SimpleObject(uuid=uuid, name=name, object_type="Connected System", description=description, sail_code=sail_code)
        
        # Extract raw XML and all elements
        obj.raw_xml = self.extract_raw_xml(root)
        obj.raw_xml_data = self.extract_all_elements(root)
        
        # Extract version information
        obj.version_uuid = self.extract_current_version_uuid(root)
        obj.version_history = self.extract_version_history(root)
        
        return obj
    
    def _parse_web_api(self, root: ET.Element) -> Optional[SimpleObject]:
        api_elem = root.find('webApi')
        if api_elem is None:
            return None
        
        uuid = api_elem.get('{http://www.appian.com/ae/types/2009}uuid')
        name = api_elem.get('name')
        desc_elem = api_elem.find('a:description', self.namespaces)
        description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
        
        # Extract expression (the main logic)
        expr_elem = api_elem.find('a:expression', self.namespaces)
        sail_code = expr_elem.text if expr_elem is not None and expr_elem.text else ""
        
        if not uuid or not name:
            return None
        
        obj = SimpleObject(uuid=uuid, name=name, object_type="Web API", description=description, sail_code=sail_code)
        
        # Extract raw XML and all elements
        obj.raw_xml = self.extract_raw_xml(root)
        obj.raw_xml_data = self.extract_all_elements(root)
        
        # Extract version information
        obj.version_uuid = self.extract_current_version_uuid(root)
        obj.version_history = self.extract_version_history(root)
        
        return obj
    
    def _parse_report(self, root: ET.Element) -> Optional[SimpleObject]:
        report_elem = root.find('tempoReport')
        if report_elem is None:
            return None
        
        uuid = report_elem.get('{http://www.appian.com/ae/types/2009}uuid')
        name = report_elem.get('name')
        desc_elem = report_elem.find('a:description', self.namespaces)
        description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
        
        # Extract UI expression (the main content)
        ui_expr_elem = report_elem.find('a:uiExpr', self.namespaces)
        sail_code = ui_expr_elem.text if ui_expr_elem is not None and ui_expr_elem.text else ""
        
        if not uuid or not name:
            return None
        
        obj = SimpleObject(uuid=uuid, name=name, object_type="Report", description=description, sail_code=sail_code)
        
        # Extract raw XML and all elements
        obj.raw_xml = self.extract_raw_xml(root)
        obj.raw_xml_data = self.extract_all_elements(root)
        
        # Extract version information
        obj.version_uuid = self.extract_current_version_uuid(root)
        obj.version_history = self.extract_version_history(root)
        
        return obj
