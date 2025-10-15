"""
Application Configuration
"""
import os
from pathlib import Path

class Config:
    # Application Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///docflow.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'txt', 'md', 'docx', 'pdf'}
    
    # Directory Settings
    BASE_DIR = Path(__file__).parent
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'outputs'
    PROMPT_FOLDER = BASE_DIR / 'prompts'
    
    # Data Source Configuration
    DATA_SOURCE = 'BEDROCK'
    
    # AWS Bedrock Settings
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    BEDROCK_KB_ID = os.environ.get('BEDROCK_KB_ID', 'WAQ6NJLGKN')
    
    @classmethod
    def init_directories(cls):
        """Initialize required directories"""
        for folder in [cls.UPLOAD_FOLDER, cls.OUTPUT_FOLDER, cls.PROMPT_FOLDER]:
            folder.mkdir(parents=True, exist_ok=True)
