"""
Dependency Analysis Service

Analyzes object dependencies and provides smart ordering for merge workflow.
Handles dependency graph construction, topological sorting with circular
dependency detection, and intelligent change ordering.
"""
from typing import Dict, Any, List, Set
import re


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected"""
    pass


class DependencyAnalysisService:
    """
    Analyzes dependencies and provides smart ordering

    Builds dependency graphs from blueprints and orders changes intelligently:
    1. NO_CONFLICT changes first (grouped by type)
    2. CONFLICT changes (ordered by dependencies)
    3. REMOVED_BUT_CUSTOMIZED changes last
    """

    def __init__(self):
        """Initialize the dependency analysis service"""
        pass

    def build_dependency_graph(
        self,
        blueprint: Dict[str, Any],
        logger=None
    ) -> Dict[str, List[str]]:
        """
        Build dependency graph from blueprint

        Extracts dependencies by analyzing:
        - SAIL code for rule!, cons!, type! references
        - Record type relationships
        - Process model references
        - Interface component references

        Args:
            blueprint: Blueprint dictionary with object_lookup
            logger: Optional logger instance

        Returns:
            Dictionary mapping object UUID to list of parent UUIDs
            (objects that this object depends on)
            {child_uuid: [parent_uuid1, parent_uuid2, ...]}
        """
        object_lookup = blueprint.get('object_lookup', {})
        if not object_lookup:
            return {}

        dependency_graph = {}

        # Build reverse lookup: name -> uuid
        name_to_uuid = {}
        for uuid, obj in object_lookup.items():
            name = obj.get('name', '')
            if name:
                name_to_uuid[name] = uuid

        # Analyze each object for dependencies
        for uuid, obj in object_lookup.items():
            dependencies = set()

            # Extract dependencies from SAIL code
            if 'sail_code' in obj and obj['sail_code']:
                sail_deps = self._extract_sail_dependencies(
                    obj['sail_code'],
                    object_lookup,
                    name_to_uuid
                )
                dependencies.update(sail_deps)

            # Extract dependencies from business logic
            if 'business_logic' in obj and obj['business_logic']:
                logic_deps = self._extract_sail_dependencies(
                    obj['business_logic'],
                    object_lookup,
                    name_to_uuid
                )
                dependencies.update(logic_deps)

            # Extract dependencies from record type relationships
            if obj.get('object_type') == 'Record Type':
                if 'relationships' in obj:
                    for rel in obj['relationships']:
                        if 'related_record_uuid' in rel:
                            related_uuid = rel['related_record_uuid']
                            if related_uuid in object_lookup:
                                dependencies.add(related_uuid)

            # Extract dependencies from fields (for record types)
            if 'fields' in obj and isinstance(obj['fields'], list):
                for field in obj['fields']:
                    if isinstance(field, dict):
                        # Check for type references
                        field_type = field.get('type', '')
                        if field_type and field_type in name_to_uuid:
                            dependencies.add(name_to_uuid[field_type])

            # Remove self-references
            dependencies.discard(uuid)

            # Store dependencies
            dependency_graph[uuid] = list(dependencies)

        return dependency_graph

    def _extract_sail_dependencies(
        self,
        code: str,
        object_lookup: Dict[str, Any],
        name_to_uuid: Dict[str, str]
    ) -> Set[str]:
        """
        Extract dependencies from SAIL code

        Looks for patterns like:
        - rule!RuleName
        - cons!ConstantName
        - type!TypeName
        - #"_a-uuid-string"

        Args:
            code: SAIL code string
            object_lookup: Object lookup dictionary
            name_to_uuid: Name to UUID mapping

        Returns:
            Set of dependent object UUIDs
        """
        dependencies = set()

        if not code:
            return dependencies

        # Pattern 1: Direct UUID references #"_a-uuid"
        uuid_pattern = r'#"(_a-[^"]+)"'
        uuid_matches = re.findall(uuid_pattern, code)
        for uuid in uuid_matches:
            if uuid in object_lookup:
                dependencies.add(uuid)

        # Pattern 2: rule! references
        rule_pattern = r'rule!([a-zA-Z_][a-zA-Z0-9_]*)'
        rule_matches = re.findall(rule_pattern, code)
        for rule_name in rule_matches:
            if rule_name in name_to_uuid:
                dependencies.add(name_to_uuid[rule_name])

        # Pattern 3: cons! references
        cons_pattern = r'cons!([a-zA-Z_][a-zA-Z0-9_]*)'
        cons_matches = re.findall(cons_pattern, code)
        for cons_name in cons_matches:
            if cons_name in name_to_uuid:
                dependencies.add(name_to_uuid[cons_name])

        # Pattern 4: type! references
        type_pattern = r'type!([a-zA-Z_][a-zA-Z0-9_]*)'
        type_matches = re.findall(type_pattern, code)
        for type_name in type_matches:
            if type_name in name_to_uuid:
                dependencies.add(name_to_uuid[type_name])

        return dependencies

    def topological_sort(
        self,
        objects: List[str],
        dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """
        Sort objects by dependency order (parents before children)

        Uses Kahn's algorithm for topological sorting with circular
        dependency detection and cycle breaking.

        Args:
            objects: List of object UUIDs to sort
            dependency_graph: Dependency graph {child: [parents]}

        Returns:
            List of object UUIDs in dependency order

        Raises:
            CircularDependencyError: If circular dependencies detected
                                    and cannot be broken
        """
        # Filter dependency graph to only include objects in the list
        objects_set = set(objects)
        filtered_graph = {}
        for obj in objects:
            deps = dependency_graph.get(obj, [])
            # Only include dependencies that are in our object list
            filtered_deps = [d for d in deps if d in objects_set]
            filtered_graph[obj] = filtered_deps

        # Calculate in-degree for each object
        in_degree = {obj: 0 for obj in objects}
        for obj in objects:
            for dep in filtered_graph.get(obj, []):
                in_degree[dep] = in_degree.get(dep, 0) + 1

        # Find all objects with no dependencies (in-degree = 0)
        queue = [obj for obj in objects if in_degree[obj] == 0]
        result = []

        # Process queue
        while queue:
            # Sort queue for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # For each object that depends on current
            for obj in objects:
                if current in filtered_graph.get(obj, []):
                    in_degree[obj] -= 1
                    if in_degree[obj] == 0:
                        queue.append(obj)

        # Check if all objects were processed
        if len(result) != len(objects):
            # Circular dependency detected
            unprocessed = [obj for obj in objects if obj not in result]

            # Try to break cycles by finding strongly connected components
            broken_graph = self._break_cycles(
                filtered_graph,
                unprocessed
            )

            # Retry topological sort with broken cycles
            return self._topological_sort_with_broken_cycles(
                objects,
                broken_graph
            )

        return result

    def _break_cycles(
        self,
        dependency_graph: Dict[str, List[str]],
        unprocessed: List[str]
    ) -> Dict[str, List[str]]:
        """
        Break circular dependencies by removing edges

        Strategy: Remove edges with lowest priority (based on object type)

        Args:
            dependency_graph: Original dependency graph
            unprocessed: Objects involved in cycles

        Returns:
            Modified dependency graph with broken cycles
        """
        # Create a copy of the graph
        broken_graph = {
            k: list(v) for k, v in dependency_graph.items()
        }

        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []

        def find_cycle_dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in broken_graph.get(node, []):
                if neighbor not in visited:
                    if find_cycle_dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        # Find all cycles
        for node in unprocessed:
            if node not in visited:
                find_cycle_dfs(node, [])

        # Break cycles by removing one edge from each cycle
        for cycle in cycles:
            if len(cycle) >= 2:
                # Remove edge from last to first in cycle
                child = cycle[-1]
                parent = cycle[0]
                if parent in broken_graph.get(child, []):
                    broken_graph[child].remove(parent)

        return broken_graph

    def _topological_sort_with_broken_cycles(
        self,
        objects: List[str],
        dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """
        Perform topological sort after breaking cycles

        Args:
            objects: List of object UUIDs
            dependency_graph: Dependency graph with broken cycles

        Returns:
            Sorted list of object UUIDs
        """
        # Calculate in-degree
        in_degree = {obj: 0 for obj in objects}
        for obj in objects:
            for dep in dependency_graph.get(obj, []):
                if dep in in_degree:
                    in_degree[dep] += 1

        # Find objects with no dependencies
        queue = [obj for obj in objects if in_degree[obj] == 0]
        result = []

        while queue:
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # Update in-degrees
            for obj in objects:
                if current in dependency_graph.get(obj, []):
                    in_degree[obj] -= 1
                    if in_degree[obj] == 0:
                        queue.append(obj)

        # If still have unprocessed objects, add them at the end
        unprocessed = [obj for obj in objects if obj not in result]
        if unprocessed:
            unprocessed.sort()
            result.extend(unprocessed)

        return result

    def order_changes(
        self,
        classified_changes: Dict[str, List[Dict]],
        dependency_graph: Dict[str, List[str]],
        logger=None
    ) -> List[Dict[str, Any]]:
        """
        Order changes intelligently:
        1. NO_CONFLICT changes first (grouped by type)
        2. CONFLICT changes (ordered by dependencies)
        3. REMOVED_BUT_CUSTOMIZED changes last

        Args:
            classified_changes: Dictionary with classification categories
            dependency_graph: Dependency graph from blueprint
            logger: Optional logger instance

        Returns:
            Ordered list of change objects
        """
        ordered_changes = []

        # Phase 1: NO_CONFLICT changes, grouped by object type
        no_conflict_changes = classified_changes.get('NO_CONFLICT', [])
        if no_conflict_changes:
            # Group by object type
            by_type = {}
            for change in no_conflict_changes:
                obj_type = change.get('type', 'Unknown')
                if obj_type not in by_type:
                    by_type[obj_type] = []
                by_type[obj_type].append(change)

            # Add each type group in sorted order
            for obj_type in sorted(by_type.keys()):
                # Sort within type by name for consistency
                type_changes = sorted(
                    by_type[obj_type],
                    key=lambda x: x.get('name', '')
                )
                ordered_changes.extend(type_changes)

        # Phase 2: CONFLICT changes, ordered by dependencies
        conflict_changes = classified_changes.get('CONFLICT', [])
        if conflict_changes:
            # Extract UUIDs
            conflict_uuids = [c['uuid'] for c in conflict_changes]

            # Sort by dependencies
            try:
                sorted_uuids = self.topological_sort(
                    conflict_uuids,
                    dependency_graph
                )

                # Build UUID to change mapping
                uuid_to_change = {
                    c['uuid']: c for c in conflict_changes
                }

                # Add in sorted order
                for uuid in sorted_uuids:
                    if uuid in uuid_to_change:
                        ordered_changes.append(uuid_to_change[uuid])

            except CircularDependencyError as e:
                # Log circular dependency
                if logger:
                    logger.log_circular_dependency_detected(str(e))
                # If sorting fails, add in original order
                ordered_changes.extend(conflict_changes)
            except Exception as e:
                # Log other errors
                if logger:
                    logger.warning(
                        f"Error during dependency sorting: {e}"
                    )
                # If sorting fails, add in original order
                ordered_changes.extend(conflict_changes)

        # Phase 3: CUSTOMER_ONLY changes - EXCLUDED from workflow
        # Customers don't need to review their own changes
        # They only need to see vendor changes and conflicts

        # Phase 4: REMOVED_BUT_CUSTOMIZED changes last
        removed_changes = classified_changes.get('REMOVED_BUT_CUSTOMIZED', [])
        if removed_changes:
            # Sort by name for consistency
            sorted_removed = sorted(
                removed_changes,
                key=lambda x: x.get('name', '')
            )
            ordered_changes.extend(sorted_removed)

        return ordered_changes

    def get_dependencies(
        self,
        object_uuid: str,
        dependency_graph: Dict[str, List[str]],
        ordered_changes: List[Dict[str, Any]] = None,
        object_lookup: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get dependency information for an object

        Args:
            object_uuid: UUID of the object
            dependency_graph: Dependency graph {child: [parents]}
            ordered_changes: List of ordered changes (optional, for enriching with review status)
            object_lookup: Object lookup dictionary (optional, for getting object names)

        Returns:
            Dictionary with:
            {
                'parents': [list of parent objects with name, review_status, etc.],
                'children': [list of child objects with name, review_status, etc.]
            }
        """
        # Get parents (objects this object depends on)
        parent_uuids = dependency_graph.get(object_uuid, [])

        # Get children (objects that depend on this object)
        child_uuids = []
        for obj_uuid, deps in dependency_graph.items():
            if object_uuid in deps:
                child_uuids.append(obj_uuid)

        # Build enriched parent objects
        parents = []
        for parent_uuid in parent_uuids:
            parent_obj = self._build_dependency_object(
                parent_uuid,
                ordered_changes,
                object_lookup
            )
            parents.append(parent_obj)

        # Build enriched child objects
        children = []
        for child_uuid in child_uuids:
            child_obj = self._build_dependency_object(
                child_uuid,
                ordered_changes,
                object_lookup
            )
            children.append(child_obj)

        return {
            'parents': parents,
            'children': children
        }

    def _build_dependency_object(
        self,
        uuid: str,
        ordered_changes: List[Dict[str, Any]] = None,
        object_lookup: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Build a dependency object with name, review status, and change index

        Args:
            uuid: Object UUID
            ordered_changes: List of ordered changes
            object_lookup: Object lookup dictionary

        Returns:
            Dictionary with uuid, name, review_status, in_change_list, change_index
        """
        # Start with basic structure
        dep_obj = {
            'uuid': uuid,
            'name': 'Unknown',
            'review_status': 'pending',
            'in_change_list': False,
            'change_index': None
        }

        # Get name from object lookup
        if object_lookup and uuid in object_lookup:
            obj = object_lookup[uuid]
            dep_obj['name'] = obj.get('name', 'Unknown')

        # Get review status and change index from ordered changes
        if ordered_changes:
            for idx, change in enumerate(ordered_changes):
                if change.get('uuid') == uuid:
                    dep_obj['in_change_list'] = True
                    dep_obj['change_index'] = idx
                    dep_obj['review_status'] = change.get('review_status', 'pending')
                    # Also update name from change if not found in lookup
                    if dep_obj['name'] == 'Unknown':
                        dep_obj['name'] = change.get('name', 'Unknown')
                    break

        return dep_obj
