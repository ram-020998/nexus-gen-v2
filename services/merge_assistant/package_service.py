"""
Package Service for normalizing blueprint data into database tables.

This service handles the extraction and normalization of Appian blueprint data
into the Package, AppianObject, ProcessModelMetadata, ProcessModelNode,
ProcessModelFlow, ObjectDependency, and PackageObjectTypeCount tables.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from models import (
    db, Package, AppianObject, PackageObjectTypeCount,
    ProcessModelMetadata, ProcessModelNode, ProcessModelFlow,
    ObjectDependency
)

logger = logging.getLogger(__name__)


class PackageService:
    """Service for managing Package and related records."""

    def __init__(self):
        """Initialize the PackageService."""
        pass

    def create_package_from_blueprint(
        self,
        session_id: int,
        package_type: str,
        blueprint_result: Dict[str, Any]
    ) -> Package:
        """
        Create Package and related records from blueprint.

        Args:
            session_id: ID of the merge session
            package_type: Type of package ('base', 'customized', 'new_vendor')
            blueprint_result: Complete blueprint dictionary from analyzer

        Returns:
            Package: Created package record

        Raises:
            ValueError: If blueprint structure is invalid
            Exception: If database operation fails
        """
        try:
            logger.info(
                f"Creating package for session {session_id}, "
                f"type: {package_type}"
            )

            # Extract metadata from blueprint
            blueprint = blueprint_result.get('blueprint', {})
            metadata = blueprint.get('metadata', {})

            # Extract package name
            package_name = metadata.get('package_name', 'Unknown')

            # Create Package record
            package = Package(
                session_id=session_id,
                package_type=package_type,
                package_name=package_name,
                total_objects=metadata.get('total_objects', 0),
                generation_time=metadata.get('generation_time')
            )

            db.session.add(package)
            db.session.flush()  # Get package ID

            logger.info(
                f"Created package {package.id} with "
                f"{package.total_objects} objects"
            )

            return package

        except Exception as e:
            logger.error(
                f"Error creating package from blueprint: {str(e)}",
                exc_info=True
            )
            raise

    def get_object_by_uuid(
        self,
        package_id: int,
        uuid: str
    ) -> Optional[AppianObject]:
        """
        Get object by UUID using indexed query.

        Args:
            package_id: ID of the package
            uuid: UUID of the object

        Returns:
            AppianObject or None if not found
        """
        return AppianObject.query.filter_by(
            package_id=package_id,
            uuid=uuid
        ).first()

    def get_objects_by_type(
        self,
        package_id: int,
        object_type: str
    ) -> List[AppianObject]:
        """
        Get all objects of specific type.

        Args:
            package_id: ID of the package
            object_type: Type of objects to retrieve

        Returns:
            List of AppianObject records
        """
        return AppianObject.query.filter_by(
            package_id=package_id,
            object_type=object_type
        ).all()

    def extract_and_create_objects(
        self,
        package: Package,
        object_lookup: Dict[str, Any]
    ) -> List[AppianObject]:
        """
        Extract objects from blueprint and create AppianObject records.

        Args:
            package: Package record to associate objects with
            object_lookup: Dictionary of objects from blueprint

        Returns:
            List of created AppianObject records

        Raises:
            Exception: If object creation fails
        """
        try:
            logger.info(
                f"Extracting {len(object_lookup)} objects "
                f"for package {package.id}"
            )

            objects = []
            for uuid, obj_data in object_lookup.items():
                # Extract basic object information
                appian_obj = AppianObject(
                    package_id=package.id,
                    uuid=uuid,
                    name=obj_data.get('name', ''),
                    object_type=obj_data.get('object_type', ''),
                    version_uuid=obj_data.get('version_uuid')
                )

                # Extract SAIL code if present
                if 'sail_code' in obj_data:
                    appian_obj.sail_code = obj_data['sail_code']

                # Extract fields if present (store as JSON)
                if 'fields' in obj_data:
                    appian_obj.fields = json.dumps(obj_data['fields'])

                # Extract properties if present (store as JSON)
                if 'properties' in obj_data:
                    appian_obj.properties = json.dumps(obj_data['properties'])

                # Extract metadata if present (store as JSON)
                # Exclude process_model_data as it's handled separately
                metadata = {}
                for key, value in obj_data.items():
                    if key not in [
                        'uuid', 'name', 'type', 'version_uuid',
                        'sail_code', 'fields', 'properties',
                        'process_model_data'
                    ]:
                        metadata[key] = value

                if metadata:
                    appian_obj.object_metadata = json.dumps(metadata)

                objects.append(appian_obj)

            # Batch insert all objects
            db.session.bulk_save_objects(objects)
            db.session.flush()

            logger.info(
                f"Created {len(objects)} AppianObject records "
                f"for package {package.id}"
            )

            return objects

        except Exception as e:
            logger.error(
                f"Error extracting objects: {str(e)}",
                exc_info=True
            )
            raise

    def extract_and_create_object_type_counts(
        self,
        package: Package,
        metadata: Dict[str, Any]
    ) -> List[PackageObjectTypeCount]:
        """
        Extract object type counts and create PackageObjectTypeCount records.

        Args:
            package: Package record to associate counts with
            metadata: Metadata dictionary from blueprint

        Returns:
            List of created PackageObjectTypeCount records

        Raises:
            Exception: If count creation fails
        """
        try:
            object_type_counts = metadata.get('object_type_counts', {})

            logger.info(
                f"Extracting {len(object_type_counts)} object type counts "
                f"for package {package.id}"
            )

            counts = []
            for object_type, count in object_type_counts.items():
                type_count = PackageObjectTypeCount(
                    package_id=package.id,
                    object_type=object_type,
                    count=count
                )
                counts.append(type_count)

            # Batch insert all counts
            db.session.bulk_save_objects(counts)
            db.session.flush()

            logger.info(
                f"Created {len(counts)} PackageObjectTypeCount records "
                f"for package {package.id}"
            )

            return counts

        except Exception as e:
            logger.error(
                f"Error extracting object type counts: {str(e)}",
                exc_info=True
            )
            raise

    def extract_and_create_process_models(
        self,
        package: Package,
        object_lookup: Dict[str, Any]
    ) -> int:
        """
        Extract process model data and create normalized records.

        Args:
            package: Package record
            object_lookup: Dictionary of objects from blueprint

        Returns:
            Number of process models processed

        Raises:
            Exception: If process model creation fails
        """
        try:
            process_model_count = 0

            for uuid, obj_data in object_lookup.items():
                # Only process Process Model objects (use 'object_type' not 'type')
                if obj_data.get('object_type') != 'Process Model':
                    continue

                # Process models have nodes and flows directly as fields
                nodes = obj_data.get('nodes', [])
                flows = obj_data.get('flows', [])
                
                # Skip if no enhanced data (no nodes or flows)
                if not nodes or not flows:
                    logger.warning(
                        f"Skipping process model {uuid} - no nodes or flows"
                    )
                    continue

                # Get the AppianObject record for this process model
                appian_obj = AppianObject.query.filter_by(
                    package_id=package.id,
                    uuid=uuid
                ).first()

                if not appian_obj:
                    logger.warning(
                        f"AppianObject not found for process model {uuid}"
                    )
                    continue

                # Calculate complexity score (simple heuristic based on nodes and flows)
                complexity_score = len(nodes) + len(flows) * 0.5

                pm_metadata = ProcessModelMetadata(
                    appian_object_id=appian_obj.id,
                    total_nodes=len(nodes),
                    total_flows=len(flows),
                    complexity_score=complexity_score
                )
                db.session.add(pm_metadata)
                db.session.flush()  # Get metadata ID

                # Create ProcessModelNode records
                node_id_map = {}  # Map node_uuid to database ID
                for node in nodes:
                    # Use 'uuid' field from node, not 'id'
                    node_uuid = node.get('uuid', '')
                    if not node_uuid:
                        continue  # Skip nodes without UUID
                        
                    pm_node = ProcessModelNode(
                        process_model_id=pm_metadata.id,
                        node_id=node_uuid,
                        node_type=node.get('type', ''),
                        node_name=node.get('name', ''),
                        properties=json.dumps(node) if node else None
                    )
                    db.session.add(pm_node)
                    db.session.flush()  # Get node ID
                    node_id_map[node_uuid] = pm_node.id

                # Create ProcessModelFlow records
                for flow in flows:
                    # Flows use 'from_node_uuid' and 'to_node_uuid' keys
                    from_node_uuid = flow.get('from_node_uuid', '')
                    to_node_uuid = flow.get('to_node_uuid', '')

                    from_node_id = node_id_map.get(from_node_uuid)
                    to_node_id = node_id_map.get(to_node_uuid)

                    if from_node_id and to_node_id:
                        pm_flow = ProcessModelFlow(
                            process_model_id=pm_metadata.id,
                            from_node_id=from_node_id,
                            to_node_id=to_node_id,
                            flow_label=flow.get('label'),
                            flow_condition=flow.get('condition')
                        )
                        db.session.add(pm_flow)
                    else:
                        logger.warning(
                            f"Could not create flow - missing node IDs "
                            f"(from: {from_node_uuid[:20] if from_node_uuid else 'None'}..., "
                            f"to: {to_node_uuid[:20] if to_node_uuid else 'None'}...)"
                        )

                process_model_count += 1

            db.session.flush()

            logger.info(
                f"Created process model records for "
                f"{process_model_count} process models in package {package.id}"
            )

            return process_model_count

        except Exception as e:
            logger.error(
                f"Error extracting process models: {str(e)}",
                exc_info=True
            )
            raise

    def extract_and_create_dependencies(
        self,
        package: Package,
        object_lookup: Dict[str, Any]
    ) -> List[ObjectDependency]:
        """
        Extract dependencies from object references.

        This method identifies dependencies by looking for UUID references
        in various object properties:
        - Process model nodes referencing interfaces
        - Expression rules referencing other rules
        - Interfaces referencing constants and rules

        Args:
            package: Package record
            object_lookup: Dictionary of objects from blueprint

        Returns:
            List of created ObjectDependency records

        Raises:
            Exception: If dependency creation fails
        """
        try:
            logger.info(
                f"Extracting dependencies for package {package.id}"
            )

            dependencies = []
            seen_dependencies = set()  # Track unique dependencies

            for parent_uuid, obj_data in object_lookup.items():
                # Extract dependencies from process models
                if obj_data.get('type') == 'Process Model':
                    pm_data = obj_data.get('process_model_data', {})
                    nodes = pm_data.get('nodes', [])

                    for node in nodes:
                        # Check for interface references
                        interface_uuid = node.get('interface')
                        if interface_uuid:
                            dep_key = (
                                parent_uuid,
                                interface_uuid,
                                'interface_reference'
                            )
                            if dep_key not in seen_dependencies:
                                dependencies.append({
                                    'package_id': package.id,
                                    'parent_uuid': parent_uuid,
                                    'child_uuid': interface_uuid,
                                    'dependency_type': 'interface_reference'
                                })
                                seen_dependencies.add(dep_key)

                        # Check for script references
                        script_ref = node.get('script_reference')
                        if script_ref:
                            dep_key = (
                                parent_uuid,
                                script_ref,
                                'rule_reference'
                            )
                            if dep_key not in seen_dependencies:
                                dependencies.append({
                                    'package_id': package.id,
                                    'parent_uuid': parent_uuid,
                                    'child_uuid': script_ref,
                                    'dependency_type': 'rule_reference'
                                })
                                seen_dependencies.add(dep_key)

                # Extract dependencies from SAIL code
                sail_code = obj_data.get('sail_code', '')
                if sail_code:
                    # Look for rule! references
                    import re
                    rule_pattern = r'rule!(\w+)'
                    rule_matches = re.findall(rule_pattern, sail_code)

                    for rule_name in rule_matches:
                        # Try to find the UUID for this rule
                        for child_uuid, child_obj in object_lookup.items():
                            if (child_obj.get('name') == f'rule!{rule_name}' or
                                    child_obj.get('name') == rule_name):
                                dep_key = (
                                    parent_uuid,
                                    child_uuid,
                                    'rule_reference'
                                )
                                if dep_key not in seen_dependencies:
                                    dependencies.append({
                                        'package_id': package.id,
                                        'parent_uuid': parent_uuid,
                                        'child_uuid': child_uuid,
                                        'dependency_type': 'rule_reference'
                                    })
                                    seen_dependencies.add(dep_key)
                                break

                    # Look for cons! references
                    cons_pattern = r'cons!(\w+)'
                    cons_matches = re.findall(cons_pattern, sail_code)

                    for cons_name in cons_matches:
                        # Try to find the UUID for this constant
                        for child_uuid, child_obj in object_lookup.items():
                            cons_match = (
                                child_obj.get('name') == f'cons!{cons_name}' or
                                child_obj.get('name') == cons_name
                            )
                            if cons_match:
                                dep_key = (
                                    parent_uuid,
                                    child_uuid,
                                    'constant_reference'
                                )
                                if dep_key not in seen_dependencies:
                                    dependencies.append({
                                        'package_id': package.id,
                                        'parent_uuid': parent_uuid,
                                        'child_uuid': child_uuid,
                                        'dependency_type': 'constant_reference'
                                    })
                                    seen_dependencies.add(dep_key)
                                break

            # Batch insert dependencies
            if dependencies:
                db.session.bulk_insert_mappings(
                    ObjectDependency,
                    dependencies
                )
                db.session.flush()

            logger.info(
                f"Created {len(dependencies)} ObjectDependency records "
                f"for package {package.id}"
            )

            return dependencies

        except Exception as e:
            logger.error(
                f"Error extracting dependencies: {str(e)}",
                exc_info=True
            )
            raise

    def create_package_with_all_data(
        self,
        session_id: int,
        package_type: str,
        blueprint_result: Dict[str, Any]
    ) -> Package:
        """
        Create package and all related records in a single transaction.

        This method orchestrates the complete normalization process:
        1. Create Package record
        2. Extract and create AppianObject records (batch)
        3. Extract and create PackageObjectTypeCount records (batch)
        4. Extract and create ProcessModel records
        5. Extract and create ObjectDependency records (batch)

        All operations are wrapped in a transaction with proper error
        handling and rollback.

        Args:
            session_id: ID of the merge session
            package_type: Type of package ('base', 'customized', 'new_vendor')
            blueprint_result: Complete blueprint dictionary from analyzer

        Returns:
            Package: Created package record with all related data

        Raises:
            ValueError: If blueprint structure is invalid
            Exception: If any database operation fails
        """
        try:
            logger.info(
                f"Starting complete package creation for "
                f"session {session_id}, type: {package_type}"
            )

            # Extract data from blueprint
            blueprint = blueprint_result.get('blueprint', {})
            metadata = blueprint.get('metadata', {})
            object_lookup = blueprint_result.get('object_lookup', {})

            # Validate blueprint structure
            if not object_lookup:
                raise ValueError("Blueprint has no objects in object_lookup")

            # Step 1: Create Package record
            package = self.create_package_from_blueprint(
                session_id,
                package_type,
                blueprint_result
            )

            # Step 2: Extract and create AppianObject records (batch)
            self.extract_and_create_objects(package, object_lookup)

            # Step 3: Extract and create PackageObjectTypeCount records (batch)
            self.extract_and_create_object_type_counts(package, metadata)

            # Step 4: Extract and create ProcessModel records
            self.extract_and_create_process_models(package, object_lookup)

            # Step 5: Extract and create ObjectDependency records (batch)
            self.extract_and_create_dependencies(package, object_lookup)

            # Commit transaction
            db.session.commit()

            logger.info(
                f"Successfully created package {package.id} with all data"
            )

            return package

        except Exception as e:
            # Rollback on any error
            db.session.rollback()
            logger.error(
                f"Error creating package with all data: {str(e)}",
                exc_info=True
            )
            raise
