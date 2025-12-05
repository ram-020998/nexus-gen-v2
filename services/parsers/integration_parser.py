"""
Parser for Appian Integration objects.

This module provides the IntegrationParser class for extracting data from
Integration XML files.
"""

from typing import Dict, Any
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class IntegrationParser(BaseParser):
    """
    Parser for Appian Integration objects.

    Extracts SAIL code, connection details, authentication, and endpoint information
    from Integration XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Integration XML file and extract all relevant data.

        Args:
            xml_path: Path to the Integration XML file

        Returns:
            Dict containing:
            - uuid: Integration UUID
            - name: Integration name
            - version_uuid: Version UUID
            - description: Integration description
            - sail_code: Cleaned SAIL code
            - connection_type: Type of connection (REST, SOAP, etc.)
            - endpoint_url: Integration endpoint URL
            - authentication_type: Authentication method
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the integration element (could be outboundIntegration or integration)
        integration_elem = root.find('.//outboundIntegration')
        if integration_elem is None:
            integration_elem = root.find('.//integration')
        if integration_elem is None:
            raise ValueError(f"No integration element found in {xml_path}")

        # Extract basic info - UUID and name are child elements
        data = {
            'uuid': self._get_text(integration_elem, 'uuid'),
            'name': self._get_text(integration_elem, 'name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(integration_elem, 'description')
        }

        # Extract SAIL code from definition element
        definition_elem = integration_elem.find('definition')
        if definition_elem is not None and definition_elem.text:
            data['sail_code'] = self._clean_sail_code(definition_elem.text)
        else:
            data['sail_code'] = None

        # Extract connection type
        data['connection_type'] = self._get_text(integration_elem, 'connectionType')

        # Extract endpoint URL
        data['endpoint_url'] = self._get_text(integration_elem, 'endpointUrl')

        # Extract authentication type
        data['authentication_type'] = self._get_text(integration_elem, 'authenticationType')

        # Extract HTTP method (for REST integrations)
        data['http_method'] = self._get_text(integration_elem, 'httpMethod')

        return data
