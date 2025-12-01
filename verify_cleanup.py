#!/usr/bin/env python3
"""
Verification script to ensure all Appian Analyzer and Merge Assistant
components have been successfully removed.
"""

import os
import sys
from pathlib import Path

def check_removed_directories():
    """Check that removed directories no longer exist."""
    removed_dirs = [
        'services/comparison',
        'services/merge',
        'services/merge_assistant',
        'services/classification',
        'services/extraction',
        'repositories/comparison',
        'repositories/extraction',
        'templates/analyzer',
        'templates/merge_assistant',
        'controllers/analyzer_controller.py',
        'controllers/merge_assistant_controller.py',
        'controllers/new_merge_assistant_controller.py',
        'domain',
        'factories',
        'migrations',
        'schemas',
        'prompts',
        'unknown_objects',
        'examples',
        '.kiro/specs',
        'core/cache.py',
        'core/retry.py',
        'core/batch_processor.py',
        'core/transaction.py',
        'core/concurrency.py',
        'core/streaming.py',
        'core/query_cache.py',
        'core/query_profiler.py',
        'core/error_logging.py',
    ]
    
    print("Checking removed directories and files...")
    all_removed = True
    for path in removed_dirs:
        if os.path.exists(path):
            print(f"  ❌ STILL EXISTS: {path}")
            all_removed = False
        else:
            print(f"  ✅ Removed: {path}")
    
    return all_removed

def check_remaining_files():
    """Check that essential files still exist."""
    essential_files = [
        'app.py',
        'models.py',
        'config.py',
        'controllers/breakdown_controller.py',
        'controllers/verify_controller.py',
        'controllers/create_controller.py',
        'controllers/convert_controller.py',
        'controllers/chat_controller.py',
        'controllers/process_controller.py',
        'controllers/settings_controller.py',
        'services/request/request_service.py',
        'services/ai/bedrock_service.py',
        'services/ai/q_agent_service.py',
        'repositories/request_repository.py',
        'repositories/chat_session_repository.py',
        'templates/dashboard.html',
        'templates/base.html',
    ]
    
    print("\nChecking essential files...")
    all_exist = True
    for path in essential_files:
        if os.path.exists(path):
            print(f"  ✅ Exists: {path}")
        else:
            print(f"  ❌ MISSING: {path}")
            all_exist = False
    
    return all_exist

def check_imports():
    """Check that no files import removed modules."""
    print("\nChecking for problematic imports...")
    
    problematic_patterns = [
        'from services.comparison',
        'from services.merge',
        'from services.merge_assistant',
        'from repositories.comparison',
        'from repositories.merge',
        'from controllers.analyzer',
        'from controllers.merge_assistant',
        'import services.comparison',
        'import services.merge',
        'import services.merge_assistant',
    ]
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip virtual env and other non-code directories
        dirs[:] = [d for d in dirs if d not in ['.venv', '.git', '__pycache__', 'Backups', '.hypothesis', '.pytest_cache']]
        for file in files:
            if file.endswith('.py') and file != 'verify_cleanup.py':
                python_files.append(os.path.join(root, file))
    
    issues_found = False
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in problematic_patterns:
                    if pattern in content:
                        print(f"  ❌ Found '{pattern}' in {py_file}")
                        issues_found = True
        except Exception as e:
            print(f"  ⚠️  Could not read {py_file}: {e}")
    
    if not issues_found:
        print("  ✅ No problematic imports found")
    
    return not issues_found

def check_models():
    """Check that models.py only contains essential models."""
    print("\nChecking models.py...")
    
    try:
        with open('models.py', 'r') as f:
            content = f.read()
        
        # Should have these
        required_models = ['class Request', 'class ChatSession']
        # Should NOT have these
        removed_models = [
            'class ComparisonRequest',
            'class MergeSession',
            'class Package',
            'class Change',
            'class ObjectLookup',
            'class Interface',
            'class ExpressionRule',
        ]
        
        all_good = True
        for model in required_models:
            if model in content:
                print(f"  ✅ Found: {model}")
            else:
                print(f"  ❌ MISSING: {model}")
                all_good = False
        
        for model in removed_models:
            if model in content:
                print(f"  ❌ STILL EXISTS: {model}")
                all_good = False
            else:
                print(f"  ✅ Removed: {model}")
        
        return all_good
    except Exception as e:
        print(f"  ❌ Error reading models.py: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("CLEANUP VERIFICATION")
    print("=" * 60)
    
    results = {
        'Removed directories': check_removed_directories(),
        'Essential files': check_remaining_files(),
        'Import statements': check_imports(),
        'Database models': check_models(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All verification checks passed!")
        print("The cleanup was successful.")
        return 0
    else:
        print("\n⚠️  Some verification checks failed.")
        print("Please review the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
