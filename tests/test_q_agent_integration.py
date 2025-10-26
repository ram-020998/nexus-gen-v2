"""
Q Agent Integration Tests - Test actual Q CLI agent execution
"""
import unittest
import subprocess
import json
import tempfile
import os
from pathlib import Path


class TestQAgentIntegration(unittest.TestCase):
    """Test actual Q CLI agent configurations and execution"""

    def setUp(self):
        """Set up test environment"""
        self.base_dir = Path(__file__).parent.parent
        self.agents_dir = self.base_dir / '.amazonq' / 'cli-agents'
        
    def test_agent_configurations_valid(self):
        """Test that all agent JSON configurations are valid"""
        agent_files = ['breakdown-agent.json', 'verify-agent.json', 'create-agent.json', 'chat-agent.json']
        
        for agent_file in agent_files:
            agent_path = self.agents_dir / agent_file
            self.assertTrue(agent_path.exists(), f"Agent file {agent_file} not found")
            
            # Test JSON is valid
            with open(agent_path, 'r') as f:
                try:
                    config = json.load(f)
                    self.assertIn('name', config, f"Agent {agent_file} missing 'name' field")
                    self.assertIn('prompt', config, f"Agent {agent_file} missing 'prompt' field")
                    self.assertIn('tools', config, f"Agent {agent_file} missing 'tools' field")
                except json.JSONDecodeError as e:
                    self.fail(f"Agent {agent_file} has invalid JSON: {e}")

    def test_q_cli_available(self):
        """Test that Q CLI is available and working"""
        result = subprocess.run(['q', '--version'], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, "Q CLI not available or not working")

    def test_breakdown_agent_execution(self):
        """Test breakdown agent actually executes and returns JSON"""
        # Create test document
        test_content = """
        User Story: As a user, I want to login to the system
        Acceptance Criteria:
        - User can enter username and password
        - System validates credentials
        - User is redirected to dashboard on success
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            # Test agent execution
            cmd = ['q', 'chat', '--agent', 'breakdown-agent', '--no-interactive', 
                   f'Analyze this document: {test_content}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Agent should execute without error
            self.assertEqual(result.returncode, 0, 
                           f"Breakdown agent failed with return code {result.returncode}")
            
            # Q CLI outputs to stderr, check for response content
            output = result.stderr
            self.assertTrue(output.strip(), "Breakdown agent returned no output")
            
            # Should contain some response from the agent
            self.assertIn("🤖", output, "Should contain agent response marker")
                
        finally:
            os.unlink(temp_path)

    def test_verify_agent_execution(self):
        """Test verify agent actually executes"""
        test_design = "Design Document: User authentication service with login validation"
        
        cmd = ['q', 'chat', '--agent', 'verify-agent', '--no-interactive', 
               f'Verify this design: {test_design}']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Agent should execute without error
        self.assertEqual(result.returncode, 0, 
                       f"Verify agent failed with return code {result.returncode}")
        
        # Q CLI outputs to stderr, check for response content
        output = result.stderr
        self.assertTrue(output.strip(), "Verify agent returned no output")
        
        # Should contain some response from the agent
        self.assertIn("🤖", output, "Should contain agent response marker")

    def test_create_agent_execution(self):
        """Test create agent actually executes"""
        test_criteria = "User should be able to login with username and password"
        
        cmd = ['q', 'chat', '--agent', 'create-agent', '--no-interactive', 
               f'Create design from: {test_criteria}']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Agent should execute without error
        self.assertEqual(result.returncode, 0, 
                       f"Create agent failed with return code {result.returncode}")
        
        # Q CLI outputs to stderr, check for response content
        output = result.stderr
        self.assertTrue(output.strip(), "Create agent returned no output")
        
        # Should contain some response from the agent
        self.assertIn("🤖", output, "Should contain agent response marker")

    def test_chat_agent_execution(self):
        """Test chat agent actually executes"""
        test_question = "What is document intelligence?"
        
        cmd = ['q', 'chat', '--agent', 'chat-agent', '--no-interactive', test_question]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Agent should execute without error
        self.assertEqual(result.returncode, 0, 
                       f"Chat agent failed with return code {result.returncode}")
        
        # Q CLI outputs to stderr, check for response content
        output = result.stderr
        self.assertTrue(output.strip(), "Chat agent returned no output")
        
        # Should contain some response from the agent
        self.assertIn("🤖", output, "Should contain agent response marker")

    def test_agent_tools_configuration(self):
        """Test that agents have correct tool configurations"""
        # Breakdown, verify, create agents should have fs_read
        for agent_name in ['breakdown-agent', 'verify-agent', 'create-agent']:
            agent_path = self.agents_dir / f'{agent_name}.json'
            with open(agent_path, 'r') as f:
                config = json.load(f)
                self.assertIn('fs_read', config['tools'], 
                            f"{agent_name} missing fs_read tool")
                self.assertIn('fs_read', config['allowedTools'], 
                            f"{agent_name} missing fs_read in allowedTools")
        
        # Chat agent should only have fs_read (no fs_write)
        chat_path = self.agents_dir / 'chat-agent.json'
        with open(chat_path, 'r') as f:
            config = json.load(f)
            self.assertIn('fs_read', config['tools'])
            self.assertNotIn('fs_write', config['tools'], 
                           "Chat agent should not have fs_write tool")


if __name__ == '__main__':
    unittest.main()
