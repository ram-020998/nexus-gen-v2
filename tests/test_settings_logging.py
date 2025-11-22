"""
Test logging functionality for Settings Service

Verifies that all operations (cleanup, backup, restore) are properly logged
with timestamps and operation results.
"""
import os
import tempfile
from pathlib import Path
from tests.base_test import BaseTestCase
from services.settings_service import SettingsService
from models import db, Request, ComparisonRequest, MergeSession, ChangeReview


class TestSettingsLogging(BaseTestCase):
    """Test logging for settings operations"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.service = SettingsService()
        self.log_file = Path('logs/settings_service.log')

    def test_cleanup_operation_logging(self):
        """Test that cleanup operations are logged with timestamps and results"""
        # Create some test data
        request = Request(
            action_type='test',
            status='completed',
            filename='test.txt'
        )
        db.session.add(request)
        db.session.commit()

        # Get initial log size
        initial_size = self.log_file.stat().st_size if self.log_file.exists() else 0

        # Perform cleanup
        result = self.service.cleanup_database()

        # Verify cleanup succeeded
        self.assertTrue(result['success'])

        # Verify log file was written to
        self.assertTrue(self.log_file.exists())
        final_size = self.log_file.stat().st_size
        self.assertGreater(final_size, initial_size)

        # Read log content
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        # Verify log contains cleanup operation messages
        self.assertIn('Starting database cleanup operation', log_content)
        self.assertIn('Database cleanup completed successfully', log_content)
        self.assertIn('deleted', log_content)
        self.assertIn('records', log_content)

    def test_backup_operation_logging(self):
        """Test that backup operations are logged with timestamps and results"""
        # Get initial log size
        initial_size = self.log_file.stat().st_size if self.log_file.exists() else 0

        # Perform backup
        backup_path = self.service.backup_database()

        # Verify backup succeeded
        self.assertTrue(os.path.exists(backup_path))

        # Verify log file was written to
        self.assertTrue(self.log_file.exists())
        final_size = self.log_file.stat().st_size
        self.assertGreater(final_size, initial_size)

        # Read log content
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        # Verify log contains backup operation messages
        self.assertIn('Starting database backup operation', log_content)
        self.assertIn('Database backup completed successfully', log_content)
        self.assertIn('nexusgen_backup_', log_content)

        # Clean up backup file
        if os.path.exists(backup_path):
            os.remove(backup_path)

    def test_restore_operation_logging(self):
        """Test that restore operations are logged with timestamps and results"""
        # First create a backup
        backup_path = self.service.backup_database()

        # Get initial log size
        initial_size = self.log_file.stat().st_size if self.log_file.exists() else 0

        # Perform restore
        result = self.service.restore_database(backup_path)

        # Verify restore succeeded
        self.assertTrue(result['success'])

        # Verify log file was written to
        self.assertTrue(self.log_file.exists())
        final_size = self.log_file.stat().st_size
        self.assertGreater(final_size, initial_size)

        # Read log content
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        # Verify log contains restore operation messages
        self.assertIn('Starting database restore operation', log_content)
        self.assertIn('Database restore completed successfully', log_content)
        self.assertIn('restored', log_content)
        self.assertIn('records', log_content)

        # Clean up backup file
        if os.path.exists(backup_path):
            os.remove(backup_path)

    def test_error_logging(self):
        """Test that errors are logged with proper error messages"""
        # Get initial log size
        initial_size = self.log_file.stat().st_size if self.log_file.exists() else 0

        # Try to restore from non-existent file
        try:
            self.service.restore_database('/nonexistent/file.sql')
            self.fail("Should have raised FileNotFoundError")
        except FileNotFoundError:
            pass

        # Verify log file was written to
        self.assertTrue(self.log_file.exists())
        final_size = self.log_file.stat().st_size
        self.assertGreater(final_size, initial_size)

        # Read log content
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        # Verify log contains error messages
        self.assertIn('SQL file not found', log_content)

    def test_log_file_rotation(self):
        """Test that log file rotation is configured"""
        # Verify logger has rotating file handler
        logger = self.service.logger
        
        # Check that logger has handlers
        self.assertGreater(len(logger.handlers), 0)
        
        # Check that at least one handler is a RotatingFileHandler
        from logging.handlers import RotatingFileHandler
        has_rotating_handler = any(
            isinstance(h, RotatingFileHandler) 
            for h in logger.handlers
        )
        self.assertTrue(has_rotating_handler)

    def test_log_timestamps(self):
        """Test that log entries include timestamps"""
        # Perform an operation
        self.service.cleanup_database()

        # Read log content
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        # Verify log contains timestamp format (YYYY-MM-DD HH:MM:SS)
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        matches = re.findall(timestamp_pattern, log_content)
        
        # Should have at least one timestamp
        self.assertGreater(len(matches), 0)
