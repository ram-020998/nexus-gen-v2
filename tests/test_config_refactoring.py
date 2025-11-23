"""
Tests for configuration refactoring (Task 17)

This test suite verifies that the refactored Config class maintains
backward compatibility while adding new validation and helper methods.
"""
import os
import pytest
from pathlib import Path
from config import Config


class TestConfigRefactoring:
    """Test suite for configuration refactoring"""
    
    def test_config_attributes_accessible(self):
        """Test that all original configuration attributes are accessible"""
        # Application settings
        assert hasattr(Config, 'SECRET_KEY')
        assert isinstance(Config.SECRET_KEY, str)
        
        # Database settings
        assert hasattr(Config, 'SQLALCHEMY_DATABASE_URI')
        assert isinstance(Config.SQLALCHEMY_DATABASE_URI, str)
        assert hasattr(Config, 'SQLALCHEMY_TRACK_MODIFICATIONS')
        assert isinstance(Config.SQLALCHEMY_TRACK_MODIFICATIONS, bool)
        
        # File settings
        assert hasattr(Config, 'MAX_CONTENT_LENGTH')
        assert isinstance(Config.MAX_CONTENT_LENGTH, int)
        assert hasattr(Config, 'ALLOWED_EXTENSIONS')
        assert isinstance(Config.ALLOWED_EXTENSIONS, set)
        
        # Directory settings
        assert hasattr(Config, 'BASE_DIR')
        assert isinstance(Config.BASE_DIR, Path)
        assert hasattr(Config, 'UPLOAD_FOLDER')
        assert isinstance(Config.UPLOAD_FOLDER, Path)
        assert hasattr(Config, 'OUTPUT_FOLDER')
        assert isinstance(Config.OUTPUT_FOLDER, Path)
        assert hasattr(Config, 'PROMPT_FOLDER')
        assert isinstance(Config.PROMPT_FOLDER, Path)
        
        # Merge assistant settings
        assert hasattr(Config, 'MERGE_UPLOAD_FOLDER')
        assert isinstance(Config.MERGE_UPLOAD_FOLDER, Path)
        assert hasattr(Config, 'MERGE_MAX_FILE_SIZE')
        assert isinstance(Config.MERGE_MAX_FILE_SIZE, int)
        assert hasattr(Config, 'MERGE_SESSION_TIMEOUT')
        assert isinstance(Config.MERGE_SESSION_TIMEOUT, int)
        
        # Data source settings
        assert hasattr(Config, 'DATA_SOURCE')
        assert isinstance(Config.DATA_SOURCE, str)
        
        # AWS settings
        assert hasattr(Config, 'AWS_REGION')
        assert isinstance(Config.AWS_REGION, str)
        assert hasattr(Config, 'BEDROCK_KB_ID')
        assert isinstance(Config.BEDROCK_KB_ID, str)
    
    def test_config_values_preserved(self):
        """Test that configuration values match expected defaults"""
        assert Config.SQLALCHEMY_DATABASE_URI == 'sqlite:///docflow.db'
        assert Config.SQLALCHEMY_TRACK_MODIFICATIONS is False
        assert Config.MAX_CONTENT_LENGTH == 200 * 1024 * 1024
        assert Config.ALLOWED_EXTENSIONS == {'txt', 'md', 'docx', 'pdf'}
        assert Config.MERGE_MAX_FILE_SIZE == 100 * 1024 * 1024
        assert Config.MERGE_SESSION_TIMEOUT == 24 * 60 * 60
        assert Config.DATA_SOURCE == 'BEDROCK'
    
    def test_environment_variable_handling(self):
        """Test that environment variables are handled correctly"""
        # Test default values
        assert Config.AWS_REGION == os.environ.get('AWS_REGION', 'us-east-1')
        assert Config.BEDROCK_KB_ID == os.environ.get('BEDROCK_KB_ID', 'WAQ6NJLGKN')
        
        # SECRET_KEY should use environment variable or default
        expected_secret = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        assert Config.SECRET_KEY == expected_secret
    
    def test_init_directories_method(self):
        """Test that init_directories method exists and is callable"""
        assert hasattr(Config, 'init_directories')
        assert callable(Config.init_directories)
        
        # Should not raise an exception
        Config.init_directories()
    
    def test_validate_method(self):
        """Test new validate method"""
        assert hasattr(Config, 'validate')
        assert callable(Config.validate)
        
        is_valid, errors = Config.validate()
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        
        # With default configuration, should be valid
        assert is_valid is True
        assert len(errors) == 0
    
    def test_get_env_var_method(self):
        """Test new get_env_var helper method"""
        assert hasattr(Config, 'get_env_var')
        assert callable(Config.get_env_var)
        
        # Test with existing environment variable
        result = Config.get_env_var('PATH')
        assert result is not None
        
        # Test with non-existing variable and default
        result = Config.get_env_var('NONEXISTENT_VAR', 'default_value')
        assert result == 'default_value'
    
    def test_is_production_method(self):
        """Test new is_production helper method"""
        assert hasattr(Config, 'is_production')
        assert callable(Config.is_production)
        
        result = Config.is_production()
        assert isinstance(result, bool)
        
        # With default dev secret key, should return False
        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            assert result is False
    
    def test_get_upload_path_method(self):
        """Test new get_upload_path helper method"""
        assert hasattr(Config, 'get_upload_path')
        assert callable(Config.get_upload_path)
        
        # Test regular upload
        path = Config.get_upload_path('test.txt')
        assert isinstance(path, Path)
        assert path.name == 'test.txt'
        assert path.parent == Config.UPLOAD_FOLDER
        
        # Test merge assistant upload
        merge_path = Config.get_upload_path('package.zip', merge_assistant=True)
        assert isinstance(merge_path, Path)
        assert merge_path.name == 'package.zip'
        assert merge_path.parent == Config.MERGE_UPLOAD_FOLDER
    
    def test_get_output_path_method(self):
        """Test new get_output_path helper method"""
        assert hasattr(Config, 'get_output_path')
        assert callable(Config.get_output_path)
        
        path = Config.get_output_path('report.pdf')
        assert isinstance(path, Path)
        assert path.name == 'report.pdf'
        assert path.parent == Config.OUTPUT_FOLDER
    
    def test_type_hints_present(self):
        """Test that type hints are present on class attributes"""
        # Check that annotations exist
        assert hasattr(Config, '__annotations__')
        annotations = Config.__annotations__
        
        # Verify key attributes have type hints
        assert 'SECRET_KEY' in annotations
        assert 'SQLALCHEMY_DATABASE_URI' in annotations
        assert 'SQLALCHEMY_TRACK_MODIFICATIONS' in annotations
        assert 'MAX_CONTENT_LENGTH' in annotations
        assert 'ALLOWED_EXTENSIONS' in annotations
        assert 'MERGE_MAX_FILE_SIZE' in annotations
        assert 'MERGE_SESSION_TIMEOUT' in annotations
        assert 'DATA_SOURCE' in annotations
        assert 'AWS_REGION' in annotations
        assert 'BEDROCK_KB_ID' in annotations
    
    def test_backward_compatibility_with_flask(self):
        """Test that Config works with Flask's from_object"""
        from flask import Flask
        
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Verify Flask can access Config attributes
        assert app.config['SECRET_KEY'] == Config.SECRET_KEY
        assert app.config['SQLALCHEMY_DATABASE_URI'] == Config.SQLALCHEMY_DATABASE_URI
        assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] == Config.SQLALCHEMY_TRACK_MODIFICATIONS
    
    def test_validation_with_invalid_data_source(self):
        """Test validation catches invalid data source"""
        # Temporarily change DATA_SOURCE
        original = Config.DATA_SOURCE
        try:
            Config.DATA_SOURCE = 'INVALID'
            is_valid, errors = Config.validate()
            
            assert is_valid is False
            assert len(errors) > 0
            assert any('DATA_SOURCE' in error for error in errors)
        finally:
            Config.DATA_SOURCE = original
    
    def test_validation_with_invalid_file_size(self):
        """Test validation catches invalid file sizes"""
        # Temporarily change MAX_CONTENT_LENGTH
        original = Config.MAX_CONTENT_LENGTH
        try:
            Config.MAX_CONTENT_LENGTH = -1
            is_valid, errors = Config.validate()
            
            assert is_valid is False
            assert len(errors) > 0
            assert any('MAX_CONTENT_LENGTH' in error for error in errors)
        finally:
            Config.MAX_CONTENT_LENGTH = original
    
    def test_docstrings_present(self):
        """Test that class and methods have docstrings"""
        assert Config.__doc__ is not None
        assert len(Config.__doc__.strip()) > 0
        
        assert Config.init_directories.__doc__ is not None
        assert Config.validate.__doc__ is not None
        assert Config.get_env_var.__doc__ is not None
        assert Config.is_production.__doc__ is not None
        assert Config.get_upload_path.__doc__ is not None
        assert Config.get_output_path.__doc__ is not None
