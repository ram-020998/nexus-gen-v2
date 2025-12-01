"""
Parser for Appian Record Type objects.

This module provides the RecordTypeParser class for extracting data from
Record Type XML files.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class RecordTypeParser(BaseParser):
    """
    Parser for Appian Record Type objects.

    Extracts fields, relationships, views, and actions from Record Type XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Record Type XML file and extract all relevant data.

        Args:
            xml_path: Path to the Record Type XML file

        Returns:
            Dict containing:
            - uuid: Record Type UUID
            - name: Record Type name
            - version_uuid: Version UUID
            - description: Record Type description
            - fields: List of field definitions
            - relationships: List of relationship definitions
            - views: List of view configurations
            - actions: List of record actions
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        ns = {'a': 'http://www.appian.com/ae/types/2009'}

        # Find the recordType element
        record_type_elem = root.find('.//recordType', ns)
        if record_type_elem is None:
            record_type_elem = root.find('.//a:recordType', ns)
        if record_type_elem is None:
            raise ValueError(f"No recordType element found in {xml_path}")

        # Extract basic info
        data = {
            'uuid': record_type_elem.get('{http://www.appian.com/ae/types/2009}uuid') or record_type_elem.get('uuid'),
            'name': record_type_elem.get('name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(record_type_elem, 'a:description', ns)
        }

        # Extract fields from sourceConfiguration
        data['fields'] = self._extract_fields(record_type_elem, ns)

        # Extract relationships
        data['relationships'] = self._extract_relationships(record_type_elem, ns)

        # Extract views
        data['views'] = self._extract_views(record_type_elem, ns)

        # Extract actions (record actions)
        data['actions'] = self._extract_actions(record_type_elem, ns)

        return data

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

    def _extract_fields(self, record_type_elem: ET.Element, ns: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract field definitions from record type.

        Args:
            record_type_elem: Record type XML element
            ns: Namespace dict

        Returns:
            List of field dictionaries
        """
        fields = []

        source_config = record_type_elem.find('a:sourceConfiguration', ns)
        if source_config is None:
            return fields

        for field_elem in source_config.findall('field'):
            field_uuid = self._get_text(field_elem, 'uuid')
            field_name = self._get_text(field_elem, 'fieldName')
            field_type = self._get_text(field_elem, 'type')
            source_field_name = self._get_text(field_elem, 'sourceFieldName')
            source_field_type = self._get_text(field_elem, 'sourceFieldType')

            is_record_id = self._get_text(field_elem, 'isRecordId') == 'true'
            is_unique = self._get_text(field_elem, 'isUnique') == 'true'
            is_custom = self._get_text(field_elem, 'isCustomField') == 'true'

            field = {
                'field_uuid': field_uuid,
                'field_name': field_name,
                'field_type': field_type,
                'source_field_name': source_field_name,
                'source_field_type': source_field_type,
                'is_record_id': is_record_id,
                'is_unique': is_unique,
                'is_custom_field': is_custom,
                'display_order': len(fields)
            }

            fields.append(field)

        return fields

    def _extract_relationships(self, record_type_elem: ET.Element, ns: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract relationship definitions from record type.

        Args:
            record_type_elem: Record type XML element
            ns: Namespace dict

        Returns:
            List of relationship dictionaries
        """
        relationships = []

        for rel_elem in record_type_elem.findall('a:recordRelationshipCfg', ns):
            rel_uuid = self._get_text(rel_elem, 'uuid')
            rel_name = self._get_text(rel_elem, 'relationshipName')
            target_record_type = self._get_text(rel_elem, 'targetRecordTypeUuid')
            rel_type = self._get_text(rel_elem, 'relationshipType')
            rel_data = self._get_text(rel_elem, 'relationshipData')

            relationship = {
                'relationship_uuid': rel_uuid,
                'relationship_name': rel_name,
                'target_record_type_uuid': target_record_type,
                'relationship_type': rel_type,
                'relationship_data': rel_data,
                'display_order': len(relationships)
            }

            relationships.append(relationship)

        return relationships

    def _extract_views(self, record_type_elem: ET.Element, ns: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract view configurations from record type.

        Args:
            record_type_elem: Record type XML element
            ns: Namespace dict

        Returns:
            List of view dictionaries
        """
        views = []

        # Extract detail view configuration
        detail_view = record_type_elem.find('a:detailViewCfg', ns)
        if detail_view is not None:
            view_name = self._get_text(detail_view, 'a:nameExpr', ns)
            url_stub = self._get_text(detail_view, 'a:urlStub', ns)
            visibility = self._get_text(detail_view, 'a:visibilityExpr', ns)

            views.append({
                'view_type': 'DETAIL',
                'view_name': view_name,
                'url_stub': url_stub,
                'visibility_expr': visibility,
                'display_order': len(views)
            })

        # Extract list view template
        list_view_expr = self._get_text(record_type_elem, 'a:listViewTemplateExpr', ns)
        if list_view_expr:
            views.append({
                'view_type': 'LIST',
                'view_name': 'List View',
                'url_stub': None,
                'visibility_expr': None,
                'display_order': len(views)
            })

        return views

    def _extract_actions(self, record_type_elem: ET.Element, ns: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract record action definitions from record type.

        Args:
            record_type_elem: Record type XML element
            ns: Namespace dict

        Returns:
            List of action dictionaries
        """
        actions = []

        # Record actions are typically defined in recordActionCfg elements
        for action_elem in record_type_elem.findall('a:recordActionCfg', ns):
            action_uuid = self._get_text(action_elem, 'a:uuid', ns)
            action_name = self._get_text(action_elem, 'a:name', ns)
            action_type = self._get_text(action_elem, 'a:actionType', ns)
            process_model = self._get_text(action_elem, 'a:processModelUuid', ns)

            action = {
                'action_uuid': action_uuid,
                'action_name': action_name,
                'action_type': action_type,
                'process_model_uuid': process_model,
                'display_order': len(actions)
            }

            actions.append(action)

        return actions
