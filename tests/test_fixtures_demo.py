"""
Demo test showing how to use the three-way merge test fixtures.

This is a reference for other tests that need to use the fixtures.
"""

import pytest
from pathlib import Path
from tests.fixtures.three_way_merge.fixture_loader import (
    SMALL_PACKAGES,
    MEDIUM_PACKAGES,
    LARGE_PACKAGES,
    CIRCULAR_DEPENDENCY_PACKAGES,
    KNOWN_DIFFERENCES_PACKAGES,
    get_all_fixture_sets,
    get_malformed_packages,
    get_fixture_by_name
)


class TestFixtureLoader:
    """Test that fixtures can be loaded correctly"""
    
    def test_small_packages_exist(self):
        """Test that small package fixtures exist"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()
        
        assert base.exists(), f"Base package not found: {base}"
        assert customized.exists(), f"Customized package not found: {customized}"
        assert new_vendor.exists(), f"New vendor package not found: {new_vendor}"
    
    def test_all_fixture_sets_exist(self):
        """Test that all fixture sets exist"""
        for fixture_set in get_all_fixture_sets():
            base, customized, new_vendor = fixture_set.get_paths()
            
            assert base.exists(), f"{fixture_set.name}: Base package not found"
            assert customized.exists(), f"{fixture_set.name}: Customized package not found"
            assert new_vendor.exists(), f"{fixture_set.name}: New vendor package not found"
    
    def test_malformed_packages_exist(self):
        """Test that malformed packages exist"""
        for malformed_path in get_malformed_packages():
            assert malformed_path.exists(), f"Malformed package not found: {malformed_path}"
    
    def test_get_fixture_by_name(self):
        """Test getting fixtures by name"""
        small = get_fixture_by_name("small")
        assert small.name == "small"
        assert small.base_path.exists()
        
        medium = get_fixture_by_name("medium")
        assert medium.name == "medium"
        
        with pytest.raises(ValueError):
            get_fixture_by_name("nonexistent")
    
    def test_expected_results_available(self):
        """Test that expected results are documented"""
        assert "conflicts" in KNOWN_DIFFERENCES_PACKAGES.expected_results
        assert "no_conflicts" in KNOWN_DIFFERENCES_PACKAGES.expected_results
        assert "customer_only" in KNOWN_DIFFERENCES_PACKAGES.expected_results
        assert "removed_but_customized" in KNOWN_DIFFERENCES_PACKAGES.expected_results


class TestFixtureUsageExamples:
    """Examples of how to use fixtures in actual tests"""
    
    def test_example_using_small_packages(self):
        """Example: Using small packages in a test"""
        base_path, customized_path, new_vendor_path = SMALL_PACKAGES.get_paths()
        
        # In a real test, you would:
        # 1. Load the packages
        # 2. Run your merge logic
        # 3. Assert against expected_results
        
        expected = SMALL_PACKAGES.expected_results
        assert "HomePage" in expected["conflicts"]
        assert "CustomerOnlyRule" in expected["customer_only"]
    
    def test_example_parametrized_test(self):
        """Example: Parametrized test across all fixture sets"""
        for fixture_set in get_all_fixture_sets():
            base, customized, new_vendor = fixture_set.get_paths()
            
            # Verify all paths exist
            assert base.exists()
            assert customized.exists()
            assert new_vendor.exists()
            
            # In a real test, you would run your merge logic here
            # and assert against fixture_set.expected_results
    
    def test_example_error_handling(self):
        """Example: Testing error handling with malformed packages"""
        for malformed_path in get_malformed_packages():
            # In a real test, you would:
            # 1. Try to load the malformed package
            # 2. Assert that appropriate error is raised
            # 3. Assert that error message is user-friendly
            
            assert malformed_path.exists()
            # Example assertion:
            # with pytest.raises(ValidationError):
            #     load_package(malformed_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
