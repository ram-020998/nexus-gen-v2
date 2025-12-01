"""
Debug Controller - Session Data Inspector
Provides detailed view of session data across all tables
"""
from flask import Blueprint, render_template, request, jsonify
from models import (
    db, MergeSession, Package, ObjectLookup, PackageObjectMapping,
    DeltaComparisonResult, Change, ObjectVersion,
    Interface, InterfaceParameter, InterfaceSecurity,
    ExpressionRule, ExpressionRuleInput,
    ProcessModel, ProcessModelNode, ProcessModelFlow,
    ProcessModelVariable,
    RecordType, RecordTypeField, RecordTypeRelationship,
    RecordTypeView, RecordTypeAction,
    CDT, CDTField,
    Integration, WebAPI, Site, Group, Constant, ConnectedSystem,
    UnknownObject
)
from sqlalchemy import inspect

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

# Map of table names to models
TABLE_MODELS = {
    'merge_sessions': MergeSession,
    'packages': Package,
    'object_lookup': ObjectLookup,
    'package_object_mappings': PackageObjectMapping,
    'delta_comparison_results': DeltaComparisonResult,
    'changes': Change,
    'object_versions': ObjectVersion,
    'interfaces': Interface,
    'interface_parameters': InterfaceParameter,
    'interface_security': InterfaceSecurity,
    'expression_rules': ExpressionRule,
    'expression_rule_inputs': ExpressionRuleInput,
    'process_models': ProcessModel,
    'process_model_nodes': ProcessModelNode,
    'process_model_flows': ProcessModelFlow,
    'process_model_variables': ProcessModelVariable,
    'record_types': RecordType,
    'record_type_fields': RecordTypeField,
    'record_type_relationships': RecordTypeRelationship,
    'record_type_views': RecordTypeView,
    'record_type_actions': RecordTypeAction,
    'cdts': CDT,
    'cdt_fields': CDTField,
    'integrations': Integration,
    'web_apis': WebAPI,
    'sites': Site,
    'groups': Group,
    'constants': Constant,
    'connected_systems': ConnectedSystem,
    'unknown_objects': UnknownObject
}

OBJECT_TYPE_TABLES = {
    'Interface': [
        'interfaces', 'interface_parameters', 'interface_security'
    ],
    'Expression Rule': [
        'expression_rules', 'expression_rule_inputs'
    ],
    'Process Model': [
        'process_models', 'process_model_nodes',
        'process_model_flows', 'process_model_variables'
    ],
    'Record Type': [
        'record_types', 'record_type_fields',
        'record_type_relationships', 'record_type_views',
        'record_type_actions'
    ],
    'CDT': ['cdts', 'cdt_fields'],
    'Integration': ['integrations'],
    'Web API': ['web_apis'],
    'Site': ['sites'],
    'Group': ['groups'],
    'Constant': ['constants'],
    'Connected System': ['connected_systems'],
    'Unknown': ['unknown_objects']
}


def model_to_dict(obj):
    """Convert SQLAlchemy model to dictionary"""
    if obj is None:
        return None

    result = {}
    for column in inspect(obj).mapper.column_attrs:
        value = getattr(obj, column.key)
        # Handle datetime objects
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        result[column.key] = value
    return result


@debug_bp.route('/')
def index():
    """Render debug page"""
    # Get all sessions for dropdown
    sessions = MergeSession.query.order_by(
        MergeSession.created_at.desc()
    ).all()

    # Get all unique object types
    object_types = db.session.query(
        ObjectLookup.object_type
    ).distinct().order_by(ObjectLookup.object_type).all()
    object_types = [ot[0] for ot in object_types if ot[0]]

    return render_template('debug.html',
                           sessions=sessions,
                           object_types=object_types,
                           package_types=['A', 'B', 'C'])


