"""
Refactored Appian Application Analyzer with proper OOP design
"""
import zipfile
import xml.etree.ElementTree as ET
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .models import AppianObject, Blueprint, Site, RecordType, ProcessModel, SimpleObject
from .parsers import (
    XMLParser, SiteParser, RecordTypeParser, ProcessModelParser, 
    ContentParser, SimpleObjectParser
)
from .sail_formatter import SAILFormatter

class ObjectLookup:
    """Manages object lookup table"""
    
    def __init__(self):
        self._objects: Dict[str, AppianObject] = {}
        self._counter = 1
    
    def add_object(self, obj: AppianObject) -> None:
        """Add object to lookup"""
        if obj.uuid and obj.name and "DEPRECATED" not in obj.name.upper():
            obj_dict = asdict(obj)
            obj_dict['s_no'] = self._counter
            obj_dict['file_path'] = ""
            self._objects[obj.uuid] = obj_dict
            self._counter += 1
    
    def get_object(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Get object by UUID"""
        return self._objects.get(uuid)
    
    def resolve_name(self, uuid: str) -> str:
        """Resolve UUID to name"""
        if not uuid:
            return "Unknown"
        obj = self._objects.get(uuid)
        return obj["name"] if obj else f"Unknown ({uuid[:8]}...)"
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all objects"""
        return self._objects
    
    def count(self) -> int:
        """Get total object count"""
        return len(self._objects)

class AnalysisEngine:
    """Handles analysis logic and summary generation"""
    
    @staticmethod
    def generate_summary(blueprint: Blueprint, object_count: int) -> Dict[str, Any]:
        """Generate analysis summary"""
        return {
            "total_sites": len(blueprint.sites),
            "total_record_types": len(blueprint.record_types),
            "total_process_models": len(blueprint.process_models),
            "total_interfaces": len(blueprint.interfaces),
            "total_rules": len(blueprint.rules),
            "total_data_types": len(blueprint.data_types),
            "total_integrations": len(blueprint.integrations),
            "total_security_groups": len(blueprint.security_groups),
            "total_constants": len(blueprint.constants),
            "complexity_assessment": AnalysisEngine._assess_complexity(object_count),
            "recommendations": AnalysisEngine._generate_recommendations(blueprint)
        }
    
    @staticmethod
    def _assess_complexity(total_objects: int) -> str:
        """Assess application complexity"""
        if total_objects > 400:
            return "Very High"
        elif total_objects > 200:
            return "High"
        elif total_objects > 100:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def _generate_recommendations(blueprint: Blueprint) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if len(blueprint.record_types) > 50:
            recommendations.append("Consider data model consolidation - high number of record types detected")
        
        if len(blueprint.integrations) > 10:
            recommendations.append("Implement integration governance framework for better management")
        
        if len(blueprint.security_groups) > 100:
            recommendations.append("Review security group structure for consolidation opportunities")
        
        return recommendations

class AppianAnalyzer:
    """Main analyzer class with proper OOP design"""
    
    def __init__(self, zip_path: str):
        self.zip_path = zip_path
        self.zip_file = zipfile.ZipFile(zip_path, 'r')
        self.object_lookup = ObjectLookup()
        self.parsers = self._initialize_parsers()
    
    def _initialize_parsers(self) -> List[XMLParser]:
        """Initialize all parsers"""
        return [
            SiteParser(),
            RecordTypeParser(),
            ProcessModelParser(),
            ContentParser(),
            SimpleObjectParser("Security Group", "group/"),
            SimpleObjectParser("Connected System", "connectedSystem/"),
            SimpleObjectParser("Web API", "webApi/"),
            SimpleObjectParser("Report", "tempoReport/")
        ]
    
    def analyze(self) -> Dict[str, Any]:
        """Main analysis method"""
        print("🔍 Starting Appian Analysis...")
        
        # Step 1: Parse all objects
        print("📋 Parsing objects...")
        blueprint = self._parse_objects()
        
        # Step 2: Resolve object references
        print("🔗 Resolving references...")
        self._resolve_references(blueprint)
        
        # Step 3: Format SAIL code and business logic
        print("🎨 Formatting SAIL code...")
        self._format_sail_code(blueprint)
        
        # Step 4: Generate summary
        print("📊 Generating summary...")
        blueprint.summary = AnalysisEngine.generate_summary(blueprint, self.object_lookup.count())
        
        # Step 4: Create metadata
        blueprint.metadata = self._create_metadata()
        
        return {
            "blueprint": asdict(blueprint),
            "object_lookup": self.object_lookup.get_all()
        }
    
    def _parse_objects(self) -> Blueprint:
        """Parse all objects from ZIP file"""
        blueprint = Blueprint(
            metadata={},
            sites=[],
            record_types=[],
            process_models=[],
            interfaces=[],
            rules=[],
            data_types=[],
            integrations=[],
            security_groups=[],
            constants=[],
            summary={}
        )
        
        # First pass: Parse all objects to build lookup
        for file_path in self.zip_file.namelist():
            if file_path.endswith('.xml') and not file_path.startswith('META-INF/'):
                try:
                    content = self.zip_file.read(file_path).decode('utf-8')
                    root = ET.fromstring(content)
                    
                    # Find appropriate parser
                    for parser in self.parsers:
                        if parser.can_parse(file_path):
                            obj = parser.parse(root, file_path)
                            if obj:
                                self._add_to_blueprint(blueprint, obj)
                                self.object_lookup.add_object(obj)
                            break
                
                except Exception as e:
                    print(f"⚠️  Error processing {file_path}: {e}")
                    continue
        
        # Second pass: Re-parse process models with object lookup and SAIL formatter for enhanced parsing
        # Create SAIL formatter for process model parsing
        sail_formatter = SAILFormatter(self.object_lookup.get_all())
        
        for file_path in self.zip_file.namelist():
            if file_path.startswith('processModel/') and file_path.endswith('.xml'):
                try:
                    content = self.zip_file.read(file_path).decode('utf-8')
                    root = ET.fromstring(content)
                    
                    # Find process model parser and pass object lookup and SAIL formatter
                    for parser in self.parsers:
                        if parser.__class__.__name__ == 'ProcessModelParser':
                            parser.set_object_lookup(self.object_lookup.get_all())
                            parser.set_sail_formatter(sail_formatter)
                            obj = parser.parse(root, file_path)
                            if obj:
                                # Replace the existing process model in blueprint
                                for i, existing_pm in enumerate(blueprint.process_models):
                                    if existing_pm.uuid == obj.uuid:
                                        blueprint.process_models[i] = obj
                                        break
                            break
                
                except Exception as e:
                    print(f"⚠️  Error re-processing {file_path}: {e}")
                    continue
        
        print(f"📊 Parsed {self.object_lookup.count()} objects")
        return blueprint
    
    def _add_to_blueprint(self, blueprint: Blueprint, obj: AppianObject) -> None:
        """Add object to appropriate blueprint section"""
        if isinstance(obj, Site):
            blueprint.sites.append(obj)
        elif isinstance(obj, RecordType):
            blueprint.record_types.append(obj)
        elif isinstance(obj, ProcessModel):
            blueprint.process_models.append(obj)
        elif obj.object_type == "Interface":
            blueprint.interfaces.append(obj)
        elif obj.object_type == "Expression Rule":
            blueprint.rules.append(obj)
        elif obj.object_type == "Data Type":
            blueprint.data_types.append(obj)
        elif obj.object_type in ["Connected System", "Web API"]:
            blueprint.integrations.append(obj)
        elif obj.object_type == "Security Group":
            blueprint.security_groups.append(obj)
        elif obj.object_type == "Constant":
            blueprint.constants.append(obj)
    
    def _resolve_references(self, blueprint: Blueprint) -> None:
        """Resolve object references using lookup"""
        # Resolve site UI object names
        for site in blueprint.sites:
            for page in site.pages:
                for ui_obj in page["ui_objects"]:
                    ui_obj["name"] = self.object_lookup.resolve_name(ui_obj["uuid"])
        
        # Resolve record type relationships and actions
        for record in blueprint.record_types:
            for rel in record.relationships:
                rel["target_record"]["name"] = self.object_lookup.resolve_name(rel["target_record"]["uuid"])
            
            for action in record.actions:
                if action["target_process"]["uuid"]:
                    action["target_process"]["name"] = self.object_lookup.resolve_name(action["target_process"]["uuid"])
        
        # Resolve process model node interfaces
        for process in blueprint.process_models:
            for node in process.nodes:
                # Safely check for details and interface
                if isinstance(node, dict) and "details" in node:
                    details = node["details"]
                    if isinstance(details, dict) and "interface" in details:
                        interface_uuid = details["interface"]["uuid"]
                        details["interface"]["name"] = self.object_lookup.resolve_name(interface_uuid)
            
            # Resolve process model interfaces
            for interface in process.interfaces:
                interface["name"] = self.object_lookup.resolve_name(interface["uuid"])
            
            # Resolve process model rules
            for rule in process.rules:
                rule["name"] = self.object_lookup.resolve_name(rule["uuid"])
    
    def _format_sail_code(self, blueprint: Blueprint) -> None:
        """Format SAIL code for all objects using SAILFormatter"""
        formatter = SAILFormatter(self.object_lookup.get_all())
        
        # Format interfaces
        for interface in blueprint.interfaces:
            if interface.sail_code:
                interface.sail_code = formatter.format_sail_code(interface.sail_code)
                # Update object_lookup with formatted code
                obj = self.object_lookup.get_object(interface.uuid)
                if obj:
                    obj['sail_code'] = interface.sail_code
        
        # Format rules
        for rule in blueprint.rules:
            if rule.sail_code:
                rule.sail_code = formatter.format_sail_code(rule.sail_code)
                # Update object_lookup with formatted code
                obj = self.object_lookup.get_object(rule.uuid)
                if obj:
                    obj['sail_code'] = rule.sail_code
        
        # Format constants
        for constant in blueprint.constants:
            if constant.sail_code:
                constant.sail_code = formatter.format_sail_code(constant.sail_code)
                # Update object_lookup with formatted code
                obj = self.object_lookup.get_object(constant.uuid)
                if obj:
                    obj['sail_code'] = constant.sail_code
        
        # Format process models (special handling for business logic)
        for process in blueprint.process_models:
            if process.business_logic:
                process.business_logic = formatter.format_process_model_logic(process.business_logic)
                # Update object_lookup with formatted business logic
                obj = self.object_lookup.get_object(process.uuid)
                if obj:
                    obj['business_logic'] = process.business_logic
        
        # Format integrations
        for integration in blueprint.integrations:
            if integration.sail_code:
                integration.sail_code = formatter.format_sail_code(integration.sail_code)
                # Update object_lookup with formatted code
                obj = self.object_lookup.get_object(integration.uuid)
                if obj:
                    obj['sail_code'] = integration.sail_code
    
    def _create_metadata(self) -> Dict[str, Any]:
        """Create analysis metadata"""
        app_name = os.path.basename(self.zip_path).replace('.zip', '')
        return {
            "application_name": app_name,
            "total_objects": self.object_lookup.count(),
            "analysis_timestamp": "2025-11-03T12:06:39.395+05:30"
        }
    
    def close(self) -> None:
        """Close the ZIP file"""
        self.zip_file.close()

def main():
    """CLI entry point"""
    import sys
    import json
    import os
    
    if len(sys.argv) != 2:
        print("Usage: python3 -m services.appian_analyzer <appian_zip_file>")
        sys.exit(1)
    
    zip_path = sys.argv[1]
    
    if not os.path.exists(zip_path):
        print(f"❌ Error: File {zip_path} not found")
        sys.exit(1)
    
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract base name for output files
    base_name = os.path.basename(zip_path).replace('.zip', '')
    
    try:
        print(f"🚀 Starting Analysis of {base_name}")
        print("=" * 50)
        
        # Initialize analyzer
        analyzer = AppianAnalyzer(zip_path)
        
        # Perform analysis
        result = analyzer.analyze()
        blueprint = result["blueprint"]
        object_lookup = result["object_lookup"]
        
        # Generate output file paths
        json_output = os.path.join(output_dir, f"{base_name}_blueprint.json")
        lookup_output = os.path.join(output_dir, f"{base_name}_object_lookup.json")
        
        print(f"\n📝 Generating output files...")
        
        # Save files
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)
        
        with open(lookup_output, 'w', encoding='utf-8') as f:
            json.dump(object_lookup, f, indent=2, ensure_ascii=False)
        
        # Display summary
        summary = blueprint["summary"]
        print(f"\n✅ Analysis Complete!")
        print(f"📊 Summary:")
        print(f"   • Total Objects: {blueprint['metadata']['total_objects']}")
        print(f"   • Complexity: {summary['complexity_assessment']}")
        print(f"   • Sites: {summary['total_sites']}")
        print(f"   • Record Types: {summary['total_record_types']}")
        print(f"   • Process Models: {summary['total_process_models']}")
        print(f"   • Interfaces: {summary['total_interfaces']}")
        print(f"   • Rules: {summary['total_rules']}")
        print(f"   • Integrations: {summary['total_integrations']}")
        print(f"   • Security Groups: {summary['total_security_groups']}")
        
        print(f"\n📁 Generated Files:")
        print(f"   • {json_output}")
        print(f"   • {lookup_output}")
        
        if summary['recommendations']:
            print(f"\n💡 Key Recommendations:")
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        analyzer.close()
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
