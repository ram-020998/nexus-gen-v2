"""
Complexity Calculator Service

This service calculates complexity and estimated time for merge changes
based on object type and change magnitude. It uses configurable thresholds
from ReportConfig to classify changes as Low, Medium, or High complexity.

The service supports:
- Line-based complexity for Interface, Expression Rule, and Record Type
- Node-based complexity for Process Models
- Constant complexity (always Low) for Constants
- Time estimation based on complexity level
- Time formatting for display
"""
import json
import logging
from typing import Dict, Any, Optional

from config.report_config import ReportConfig


logger = logging.getLogger(__name__)


class ComplexityCalculatorService:
    """
    Service for calculating complexity and time estimates for changes.

    This service analyzes changes and calculates:
    1. Complexity level (Low, Medium, High) based on object type
    2. Estimated time in minutes based on complexity
    3. Formatted time display (minutes or hours)

    The service uses configurable thresholds from ReportConfig and
    supports different calculation methods for different object types.
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """
        Initialize the complexity calculator service.

        Args:
            config: Optional custom ReportConfig instance.
                   If None, uses the default ReportConfig class.
        """
        self.config = config or ReportConfig
        logger.info("ComplexityCalculatorService initialized")

    def calculate_complexity(
        self,
        change: Dict[str, Any],
        base_object: Optional[Any] = None,
        customer_object: Optional[Any] = None,
        vendor_object: Optional[Any] = None
    ) -> str:
        """
        Calculate complexity for a change.

        Routes to appropriate calculation method based on object type:
        - Line-based: Interface, Expression Rule, Record Type
        - Always Low: Constant
        - Node-based: Process Model

        Args:
            change: Change dictionary with object_type and other metadata
            base_object: Base version object (A) - can be dict or model
            customer_object: Customer version object (B) - can be dict or model
            vendor_object: Vendor version object (C) - can be dict or model

        Returns:
            str: Complexity level ("Low", "Medium", or "High")

        Example:
            >>> calculator = ComplexityCalculatorService()
            >>> complexity = calculator.calculate_complexity(
            ...     change={'object_type': 'Interface'},
            ...     base_object=base_obj,
            ...     vendor_object=vendor_obj
            ... )
            >>> print(complexity)  # "Medium"
        """
        object_type = change.get('object_type', '')

        # Check if object type is always Low complexity
        if self.config.is_always_low_type(object_type):
            logger.debug(
                f"Object type '{object_type}' is always Low complexity"
            )
            return self.config.COMPLEXITY_LOW

        # Check if object type uses line-based complexity
        if self.config.is_line_based_type(object_type):
            return self._calculate_line_based_complexity(
                base_object,
                customer_object,
                vendor_object
            )

        # Check if object type is Process Model
        if self.config.is_process_model_type(object_type):
            return self._calculate_process_model_complexity(
                base_object,
                customer_object,
                vendor_object
            )

        # Default to Low for unknown types
        logger.warning(
            f"Unknown object type '{object_type}', "
            f"defaulting to Low complexity"
        )
        return self.config.COMPLEXITY_LOW

    def calculate_estimated_time(self, complexity: str) -> int:
        """
        Calculate estimated time in minutes based on complexity.

        Args:
            complexity: Complexity level ("Low", "Medium", or "High")

        Returns:
            int: Estimated time in minutes

        Example:
            >>> calculator = ComplexityCalculatorService()
            >>> time = calculator.calculate_estimated_time("Medium")
            >>> print(time)  # 40
        """
        try:
            return self.config.get_time_estimate(complexity)
        except ValueError as e:
            logger.warning(
                f"Invalid complexity level '{complexity}': {e}. "
                f"Defaulting to Low complexity time."
            )
            return self.config.TIME_LOW_COMPLEXITY

    def format_time_display(self, minutes: int) -> str:
        """
        Format time for display.

        Formats as minutes if less than 60, otherwise as hours.

        Args:
            minutes: Time in minutes

        Returns:
            str: Formatted time string ("X minutes" or "Y hours")

        Example:
            >>> calculator = ComplexityCalculatorService()
            >>> print(calculator.format_time_display(45))  # "45 minutes"
            >>> print(calculator.format_time_display(120))  # "2 hours"
        """
        if minutes < self.config.TIME_DISPLAY_HOUR_THRESHOLD:
            return f"{minutes} minutes"
        else:
            hours = minutes / 60
            # Format with 1 decimal place if not a whole number
            if hours == int(hours):
                return f"{int(hours)} hours"
            else:
                return f"{hours:.1f} hours"

    def _calculate_line_based_complexity(
        self,
        base_object: Optional[Any],
        customer_object: Optional[Any],
        vendor_object: Optional[Any]
    ) -> str:
        """
        Calculate complexity based on SAIL code line differences.

        Compares SAIL code between base and the most recent version
        (vendor if available, otherwise customer).

        Args:
            base_object: Base version object (A)
            customer_object: Customer version object (B)
            vendor_object: Vendor version object (C)

        Returns:
            str: Complexity level based on line count thresholds
        """
        # Extract SAIL code from objects
        base_sail = self._extract_sail_code(base_object)

        # Use vendor version if available, otherwise customer
        new_sail = (
            self._extract_sail_code(vendor_object)
            if vendor_object
            else self._extract_sail_code(customer_object)
        )

        # Count line differences
        line_diff = self._count_line_differences(base_sail, new_sail)

        logger.debug(
            f"Line-based complexity: {line_diff} lines changed"
        )

        # Apply thresholds
        if line_diff <= self.config.LINE_BASED_LOW_MAX:
            return self.config.COMPLEXITY_LOW
        elif line_diff <= self.config.LINE_BASED_MEDIUM_MAX:
            return self.config.COMPLEXITY_MEDIUM
        else:
            return self.config.COMPLEXITY_HIGH

    def _calculate_process_model_complexity(
        self,
        base_object: Optional[Any],
        customer_object: Optional[Any],
        vendor_object: Optional[Any]
    ) -> str:
        """
        Calculate complexity based on process model node modifications.

        Compares nodes between base and the most recent version
        (vendor if available, otherwise customer).

        Args:
            base_object: Base version object (A)
            customer_object: Customer version object (B)
            vendor_object: Vendor version object (C)

        Returns:
            str: Complexity level based on node modification thresholds
        """
        # Extract process model data
        base_pm_data = self._extract_process_model_data(base_object)

        # Use vendor version if available, otherwise customer
        new_pm_data = (
            self._extract_process_model_data(vendor_object)
            if vendor_object
            else self._extract_process_model_data(customer_object)
        )

        # Count modified nodes
        modified_nodes = self._count_modified_nodes(
            base_pm_data,
            new_pm_data
        )

        logger.debug(
            f"Process model complexity: {modified_nodes} nodes modified"
        )

        # Apply thresholds
        if modified_nodes <= self.config.PROCESS_MODEL_LOW_MAX:
            return self.config.COMPLEXITY_LOW
        elif modified_nodes <= self.config.PROCESS_MODEL_MEDIUM_MAX:
            return self.config.COMPLEXITY_MEDIUM
        else:
            return self.config.COMPLEXITY_HIGH

    def _extract_sail_code(self, obj: Optional[Any]) -> Optional[str]:
        """
        Extract SAIL code from an object.

        Handles both dictionary and SQLAlchemy model objects.

        Args:
            obj: Object containing SAIL code (dict or model)

        Returns:
            str or None: SAIL code if present, None otherwise
        """
        if obj is None:
            return None

        # Handle dictionary objects
        if isinstance(obj, dict):
            return obj.get('sail_code')

        # Handle SQLAlchemy model objects
        if hasattr(obj, 'sail_code'):
            return obj.sail_code

        return None

    def _extract_process_model_data(
        self,
        obj: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract process model data from an object.

        Handles both dictionary and SQLAlchemy model objects.

        Args:
            obj: Object containing process model data (dict or model)

        Returns:
            dict or None: Process model data if present, None otherwise
        """
        if obj is None:
            return None

        # Handle dictionary objects
        if isinstance(obj, dict):
            # Check for process_model_metadata key
            if 'process_model_metadata' in obj:
                return obj['process_model_metadata']
            # Check for nodes directly in object
            if 'nodes' in obj:
                return obj
            return None

        # Handle SQLAlchemy model objects
        if hasattr(obj, 'process_model_metadata'):
            pm_metadata = obj.process_model_metadata
            if pm_metadata:
                # Convert to dictionary with nodes
                return {
                    'nodes': [
                        {
                            'node_id': node.node_id,
                            'node_type': node.node_type,
                            'node_name': node.node_name,
                            'properties': node.properties
                        }
                        for node in pm_metadata.nodes
                    ] if hasattr(pm_metadata, 'nodes') else []
                }

        return None

    def _count_line_differences(
        self,
        base_sail: Optional[str],
        new_sail: Optional[str]
    ) -> int:
        """
        Count the number of line differences between two SAIL code strings.

        Uses a simple line-by-line comparison. Counts added, removed,
        and modified lines.

        Args:
            base_sail: Base SAIL code
            new_sail: New SAIL code

        Returns:
            int: Number of lines that differ
        """
        # Handle None cases
        if base_sail is None and new_sail is None:
            return 0
        if base_sail is None:
            # All lines in new_sail are added
            return len(new_sail.splitlines()) if new_sail else 0
        if new_sail is None:
            # All lines in base_sail are removed
            return len(base_sail.splitlines()) if base_sail else 0

        # Split into lines
        base_lines = base_sail.splitlines()
        new_lines = new_sail.splitlines()

        # Simple diff: count lines that are different
        # This is a simplified approach - a more sophisticated diff
        # algorithm could be used for better accuracy
        max_lines = max(len(base_lines), len(new_lines))
        diff_count = 0

        for i in range(max_lines):
            base_line = base_lines[i] if i < len(base_lines) else None
            new_line = new_lines[i] if i < len(new_lines) else None

            if base_line != new_line:
                diff_count += 1

        return diff_count

    def _count_modified_nodes(
        self,
        base_pm_data: Optional[Dict[str, Any]],
        new_pm_data: Optional[Dict[str, Any]]
    ) -> int:
        """
        Count the number of modified nodes in a process model.

        Compares nodes by node_id and counts added, removed, and
        modified nodes.

        Args:
            base_pm_data: Base process model data with 'nodes' list
            new_pm_data: New process model data with 'nodes' list

        Returns:
            int: Number of nodes that were modified
        """
        # Handle None cases
        if base_pm_data is None and new_pm_data is None:
            return 0

        base_nodes = (
            base_pm_data.get('nodes', [])
            if base_pm_data
            else []
        )
        new_nodes = (
            new_pm_data.get('nodes', [])
            if new_pm_data
            else []
        )

        # Build node maps by node_id
        base_node_map = {
            node['node_id']: node
            for node in base_nodes
            if isinstance(node, dict) and 'node_id' in node
        }
        new_node_map = {
            node['node_id']: node
            for node in new_nodes
            if isinstance(node, dict) and 'node_id' in node
        }

        modified_count = 0

        # Count added nodes (in new but not in base)
        for node_id in new_node_map:
            if node_id not in base_node_map:
                modified_count += 1

        # Count removed nodes (in base but not in new)
        for node_id in base_node_map:
            if node_id not in new_node_map:
                modified_count += 1

        # Count modified nodes (in both but different)
        for node_id in base_node_map:
            if node_id in new_node_map:
                base_node = base_node_map[node_id]
                new_node = new_node_map[node_id]

                # Compare node properties
                if self._nodes_are_different(base_node, new_node):
                    modified_count += 1

        return modified_count

    def _nodes_are_different(
        self,
        base_node: Dict[str, Any],
        new_node: Dict[str, Any]
    ) -> bool:
        """
        Check if two nodes are different.

        Compares node_type, node_name, and properties.

        Args:
            base_node: Base node dictionary
            new_node: New node dictionary

        Returns:
            bool: True if nodes are different, False otherwise
        """
        # Compare node type
        if base_node.get('node_type') != new_node.get('node_type'):
            return True

        # Compare node name
        if base_node.get('node_name') != new_node.get('node_name'):
            return True

        # Compare properties (as JSON strings for consistency)
        base_props = base_node.get('properties')
        new_props = new_node.get('properties')

        # Normalize properties for comparison
        base_props_str = (
            json.dumps(base_props, sort_keys=True)
            if base_props
            else None
        )
        new_props_str = (
            json.dumps(new_props, sort_keys=True)
            if new_props
            else None
        )

        return base_props_str != new_props_str