@debug_bp.route('/api/session-data', methods=['POST'])
def get_session_data():
    """Get filtered session data"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        package_filter = data.get('package')  # 'A', 'B', 'C', or None
        object_type_filter = data.get('object_type')  # object type or None
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Verify session exists
        session = MergeSession.query.filter_by(id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get package IDs for filtering
        package_ids = []
        if package_filter:
            package_type_map = {
                'A': 'base',
                'B': 'customized',
                'C': 'new_vendor'
            }
            package = Package.query.filter_by(
                session_id=session_id,
                package_type=package_type_map[package_filter]
            ).first()
            if package:
                package_ids = [package.id]
        else:
            packages = Package.query.filter_by(
                session_id=session_id
            ).all()
            package_ids = [p.id for p in packages]
        
        # Build response structure
        response = {
            'session_info': model_to_dict(session),
            'packages': {},
            'tables': {}
        }

        # Get package information
        packages = Package.query.filter_by(session_id=session_id).all()
        for pkg in packages:
            pkg_map = {
                'base': 'A',
                'customized': 'B',
                'new_vendor': 'C'
            }
            pkg_label = pkg_map[pkg.package_type]
            if not package_filter or package_filter == pkg_label:
                response['packages'][pkg_label] = model_to_dict(pkg)
        
        # Get object IDs based on filters
        object_ids = set()
        if package_ids:
            mappings = PackageObjectMapping.query.filter(
                PackageObjectMapping.package_id.in_(package_ids)
            ).all()
            object_ids = {m.object_id for m in mappings}

        if object_type_filter:
            objects = ObjectLookup.query.filter_by(
                object_type=object_type_filter
            ).all()
            type_object_ids = {o.id for o in objects}
            if object_ids:
                object_ids = object_ids.intersection(type_object_ids)
            else:
                object_ids = type_object_ids

        # Collect data from all tables
        response['tables'] = collect_table_data(
            session_id, package_ids, object_ids, object_type_filter
        )

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def collect_table_data(session_id, package_ids, object_ids,
                       object_type_filter):
    """Collect data from all relevant tables"""
    tables_data = {}

    # Core tables
    tables_data['object_lookup'] = collect_objects(object_ids)
    tables_data['package_object_mappings'] = collect_mappings(
        package_ids, object_ids
    )
    tables_data['delta_comparison_results'] = collect_delta_results(
        session_id, object_ids
    )
    tables_data['changes'] = collect_changes(session_id, object_ids)
    tables_data['object_versions'] = collect_versions(
        package_ids, object_ids
    )

    # Object-specific tables
    if object_type_filter:
        if object_type_filter in OBJECT_TYPE_TABLES:
            for table_name in OBJECT_TYPE_TABLES[object_type_filter]:
                tables_data[table_name] = collect_object_specific_data(
                    table_name, object_ids, package_ids
                )
    else:
        # Collect all object-specific tables
        for obj_type, table_names in OBJECT_TYPE_TABLES.items():
            for table_name in table_names:
                tables_data[table_name] = collect_object_specific_data(
                    table_name, object_ids, package_ids
                )

    return tables_data


def collect_objects(object_ids):
    """Collect object_lookup data"""
    if not object_ids:
        return []

    objects = ObjectLookup.query.filter(
        ObjectLookup.id.in_(object_ids)
    ).all()
    return [model_to_dict(obj) for obj in objects]


def collect_mappings(package_ids, object_ids):
    """Collect package_object_mappings data"""
    if not package_ids or not object_ids:
        return []

    mappings = PackageObjectMapping.query.filter(
        PackageObjectMapping.package_id.in_(package_ids),
        PackageObjectMapping.object_id.in_(object_ids)
    ).all()
    return [model_to_dict(m) for m in mappings]


def collect_delta_results(session_id, object_ids):
    """Collect delta_comparison_results data"""
    if not object_ids:
        return []

    results = DeltaComparisonResult.query.filter(
        DeltaComparisonResult.session_id == session_id,
        DeltaComparisonResult.object_id.in_(object_ids)
    ).all()
    return [model_to_dict(r) for r in results]


def collect_changes(session_id, object_ids):
    """Collect changes data"""
    if not object_ids:
        return []

    changes = Change.query.filter(
        Change.session_id == session_id,
        Change.object_id.in_(object_ids)
    ).all()
    return [model_to_dict(c) for c in changes]


def collect_versions(package_ids, object_ids):
    """Collect object_versions data"""
    if not package_ids or not object_ids:
        return []

    versions = ObjectVersion.query.filter(
        ObjectVersion.package_id.in_(package_ids),
        ObjectVersion.object_id.in_(object_ids)
    ).all()
    return [model_to_dict(v) for v in versions]


def collect_object_specific_data(table_name, object_ids, package_ids):
    """Collect data from object-specific tables filtered by package"""
    if not object_ids or table_name not in TABLE_MODELS:
        return []

    model = TABLE_MODELS[table_name]

    # Child tables don't have object_id, need to query via parent
    child_tables = {
        'interface_parameters': ('interface_id', Interface),
        'interface_security': ('interface_id', Interface),
        'expression_rule_inputs': ('rule_id', ExpressionRule),
        'process_model_nodes': ('process_model_id', ProcessModel),
        'process_model_flows': ('process_model_id', ProcessModel),
        'process_model_variables': ('process_model_id', ProcessModel),
        'record_type_fields': ('record_type_id', RecordType),
        'record_type_relationships': ('record_type_id', RecordType),
        'record_type_views': ('record_type_id', RecordType),
        'record_type_actions': ('record_type_id', RecordType),
        'cdt_fields': ('cdt_id', CDT)
    }

    if table_name in child_tables:
        fk_column, parent_model = child_tables[table_name]
        
        # Get version_uuids for the selected packages
        if package_ids:
            version_pairs = db.session.query(
                ObjectVersion.object_id,
                ObjectVersion.version_uuid
            ).filter(
                ObjectVersion.package_id.in_(package_ids),
                ObjectVersion.object_id.in_(object_ids)
            ).all()
            
            if not version_pairs:
                return []
            
            # Get parent IDs filtered by version_uuid (first match only)
            parent_ids = []
            for obj_id, ver_uuid in version_pairs:
                parent = parent_model.query.filter(
                    parent_model.object_id == obj_id,
                    parent_model.version_uuid == ver_uuid
                ).first()
                if parent:
                    parent_ids.append(parent.id)
        else:
            # No package filter, get all parent IDs
            parent_ids = [p.id for p in parent_model.query.filter(
                parent_model.object_id.in_(object_ids)
            ).all()]
        
        if not parent_ids:
            return []
        
        # Query child records
        fk_attr = getattr(model, fk_column)
        records = model.query.filter(fk_attr.in_(parent_ids)).all()
    else:
        # Direct object_id relationship - filter by version_uuid
        if package_ids:
            # Get (object_id, version_uuid) pairs for the selected packages
            version_pairs = db.session.query(
                ObjectVersion.object_id,
                ObjectVersion.version_uuid
            ).filter(
                ObjectVersion.package_id.in_(package_ids),
                ObjectVersion.object_id.in_(object_ids)
            ).all()
            
            if not version_pairs:
                return []
            
            # Build a list of records that match the exact (object_id, version_uuid) pairs
            records = []
            for obj_id, ver_uuid in version_pairs:
                # Get the FIRST record that matches this object_id and version_uuid
                # This handles the case where multiple packages have the same version
                record = model.query.filter(
                    model.object_id == obj_id,
                    model.version_uuid == ver_uuid
                ).first()
                if record:
                    records.append(record)
        else:
            # No package filter, get all records
            records = model.query.filter(
                model.object_id.in_(object_ids)
            ).all()

    return [model_to_dict(r) for r in records]
