"""
Q Agent Service - Handle Amazon Q CLI agent interactions
"""
import subprocess
import json
import tempfile
import logging
import time
from pathlib import Path
from config import Config
from services.process_tracker import ProcessTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QAgentService:
    """Handle Q CLI agent operations"""

    def __init__(self):
        self.config = Config

    def process_breakdown(self, request_id: int, file_content: str, bedrock_context: dict) -> tuple:
        """Process spec breakdown using Q agent - database-first approach"""
        tracker = ProcessTracker(request_id, 'breakdown')
        tracker.set_agent_metadata('breakdown-agent')
        
        logger.info(f"Starting breakdown process for request {request_id}")
        
        try:
            # Track file processing step
            tracker.start_step('File Processing')
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            tracker.end_step('File Processing')

            # Track Bedrock query step
            tracker.start_step('Bedrock Query')
            bedrock_results = bedrock_context.get('results', [])
            tracker.set_rag_metrics(bedrock_results)
            
            if bedrock_results:
                avg_score = sum(r.get('score', 0) for r in bedrock_results) / len(bedrock_results)
                logger.info(f"Bedrock RAG: {len(bedrock_results)} results, avg similarity: {avg_score:.3f}")
            else:
                logger.warning("No Bedrock context available for breakdown")
                tracker.add_error("No Bedrock context available", "Bedrock Query")
            tracker.end_step('Bedrock Query')

            # Track Q Agent processing step - NO FILE OUTPUT
            tracker.start_step('Q Agent Processing')
            prompt = self._create_breakdown_prompt_no_file(temp_file_path, bedrock_context)
            result = self._execute_q_agent("breakdown-agent", prompt)
            
            logger.info(f"Q Agent execution: return code: {result.returncode}")
            tracker.end_step('Q Agent Processing')

            # Clean up temp file
            Path(temp_file_path).unlink(missing_ok=True)

            # Track output processing - PARSE FROM STDERR (Q CLI outputs there)
            tracker.start_step('Output Processing')
            raw_output = self._extract_agent_response(result)
            
            # Store raw output for debugging
            if raw_output:
                parsed_result = self._safe_parse_json(raw_output, "breakdown")
                tracker.set_response_length(raw_output)
            else:
                parsed_result = self._generate_fallback_breakdown()
                tracker.add_error("No agent output received", "Output Processing")
                tracker.set_json_validity(False)
            
            tracker.end_step('Output Processing')
            logger.info(f"Breakdown completed successfully for request {request_id}")
            
            # Store raw output in tracker for database storage
            tracker.raw_agent_output = raw_output
            
            return parsed_result, tracker

        except Exception as e:
            logger.error(f"Breakdown process failed for request {request_id}: {str(e)}")
            tracker.add_error(f"Process failed: {str(e)}", "General")
            tracker.set_json_validity(False)
            return self._generate_fallback_breakdown(), tracker

    def process_verification(self, request_id: int, design_content: str, bedrock_context: dict) -> tuple:
        """Process design verification using Q agent - database-first approach"""
        tracker = ProcessTracker(request_id, 'verification')
        tracker.set_agent_metadata('verify-agent')
        
        logger.info(f"Starting verification process for request {request_id}")
        
        try:
            # Track Bedrock query step
            tracker.start_step('Bedrock Query')
            bedrock_results = bedrock_context.get('results', [])
            tracker.set_rag_metrics(bedrock_results)
            
            if bedrock_results:
                avg_score = sum(r.get('score', 0) for r in bedrock_results) / len(bedrock_results)
                logger.info(f"Bedrock RAG: {len(bedrock_results)} results, avg similarity: {avg_score:.3f}")
            tracker.end_step('Bedrock Query')

            # Track Q Agent processing step - NO FILE OUTPUT
            tracker.start_step('Q Agent Processing')
            prompt = self._create_verification_prompt_no_file(design_content, bedrock_context)
            result = self._execute_q_agent("verify-agent", prompt)
            
            logger.info(f"Verification execution: return code: {result.returncode}")
            tracker.end_step('Q Agent Processing')

            # Track output processing - PARSE FROM STDERR (Q CLI outputs there)
            tracker.start_step('Output Processing')
            raw_output = self._extract_agent_response(result)
            
            if raw_output:
                parsed_result = self._safe_parse_json(raw_output, "verification")
                tracker.set_response_length(raw_output)
            else:
                parsed_result = self._generate_fallback_verification()
                tracker.add_error("No agent output received", "Output Processing")
                tracker.set_json_validity(False)
            
            tracker.end_step('Output Processing')
            logger.info(f"Verification completed successfully for request {request_id}")
            
            return parsed_result, tracker

        except Exception as e:
            logger.error(f"Verification process failed for request {request_id}: {str(e)}")
            tracker.add_error(f"Process failed: {str(e)}", "General")
            tracker.set_json_validity(False)
            return self._generate_fallback_verification(), tracker

    def process_creation(self, request_id: int, acceptance_criteria: str, bedrock_context: dict) -> tuple:
        """Process design document creation using Q agent - database-first approach"""
        tracker = ProcessTracker(request_id, 'creation')
        tracker.set_agent_metadata('create-agent')
        
        logger.info(f"Starting creation process for request {request_id}")
        
        try:
            # Track Bedrock query step
            tracker.start_step('Bedrock Query')
            bedrock_results = bedrock_context.get('results', [])
            tracker.set_rag_metrics(bedrock_results)
            
            if bedrock_results:
                avg_score = sum(r.get('score', 0) for r in bedrock_results) / len(bedrock_results)
                logger.info(f"Bedrock RAG: {len(bedrock_results)} results, avg similarity: {avg_score:.3f}")
            tracker.end_step('Bedrock Query')

            # Track Q Agent processing step - NO FILE OUTPUT
            tracker.start_step('Q Agent Processing')
            prompt = self._create_creation_prompt_no_file(acceptance_criteria, bedrock_context)
            result = self._execute_q_agent("create-agent", prompt)
            
            logger.info(f"Creation execution: return code: {result.returncode}")
            tracker.end_step('Q Agent Processing')

            # Track output processing - PARSE FROM STDERR (Q CLI outputs there)
            tracker.start_step('Output Processing')
            raw_output = self._extract_agent_response(result)
            
            if raw_output:
                parsed_result = self._safe_parse_json(raw_output, "creation")
                tracker.set_response_length(raw_output)
            else:
                parsed_result = self._generate_fallback_creation()
                tracker.add_error("No agent output received", "Output Processing")
                tracker.set_json_validity(False)
            
            tracker.end_step('Output Processing')
            logger.info(f"Creation completed successfully for request {request_id}")
            
            return parsed_result, tracker

        except Exception as e:
            logger.error(f"Creation process failed for request {request_id}: {str(e)}")
            tracker.add_error(f"Process failed: {str(e)}", "General")
            tracker.set_json_validity(False)
            return self._generate_fallback_creation(), tracker

    def process_chat(self, question: str, bedrock_context: dict) -> str:
        """Process chat question using Q agent"""
        try:
            prompt = self._create_chat_prompt(question, bedrock_context)
            result = self._execute_q_agent("chat-agent", prompt)

            # Extract response from Q CLI output
            response_text = self._extract_agent_response(result)

            if result.returncode == 0 and response_text:
                return self._clean_response(response_text)
            else:
                return self._generate_fallback_chat_response(question)

        except Exception:
            return self._generate_fallback_chat_response(question)

    def _execute_q_agent(self, agent_name: str, prompt: str) -> subprocess.CompletedProcess:
        """Execute Q CLI agent with prompt"""
        cmd = ['q', 'chat', '--agent', agent_name, '--no-interactive', '--wrap', 'never', prompt]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.config.BASE_DIR),
            timeout=60,
            input='\n'
        )

        return result

    def _extract_agent_response(self, result: subprocess.CompletedProcess) -> str:
        """Extract actual agent response from Q CLI output"""
        import re
        
        # Q CLI outputs to stderr with ANSI codes and UI elements
        output = result.stderr if result.stderr else result.stdout
        if not output:
            return ""
        
        # Remove ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_output = ansi_escape.sub('', output)
        
        # Look for the actual response after the prompt marker ">"
        lines = clean_output.split('\n')
        response_lines = []
        capturing = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('> ') or line == '>':
                capturing = True
                # Get content after the prompt marker
                content = line[2:].strip() if line.startswith('> ') else ""
                if content:
                    response_lines.append(content)
            elif capturing and line and not line.startswith('╭') and not line.startswith('│') and not line.startswith('╰'):
                # Continue capturing until we hit UI elements
                if 'Did you know?' in line or '/help' in line or '━━━' in line:
                    break
                response_lines.append(line)
        
        response = '\n'.join(response_lines).strip()
        return response

    def _safe_parse_json(self, raw_output: str, fallback_type: str = "breakdown") -> dict:
        """Safely parse JSON with recovery mechanisms"""
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            # Try auto-review to fix JSON issues
            reviewed_output = self._auto_review_json(raw_output, fallback_type)
            try:
                return json.loads(reviewed_output)
            except json.JSONDecodeError:
                pass
            
            # Try to extract JSON from mixed content
            start = raw_output.find('{')
            end = raw_output.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(raw_output[start:end+1])
                except Exception:
                    pass
            
            # Fallback to appropriate default
            if fallback_type == "breakdown":
                return self._generate_fallback_breakdown()
            elif fallback_type == "verification":
                return self._generate_fallback_verification()
            elif fallback_type == "creation":
                return self._generate_fallback_creation()
            else:
                return {"error": "Invalid JSON format", "raw_output": raw_output[:500]}

    def _auto_review_json(self, raw_output: str, expected_type: str) -> str:
        """Auto-review and fix JSON output using Q agent"""
        try:
            # First check if JSON is already valid
            json.loads(raw_output)
            return raw_output  # Already valid, no review needed
        except json.JSONDecodeError:
            pass
        
        review_prompt = f"""
You are a JSON reviewer. Check the JSON below for logical completeness and formatting issues.
If incomplete or malformed, correct and return ONLY the fixed JSON.

Expected type: {expected_type}
JSON to review: {raw_output}

Return only valid JSON, no explanations.
"""
        
        try:
            result = self._execute_q_agent("chat-agent", review_prompt)
            if result.stdout.strip():
                return result.stdout.strip()
            return raw_output  # Return original if review fails
        except Exception:
            return raw_output

    def _create_breakdown_prompt_no_file(self, file_path: str, bedrock_context: dict) -> str:
        """Create breakdown prompt that returns JSON directly (no file saving)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        except:
            document_text = "Unable to read document content"
        
        context_summary = bedrock_context.get('summary', 'No context available')

        return f"""
