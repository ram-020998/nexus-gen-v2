"""
Test Configuration
"""
import tempfile
from pathlib import Path


class TestConfig:
    # Test database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Test settings
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False

    # File settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'txt', 'md', 'docx', 'pdf'}

    # Test directories
    BASE_DIR = Path(tempfile.mkdtemp())
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'outputs'
    PROMPT_FOLDER = BASE_DIR / 'prompts'

    # AWS Bedrock Settings (test)
    AWS_REGION = 'us-east-1'
    BEDROCK_KB_ID = 'TEST_KB_ID'

    @classmethod
    def init_directories(cls):
        """Initialize test directories"""
        for folder in [cls.UPLOAD_FOLDER, cls.OUTPUT_FOLDER, cls.PROMPT_FOLDER]:
            folder.mkdir(parents=True, exist_ok=True)
