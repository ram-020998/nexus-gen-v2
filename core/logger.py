"""
Centralized Logging Configuration for NexusGen

This module provides a comprehensive logging setup with:
- File rotation to prevent disk space issues
- Separate log files for different components
- Structured log format with timestamps and context
- Console and file handlers
- Different log levels for development and production
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggerConfig:
    """
    Centralized logger configuration for the application.
    
    Provides methods to create and configure loggers with consistent
    formatting, file rotation, and appropriate log levels.
    """
    
    # Log directory
    LOG_DIR = Path(__file__).parent.parent / 'logs'
    
    # Log format
    DETAILED_FORMAT = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
    )
    
    SIMPLE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Default log level
    DEFAULT_LEVEL = logging.INFO
    
    # File rotation settings
    MAX_BYTES = 10 * 1024 * 1024  # 10MB per file
    BACKUP_COUNT = 5  # Keep 5 backup files
    
    @classmethod
    def setup(cls) -> None:
        """
        Initialize logging configuration for the entire application.
        
        This should be called once during application startup (in app.py).
        Sets up the root logger with console and file handlers.
        """
        # Ensure log directory exists
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(cls.DEFAULT_LEVEL)
        
        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter(cls.SIMPLE_FORMAT)
        )
        root_logger.addHandler(console_handler)
        
        # Add main application file handler
        main_log_file = cls.LOG_DIR / 'nexusgen.log'
        file_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=cls.MAX_BYTES,
            backupCount=cls.BACKUP_COUNT
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(cls.DETAILED_FORMAT)
        )
        root_logger.addHandler(file_handler)
        
        # Log startup message
        root_logger.info("=" * 80)
        root_logger.info("NexusGen Application Starting")
        root_logger.info("=" * 80)
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        log_file: Optional[str] = None,
        level: Optional[int] = None
    ) -> logging.Logger:
        """
        Get a configured logger instance.
        
        Args:
            name: Logger name (typically __name__ from calling module)
            log_file: Optional separate log file for this logger
            level: Optional log level (defaults to DEFAULT_LEVEL)
            
        Returns:
            Configured logger instance
            
        Example:
            >>> logger = LoggerConfig.get_logger(__name__)
            >>> logger.info("Processing started")
            
            >>> # With separate log file
            >>> merge_logger = LoggerConfig.get_logger(
            ...     'merge_assistant',
            ...     log_file='merge_assistant.log'
            ... )
        """
        logger = logging.getLogger(name)
        
        # Set level
        if level is not None:
            logger.setLevel(level)
        else:
            logger.setLevel(cls.DEFAULT_LEVEL)
        
        # Add separate file handler if specified
        if log_file:
            log_path = cls.LOG_DIR / log_file
            
            # Check if handler already exists
            handler_exists = any(
                isinstance(h, RotatingFileHandler) and h.baseFilename == str(log_path)
                for h in logger.handlers
            )
            
            if not handler_exists:
                file_handler = RotatingFileHandler(
                    log_path,
                    maxBytes=cls.MAX_BYTES,
                    backupCount=cls.BACKUP_COUNT
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(
                    logging.Formatter(cls.DETAILED_FORMAT)
                )
                logger.addHandler(file_handler)
        
        return logger
    
    @classmethod
    def get_merge_logger(cls) -> logging.Logger:
        """
        Get logger specifically for merge assistant operations.
        
        Returns:
            Logger configured for merge assistant with separate log file
            
        Example:
            >>> logger = LoggerConfig.get_merge_logger()
            >>> logger.info("Starting merge session")
        """
        return cls.get_logger(
            'merge_assistant',
            log_file='merge_assistant.log',
            level=logging.DEBUG
        )
    
    @classmethod
    def log_function_entry(
        cls,
        logger: logging.Logger,
        function_name: str,
        **kwargs
    ) -> None:
        """
        Log function entry with parameters.
        
        Args:
            logger: Logger instance
            function_name: Name of the function being entered
            **kwargs: Function parameters to log
            
        Example:
            >>> logger = LoggerConfig.get_logger(__name__)
            >>> LoggerConfig.log_function_entry(
            ...     logger,
            ...     'process_package',
            ...     package_id=123,
            ...     package_type='base'
            ... )
        """
        params = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        logger.debug(f"→ Entering {function_name}({params})")
    
    @classmethod
    def log_function_exit(
        cls,
        logger: logging.Logger,
        function_name: str,
        result: Optional[str] = None
    ) -> None:
        """
        Log function exit with optional result.
        
        Args:
            logger: Logger instance
            function_name: Name of the function being exited
            result: Optional result description
            
        Example:
            >>> logger = LoggerConfig.get_logger(__name__)
            >>> LoggerConfig.log_function_exit(
            ...     logger,
            ...     'process_package',
            ...     result='Processed 42 objects'
            ... )
        """
        if result:
            logger.debug(f"← Exiting {function_name}: {result}")
        else:
            logger.debug(f"← Exiting {function_name}")
    
    @classmethod
    def log_step(
        cls,
        logger: logging.Logger,
        step_number: int,
        total_steps: int,
        description: str
    ) -> None:
        """
        Log a workflow step with progress indicator.
        
        Args:
            logger: Logger instance
            step_number: Current step number
            total_steps: Total number of steps
            description: Step description
            
        Example:
            >>> logger = LoggerConfig.get_logger(__name__)
            >>> LoggerConfig.log_step(
            ...     logger,
            ...     step_number=3,
            ...     total_steps=8,
            ...     description='Extracting Package B'
            ... )
        """
        logger.info(f"Step {step_number}/{total_steps}: {description}")
    
    @classmethod
    def log_separator(cls, logger: logging.Logger, char: str = "=") -> None:
        """
        Log a visual separator line.
        
        Args:
            logger: Logger instance
            char: Character to use for separator (default: "=")
            
        Example:
            >>> logger = LoggerConfig.get_logger(__name__)
            >>> LoggerConfig.log_separator(logger)
        """
        logger.info(char * 80)
    
    @classmethod
    def log_error_with_context(
        cls,
        logger: logging.Logger,
        error: Exception,
        context: str,
        **kwargs
    ) -> None:
        """
        Log an error with contextual information.
        
        Args:
            logger: Logger instance
            error: Exception that occurred
            context: Description of what was being done when error occurred
            **kwargs: Additional context information
            
        Example:
            >>> logger = LoggerConfig.get_logger(__name__)
            >>> try:
            ...     process_package(package_id=123)
            ... except Exception as e:
            ...     LoggerConfig.log_error_with_context(
            ...         logger,
            ...         e,
            ...         'Processing package',
            ...         package_id=123,
            ...         package_type='base'
            ...     )
        """
        context_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        logger.error(
            f"Error during {context}: {str(error)} | Context: {context_str}",
            exc_info=True
        )
    
    @classmethod
    def log_performance(
        cls,
        logger: logging.Logger,
        operation: str,
        duration_seconds: float,
        **metrics
    ) -> None:
        """
        Log performance metrics for an operation.
        
        Args:
            logger: Logger instance
            operation: Name of the operation
            duration_seconds: Duration in seconds
            **metrics: Additional performance metrics
            
        Example:
            >>> logger = LoggerConfig.get_logger(__name__)
            >>> LoggerConfig.log_performance(
            ...     logger,
            ...     'Package Extraction',
            ...     duration_seconds=12.5,
            ...     objects_processed=150,
            ...     files_parsed=75
            ... )
        """
        metrics_str = ', '.join(f"{k}={v}" for k, v in metrics.items())
        logger.info(
            f"Performance: {operation} completed in {duration_seconds:.2f}s | "
            f"Metrics: {metrics_str}"
        )


# Convenience function for getting merge logger
def get_merge_logger() -> logging.Logger:
    """
    Convenience function to get merge assistant logger.
    
    Returns:
        Logger configured for merge assistant
        
    Example:
        >>> from core.logger import get_merge_logger
        >>> logger = get_merge_logger()
        >>> logger.info("Starting merge operation")
    """
    return LoggerConfig.get_merge_logger()
