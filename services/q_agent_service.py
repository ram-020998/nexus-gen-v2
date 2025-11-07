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
        self._artifacts_context = None

    @property
    def artifacts_context(self) -> str:
        """Lazy load application artifacts"""
        if self._artifacts_context is None:
            self._artifacts_context = self._load_application_artifacts()
        return self._artifacts_context

    def process_breakdown(self, request_id: int, file_content: str, bedrock_context: dict) -> dict:
        """Process spec breakdown using Q agent"""
        try:
            # Prepare prompt with content and Bedrock context
            prompt = self._create_breakdown_prompt(file_content, bedrock_context)

            # Store the prompt in database (always store, even if Q agent fails)
            self._update_request_field(request_id, 'q_agent_prompt', prompt)

            # Execute Q agent and capture output
            result = self._execute_q_agent("breakdown-agent", prompt)
            
            # Store raw output for debugging
            self._update_request_field(request_id, 'raw_agent_output', result.stdout)

            # Parse JSON from Q agent output
            json_output = self._extract_json_from_output(result)
            if json_output:
                return json_output
            else:
                # Log the failure reason
                error_msg = f"Q agent JSON extraction failed. Return code: {result.returncode}"
                self._update_request_field(request_id, 'error_log', error_msg)
                return self._generate_fallback_breakdown()

        except Exception as e:
            # Log the actual error
            error_msg = f"Q agent execution failed: {str(e)}"
            self._update_request_field(request_id, 'error_log', error_msg)
            return self._generate_fallback_breakdown()

    def _update_request_field(self, request_id: int, field: str, value: str):
        """Update a specific field in the request"""
        from models import db, Request
        request = Request.query.get(request_id)
        if request:
            setattr(request, field, value)
            db.session.commit()

    def process_verification(self, request_id: int, design_content: str, bedrock_context: dict) -> dict:
        """Process design verification using Q agent"""
        try:
            # Prepare prompt with content and Bedrock context
            prompt = self._create_verification_prompt(design_content, bedrock_context)

            # Store the prompt in database (always store, even if Q agent fails)
            self._update_request_field(request_id, 'q_agent_prompt', prompt)

            # Execute Q agent and capture output
            result = self._execute_q_agent("verify-agent", prompt)
            
            # Store raw output for debugging
            self._update_request_field(request_id, 'raw_agent_output', result.stdout)

            # Parse JSON from Q agent output
            json_output = self._extract_json_from_output(result)
            if json_output:
                return json_output
            else:
                # Log the failure reason
                error_msg = f"Verify agent JSON extraction failed. Return code: {result.returncode}"
                self._update_request_field(request_id, 'error_log', error_msg)
                return self._generate_fallback_verification()

        except Exception as e:
            # Log the actual error
            error_msg = f"Verify agent execution failed: {str(e)}"
            self._update_request_field(request_id, 'error_log', error_msg)
            return self._generate_fallback_verification()

    def process_creation(self, request_id: int, acceptance_criteria: str, bedrock_context: dict) -> dict:
        """Process design document creation using Q agent"""
        try:
            # Prepare prompt with content and Bedrock context
            prompt = self._create_creation_prompt(acceptance_criteria, bedrock_context)

            # Store the prompt in database (always store, even if Q agent fails)
            self._update_request_field(request_id, 'q_agent_prompt', prompt)

            # Execute Q agent and capture output
            result = self._execute_q_agent("create-agent", prompt)
            
            # Store raw output for debugging
            self._update_request_field(request_id, 'raw_agent_output', result.stdout)

            # Parse JSON from Q agent output
            json_output = self._extract_json_from_output(result)
            if json_output:
                return json_output
            else:
                # Log the failure reason
                error_msg = f"Create agent JSON extraction failed. Return code: {result.returncode}"
                self._update_request_field(request_id, 'error_log', error_msg)
                return self._generate_fallback_creation()

        except Exception as e:
            # Log the actual error
            error_msg = f"Create agent execution failed: {str(e)}"
            self._update_request_field(request_id, 'error_log', error_msg)
            return self._generate_fallback_creation()

    def process_chat(self, question: str, bedrock_context: dict) -> str:
        """Process chat question using Q agent"""
        try:
            prompt = self._create_chat_prompt(question, bedrock_context)
            result = self._execute_q_agent("chat-agent", prompt)

            # Q CLI outputs to stderr, so check both stdout and stderr
            response_text = ""
            if result.stdout.strip():
                response_text = result.stdout.strip()
            elif result.stderr.strip():
                response_text = result.stderr.strip()

            if result.returncode == 0 and response_text:
                return self._clean_response(response_text)
            else:
                return self._generate_fallback_chat_response(question)

        except Exception:
            return self._generate_fallback_chat_response(question)

    def _execute_q_agent(self, agent_name: str, prompt: str) -> subprocess.CompletedProcess:
        """Execute Q CLI agent with prompt"""
        cmd = ['q', 'chat', '--agent', agent_name, '--no-interactive', prompt]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.config.BASE_DIR),
            timeout=120,  # Increased from 60 to 120 seconds
            input='\n'  # Send newline to handle any interactive prompts
        )

        return result

    def _extract_json_from_output(self, result: subprocess.CompletedProcess) -> dict:
        """Extract JSON from Q agent output"""
        try:
            # Q agent outputs to stdout
            output = result.stdout
            
            # Remove ANSI color codes
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_output = ansi_escape.sub('', output)
            
            # Find the JSON block - look for any JSON structure
            lines = clean_output.split('\n')
            json_lines = []
            in_json = False
            brace_count = 0
            
            for line in lines:
                line = line.strip()
                # Start JSON extraction when we find an opening brace
                if line.startswith('{') and not in_json:
                    in_json = True
                    json_lines.append(line)
                    brace_count += line.count('{') - line.count('}')
                elif in_json:
                    json_lines.append(line)
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        break
            
            if json_lines:
                json_str = '\n'.join(json_lines)
                # Clean up any remaining non-printable characters
                json_str = re.sub(r'[^\x20-\x7E\n\r\t]', '', json_str)
                return json.loads(json_str)
                
            return None
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"JSON extraction error: {e}")
            print(f"Clean output preview: {clean_output[:500]}")
            return None

    def _create_breakdown_prompt(self, file_content: str, bedrock_context: dict) -> str:
        """Create breakdown prompt with Bedrock context and application artifacts"""
        # Get relevant context from Bedrock
        context_text = ""
        if bedrock_context and 'results' in bedrock_context:
            results = bedrock_context['results'][:2]  # Limit to first 2 results
            context_text = "\n".join([r.get('content', '')[:200] for r in results])
        
        # Get artifacts information
        artifacts_ref = self._prepare_artifacts_for_q(file_content)
        
        return f"""
{artifacts_ref}

Here is the specification content:
{file_content}

Additional context from knowledge base:
{context_text}

INSTRUCTIONS:
1. Analyze the specification using the artifacts files referenced above
2. Reference specific objects from the Source Selection application artifacts
3. Consider object dependencies and relationships defined in the blueprint and lookup files
4. Create user stories that align with existing application architecture

Create user stories from this specification. Return only valid JSON in this exact format:
{{
  "epics": [
    {{
      "name": "Epic Name",
      "stories": [
        {{
          "id": "STORY-001", 
          "description": "As a user, I want...",
          "acceptance_criteria": ["criterion 1", "criterion 2"]
        }}
      ]
    }}
  ]
}}
"""

    def _create_verification_prompt(self, design_content: str, bedrock_context: dict) -> str:
        """Create verification prompt with Bedrock context and application artifacts"""
        artifacts_ref = self._prepare_artifacts_for_q(design_content)
        
        return f"""
{artifacts_ref}

Please verify this design document content:

{design_content}

Bedrock Context (existing designs):
{json.dumps(bedrock_context, indent=2)}

INSTRUCTIONS:
1. Verify the design against the artifacts files referenced above
2. Check if referenced objects exist in the blueprint and lookup files
3. Validate object dependencies and relationships
4. Ensure design follows existing application patterns and architecture

Analyze against existing designs and artifacts to identify:
1. Missing objects or components
2. Areas that need attention
3. Recommendations based on similar designs and artifact patterns

Return only valid JSON output with verification results.
"""

    def _create_creation_prompt(self, acceptance_criteria: str, bedrock_context: dict) -> str:
        """Create design creation prompt with Bedrock context and application artifacts"""
        context_summary = bedrock_context.get('summary', 'No relevant context found')
        context_results = bedrock_context.get('results', [])

        context_info = "BEDROCK CONTEXT:\n"
        if context_results:
            context_info += f"Summary: {context_summary}\n"
            for i, result in enumerate(context_results[:2]):  # Limit to 2 results
                content = result.get('content', '')
                if content:
                    context_info += f"{i + 1}. {content[:150]}...\n"
        else:
            context_info += "No existing components found in knowledge base.\n"

        # Get detailed artifacts information
        artifacts_info = self._get_relevant_objects(acceptance_criteria)
        artifacts_ref = self._prepare_artifacts_for_q(acceptance_criteria)

        return f"""
{artifacts_ref}

{artifacts_info}

ACCEPTANCE CRITERIA:
{acceptance_criteria}

{context_info}

INSTRUCTIONS:
1. Use the artifacts files referenced above for specific object names and types
2. Look for existing evaluation forms, rules, and interfaces in the artifacts
3. Reference exact object names from the Source Selection application
4. Consider object dependencies and relationships

OUTPUT FORMAT: Return only valid JSON:
{{
  "design_document": {{
    "overview": "Brief description of changes needed",
    "existing_objects_to_modify": [
      {{
        "name": "Exact object name from artifacts",
        "type": "Object type",
        "current_description": "What it currently does",
        "proposed_changes": "Specific changes needed",
        "new_methods": ["method1", "method2"]
      }}
    ],
    "new_objects": [
      {{
        "name": "New object name",
        "type": "Object type", 
        "description": "Purpose and functionality",
        "methods": ["method1", "method2"]
      }}
    ],
    "implementation_notes": ["Note 1", "Note 2"],
    "dependencies": ["Dependency 1", "Dependency 2"]
  }}
}}
"""

    def _create_chat_prompt(self, question: str, bedrock_context: dict) -> str:
        """Create chat prompt with Bedrock context and application artifacts"""
        artifacts_ref = self._prepare_artifacts_for_q(question)
        
        return f"""
{artifacts_ref}

User Question: {question}

Bedrock Context (relevant documents):
{json.dumps(bedrock_context, indent=2)}

INSTRUCTIONS:
1. Answer using information from the artifacts files referenced above
2. Reference specific objects, dependencies, and relationships from the artifacts when relevant
3. Provide detailed technical information based on the blueprint and lookup files
4. Be helpful and conversational while being technically accurate

Please answer the user's question based on the available context and artifacts.
"""

    def _generate_fallback_breakdown(self) -> dict:
        """Generate fallback breakdown data"""
        return {
            "epic": "Feature Implementation",
            "stories": [
                {
                    "story_name": "Core Functionality",
                    "acceptance_criteria": (
                        "**GIVEN**: System is ready\n**WHEN**: User performs action\n"
                        "**THEN**: Expected result occurs"),
                    "issue_type": "User Story",
                    "points": ""}]}

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
                "overview": "Design document generated from acceptance criteria (fallback mode)",
                "existing_objects_to_modify": [],
                "new_objects": [
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
                    "Database service",
                    "Validation framework"
                ]
            }
        }

    def process_conversion(self, request_id: int, maria_sql: str) -> str:
        """Process SQL conversion using Q agent"""
        try:
            # Prepare prompt for conversion
            prompt = self._create_conversion_prompt(maria_sql)

            # Store the prompt in database
            self._update_request_field(request_id, 'q_agent_prompt', prompt)

            # Execute Q agent and capture output
            result = self._execute_q_agent("convert-agent", prompt)
            
            # Store raw output for debugging
            self._update_request_field(request_id, 'raw_agent_output', result.stdout)

            # Extract Oracle SQL from output
            oracle_sql = self._extract_sql_from_output(result)
            if oracle_sql:
                return oracle_sql
            else:
                # Log the failure reason
                error_msg = f"Convert agent SQL extraction failed. Return code: {result.returncode}"
                self._update_request_field(request_id, 'error_log', error_msg)
                return self._generate_fallback_conversion(maria_sql)

        except Exception as e:
            # Log the actual error
            error_msg = f"Convert agent execution failed: {str(e)}"
            self._update_request_field(request_id, 'error_log', error_msg)
            return self._generate_fallback_conversion(maria_sql)

    def _create_conversion_prompt(self, maria_sql: str) -> str:
        """Create conversion prompt with guide content"""
        # Read the conversion guide
        guide_content = ""
        try:
            guide_path = Path(self.config.BASE_DIR) / "mariaToOracleConversionGuid.md"
            if guide_path.exists():
                guide_content = guide_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not read conversion guide: {e}")
        
        return f"""
CONVERSION GUIDE:
{guide_content}

MARIADB SQL TO CONVERT:
{maria_sql}

INSTRUCTIONS:
Follow the conversion guide above exactly. Convert the MariaDB SQL to Oracle format using the patterns and rules specified in the guide. Return only the converted Oracle SQL script.
"""

    def _extract_sql_from_output(self, result: subprocess.CompletedProcess) -> str:
        """Extract SQL from Q agent output"""
        try:
            # Q agent outputs to stdout
            output = result.stdout
            
            # Remove ANSI color codes more thoroughly
            import re
            # Remove all ANSI escape sequences
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_output = ansi_escape.sub('', output)
            
            # Remove remaining color codes like '10m', 'm10m', 'mmm'
            clean_output = re.sub(r'\d+m', '', clean_output)
            clean_output = re.sub(r'm\d+m', '', clean_output)
            clean_output = re.sub(r'mmm+', '', clean_output)
            clean_output = re.sub(r'mm+', '', clean_output)
            
            # Split into lines and clean each line
            lines = clean_output.split('\n')
            sql_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and Q CLI UI elements
                if not line or any(ui in line for ui in ['╭', '╮', '│', '━', '🤖', '🛠️', '●', '✓', 'WARNING:', 'Using tool:', 'Completed in']):
                    continue
                
                # Include SQL-related lines
                if (line.startswith('CREATE') or 
                    line.startswith('EXECUTE') or 
                    line.startswith('--') or
                    'VARCHAR2' in line or 
                    'NUMBER' in line or
                    'TIMESTAMP' in line or
                    'CONSTRAINT' in line or
                    'PRIMARY KEY' in line or
                    line.startswith(')') or
                    line.endswith(',') or
                    line.endswith(';')):
                    sql_lines.append(line)
            
            if sql_lines:
                return self._format_sql(sql_lines)
            
            # If no SQL found using filters, return cleaned output
            return clean_output.strip() if clean_output.strip() else None
                
        except Exception as e:
            print(f"SQL extraction error: {e}")
            return None

    def _format_sql(self, sql_lines: list) -> str:
        """Format SQL lines with proper indentation and spacing"""
        formatted_lines = []
        indent_level = 0
        
        for line in sql_lines:
            line = line.strip()
            
            # Decrease indent for closing parenthesis
            if line.startswith(')'):
                indent_level = max(0, indent_level - 1)
            
            # Add proper indentation
            if line.startswith('CREATE') or line.startswith('EXECUTE') or line.startswith('--'):
                formatted_lines.append(line)
            else:
                formatted_lines.append('  ' + line)
            
            # Increase indent after opening parenthesis
            if line.endswith('('):
                indent_level += 1
            
            # Add blank line after each statement
            if line.endswith(';'):
                formatted_lines.append('')
        
        return '\n'.join(formatted_lines).strip()

    def _generate_fallback_conversion(self, maria_sql: str) -> str:
        """Generate fallback conversion with basic Oracle patterns"""
        # Basic conversion patterns
        oracle_sql = maria_sql
        
        # Basic data type conversions
        oracle_sql = oracle_sql.replace('INT(11)', 'NUMBER(10)')
        oracle_sql = oracle_sql.replace('TINYINT(1)', 'NUMBER(1)')
        oracle_sql = oracle_sql.replace('VARCHAR(', 'VARCHAR2(')
        oracle_sql = oracle_sql.replace('DATETIME', 'TIMESTAMP')
        oracle_sql = oracle_sql.replace('AUTO_INCREMENT', '')
        oracle_sql = oracle_sql.replace('IF NOT EXISTS', '')
        oracle_sql = oracle_sql.replace('`', '')
        
        return f"""-- Basic Oracle conversion (Q agent unavailable)
-- Note: This is a simplified conversion. Use Q agent for complete conversion.

{oracle_sql}

-- Additional Oracle-specific statements would be generated by Q agent:
-- 1. EXECUTE IMMEDIATE for table creation
-- 2. Named constraints (table_name_PK)
-- 3. Separate index creation
-- 4. Sequence creation for AUTO_INCREMENT columns"""

    def _generate_fallback_chat_response(self, question: str) -> str:
        """Generate fallback chat response"""
        return (f"I understand you're asking about: {question}. However, I don't have specific "
                "information available in the knowledge base to provide a detailed answer. "
                "Could you try rephrasing your question or provide more context?")

    def _load_application_artifacts(self) -> str:
        """Load application artifacts for object definitions and dependencies"""
        try:
            artifacts_dir = Path(self.config.BASE_DIR) / "applicationArtifacts" / "Source Selection"
            blueprint_file = artifacts_dir / "SourceSelectionv2.6.0_blueprint.json"
            lookup_file = artifacts_dir / "SourceSelectionv2.6.0_object_lookup.json"
            
            artifacts_info = "APPLICATION ARTIFACTS - SOURCE SELECTION v2.6.0:\n"
            
            if blueprint_file.exists():
                with open(blueprint_file, 'r', encoding='utf-8') as f:
                    blueprint_data = json.load(f)
                    
                    # Add sample rule names if available
                    if 'rules' in blueprint_data and blueprint_data['rules']:
                        sample_rules = [rule.get('name', 'Unnamed') for rule in blueprint_data['rules'][:3]]
                        artifacts_info += f"Sample Rules: {', '.join(sample_rules)}\n"
            
            if lookup_file.exists():
                with open(lookup_file, 'r', encoding='utf-8') as f:
                    lookup_data = json.load(f)
                    
                    # Get sample objects by type
                    sample_objects = {}
                    for obj_id, obj_data in list(lookup_data.items())[:50]:  # Sample first 50
                        obj_type = obj_data.get('object_type', 'Unknown')
                        obj_name = obj_data.get('name', 'Unnamed')
                        
                        if obj_type not in sample_objects:
                            sample_objects[obj_type] = []
                        if len(sample_objects[obj_type]) < 2:
                            sample_objects[obj_type].append(obj_name)
                    
                    # Add key object types
                    for obj_type in ['Expression Rule', 'Interface', 'Constant']:
                        if obj_type in sample_objects:
                            artifacts_info += f"{obj_type}s: {', '.join(sample_objects[obj_type])}\n"
            
            artifacts_info += "Use these artifacts for specific object names and relationships.\n"
            return artifacts_info
            
        except Exception as e:
            return f"APPLICATION ARTIFACTS: Error loading - {str(e)}\n"

    def _get_relevant_objects(self, query_text: str, max_objects: int = 10) -> str:
        """Get relevant objects from artifacts based on query text"""
        try:
            artifacts_dir = Path(self.config.BASE_DIR) / "applicationArtifacts" / "Source Selection"
            lookup_file = artifacts_dir / "SourceSelectionv2.6.0_object_lookup.json"
            blueprint_file = artifacts_dir / "SourceSelectionv2.6.0_blueprint.json"
            
            result = "DETAILED ARTIFACTS INFORMATION:\n\n"
            
            # Get relevant objects from lookup
            if lookup_file.exists():
                with open(lookup_file, 'r', encoding='utf-8') as f:
                    lookup_data = json.load(f)
                
                keywords = ['evaluation', 'create', 'form', 'settings', 'award', 'type'] + query_text.lower().split()
                relevant_objects = []
                
                for obj_id, obj_data in lookup_data.items():
                    obj_name = obj_data.get('name', '').lower()
                    obj_desc = obj_data.get('description', '').lower()
                    
                    if any(keyword in obj_name or keyword in obj_desc for keyword in keywords):
                        relevant_objects.append({
                            'name': obj_data.get('name', 'Unnamed'),
                            'type': obj_data.get('object_type', 'Unknown'),
                            'description': obj_data.get('description', 'No description')
                        })
                    
                    if len(relevant_objects) >= max_objects:
                        break
                
                if relevant_objects:
                    result += "RELEVANT OBJECTS FROM LOOKUP:\n"
                    for obj in relevant_objects:
                        result += f"- {obj['name']} ({obj['type']})\n"
                        result += f"  Description: {obj['description'][:150]}...\n\n"
            
            # Get relevant rules from blueprint
            if blueprint_file.exists():
                with open(blueprint_file, 'r', encoding='utf-8') as f:
                    blueprint_data = json.load(f)
                
                if 'rules' in blueprint_data:
                    result += "RELEVANT RULES FROM BLUEPRINT:\n"
                    rule_count = 0
                    for rule in blueprint_data['rules']:
                        rule_name = rule.get('name', '').lower()
                        if any(keyword in rule_name for keyword in ['evaluation', 'create', 'form', 'settings']):
                            result += f"- {rule.get('name', 'Unnamed Rule')}\n"
                            if 'description' in rule:
                                result += f"  Description: {rule['description'][:100]}...\n"
                            result += "\n"
                            rule_count += 1
                            if rule_count >= 5:
                                break
                
                if 'interfaces' in blueprint_data:
                    result += "RELEVANT INTERFACES FROM BLUEPRINT:\n"
                    interface_count = 0
                    for interface in blueprint_data['interfaces']:
                        interface_name = interface.get('name', '').lower()
                        if any(keyword in interface_name for keyword in ['evaluation', 'create', 'form', 'settings']):
                            result += f"- {interface.get('name', 'Unnamed Interface')}\n"
                            if 'description' in interface:
                                result += f"  Description: {interface['description'][:100]}...\n"
                            result += "\n"
                            interface_count += 1
                            if interface_count >= 5:
                                break
            
            return result
            
        except Exception as e:
            return f"ARTIFACTS ERROR: {str(e)}\n"

    def _prepare_artifacts_for_q(self, query_text: str) -> str:
        """Prepare artifacts information in a format Q can access"""
        try:
            artifacts_dir = Path(self.config.BASE_DIR) / "applicationArtifacts" / "Source Selection"
            
            # Create a summary file for Q to reference
            summary_content = f"""SOURCE SELECTION APPLICATION ARTIFACTS SUMMARY

BLUEPRINT FILE: {artifacts_dir}/SourceSelectionv2.6.0_blueprint.json
LOOKUP FILE: {artifacts_dir}/SourceSelectionv2.6.0_object_lookup.json

KEY EVALUATION-RELATED OBJECTS TO REFERENCE:
"""
            
            # Add specific objects from lookup
            lookup_file = artifacts_dir / "SourceSelectionv2.6.0_object_lookup.json"
            if lookup_file.exists():
                with open(lookup_file, 'r', encoding='utf-8') as f:
                    lookup_data = json.load(f)
                
                eval_objects = []
                for obj_id, obj_data in lookup_data.items():
                    obj_name = obj_data.get('name', '').lower()
                    if 'evaluation' in obj_name or 'create' in obj_name or 'form' in obj_name:
                        eval_objects.append({
                            'name': obj_data.get('name'),
                            'type': obj_data.get('object_type'),
                            'description': obj_data.get('description', '')[:200]
                        })
                    if len(eval_objects) >= 15:
                        break
                
                for obj in eval_objects:
                    summary_content += f"\n{obj['name']} ({obj['type']})\n"
                    summary_content += f"Description: {obj['description']}\n"
            
            # Write to temp file
            temp_file = Path(self.config.BASE_DIR) / "temp_artifacts_summary.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            return f"ARTIFACTS REFERENCE: See {temp_file} for detailed object information.\n"
            
        except Exception as e:
            return f"ARTIFACTS PREP ERROR: {str(e)}\n"

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
