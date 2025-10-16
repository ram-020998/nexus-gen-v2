#!/usr/bin/env python3
"""
Quick Health Check Script for NexusGen Application
Run this to verify the application is healthy
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_health_checks():
    """Run essential health checks"""
    print("🏥 NexusGen Application Health Check")
    print("=" * 40)
    
    # Import and run health tests
    from tests.test_health import TestApplicationHealth, TestSystemResources
    
    # Create test suite with essential tests
    suite = unittest.TestSuite()
    
    # Add critical health tests
    suite.addTest(TestApplicationHealth('test_database_connectivity'))
    suite.addTest(TestApplicationHealth('test_all_routes_accessible'))
    suite.addTest(TestApplicationHealth('test_bedrock_service_integration'))
    suite.addTest(TestApplicationHealth('test_file_service_health'))
    suite.addTest(TestApplicationHealth('test_document_service_health'))
    suite.addTest(TestApplicationHealth('test_json_parsing_robustness'))
    suite.addTest(TestApplicationHealth('test_error_handling_robustness'))
    suite.addTest(TestApplicationHealth('test_configuration_health'))
    
    # Add system resource tests
    suite.addTest(TestSystemResources('test_memory_usage_reasonable'))
    suite.addTest(TestSystemResources('test_file_size_limits'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print health summary
    print("\n" + "=" * 40)
    if result.wasSuccessful():
        print("✅ HEALTH CHECK PASSED")
        print(f"All {result.testsRun} health checks completed successfully")
        print("Application is healthy and ready to use!")
    else:
        print("❌ HEALTH CHECK FAILED")
        print(f"Failed: {len(result.failures)} | Errors: {len(result.errors)} | Total: {result.testsRun}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print("=" * 40)
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_health_checks()
    sys.exit(exit_code)
