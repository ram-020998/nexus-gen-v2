"""
Parser for Appian Site objects.

This module provides the SiteParser class for extracting data from
Site XML files.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class SiteParser(BaseParser):
    """
    Parser for Appian Site objects.

    Extracts page hierarchy and site configuration from Site XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Site XML file and extract all relevant data.

        Args:
            xml_path: Path to the Site XML file

        Returns:
            Dict containing:
            - uuid: Site UUID
            - name: Site name
            - version_uuid: Version UUID
            - description: Site description
            - pages: List of page definitions in hierarchy
            - url_stub: Site URL stub
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the site element
        ns = {'a': 'http://www.appian.com/ae/types/2009'}
        site_elem = root.find('.//site', ns)
        if site_elem is None:
            raise ValueError(f"No site element found in {xml_path}")

        # Extract basic info - UUID and name are attributes with namespace
        data = {
            'uuid': site_elem.get('{http://www.appian.com/ae/types/2009}uuid') or site_elem.get('uuid'),
            'name': site_elem.get('name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(site_elem, 'description')
        }

        # Extract URL stub
        data['url_stub'] = self._get_text(site_elem, 'urlStub')

        # Extract pages
        data['pages'] = self._extract_pages(site_elem)

        return data

    def _extract_pages(self, site_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract page hierarchy from site element.

        Args:
            site_elem: Site XML element

        Returns:
            List of page dictionaries with hierarchy information
        """
        pages = []

        pages_elem = site_elem.find('pages')
        if pages_elem is None:
            return pages

        for page_elem in pages_elem.findall('.//page'):
            page_uuid = page_elem.get('uuid')
            page_name = self._get_text(page_elem, 'name')
            page_title = self._get_text(page_elem, 'title')
            page_url = self._get_text(page_elem, 'urlStub')
            parent_uuid = self._get_text(page_elem, 'parentUuid')

            page = {
                'page_uuid': page_uuid,
                'page_name': page_name,
                'page_title': page_title,
                'page_url': page_url,
                'parent_uuid': parent_uuid,
                'display_order': len(pages)
            }

            pages.append(page)

        return pages