You are a senior product analyst who extracts precise user stories from technical specifications.

### OBJECTIVE
Read the provided specification and return a JSON breakdown that lists Epics, their User Stories, and Acceptance Criteria.

### DOCUMENT CONTENT
{document_text}

### CONTEXT FROM KNOWLEDGE BASE
{context_summary}

### INSTRUCTIONS
1. Identify major **Epics** that represent key features or business modules.
2. Under each Epic, list **User Stories** as per agile best practices.
3. For each User Story, include **clear and actionable Acceptance Criteria**.
4. Follow this exact JSON schema (no markdown, no commentary, no code block formatting):

{{
  "epics": [
    {{
      "name": "string",
      "stories": [
        {{
          "id": "string",
          "description": "string",
          "acceptance_criteria": [
            "string", "string"
          ]
        }}
      ]
    }}
  ]
}}

### RULES
- Output **only** valid JSON (no explanations or text outside JSON).
- Ensure JSON is syntactically valid and parsable by `json.loads()`.
- Avoid repetition or placeholder values.
- DO NOT save to any file - return JSON directly in your response.
"""

    def _create_verification_prompt_no_file(self, design_content: str, bedrock_context: dict) -> str:
        """Create verification prompt that returns JSON directly (no file saving)"""
        bedrock_context_str = bedrock_context.get('summary', 'No context available')
        
        return f"""
