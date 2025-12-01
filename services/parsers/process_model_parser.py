"""
Parser for Appian Process Model objects.

This module provides the ProcessModelParser class for extracting data from
Process Model XML files.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from services.parsers.base_parser import BaseParser


class ProcessModelParser(BaseParser):
    """
    Parser for Appian Process Model objects.

    Extracts nodes, flows, variables, and calculates complexity from Process Model XML files.
    """

    def parse(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse Process Model XML file and extract all relevant data.

        Args:
            xml_path: Path to the Process Model XML file

        Returns:
            Dict containing:
            - uuid: Process Model UUID
            - name: Process Model name
            - version_uuid: Version UUID
            - description: Process Model description
            - nodes: List of node definitions
            - flows: List of flow/connection definitions
            - variables: List of process variable definitions
            - total_nodes: Count of nodes
            - total_flows: Count of flows
            - complexity_score: Calculated complexity metric
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the process model element
        pm_elem = root.find('.//{http://www.appian.com/ae/types/2009}pm')
        if pm_elem is None:
            raise ValueError(f"No process model element found in {xml_path}")

        # Extract basic info from meta element
        meta_elem = pm_elem.find('.//{http://www.appian.com/ae/types/2009}meta')
        if meta_elem is None:
            raise ValueError(f"No meta element found in {xml_path}")

        data = self._extract_basic_info_from_meta(meta_elem)

        # Extract version UUID from root level
        version_uuid_elem = root.find('.//versionUuid')
        if version_uuid_elem is not None and version_uuid_elem.text:
            data['version_uuid'] = version_uuid_elem.text

        # Extract nodes
        data['nodes'] = self._extract_nodes(pm_elem)

        # Extract flows/connections
        data['flows'] = self._extract_flows(pm_elem)

        # Extract process variables
        data['variables'] = self._extract_variables(pm_elem)

        # Calculate statistics
        data['total_nodes'] = len(data['nodes'])
        data['total_flows'] = len(data['flows'])
        data['complexity_score'] = self._calculate_complexity(data)

        return data

    def _extract_basic_info_from_meta(self, meta_elem: ET.Element) -> Dict[str, Any]:
        """
        Extract basic information from process model meta element.

        Args:
            meta_elem: Meta XML element

        Returns:
            Dict with uuid, name, version_uuid, description
        """
        ns = {'a': 'http://www.appian.com/ae/types/2009'}

        uuid_elem = meta_elem.find('a:uuid', ns)
        uuid = uuid_elem.text if uuid_elem is not None and uuid_elem.text else None

        # Extract name from string-map
        name = None
        name_elem = meta_elem.find('a:name', ns)
        if name_elem is not None:
            string_map = name_elem.find('a:string-map', ns)
            if string_map is not None:
                pair = string_map.find('a:pair', ns)
                if pair is not None:
                    value_elem = pair.find('a:value', ns)
                    if value_elem is not None and value_elem.text:
                        name = value_elem.text

        # Extract description from string-map
        description = None
        desc_elem = meta_elem.find('a:desc', ns)
        if desc_elem is not None:
            string_map = desc_elem.find('a:string-map', ns)
            if string_map is not None:
                pair = string_map.find('a:pair', ns)
                if pair is not None:
                    value_elem = pair.find('a:value', ns)
                    if value_elem is not None and value_elem.text:
                        description = value_elem.text

        # Version UUID is at the root level - we need to pass it from parse()
        # For now, set to None and extract it in parse()
        version_uuid = None

        return {
            'uuid': uuid,
            'name': name,
            'version_uuid': version_uuid,
            'description': description
        }

    def _extract_nodes(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract node definitions from process model.

        Args:
            pm_elem: Process model XML element

        Returns:
            List of node dictionaries
        """
        ns = {'a': 'http://www.appian.com/ae/types/2009'}
        nodes = []

        nodes_elem = pm_elem.find('a:nodes', ns)
        if nodes_elem is None:
            return nodes

        for node_elem in nodes_elem.findall('a:node', ns):
            node_uuid = node_elem.get('uuid')
            gui_id_elem = node_elem.find('a:guiId', ns)
            gui_id = gui_id_elem.text if gui_id_elem is not None else None

            # Extract node name from fname string-map
            node_name = None
            fname_elem = node_elem.find('a:fname', ns)
            if fname_elem is not None:
                string_map = fname_elem.find('a:string-map', ns)
                if string_map is not None:
                    pair = string_map.find('a:pair', ns)
                    if pair is not None:
                        value_elem = pair.find('a:value', ns)
                        if value_elem is not None and value_elem.text:
                            node_name = value_elem.text

            # Determine node type from activity class
            node_type = 'Unknown'
            ac_elem = node_elem.find('a:ac', ns)
            if ac_elem is not None:
                local_id_elem = ac_elem.find('a:local-id', ns)
                if local_id_elem is not None and local_id_elem.text:
                    node_type = local_id_elem.text

            node = {
                'node_id': node_uuid or gui_id,
                'node_type': node_type,
                'node_name': node_name,
                'gui_id': gui_id,
                'properties': {}
            }

            nodes.append(node)

        return nodes

    def _extract_flows(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract flow/connection definitions from process model.

        Args:
            pm_elem: Process model XML element

        Returns:
            List of flow dictionaries
        """
        ns = {'a': 'http://www.appian.com/ae/types/2009'}
        flows = []

        nodes_elem = pm_elem.find('a:nodes', ns)
        if nodes_elem is None:
            return flows

        # Flows are defined as connections within nodes
        for node_elem in nodes_elem.findall('a:node', ns):
            from_node_uuid = node_elem.get('uuid')
            from_gui_id_elem = node_elem.find('a:guiId', ns)
            from_gui_id = from_gui_id_elem.text if from_gui_id_elem is not None else None
            from_node_id = from_node_uuid or from_gui_id

            connections_elem = node_elem.find('a:connections', ns)
            if connections_elem is None:
                continue

            for conn_elem in connections_elem.findall('a:connection', ns):
                to_elem = conn_elem.find('a:to', ns)
                to_node_id = to_elem.text if to_elem is not None else None

                flow_label_elem = conn_elem.find('a:flowLabel', ns)
                flow_label = flow_label_elem.text if flow_label_elem is not None else None

                flow = {
                    'from_node_id': from_node_id,
                    'to_node_id': to_node_id,
                    'flow_label': flow_label,
                    'flow_condition': None  # Not typically in XML
                }

                flows.append(flow)

        return flows

    def _extract_variables(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract process variable definitions from process model.

        Args:
            pm_elem: Process model XML element

        Returns:
            List of variable dictionaries
        """
        ns = {'a': 'http://www.appian.com/ae/types/2009'}
        variables = []

        pvs_elem = pm_elem.find('a:pvs', ns)
        if pvs_elem is None:
            return variables

        for pv_elem in pvs_elem.findall('a:pv', ns):
            var_name = pv_elem.get('name')
            if not var_name:
                continue

            # Check if it's a parameter
            parameter_elem = pv_elem.find('a:parameter', ns)
            is_parameter = parameter_elem is not None and parameter_elem.text == 'true'

            # Extract type information
            var_type = None
            value_elem = pv_elem.find('a:value', ns)
            if value_elem is not None:
                xsi_type = value_elem.get('{http://www.w3.org/2001/XMLSchema-instance}type')
                if xsi_type:
                    var_type = xsi_type

            variable = {
                'variable_name': var_name,
                'variable_type': var_type,
                'is_parameter': is_parameter,
                'default_value': None
            }

            variables.append(variable)

        return variables

    def _calculate_complexity(self, data: Dict[str, Any]) -> float:
        """
        Calculate process model complexity score.

        Uses McCabe cyclomatic complexity: nodes + flows - 2

        Args:
            data: Process model data dict

        Returns:
            Complexity score
        """
        total_nodes = data.get('total_nodes', 0)
        total_flows = data.get('total_flows', 0)

        # McCabe complexity: nodes + flows - 2
        # Ensure minimum of 0
        complexity = max(0, total_nodes + total_flows - 2)

        return float(complexity)
