"""
Unit tests for enhanced data models
"""
import unittest
from datetime import datetime
from services.appian_analyzer.models import (
    VersionInfo,
    ImportChangeStatus,
    AppianObject,
    ComparisonResult,
    EnhancedComparisonReport,
    Site,
    RecordType,
    ProcessModel,
    SimpleObject,
    Blueprint
)


class TestVersionInfo(unittest.TestCase):
    """Test VersionInfo dataclass"""

    def test_version_info_creation(self):
        """Test creating a VersionInfo instance"""
        timestamp = datetime.now()
        version = VersionInfo(
            version_uuid="test-uuid-123",
            timestamp=timestamp,
            author="test.user",
            description="Test version"
        )

        self.assertEqual(version.version_uuid, "test-uuid-123")
        self.assertEqual(version.timestamp, timestamp)
        self.assertEqual(version.author, "test.user")
        self.assertEqual(version.description, "Test version")

    def test_version_info_default_description(self):
        """Test VersionInfo with default description"""
        timestamp = datetime.now()
        version = VersionInfo(
            version_uuid="test-uuid-123",
            timestamp=timestamp,
            author="test.user"
        )

        self.assertEqual(version.description, "")


class TestImportChangeStatus(unittest.TestCase):
    """Test ImportChangeStatus enum"""

    def test_all_status_values(self):
        """Test all ImportChangeStatus enum values"""
        self.assertEqual(ImportChangeStatus.NEW.value, "NEW")
        self.assertEqual(ImportChangeStatus.CHANGED.value, "CHANGED")
        self.assertEqual(
            ImportChangeStatus.CONFLICT_DETECTED.value,
            "CONFLICT_DETECTED"
        )
        self.assertEqual(
            ImportChangeStatus.NOT_CHANGED.value,
            "NOT_CHANGED"
        )
        self.assertEqual(
            ImportChangeStatus.NOT_CHANGED_NEW_VUUID.value,
            "NOT_CHANGED_NEW_VUUID"
        )
        self.assertEqual(ImportChangeStatus.REMOVED.value, "REMOVED")
        self.assertEqual(ImportChangeStatus.UNKNOWN.value, "UNKNOWN")

    def test_status_count(self):
        """Test that we have exactly 7 status values"""
        self.assertEqual(len(ImportChangeStatus), 7)


class TestAppianObject(unittest.TestCase):
    """Test enhanced AppianObject"""

    def test_appian_object_creation(self):
        """Test creating an AppianObject with all fields"""
        obj = AppianObject(
            uuid="obj-uuid-123",
            name="Test Object",
            object_type="Interface",
            description="Test description",
            raw_xml="<xml>test</xml>",
            version_uuid="v-uuid-123",
            diff_hash="abc123"
        )

        self.assertEqual(obj.uuid, "obj-uuid-123")
        self.assertEqual(obj.name, "Test Object")
        self.assertEqual(obj.object_type, "Interface")
        self.assertEqual(obj.description, "Test description")
        self.assertEqual(obj.raw_xml, "<xml>test</xml>")
        self.assertEqual(obj.version_uuid, "v-uuid-123")
        self.assertEqual(obj.diff_hash, "abc123")

    def test_appian_object_default_values(self):
        """Test AppianObject with default values"""
        obj = AppianObject(
            uuid="obj-uuid-123",
            name="Test Object",
            object_type="Interface"
        )

        self.assertEqual(obj.description, "")
        self.assertEqual(obj.raw_xml, "")
        self.assertEqual(obj.version_uuid, "")
        self.assertEqual(obj.version_history, [])
        self.assertEqual(obj.raw_xml_data, {})
        self.assertEqual(obj.diff_hash, "")

    def test_appian_object_with_version_history(self):
        """Test AppianObject with version history"""
        timestamp = datetime.now()
        version1 = VersionInfo(
            version_uuid="v1",
            timestamp=timestamp,
            author="user1"
        )
        version2 = VersionInfo(
            version_uuid="v2",
            timestamp=timestamp,
            author="user2"
        )

        obj = AppianObject(
            uuid="obj-uuid-123",
            name="Test Object",
            object_type="Interface",
            version_history=[version1, version2]
        )

        self.assertEqual(len(obj.version_history), 2)
        self.assertEqual(obj.version_history[0].version_uuid, "v1")
        self.assertEqual(obj.version_history[1].version_uuid, "v2")

    def test_appian_object_with_raw_xml_data(self):
        """Test AppianObject with raw XML data"""
        obj = AppianObject(
            uuid="obj-uuid-123",
            name="Test Object",
            object_type="Interface",
            raw_xml_data={"element1": "value1", "element2": "value2"}
        )

        self.assertEqual(obj.raw_xml_data["element1"], "value1")
        self.assertEqual(obj.raw_xml_data["element2"], "value2")


