"""
Package Extraction Service

Handles extraction and parsing of Appian packages (ZIP files).
Stores objects in the global object_lookup registry and creates package-object mappings.
"""

import os
import json
import tempfile
import zipfile
import time
from typing import Dict, Any, List, Optional

from core.base_service import BaseService
from core.logger import get_merge_logger, LoggerConfig
from models import db, Package, ObjectLookup, ObjectVersion, PackageObjectMapping
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.package_object_mapping_repository import PackageObjectMappingRepository
from services.parsers.xml_parser_factory import XMLParserFactory
from services.sail_formatter import SAILFormatter


class PackageExtractionService(BaseService):
    """
    Service for extracting and parsing Appian packages.
    
    This service handles the complete workflow of:
    1. Extracting ZIP files
    2. Parsing XML files
    3. Storing objects in object_lookup (NO DUPLICATES!)
    4. Creating package_object_mappings
    5. Storing object-specific data
    6. Storing version data
    
    Key Design Principles:
    - Each object stored once in object_lookup (use find_or_create)
    - Package-object relationships tracked via package_object_mappings
    - Object-specific data stored in type-specific tables
    - Version data stored in object_versions
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = get_merge_logger()
        self.object_lookup_cache = {}
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.object_lookup_repo = self._get_repository(ObjectLookupRepository)
        self.package_object_mapping_repo = self._get_repository(PackageObjectMappingRepository)
        self.parser_factory = XMLParserFactory()
        # Initialize SAIL formatter (not a service, just a utility class)
        self.sail_formatter = SAILFormatter()
        self.sail_formatter._initialize_dependencies()
    
    def _ensure_not_none(self, value: Any, default: str = 'Unknown') -> str:
        """
        Ensure a value is not None or empty string.
        
        This prevents NOT NULL constraint violations in the database.
        
        Args:
            value: Value to check
            default: Default value if None or empty
            
        Returns:
            Original value or default
        """
        if value is None or value == '':
            return default
        return value
    
    def extract_package(
        self,
        session_id: int,
        zip_path: str,
        package_type: str
    ) -> Package:
        """
        Extract package and store all objects.
        
        This is the main entry point for package extraction. It follows a 7-step workflow:
        1. Create package record
        2. Extract ZIP to temp directory
        3. Find all XML files
        4. Parse each XML file
        5. For each object:
           a. Find or create in object_lookup (NO DUPLICATES!)
           b. Create package_object_mapping
           c. Store object-specific data in object tables
           d. Store version data in object_versions
        6. Update package statistics
        7. Clean up temp directory
        
        Args:
            session_id: Merge session ID
            zip_path: Path to ZIP file
            package_type: Package type (base, customized, new_vendor)
            
        Returns:
            Package object with total_objects count
            
        Raises:
            PackageExtractionException: If extraction fails
            
        Example:
            >>> service = PackageExtractionService()
            >>> package = service.extract_package(
            ...     session_id=1,
            ...     zip_path="/path/to/package.zip",
            ...     package_type="base"
            ... )
            >>> print(f"Extracted {package.total_objects} objects")
        """
        extraction_start = time.time()
        
        LoggerConfig.log_function_entry(
            self.logger,
            'extract_package',
            session_id=session_id,
            zip_path=zip_path,
            package_type=package_type
        )
        
        self.logger.info(f"Starting extraction of {package_type} package: {zip_path}")
        
        # Step 1: Create package record
        self.logger.debug(f"Creating package record for session_id={session_id}")
        package = Package(
            session_id=session_id,
            package_type=package_type,
            filename=os.path.basename(zip_path),
            total_objects=0
        )
        db.session.add(package)
        db.session.flush()
        self.logger.debug(f"Package record created with id={package.id}")
        
        temp_dir = None
        try:
            # Step 2: Extract ZIP to temp directory
            step_start = time.time()
            temp_dir = tempfile.mkdtemp(prefix=f"appian_pkg_{package.id}_")
            self.logger.debug(f"Created temp directory: {temp_dir}")
            
            self._extract_zip(zip_path, temp_dir)
            
            step_duration = time.time() - step_start
            self.logger.debug(f"ZIP extraction completed in {step_duration:.2f}s")
            
            # Step 3: Find all XML files
            step_start = time.time()
            xml_files = self._find_xml_files(temp_dir)
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"Found {len(xml_files)} XML/XSD files in {step_duration:.2f}s"
            )
            
            # Step 4-5: Parse each XML file and process objects
            objects_processed = 0
            objects_failed = 0
            object_type_counts = {}
            
            self.logger.debug("Starting object processing")
            
            for idx, xml_file in enumerate(xml_files, 1):
                try:
                    if idx % 10 == 0:
                        self.logger.debug(f"Processing file {idx}/{len(xml_files)}")
                    
                    obj_lookup = self._process_object(package.id, xml_file)
                    
                    if obj_lookup:
                        objects_processed += 1
                        # Track object type counts
                        obj_type = obj_lookup.object_type
                        object_type_counts[obj_type] = object_type_counts.get(obj_type, 0) + 1
                    else:
                        objects_failed += 1
                        
                except Exception as e:
                    objects_failed += 1
                    self.logger.warning(
                        f"Failed to process {os.path.basename(xml_file)}: {e}"
                    )
                    # Continue with next file
            
            # Log object type breakdown
            if object_type_counts:
                self.logger.info(f"Object type breakdown for {package_type} package:")
                for obj_type, count in sorted(object_type_counts.items()):
                    self.logger.info(f"  - {obj_type}: {count}")
            
            if objects_failed > 0:
                self.logger.warning(
                    f"Failed to process {objects_failed} files "
                    f"({objects_failed}/{len(xml_files)})"
                )
            
            # Step 6: Update package statistics
            package.total_objects = objects_processed
            db.session.flush()
            
            # Step 6.5: Format SAIL code with UUID resolution
            self.logger.info("Formatting SAIL code with UUID resolution...")
            self._format_sail_code_for_package(package.id, session_id)
            
            extraction_duration = time.time() - extraction_start
            
            LoggerConfig.log_performance(
                self.logger,
                f'Package Extraction ({package_type})',
                extraction_duration,
                package_id=package.id,
                total_files=len(xml_files),
                objects_processed=objects_processed,
                objects_failed=objects_failed
            )
            
            self.logger.info(
                f"Successfully extracted {objects_processed} objects "
                f"from {package_type} package"
            )
            
            LoggerConfig.log_function_exit(
                self.logger,
                'extract_package',
                result=f"{objects_processed} objects extracted"
            )
            
            return package
            
        except Exception as e:
            extraction_duration = time.time() - extraction_start
            
            LoggerConfig.log_error_with_context(
                self.logger,
                e,
                'Package extraction',
                session_id=session_id,
                package_id=package.id if package else None,
                package_type=package_type,
                zip_path=zip_path,
                extraction_duration=f"{extraction_duration:.2f}s"
            )
            
            raise PackageExtractionException(f"Failed to extract package: {e}")
        
        finally:
            # Step 7: Clean up temp directory
            if temp_dir and os.path.exists(temp_dir):
                self._cleanup_temp_dir(temp_dir)
    
    def _extract_zip(self, zip_path: str, extract_to: str) -> None:
        """
        Extract ZIP file to directory.
        
        Args:
            zip_path: Path to ZIP file
            extract_to: Directory to extract to
            
        Raises:
            PackageExtractionException: If extraction fails
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        except Exception as e:
            raise PackageExtractionException(f"Failed to extract ZIP: {e}")
    
    def _find_xml_files(self, directory: str) -> List[str]:
        """
        Find all XML and XSD files in directory recursively.
        
        CDTs are stored as .xsd files, while other objects use .xml files.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of XML and XSD file paths
        """
        xml_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.xml') or file.endswith('.xsd'):
                    xml_files.append(os.path.join(root, file))
        return xml_files
    
    def _process_object(
        self,
        package_id: int,
        xml_path: str
    ) -> Optional[ObjectLookup]:
        """
        Process single object from XML file.
        
        This method:
        1. Parses XML to extract object data
        2. Finds or creates object in object_lookup (NO DUPLICATES!)
        3. Creates package_object_mapping
        4. Stores object-specific data
        5. Stores version data in object_versions
        
        Args:
            package_id: Package ID
            xml_path: Path to XML file
            
        Returns:
            ObjectLookup object if successful, None if parsing fails
        """
        try:
            # Determine object type from XML
            object_type = self._determine_object_type(xml_path)
            
            # Get appropriate parser
            parser = self.parser_factory.get_parser(object_type)
            
            # Parse XML
            try:
                parsed_data = parser.parse(xml_path)
            except Exception as parse_error:
                self.logger.warning(
                    f"Failed to parse {xml_path} as {object_type}: {parse_error}"
                )
                return None
            
            if not parsed_data or not parsed_data.get('uuid'):
                self.logger.warning(
                    f"No UUID found in {xml_path}. "
                    f"Parsed data keys: {list(parsed_data.keys()) if parsed_data else 'None'}"
                )
                return None
            
            # Step 5a: Find or create in object_lookup (CRITICAL - NO DUPLICATES!)
            obj_lookup = self.object_lookup_repo.find_or_create(
                uuid=parsed_data['uuid'],
                name=parsed_data.get('name', 'Unknown'),
                object_type=object_type,
                description=parsed_data.get('description')
            )
            
            # Step 5b: Create package_object_mapping
            self.package_object_mapping_repo.create_mapping(
                package_id=package_id,
                object_id=obj_lookup.id
            )
            
            # Step 5c: Store object-specific data
            self._store_object_specific_data(obj_lookup.id, package_id, object_type, parsed_data)
            
            # Step 5d: Store version data in object_versions
            self._store_version_data(obj_lookup.id, package_id, parsed_data)
            
            return obj_lookup
            
        except Exception as e:
            self.logger.error(f"Failed to process object from {xml_path}: {e}")
            raise
    
    def _determine_object_type(self, xml_path: str) -> str:
        """
        Determine object type from XML/XSD file.
        
        Looks at the root element name to determine the object type.
        Appian XML files use "Haul" suffix (e.g., groupHaul, processModelHaul).
        For contentHaul, looks at child elements to determine actual type.
        XSD files are CDTs (Custom Data Types).
        
        Args:
            xml_path: Path to XML or XSD file
            
        Returns:
            Object type string (e.g., 'Interface', 'Process Model', 'CDT')
        """
        import xml.etree.ElementTree as ET
        
        # XSD files are always CDTs
        if xml_path.endswith('.xsd'):
            return 'CDT'
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Remove namespace if present
            tag = root.tag
            if '}' in tag:
                tag = tag.split('}')[1]
            
            # Special handling for contentHaul - look at child elements
            if tag == 'contentHaul':
                # Check for specific child elements
                for child in root:
                    child_tag = child.tag
                    if '}' in child_tag:
                        child_tag = child_tag.split('}')[1]
                    
                    child_type_mapping = {
                        'interface': 'Interface',
                        'expressionRule': 'Expression Rule',
                        'rule': 'Expression Rule',  # Expression rules use 'rule' tag
                        'constant': 'Constant',
                        'integration': 'Integration',
                        'webApi': 'Web API',
                        'rulesFolder': 'Unknown',  # Folders are not objects we track
                        'dataStore': 'Unknown',  # Data stores handled separately
                    }
                    
                    if child_tag in child_type_mapping:
                        return child_type_mapping[child_tag]
            
            # Map XML tag to object type
            # Appian uses "Haul" suffix for most objects
            type_mapping = {
                'interfaceHaul': 'Interface',
                'expressionRuleHaul': 'Expression Rule',
                'processModelHaul': 'Process Model',
                'recordTypeHaul': 'Record Type',
                'dataTypeHaul': 'CDT',
                'integrationHaul': 'Integration',
                'webApiHaul': 'Web API',
                'siteHaul': 'Site',
                'groupHaul': 'Group',
                'constantHaul': 'Constant',
                'connectedSystemHaul': 'Connected System',
                # Also support without Haul suffix
                'interface': 'Interface',
                'expressionRule': 'Expression Rule',
                'processModel': 'Process Model',
                'recordType': 'Record Type',
                'dataType': 'CDT',
                'integration': 'Integration',
                'webApi': 'Web API',
                'site': 'Site',
                'group': 'Group',
                'constant': 'Constant',
                'connectedSystem': 'Connected System',
            }
            
            return type_mapping.get(tag, 'Unknown')
            
        except Exception as e:
            self.logger.warning(f"Could not determine object type for {xml_path}: {e}")
            return 'Unknown'
    
    def _store_object_specific_data(
        self,
        object_id: int,
        package_id: int,
        object_type: str,
        parsed_data: Dict[str, Any]
    ) -> None:
        """
        Store object-specific data in type-specific tables.
        
        This method stores detailed object data in the appropriate table
        based on object type (interfaces, process_models, etc.).
        
        Args:
            object_id: Object ID from object_lookup
            package_id: Package ID
            object_type: Object type
            parsed_data: Parsed data from XML
        """
        # Import models dynamically to avoid circular imports
        from models import (
            Interface, InterfaceParameter, InterfaceSecurity,
            ExpressionRule, ExpressionRuleInput,
            ProcessModel, ProcessModelNode, ProcessModelFlow, ProcessModelVariable,
            RecordType, RecordTypeField, RecordTypeRelationship,
            RecordTypeView, RecordTypeAction,
            CDT, CDTField,
            Integration, WebAPI, Site, Group, Constant, ConnectedSystem,
            UnknownObject
        )
        
        try:
            if object_type == 'Interface':
                self._store_interface_data(object_id, package_id, parsed_data)
            elif object_type == 'Expression Rule':
                self._store_expression_rule_data(object_id, package_id, parsed_data)
            elif object_type == 'Process Model':
                self._store_process_model_data(object_id, package_id, parsed_data)
            elif object_type == 'Record Type':
                self._store_record_type_data(object_id, package_id, parsed_data)
            elif object_type == 'CDT':
                self._store_cdt_data(object_id, package_id, parsed_data)
            elif object_type == 'Integration':
                self._store_integration_data(object_id, package_id, parsed_data)
            elif object_type == 'Web API':
                self._store_web_api_data(object_id, package_id, parsed_data)
            elif object_type == 'Site':
                self._store_site_data(object_id, package_id, parsed_data)
            elif object_type == 'Group':
                self._store_group_data(object_id, package_id, parsed_data)
            elif object_type == 'Constant':
                self._store_constant_data(object_id, package_id, parsed_data)
            elif object_type == 'Connected System':
                self._store_connected_system_data(object_id, package_id, parsed_data)
            else:
                self._store_unknown_object_data(object_id, package_id, parsed_data)
                
        except Exception as e:
            self.logger.error(f"Failed to store {object_type} data: {e}")
            # Don't raise - we still want to continue processing
    
    def _store_version_data(
        self,
        object_id: int,
        package_id: int,
        parsed_data: Dict[str, Any]
    ) -> None:
        """
        Store version data in object_versions table.
        
        Args:
            object_id: Object ID from object_lookup
            package_id: Package ID
            parsed_data: Parsed data from XML
        """
        version = ObjectVersion(
            object_id=object_id,
            package_id=package_id,
            version_uuid=parsed_data.get('version_uuid'),
            sail_code=parsed_data.get('sail_code'),
            fields=json.dumps(parsed_data.get('fields', [])) if parsed_data.get('fields') else None,
            properties=json.dumps(parsed_data.get('properties', {})) if parsed_data.get('properties') else None,
            raw_xml=parsed_data.get('raw_xml')
        )
        db.session.add(version)
        db.session.flush()
    
    def _cleanup_temp_dir(self, temp_dir: str) -> None:
        """
        Clean up temporary directory.
        
        Args:
            temp_dir: Directory to clean up
        """
        try:
            import shutil
            shutil.rmtree(temp_dir)
            self.logger.info(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            self.logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
    
    def _format_sail_code_for_package(self, package_id: int, session_id: int) -> None:
        """
        Format SAIL code for all objects in a package with UUID resolution.
        
        This method:
        1. Builds object lookup cache from all packages in the session
        2. Formats SAIL code in object_versions table
        3. Formats SAIL code in object-specific tables (interfaces, expression_rules, etc.)
        
        Args:
            package_id: Package ID to format
            session_id: Session ID to build object lookup cache
        """
        try:
            format_start = time.time()
            
            # Build object lookup cache from all packages in session
            self.logger.debug("Building object lookup cache...")
            object_lookup_dict = self._build_object_lookup_cache(session_id)
            self.sail_formatter.set_object_lookup(object_lookup_dict)
            self.logger.debug(f"Object lookup cache built with {len(object_lookup_dict)} objects")
            
            # Format SAIL code in object_versions
            formatted_count = self._format_object_versions(package_id)
            
            # Format SAIL code in object-specific tables
            formatted_count += self._format_interfaces(package_id)
            formatted_count += self._format_expression_rules(package_id)
            formatted_count += self._format_integrations(package_id)
            formatted_count += self._format_web_apis(package_id)
            
            db.session.flush()
            
            format_duration = time.time() - format_start
            self.logger.info(
                f"Formatted SAIL code for {formatted_count} objects in {format_duration:.2f}s"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to format SAIL code: {e}")
            # Don't raise - formatting is optional enhancement
    
    def _build_object_lookup_cache(self, session_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Build object lookup cache for UUID resolution.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict mapping UUID -> {name, object_type}
        """
        from models import MergeSession, Package
        
        # Get all packages in session
        session = MergeSession.query.get(session_id)
        if not session:
            return {}
        
        # Query all objects from object_lookup that are in this session's packages
        objects = db.session.query(ObjectLookup).join(
            PackageObjectMapping,
            PackageObjectMapping.object_id == ObjectLookup.id
        ).join(
            Package,
            Package.id == PackageObjectMapping.package_id
        ).filter(
            Package.session_id == session_id
        ).distinct().all()
        
        # Build lookup dict
        lookup_dict = {}
        for obj in objects:
            lookup_dict[obj.uuid] = {
                'name': obj.name,
                'object_type': obj.object_type
            }
        
        return lookup_dict
    
    def _format_object_versions(self, package_id: int) -> int:
        """Format SAIL code in object_versions table."""
        versions = ObjectVersion.query.filter_by(package_id=package_id).all()
        formatted_count = 0
        
        for version in versions:
            if version.sail_code:
                try:
                    formatted_code = self.sail_formatter.format_sail_code(version.sail_code)
                    if formatted_code != version.sail_code:
                        version.sail_code = formatted_code
                        formatted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to format SAIL code for version {version.id}: {e}")
        
        return formatted_count
    
    def _format_interfaces(self, package_id: int) -> int:
        """Format SAIL code in interfaces table."""
        from models import Interface
        
        interfaces = Interface.query.filter_by(package_id=package_id).all()
        formatted_count = 0
        
        for interface in interfaces:
            if interface.sail_code:
                try:
                    formatted_code = self.sail_formatter.format_sail_code(interface.sail_code)
                    if formatted_code != interface.sail_code:
                        interface.sail_code = formatted_code
                        formatted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to format SAIL code for interface {interface.id}: {e}")
        
        return formatted_count
    
    def _format_expression_rules(self, package_id: int) -> int:
        """Format SAIL code in expression_rules table."""
        from models import ExpressionRule
        
        rules = ExpressionRule.query.filter_by(package_id=package_id).all()
        formatted_count = 0
        
        for rule in rules:
            if rule.sail_code:
                try:
                    formatted_code = self.sail_formatter.format_sail_code(rule.sail_code)
                    if formatted_code != rule.sail_code:
                        rule.sail_code = formatted_code
                        formatted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to format SAIL code for rule {rule.id}: {e}")
        
        return formatted_count
    
    def _format_integrations(self, package_id: int) -> int:
        """Format SAIL code in integrations table."""
        from models import Integration
        
        integrations = Integration.query.filter_by(package_id=package_id).all()
        formatted_count = 0
        
        for integration in integrations:
            if integration.sail_code:
                try:
                    formatted_code = self.sail_formatter.format_sail_code(integration.sail_code)
                    if formatted_code != integration.sail_code:
                        integration.sail_code = formatted_code
                        formatted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to format SAIL code for integration {integration.id}: {e}")
        
        return formatted_count
    
    def _format_web_apis(self, package_id: int) -> int:
        """Format SAIL code in web_apis table."""
        from models import WebAPI
        
        web_apis = WebAPI.query.filter_by(package_id=package_id).all()
        formatted_count = 0
        
        for web_api in web_apis:
            if web_api.sail_code:
                try:
                    formatted_code = self.sail_formatter.format_sail_code(web_api.sail_code)
                    if formatted_code != web_api.sail_code:
                        web_api.sail_code = formatted_code
                        formatted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to format SAIL code for web_api {web_api.id}: {e}")
        
        return formatted_count
    
    # Object-specific storage methods
    
    def _store_interface_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Interface-specific data."""
        from models import Interface, InterfaceParameter, InterfaceSecurity
        
        # Check if already exists (prevent duplicate insertion)
        existing = Interface.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"Interface already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        interface = Interface(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Interface'),
            version_uuid=data.get('version_uuid'),
            sail_code=data.get('sail_code'),
            description=data.get('description')
        )
        db.session.add(interface)
        db.session.flush()
        
        # Store parameters
        for param in data.get('parameters', []):
            param_obj = InterfaceParameter(
                interface_id=interface.id,
                parameter_name=param.get('name'),
                parameter_type=param.get('type'),
                is_required=param.get('required', False),
                default_value=param.get('default_value'),
                display_order=param.get('display_order', 0)
            )
            db.session.add(param_obj)
        
        # Store security
        for sec in data.get('security', []):
            sec_obj = InterfaceSecurity(
                interface_id=interface.id,
                role_name=sec.get('role_name'),
                permission_type=sec.get('permission_type')
            )
            db.session.add(sec_obj)
        
        db.session.flush()
    
    def _store_expression_rule_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Expression Rule-specific data."""
        from models import ExpressionRule, ExpressionRuleInput
        
        # Check if already exists (prevent duplicate insertion)
        existing = ExpressionRule.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"ExpressionRule already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        rule = ExpressionRule(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Expression Rule'),
            version_uuid=data.get('version_uuid'),
            sail_code=data.get('sail_code'),
            output_type=data.get('output_type'),
            description=data.get('description')
        )
        db.session.add(rule)
        db.session.flush()
        
        # Store inputs
        for inp in data.get('inputs', []):
            input_obj = ExpressionRuleInput(
                rule_id=rule.id,
                input_name=inp.get('name'),
                input_type=inp.get('type'),
                is_required=inp.get('required', False),
                default_value=inp.get('default_value'),
                display_order=inp.get('display_order', 0)
            )
            db.session.add(input_obj)
        
        db.session.flush()
    
    def _store_process_model_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Process Model-specific data."""
        from models import ProcessModel, ProcessModelNode, ProcessModelFlow, ProcessModelVariable
        
        # Check if already exists (prevent duplicate insertion)
        existing = ProcessModel.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"ProcessModel already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        pm = ProcessModel(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Process Model'),
            version_uuid=data.get('version_uuid'),
            description=data.get('description'),
            total_nodes=data.get('total_nodes', 0),
            total_flows=data.get('total_flows', 0),
            complexity_score=data.get('complexity_score')
        )
        db.session.add(pm)
        db.session.flush()
        
        # Store nodes
        node_map = {}  # Map node_id to database id
        for node in data.get('nodes', []):
            node_obj = ProcessModelNode(
                process_model_id=pm.id,
                node_id=node.get('node_id'),
                node_type=node.get('node_type'),
                node_name=node.get('node_name'),
                properties=json.dumps(node.get('properties', {}))
            )
            db.session.add(node_obj)
            db.session.flush()
            # Map both node_id (UUID) and gui_id to database id for flow lookups
            node_map[node.get('node_id')] = node_obj.id
            if node.get('gui_id'):
                node_map[node.get('gui_id')] = node_obj.id
        
        # Store flows
        for flow in data.get('flows', []):
            from_node_id = node_map.get(flow.get('from_node_id'))
            to_node_id = node_map.get(flow.get('to_node_id'))
            
            if from_node_id and to_node_id:
                flow_obj = ProcessModelFlow(
                    process_model_id=pm.id,
                    from_node_id=from_node_id,
                    to_node_id=to_node_id,
                    flow_label=flow.get('flow_label'),
                    flow_condition=flow.get('flow_condition')
                )
                db.session.add(flow_obj)
        
        # Store variables
        for var in data.get('variables', []):
            var_obj = ProcessModelVariable(
                process_model_id=pm.id,
                variable_name=var.get('variable_name'),
                variable_type=var.get('variable_type'),
                is_parameter=var.get('is_parameter', False),
                default_value=var.get('default_value')
            )
            db.session.add(var_obj)
        
        db.session.flush()
    
    def _store_record_type_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Record Type-specific data."""
        from models import RecordType, RecordTypeField, RecordTypeRelationship, RecordTypeView, RecordTypeAction
        
        # Check if already exists (prevent duplicate insertion)
        existing = RecordType.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"RecordType already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        rt = RecordType(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Record Type'),
            version_uuid=data.get('version_uuid'),
            description=data.get('description'),
            source_type=data.get('source_type')
        )
        db.session.add(rt)
        db.session.flush()
        
        # Store fields
        for field in data.get('fields', []):
            field_obj = RecordTypeField(
                record_type_id=rt.id,
                field_name=field.get('field_name'),
                field_type=field.get('field_type'),
                is_primary_key=field.get('is_primary_key', False),
                is_required=field.get('is_required', False),
                display_order=field.get('display_order', 0)
            )
            db.session.add(field_obj)
        
        # Store relationships
        for rel in data.get('relationships', []):
            rel_obj = RecordTypeRelationship(
                record_type_id=rt.id,
                relationship_name=rel.get('relationship_name'),
                related_record_uuid=rel.get('related_record_uuid'),
                relationship_type=rel.get('relationship_type')
            )
            db.session.add(rel_obj)
        
        # Store views
        for view in data.get('views', []):
            view_obj = RecordTypeView(
                record_type_id=rt.id,
                view_name=view.get('view_name'),
                view_type=view.get('view_type'),
                configuration=json.dumps(view.get('configuration', {}))
            )
            db.session.add(view_obj)
        
        # Store actions
        for action in data.get('actions', []):
            action_obj = RecordTypeAction(
                record_type_id=rt.id,
                action_name=action.get('action_name'),
                action_type=action.get('action_type'),
                configuration=json.dumps(action.get('configuration', {}))
            )
            db.session.add(action_obj)
        
        db.session.flush()
    
    def _store_cdt_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store CDT-specific data."""
        from models import CDT, CDTField
        
        # Check if already exists (prevent duplicate insertion)
        existing = CDT.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"CDT already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        cdt = CDT(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown CDT'),
            version_uuid=data.get('version_uuid'),
            namespace=data.get('namespace'),
            description=data.get('description')
        )
        db.session.add(cdt)
        db.session.flush()
        
        # Store fields
        for field in data.get('fields', []):
            field_obj = CDTField(
                cdt_id=cdt.id,
                field_name=field.get('field_name'),
                field_type=field.get('field_type'),
                is_list=field.get('is_list', False),
                is_required=field.get('is_required', False),
                display_order=field.get('display_order', 0)
            )
            db.session.add(field_obj)
        
        db.session.flush()
    
    def _store_integration_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Integration-specific data."""
        from models import Integration
        
        # Check if already exists (prevent duplicate insertion)
        existing = Integration.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"Integration already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        integration = Integration(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Integration'),
            version_uuid=data.get('version_uuid'),
            sail_code=data.get('sail_code'),
            connection_info=data.get('connection_info'),
            authentication_info=data.get('authentication_info'),
            endpoint=data.get('endpoint'),
            description=data.get('description')
        )
        db.session.add(integration)
        db.session.flush()
    
    def _store_web_api_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Web API-specific data."""
        from models import WebAPI
        
        # Check if already exists (prevent duplicate insertion)
        existing = WebAPI.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"WebAPI already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        web_api = WebAPI(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Web API'),
            version_uuid=data.get('version_uuid'),
            sail_code=data.get('sail_code'),
            endpoint=data.get('endpoint'),
            http_methods=json.dumps(data.get('http_methods', [])),
            description=data.get('description')
        )
        db.session.add(web_api)
        db.session.flush()
    
    def _store_site_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Site-specific data."""
        from models import Site
        
        # Check if already exists (prevent duplicate insertion)
        existing = Site.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"Site already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        site = Site(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Site'),
            version_uuid=data.get('version_uuid'),
            page_hierarchy=json.dumps(data.get('pages', [])),
            description=data.get('description')
        )
        db.session.add(site)
        db.session.flush()
    
    def _store_group_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Group-specific data."""
        from models import Group
        
        # Check if already exists (prevent duplicate insertion)
        existing = Group.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"Group already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        group = Group(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Group'),
            version_uuid=data.get('version_uuid'),
            members=json.dumps(data.get('members', [])),
            parent_group_uuid=data.get('parent_group_uuid'),
            description=data.get('description')
        )
        db.session.add(group)
        db.session.flush()
    
    def _store_constant_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Constant-specific data."""
        from models import Constant
        
        # Check if already exists (prevent duplicate insertion)
        existing = Constant.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"Constant already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        constant = Constant(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Constant'),
            version_uuid=data.get('version_uuid'),
            constant_value=data.get('value'),  # Parser returns 'value'
            constant_type=data.get('value_type'),  # Parser returns 'value_type'
            scope=data.get('scope'),
            description=data.get('description')
        )
        db.session.add(constant)
        db.session.flush()
    
    def _store_connected_system_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Connected System-specific data."""
        from models import ConnectedSystem
        
        # Check if already exists (prevent duplicate insertion)
        existing = ConnectedSystem.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"ConnectedSystem already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        cs = ConnectedSystem(
            object_id=object_id,
            package_id=package_id,
            uuid=data['uuid'],
            name=self._ensure_not_none(data.get('name'), 'Unknown Connected System'),
            version_uuid=data.get('version_uuid'),
            system_type=data.get('system_type'),
            properties=data.get('properties'),  # Already JSON string from parser
            description=data.get('description')
        )
        db.session.add(cs)
        db.session.flush()
    
    def _store_unknown_object_data(self, object_id: int, package_id: int, data: Dict[str, Any]) -> None:
        """Store Unknown object data."""
        from models import UnknownObject
        
        # Check if already exists (prevent duplicate insertion)
        existing = UnknownObject.query.filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if existing:
            self.logger.debug(f"UnknownObject already exists for object_id={object_id}, package_id={package_id}, skipping")
            return
        
        unknown = UnknownObject(
            object_id=object_id,
            package_id=package_id,
            uuid=data.get('uuid', 'unknown'),
            name=data.get('name', 'Unknown'),
            version_uuid=data.get('version_uuid'),
            raw_xml=data.get('raw_xml'),
            description=data.get('description')
        )
        db.session.add(unknown)
        db.session.flush()


class PackageExtractionException(Exception):
    """Exception raised when package extraction fails."""
    pass