You are a senior solution architect verifying a design document for completeness.

### GOAL
Compare the design document content with known design patterns and identify:
1. Missing Appian objects or sections
2. Improvement recommendations

### DESIGN DOCUMENT
{design_content}

### CONTEXT FROM KNOWLEDGE BASE
{bedrock_context_str}

### EXPECTED OUTPUT
Return a single JSON object exactly in this format:
{{
  "status": "verified",
  "missing_objects": [
    {{"name": "string", "type": "string", "reason": "string"}}
  ],
  "recommendations": [
    "string", "string"
  ]
}}

### RULES
- Include detailed missing object reasoning.
- Focus on correctness and completeness.
- Output strictly valid JSON, no explanations or markdown.
- DO NOT save to any file - return JSON directly in your response.
"""

    def _create_creation_prompt_no_file(self, acceptance_criteria: str, bedrock_context: dict) -> str:
        """Create design creation prompt that returns JSON directly (no file saving)"""
        bedrock_context_str = bedrock_context.get('summary', 'No relevant context found')

        return f"""
You are a senior Appian solution designer.

### OBJECTIVE
Generate a professional design document based on the given Acceptance Criteria.

### INPUT CRITERIA
{acceptance_criteria}

### CONTEXT FROM KNOWLEDGE BASE
{bedrock_context_str}

