"""
Base Test Class
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from app import create_app
from models import db
from test_config import TestConfig

class BaseTestCase(unittest.TestCase):
    """Base test case for all tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config.from_object(TestConfig)
        TestConfig.init_directories()
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        # Clean up test directories
        if TestConfig.BASE_DIR.exists():
            shutil.rmtree(TestConfig.BASE_DIR)
    
    def create_test_file(self, content="Test content", filename="test.txt"):
        """Create a test file for upload"""
        test_file = TestConfig.UPLOAD_FOLDER / filename
        test_file.write_text(content)
        return test_file
