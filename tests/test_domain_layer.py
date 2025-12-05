"""
Tests for domain layer components.

This test file verifies that the domain enums, entities, and comparison
strategies work correctly.
"""

import pytest
from domain.enums import (
    PackageType,
    ChangeCategory,
    Classification,
    ChangeType,
    SessionStatus
)
from domain.entities import (
    ObjectIdentity,
    DeltaChange,
    CustomerModification,
    ClassifiedChange
)
from domain.comparison_strategies import (
    SimpleVersionComparisonStrategy,
    SAILCodeComparisonStrategy,
    StructuralComparisonStrategy,
    CompositeComparisonStrategy
)


class TestEnums:
    """Test domain enums."""

    def test_package_type_values(self):
        """Test PackageType enum values."""
        assert PackageType.BASE.value == 'base'
        assert PackageType.CUSTOMIZED.value == 'customized'
        assert PackageType.NEW_VENDOR.value == 'new_vendor'

    def test_change_category_values(self):
        """Test ChangeCategory enum values."""
        assert ChangeCategory.NEW.value == 'NEW'
        assert ChangeCategory.MODIFIED.value == 'MODIFIED'
        assert ChangeCategory.DEPRECATED.value == 'DEPRECATED'

    def test_classification_values(self):
        """Test Classification enum values."""
        assert Classification.NO_CONFLICT.value == 'NO_CONFLICT'
        assert Classification.CONFLICT.value == 'CONFLICT'
        assert Classification.NEW.value == 'NEW'
        assert Classification.DELETED.value == 'DELETED'

    def test_change_type_values(self):
        """Test ChangeType enum values."""
        assert ChangeType.ADDED.value == 'ADDED'
        assert ChangeType.MODIFIED.value == 'MODIFIED'
        assert ChangeType.REMOVED.value == 'REMOVED'

    def test_session_status_values(self):
        """Test SessionStatus enum values."""
        assert SessionStatus.PROCESSING.value == 'processing'
        assert SessionStatus.READY.value == 'ready'
        assert SessionStatus.IN_PROGRESS.value == 'in_progress'
        assert SessionStatus.COMPLETED.value == 'completed'
        assert SessionStatus.ERROR.value == 'error'


class TestEntities:
    """Test domain entities."""

    def test_object_identity_creation(self):
        """Test ObjectIdentity creation with valid data."""
        obj = ObjectIdentity(
            uuid='test-uuid-123',
            name='Test Object',
            object_type='Interface',
            description='Test description'
        )
        assert obj.uuid == 'test-uuid-123'
        assert obj.name == 'Test Object'
        assert obj.object_type == 'Interface'
        assert obj.description == 'Test description'

    def test_object_identity_validation(self):
        """Test ObjectIdentity validation."""
        with pytest.raises(ValueError, match="uuid is required"):
            ObjectIdentity(uuid='', name='Test', object_type='Interface')

        with pytest.raises(ValueError, match="name is required"):
            ObjectIdentity(uuid='test-uuid', name='', object_type='Interface')

        with pytest.raises(ValueError, match="object_type is required"):
            ObjectIdentity(uuid='test-uuid', name='Test', object_type='')

    def test_delta_change_creation(self):
        """Test DeltaChange creation with valid data."""
        change = DeltaChange(
            object_id=1,
            change_category=ChangeCategory.MODIFIED,
            version_changed=True,
            content_changed=False
        )
        assert change.object_id == 1
        assert change.change_category == ChangeCategory.MODIFIED
        assert change.version_changed is True
        assert change.content_changed is False

    def test_delta_change_validation(self):
        """Test DeltaChange validation."""
        with pytest.raises(ValueError, match="object_id must be positive"):
            DeltaChange(
                object_id=0,
                change_category=ChangeCategory.NEW,
                version_changed=False,
                content_changed=False
            )

    def test_customer_modification_creation(self):
        """Test CustomerModification creation."""
        mod = CustomerModification(
            object_id=1,
            exists_in_customer=True,
            customer_modified=True,
            version_changed=False,
            content_changed=True
        )
        assert mod.object_id == 1
        assert mod.exists_in_customer is True
        assert mod.customer_modified is True

    def test_classified_change_creation(self):
        """Test ClassifiedChange creation."""
        change = ClassifiedChange(
            object_id=1,
            classification=Classification.CONFLICT,
            vendor_change_type=ChangeType.MODIFIED,
            customer_change_type=ChangeType.MODIFIED,
            display_order=0
        )
        assert change.object_id == 1
        assert change.classification == Classification.CONFLICT
        assert change.vendor_change_type == ChangeType.MODIFIED
        assert change.customer_change_type == ChangeType.MODIFIED


