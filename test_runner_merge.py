#!/usr/bin/env python3
"""
Test runner specifically for merge assistant property tests
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == '__main__':
    # Load the specific test module
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('tests.test_merge_assistant_properties')
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("MERGE ASSISTANT PROPERTY TESTS SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ ALL PROPERTY TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME PROPERTY TESTS FAILED")
        sys.exit(1)
