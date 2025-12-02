"""
Test SAIL Diff Service
Quick test to verify the GitHub-style diff generation works correctly
"""

from services.sail_diff_service import SailDiffService


def test_sail_diff_basic():
    """Test basic diff generation"""
    
    old_code = """a!localVariables(
  local!items: {1, 2, 3},
  local!total: sum(local!items)
)"""
    
    new_code = """a!localVariables(
  local!items: {1, 2, 3, 4, 5},
  local!total: sum(local!items),
  local!average: avg(local!items)
)"""
    
    service = SailDiffService()
    
    # Generate diff
    hunks = service.generate_unified_diff(old_code, new_code)
    
    print(f"\n✓ Generated {len(hunks)} hunk(s)")
    
    for i, hunk in enumerate(hunks):
        print(f"\n  Hunk {i+1}:")
        print(f"    Old: lines {hunk.old_start}-{hunk.old_start + hunk.old_count - 1}")
        print(f"    New: lines {hunk.new_start}-{hunk.new_start + hunk.new_count - 1}")
        print(f"    Changes: {len(hunk.lines)} lines")
        
        for line in hunk.lines:
            symbol = {
                'added': '+',
                'removed': '-',
                'unchanged': ' '
            }.get(line.line_type.value, ' ')
            print(f"      {symbol} {line.content[:50]}...")
    
    # Get stats
    stats = service.get_change_stats(old_code, new_code)
    print(f"\n✓ Stats: +{stats['additions']} -{stats['deletions']}")
    
    # Check if has changes
    has_changes = service.has_changes(old_code, new_code)
    print(f"✓ Has changes: {has_changes}")
    
    assert len(hunks) > 0, "Should generate at least one hunk"
    assert stats['additions'] > 0, "Should have additions"
    assert has_changes, "Should detect changes"
    
    print("\n✅ All tests passed!")


def test_no_changes():
    """Test when there are no changes"""
    
    code = """a!localVariables(
  local!test: "hello"
)"""
    
    service = SailDiffService()
    
    hunks = service.generate_unified_diff(code, code)
    stats = service.get_change_stats(code, code)
    has_changes = service.has_changes(code, code)
    
    print(f"\n✓ No changes test:")
    print(f"  Hunks: {len(hunks)}")
    print(f"  Stats: +{stats['additions']} -{stats['deletions']}")
    print(f"  Has changes: {has_changes}")
    
    assert len(hunks) == 0, "Should have no hunks"
    assert stats['additions'] == 0, "Should have no additions"
    assert stats['deletions'] == 0, "Should have no deletions"
    assert not has_changes, "Should not detect changes"
    
    print("✅ No changes test passed!")


def test_none_handling():
    """Test handling of None values"""
    
    service = SailDiffService()
    
    # Test None old code
    hunks = service.generate_unified_diff(None, "new code")
    assert len(hunks) > 0, "Should handle None old code"
    
    # Test None new code
    hunks = service.generate_unified_diff("old code", None)
    assert len(hunks) > 0, "Should handle None new code"
    
    # Test both None
    hunks = service.generate_unified_diff(None, None)
    assert len(hunks) == 0, "Should handle both None"
    
    print("\n✅ None handling test passed!")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing SAIL Diff Service")
    print("=" * 60)
    
    test_sail_diff_basic()
    test_no_changes()
    test_none_handling()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
