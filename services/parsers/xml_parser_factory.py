"""
Factory for creating appropriate XML parsers based on object type.

This module provides the XMLParserFactory that creates the correct parser
for each Appian object type.
"""

from typing import Dict
from services.parsers.base_parser import BaseParser
from services.parsers.unknown_object_parser import UnknownObjectParser
from services.parsers.interface_parser import InterfaceParser
from services.parsers.expression_rule_parser import ExpressionRuleParser
from services.parsers.process_model_parser import ProcessModelParser
from services.parsers.record_type_parser import RecordTypeParser
from services.parsers.cdt_parser import CDTParser
from services.parsers.integration_parser import IntegrationParser
from services.parsers.web_api_parser import WebAPIParser
from services.parsers.site_parser import SiteParser
from services.parsers.group_parser import GroupParser
from services.parsers.constant_parser import ConstantParser
from services.parsers.connected_system_parser import ConnectedSystemParser


class XMLParserFactory:
    """
    Factory for creating XML parsers based on object type.

    This factory maintains a registry of parsers for each Appian object type
    and returns the appropriate parser when requested.
    """

    def __init__(self):
        """
        Initialize the parser factory.

        Registers all available parsers for Appian object types.
        """
        self._parsers: Dict[str, BaseParser] = {}
        self._unknown_parser = UnknownObjectParser()

        # Register all parsers
        self._register_default_parsers()

    def _register_default_parsers(self) -> None:
        """
        Register all default parsers for Appian object types.
        """
        self.register_parser('Interface', InterfaceParser())
        self.register_parser('Expression Rule', ExpressionRuleParser())
        self.register_parser('Process Model', ProcessModelParser())
        self.register_parser('Record Type', RecordTypeParser())
        self.register_parser('CDT', CDTParser())
        self.register_parser('Data Type', CDTParser())  # Alias for CDT
        self.register_parser('Integration', IntegrationParser())
        self.register_parser('Web API', WebAPIParser())
        self.register_parser('Site', SiteParser())
        self.register_parser('Group', GroupParser())
        self.register_parser('Constant', ConstantParser())
        self.register_parser('Connected System', ConnectedSystemParser())

    def register_parser(self, object_type: str, parser: BaseParser) -> None:
        """
        Register a parser for a specific object type.
        
        Args:
            object_type: The Appian object type
                (e.g., 'Interface', 'Process Model')
            parser: The parser instance to use for this object type
        """
        self._parsers[object_type] = parser
    
    def get_parser(self, object_type: str) -> BaseParser:
        """
        Get the appropriate parser for an object type.
        
        Args:
            object_type: The Appian object type
            
        Returns:
            Parser instance for the object type, or UnknownObjectParser
                if no specific parser is registered
        """
        return self._parsers.get(object_type, self._unknown_parser)
    
    def get_supported_types(self) -> list:
        """
        Get list of supported object types.
        
        Returns:
            List of object type names that have registered parsers
        """
        return list(self._parsers.keys())


# Create a singleton instance for the application
_factory_instance = None


def get_parser_factory() -> XMLParserFactory:
    """
    Get the singleton XMLParserFactory instance.
    
    Returns:
        The global XMLParserFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = XMLParserFactory()
    return _factory_instance
