"""
Parser for Appian Site objects
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ..models import Site
from .base_parser import XMLParser


class SiteParser(XMLParser):
    """Parser for Site objects"""
    
    def can_parse(self, file_path: str) -> bool:
        return 'site/' in file_path
    
    def parse(self, root: ET.Element, file_path: str) -> Optional[Site]:
        site_elem = root.find('site')
        if site_elem is None:
            return None
        
        uuid = site_elem.get('{http://www.appian.com/ae/types/2009}uuid')
        name = site_elem.get('name')
        desc_elem = site_elem.find('description')
        description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
        
        if not uuid or not name:
            return None
        
        site = Site(uuid=uuid, name=name, object_type="Site", description=description)
        site.pages = self._parse_pages(site_elem)
        site.security = self._parse_security(root)
        
        # Extract raw XML and all elements
        site.raw_xml = self.extract_raw_xml(root)
        site.raw_xml_data = self.extract_all_elements(root)
        
        # Extract version information
        site.version_uuid = self.extract_current_version_uuid(root)
        site.version_history = self.extract_version_history(root)
        
        return site
    
    def _parse_pages(self, site_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse site pages"""
        pages = []
        for page_elem in site_elem.findall('page', self.namespaces):
            page_uuid = page_elem.get('{http://www.appian.com/ae/types/2009}uuid')
            static_name = self._get_element_text(page_elem, 'staticName')
            
            page_data = {
                "uuid": page_uuid,
                "name": static_name,
                "ui_objects": [],
                "visibility": self._get_element_text(page_elem, 'visibilityExpr')
            }
            
            ui_elem = page_elem.find('uiObject', self.namespaces)
            if ui_elem is not None:
                ui_uuid = ui_elem.get('{http://www.appian.com/ae/types/2009}uuid')
                ui_type = ui_elem.get('{http://www.w3.org/2001/XMLSchema-instance}type', '')
                page_data["ui_objects"].append({
                    "uuid": ui_uuid,
                    "name": "Unknown",  # Will be resolved later
                    "type": ui_type.replace('a:', '') if ui_type else "Unknown"
                })
            
            pages.append(page_data)
        
        return pages
    
    def _parse_security(self, root: ET.Element) -> Dict[str, Any]:
        """Parse security from roleMap"""
        security = {"roles": []}
        for role_elem in root.findall('.//roleMap/role'):
            role_name = role_elem.get('name')
            users = [u.text for u in role_elem.findall('.//userUuid')]
            group_uuids = [g.text for g in role_elem.findall('.//groupUuid')]
            
            if users or group_uuids:
                security["roles"].append({
                    "role": role_name,
                    "users": users,
                    "groups": [{"uuid": g, "name": "Unknown"} for g in group_uuids]
                })
        
        return security
