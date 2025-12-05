"""
Parser for Appian Interface objects.

This module provides the InterfaceParser class for extracting data from
Interface XML files.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class InterfaceParser(BaseParser):
    """
    Parser for Appian Interface objects.

    Extracts SAIL code, parameters, and security settings from Interface XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Interface XML file and extract all relevant data.

        Args:
            xml_path: Path to the Interface XML file

        Returns:
            Dict containing:
            - uuid: Interface UUID
            - name: Interface name
            - version_uuid: Version UUID
            - description: Interface description
            - sail_code: Cleaned SAIL code
            - parameters: List of parameter definitions
            - security: List of security role assignments
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the interface element
        interface_elem = root.find('.//interface')
        if interface_elem is None:
            raise ValueError(f"No interface element found in {xml_path}")

        # Extract basic info - UUID and name are child elements, not attributes
        data = {
            'uuid': self._get_text(interface_elem, 'uuid'),
            'name': self._get_text(interface_elem, 'name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(interface_elem, 'description')
        }

        # Extract SAIL code from definition element
        definition_elem = interface_elem.find('definition')
        if definition_elem is not None and definition_elem.text:
            data['sail_code'] = self._clean_sail_code(definition_elem.text)
        else:
            data['sail_code'] = None

        # Extract parameters
        data['parameters'] = self._extract_parameters(interface_elem)

        # Extract security settings
        data['security'] = self._extract_security(root)

        return data

    def _extract_parameters(self, interface_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract parameter definitions from interface element.

        Args:
            interface_elem: Interface XML element

        Returns:
            List of parameter dictionaries with name, type, required, default_value
        """
        parameters = []

        for param_elem in interface_elem.findall('.//namedTypedValue'):
            name_elem = param_elem.find('name')
            type_elem = param_elem.find('type')

            if name_elem is not None and name_elem.text:
                param = {
                    'name': name_elem.text,
                    'type': None,
                    'required': False,  # Default, Appian doesn't explicitly mark this
                    'default_value': None,
                    'display_order': len(parameters)
                }

                # Extract type information
                if type_elem is not None:
                    type_name_elem = type_elem.find('name')
                    type_namespace_elem = type_elem.find('namespace')

                    if type_name_elem is not None and type_name_elem.text:
                        param['type'] = type_name_elem.text

                        # Add namespace if present
                        if type_namespace_elem is not None and type_namespace_elem.text:
                            param['type'] = f"{type_namespace_elem.text}:{param['type']}"

                parameters.append(param)

        return parameters

    def _extract_security(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract security role assignments from roleMap element.

        Args:
            root: Root XML element

        Returns:
            List of security role dictionaries with role_name and permission_type
        """
        security = []

        role_map = root.find('.//roleMap')
        if role_map is None:
            return security

        for role_elem in role_map.findall('role'):
            role_name = role_elem.get('name')
            if not role_name:
                continue

            # Check if role has any users or groups
            users = role_elem.findall('.//users/*')
            groups = role_elem.findall('.//groups/*')

            # Determine permission type based on role name
            permission_type = self._map_role_to_permission(role_name)

            # Only add if there are users or groups, or if it's a public role
            if users or groups or role_map.get('public') == 'true':
                security.append({
                    'role_name': role_name,
                    'permission_type': permission_type,
                    'inherit': role_elem.get('inherit') == 'true',
                    'allow_for_all': role_elem.get('allowForAll') == 'true'
                })

        return security

    def _map_role_to_permission(self, role_name: str) -> str:
        """
        Map Appian role name to permission type.

        Args:
            role_name: Appian role name

        Returns:
            Permission type string
        """
        role_mapping = {
            'readers': 'VIEW',
            'authors': 'EDIT',
            'administrators': 'ADMIN',
            'denyReaders': 'DENY_VIEW',
            'denyAuthors': 'DENY_EDIT',
            'denyAdministrators': 'DENY_ADMIN'
        }
        return role_mapping.get(role_name, role_name.upper())
