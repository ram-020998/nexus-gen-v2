"""
Helper module for loading test fixtures in tests.

Provides convenient access to all test fixtures and their expected results.
"""

from pathlib import Path
from typing import Tuple, Dict, Any

# Base directory for fixtures
FIXTURES_DIR = Path(__file__).parent


class FixtureSet:
    """Represents a set of three related packages (A, B, C)"""
    
    def __init__(self, name: str, base_file: str, customized_file: str, new_vendor_file: str,
                 expected_results: Dict[str, Any] = None):
        self.name = name
        self.base_path = FIXTURES_DIR / base_file
        self.customized_path = FIXTURES_DIR / customized_file
        self.new_vendor_path = FIXTURES_DIR / new_vendor_file
        self.expected_results = expected_results or {}
    
    def get_paths(self) -> Tuple[Path, Path, Path]:
        """Get all three package paths as a tuple (base, customized, new_vendor)"""
        return (self.base_path, self.customized_path, self.new_vendor_path)
    
    def __repr__(self):
        return f"FixtureSet(name='{self.name}')"


# ============================================================================
# FIXTURE DEFINITIONS
# ============================================================================

SMALL_PACKAGES = FixtureSet(
    name="small",
    base_file="small_base_v1.0.zip",
    customized_file="small_customized_v1.0.zip",
    new_vendor_file="small_new_vendor_v2.0.zip",
    expected_results={
        "total_objects": 5,
        "conflicts": ["HomePage", "FormatName"],
        "no_conflicts": ["GetUserName", "User", "VendorNewFeature"],
        "customer_only": ["CustomerOnlyRule"],
        "removed_but_customized": []
    }
)

MEDIUM_PACKAGES = FixtureSet(
    name="medium",
    base_file="medium_base_v1.0.zip",
    customized_file="medium_customized_v1.0.zip",
    new_vendor_file="medium_new_vendor_v2.0.zip",
    expected_results={
        "total_objects": 25,
        "conflicts": ["Interface0"],
        "no_conflicts": ["Interface1", "VendorRule"],
        "customer_only": ["CustomerRule"],
        "removed_but_customized": []
    }
)

LARGE_PACKAGES = FixtureSet(
    name="large",
    base_file="large_base_v1.0.zip",
    customized_file="large_customized_v1.0.zip",
    new_vendor_file="large_new_vendor_v2.0.zip",
    expected_results={
        "total_objects": 60,
        "conflicts": 5,  # Interfaces 0-4
        "no_conflicts": 5,  # Interfaces 5-9
    }
)


CIRCULAR_DEPENDENCY_PACKAGES = FixtureSet(
    name="circular_dependency",
    base_file="circular_base_v1.0.zip",
    customized_file="circular_customized_v1.0.zip",
    new_vendor_file="circular_new_vendor_v2.0.zip",
    expected_results={
        "has_circular_dependency": True,
        "circular_objects": ["RuleA", "RuleB", "RuleC"]
    }
)

KNOWN_DIFFERENCES_PACKAGES = FixtureSet(
    name="known_differences",
    base_file="known_diff_base_v1.0.zip",
    customized_file="known_diff_customized_v1.0.zip",
    new_vendor_file="known_diff_new_vendor_v2.0.zip",
    expected_results={
        "conflicts": ["SharedInterface", "SharedRule"],
        "no_conflicts": ["VendorOnlyRule"],
        "customer_only": ["CustomerOnlyRule"],
        "removed_but_customized": ["ToBeRemoved"]
    }
)

# Malformed packages (single files, not sets)
MALFORMED_NO_APPLICATION = FIXTURES_DIR / "malformed_no_application.zip"
MALFORMED_INVALID_XML = FIXTURES_DIR / "malformed_invalid_xml.zip"
MALFORMED_EMPTY = FIXTURES_DIR / "malformed_empty.zip"
MALFORMED_WRONG_STRUCTURE = FIXTURES_DIR / "malformed_wrong_structure.zip"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_fixture_sets():
    """Get all valid fixture sets"""
    return [
        SMALL_PACKAGES,
        MEDIUM_PACKAGES,
        LARGE_PACKAGES,
        CIRCULAR_DEPENDENCY_PACKAGES,
        KNOWN_DIFFERENCES_PACKAGES
    ]


def get_malformed_packages():
    """Get all malformed package paths"""
    return [
        MALFORMED_NO_APPLICATION,
        MALFORMED_INVALID_XML,
        MALFORMED_EMPTY,
        MALFORMED_WRONG_STRUCTURE
    ]


def get_fixture_by_name(name: str) -> FixtureSet:
    """Get a fixture set by name"""
    fixtures = {
        "small": SMALL_PACKAGES,
        "medium": MEDIUM_PACKAGES,
        "large": LARGE_PACKAGES,
        "circular": CIRCULAR_DEPENDENCY_PACKAGES,
        "known_diff": KNOWN_DIFFERENCES_PACKAGES
    }
    
    if name not in fixtures:
        raise ValueError(f"Unknown fixture name: {name}. Available: {list(fixtures.keys())}")
    
    return fixtures[name]


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("Available Test Fixtures:\n")
    
    for fixture_set in get_all_fixture_sets():
        print(f"📦 {fixture_set.name.upper()}")
        print(f"   Base: {fixture_set.base_path.name}")
        print(f"   Customized: {fixture_set.customized_path.name}")
        print(f"   New Vendor: {fixture_set.new_vendor_path.name}")
        if fixture_set.expected_results:
            print(f"   Expected: {fixture_set.expected_results}")
        print()
    
    print("\n🚫 Malformed Packages:")
    for malformed in get_malformed_packages():
        print(f"   - {malformed.name}")
