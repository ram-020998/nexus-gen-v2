"""
Report Configuration Module

This module provides centralized configuration for merge assistant report generation,
including complexity calculation rules, time estimation values, and Excel formatting settings.

All thresholds and labels are defined as class attributes and can be easily modified
without changing core logic. Configuration values are validated on application startup.
"""
from typing import List, Dict, Any, Tuple, Set
import logging


class ReportConfig:
    """
    Configuration class for merge assistant report generation.
    
    This class centralizes all configuration values for:
    - Complexity calculation thresholds
    - Time estimation values
    - Excel column definitions
    - Object type classifications
    
    All values are class attributes that can be accessed directly.
    Configuration is validated on startup to ensure all values are valid.
    
    Usage:
        # Access configuration values
        low_threshold = ReportConfig.LINE_BASED_LOW_MAX
        time_estimate = ReportConfig.TIME_LOW_COMPLEXITY
        
        # Validate configuration
        is_valid, errors = ReportConfig.validate()
        if not is_valid:
            for error in errors:
                print(f"Configuration error: {error}")
    """
    
    # ============================================================================
    # Complexity Thresholds for Line-Based Objects
    # ============================================================================
    
    LINE_BASED_LOW_MAX: int = 20
    """Maximum line changes for Low complexity (line-based objects)"""
    
    LINE_BASED_MEDIUM_MAX: int = 60
    """Maximum line changes for Medium complexity (line-based objects)"""
    
    # Note: High complexity is anything above LINE_BASED_MEDIUM_MAX
    
    # ============================================================================
    # Complexity Thresholds for Process Models (Node Count)
    # ============================================================================
    
    PROCESS_MODEL_LOW_MAX: int = 3
    """Maximum node modifications for Low complexity (Process Models)"""
    
    PROCESS_MODEL_MEDIUM_MAX: int = 8
    """Maximum node modifications for Medium complexity (Process Models)"""
    
    # Note: High complexity is anything above PROCESS_MODEL_MEDIUM_MAX
    
    # ============================================================================
    # Time Estimates (in minutes)
    # ============================================================================
    
    TIME_LOW_COMPLEXITY: int = 20
    """Estimated time in minutes for Low complexity changes"""
    
    TIME_MEDIUM_COMPLEXITY: int = 40
    """Estimated time in minutes for Medium complexity changes"""
    
    TIME_HIGH_COMPLEXITY: int = 100
    """Estimated time in minutes for High complexity changes"""
    
    # ============================================================================
    # Complexity Labels
    # ============================================================================
    
    COMPLEXITY_LOW: str = "Low"
    """Label for Low complexity"""
    
    COMPLEXITY_MEDIUM: str = "Medium"
    """Label for Medium complexity"""
    
    COMPLEXITY_HIGH: str = "High"
    """Label for High complexity"""
    
    # ============================================================================
    # Object Type Classifications
    # ============================================================================
    
    LINE_BASED_TYPES: Set[str] = {"Interface", "Expression Rule", "Record Type"}
    """Object types that use line-based complexity calculation"""
    
    ALWAYS_LOW_TYPES: Set[str] = {"Constant"}
    """Object types that are always classified as Low complexity"""
    
    PROCESS_MODEL_TYPE: str = "Process Model"
    """Object type identifier for Process Models"""
    
    # ============================================================================
    # Excel Column Definitions
    # ============================================================================
    
    EXCEL_COLUMNS: List[str] = [
        "S. No",
        "Category",
        "Object Name",
        "Object UUID",
        "Change Description",
        "Actual SAIL Change",
        "Complexity",
        "Estimated Time",
        "Comments"
    ]
    """Excel report column headers in display order"""
    
    # ============================================================================
    # SAIL Code Settings
    # ============================================================================
    
    SAIL_CODE_MAX_LENGTH: int = 500
    """Maximum character length for SAIL code in Excel cells (truncated with ellipsis)"""
    
    SAIL_CODE_TRUNCATION_SUFFIX: str = "..."
    """Suffix appended to truncated SAIL code"""
    
    # ============================================================================
    # Time Display Settings
    # ============================================================================
    
    TIME_DISPLAY_HOUR_THRESHOLD: int = 60
    """Minimum minutes to display time in hours instead of minutes"""
    
    # ============================================================================
    # Validation Settings
    # ============================================================================
    
    MIN_THRESHOLD_VALUE: int = 1
    """Minimum allowed value for any threshold"""
    
    MAX_THRESHOLD_VALUE: int = 10000
    """Maximum allowed value for any threshold"""
    
    # ============================================================================
    # Default Values (Fallback)
    # ============================================================================
    
    DEFAULT_VALUES: Dict[str, Any] = {
        'LINE_BASED_LOW_MAX': 20,
        'LINE_BASED_MEDIUM_MAX': 60,
        'PROCESS_MODEL_LOW_MAX': 3,
        'PROCESS_MODEL_MEDIUM_MAX': 8,
        'TIME_LOW_COMPLEXITY': 20,
        'TIME_MEDIUM_COMPLEXITY': 40,
        'TIME_HIGH_COMPLEXITY': 100,
        'COMPLEXITY_LOW': 'Low',
        'COMPLEXITY_MEDIUM': 'Medium',
        'COMPLEXITY_HIGH': 'High',
        'SAIL_CODE_MAX_LENGTH': 500,
        'TIME_DISPLAY_HOUR_THRESHOLD': 60,
    }
    """Default configuration values used as fallback for invalid configuration"""
    
    @classmethod
    def validate(cls) -> Tuple[bool, List[str]]:
        """
        Validate all configuration values.
        
        Performs comprehensive validation of all configuration settings to ensure
        they are properly set and within acceptable ranges. This includes:
        - Threshold values are positive integers
        - Thresholds are in logical order (low < medium)
        - Time estimates are positive
        - Labels are non-empty strings
        - Object type sets are not empty
        - Column definitions are complete
        
        Returns:
            Tuple[bool, List[str]]: A tuple containing:
                - bool: True if all validations pass, False otherwise
                - List[str]: List of validation error messages (empty if valid)
        
        Example:
            >>> is_valid, errors = ReportConfig.validate()
            >>> if not is_valid:
            ...     for error in errors:
            ...         logging.error(f"Configuration error: {error}")
        """
        errors: List[str] = []
        
        # Validate line-based thresholds
        if not isinstance(cls.LINE_BASED_LOW_MAX, int) or cls.LINE_BASED_LOW_MAX < cls.MIN_THRESHOLD_VALUE:
            errors.append(
                f"LINE_BASED_LOW_MAX must be a positive integer >= {cls.MIN_THRESHOLD_VALUE}, "
                f"got {cls.LINE_BASED_LOW_MAX}"
            )
        
        if not isinstance(cls.LINE_BASED_MEDIUM_MAX, int) or cls.LINE_BASED_MEDIUM_MAX < cls.MIN_THRESHOLD_VALUE:
            errors.append(
                f"LINE_BASED_MEDIUM_MAX must be a positive integer >= {cls.MIN_THRESHOLD_VALUE}, "
                f"got {cls.LINE_BASED_MEDIUM_MAX}"
            )
        
        # Validate line-based threshold ordering
        if cls.LINE_BASED_LOW_MAX >= cls.LINE_BASED_MEDIUM_MAX:
            errors.append(
                f"LINE_BASED_LOW_MAX ({cls.LINE_BASED_LOW_MAX}) must be less than "
                f"LINE_BASED_MEDIUM_MAX ({cls.LINE_BASED_MEDIUM_MAX})"
            )
        
        # Validate process model thresholds
        if not isinstance(cls.PROCESS_MODEL_LOW_MAX, int) or cls.PROCESS_MODEL_LOW_MAX < cls.MIN_THRESHOLD_VALUE:
            errors.append(
                f"PROCESS_MODEL_LOW_MAX must be a positive integer >= {cls.MIN_THRESHOLD_VALUE}, "
                f"got {cls.PROCESS_MODEL_LOW_MAX}"
            )
        
        if not isinstance(cls.PROCESS_MODEL_MEDIUM_MAX, int) or cls.PROCESS_MODEL_MEDIUM_MAX < cls.MIN_THRESHOLD_VALUE:
            errors.append(
                f"PROCESS_MODEL_MEDIUM_MAX must be a positive integer >= {cls.MIN_THRESHOLD_VALUE}, "
                f"got {cls.PROCESS_MODEL_MEDIUM_MAX}"
            )
        
        # Validate process model threshold ordering
        if cls.PROCESS_MODEL_LOW_MAX >= cls.PROCESS_MODEL_MEDIUM_MAX:
            errors.append(
                f"PROCESS_MODEL_LOW_MAX ({cls.PROCESS_MODEL_LOW_MAX}) must be less than "
                f"PROCESS_MODEL_MEDIUM_MAX ({cls.PROCESS_MODEL_MEDIUM_MAX})"
            )
        
        # Validate time estimates
        if not isinstance(cls.TIME_LOW_COMPLEXITY, int) or cls.TIME_LOW_COMPLEXITY <= 0:
            errors.append(
                f"TIME_LOW_COMPLEXITY must be a positive integer, got {cls.TIME_LOW_COMPLEXITY}"
            )
        
        if not isinstance(cls.TIME_MEDIUM_COMPLEXITY, int) or cls.TIME_MEDIUM_COMPLEXITY <= 0:
            errors.append(
                f"TIME_MEDIUM_COMPLEXITY must be a positive integer, got {cls.TIME_MEDIUM_COMPLEXITY}"
            )
        
        if not isinstance(cls.TIME_HIGH_COMPLEXITY, int) or cls.TIME_HIGH_COMPLEXITY <= 0:
            errors.append(
                f"TIME_HIGH_COMPLEXITY must be a positive integer, got {cls.TIME_HIGH_COMPLEXITY}"
            )
        
        # Validate time estimate ordering (optional but logical)
        if cls.TIME_LOW_COMPLEXITY >= cls.TIME_MEDIUM_COMPLEXITY:
            errors.append(
                f"TIME_LOW_COMPLEXITY ({cls.TIME_LOW_COMPLEXITY}) should be less than "
                f"TIME_MEDIUM_COMPLEXITY ({cls.TIME_MEDIUM_COMPLEXITY})"
            )
        
        if cls.TIME_MEDIUM_COMPLEXITY >= cls.TIME_HIGH_COMPLEXITY:
            errors.append(
                f"TIME_MEDIUM_COMPLEXITY ({cls.TIME_MEDIUM_COMPLEXITY}) should be less than "
                f"TIME_HIGH_COMPLEXITY ({cls.TIME_HIGH_COMPLEXITY})"
            )
        
        # Validate complexity labels
        if not isinstance(cls.COMPLEXITY_LOW, str) or not cls.COMPLEXITY_LOW.strip():
            errors.append("COMPLEXITY_LOW must be a non-empty string")
        
        if not isinstance(cls.COMPLEXITY_MEDIUM, str) or not cls.COMPLEXITY_MEDIUM.strip():
            errors.append("COMPLEXITY_MEDIUM must be a non-empty string")
        
        if not isinstance(cls.COMPLEXITY_HIGH, str) or not cls.COMPLEXITY_HIGH.strip():
            errors.append("COMPLEXITY_HIGH must be a non-empty string")
        
        # Validate object type sets
        if not isinstance(cls.LINE_BASED_TYPES, set) or not cls.LINE_BASED_TYPES:
            errors.append("LINE_BASED_TYPES must be a non-empty set")
        
        if not isinstance(cls.ALWAYS_LOW_TYPES, set) or not cls.ALWAYS_LOW_TYPES:
            errors.append("ALWAYS_LOW_TYPES must be a non-empty set")
        
        if not isinstance(cls.PROCESS_MODEL_TYPE, str) or not cls.PROCESS_MODEL_TYPE.strip():
            errors.append("PROCESS_MODEL_TYPE must be a non-empty string")
        
        # Validate Excel columns
        if not isinstance(cls.EXCEL_COLUMNS, list) or not cls.EXCEL_COLUMNS:
            errors.append("EXCEL_COLUMNS must be a non-empty list")
        elif len(cls.EXCEL_COLUMNS) != 9:
            errors.append(f"EXCEL_COLUMNS must contain exactly 9 columns, got {len(cls.EXCEL_COLUMNS)}")
        
        # Validate SAIL code settings
        if not isinstance(cls.SAIL_CODE_MAX_LENGTH, int) or cls.SAIL_CODE_MAX_LENGTH <= 0:
            errors.append(
                f"SAIL_CODE_MAX_LENGTH must be a positive integer, got {cls.SAIL_CODE_MAX_LENGTH}"
            )
        
        if not isinstance(cls.SAIL_CODE_TRUNCATION_SUFFIX, str):
            errors.append("SAIL_CODE_TRUNCATION_SUFFIX must be a string")
        
        # Validate time display settings
        if not isinstance(cls.TIME_DISPLAY_HOUR_THRESHOLD, int) or cls.TIME_DISPLAY_HOUR_THRESHOLD <= 0:
            errors.append(
                f"TIME_DISPLAY_HOUR_THRESHOLD must be a positive integer, "
                f"got {cls.TIME_DISPLAY_HOUR_THRESHOLD}"
            )
        
        return len(errors) == 0, errors
    
    @classmethod
    def apply_defaults(cls) -> None:
        """
        Apply default values for any invalid configuration.
        
        This method resets all configuration values to their defaults from
        the DEFAULT_VALUES dictionary. It should be called when validation
        fails to ensure the application can continue with safe defaults.
        
        Example:
            >>> is_valid, errors = ReportConfig.validate()
            >>> if not is_valid:
            ...     logging.warning("Invalid configuration detected, applying defaults")
            ...     ReportConfig.apply_defaults()
        """
        for key, value in cls.DEFAULT_VALUES.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
        
        logging.info("Applied default configuration values for ReportConfig")
    
    @classmethod
    def get_complexity_label(cls, complexity_level: str) -> str:
        """
        Get the display label for a complexity level.
        
        Args:
            complexity_level: One of 'low', 'medium', or 'high' (case-insensitive)
        
        Returns:
            str: The configured label for the complexity level
        
        Raises:
            ValueError: If complexity_level is not recognized
        
        Example:
            >>> label = ReportConfig.get_complexity_label('low')
            >>> print(label)  # "Low"
        """
        level = complexity_level.lower()
        if level == 'low':
            return cls.COMPLEXITY_LOW
        elif level == 'medium':
            return cls.COMPLEXITY_MEDIUM
        elif level == 'high':
            return cls.COMPLEXITY_HIGH
        else:
            raise ValueError(f"Unknown complexity level: {complexity_level}")
    
    @classmethod
    def get_time_estimate(cls, complexity_level: str) -> int:
        """
        Get the time estimate in minutes for a complexity level.
        
        Args:
            complexity_level: One of 'low', 'medium', or 'high' (case-insensitive)
        
        Returns:
            int: Time estimate in minutes
        
        Raises:
            ValueError: If complexity_level is not recognized
        
        Example:
            >>> time = ReportConfig.get_time_estimate('medium')
            >>> print(time)  # 40
        """
        level = complexity_level.lower()
        if level == 'low':
            return cls.TIME_LOW_COMPLEXITY
        elif level == 'medium':
            return cls.TIME_MEDIUM_COMPLEXITY
        elif level == 'high':
            return cls.TIME_HIGH_COMPLEXITY
        else:
            raise ValueError(f"Unknown complexity level: {complexity_level}")
    
    @classmethod
    def is_line_based_type(cls, object_type: str) -> bool:
        """
        Check if an object type uses line-based complexity calculation.
        
        Args:
            object_type: The type of Appian object
        
        Returns:
            bool: True if the object type uses line-based complexity
        
        Example:
            >>> is_line_based = ReportConfig.is_line_based_type('Interface')
            >>> print(is_line_based)  # True
        """
        return object_type in cls.LINE_BASED_TYPES
    
    @classmethod
    def is_always_low_type(cls, object_type: str) -> bool:
        """
        Check if an object type is always Low complexity.
        
        Args:
            object_type: The type of Appian object
        
        Returns:
            bool: True if the object type is always Low complexity
        
        Example:
            >>> is_always_low = ReportConfig.is_always_low_type('Constant')
            >>> print(is_always_low)  # True
        """
        return object_type in cls.ALWAYS_LOW_TYPES
    
    @classmethod
    def is_process_model_type(cls, object_type: str) -> bool:
        """
        Check if an object type is a Process Model.
        
        Args:
            object_type: The type of Appian object
        
        Returns:
            bool: True if the object type is a Process Model
        
        Example:
            >>> is_pm = ReportConfig.is_process_model_type('Process Model')
            >>> print(is_pm)  # True
        """
        return object_type == cls.PROCESS_MODEL_TYPE
    
    @classmethod
    def log_configuration(cls) -> None:
        """
        Log current configuration values.
        
        Logs all configuration values at INFO level for debugging and
        verification purposes. Useful during application startup.
        
        Example:
            >>> ReportConfig.log_configuration()
        """
        logging.info("=" * 80)
        logging.info("Report Configuration Values")
        logging.info("=" * 80)
        logging.info(f"Line-Based Complexity Thresholds:")
        logging.info(f"  Low: 1-{cls.LINE_BASED_LOW_MAX} lines")
        logging.info(f"  Medium: {cls.LINE_BASED_LOW_MAX + 1}-{cls.LINE_BASED_MEDIUM_MAX} lines")
        logging.info(f"  High: >{cls.LINE_BASED_MEDIUM_MAX} lines")
        logging.info(f"")
        logging.info(f"Process Model Complexity Thresholds:")
        logging.info(f"  Low: 1-{cls.PROCESS_MODEL_LOW_MAX} nodes")
        logging.info(f"  Medium: {cls.PROCESS_MODEL_LOW_MAX + 1}-{cls.PROCESS_MODEL_MEDIUM_MAX} nodes")
        logging.info(f"  High: >{cls.PROCESS_MODEL_MEDIUM_MAX} nodes")
        logging.info(f"")
        logging.info(f"Time Estimates:")
        logging.info(f"  Low: {cls.TIME_LOW_COMPLEXITY} minutes")
        logging.info(f"  Medium: {cls.TIME_MEDIUM_COMPLEXITY} minutes")
        logging.info(f"  High: {cls.TIME_HIGH_COMPLEXITY} minutes")
        logging.info(f"")
        logging.info(f"Object Type Classifications:")
        logging.info(f"  Line-Based: {', '.join(cls.LINE_BASED_TYPES)}")
        logging.info(f"  Always Low: {', '.join(cls.ALWAYS_LOW_TYPES)}")
        logging.info(f"  Process Model: {cls.PROCESS_MODEL_TYPE}")
        logging.info(f"")
        logging.info(f"Excel Settings:")
        logging.info(f"  Columns: {len(cls.EXCEL_COLUMNS)}")
        logging.info(f"  SAIL Code Max Length: {cls.SAIL_CODE_MAX_LENGTH} characters")
        logging.info("=" * 80)
