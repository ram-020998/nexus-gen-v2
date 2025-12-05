"""
Tests for parser layer - BaseParser and XMLParserFactory.

These tests verify the basic functionality of the parser infrastructure.
"""

import pytest
import xml.etree.ElementTree as ET
from io import StringIO
from services.parsers.base_parser import BaseParser
from services.parsers.xml_parser_factory import (
    XMLParserFactory,
    UnknownObjectParser,
    get_parser_factory
)


class TestBaseParser:
    """Tests for BaseParser utility methods."""

    def test_extract_basic_info(self):
        """Test extraction of basic object information from XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object uuid="test-uuid-123" name="Test Object" versionUuid="v1">
            <description>Test description</description>
        </object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        info = parser._extract_basic_info(root)
        
        assert info['uuid'] == 'test-uuid-123'
        assert info['name'] == 'Test Object'
        assert info['version_uuid'] == 'v1'
        assert info['description'] == 'Test description'

    def test_get_text_existing_element(self):
        """Test getting text from existing XML element."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object>
            <field>Value</field>
        </object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        text = parser._get_text(root, 'field')
        
        assert text == 'Value'

    def test_get_text_missing_element(self):
        """Test getting text from missing XML element returns None."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object>
            <field>Value</field>
        </object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        text = parser._get_text(root, 'missing')
        
        assert text is None

    def test_clean_sail_code_normalizes_whitespace(self):
        """Test SAIL code cleaning normalizes whitespace."""
        parser = UnknownObjectParser()
        
        sail_code = """
        
        a!localVariables(
          local!value:  "test",
          local!result:   123
        )
        
        """
        
        cleaned = parser._clean_sail_code(sail_code)
        
        # Should remove leading/trailing blank lines
        assert not cleaned.startswith('\n')
        assert not cleaned.endswith('\n\n')
        
        # Should contain the function call
        assert 'a!localVariables' in cleaned

    def test_clean_sail_code_handles_none(self):
        """Test SAIL code cleaning handles None input."""
        parser = UnknownObjectParser()
        
        cleaned = parser._clean_sail_code(None)
        
        assert cleaned is None

    def test_clean_sail_code_handles_empty_string(self):
        """Test SAIL code cleaning handles empty string."""
        parser = UnknownObjectParser()
        
        cleaned = parser._clean_sail_code("")
        
        assert cleaned is None

    def test_get_boolean_true_values(self):
        """Test getting boolean values for true."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object>
            <flag1>true</flag1>
            <flag2>True</flag2>
            <flag3>1</flag3>
            <flag4>yes</flag4>
        </object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        
        assert parser._get_boolean(root, 'flag1') is True
        assert parser._get_boolean(root, 'flag2') is True
        assert parser._get_boolean(root, 'flag3') is True
        assert parser._get_boolean(root, 'flag4') is True

    def test_get_boolean_false_values(self):
        """Test getting boolean values for false."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object>
            <flag1>false</flag1>
            <flag2>0</flag2>
            <flag3>no</flag3>
        </object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        
        assert parser._get_boolean(root, 'flag1') is False
        assert parser._get_boolean(root, 'flag2') is False
        assert parser._get_boolean(root, 'flag3') is False

    def test_get_boolean_missing_uses_default(self):
        """Test getting boolean from missing element uses default."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object></object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        
        assert parser._get_boolean(root, 'missing') is False
        assert parser._get_boolean(root, 'missing', default=True) is True

    def test_get_int_valid_value(self):
        """Test getting integer value."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object>
            <count>42</count>
        </object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        
        assert parser._get_int(root, 'count') == 42

    def test_get_int_missing_uses_default(self):
        """Test getting integer from missing element uses default."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object></object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        
        assert parser._get_int(root, 'missing') == 0
        assert parser._get_int(root, 'missing', default=99) == 99

    def test_get_int_invalid_value_uses_default(self):
        """Test getting integer from invalid value uses default."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <object>
            <count>not-a-number</count>
        </object>
        """
        root = ET.fromstring(xml_content)
        
        parser = UnknownObjectParser()
        
        assert parser._get_int(root, 'count') == 0
        assert parser._get_int(root, 'count', default=99) == 99


class TestXMLParserFactory:
    """Tests for XMLParserFactory."""

    def test_factory_initialization(self):
        """Test factory initializes correctly with default parsers."""
        factory = XMLParserFactory()
        
        assert factory is not None
        # Factory should have default parsers registered
        supported_types = factory.get_supported_types()
        assert len(supported_types) > 0
        assert 'Interface' in supported_types
        assert 'Expression Rule' in supported_types
        assert 'Process Model' in supported_types

    def test_register_and_get_parser(self):
        """Test registering and retrieving a parser."""
        factory = XMLParserFactory()
        parser = UnknownObjectParser()
        
        factory.register_parser('TestType', parser)
        
        retrieved = factory.get_parser('TestType')
        assert retrieved is parser

    def test_get_parser_unknown_type_returns_unknown_parser(self):
        """Test getting parser for unknown type returns UnknownObjectParser."""
        factory = XMLParserFactory()
        
        parser = factory.get_parser('NonExistentType')
        
        assert isinstance(parser, UnknownObjectParser)

    def test_get_supported_types(self):
        """Test getting list of supported types."""
        factory = XMLParserFactory()
        parser1 = UnknownObjectParser()
        parser2 = UnknownObjectParser()
        
        # Get initial count
        initial_count = len(factory.get_supported_types())
        
        factory.register_parser('Type1', parser1)
        factory.register_parser('Type2', parser2)
        
        types = factory.get_supported_types()
        
        assert 'Type1' in types
        assert 'Type2' in types
        # Should have initial parsers plus the 2 we added
        assert len(types) == initial_count + 2

    def test_singleton_factory(self):
        """Test get_parser_factory returns singleton instance."""
        factory1 = get_parser_factory()
        factory2 = get_parser_factory()
        
        assert factory1 is factory2


class TestUnknownObjectParser:
    """Tests for UnknownObjectParser."""

    def test_parse_unknown_object(self, tmp_path):
        """Test parsing an unknown object type."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <unknownObject uuid="unknown-123" name="Unknown" versionUuid="v1">
            <description>Unknown object type</description>
            <customField>Custom value</customField>
        </unknownObject>
        """
        
        xml_file = tmp_path / "unknown.xml"
        xml_file.write_text(xml_content)
        
        parser = UnknownObjectParser()
        data = parser.parse(str(xml_file))
        
        assert data['uuid'] == 'unknown-123'
        assert data['name'] == 'Unknown'
        assert data['version_uuid'] == 'v1'
        assert data['description'] == 'Unknown object type'
        assert 'raw_xml' in data
        assert 'customField' in data['raw_xml']
