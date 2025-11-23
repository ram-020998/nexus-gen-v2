"""
XML parsers for different Appian object types

This module maintains backward compatibility by re-exporting all parser classes
from the new modular structure in the parsers/ package.

The parsers have been decomposed into separate files for better maintainability:
- base_parser.py: XMLParser base class
- site_parser.py: SiteParser
- record_type_parser.py: RecordTypeParser
- process_model_parser.py: ProcessModelParser
- content_parser.py: ContentParser
- simple_object_parser.py: SimpleObjectParser

All original functionality is preserved through these compatibility imports.
"""

# Import all parser classes from the new modular structure
from .parsers.base_parser import XMLParser
from .parsers.site_parser import SiteParser
from .parsers.record_type_parser import RecordTypeParser
from .parsers.process_model_parser import ProcessModelParser
from .parsers.content_parser import ContentParser
from .parsers.simple_object_parser import SimpleObjectParser

# Export all classes to maintain backward compatibility
__all__ = [
    'XMLParser',
    'SiteParser',
    'RecordTypeParser',
    'ProcessModelParser',
    'ContentParser',
    'SimpleObjectParser'
]
