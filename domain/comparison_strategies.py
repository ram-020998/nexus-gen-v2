"""
Comparison strategies for three-way merge functionality.

These strategies encapsulate the logic for comparing object versions
and content to determine if changes occurred.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json


class VersionComparisonStrategy(ABC):
    """
    Abstract base class for version comparison strategies.
    
    Version comparison determines if an object's version changed between
    two packages by comparing version UUIDs.
    """
    
    @abstractmethod
    def compare(
        self,
        version_a: Optional[str],
        version_b: Optional[str]
    ) -> bool:
        """
        Compare two version UUIDs.
        
        Args:
            version_a: Version UUID from first package
            version_b: Version UUID from second package
            
        Returns:
            True if versions are different, False if same
        """
        pass


class SimpleVersionComparisonStrategy(VersionComparisonStrategy):
    """
    Simple version comparison based on UUID equality.
    
    This is the default strategy that compares version UUIDs directly.
    """
    
    def compare(
        self,
        version_a: Optional[str],
        version_b: Optional[str]
    ) -> bool:
        """
        Compare version UUIDs for equality.
        
        Args:
            version_a: Version UUID from first package
            version_b: Version UUID from second package
            
        Returns:
            True if versions are different, False if same
            
        Note:
            - If both are None, returns False (no change)
            - If one is None and other isn't, returns True (changed)
            - Otherwise compares string equality
        """
        # Both None means no version info, treat as no change
        if version_a is None and version_b is None:
            return False
        
        # One None and one not None means changed
        if version_a is None or version_b is None:
            return True
        
        # Compare version UUIDs
        return version_a != version_b


class ContentComparisonStrategy(ABC):
    """
    Abstract base class for content comparison strategies.
    
    Content comparison determines if an object's content changed between
    two packages when the version UUID is the same.
    """
    
    @abstractmethod
    def compare(
        self,
        content_a: Dict[str, Any],
        content_b: Dict[str, Any]
    ) -> bool:
        """
        Compare two content dictionaries.
        
        Args:
            content_a: Content from first package
            content_b: Content from second package
            
        Returns:
            True if content is different, False if same
        """
        pass


class SAILCodeComparisonStrategy(ContentComparisonStrategy):
    """
    Content comparison strategy focused on SAIL code.
    
    This strategy compares SAIL code and other critical fields to determine
    if meaningful content changes occurred.
    """
    
    def __init__(self, critical_fields: Optional[list] = None):
        """
        Initialize the strategy.

        Args:
            critical_fields: List of field names to compare
                           (default: ['sail_code'])
        """
        self.critical_fields = critical_fields or ['sail_code']
    
    def compare(
        self,
        content_a: Dict[str, Any],
        content_b: Dict[str, Any]
    ) -> bool:
        """
        Compare content by checking critical fields.
        
        Args:
            content_a: Content from first package
            content_b: Content from second package
            
        Returns:
            True if any critical field differs, False if all same
        """
        for field in self.critical_fields:
            value_a = content_a.get(field)
            value_b = content_b.get(field)
            
            # Normalize None and empty string
            value_a = value_a if value_a else None
            value_b = value_b if value_b else None
            
            if value_a != value_b:
                return True
        
        return False


class StructuralComparisonStrategy(ContentComparisonStrategy):
    """
    Content comparison strategy for structured data.
    
    This strategy compares complex nested structures like process models,
    record types, etc. by serializing to JSON and comparing.
    """
    
    def __init__(self, ignore_fields: Optional[list] = None):
        """
        Initialize the strategy.

        Args:
            ignore_fields: List of field names to ignore in comparison
                          (e.g., timestamps, IDs)
        """
        self.ignore_fields = ignore_fields or [
            'created_at', 'updated_at', 'id'
        ]
    
    def compare(
        self,
        content_a: Dict[str, Any],
        content_b: Dict[str, Any]
    ) -> bool:
        """
        Compare content by serializing to JSON and comparing.
        
        Args:
            content_a: Content from first package
            content_b: Content from second package
            
        Returns:
            True if content differs, False if same
        """
        # Remove ignored fields
        filtered_a = self._filter_fields(content_a)
        filtered_b = self._filter_fields(content_b)
        
        # Serialize to JSON for comparison
        json_a = json.dumps(filtered_a, sort_keys=True)
        json_b = json.dumps(filtered_b, sort_keys=True)
        
        return json_a != json_b
    
    def _filter_fields(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove ignored fields from content dictionary.
        
        Args:
            content: Original content dictionary
            
        Returns:
            Filtered dictionary without ignored fields
        """
        return {
            key: value
            for key, value in content.items()
            if key not in self.ignore_fields
        }


class CompositeComparisonStrategy(ContentComparisonStrategy):
    """
    Composite strategy that combines multiple comparison strategies.
    
    This allows checking multiple aspects of content (e.g., SAIL code
    and structural data) in a single comparison.
    """
    
    def __init__(self, strategies: list[ContentComparisonStrategy]):
        """
        Initialize with a list of strategies.

        Args:
            strategies: List of comparison strategies to apply
        """
        if not strategies:
            raise ValueError("At least one strategy is required")
        self.strategies = strategies
    
    def compare(
        self,
        content_a: Dict[str, Any],
        content_b: Dict[str, Any]
    ) -> bool:
        """
        Compare content using all strategies.

        Returns True if ANY strategy detects a difference.

        Args:
            content_a: Content from first package
            content_b: Content from second package

        Returns:
            True if any strategy detects a difference, False if all same
        """
        for strategy in self.strategies:
            if strategy.compare(content_a, content_b):
                return True

        return False
