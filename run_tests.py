#!/usr/bin/env python3
"""
Test Runner for NexusGen Application
"""
import unittest
import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_tests(test_type='all'):
    """Run tests based on type"""
    print(f"🧪 Running {test_type.upper()} tests for NexusGen Application")
    print("=" * 60)
    
    # Discover tests based on type
    loader = unittest.TestLoader()
    start_dir = 'tests'
    
    if test_type == 'health':
        # Run only health checks
        suite = loader.loadTestsFromName('tests.test_health')
    elif test_type == 'unit':
        # Run unit tests (models, services)
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromName('tests.test_models'))
        suite.addTests(loader.loadTestsFromName('tests.test_services'))
    elif test_type == 'integration':
        # Run integration tests
        suite = loader.loadTestsFromName('tests.test_integration')
    elif test_type == 'controllers':
        # Run controller tests
        suite = loader.loadTestsFromName('tests.test_controllers')
    elif test_type == 'performance':
        # Run performance tests
        suite = loader.loadTestsFromName('tests.test_performance')
    else:
        # Run all tests
        suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with timing
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    end_time = time.time()
    
    # Print detailed summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(getattr(result, 'skipped', []))}")
    print(f"Duration: {end_time - start_time:.2f} seconds")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    
    # Show failures and errors
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"  {i}. {test}")
            # Show just the assertion error
            lines = traceback.split('\n')
            for line in lines:
                if 'AssertionError' in line:
                    print(f"     {line.strip()}")
                    break
    
    if result.errors:
        print(f"\n💥 ERRORS ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"  {i}. {test}")
            # Show the last exception line
            lines = traceback.split('\n')
            for line in reversed(lines):
                if line.strip() and not line.startswith(' '):
                    print(f"     {line.strip()}")
                    break
    
    # Health status
    print(f"\n{'='*60}")
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Application is healthy!")
    else:
        print("❌ SOME TESTS FAILED - Check issues above")
        if test_type == 'health':
            print("⚠️  Application may not be fully healthy")
    
    print(f"{'='*60}")
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

def main():
    """Main function with argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run NexusGen tests')
    parser.add_argument('--type', '-t', 
                       choices=['all', 'health', 'unit', 'integration', 'controllers', 'performance'],
                       default='all',
                       help='Type of tests to run (default: all)')
    
    args = parser.parse_args()
    
    exit_code = run_tests(args.type)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
