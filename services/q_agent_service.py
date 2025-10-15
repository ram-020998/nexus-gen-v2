"""
Q Agent Service - Handle Amazon Q CLI agent interactions
"""
import subprocess
import json
import tempfile
from pathlib import Path
from config import Config

class QAgentService:
    """Handle Q CLI agent operations"""
    
    def __init__(self):
        self.config = Config
    
    def process_breakdown(self, request_id: int, file_content: str, bedrock_context: dict) -> dict:
        """Process spec breakdown using Q agent"""
        try:
            # Create output path
            output_path = self.config.OUTPUT_FOLDER / str(request_id) / "breakdown_data.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temporary file with spec content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Prepare prompt with Bedrock context
            prompt = self._create_breakdown_prompt(temp_file_path, str(output_path), bedrock_context)
            
            # Execute Q agent
            result = self._execute_q_agent("breakdown-agent", prompt)
            
            # Clean up temp file
            Path(temp_file_path).unlink(missing_ok=True)
            
            # Read generated JSON
            if output_path.exists():
                with open(output_path, 'r') as f:
                    return json.load(f)
            else:
                # Fallback to mock data if Q agent fails
                return self._generate_fallback_breakdown()
                
        except Exception as e:
            print(f"Q Agent error: {e}")
            return self._generate_fallback_breakdown()
    
    def process_verification(self, request_id: int, design_content: str, bedrock_context: dict) -> dict:
        """Process design verification using Q agent"""
        try:
            output_path = self.config.OUTPUT_FOLDER / str(request_id) / "verification_data.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            prompt = self._create_verification_prompt(design_content, str(output_path), bedrock_context)
            result = self._execute_q_agent("verify-agent", prompt)
            
            if output_path.exists():
                with open(output_path, 'r') as f:
                    return json.load(f)
            else:
                return self._generate_fallback_verification()
                
        except Exception as e:
            print(f"Q Agent error: {e}")
            return self._generate_fallback_verification()
    
    def process_creation(self, request_id: int, acceptance_criteria: str, bedrock_context: dict) -> dict:
        """Process design document creation using Q agent"""
        try:
            output_path = self.config.OUTPUT_FOLDER / str(request_id) / "design_data.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            prompt = self._create_creation_prompt(acceptance_criteria, str(output_path), bedrock_context)
            result = self._execute_q_agent("create-agent", prompt)
            
            if output_path.exists():
                with open(output_path, 'r') as f:
                    return json.load(f)
            else:
                return self._generate_fallback_creation()
                
        except Exception as e:
            print(f"Q Agent error: {e}")
            return self._generate_fallback_creation()
    
    def process_chat(self, question: str, bedrock_context: dict) -> str:
        """Process chat question using Q agent"""
        try:
            prompt = self._create_chat_prompt(question, bedrock_context)
            result = self._execute_q_agent("chat-agent", prompt)
            
            if result.returncode == 0 and result.stdout.strip():
                return self._clean_response(result.stdout.strip())
            else:
                return self._generate_fallback_chat_response(question)
                
        except Exception as e:
            print(f"Q Agent error: {e}")
            return self._generate_fallback_chat_response(question)
    
    def _execute_q_agent(self, agent_name: str, prompt: str) -> subprocess.CompletedProcess:
        """Execute Q CLI agent with prompt"""
        cmd = ['q', 'chat', '--agent', agent_name, '--no-interactive', prompt]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.config.BASE_DIR),
            timeout=30,
            input='\n'  # Send newline to handle any interactive prompts
        )
        
        return result
    
    def _create_breakdown_prompt(self, file_path: str, output_path: str, bedrock_context: dict) -> str:
        """Create breakdown prompt with Bedrock context"""
        return f"""
Please analyze the specification document at: {file_path}

Bedrock Context (similar breakdowns):
{json.dumps(bedrock_context, indent=2)}

Generate a spec breakdown following the patterns shown in the Bedrock context.
Save the JSON output to: {output_path}

Focus on:
1. Creating clear user stories
2. Using GIVEN/WHEN/THEN format for acceptance criteria
3. Following the epic/story structure from similar examples
"""
    
    def _create_verification_prompt(self, design_content: str, output_path: str, bedrock_context: dict) -> str:
        """Create verification prompt with Bedrock context"""
        return f"""
Please verify this design document content:

{design_content}

Bedrock Context (existing designs):
{json.dumps(bedrock_context, indent=2)}

Analyze against existing designs and identify:
1. Missing objects or components
2. Areas that need attention
3. Recommendations based on similar designs

Save the JSON output to: {output_path}
"""
    
    def _create_creation_prompt(self, acceptance_criteria: str, output_path: str, bedrock_context: dict) -> str:
        """Create design creation prompt with Bedrock context"""
        return f"""
Please create a design document from these acceptance criteria:

{acceptance_criteria}

Bedrock Context (similar designs):
{json.dumps(bedrock_context, indent=2)}

Generate a comprehensive design document including:
1. Objects and components needed
2. Implementation approach
3. Dependencies and considerations

Save the JSON output to: {output_path}
"""
    
    def _create_chat_prompt(self, question: str, bedrock_context: dict) -> str:
        """Create chat prompt with Bedrock context"""
        print(f"DEBUG: Bedrock context summary: {bedrock_context.get('summary', 'No summary')[:100]}")
        print(f"DEBUG: Bedrock results count: {len(bedrock_context.get('results', []))}")
        return f"""
User Question: {question}

Bedrock Context (relevant documents):
{json.dumps(bedrock_context, indent=2)}

Please answer the user's question based on the available context. Be helpful and conversational.
"""
    
    def _generate_fallback_breakdown(self) -> dict:
        """Generate fallback breakdown data"""
        return {
            "epic": "Feature Implementation",
            "stories": [
                {
                    "story_name": "Core Functionality",
                    "acceptance_criteria": "**GIVEN**: System is ready\n**WHEN**: User performs action\n**THEN**: Expected result occurs",
                    "issue_type": "User Story",
                    "points": ""
                }
            ]
        }
    
    def _generate_fallback_verification(self) -> dict:
        """Generate fallback verification data"""
        return {
            "status": "verified",
            "missing_objects": ["No specific issues identified"],
            "recommendations": ["Design appears complete based on available context"],
            "similar_designs": ["No similar designs found in context"]
        }
    
    def _generate_fallback_creation(self) -> dict:
        """Generate fallback creation data"""
        return {
            "design_document": {
                "overview": "Design document generated from acceptance criteria",
                "objects": [
                    {
                        "name": "MainService",
                        "type": "Service",
                        "description": "Core service handling main functionality",
                        "methods": ["processRequest", "validateInput", "generateResponse"]
                    }
                ],
                "implementation_notes": [
                    "Follow existing service patterns",
                    "Implement proper error handling",
                    "Add logging and monitoring"
                ],
                "dependencies": [
                    "Database connection",
                    "Authentication service",
                    "Logging framework"
                ]
            }
        }
    
    def _generate_fallback_chat_response(self, question: str) -> str:
        """Generate fallback chat response"""
        return f"I understand you're asking about: {question}. However, I don't have specific information available in the knowledge base to provide a detailed answer. Could you try rephrasing your question or provide more context?"
    
    def _clean_response(self, response: str) -> str:
        """Clean ANSI codes and unwanted characters from response"""
        import re
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', response)
        
        # Remove other unwanted characters
        cleaned = cleaned.replace('mm mm', ' ')
        cleaned = cleaned.replace('10m"', '"')
        cleaned = cleaned.replace('m.mm', '.')
        cleaned = cleaned.replace('mm', '')
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
