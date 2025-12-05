"""
Application Configuration

This module provides centralized configuration management for the NexusGen application.
All configuration values are defined as class attributes with type hints and validation.
Environment variables are handled consistently with sensible defaults.
"""
import os
from pathlib import Path
from typing import Set, Optional, ClassVar


class Config:
    """
    Application configuration class.
    
    This class centralizes all application settings including database configuration,
    file handling, directory paths, and external service settings. All configuration
    values are class attributes that can be accessed directly (e.g., Config.SECRET_KEY).
    
    Environment Variables:
        SECRET_KEY: Flask secret key for session management (default: 'dev-secret-key-change-in-production')
        AWS_REGION: AWS region for Bedrock services (default: 'us-east-1')
        BEDROCK_KB_ID: Bedrock knowledge base ID (default: 'WAQ6NJLGKN')
    
    Usage:
        # Access configuration values
        secret = Config.SECRET_KEY
        upload_dir = Config.UPLOAD_FOLDER
        
        # Initialize directories
        Config.init_directories()
        
        # Validate configuration
        is_valid, errors = Config.validate()
    """
    
    # Application Settings
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    """Flask secret key for session management and security"""

    # Database Configuration
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///docflow.db'
    """SQLAlchemy database connection URI"""
    
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    """Disable SQLAlchemy modification tracking for performance"""
    
    # Connection Pooling Settings (Requirement 11.5)
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        'pool_size': 10,  # Number of connections to maintain in the pool
        'pool_recycle': 3600,  # Recycle connections after 1 hour
        'pool_pre_ping': True,  # Verify connections before using them
        'max_overflow': 20,  # Maximum number of connections that can be created beyond pool_size
        'pool_timeout': 30,  # Timeout for getting a connection from the pool
    }
    """SQLAlchemy engine options for connection pooling and performance"""

    # File Upload Settings
    MAX_CONTENT_LENGTH: int = 200 * 1024 * 1024  # 200MB (to accommodate large Appian packages)
    """Maximum allowed file upload size in bytes (200MB)"""
    
    ALLOWED_EXTENSIONS: Set[str] = {'txt', 'md', 'docx', 'pdf'}
    """Set of allowed file extensions for uploads"""

    # Directory Settings
    BASE_DIR: ClassVar[Path] = Path(__file__).parent
    """Base directory of the application"""
    
    UPLOAD_FOLDER: ClassVar[Path] = BASE_DIR / 'uploads'
    """Directory for temporary file uploads"""
    
    OUTPUT_FOLDER: ClassVar[Path] = BASE_DIR / 'outputs'
    """Directory for generated output files"""
    
    PROMPT_FOLDER: ClassVar[Path] = BASE_DIR / 'prompts'
    """Directory for AI prompt templates"""
    

    
    MERGE_MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB for Appian packages
    """Maximum file size for merge assistant uploads in bytes (100MB)"""
    
    MERGE_SESSION_TIMEOUT: int = 24 * 60 * 60  # 24 hours in seconds
    """Merge session timeout in seconds (24 hours)"""

    # Data Source Configuration
    DATA_SOURCE: str = 'BEDROCK'
    """Primary data source for AI operations (BEDROCK or other)"""

    # AWS Bedrock Settings
    AWS_REGION: str = os.environ.get('AWS_REGION', 'us-east-1')
    """AWS region for Bedrock services"""
    
    BEDROCK_KB_ID: str = os.environ.get('BEDROCK_KB_ID', 'WAQ6NJLGKN')
    """Bedrock knowledge base identifier"""

    @classmethod
    def init_directories(cls) -> None:
        """
        Initialize required directories.
        
        Creates all necessary directories for file uploads, outputs, and prompts
        if they don't already exist. Uses parents=True to create parent directories
        and exist_ok=True to avoid errors if directories already exist.
        
        Raises:
            OSError: If directory creation fails due to permissions or other OS errors
        """
        for folder in [cls.UPLOAD_FOLDER, cls.OUTPUT_FOLDER, cls.PROMPT_FOLDER]:
            folder.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate configuration values.
        
        Performs comprehensive validation of all configuration settings to ensure
        they are properly set and within acceptable ranges. This includes checking
        for required environment variables, validating file sizes, and ensuring
        directory paths are valid.
        
        Returns:
            tuple[bool, list[str]]: A tuple containing:
                - bool: True if all validations pass, False otherwise
                - list[str]: List of validation error messages (empty if valid)
        
        Example:
            >>> is_valid, errors = Config.validate()
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"Configuration error: {error}")
        """
        errors: list[str] = []
        
        # Validate SECRET_KEY
        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY is not set")
        elif cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            # Warning, not an error - this is acceptable for development
            pass
        
        # Validate database URI
        if not cls.SQLALCHEMY_DATABASE_URI:
            errors.append("SQLALCHEMY_DATABASE_URI is not set")
        
        # Validate file size limits
        if cls.MAX_CONTENT_LENGTH <= 0:
            errors.append("MAX_CONTENT_LENGTH must be positive")
        
        if cls.MERGE_MAX_FILE_SIZE <= 0:
            errors.append("MERGE_MAX_FILE_SIZE must be positive")
        
        # Validate timeout
        if cls.MERGE_SESSION_TIMEOUT <= 0:
            errors.append("MERGE_SESSION_TIMEOUT must be positive")
        
        # Validate allowed extensions
        if not cls.ALLOWED_EXTENSIONS:
            errors.append("ALLOWED_EXTENSIONS cannot be empty")
        
        # Validate data source
        valid_data_sources = {'BEDROCK', 'LOCAL', 'MOCK'}
        if cls.DATA_SOURCE not in valid_data_sources:
            errors.append(f"DATA_SOURCE must be one of {valid_data_sources}, got '{cls.DATA_SOURCE}'")
        
        # Validate AWS settings if using BEDROCK
        if cls.DATA_SOURCE == 'BEDROCK':
            if not cls.AWS_REGION:
                errors.append("AWS_REGION is required when DATA_SOURCE is BEDROCK")
            if not cls.BEDROCK_KB_ID:
                errors.append("BEDROCK_KB_ID is required when DATA_SOURCE is BEDROCK")
        
        # Validate directory paths
        if not cls.BASE_DIR.exists():
            errors.append(f"BASE_DIR does not exist: {cls.BASE_DIR}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_env_var(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable with optional default.
        
        Provides a consistent interface for accessing environment variables
        throughout the application. This method is provided for consistency
        but direct os.environ.get() calls are also acceptable.
        
        Args:
            key: Environment variable name
            default: Default value if environment variable is not set
        
        Returns:
            str or None: Environment variable value or default
        
        Example:
            >>> api_key = Config.get_env_var('API_KEY', 'default-key')
        """
        return os.environ.get(key, default)
    
    @classmethod
    def is_production(cls) -> bool:
        """
        Check if running in production environment.
        
        Determines if the application is running in production mode based on
        the SECRET_KEY value. In production, SECRET_KEY should be set to a
        secure value different from the development default.
        
        Returns:
            bool: True if running in production, False otherwise
        
        Example:
            >>> if Config.is_production():
            ...     # Use production settings
            ...     pass
        """
        return cls.SECRET_KEY != 'dev-secret-key-change-in-production'
    
    @classmethod
    def get_upload_path(cls, filename: str) -> Path:
        """
        Get full path for uploaded file.
        
        Constructs the full filesystem path for an uploaded file.
        
        Args:
            filename: Name of the uploaded file
        
        Returns:
            Path: Full path to the uploaded file
        
        Example:
            >>> path = Config.get_upload_path('document.txt')
        """
        return cls.UPLOAD_FOLDER / filename
    
    @classmethod
    def get_output_path(cls, filename: str) -> Path:
        """
        Get full path for output file.
        
        Constructs the full filesystem path for a generated output file.
        
        Args:
            filename: Name of the output file
        
        Returns:
            Path: Full path to the output file
        
        Example:
            >>> output_path = Config.get_output_path('report.pdf')
        """
        return cls.OUTPUT_FOLDER / filename
