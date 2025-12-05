"""
Parser for Appian Expression Rule objects.

This module provides the ExpressionRuleParser class for extracting data from
Expression Rule XML files.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class ExpressionRuleParser(BaseParser):
    """
    Parser for Appian Expression Rule objects.

    Extracts SAIL code, inputs, and output type from Expression Rule XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Expression Rule XML file and extract all relevant data.

        Args:
            xml_path: Path to the Expression Rule XML file

        Returns:
            Dict containing:
            - uuid: Expression Rule UUID
            - name: Expression Rule name
            - version_uuid: Version UUID
            - description: Expression Rule description
            - sail_code: Cleaned SAIL code (from definition element)
            - inputs: List of input parameter definitions
            - output_type: Output type definition
            - return_type: Alias for output_type (for compatibility)
            - definition: Raw definition text (for compatibility)

        Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 8.2, 8.3, 8.4
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the rule element
        rule_elem = root.find('.//rule')
        if rule_elem is None:
            raise ValueError(f"No rule element found in {xml_path}")

        # Extract basic info - UUID and name are child elements, not attributes
        data = {
            'uuid': self._get_text(rule_elem, 'uuid'),
            'name': self._get_text(rule_elem, 'name'),
            'version_uuid': self._get_text(root, './/versionUuid'),
            'description': self._get_text(rule_elem, 'description')
        }

        # Extract SAIL code from definition element
        definition_elem = rule_elem.find('definition')
        if definition_elem is not None and definition_elem.text:
            # Store both cleaned SAIL code and raw definition
            data['sail_code'] = self._clean_sail_code(definition_elem.text)
            data['definition'] = definition_elem.text  # Raw definition
        else:
            data['sail_code'] = None
            data['definition'] = None

        # Extract input parameters
        data['inputs'] = self._extract_inputs(rule_elem)

        # Extract output type (if specified)
        output_type = self._extract_output_type(rule_elem)
        data['output_type'] = output_type
        data['return_type'] = output_type  # Alias for compatibility

        return data

    def _extract_inputs(self, rule_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract input parameter definitions from rule element.

        Args:
            rule_elem: Rule XML element

        Returns:
            List of input parameter dictionaries with keys:
            - name: Parameter name
            - type: Data type (with namespace if present)
            - data_type: Alias for type (for compatibility)
            - required: Whether parameter is required (default False)
            - description: Parameter description (if present)
            - default_value: Default value (if present)
            - display_order: Order in parameter list

        Validates: Requirements 1.3
        """
        inputs = []

        for param_elem in rule_elem.findall('.//namedTypedValue'):
            name_elem = param_elem.find('name')
            type_elem = param_elem.find('type')

            if name_elem is not None and name_elem.text:
                input_param = {
                    'name': name_elem.text,
                    'type': None,
                    'data_type': None,  # Alias for compatibility
                    'required': False,  # Appian doesn't mark this in XML
                    'description': None,  # Not typically in XML
                    'default_value': None,  # Not typically in XML
                    'display_order': len(inputs)
                }

                # Extract type information
                if type_elem is not None:
                    type_name_elem = type_elem.find('name')
                    type_namespace_elem = type_elem.find('namespace')

                    if type_name_elem is not None and type_name_elem.text:
                        input_param['type'] = type_name_elem.text

                        # Add namespace if present
                        if (type_namespace_elem is not None and
                                type_namespace_elem.text):
                            ns = type_namespace_elem.text
                            input_param['type'] = f"{ns}:{input_param['type']}"

                        # Set data_type alias
                        input_param['data_type'] = input_param['type']

                # Check for description (rare but possible)
                desc_elem = param_elem.find('description')
                if desc_elem is not None and desc_elem.text:
                    input_param['description'] = desc_elem.text

                inputs.append(input_param)

        return inputs

    def _extract_output_type(self, rule_elem: ET.Element) -> str:
        """
        Extract output type from rule element.

        Args:
            rule_elem: Rule XML element

        Returns:
            Output type string, or None if not specified
        """
        # Look for output type in various possible locations
        # Some expression rules may have explicit output type definitions
        output_type_elem = rule_elem.find('.//outputType')
        if output_type_elem is not None:
            type_name = output_type_elem.find('name')
            type_namespace = output_type_elem.find('namespace')

            if type_name is not None and type_name.text:
                output_type = type_name.text
                if type_namespace is not None and type_namespace.text:
                    output_type = f"{type_namespace.text}:{output_type}"
                return output_type

        # Default to Variant if not specified
        return None