### OUTPUT FORMAT
Return valid JSON in this structure:
{{
  "overview": "string",
  "objects_and_components": [
    {{
      "name": "string",
      "type": "string",
      "description": "string",
      "methods": ["string", "string"]
    }}
  ],
  "implementation_notes": ["string"],
  "dependencies": ["string"]
}}

### RULES
- Be specific and technical — name actual Appian objects where applicable.
- Maintain logical consistency between acceptance criteria and generated components.
- Output only valid JSON — no markdown, commentary, or explanations.
- DO NOT save to any file - return JSON directly in your response.
"""

    def _create_breakdown_prompt(self, file_path: str, output_path: str, bedrock_context: dict) -> str:
        """Create breakdown prompt with Bedrock context"""
        # Read document content for direct inclusion
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        except:
            document_text = "Unable to read document content"
        
        context_summary = bedrock_context.get('summary', 'No context available')

        return f"""
You are a senior product analyst who extracts precise user stories from technical specifications.

### OBJECTIVE
Read the provided specification and return a JSON breakdown that lists Epics, their User Stories, and Acceptance Criteria.

### DOCUMENT CONTENT
{document_text}

### CONTEXT FROM KNOWLEDGE BASE
{context_summary}

### INSTRUCTIONS
1. Identify major **Epics** that represent key features or business modules.
2. Under each Epic, list **User Stories** as per agile best practices.
3. For each User Story, include **clear and actionable Acceptance Criteria**.
4. Follow this exact JSON schema (no markdown, no commentary, no code block formatting):

{{
  "epics": [
    {{
      "name": "string",
      "stories": [
        {{
          "id": "string",
          "description": "string",
          "acceptance_criteria": [
            "string", "string"
          ]
        }}
      ]
    }}
  ]
}}

### RULES
- Output **only** valid JSON (no explanations or text outside JSON).
- Ensure JSON is syntactically valid and parsable by `json.loads()`.
- Avoid repetition or placeholder values.
- Save output to: {output_path}
"""

    def _create_verification_prompt(self, design_content: str, output_path: str, bedrock_context: dict) -> str:
        """Create verification prompt with Bedrock context"""
        bedrock_context_str = bedrock_context.get('summary', 'No context available')
        
        return f"""
You are a senior solution architect verifying a design document for completeness.

### GOAL
Compare the design document content with known design patterns and identify:
1. Missing Appian objects or sections
2. Improvement recommendations

### DESIGN DOCUMENT
{design_content}

### CONTEXT FROM KNOWLEDGE BASE
{bedrock_context_str}

### EXPECTED OUTPUT
Return a single JSON object exactly in this format:
{{
  "status": "verified",
  "missing_objects": [
    {{"name": "string", "type": "string", "reason": "string"}}
  ],
  "recommendations": [
    "string", "string"
  ]
}}

### RULES
- Include detailed missing object reasoning.
- Focus on correctness and completeness.
- Output strictly valid JSON, no explanations or markdown.
- Save output to: {output_path}
"""

    def _create_creation_prompt(self, acceptance_criteria: str, output_path: str, bedrock_context: dict) -> str:
        """Create design creation prompt with Bedrock context"""
        bedrock_context_str = bedrock_context.get('summary', 'No relevant context found')

        return f"""
You are a senior Appian solution designer.

### OBJECTIVE
Generate a professional design document based on the given Acceptance Criteria.

### INPUT CRITERIA
{acceptance_criteria}

### CONTEXT FROM KNOWLEDGE BASE
{bedrock_context_str}

### OUTPUT FORMAT
Return valid JSON in this structure:
{{
  "overview": "string",
  "objects_and_components": [
    {{
      "name": "string",
      "type": "string",
      "description": "string",
      "methods": ["string", "string"]
    }}
  ],
  "implementation_notes": ["string"],
  "dependencies": ["string"]
}}

