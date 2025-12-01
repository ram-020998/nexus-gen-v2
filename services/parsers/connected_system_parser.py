"""
Parser for Appian Connected System objects.

This module provides the ConnectedSystemParser class for extracting data from
Connected System XML files.
"""

from typing import Dict, Any
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class ConnectedSystemParser(BaseParser):
    """
    Parser for Appian Connected System objects.

    Extracts system type and configuration properties from Connected System XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Connected System XML file and extract all relevant data.

        Args:
            xml_path: Path to the Connected System XML file

        Returns:
            Dict containing:
            - uuid: Connected System UUID
            - name: Connected System name
            - version_uuid: Version UUID
            - description: Connected System description
            - system_type: Type of connected system
            - properties: Configuration properties as JSON string
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the connectedSystem element
        connected_system_elem = root.find('.//connectedSystem')
        if connected_system_elem is None:
            raise ValueError(f"No connectedSystem element found in {xml_path}")

        # Extract basic info - UUID and name are child elements
        data = {
            'uuid': self._get_text(connected_system_elem, 'uuid'),
            'name': self._get_text(connected_system_elem, 'name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(connected_system_elem, 'description')
        }

        # Extract system type
        data['system_type'] = self._get_text(connected_system_elem, 'systemType')

        # Extract properties
        data['properties'] = self._extract_properties(connected_system_elem)

        return data

    def _extract_properties(self, connected_system_elem: ET.Element) -> str:
        """
        Extract configuration properties from connected system element.

        Args:
            connected_system_elem: Connected System XML element

        Returns:
            JSON string of properties
        """
        import json

        properties = {}

        properties_elem = connected_system_elem.find('properties')
        if properties_elem is None:
            return json.dumps(properties)

        for prop_elem in properties_elem.findall('property'):
            prop_name = prop_elem.get('name')
            prop_value = prop_elem.text

            if prop_name:
                properties[prop_name] = prop_value

        return json.dumps(properties)
