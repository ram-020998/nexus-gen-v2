"""
Parser for unrecognized Appian object types.

This module provides the UnknownObjectParser class for handling objects
that don't have a dedicated parser.
"""

from typing import Dict, Any
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class UnknownObjectParser(BaseParser):
    """
    Parser for unrecognized object types.

    This parser extracts only basic information and stores the raw XML
    for objects that don't have a dedicated parser.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse unknown object type.

        Args:
            xml_path: Path to the XML file

        Returns:
            Dict with basic object information and raw XML
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Try to extract basic info from root or first child
        data = {}

        # Try to find any element with uuid and name attributes
        for elem in root.iter():
            if elem.get('uuid') and elem.get('name'):
                data = self._extract_basic_info(elem)
                break

        # If no basic info found, create minimal data
        if not data:
            data = {
                'uuid': None,
                'name': None,
                'version_uuid': None,
                'description': None
            }

        # Store raw XML for unknown objects
        with open(xml_path, 'r', encoding='utf-8') as f:
            data['raw_xml'] = f.read()

        return data
