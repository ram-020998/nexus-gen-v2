"""
Integration test to verify fixtures work with actual merge assistant services.

This test demonstrates that the fixtures are compatible with the real services.
"""

import pytest
from pathlib import Path
from tests.fixtures.three_way_merge.fixture_loader import SMALL_PACKAGES


class TestFixtureIntegration:
    """Test that fixtures work with actual services"""
    
    def test_fixtures_are_valid_zip_files(self):
        """Verify fixtures are valid ZIP files"""
        import zipfile
        
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()
        
        # Should be able to open as ZIP files
        with zipfile.ZipFile(base, 'r') as zf:
            assert len(zf.namelist()) > 0
        
        with zipfile.ZipFile(customized, 'r') as zf:
            assert len(zf.namelist()) > 0
        
        with zipfile.ZipFile(new_vendor, 'r') as zf:
            assert len(zf.namelist()) > 0
    
    def test_fixtures_contain_application_xml(self):
        """Verify fixtures contain application.xml files"""
        import zipfile
        
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()
        
        for package_path in [base, customized, new_vendor]:
            with zipfile.ZipFile(package_path, 'r') as zf:
                files = zf.namelist()
                app_files = [f for f in files if f.startswith('application/')]
                assert len(app_files) > 0, f"No application files in {package_path.name}"
    
    def test_fixtures_contain_valid_xml(self):
        """Verify fixtures contain parseable XML"""
        import zipfile
        import xml.etree.ElementTree as ET
        
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()
        
        for package_path in [base, customized, new_vendor]:
            with zipfile.ZipFile(package_path, 'r') as zf:
                for file in zf.namelist():
                    content = zf.read(file)
                    # Should not raise ParseError
                    ET.fromstring(content)
    
    def test_fixture_paths_are_absolute(self):
        """Verify fixture paths are absolute for reliable access"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()
        
        assert base.is_absolute()
        assert customized.is_absolute()
        assert new_vendor.is_absolute()
    
    def test_all_fixture_sets_have_three_packages(self):
        """Verify all fixture sets have complete A, B, C packages"""
        from tests.fixtures.three_way_merge.fixture_loader import get_all_fixture_sets
        
        for fixture_set in get_all_fixture_sets():
            base, customized, new_vendor = fixture_set.get_paths()
            
            assert base.exists(), f"{fixture_set.name}: Missing base package"
            assert customized.exists(), f"{fixture_set.name}: Missing customized package"
            assert new_vendor.exists(), f"{fixture_set.name}: Missing new vendor package"
            
            # All should be different files
            assert base != customized
            assert base != new_vendor
            assert customized != new_vendor


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
