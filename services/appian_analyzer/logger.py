"""
Logging configuration for Appian Analyzer
Provides structured logging with file rotation and request tracking
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


class AppianAnalyzerLogger:
    """
    Centralized logger for Appian Analyzer with request tracking
    """
    
    def __init__(self, name='appian_analyzer'):
        """Initialize logger with file and console handlers"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # File handler with rotation (10MB per file, keep 5 backups)
        log_file = log_dir / 'appian_analyzer.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler (only INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Detailed formatter for file
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Simpler formatter for console
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """Get the configured logger instance"""
        return self.logger


class RequestLogger:
    """
    Context-aware logger for tracking individual comparison requests
    Automatically adds request ID to all log messages
    """
    
    def __init__(self, request_id, logger=None):
        """
        Initialize request logger
        
        Args:
            request_id: Unique identifier for the request (e.g., "CMP_007")
            logger: Base logger instance (creates new if not provided)
        """
        self.request_id = request_id
        self.logger = logger or AppianAnalyzerLogger().get_logger()
        self.start_time = datetime.now()
    
    def _format_message(self, message):
        """Add request ID prefix to message"""
        return f"[{self.request_id}] {message}"
    
    def debug(self, message, **kwargs):
        """Log debug message"""
        self.logger.debug(self._format_message(message), **kwargs)
    
    def info(self, message, **kwargs):
        """Log info message"""
        self.logger.info(self._format_message(message), **kwargs)
    
    def warning(self, message, **kwargs):
        """Log warning message"""
        self.logger.warning(self._format_message(message), **kwargs)
    
    def error(self, message, exc_info=False, **kwargs):
        """Log error message with optional exception info"""
        self.logger.error(self._format_message(message), exc_info=exc_info, **kwargs)
    
    def critical(self, message, exc_info=False, **kwargs):
        """Log critical message with optional exception info"""
        self.logger.critical(self._format_message(message), exc_info=exc_info, **kwargs)
    
    def log_stage(self, stage_name, details=None):
        """
        Log a processing stage with optional details
        
        Args:
            stage_name: Name of the processing stage
            details: Optional dictionary of additional details
        """
        message = f"Stage: {stage_name}"
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" | {detail_str}"
        self.info(message)
    
    def log_metrics(self, metrics):
        """
        Log performance metrics
        
        Args:
            metrics: Dictionary of metric name -> value
        """
        metric_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
        self.info(f"Metrics: {metric_str}")
    
    def log_completion(self, status='success', **kwargs):
        """
        Log request completion with elapsed time
        
        Args:
            status: Completion status (success/error/warning)
            **kwargs: Additional completion details
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()
        details = {
            'status': status,
            'elapsed_time': f"{elapsed:.2f}s",
            **kwargs
        }
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        self.info(f"Completed: {detail_str}")


# Global logger instance
_global_logger = None


def get_logger():
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AppianAnalyzerLogger().get_logger()
    return _global_logger


def create_request_logger(request_id):
    """
    Create a request-specific logger
    
    Args:
        request_id: Unique identifier for the request
    
    Returns:
        RequestLogger instance
    """
    return RequestLogger(request_id, get_logger())