class TestComparisonResult(unittest.TestCase):
    """Test ComparisonResult dataclass"""

    def test_comparison_result_creation(self):
        """Test creating a ComparisonResult"""
        obj = AppianObject(
            uuid="obj-uuid-123",
            name="Test Object",
            object_type="Interface"
        )

        result = ComparisonResult(
            status=ImportChangeStatus.CHANGED,
            obj=obj,
            version_info={"old": "v1", "new": "v2"},
            content_diff="Some diff",
            diagnostics=["Warning 1", "Warning 2"]
        )

        self.assertEqual(result.status, ImportChangeStatus.CHANGED)
        self.assertEqual(result.obj.uuid, "obj-uuid-123")
        self.assertEqual(result.version_info["old"], "v1")
        self.assertEqual(result.content_diff, "Some diff")
        self.assertEqual(len(result.diagnostics), 2)

    def test_comparison_result_default_values(self):
        """Test ComparisonResult with default values"""
        obj = AppianObject(
            uuid="obj-uuid-123",
            name="Test Object",
            object_type="Interface"
        )

        result = ComparisonResult(
            status=ImportChangeStatus.NEW,
            obj=obj
        )

        self.assertIsNone(result.version_info)
        self.assertIsNone(result.content_diff)
        self.assertEqual(result.diagnostics, [])


class TestEnhancedComparisonReport(unittest.TestCase):
    """Test EnhancedComparisonReport dataclass"""

    def test_enhanced_comparison_report_creation(self):
        """Test creating an EnhancedComparisonReport"""
        obj = AppianObject(
            uuid="obj-uuid-123",
            name="Test Object",
            object_type="Interface"
        )

        result = ComparisonResult(
            status=ImportChangeStatus.CHANGED,
            obj=obj
        )

        report = EnhancedComparisonReport(
            summary={"total_changes": 1},
            changes_by_status={ImportChangeStatus.CHANGED: [result]},
            changes_by_category={"interfaces": {"added": 0, "modified": 1}},
            detailed_changes=[result],
            impact_assessment={"level": "LOW"},
            diagnostics=["Info message"]
        )

        self.assertEqual(report.summary["total_changes"], 1)
        self.assertEqual(
            len(report.changes_by_status[ImportChangeStatus.CHANGED]),
            1
        )
        self.assertEqual(
            report.changes_by_category["interfaces"]["modified"],
            1
        )
        self.assertEqual(len(report.detailed_changes), 1)
        self.assertEqual(report.impact_assessment["level"], "LOW")
        self.assertEqual(len(report.diagnostics), 1)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing data"""

    def test_site_backward_compatibility(self):
        """Test Site still works with existing code"""
        site = Site(
            uuid="site-uuid",
            name="Test Site",
            object_type="Site"
        )

        self.assertEqual(site.uuid, "site-uuid")
        self.assertEqual(site.pages, [])
        self.assertEqual(site.security, {"roles": []})
        # New fields should have defaults
        self.assertEqual(site.raw_xml, "")
        self.assertEqual(site.version_uuid, "")

    def test_record_type_backward_compatibility(self):
        """Test RecordType still works with existing code"""
        record = RecordType(
            uuid="record-uuid",
            name="Test Record",
            object_type="Record Type"
        )

        self.assertEqual(record.uuid, "record-uuid")
        self.assertEqual(record.fields, [])
        self.assertEqual(record.relationships, [])
        # New fields should have defaults
        self.assertEqual(record.raw_xml, "")
        self.assertEqual(record.version_history, [])

    def test_process_model_backward_compatibility(self):
        """Test ProcessModel still works with existing code"""
        process = ProcessModel(
            uuid="process-uuid",
            name="Test Process",
            object_type="Process Model"
        )

        self.assertEqual(process.uuid, "process-uuid")
        self.assertEqual(process.variables, [])
        self.assertEqual(process.nodes, [])
        # New fields should have defaults
        self.assertEqual(process.raw_xml_data, {})
        self.assertEqual(process.diff_hash, "")

    def test_simple_object_backward_compatibility(self):
        """Test SimpleObject still works with existing code"""
        obj = SimpleObject(
            uuid="obj-uuid",
            name="Test Interface",
            object_type="Interface",
            sail_code="a!textField()"
        )

        self.assertEqual(obj.uuid, "obj-uuid")
        self.assertEqual(obj.sail_code, "a!textField()")
        # New fields should have defaults
        self.assertEqual(obj.raw_xml, "")
        self.assertEqual(obj.version_uuid, "")


if __name__ == '__main__':
    unittest.main()
