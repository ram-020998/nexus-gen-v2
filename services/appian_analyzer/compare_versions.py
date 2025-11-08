#!/usr/bin/env python3
"""
Simple CLI for comparing Appian application versions
"""

import sys
from .version_comparator import AppianVersionComparator

def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_versions.py <version1.zip> <version2.zip>")
        print("Example: python compare_versions.py applicationZips/AM_v1.0.zip applicationZips/AM_v2.0.zip")
        sys.exit(1)
    
    version1_zip = sys.argv[1]
    version2_zip = sys.argv[2]
    
    try:
        comparator = AppianVersionComparator(version1_zip, version2_zip)
        result = comparator.compare_versions()
        
        # Print detailed summary
        summary = result["comparison_summary"]
        print(f"\n🎯 Version Comparison Complete:")
        print(f"  📦 From: {summary['version_from']}")
        print(f"  📦 To: {summary['version_to']}")
        print(f"  📊 Total Changes: {summary['total_changes']}")
        print(f"  📈 Impact Level: {summary['impact_level']}")
        
        if result["changes_by_category"]:
            print(f"\n📋 Component Changes:")
            for category, changes in result["changes_by_category"].items():
                total = changes['total']
                if total > 0:
                    print(f"  • {category.replace('_', ' ').title()}: {total} changes")
                    print(f"    ➕ Added: {changes['added']}")
                    print(f"    🔄 Modified: {changes['modified']}")
                    print(f"    ➖ Removed: {changes['removed']}")
        
        print(f"\n📄 Detailed comparison saved to output/ folder")
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
