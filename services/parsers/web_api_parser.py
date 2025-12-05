"""
Parser for Appian Web API objects.

This module provides the WebAPIParser class for extracting data from
Web API XML files.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class WebAPIParser(BaseParser):
    """
    Parser for Appian Web API objects.

    Extracts SAIL code, endpoint details, and HTTP methods from Web API XML files.
    """

    def _get_text(self, element: ET.Element, path: str, ns: Dict[str, str] = None) -> str:
        """
        Override to support namespaces.

        Args:
            element: Parent XML element
            path: XPath to the target element
            ns: Namespace dict

        Returns:
            Text content of the element, or None if element not found
        """
        if ns:
            elem = element.find(path, ns)
        else:
            elem = element.find(path)
        return elem.text if elem is not None and elem.text else None

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Web API XML file and extract all relevant data.

        Args:
            xml_path: Path to the Web API XML file

        Returns:
            Dict containing:
            - uuid: Web API UUID
            - name: Web API name
            - version_uuid: Version UUID
            - description: Web API description
            - sail_code: Cleaned SAIL code
            - endpoint_path: API endpoint path
            - http_methods: List of supported HTTP methods
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the webApi element
        ns = {'a': 'http://www.appian.com/ae/types/2009'}
        web_api_elem = root.find('.//webApi', ns)
        if web_api_elem is None:
            web_api_elem = root.find('.//a:webApi', ns)
        if web_api_elem is None:
            raise ValueError(f"No webApi element found in {xml_path}")

        # Extract basic info - UUID and name are attributes with namespace
        data = {
            'uuid': web_api_elem.get('{http://www.appian.com/ae/types/2009}uuid') or web_api_elem.get('uuid'),
            'name': web_api_elem.get('name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(web_api_elem, 'a:description', ns) or self._get_text(web_api_elem, 'description')
        }

        # Extract SAIL code from definition element
        definition_elem = web_api_elem.find('definition')
        if definition_elem is not None and definition_elem.text:
            data['sail_code'] = self._clean_sail_code(definition_elem.text)
        else:
            data['sail_code'] = None

        # Extract endpoint path
        data['endpoint_path'] = self._get_text(web_api_elem, 'endpointPath')

        # Extract HTTP methods
        data['http_methods'] = self._extract_http_methods(web_api_elem)

        return data

    def _extract_http_methods(self, web_api_elem: ET.Element) -> List[str]:
        """
        Extract supported HTTP methods from web API element.

        Args:
            web_api_elem: Web API XML element

        Returns:
            List of HTTP method strings (GET, POST, PUT, DELETE, etc.)
        """
        methods = []

        # Check for individual method elements
        for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            method_elem = web_api_elem.find(f'supports{method}')
            if method_elem is not None and method_elem.text == 'true':
                methods.append(method)

        # Alternative: check for httpMethods element
        if not methods:
            http_methods_elem = web_api_elem.find('httpMethods')
            if http_methods_elem is not None:
                for method_elem in http_methods_elem.findall('method'):
                    if method_elem.text:
                        methods.append(method_elem.text.upper())

        return methods
