"""
Test Configuration

Configuration for test environment.
"""
from pathlib import Path
import tempfile


class TestConfig:
    """Test configuration"""
    
    # Use temporary directory for tests
    BASE_DIR = Path(tempfile.mkdtemp(prefix='nexusgen_test_'))
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Testing
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # Directories
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'outputs'
    
    @classmethod
    def init_directories(cls):
        """Initialize test directories"""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
