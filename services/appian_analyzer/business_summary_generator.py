"""
Business Summary Generator for Appian Objects
Generates human-readable business summaries from SAIL code analysis
"""

import re
import json
from typing import Dict, List, Any, Optional

class BusinessSummaryGenerator:
    """Generates business summaries from SAIL code using pattern analysis"""
    
    def __init__(self, object_lookup: Dict[str, Dict], blueprint_data: Dict):
        self.object_lookup = object_lookup
        self.blueprint_data = blueprint_data
        self.sail_patterns = self._load_sail_patterns()
    
    def _load_sail_patterns(self) -> Dict[str, List[str]]:
        """Load SAIL patterns for business logic extraction"""
        return {
            'data_operations': [
                r'a!save\s*\(',
                r'a!update\s*\(',
                r'a!writeToDataStoreEntity\s*\(',
                r'a!deleteFromDataStoreEntity\s*\(',
                r'a!queryRecordType\s*\(',
                r'a!queryEntity\s*\(',
                r'a!writeRecords\s*\(',
                r'a!deleteRecords\s*\('
            ],
            'validations': [
                r'a!validationMessage\s*\(',
                r'required\s*:\s*true',
                r'validations\s*:',
                r'if\s*\([^,]*,\s*"[^"]*error[^"]*"',
                r'requiredMessage\s*:',
                r'validate\s*:\s*true'
            ],
            'user_interactions': [
                r'a!buttonWidget\s*\(',
                r'a!textField\s*\(',
                r'a!dropdownField\s*\(',
                r'a!fileUploadField\s*\(',
                r'a!gridField\s*\(',
                r'a!dynamicLink\s*\(',
                r'a!checkboxField\s*\(',
                r'a!radioButtonField\s*\(',
                r'a!dateField\s*\(',
                r'a!paragraphField\s*\('
            ],
            'business_logic': [
                r'if\s*\(',
                r'a!match\s*\(',
                r'choose\s*\(',
                r'and\s*\(',
                r'or\s*\(',
                r'a!forEach\s*\(',
                r'apply\s*\(',
                r'filter\s*\('
            ],
            'calculations': [
                r'sum\s*\(',
                r'average\s*\(',
                r'count\s*\(',
                r'max\s*\(',
                r'min\s*\(',
                r'length\s*\(',
                r'round\s*\(',
                r'abs\s*\(',
                r'\+|\-|\*|\/|\%'
            ],
            'integrations': [
                r'rule!\w+',
                r'cons!\w+',
                r'a!startProcessLink\s*\(',
                r'a!recordLink\s*\(',
                r'#"[^"]*"\s*\('
            ],
            'data_display': [
                r'a!gridLayout\s*\(',
                r'a!richTextDisplayField\s*\(',
                r'a!cardLayout\s*\(',
                r'a!columnsLayout\s*\(',
                r'a!sectionLayout\s*\('
            ]
        }
    
    def generate_summary(self, obj: Dict[str, Any]) -> str:
        """Generate business summary for a single object"""
        obj_type = obj.get('type', 'Unknown')
        obj_name = obj.get('name', 'Unknown')
        sail_code = obj.get('sail_code', '')
        
        if not sail_code:
            return f"=== BUSINESS SUMMARY ===\nObject: {obj_name} ({obj_type})\nNo SAIL code available for analysis.\n"
        
        # Extract patterns from SAIL code
        patterns = self._extract_patterns(sail_code)
        
        # Get related objects
        related_objects = self._get_related_objects(obj.get('uuid', ''))
        
        # Generate structured summary
        summary = self._build_summary(obj_name, obj_type, patterns, related_objects)
        
        return summary
    
    def _extract_patterns(self, sail_code: str) -> Dict[str, List[str]]:
        """Extract business patterns from SAIL code"""
        extracted = {}
        
        for category, pattern_list in self.sail_patterns.items():
            matches = []
            for pattern in pattern_list:
                found = re.findall(pattern, sail_code, re.IGNORECASE | re.MULTILINE)
                matches.extend(found)
            extracted[category] = list(set(matches))  # Remove duplicates
        
        return extracted
    
    def _get_related_objects(self, obj_uuid: str) -> List[str]:
        """Get related objects from blueprint data"""
        related = []
        
        # Find objects that reference this UUID
        for uuid, obj_info in self.object_lookup.items():
            if uuid != obj_uuid and obj_uuid in str(obj_info):
                related.append(obj_info.get('name', uuid))
        
        return related[:10]  # Limit to top 10 related objects
    
    def _build_summary(self, name: str, obj_type: str, patterns: Dict, related: List[str]) -> str:
        """Build formatted business summary"""
        summary = f"=== BUSINESS SUMMARY ===\n"
        summary += f"Object: {name} ({obj_type})\n"
        summary += f"Purpose: {self._infer_purpose(patterns, obj_type)}\n\n"
        
        # Data Operations
        if patterns.get('data_operations'):
            summary += "Data Operations:\n"
            for op in patterns['data_operations'][:5]:  # Limit to top 5
                summary += f"- {self._describe_data_operation(op)}\n"
            if len(patterns['data_operations']) > 5:
                summary += f"- ... and {len(patterns['data_operations']) - 5} more data operations\n"
            summary += "\n"
        
        # Business Logic
        if patterns.get('business_logic'):
            summary += "Business Logic:\n"
            for logic in patterns['business_logic'][:5]:
                summary += f"- {self._describe_business_logic(logic)}\n"
            if len(patterns['business_logic']) > 5:
                summary += f"- ... and {len(patterns['business_logic']) - 5} more logic patterns\n"
            summary += "\n"
        
        # User Experience
        if patterns.get('user_interactions'):
            summary += "User Experience:\n"
            ui_types = {}
            for ui in patterns['user_interactions']:
                ui_desc = self._describe_user_interaction(ui)
                ui_types[ui_desc] = ui_types.get(ui_desc, 0) + 1
            
            for ui_desc, count in ui_types.items():
                if count > 1:
                    summary += f"- {ui_desc} ({count} instances)\n"
                else:
                    summary += f"- {ui_desc}\n"
            summary += "\n"
        
        # Data Display
        if patterns.get('data_display'):
            summary += "Data Display:\n"
            for display in patterns['data_display'][:3]:
                summary += f"- {self._describe_data_display(display)}\n"
            summary += "\n"
        
        # Validations
        if patterns.get('validations'):
            summary += "Validations & Rules:\n"
            validation_count = len(patterns['validations'])
            summary += f"- {validation_count} validation rule(s) implemented\n"
            for val in patterns['validations'][:3]:
                summary += f"- {self._describe_validation(val)}\n"
            summary += "\n"
        
        # Calculations
        if patterns.get('calculations'):
            calc_count = len(patterns['calculations'])
            summary += "Calculations:\n"
            summary += f"- {calc_count} mathematical operation(s) detected\n"
            summary += "- Includes arithmetic, aggregation, or mathematical functions\n\n"
        
        # Integration Points
        if patterns.get('integrations') or related:
            summary += "Integration Points:\n"
            
            # Group integrations by type
            rules = [i for i in patterns.get('integrations', []) if i.startswith('rule!')]
            constants = [i for i in patterns.get('integrations', []) if i.startswith('cons!')]
            external_refs = [i for i in patterns.get('integrations', []) if i.startswith('#')]
            
            if rules:
                summary += f"- Calls {len(rules)} business rule(s): {', '.join(rules[:3])}\n"
                if len(rules) > 3:
                    summary += f"  ... and {len(rules) - 3} more rules\n"
            
            if constants:
                summary += f"- Uses {len(constants)} constant(s): {', '.join(constants[:3])}\n"
            
            if external_refs:
                summary += f"- References {len(external_refs)} external object(s)\n"
            
            if related:
                summary += f"- Related to: {', '.join(related[:3])}\n"
            summary += "\n"
        
        return summary
    
    def _infer_purpose(self, patterns: Dict, obj_type: str) -> str:
        """Infer object purpose from patterns"""
        if obj_type == 'Interface':
            if patterns.get('data_operations'):
                return "Data entry and management interface with database operations"
            elif patterns.get('user_interactions') and patterns.get('validations'):
                return "Form interface for user input with validation"
            elif patterns.get('data_display'):
                return "Data presentation and display interface"
            elif patterns.get('user_interactions'):
                return "Interactive user interface for data input"
            else:
                return "Display interface for information presentation"
        elif obj_type == 'Expression Rule':
            if patterns.get('data_operations'):
                return "Data processing rule with database operations"
            elif patterns.get('calculations'):
                return "Business calculation and mathematical processing rule"
            elif patterns.get('business_logic'):
                return "Business logic and decision processing rule"
            elif patterns.get('validations'):
                return "Data validation and verification rule"
            else:
                return "Utility rule for data processing and transformation"
        elif obj_type == 'Process Model':
            return "Automated workflow for business process execution"
        elif obj_type == 'Constant':
            return "Configuration constant for application settings"
        else:
            return f"{obj_type} for business functionality"
    
    def _describe_data_operation(self, operation: str) -> str:
        """Describe data operation in business terms"""
        if 'save' in operation.lower():
            return "Saves data to database"
        elif 'update' in operation.lower():
            return "Updates existing records"
        elif 'delete' in operation.lower():
            return "Removes data from system"
        elif 'query' in operation.lower():
            return "Retrieves data from database"
        else:
            return f"Data operation: {operation}"
    
    def _describe_business_logic(self, logic: str) -> str:
        """Describe business logic in human terms"""
        if logic.startswith('if'):
            return "Conditional decision making"
        elif 'match' in logic.lower():
            return "Multi-condition branching logic"
        elif 'choose' in logic.lower():
            return "Selection-based decision logic"
        elif logic.startswith('and'):
            return "Multiple condition validation"
        elif logic.startswith('or'):
            return "Alternative condition checking"
        elif 'forEach' in logic:
            return "Iterative data processing"
        else:
            return f"Business logic: {logic}"
    
    def _describe_user_interaction(self, ui: str) -> str:
        """Describe user interaction components"""
        if 'button' in ui.lower():
            return "Action button for user interaction"
        elif 'textField' in ui:
            return "Text input field"
        elif 'dropdown' in ui.lower():
            return "Selection dropdown menu"
        elif 'fileUpload' in ui:
            return "File upload capability"
        elif 'grid' in ui.lower():
            return "Data grid for tabular display"
        elif 'link' in ui.lower():
            return "Navigation or action link"
        else:
            return f"User interface component: {ui}"
    
    def _describe_validation(self, validation: str) -> str:
        """Describe validation rules"""
        if 'required' in validation.lower():
            return "Required field validation"
        elif 'validationMessage' in validation:
            return "Custom validation with error message"
        elif 'error' in validation.lower():
            return "Error condition validation"
        else:
            return f"Data validation: {validation}"
    
    def _describe_data_display(self, display: str) -> str:
        """Describe data display components"""
        if 'gridLayout' in display:
            return "Grid layout for structured data presentation"
        elif 'richTextDisplayField' in display:
            return "Rich text display for formatted content"
        elif 'cardLayout' in display:
            return "Card-based layout for organized information"
        elif 'columnsLayout' in display:
            return "Multi-column layout for data organization"
        elif 'sectionLayout' in display:
            return "Section-based layout for content grouping"
        else:
            return f"Display component: {display}"
    
    def _describe_integration(self, integration: str) -> str:
        """Describe integration points"""
        if 'startProcessLink' in integration:
            return "Triggers business process workflow"
        elif integration.startswith('rule!'):
            return f"Calls business rule: {integration}"
        elif integration.startswith('cons!'):
            return f"Uses constant: {integration}"
        elif integration.startswith('#'):
            return "References external object"
        else:
            return f"Integration: {integration}"
    
    def generate_batch_summaries(self, objects: List[Dict], batch_size: int = 10) -> Dict[str, str]:
        """Generate summaries for a batch of objects"""
        summaries = {}
        
        for i, obj in enumerate(objects[:batch_size]):
            obj_name = obj.get('name', f'Object_{i}')
            try:
                summaries[obj_name] = self.generate_summary(obj)
                print(f"Generated summary for: {obj_name}")
            except Exception as e:
                summaries[obj_name] = f"Error generating summary: {str(e)}"
                print(f"Error processing {obj_name}: {str(e)}")
        
        return summaries
    
    def save_summaries_to_file(self, summaries: Dict[str, str], filename: str):
        """Save generated summaries to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("APPIAN APPLICATION BUSINESS SUMMARIES\n")
            f.write("=" * 50 + "\n\n")
            
            for obj_name, summary in summaries.items():
                f.write(summary)
                f.write("\n" + "-" * 80 + "\n\n")
        
        print(f"Summaries saved to: {filename}")
