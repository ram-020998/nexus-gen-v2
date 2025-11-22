"""
Integration tests for merge assistant logging functionality

Tests that logging is properly integrated into the merge assistant workflow
and that all stage transitions, metrics, and user actions are logged.
"""
import pytest
import os
import tempfile
from pathlib import Path
from services.merge_assistant.logger import (
    create_merge_session_logger,
    MergeSessionLogger
)


class TestMergeSessionLogger:
    """Test the MergeSessionLogger class"""
    
    def test_logger_creation(self):
        """Test that logger can be created with session ID"""
        logger = create_merge_session_logger("MRG_001")
        
        assert logger is not None
        assert isinstance(logger, MergeSessionLogger)
        assert logger.session_id == "MRG_001"
        assert logger.request_id == "MRG_001"
    
    def test_log_upload(self):
        """Test logging package upload"""
        logger = create_merge_session_logger("MRG_TEST_001")
        
        # Should not raise exception
        logger.log_upload(
            "base_package.zip",
            "customized_package.zip",
            "new_vendor_package.zip"
        )
    
    def test_log_blueprint_generation(self):
        """Test logging blueprint generation stages"""
        logger = create_merge_session_logger("MRG_TEST_002")
        
        # Should not raise exceptions
        logger.log_blueprint_generation_start("base")
        logger.log_blueprint_generation_complete("base", 100, 2.5)
        logger.log_blueprint_generation_error("customized", "Test error")
    
    def test_log_comparison(self):
        """Test logging comparison stages"""
        logger = create_merge_session_logger("MRG_TEST_003")
        
        # Should not raise exceptions
        logger.log_comparison_start("vendor")
        logger.log_comparison_complete("vendor", 10, 20, 5)
        logger.log_comparison_start("customer")
        logger.log_comparison_complete("customer", 5, 15, 2)
    
    def test_log_classification(self):
        """Test logging classification stages"""
        logger = create_merge_session_logger("MRG_TEST_004")
        
        # Should not raise exceptions
        logger.log_classification_start()
        logger.log_classification_complete(50, 30, 10, 5)
    
    def test_log_ordering(self):
        """Test logging ordering stages"""
        logger = create_merge_session_logger("MRG_TEST_005")
        
        # Should not raise exceptions
        logger.log_ordering_start()
        logger.log_ordering_complete(95)
        logger.log_circular_dependency_detected("cycle: A -> B -> C -> A")
    
    def test_log_guidance_generation(self):
        """Test logging guidance generation"""
        logger = create_merge_session_logger("MRG_TEST_006")
        
        # Should not raise exceptions
        logger.log_guidance_generation_start()
        logger.log_guidance_generation_complete(95)
    
    def test_log_session_ready(self):
        """Test logging session ready"""
        logger = create_merge_session_logger("MRG_TEST_007")
        
        # Should not raise exception
        logger.log_session_ready(15)
    
    def test_log_workflow(self):
        """Test logging workflow stages"""
        logger = create_merge_session_logger("MRG_TEST_008")
        
        # Should not raise exceptions
        logger.log_workflow_start()
        logger.log_user_action(
            "reviewed",
            0,
            "TestInterface",
            "Interface",
            "NO_CONFLICT"
        )
        logger.log_workflow_complete(80, 15)
    
    def test_log_report(self):
        """Test logging report generation and export"""
        logger = create_merge_session_logger("MRG_TEST_009")
        
        # Should not raise exceptions
        logger.log_report_generation()
        logger.log_report_export("json")
        logger.log_report_export("pdf")
    
    def test_log_filter(self):
        """Test logging filter application"""
        logger = create_merge_session_logger("MRG_TEST_010")
        
        # Should not raise exception
        logger.log_filter_applied(
            classification="CONFLICT",
            object_type="Interface",
            review_status="pending",
            search_term="test",
            result_count=25
        )
    
    def test_log_error(self):
        """Test logging errors with context"""
        logger = create_merge_session_logger("MRG_TEST_011")
        
        # Should not raise exception
        logger.log_error(
            "blueprint_generation",
            "Test error message",
            {"package": "base", "file": "test.zip"}
        )
    
    def test_log_file_exists(self):
        """Test that log file is created"""
        # Create a logger and log something
        logger = create_merge_session_logger("MRG_TEST_012")
        logger.info("Test log message")
        
        # Check that log file exists
        log_file = Path("logs/appian_analyzer.log")
        assert log_file.exists(), "Log file should be created"
        
        # Check that log file contains our session ID
        with open(log_file, 'r') as f:
            content = f.read()
            assert "[MRG_TEST_012]" in content, \
                "Log file should contain session ID"


class TestLoggingIntegration:
    """Test logging integration with merge assistant services"""
    
    def test_logger_format(self):
        """Test that logger formats messages correctly"""
        logger = create_merge_session_logger("MRG_FORMAT_TEST")
        
        # Log a test message
        logger.info("Test message")
        
        # Read log file
        log_file = Path("logs/appian_analyzer.log")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        # Find our message
        test_line = None
        for line in reversed(lines):
            if "[MRG_FORMAT_TEST]" in line and "Test message" in line:
                test_line = line
                break
        
        assert test_line is not None, "Test message should be in log"
        assert "[MRG_FORMAT_TEST]" in test_line, \
            "Session ID should be in brackets"
        assert "Test message" in test_line, \
            "Message should be in log"
    
    def test_stage_logging_format(self):
        """Test that stage logging includes proper formatting"""
        logger = create_merge_session_logger("MRG_STAGE_TEST")
        
        # Log a stage
        logger.log_stage("Test Stage", {"key": "value"})
        
        # Read log file
        log_file = Path("logs/appian_analyzer.log")
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find our message
        test_line = None
        for line in reversed(lines):
            if "[MRG_STAGE_TEST]" in line and "Stage: Test Stage" in line:
                test_line = line
                break
        
        assert test_line is not None, "Stage message should be in log"
        assert "Stage: Test Stage" in test_line, \
            "Stage name should be in log"
        assert "key=value" in test_line, \
            "Stage details should be in log"
    
    def test_metrics_logging_format(self):
        """Test that metrics logging includes proper formatting"""
        logger = create_merge_session_logger("MRG_METRICS_TEST")
        
        # Log metrics
        logger.log_metrics({
            "total_changes": 100,
            "conflicts": 25,
            "no_conflict": 75
        })
        
        # Read log file
        log_file = Path("logs/appian_analyzer.log")
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find our message
        test_line = None
        for line in reversed(lines):
            if "[MRG_METRICS_TEST]" in line and "Metrics:" in line:
                test_line = line
                break
        
        assert test_line is not None, "Metrics message should be in log"
        assert "Metrics:" in test_line, "Metrics label should be in log"
        assert "total_changes=100" in test_line, \
            "Metric values should be in log"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
