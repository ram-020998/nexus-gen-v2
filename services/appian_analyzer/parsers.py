"""
XML parsers for different Appian object types
"""
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from .models import AppianObject, Site, RecordType, ProcessModel, SimpleObject
from .version_history_extractor import VersionHistoryExtractor

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

class ProcessModelParser(XMLParser):
    """Parser for Process Model objects"""
    
    def can_parse(self, file_path: str) -> bool:
        return 'processModel/' in file_path
    
    def parse(self, root: ET.Element, file_path: str) -> Optional[ProcessModel]:
        pm_port = root.find('{http://www.appian.com/ae/types/2009}process_model_port')
        if pm_port is None:
            return None
        
        pm_elem = pm_port.find('{http://www.appian.com/ae/types/2009}pm')
        if pm_elem is None:
            return None
        
        meta_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}meta')
        if meta_elem is None:
            return None
        
        uuid_elem = meta_elem.find('{http://www.appian.com/ae/types/2009}uuid')
        name_elem = meta_elem.find('{http://www.appian.com/ae/types/2009}name')
        desc_elem = meta_elem.find('{http://www.appian.com/ae/types/2009}desc')
        
        uuid = uuid_elem.text if uuid_elem is not None and uuid_elem.text else None
        
        # Parse name from string-map structure
        name = self._parse_string_map(name_elem) if name_elem is not None else None
        
        # Parse description from string-map structure  
        description = self._parse_string_map(desc_elem) if desc_elem is not None else ""
        
        if not uuid:
            return None
        
        if not name:
            name = f"Process Model {uuid.split('-')[0]}"
        
        process = ProcessModel(uuid=uuid, name=name, object_type="Process Model", description=description)
        process.variables = self._parse_variables(pm_elem)
        process.nodes = self._parse_nodes(pm_elem)
        process.flows = self._parse_flows(pm_elem)
        process.interfaces = self._parse_interfaces(pm_elem)
        process.rules = self._parse_rules(pm_elem)
        process.business_logic = self._extract_complete_business_logic(pm_elem)
        process.security = self._parse_security(root)
        
        # Extract raw XML and all elements
        process.raw_xml = self.extract_raw_xml(root)
        process.raw_xml_data = self.extract_all_elements(root)
        
        # Extract version information
        process.version_uuid = self.extract_current_version_uuid(root)
        process.version_history = self.extract_version_history(root)
        
        return process
    
    def _extract_complete_business_logic(self, pm_elem: ET.Element) -> str:
        """Extract all business logic from process model nodes"""
        business_logic_parts = []
        
        nodes_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}nodes')
        if nodes_elem is not None:
            for node in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
                ac_elem = node.find('{http://www.appian.com/ae/types/2009}ac')
                if ac_elem is not None:
                    # Get node name
                    name_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}name')
                    node_name = name_elem.text if name_elem is not None and name_elem.text else "Unnamed Node"
                    
                    node_logic = f"=== NODE: {node_name} ===\\n"
                    
                    # Extract all expressions and logic from AC
                    for child in ac_elem.iter():
                        if child.text and child.text.strip():
                            # Skip simple values and focus on expressions/logic
                            text = child.text.strip()
                            if any(keyword in text for keyword in ['rule!', '#"', 'if(', 'and(', 'or(', 'not(', 'local!', 'pv!', 'rv!', 'cons!', 'fn!']):
                                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                                node_logic += f"{tag_name}: {text}\\n"
                    
                    # Extract output expressions
                    output_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}output-exprs')
                    if output_elem is not None and output_elem.text and output_elem.text.strip():
                        node_logic += f"output-exprs: {output_elem.text.strip()}\\n"
                    
                    if node_logic != f"=== NODE: {node_name} ===\\n":
                        business_logic_parts.append(node_logic)
        
        return "\\n".join(business_logic_parts) if business_logic_parts else ""
    
    def _parse_string_map(self, elem: ET.Element) -> str:
        """Parse string-map structure to extract localized text"""
        if elem is None:
            return ""
        
        string_map = elem.find('a:string-map', self.namespaces)
        if string_map is not None:
            # Look for English locale pair
            for pair in string_map.findall('a:pair', self.namespaces):
                locale = pair.find('a:locale', self.namespaces)
                value = pair.find('a:value', self.namespaces)
                
                if locale is not None and value is not None:
                    lang = locale.get('lang', '')
                    if lang == 'en':  # English locale
                        return value.text.strip() if value.text else ""
            
            # Fallback to first pair if no English found
            first_pair = string_map.find('a:pair', self.namespaces)
            if first_pair is not None:
                value = first_pair.find('a:value', self.namespaces)
                if value is not None:
                    return value.text.strip() if value.text else ""
        
        # Fallback to direct text if no string-map
        return elem.text.strip() if elem.text else ""
    
    def _parse_variables(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse process variables with proper names and types"""
        variables = []
        
        pvs_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}pvs')
        if pvs_elem is not None:
            for pv in pvs_elem.findall('{http://www.appian.com/ae/types/2009}pv'):
                # Parse name from string-map
                name_elem = pv.find('{http://www.appian.com/ae/types/2009}name')
                name = self._parse_string_map(name_elem) if name_elem is not None else ""
                
                # Parse type
                type_elem = pv.find('{http://www.appian.com/ae/types/2009}type')
                var_type = type_elem.text if type_elem is not None and type_elem.text else ""
                
                # Parse parameter flag
                param_elem = pv.find('{http://www.appian.com/ae/types/2009}parameter')
                is_parameter = param_elem.text == 'true' if param_elem is not None else False
                
                # Parse required flag
                req_elem = pv.find('{http://www.appian.com/ae/types/2009}required')
                is_required = req_elem.text == 'true' if req_elem is not None else False
                
                # Parse multiple flag
                mult_elem = pv.find('{http://www.appian.com/ae/types/2009}multiple')
                is_multiple = mult_elem.text == 'true' if mult_elem is not None else False
                
                if name:  # Only add if name exists
                    var_data = {
                        "name": name,
                        "type": var_type,
                        "parameter": is_parameter,
                        "required": is_required,
                        "multiple": is_multiple
                    }
                    variables.append(var_data)
        
        return variables
    
    def _parse_interfaces(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse interfaces used in the process model"""
        interfaces = []
        interface_uuids = set()
        
        # Extract from form-map (these are definitely interfaces)
        form_map = pm_elem.find('{http://www.appian.com/ae/types/2009}form-map')
        if form_map is not None:
            for ui_expr in form_map.findall('.//{http://www.appian.com/ae/types/2009}uiExpressionForm'):
                expr_elem = ui_expr.find('{http://www.appian.com/ae/types/2009}expression')
                if expr_elem is not None and expr_elem.text:
                    # Extract UUID from expression like #\"_a-uuid\"
                    import re
                    uuid_match = re.search(r'#\"(_a-[^\"]+)\"', expr_elem.text)
                    if uuid_match:
                        interface_uuid = uuid_match.group(1)
                        interface_uuids.add(interface_uuid)
        
        # Convert to list with resolved names and filter by object type
        for uuid in interface_uuids:
            # Check if this UUID is actually an interface in our lookup
            obj = self.object_lookup.get(uuid) if hasattr(self, 'object_lookup') else None
            if obj and obj.get('object_type') == 'Interface':
                interfaces.append({
                    "uuid": uuid,
                    "name": "Unknown"  # Will be resolved later
                })
        
        return interfaces
    
    def _parse_rules(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse rules used in the process model"""
        rules = []
        rule_uuids = set()
        
        # Extract from AC (activity class) elements - these contain business logic
        nodes_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}nodes')
        if nodes_elem is not None:
            for node in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
                ac_elem = node.find('{http://www.appian.com/ae/types/2009}ac')
                if ac_elem is not None:
                    # Look for rule references in output expressions and other AC elements
                    for child in ac_elem.iter():
                        if child.text and 'form' not in child.tag.lower() and 'ui' not in child.tag.lower():
                            import re
                            uuid_matches = re.findall(r'#\"(_a-[^\"]+)\"', child.text)
                            for uuid in uuid_matches:
                                rule_uuids.add(uuid)
        
        # Convert to list with resolved names and filter by object type
        for uuid in rule_uuids:
            # Check if this UUID is actually a rule in our lookup
            obj = self.object_lookup.get(uuid) if hasattr(self, 'object_lookup') else None
            if obj and obj.get('object_type') == 'Expression Rule':
                rules.append({
                    "uuid": uuid,
                    "name": "Unknown"  # Will be resolved later
                })
        
        return rules
    
    def _parse_nodes(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse process nodes"""
        nodes = []
        for node_elem in pm_elem.findall('.//nodes/node'):
            node_data = {
                "uuid": node_elem.get('uuid'),
                "name": self._get_element_text(node_elem, 'name'),
                "type": self._determine_node_type(node_elem),
                "details": self._parse_node_details(node_elem)
            }
            nodes.append(node_data)
        return nodes
    
    def _parse_flows(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse process flows"""
        flows = []
        for flow_elem in pm_elem.findall('.//flows/flow'):
            flow_data = {
                "from": self._get_element_text(flow_elem, 'from'),
                "to": self._get_element_text(flow_elem, 'to'),
                "condition": self._get_element_text(flow_elem, 'condition')
            }
            flows.append(flow_data)
        return flows
    
    def _determine_node_type(self, node_elem: ET.Element) -> str:
        """Determine node type"""
        if node_elem.find('.//form-config') is not None:
            return "User Input Task"
        elif node_elem.find('.//expr') is not None:
            return "Script Task"
        elif node_elem.find('.//subprocess') is not None:
            return "Call Process"
        return "Unknown"
    
    def _parse_node_details(self, node_elem: ET.Element) -> Dict[str, Any]:
        """Parse node details"""
        details = {}
        form_config = node_elem.find('.//form-config')
        if form_config is not None:
            ui_expr = form_config.find('.//uiExpressionForm')
            if ui_expr is not None:
                details["interface"] = {"uuid": ui_expr.text, "name": "Unknown"}
        
        expr_elem = node_elem.find('.//expr')
        if expr_elem is not None:
            details["expression"] = expr_elem.text
        
        return details
    
    def _parse_security(self, root: ET.Element) -> Dict[str, Any]:
        """Parse process model security"""
        security = {"roles": []}
        role_map = root.find('roleMap')
        if role_map is not None:
            for role_elem in role_map.findall('role'):
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
