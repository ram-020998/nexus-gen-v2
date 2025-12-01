"""
Parser for Appian Custom Data Type (CDT) objects.

This module provides the CDTParser class for extracting data from
CDT XSD files.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class CDTParser(BaseParser):
    """
    Parser for Appian Custom Data Type (CDT) objects.

    Extracts namespace and field definitions from CDT XSD files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse CDT XSD file and extract all relevant data.

        Args:
            xml_path: Path to the CDT XSD file

        Returns:
            Dict containing:
            - uuid: CDT UUID (extracted from metadata)
            - name: CDT name (from complexType name)
            - version_uuid: Version UUID
            - description: CDT description
            - namespace: Target namespace
            - fields: List of field definitions
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        ns = {
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'ns2': 'http://www.appian.com/ae/types/2009'
        }

        # Extract namespace
        namespace = root.get('targetNamespace')

        # Find the complexType element (CDT definition)
        complex_type = root.find('.//xsd:complexType', ns)
        if complex_type is None:
            raise ValueError(f"No complexType element found in {xml_path}")

        # Extract name from complexType
        name = complex_type.get('name')

        # Extract metadata (UUID, version, description)
        metadata = complex_type.find('.//ns2:Metadata', ns)
        version_uuid = None
        description = None

        if metadata is not None:
            version_uuid_elem = metadata.find('ns2:versionUuid', ns)
            if version_uuid_elem is not None and version_uuid_elem.text:
                version_uuid = version_uuid_elem.text

        # Extract description from annotation
        annotation = complex_type.find('xsd:annotation', ns)
        if annotation is not None:
            doc_elem = annotation.find('xsd:documentation', ns)
            if doc_elem is not None and doc_elem.text:
                description = doc_elem.text.strip()

        # In Appian, CDTs use namespace + name as their unique identifier
        # The UUID is the fully qualified type name: {namespace}name
        uuid = f"{{{namespace}}}{name}" if namespace else name

        data = {
            'uuid': uuid,
            'name': name,
            'version_uuid': version_uuid,
            'description': description,
            'namespace': namespace
        }

        # Extract fields
        data['fields'] = self._extract_fields(complex_type, ns)

        return data

    def _extract_fields(self, complex_type: ET.Element, ns: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract field definitions from CDT complexType.

        Args:
            complex_type: ComplexType XML element
            ns: Namespace dict

        Returns:
            List of field dictionaries
        """
        fields = []

        sequence = complex_type.find('xsd:sequence', ns)
        if sequence is None:
            return fields

        for element in sequence.findall('xsd:element', ns):
            field_name = element.get('name')
            field_type = element.get('type')
            nillable = element.get('nillable') == 'true'

            # Determine if it's a list type
            is_list = False
            max_occurs = element.get('maxOccurs')
            if max_occurs and max_occurs == 'unbounded':
                is_list = True

            # Extract column name from JPA annotation
            column_name = None
            annotation = element.find('xsd:annotation', ns)
            if annotation is not None:
                appinfo = annotation.find('xsd:appinfo', ns)
                if appinfo is not None and appinfo.text:
                    # Parse JPA annotation to extract column name
                    jpa_text = appinfo.text
                    if '@Column' in jpa_text:
                        # Extract name from @Column(name="...")
                        import re
                        match = re.search(r'name="([^"]+)"', jpa_text)
                        if match:
                            column_name = match.group(1)

            field = {
                'field_name': field_name,
                'field_type': field_type,
                'is_list': is_list,
                'is_required': not nillable,  # If not nillable, then required
                'column_name': column_name,
                'display_order': len(fields)
            }

            fields.append(field)

        return fields
