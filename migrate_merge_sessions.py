#!/usr/bin/env python3
"""
Migration Script for Merge Assistant Data Model Refactoring

This script handles:
1. Creating database backups
2. Migrating existing MergeSession data from JSON to normalized schema
3. Verifying migration completeness
4. Testing application with migrated data

Usage:
    python migrate_merge_sessions.py --backup          # Create backup only
    python migrate_merge_sessions.py --migrate         # Run migration
    python migrate_merge_sessions.py --verify          # Verify migration
    python migrate_merge_sessions.py --all             # Backup, migrate, and verify
"""

import os
import sys
import shutil
import argparse
import json
from datetime import datetime
from pathlib import Path

from app import create_app
from models import db, MergeSession, Package, AppianObject, Change, ChangeReview
from services.merge_assistant.migration_service import MigrationService, MigrationError


class MigrationRunner:
    """Handles the complete migration workflow"""
    
    def __init__(self):
        self.app = create_app()
        self.migration_service = MigrationService()
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self) -> Path:
        """
        Create a backup of the production database
        
        Returns:
            Path to the backup file
        """
        print("\n" + "="*80)
        print("STEP 1: Creating Database Backup")
        print("="*80)
        
        with self.app.app_context():
            # Get database path
            db_uri = self.app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri.startswith('sqlite:///'):
                db_path = Path(db_uri.replace('sqlite:///', ''))
                if not db_path.is_absolute():
                    db_path = Path('instance') / db_path
            else:
                print(f"❌ Unsupported database type: {db_uri}")
                sys.exit(1)
            
            if not db_path.exists():
                print(f"❌ Database file not found: {db_path}")
                sys.exit(1)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"docflow_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Copy database file
            print(f"📁 Source database: {db_path}")
            print(f"💾 Backup location: {backup_path}")
            print(f"📊 Database size: {db_path.stat().st_size / (1024*1024):.2f} MB")
            
            try:
                shutil.copy2(db_path, backup_path)
                print(f"✅ Backup created successfully")
                
                # Verify backup integrity
                if backup_path.exists() and backup_path.stat().st_size > 0:
                    print(f"✅ Backup integrity verified")
                    print(f"💾 Backup size: {backup_path.stat().st_size / (1024*1024):.2f} MB")
                else:
                    print(f"❌ Backup verification failed")
                    sys.exit(1)
                
                return backup_path
                
            except Exception as e:
                print(f"❌ Backup failed: {str(e)}")
                sys.exit(1)
    
    def get_session_stats(self) -> dict:
        """Get statistics about sessions in the database"""
        with self.app.app_context():
            total_sessions = MergeSession.query.count()
            migrated_sessions = db.session.query(MergeSession).join(
                Package, MergeSession.id == Package.session_id
            ).distinct().count()
            unmigrated_sessions = total_sessions - migrated_sessions
            
            return {
                'total': total_sessions,
                'migrated': migrated_sessions,
                'unmigrated': unmigrated_sessions
            }
    
    def migrate_all_sessions(self, skip_errors: bool = True) -> dict:
        """
        Migrate all unmigrated sessions
        
        Args:
            skip_errors: Continue on errors if True
            
        Returns:
            Migration statistics
        """
        print("\n" + "="*80)
        print("STEP 2: Migrating Sessions")
        print("="*80)
        
        with self.app.app_context():
            # Get session statistics
            stats = self.get_session_stats()
            
            print(f"\n📊 Session Statistics:")
            print(f"   Total sessions: {stats['total']}")
            print(f"   Already migrated: {stats['migrated']}")
            print(f"   Need migration: {stats['unmigrated']}")
            
            if stats['unmigrated'] == 0:
                print("\n✅ No sessions need migration")
                return {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'errors': []
                }
            
            print(f"\n🚀 Starting migration of {stats['unmigrated']} sessions...")
            print()
            
            # Get all unmigrated sessions
            sessions = MergeSession.query.all()
            migration_stats = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'errors': []
            }
            
            for i, session in enumerate(sessions, 1):
                # Check if already migrated
                if session.packages:
                    print(f"⏭️  [{i}/{len(sessions)}] Session {session.reference_id} already migrated, skipping")
                    migration_stats['skipped'] += 1
                    continue
                
                migration_stats['total'] += 1
                print(f"🔄 [{i}/{len(sessions)}] Migrating session {session.reference_id}...")
                
                try:
                    # Migrate session
                    success = self.migration_service.migrate_session(session.id)
                    
                    if success:
                        migration_stats['successful'] += 1
                        print(f"   ✅ Successfully migrated session {session.reference_id}")
                        
                        # Show migration details
                        packages = Package.query.filter_by(session_id=session.id).count()
                        objects = db.session.query(AppianObject).join(
                            Package, AppianObject.package_id == Package.id
                        ).filter(Package.session_id == session.id).count()
                        changes = Change.query.filter_by(session_id=session.id).count()
                        
                        print(f"      📦 Packages: {packages}")
                        print(f"      📄 Objects: {objects}")
                        print(f"      🔄 Changes: {changes}")
                    else:
                        migration_stats['failed'] += 1
                        print(f"   ❌ Failed to migrate session {session.reference_id}")
                        
                except Exception as e:
                    migration_stats['failed'] += 1
                    error_msg = f"Session {session.reference_id}: {str(e)}"
                    migration_stats['errors'].append(error_msg)
                    print(f"   ❌ Error: {str(e)}")
                    
                    if not skip_errors:
                        print("\n❌ Migration stopped due to error")
                        raise
                
                print()
            
            # Print summary
            print("="*80)
            print("Migration Summary")
            print("="*80)
            print(f"Total sessions processed: {migration_stats['total']}")
            print(f"✅ Successful: {migration_stats['successful']}")
            print(f"❌ Failed: {migration_stats['failed']}")
            print(f"⏭️  Skipped (already migrated): {migration_stats['skipped']}")
            
            if migration_stats['errors']:
                print(f"\n❌ Errors encountered:")
                for error in migration_stats['errors']:
                    print(f"   - {error}")
            
            return migration_stats
    
    def verify_all_sessions(self) -> dict:
        """
        Verify migration completeness for all sessions
        
        Returns:
            Verification statistics
        """
        print("\n" + "="*80)
        print("STEP 3: Verifying Migration Completeness")
        print("="*80)
        
        with self.app.app_context():
            sessions = MergeSession.query.all()
            
            if not sessions:
                print("\n⚠️  No sessions found in database")
                return {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'failures': []
                }
            
            print(f"\n🔍 Verifying {len(sessions)} sessions...")
            print()
            
            verification_stats = {
                'total': len(sessions),
                'passed': 0,
                'failed': 0,
                'failures': []
            }
            
            for i, session in enumerate(sessions, 1):
                print(f"🔍 [{i}/{len(sessions)}] Verifying session {session.reference_id}...")
                
                try:
                    # Verify session
                    results = self.migration_service.verify_migration(session.id)
                    
                    # Check if all verifications passed
                    all_passed = all(results.values())
                    
                    if all_passed:
                        verification_stats['passed'] += 1
                        print(f"   ✅ All checks passed")
                    else:
                        verification_stats['failed'] += 1
                        print(f"   ❌ Some checks failed:")
                        
                        failed_checks = [k for k, v in results.items() if not v]
                        for check in failed_checks:
                            print(f"      - {check}")
                        
                        verification_stats['failures'].append({
                            'session': session.reference_id,
                            'failed_checks': failed_checks
                        })
                    
                    # Show details
                    packages = Package.query.filter_by(session_id=session.id).count()
                    objects = db.session.query(AppianObject).join(
                        Package, AppianObject.package_id == Package.id
                    ).filter(Package.session_id == session.id).count()
                    changes = Change.query.filter_by(session_id=session.id).count()
                    reviews = ChangeReview.query.filter_by(session_id=session.id).count()
                    
                    print(f"      📦 Packages: {packages}")
                    print(f"      📄 Objects: {objects}")
                    print(f"      🔄 Changes: {changes}")
                    print(f"      📝 Reviews: {reviews}")
                    
                except Exception as e:
                    verification_stats['failed'] += 1
                    print(f"   ❌ Verification error: {str(e)}")
                    verification_stats['failures'].append({
                        'session': session.reference_id,
                        'error': str(e)
                    })
                
                print()
            
            # Print summary
            print("="*80)
            print("Verification Summary")
            print("="*80)
            print(f"Total sessions verified: {verification_stats['total']}")
            print(f"✅ Passed: {verification_stats['passed']}")
            print(f"❌ Failed: {verification_stats['failed']}")
            
            if verification_stats['failures']:
                print(f"\n❌ Failed verifications:")
                for failure in verification_stats['failures']:
                    print(f"   - {failure['session']}")
                    if 'failed_checks' in failure:
                        for check in failure['failed_checks']:
                            print(f"      • {check}")
                    if 'error' in failure:
                        print(f"      • Error: {failure['error']}")
            
            return verification_stats
    
    def test_application(self):
        """
        Test application functionality with migrated data
        
        This performs basic smoke tests to ensure the application works
        with the new schema.
        """
        print("\n" + "="*80)
        print("STEP 4: Testing Application with Migrated Data")
        print("="*80)
        
        with self.app.app_context():
            sessions = MergeSession.query.all()
            
            if not sessions:
                print("\n⚠️  No sessions found to test")
                return {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'errors': []
                }
            
            print(f"\n🧪 Running smoke tests on {len(sessions)} sessions...")
            print()
            
            test_results = {
                'total': len(sessions),
                'passed': 0,
                'failed': 0,
                'errors': []
            }
            
            for i, session in enumerate(sessions, 1):
                print(f"🧪 [{i}/{len(sessions)}] Testing session {session.reference_id}...")
                
                try:
                    # Test 1: Query packages
                    packages = Package.query.filter_by(session_id=session.id).all()
                    assert len(packages) == 3, f"Expected 3 packages, got {len(packages)}"
                    print(f"   ✅ Package query test passed")
                    
                    # Test 2: Query objects
                    for package in packages:
                        objects = AppianObject.query.filter_by(package_id=package.id).all()
                        assert len(objects) > 0, f"No objects found for package {package.id}"
                    print(f"   ✅ Object query test passed")
                    
                    # Test 3: Query changes with joins
                    changes = db.session.query(Change).filter_by(
                        session_id=session.id
                    ).order_by(Change.display_order).limit(10).all()
                    assert len(changes) > 0, "No changes found"
                    print(f"   ✅ Change query test passed")
                    
                    # Test 4: Filter by classification
                    conflict_changes = Change.query.filter_by(
                        session_id=session.id,
                        classification='CONFLICT'
                    ).count()
                    print(f"   ✅ Filter test passed (found {conflict_changes} conflicts)")
                    
                    # Test 5: Search by object name
                    search_results = Change.query.filter(
                        Change.session_id == session.id,
                        Change.object_name.like('%test%')
                    ).count()
                    print(f"   ✅ Search test passed (found {search_results} matches)")
                    
                    # Test 6: Review linkage
                    reviews = ChangeReview.query.filter_by(session_id=session.id).all()
                    for review in reviews[:5]:  # Test first 5
                        if review.change_id:
                            change = Change.query.get(review.change_id)
                            assert change is not None, f"Invalid change_id {review.change_id}"
                    print(f"   ✅ Review linkage test passed")
                    
                    test_results['passed'] += 1
                    print(f"   ✅ All tests passed for session {session.reference_id}")
                    
                except AssertionError as e:
                    test_results['failed'] += 1
                    error_msg = f"Session {session.reference_id}: {str(e)}"
                    test_results['errors'].append(error_msg)
                    print(f"   ❌ Test failed: {str(e)}")
                    
                except Exception as e:
                    test_results['failed'] += 1
                    error_msg = f"Session {session.reference_id}: {str(e)}"
                    test_results['errors'].append(error_msg)
                    print(f"   ❌ Error: {str(e)}")
                
                print()
            
            # Print summary
            print("="*80)
            print("Testing Summary")
            print("="*80)
            print(f"Total sessions tested: {test_results['total']}")
            print(f"✅ Passed: {test_results['passed']}")
            print(f"❌ Failed: {test_results['failed']}")
            
            if test_results['errors']:
                print(f"\n❌ Test errors:")
                for error in test_results['errors']:
                    print(f"   - {error}")
            
            return test_results


