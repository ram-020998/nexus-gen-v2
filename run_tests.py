#!/usr/bin/env python3
"""
Test Runner for NexusGen Application
Runs both unit tests and integration tests
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """Run unit tests (mocked tests)"""
    print("RUNNING UNIT TESTS")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    # Exclude integration tests
    filtered_suite = unittest.TestSuite()
    for test_group in suite:
        for test_case in test_group:
            if 'integration' not in test_case.__class__.__name__.lower():
                filtered_suite.addTest(test_case)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(filtered_suite)
    
    return result.wasSuccessful(), result.testsRun, len(result.failures), len(result.errors)


def run_integration_tests():
    """Run integration tests (actual Q CLI execution)"""
    print("\nRUNNING INTEGRATION TESTS")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('tests.test_q_agent_integration')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful(), result.testsRun, len(result.failures), len(result.errors)


def run_tests():
    """Run all tests"""
    # Run unit tests
    unit_success, unit_tests, unit_failures, unit_errors = run_unit_tests()
    
    # Run integration tests
    try:
        int_success, int_tests, int_failures, int_errors = run_integration_tests()
    except Exception as e:
        print(f"\nIntegration tests failed to run: {e}")
        int_success, int_tests, int_failures, int_errors = False, 0, 0, 1
    
    # Summary
    total_tests = unit_tests + int_tests
    total_failures = unit_failures + int_failures
    total_errors = unit_errors + int_errors
    
    print(f"\n{'=' * 50}")
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Unit Tests: {unit_tests} run, {unit_failures} failures, {unit_errors} errors")
    print(f"Integration Tests: {int_tests} run, {int_failures} failures, {int_errors} errors")
    print(f"Total Tests: {total_tests}")
    print(f"Total Failures: {total_failures}")
    print(f"Total Errors: {total_errors}")
    
    if unit_success and int_success:
        success_rate = 100.0
        print(f"Success rate: {success_rate}%")
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
