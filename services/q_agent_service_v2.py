"""
Q Agent Service V2 - Database-first approach without file dependencies
"""
import subprocess
import json
import tempfile
import logging
import time
from pathlib import Path
from config import Config
from services.process_tracker import ProcessTracker

logger = logging.getLogger(__name__)


class QAgentServiceV2:
    """Q Agent service that relies on database instead of output files"""

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

            # Track output processing - PARSE FROM STDOUT ONLY
            tracker.start_step('Output Processing')
            raw_output = result.stdout.strip() if result.stdout else ""
            
            if raw_output:
                parsed_result = self._safe_parse_json(raw_output, "breakdown")
                tracker.set_response_length(raw_output)
            else:
                parsed_result = self._generate_fallback_breakdown()
                tracker.add_error("No agent output received", "Output Processing")
                tracker.set_json_validity(False)
            
            tracker.end_step('Output Processing')
            logger.info(f"Breakdown completed successfully for request {request_id}")
            
            return parsed_result, tracker

        except Exception as e:
            logger.error(f"Breakdown process failed for request {request_id}: {str(e)}")
            tracker.add_error(f"Process failed: {str(e)}", "General")
            tracker.set_json_validity(False)
            return self._generate_fallback_breakdown(), tracker

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

    def _execute_q_agent(self, agent_name: str, prompt: str) -> subprocess.CompletedProcess:
        """Execute Q CLI agent with prompt"""
        cmd = ['q', 'chat', '--agent', agent_name, '--no-interactive', prompt]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.config.BASE_DIR),
            timeout=60,
            input='\n'
        )

        return result

    def _safe_parse_json(self, raw_output: str, fallback_type: str = "breakdown") -> dict:
        """Safely parse JSON with recovery mechanisms"""
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
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
            else:
                return {"error": "Invalid JSON format", "raw_output": raw_output[:500]}

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
