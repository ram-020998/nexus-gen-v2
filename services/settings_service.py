"""
Settings Service

Provides business logic for settings operations including database cleanup,
backup, and restore functionality.
"""
import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from models import db, Request


def _get_settings_logger():
    """
    Get or create settings logger with file rotation.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger('settings_service')

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # File handler with rotation (10MB per file, keep 5 backups)
    log_file = log_dir / 'settings_service.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler (only INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Detailed formatter for file
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | '
        '%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Simpler formatter for console
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class SettingsService:
    """Service for managing application settings and database operations"""

    def __init__(self):
        """Initialize settings service with logger"""
        self.logger = _get_settings_logger()

    def cleanup_database(self) -> dict:
        """
        Clean up all database tables and uploaded files.

        Returns:
            dict: {
                'success': bool,
                'deleted_records': int,
                'deleted_files': int,
                'details': dict
            }
        """
        start_time = datetime.now()
        self.logger.info("Starting database cleanup operation")

        deleted_counts = {
            'requests': 0,
            'files': 0
        }

        try:
            # Delete all records from requests table
            self.logger.debug("Deleting records from requests table")
            deleted_counts['requests'] = Request.query.delete()

            # Commit database changes
            self.logger.debug("Committing database changes")
            db.session.commit()

            # Delete uploaded files
            self.logger.debug("Deleting uploaded files")
            deleted_counts['files'] = self._delete_uploaded_files()

            # Calculate totals
            total_records = deleted_counts['requests']

            elapsed = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"Database cleanup completed successfully: "
                f"deleted {total_records} records, "
                f"{deleted_counts['files']} files in {elapsed:.2f}s"
            )
            self.logger.debug(f"Cleanup details: {deleted_counts}")

            return {
                'success': True,
                'deleted_records': total_records,
                'deleted_files': deleted_counts['files'],
                'details': deleted_counts
            }
        except Exception as e:
            db.session.rollback()
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Database cleanup failed after {elapsed:.2f}s: {str(e)}",
                exc_info=True
            )
            raise Exception(f"Database cleanup failed: {str(e)}")

    def _delete_uploaded_files(self) -> int:
        """
        Delete uploaded files except .gitkeep files.

        Returns:
            int: Number of files deleted
        """
        upload_dirs = [
            'uploads'
        ]

        total_deleted = 0
        for upload_dir in upload_dirs:
            if os.path.exists(upload_dir):
                for file in os.listdir(upload_dir):
                    file_path = os.path.join(upload_dir, file)
                    if os.path.isfile(file_path) and file != '.gitkeep':
                        try:
                            os.remove(file_path)
                            total_deleted += 1
                            self.logger.debug(f"Deleted file: {file_path}")
                        except Exception as e:
                            # Log but don't fail the entire operation
                            self.logger.warning(
                                f"Failed to delete {file_path}: {str(e)}"
                            )

        self.logger.debug(
            f"Deleted {total_deleted} files from upload directories"
        )
        return total_deleted

    def backup_database(self) -> str:
        """
        Generate SQL export of the database.

        Returns:
            str: Path to the generated backup file

        Raises:
            Exception: If backup generation fails
        """
        start_time = datetime.now()
        self.logger.info("Starting database backup operation")

        # Ensure backup directory exists
        try:
            backup_dir = Path('outputs/backups')
            backup_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Backup directory: {backup_dir}")
        except OSError as e:
            self.logger.error(
                f"Failed to create backup directory: {str(e)}",
                exc_info=True
            )
            raise Exception(f"Failed to create backup directory: {str(e)}")

        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'nexusgen_backup_{timestamp}.sql'
        backup_path = backup_dir / filename
        self.logger.debug(f"Backup file: {filename}")

        # Database path
        db_path = 'instance/docflow.db'

        # Check if database exists
        if not os.path.exists(db_path):
            self.logger.error(f"Database not found at {db_path}")
            raise FileNotFoundError(f"Database not found at {db_path}")

        try:
            # Generate SQL dump using sqlite3 command
            self.logger.debug("Executing sqlite3 .dump command")
            with open(backup_path, 'w', encoding='utf-8') as f:
                subprocess.run(
                    ['sqlite3', db_path, '.dump'],
                    stdout=f,
                    check=True,
                    text=True,
                    stderr=subprocess.PIPE,
                    timeout=300  # 5 minute timeout
                )

            # Verify backup file was created and has content
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                self.logger.error("Backup file is empty or was not created")
                raise Exception("Backup file is empty or was not created")

            file_size = backup_path.stat().st_size
            elapsed = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"Database backup completed successfully: "
                f"{filename} ({file_size / 1024:.1f} KB) "
                f"in {elapsed:.2f}s"
            )

            return str(backup_path)

        except subprocess.TimeoutExpired:
            # Clean up partial file if it exists
            if backup_path.exists():
                backup_path.unlink()
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Backup generation timed out after {elapsed:.2f}s"
            )
            raise Exception(
                "Backup generation timed out. "
                "Database may be too large or locked."
            )

        except subprocess.CalledProcessError as e:
            # Clean up partial file if it exists
            if backup_path.exists():
                backup_path.unlink()
            error_msg = e.stderr if e.stderr else str(e)
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Backup generation failed after {elapsed:.2f}s: "
                f"{error_msg}",
                exc_info=True
            )
            raise Exception(f"Backup generation failed: {error_msg}")

        except FileNotFoundError:
            # sqlite3 command not found
            if backup_path.exists():
                backup_path.unlink()
            self.logger.error(
                "SQLite tools not available on the server",
                exc_info=True
            )
            raise Exception(
                "SQLite tools not available. "
                "Please ensure sqlite3 is installed on the server."
            )

        except IOError as e:
            # File I/O errors
            if backup_path.exists():
                backup_path.unlink()
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Failed to write backup file after {elapsed:.2f}s: "
                f"{str(e)}",
                exc_info=True
            )
            raise Exception(f"Failed to write backup file: {str(e)}")

        except Exception as e:
            # Clean up partial file if it exists
            if backup_path.exists():
                backup_path.unlink()
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Backup failed after {elapsed:.2f}s: {str(e)}",
                exc_info=True
            )
            raise Exception(f"Backup failed: {str(e)}")

    def restore_database(self, sql_file_path: str) -> dict:
        """
        Restore database from SQL backup file.

        Args:
            sql_file_path: Path to the SQL backup file

        Returns:
            dict: {
                'success': bool,
                'restored_records': int,
                'details': dict
            }

        Raises:
            Exception: If restore fails or SQL is invalid
        """
        start_time = datetime.now()
        self.logger.info(
            f"Starting database restore operation from {sql_file_path}"
        )

        # Validate file extension
        if not sql_file_path.endswith('.sql'):
            self.logger.error(
                f"Invalid file format: {sql_file_path} "
                "(only .sql files accepted)"
            )
            raise ValueError(
                "Invalid file format. Only .sql files are accepted."
            )

        # Check if file exists
        if not os.path.exists(sql_file_path):
            self.logger.error(f"SQL file not found: {sql_file_path}")
            raise FileNotFoundError(f"SQL file not found: {sql_file_path}")

        # Check file size (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        file_size = os.path.getsize(sql_file_path)
        self.logger.debug(
            f"SQL file size: {file_size / (1024*1024):.1f} MB"
        )

        if file_size > max_size:
            self.logger.error(
                f"File too large: {file_size / (1024*1024):.1f}MB "
                "(max 100MB)"
            )
            raise ValueError(
                f"File too large ({file_size / (1024*1024):.1f}MB). "
                f"Maximum size is 100MB."
            )

        # Validate SQL content
        self.logger.debug("Validating SQL file content")
        if not self._validate_sql_file(sql_file_path):
            self.logger.error(
                f"Invalid SQL file content: {sql_file_path}"
            )
            raise ValueError(
                "Invalid SQL file content. "
                "File must contain valid SQL statements."
            )

        db_path = 'instance/docflow.db'
        backup_path = None

        # Check if database exists
        if not os.path.exists(db_path):
            self.logger.error(f"Database not found at {db_path}")
            raise FileNotFoundError(f"Database not found at {db_path}")

        try:
            # Create a backup of current database before restore
            # This allows us to rollback if restore fails
            import tempfile
            backup_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'pre_restore_backup_{timestamp}.sql'
            backup_path = os.path.join(backup_dir, backup_filename)

            self.logger.debug(
                f"Creating pre-restore backup at {backup_path}"
            )

            # Backup current database
            try:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    subprocess.run(
                        ['sqlite3', db_path, '.dump'],
                        stdout=f,
                        check=True,
                        text=True,
                        stderr=subprocess.PIPE,
                        timeout=300  # 5 minute timeout
                    )
                self.logger.debug("Pre-restore backup created successfully")
            except subprocess.TimeoutExpired:
                self.logger.error("Pre-restore backup timed out")
                raise Exception(
                    "Pre-restore backup timed out. "
                    "Database may be too large or locked."
                )
            except FileNotFoundError:
                self.logger.error("SQLite tools not available")
                raise Exception(
                    "SQLite tools not available. "
                    "Please ensure sqlite3 is installed on the server."
                )

            # Drop all tables and recreate from SQL file
            # This is safer than trying to merge schemas
            self.logger.debug("Dropping all existing tables")
            self._drop_all_tables(db_path)

            # Execute SQL file to restore data
            self.logger.debug(f"Executing SQL file: {sql_file_path}")
            self._execute_sql_file(db_path, sql_file_path)

            # Count restored records
            self.logger.debug("Counting restored records")
            restored_counts = {
                'requests': Request.query.count()
            }

            total_restored = sum(restored_counts.values())
            elapsed = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"Database restore completed successfully: "
                f"restored {total_restored} records in {elapsed:.2f}s"
            )
            self.logger.debug(f"Restore details: {restored_counts}")

            # Clean up temporary backup on success
            if backup_path and os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                    self.logger.debug(
                        "Pre-restore backup cleaned up successfully"
                    )
                except Exception as e:
                    # Log but don't fail if cleanup fails
                    self.logger.warning(
                        f"Failed to clean up backup file {backup_path}: "
                        f"{str(e)}"
                    )

            return {
                'success': True,
                'restored_records': total_restored,
                'details': restored_counts
            }

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Database restore failed after {elapsed:.2f}s: {str(e)}",
                exc_info=True
            )

            # Rollback by restoring the pre-restore backup
            if backup_path and os.path.exists(backup_path):
                try:
                    self.logger.warning(
                        "Attempting to rollback database restore..."
                    )
                    # Drop all tables
                    self._drop_all_tables(db_path)

                    # Restore from backup
                    self._execute_sql_file(db_path, backup_path)

                    # Clean up backup file
                    os.remove(backup_path)
                    self.logger.info("Rollback successful")
                except Exception as rollback_error:
                    # If rollback fails, log but raise original error
                    self.logger.critical(
                        f"Rollback failed: {str(rollback_error)}",
                        exc_info=True
                    )
                    self.logger.critical(
                        f"Pre-restore backup saved at: {backup_path}"
                    )

            db.session.rollback()

            # Provide more specific error messages
            error_msg = str(e)
            if 'sqlite3' in error_msg.lower():
                error_msg = (
                    "SQLite tools not available. "
                    "Please ensure sqlite3 is installed on the server."
                )
            elif 'timeout' in error_msg.lower():
                error_msg = (
                    "Restore operation timed out. "
                    "Database may be too large or locked."
                )
            elif 'Invalid SQL' in error_msg:
                error_msg = (
                    "Invalid SQL file content. "
                    "Please ensure the file is a valid database backup."
                )

            raise Exception(f"Database restore failed: {error_msg}")

    def _validate_sql_file(self, file_path: str) -> bool:
        """
        Validate SQL file format and content.

        Args:
            file_path: Path to SQL file

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first 2000 characters to check for SQL keywords
                content = f.read(2000).upper()

                # Check for SQL keywords that should be present in a backup
                sql_keywords = ['CREATE', 'INSERT', 'TABLE', 'BEGIN']
                has_keywords = any(
                    keyword in content for keyword in sql_keywords
                )

                # Check for dangerous commands that should not be present
                dangerous_keywords = ['DROP DATABASE', 'DROP SCHEMA']
                has_dangerous = any(
                    keyword in content for keyword in dangerous_keywords
                )

                return has_keywords and not has_dangerous

        except Exception:
            return False

    def _drop_all_tables(self, db_path: str) -> None:
        """
        Drop all tables from the database.

        Args:
            db_path: Path to SQLite database

        Raises:
            Exception: If dropping tables fails
        """
        try:
            # Get list of all tables
            result = subprocess.run(
                ['sqlite3', db_path, '.tables'],
                capture_output=True,
                text=True,
                check=True
            )

            tables = result.stdout.split()

            # Drop each table
            for table in tables:
                subprocess.run(
                    ['sqlite3', db_path, f'DROP TABLE IF EXISTS {table};'],
                    capture_output=True,
                    text=True,
                    check=True
                )

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise Exception(f"Failed to drop tables: {error_msg}")

        except FileNotFoundError:
            raise Exception(
                "SQLite tools not available. "
                "Please ensure sqlite3 is installed."
            )

    def _execute_sql_file(self, db_path: str, sql_file_path: str) -> None:
        """
        Execute SQL file against database.

        Args:
            db_path: Path to SQLite database
            sql_file_path: Path to SQL file to execute

        Raises:
            Exception: If SQL execution fails
        """
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                subprocess.run(
                    ['sqlite3', db_path],
                    stdin=f,
                    check=True,
                    text=True,
                    capture_output=True,
                    timeout=300  # 5 minute timeout
                )

        except subprocess.TimeoutExpired:
            raise Exception(
                "SQL execution timed out. "
                "File may be too large or contain complex operations."
            )

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            # Check for common SQL errors
            if 'syntax error' in error_msg.lower():
                raise Exception(f"Invalid SQL syntax in file: {error_msg}")
            raise Exception(f"SQL execution failed: {error_msg}")

        except FileNotFoundError:
            raise Exception(
                "SQLite tools not available. "
                "Please ensure sqlite3 is installed on the server."
            )

        except IOError as e:
            raise Exception(f"Failed to read SQL file: {str(e)}")
