# Parser Layer

This module provides the infrastructure for parsing Appian XML files.

## Components

### BaseParser (base_parser.py)

Abstract base class for all object-specific parsers. Provides common utility methods:

- `parse(xml_path)` - Abstract method to be implemented by subclasses
- `_extract_basic_info(root)` - Extracts uuid, name, version_uuid, description
- `_get_text(element, path)` - Safely retrieves text from XML element
- `_get_attribute(element, path, attribute)` - Safely retrieves attribute value
- `_clean_sail_code(sail_code)` - Normalizes SAIL code for comparison
- `_get_boolean(element, path, default)` - Retrieves boolean value
- `_get_int(element, path, default)` - Retrieves integer value

### XMLParserFactory (xml_parser_factory.py)

Factory for creating appropriate parsers based on object type.

- `register_parser(object_type, parser)` - Register a parser for an object type
- `get_parser(object_type)` - Get parser for object type (returns UnknownObjectParser if not found)
- `get_supported_types()` - List all registered object types
- `get_parser_factory()` - Get singleton factory instance

### UnknownObjectParser (xml_parser_factory.py)

Default parser for unrecognized object types. Extracts basic info and stores raw XML.

## Usage

```python
from services.parsers.xml_parser_factory import get_parser_factory

# Get the factory
factory = get_parser_factory()

# Register a custom parser
factory.register_parser('Interface', InterfaceParser())

# Get a parser and parse XML
parser = factory.get_parser('Interface')
data = parser.parse('/path/to/interface.xml')
```

## Testing

Run tests with:
```bash
python -m pytest tests/test_parsers.py -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

All 18 tests pass, covering:
- Basic info extraction
- Text and attribute retrieval
- SAIL code cleaning
- Boolean and integer parsing
- Factory registration and retrieval
- Unknown object handling
