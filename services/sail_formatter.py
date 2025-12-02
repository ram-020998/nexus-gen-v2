"""
SAIL Code Formatter - Formats and cleans SAIL code with UUID resolution

This service formats SAIL code by:
1. Removing escape sequences
2. Replacing UUID references with actual object names
3. Replacing Appian function calls with public names
4. Cleaning up formatting
"""

import re
import json
from typing import Dict, Any
from pathlib import Path

from core.base_service import BaseService
from core.logger import get_merge_logger


class SAILFormatter(BaseService):
    """Formats SAIL code by resolving UUIDs and cleaning formatting"""
    
    def __init__(self, container=None):
        """Initialize formatter with dependencies"""
        super().__init__(container)
        self.logger = get_merge_logger()
        self.appian_functions = self._load_appian_functions()
        self.object_lookup = {}
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies"""
        pass
    
    def set_object_lookup(self, object_lookup: Dict[str, Dict[str, Any]]) -> None:
        """
        Set the object lookup dictionary for UUID resolution.
        
        Args:
            object_lookup: Dict mapping UUID -> {name, object_type, ...}
        """
        self.object_lookup = object_lookup
    
    def _load_appian_functions(self) -> Dict[str, str]:
        """Load Appian public functions mapping"""
        try:
            schema_path = Path(__file__).parent / 'schemas' / 'appian_public_functions.json'
            with open(schema_path, 'r') as f:
                data = json.load(f)
            
            # Create reverse mapping from internal names to public names
            function_map = {}
            functions = data['appian_public_functions']['functions']
            
            for category, components in functions.items():
                for public_name, internal_names in components.items():
                    # Map public name to itself
                    function_map[public_name] = public_name
                    # Map internal names to public name
                    for internal_name in internal_names:
                        function_map[internal_name] = public_name
            
            self.logger.info(f"Loaded {len(function_map)} Appian function mappings")
            return function_map
        
        except Exception as e:
            self.logger.warning(f"Could not load Appian functions mapping: {e}")
            return {}
    
    def format_sail_code(self, sail_code: str) -> str:
        """
        Format SAIL code with UUID resolution and cleanup.
        
        Args:
            sail_code: Raw SAIL code
            
        Returns:
            Formatted SAIL code
        """
        if not sail_code or not sail_code.strip():
            return ""
        
        # Step 1: Remove escape sequences
        formatted_code = self._remove_escape_sequences(sail_code)
        
        # Step 2: Replace UUID references with object names
        formatted_code = self._replace_uuid_references(formatted_code)
        
        # Step 3: Replace Appian function calls with public names
        formatted_code = self._replace_appian_functions(formatted_code)
        
        # Step 4: Clean up formatting
        formatted_code = self._clean_formatting(formatted_code)
        
        return formatted_code
    
    def format_process_model_logic(self, business_logic: str) -> str:
        """
        Format process model business logic with proper node separation.
        
        Args:
            business_logic: Raw business logic text
            
        Returns:
            Formatted business logic
        """
        if not business_logic or not business_logic.strip():
            return ""
        
        # Step 1: Remove escape sequences
        formatted_logic = self._remove_escape_sequences(business_logic)
        
        # Step 2: Replace UUID references
        formatted_logic = self._replace_uuid_references(formatted_logic)
        
        # Step 3: Format node sections with proper line breaks
        formatted_logic = self._format_node_sections(formatted_logic)
        
        return formatted_logic
    
    def _remove_escape_sequences(self, code: str) -> str:
        """Remove escape sequences while preserving content"""
        # Remove common escape sequences
        code = code.replace('\\n', '\n')
        code = code.replace('\\t', '\t')
        code = code.replace('\\r', '\r')
        code = code.replace('\\"', '"')
        code = code.replace("\\'", "'")
        code = code.replace('\\\\', '\\')
        return code
    
    def _replace_uuid_references(self, code: str) -> str:
        """Replace UUID references with actual object names"""
        # Pattern to match various UUID reference formats
        patterns = [
            r'#"(_a-[a-f0-9\-_]+)"',  # Standard format: #"_a-uuid"
            r'#"([a-f0-9\-]{36})"',   # Standard UUID format: #"uuid"
            r'rule!([a-f0-9\-]{36})',  # Rule reference: rule!uuid
            r'cons!([a-f0-9\-]{36})',  # Constant reference: cons!uuid
            r'type!([a-f0-9\-]{36})',  # Type reference: type!uuid
        ]
        
        def replace_uuid(match):
            uuid = match.group(1)
            obj = self.object_lookup.get(uuid)
            
            if obj:
                object_name = obj.get('name', uuid)
                object_type = obj.get('object_type', '')
                
                # Return appropriate format based on object type
                if object_type == 'Expression Rule':
                    return f'rule!{object_name}'
                elif object_type == 'Constant':
                    return f'cons!{object_name}'
                elif object_type == 'Interface':
                    return f'rule!{object_name}'
                else:
                    return f'rule!{object_name}'
            
            return match.group(0)  # Return original if not found
        
        # Apply all patterns
        for pattern in patterns:
            code = re.sub(pattern, replace_uuid, code)
        
        return code
    
    def _replace_appian_functions(self, code: str) -> str:
        """Replace a! and #"SYSTEM_*" function calls with public function names"""
        if not self.appian_functions:
            return code
        
        # Pattern 1: a!functionName( calls
        pattern1 = r'a!([a-zA-Z][a-zA-Z0-9_]*)\s*\('
        
        # Pattern 2: #"SYSTEM_SYSRULES_functionName"( calls
        pattern2 = r'#"SYSTEM_SYSRULES_([a-zA-Z][a-zA-Z0-9_]*)"?\s*\('
        
        def replace_a_function(match):
            internal_name = match.group(1)
            public_name = self.appian_functions.get(internal_name, internal_name)
            return f'a!{public_name}('
        
        def replace_system_function(match):
            internal_name = match.group(1)
            public_name = self.appian_functions.get(internal_name, internal_name)
            return f'a!{public_name}('
        
        # Apply both patterns
        code = re.sub(pattern1, replace_a_function, code)
        code = re.sub(pattern2, replace_system_function, code)
        
        return code
    
    def _clean_formatting(self, code: str) -> str:
        """Clean up code formatting"""
        # Remove excessive whitespace while preserving structure
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove trailing whitespace but preserve indentation
            cleaned_line = line.rstrip()
            if cleaned_line or (cleaned_lines and cleaned_lines[-1].strip()):
                cleaned_lines.append(cleaned_line)
        
        # Remove excessive empty lines (more than 2 consecutive)
        result_lines = []
        empty_count = 0
        
        for line in cleaned_lines:
            if line.strip():
                result_lines.append(line)
                empty_count = 0
            else:
                empty_count += 1
                if empty_count <= 2:
                    result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _format_node_sections(self, logic: str) -> str:
        """Format process model node sections with proper separation"""
        # Split by node headers and reformat
        node_sections = re.split(r'(=== NODE: [^=]+ ===)', logic)
        formatted_sections = []
        
        for i, section in enumerate(node_sections):
            if section.startswith('=== NODE:'):
                # This is a node header
                formatted_sections.append(f'\n{section}\n')
            elif section.strip():
                # This is node content - format with proper line breaks
                lines = section.strip().split('\n')
                formatted_lines = []
                
                for line in lines:
                    line = line.strip()
                    if line:
                        # Add proper indentation for readability
                        if ':' in line and not line.startswith('  '):
                            formatted_lines.append(f'  {line}')
                        else:
                            formatted_lines.append(f'    {line}')
                
                if formatted_lines:
                    formatted_sections.append('\n'.join(formatted_lines))
        
        return ''.join(formatted_sections).strip()