class TestComparisonStrategies:
    """Test comparison strategies."""

    def test_simple_version_comparison_same(self):
        """Test version comparison with same versions."""
        strategy = SimpleVersionComparisonStrategy()
        assert strategy.compare('v1', 'v1') is False

    def test_simple_version_comparison_different(self):
        """Test version comparison with different versions."""
        strategy = SimpleVersionComparisonStrategy()
        assert strategy.compare('v1', 'v2') is True

    def test_simple_version_comparison_none(self):
        """Test version comparison with None values."""
        strategy = SimpleVersionComparisonStrategy()
        assert strategy.compare(None, None) is False
        assert strategy.compare('v1', None) is True
        assert strategy.compare(None, 'v1') is True

    def test_sail_code_comparison_same(self):
        """Test SAIL code comparison with same code."""
        strategy = SAILCodeComparisonStrategy()
        content_a = {'sail_code': 'a!localVariables()'}
        content_b = {'sail_code': 'a!localVariables()'}
        assert strategy.compare(content_a, content_b) is False

    def test_sail_code_comparison_different(self):
        """Test SAIL code comparison with different code."""
        strategy = SAILCodeComparisonStrategy()
        content_a = {'sail_code': 'a!localVariables()'}
        content_b = {'sail_code': 'a!localVariables(x: 1)'}
        assert strategy.compare(content_a, content_b) is True

    def test_sail_code_comparison_custom_fields(self):
        """Test SAIL code comparison with custom fields."""
        strategy = SAILCodeComparisonStrategy(
            critical_fields=['sail_code', 'parameters']
        )
        content_a = {
            'sail_code': 'test',
            'parameters': ['a', 'b']
        }
        content_b = {
            'sail_code': 'test',
            'parameters': ['a', 'b', 'c']
        }
        assert strategy.compare(content_a, content_b) is True

    def test_structural_comparison_same(self):
        """Test structural comparison with same structure."""
        strategy = StructuralComparisonStrategy()
        content_a = {'field1': 'value1', 'field2': 'value2'}
        content_b = {'field1': 'value1', 'field2': 'value2'}
        assert strategy.compare(content_a, content_b) is False

    def test_structural_comparison_different(self):
        """Test structural comparison with different structure."""
        strategy = StructuralComparisonStrategy()
        content_a = {'field1': 'value1'}
        content_b = {'field1': 'value2'}
        assert strategy.compare(content_a, content_b) is True

    def test_structural_comparison_ignores_fields(self):
        """Test structural comparison ignores specified fields."""
        strategy = StructuralComparisonStrategy(
            ignore_fields=['created_at']
        )
        content_a = {'field1': 'value1', 'created_at': '2024-01-01'}
        content_b = {'field1': 'value1', 'created_at': '2024-01-02'}
        assert strategy.compare(content_a, content_b) is False

    def test_composite_comparison_any_difference(self):
        """Test composite comparison detects any difference."""
        strategies = [
            SAILCodeComparisonStrategy(),
            StructuralComparisonStrategy()
        ]
        composite = CompositeComparisonStrategy(strategies)

        content_a = {'sail_code': 'test1', 'field': 'value'}
        content_b = {'sail_code': 'test2', 'field': 'value'}
        assert composite.compare(content_a, content_b) is True

    def test_composite_comparison_no_difference(self):
        """Test composite comparison with no differences."""
        strategies = [
            SAILCodeComparisonStrategy(),
            StructuralComparisonStrategy()
        ]
        composite = CompositeComparisonStrategy(strategies)

        content_a = {'sail_code': 'test', 'field': 'value'}
        content_b = {'sail_code': 'test', 'field': 'value'}
        assert composite.compare(content_a, content_b) is False

    def test_composite_comparison_requires_strategies(self):
        """Test composite comparison requires at least one strategy."""
        with pytest.raises(ValueError, match="At least one strategy"):
            CompositeComparisonStrategy([])
