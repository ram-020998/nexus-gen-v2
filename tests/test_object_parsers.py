"""
Tests for object-specific parsers using real XML samples.

This module tests that each parser can successfully parse its corresponding
sample XML file from applicationArtifacts/ObjectSpecificXml/.
"""

import pytest
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


class TestInterfaceParser:
    """Tests for InterfaceParser."""

    def test_parse_interface_xml(self):
        """Test parsing real Interface XML file."""
        parser = InterfaceParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /interface.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert data['sail_code'] is not None
        assert isinstance(data['parameters'], list)
        assert isinstance(data['security'], list)
        assert len(data['parameters']) > 0  # Should have parameters


class TestExpressionRuleParser:
    """Tests for ExpressionRuleParser."""

    def test_parse_expression_rule_xml(self):
        """Test parsing real Expression Rule XML file."""
        parser = ExpressionRuleParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /expressionRule.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert data['sail_code'] is not None
        assert isinstance(data['inputs'], list)
        assert len(data['inputs']) > 0  # Should have inputs


class TestProcessModelParser:
    """Tests for ProcessModelParser."""

    def test_parse_process_model_xml(self):
        """Test parsing real Process Model XML file."""
        parser = ProcessModelParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /processModel.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert isinstance(data['nodes'], list)
        assert isinstance(data['flows'], list)
        assert isinstance(data['variables'], list)
        assert data['total_nodes'] > 0
        assert data['complexity_score'] >= 0


class TestRecordTypeParser:
    """Tests for RecordTypeParser."""

    def test_parse_record_type_xml(self):
        """Test parsing real Record Type XML file."""
        parser = RecordTypeParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /recordType.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert isinstance(data['fields'], list)
        assert isinstance(data['relationships'], list)
        assert isinstance(data['views'], list)
        assert len(data['fields']) > 0  # Should have fields


class TestCDTParser:
    """Tests for CDTParser."""

    def test_parse_cdt_xml(self):
        """Test parsing real CDT XSD file."""
        parser = CDTParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /dataType.xsd'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert data['namespace'] is not None
        assert isinstance(data['fields'], list)
        assert len(data['fields']) > 0  # Should have fields


class TestIntegrationParser:
    """Tests for IntegrationParser."""

    def test_parse_integration_xml(self):
        """Test parsing real Integration XML file."""
        parser = IntegrationParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /integration.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        # SAIL code may or may not be present
        assert 'sail_code' in data


class TestWebAPIParser:
    """Tests for WebAPIParser."""

    def test_parse_web_api_xml(self):
        """Test parsing real Web API XML file."""
        parser = WebAPIParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /webApi.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert isinstance(data['http_methods'], list)


class TestSiteParser:
    """Tests for SiteParser."""

    def test_parse_site_xml(self):
        """Test parsing real Site XML file."""
        parser = SiteParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /site.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert isinstance(data['pages'], list)


class TestGroupParser:
    """Tests for GroupParser."""

    def test_parse_group_xml(self):
        """Test parsing real Group XML file."""
        parser = GroupParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /group.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert isinstance(data['members'], list)


class TestConstantParser:
    """Tests for ConstantParser."""

    def test_parse_constant_xml(self):
        """Test parsing real Constant XML file."""
        parser = ConstantParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /constant.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert 'value' in data
        assert 'value_type' in data


class TestConnectedSystemParser:
    """Tests for ConnectedSystemParser."""

    def test_parse_connected_system_xml(self):
        """Test parsing real Connected System XML file."""
        parser = ConnectedSystemParser()
        xml_path = 'applicationArtifacts/ObjectSpecificXml /connectedSystem.xml'

        data = parser.parse(xml_path)

        assert data is not None
        assert data['uuid'] is not None
        assert data['name'] is not None
        assert 'system_type' in data
        assert 'properties' in data
