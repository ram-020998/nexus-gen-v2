"""
Configuration package for NexusGen application.

This package contains configuration modules for various features.
"""

import sys
import importlib.util
from pathlib import Path

from .report_config import ReportConfig

# Import Config from parent config.py module
# Add parent directory to path to import from config.py
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import Config class from config.py file
config_file = parent_dir / 'config.py'
spec = importlib.util.spec_from_file_location('app_config', config_file)
app_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_config_module)
Config = app_config_module.Config

__all__ = ['ReportConfig', 'Config']