def main():
    """Main entry point for migration script"""
    parser = argparse.ArgumentParser(
        description='Migrate Merge Assistant data to normalized schema'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create database backup only'
    )
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Run migration only'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify migration only'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test application only'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all steps: backup, migrate, verify, and test'
    )
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop migration on first error (default: continue)'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any([args.backup, args.migrate, args.verify, args.test, args.all]):
        parser.print_help()
        sys.exit(0)
    
    runner = MigrationRunner()
    
    try:
        # Step 1: Backup
        if args.backup or args.all:
            backup_path = runner.create_backup()
            print(f"\n💾 Backup saved to: {backup_path}")
        
        # Step 2: Migrate
        if args.migrate or args.all:
            migration_stats = runner.migrate_all_sessions(
                skip_errors=not args.stop_on_error
            )
            
            if migration_stats['failed'] > 0:
                print(f"\n⚠️  Migration completed with {migration_stats['failed']} failures")
                if args.stop_on_error:
                    sys.exit(1)
        
        # Step 3: Verify
        if args.verify or args.all:
            verification_stats = runner.verify_all_sessions()
            
            if verification_stats['failed'] > 0:
                print(f"\n⚠️  Verification found {verification_stats['failed']} issues")
        
        # Step 4: Test
        if args.test or args.all:
            test_results = runner.test_application()
            
            if test_results['failed'] > 0:
                print(f"\n⚠️  Testing found {test_results['failed']} issues")
        
        print("\n" + "="*80)
        print("✅ Migration process completed")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
