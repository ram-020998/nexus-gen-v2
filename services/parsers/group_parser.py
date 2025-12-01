"""
Parser for Appian Group objects.

This module provides the GroupParser class for extracting data from
Group XML files.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class GroupParser(BaseParser):
    """
    Parser for Appian Group objects.

    Extracts group members and parent group information from Group XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Group XML file and extract all relevant data.

        Args:
            xml_path: Path to the Group XML file

        Returns:
            Dict containing:
            - uuid: Group UUID
            - name: Group name
            - version_uuid: Version UUID
            - description: Group description
            - members: List of group member UUIDs
            - parent_group_uuid: Parent group UUID (if any)
            - group_type: Type of group
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the group element
        group_elem = root.find('.//group')
        if group_elem is None:
            raise ValueError(f"No group element found in {xml_path}")

        # Extract basic info - UUID and name are child elements
        data = {
            'uuid': self._get_text(group_elem, 'uuid'),
            'name': self._get_text(group_elem, 'name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(group_elem, 'description')
        }

        # Extract parent group
        data['parent_group_uuid'] = self._get_text(group_elem, 'parentGroupUuid')

        # Extract group type
        data['group_type'] = self._get_text(group_elem, 'groupType')

        # Extract members
        data['members'] = self._extract_members(group_elem)

        return data

    def _extract_members(self, group_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract group members from group element.

        Args:
            group_elem: Group XML element

        Returns:
            List of member dictionaries with user/group UUIDs
        """
        members = []

        members_elem = group_elem.find('members')
        if members_elem is None:
            return members

        # Extract user members
        for user_elem in members_elem.findall('.//user'):
            user_uuid = user_elem.get('uuid') or user_elem.text
            if user_uuid:
                members.append({
                    'member_type': 'USER',
                    'member_uuid': user_uuid,
                    'display_order': len(members)
                })

        # Extract group members (nested groups)
        for nested_group_elem in members_elem.findall('.//group'):
            group_uuid = nested_group_elem.get('uuid') or nested_group_elem.text
            if group_uuid:
                members.append({
                    'member_type': 'GROUP',
                    'member_uuid': group_uuid,
                    'display_order': len(members)
                })

        return members