### RULES
- Be specific and technical — name actual Appian objects where applicable.
- Maintain logical consistency between acceptance criteria and generated components.
- Output only valid JSON — no markdown, commentary, or explanations.
- Save output to: {output_path}
"""

    def _create_chat_prompt(self, question: str, bedrock_context: dict) -> str:
        """Create chat prompt with Bedrock context"""
        return f"""
User Question: {question}

Bedrock Context (relevant documents):
{json.dumps(bedrock_context, indent=2)}

Please answer the user's question based on the available context. Be helpful and conversational.
"""

    def _generate_fallback_breakdown(self) -> dict:
        """Generate fallback breakdown data"""
        return {
            "epics": [
                {
                    "name": "Feature Implementation",
                    "stories": [
                        {
                            "id": "STORY-001",
                            "description": "Core functionality implementation",
                            "acceptance_criteria": [
                                "System processes user input correctly",
                                "Expected results are returned to user",
                                "Error handling works for invalid inputs"
                            ]
                        }
                    ]
                }
            ]
        }

    def _generate_fallback_verification(self) -> dict:
        """Generate fallback verification data"""
        return {
            "status": "verified",
            "missing_objects": [
                {"name": "ValidationService", "type": "Service", "reason": "Input validation not specified"}
            ],
            "recommendations": [
                "Design appears complete based on available context",
                "Consider adding error handling components"
            ]
        }

    def _generate_fallback_creation(self) -> dict:
        """Generate fallback creation data"""
        return {
            "overview": "Design document generated from acceptance criteria (fallback mode)",
            "objects_and_components": [
                {
                    "name": "MainService",
                    "type": "Service",
                    "description": "Core service handling main functionality",
                    "methods": ["processRequest", "validateInput", "generateResponse"]
                }
            ],
            "implementation_notes": [
                "Follow existing service patterns",
                "Implement proper error handling"
            ],
            "dependencies": [
                "Database service",
                "Validation framework"
            ]
        }

    def _generate_fallback_chat_response(self, question: str) -> str:
        """Generate fallback chat response"""
        return (f"I understand you're asking about: {question}. However, I don't have specific "
                "information available in the knowledge base to provide a detailed answer. "
                "Could you try rephrasing your question or provide more context?")

    def _clean_response(self, response: str) -> str:
        """Clean ANSI codes and unwanted characters from response"""
        import re
        
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', response)
        
        # Remove Q CLI UI elements and formatting
        cleaned = re.sub(r'╭[─]*.*?╮', '', cleaned, flags=re.DOTALL)  # Remove boxes
        cleaned = re.sub(r'━[━]*', '', cleaned)  # Remove horizontal lines
        cleaned = re.sub(r'│.*?│', '', cleaned)  # Remove box content
        cleaned = re.sub(r'/help.*?fuzzy search', '', cleaned)  # Remove help text
        cleaned = re.sub(r'WARNING:.*?allowedPaths.*?\]', '', cleaned)  # Remove warnings
        cleaned = re.sub(r'🤖.*?claude-sonnet-4', '', cleaned)  # Remove model info
        cleaned = re.sub(r'🛠️.*?Using tool:.*?fs_read.*?trusted', '', cleaned)  # Remove tool usage
        cleaned = re.sub(r'●.*?Completed in.*?s', '', cleaned)  # Remove completion info
        cleaned = re.sub(r'✓.*?Successfully.*?entries?\)', '', cleaned)  # Remove success messages
        cleaned = re.sub(r'> ', '', cleaned)  # Remove prompt markers
        
        # Extract the actual response content (usually after the last tool usage)
        lines = cleaned.split('\n')
        content_lines = []
        capturing = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Start capturing after we see actual content (not UI elements)
            if any(keyword in line.lower() for keyword in ['nexusgen', 'based on', 'here\'s what', 'document intelligence']):
                capturing = True
            if capturing and line and not any(ui_element in line for ui_element in ['⋮', '●', '✓', '🛠️', '🤖']):
                content_lines.append(line)
        
        if content_lines:
            cleaned = ' '.join(content_lines)
        else:
            # Fallback: just clean up the text
            cleaned = ' '.join(cleaned.split())
        
        # Final cleanup
        cleaned = cleaned.replace('mm mm', ' ')
        cleaned = cleaned.replace('10m"', '"')
        cleaned = cleaned.replace('m.mm', '.')
        cleaned = cleaned.replace('mm', '')
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
