"""
Database Models
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()


class Request(db.Model):
    """Main requests table for breakdown, verify, create actions"""
    __tablename__ = 'requests'

    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(20), nullable=False)  # 'breakdown', 'verify', 'create'
    filename = db.Column(db.String(255))  # for breakdown (uploaded file)
    input_text = db.Column(db.Text)  # for verify/create (pasted content)
    status = db.Column(db.String(20), default='processing')  # 'processing', 'completed', 'error'
    rag_query = db.Column(db.Text)  # query sent to RAG
    rag_response = db.Column(db.Text)  # RAG API response
    final_output = db.Column(db.Text)  # processed result from Q agent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    export_path = db.Column(db.String(500))  # Excel file path (breakdown only)
    
    # Step 9 additions
    reference_id = db.Column(db.String(20))  # RQ_ND_001 format
    agent_name = db.Column(db.String(50))  # breakdown-agent, verify-agent, etc.
    model_name = db.Column(db.String(100))  # amazon.nova-pro-v1:0
    parameters = db.Column(db.Text)  # JSON string of model parameters
    total_time = db.Column(db.Integer)  # Total processing time in seconds
    step_durations = db.Column(db.Text)  # JSON string of step timings
    raw_agent_output = db.Column(db.Text)  # Raw Q agent response before cleaning
    q_agent_prompt = db.Column(db.Text)  # Prompt sent to Q agent
    rag_similarity_avg = db.Column(db.Float)  # Average RAG similarity score
    json_valid = db.Column(db.Boolean, default=True)  # JSON validity flag
    error_log = db.Column(db.Text)  # Error messages and retry attempts

    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'filename': self.filename,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'export_path': self.export_path,
            'reference_id': self.reference_id,
            'agent_name': self.agent_name,
            'model_name': self.model_name,
            'total_time': self.total_time,
            'rag_similarity_avg': self.rag_similarity_avg,
            'json_valid': self.json_valid
        }


class ChatSession(db.Model):
    """Chat sessions for AI assistant"""
    __tablename__ = 'chat_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()))
    question = db.Column(db.Text, nullable=False)
    rag_response = db.Column(db.Text)
    answer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at.isoformat()
        }


# ============================================================================
# Three-Way Merge Models
# ============================================================================

class MergeSession(db.Model):
    """Merge sessions for three-way merge analysis"""
    __tablename__ = 'merge_sessions'

    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default='processing')
    total_changes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # UI Enhancement fields
    reviewed_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    estimated_complexity = db.Column(db.String(20))
    estimated_time_hours = db.Column(db.Float)

    # Relationships
    packages = db.relationship('Package', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    delta_results = db.relationship('DeltaComparisonResult', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    changes = db.relationship('Change', backref='session', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'reference_id': self.reference_id,
            'status': self.status,
            'total_changes': self.total_changes,
            'reviewed_count': self.reviewed_count,
            'skipped_count': self.skipped_count,
            'estimated_complexity': self.estimated_complexity,
            'estimated_time_hours': self.estimated_time_hours,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Package(db.Model):
    """Packages uploaded for merge analysis"""
    __tablename__ = 'packages'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id', ondelete='CASCADE'), nullable=False)
    package_type = db.Column(db.String(20), nullable=False)  # base, customized, new_vendor
    filename = db.Column(db.String(500), nullable=False)
    total_objects = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    object_mappings = db.relationship('PackageObjectMapping', backref='package', lazy='dynamic', cascade='all, delete-orphan')
    object_versions = db.relationship('ObjectVersion', backref='package', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'package_type': self.package_type,
            'filename': self.filename,
            'total_objects': self.total_objects,
            'created_at': self.created_at.isoformat()
        }


class ObjectLookup(db.Model):
    """Global object registry - single source of truth for all objects"""
    __tablename__ = 'object_lookup'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(255), nullable=False, unique=True, index=True)
    name = db.Column(db.String(500), nullable=False, index=True)
    object_type = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    package_mappings = db.relationship('PackageObjectMapping', backref='object', lazy='dynamic', cascade='all, delete-orphan')
    versions = db.relationship('ObjectVersion', backref='object', lazy='dynamic', cascade='all, delete-orphan')
    delta_results = db.relationship('DeltaComparisonResult', backref='object', lazy='dynamic', cascade='all, delete-orphan')
    changes = db.relationship('Change', foreign_keys='Change.object_id', backref='object', lazy='dynamic', cascade='all, delete-orphan')
    vendor_changes = db.relationship('Change', foreign_keys='Change.vendor_object_id', backref='vendor_object', lazy='dynamic', cascade='all, delete-orphan')
    customer_changes = db.relationship('Change', foreign_keys='Change.customer_object_id', backref='customer_object', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'object_type': self.object_type,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


class PackageObjectMapping(db.Model):
    """Junction table tracking which objects belong to which packages"""
    __tablename__ = 'package_object_mappings'

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('package_id', 'object_id', name='uq_package_object'),
        db.Index('idx_pom_package_object', 'package_id', 'object_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'package_id': self.package_id,
            'object_id': self.object_id,
            'created_at': self.created_at.isoformat()
        }


class DeltaComparisonResult(db.Model):
    """Results of A→C comparison (vendor delta)"""
    __tablename__ = 'delta_comparison_results'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    change_category = db.Column(db.String(20), nullable=False)  # NEW, MODIFIED, DEPRECATED
    change_type = db.Column(db.String(20), nullable=False)  # ADDED, MODIFIED, REMOVED
    version_changed = db.Column(db.Boolean, default=False)
    content_changed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('session_id', 'object_id', name='uq_session_object'),
        db.Index('idx_delta_category', 'session_id', 'change_category'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'object_id': self.object_id,
            'change_category': self.change_category,
            'change_type': self.change_type,
            'version_changed': self.version_changed,
            'content_changed': self.content_changed,
            'created_at': self.created_at.isoformat()
        }


class CustomerComparisonResult(db.Model):
    """
    Stores customer comparison results (Set E: A→B comparison).
    
    This table stores ALL changes made by the customer from the base version.
    It's symmetric with delta_comparison_results (vendor changes).
    """
    __tablename__ = 'customer_comparison_results'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('merge_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    object_id = db.Column(
        db.Integer,
        db.ForeignKey('object_lookup.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    change_category = db.Column(db.String(20), nullable=False)  # NEW, MODIFIED, DEPRECATED
    change_type = db.Column(db.String(20), nullable=False)  # ADDED, MODIFIED, REMOVED
    version_changed = db.Column(db.Boolean, default=False)
    content_changed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one result per object per session
    __table_args__ = (
        db.UniqueConstraint('session_id', 'object_id', name='uq_customer_comparison_session_object'),
        db.Index('idx_customer_comparison_category', 'session_id', 'change_category'),
    )
    
    # Relationships
    session = db.relationship('MergeSession', backref='customer_comparison_results')
    object = db.relationship('ObjectLookup', backref='customer_comparisons')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'object_id': self.object_id,
            'change_category': self.change_category,
            'change_type': self.change_type,
            'version_changed': self.version_changed,
            'content_changed': self.content_changed,
            'created_at': self.created_at.isoformat()
        }


class Change(db.Model):
    """Working set of classified changes for user review"""
    __tablename__ = 'changes'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    classification = db.Column(db.String(50), nullable=False)  # NO_CONFLICT, CONFLICT, NEW, DELETED
    change_type = db.Column(db.String(20))
    vendor_change_type = db.Column(db.String(20))
    customer_change_type = db.Column(db.String(20))
    display_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dual Object Tracking (Migration 003)
    vendor_object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), index=True)
    customer_object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), index=True)
    
    # UI Enhancement fields
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, skipped
    notes = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.String(255))

    __table_args__ = (
        db.Index('idx_change_session_classification', 'session_id', 'classification'),
        db.Index('idx_change_session_object', 'session_id', 'object_id'),
        db.Index('idx_change_session_order', 'session_id', 'display_order'),
        db.Index('idx_change_session_status', 'session_id', 'status'),
        db.Index('idx_change_reviewed_at', 'reviewed_at'),
        db.Index('idx_change_vendor_object', 'vendor_object_id'),
        db.Index('idx_change_customer_object', 'customer_object_id'),
        db.Index('idx_change_vendor_customer', 'vendor_object_id', 'customer_object_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'object_id': self.object_id,
            'vendor_object_id': self.vendor_object_id,
            'customer_object_id': self.customer_object_id,
            'classification': self.classification,
            'change_type': self.change_type,
            'vendor_change_type': self.vendor_change_type,
            'customer_change_type': self.customer_change_type,
            'display_order': self.display_order,
            'status': self.status,
            'notes': self.notes,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by,
            'created_at': self.created_at.isoformat()
        }


class ObjectVersion(db.Model):
    """Package-specific versions of objects"""
    __tablename__ = 'object_versions'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    version_uuid = db.Column(db.String(255))
    sail_code = db.Column(db.Text)
    fields = db.Column(db.Text)  # JSON string
    properties = db.Column(db.Text)  # JSON string
    raw_xml = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_object_package'),
        db.Index('idx_objver_object_package', 'object_id', 'package_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'object_id': self.object_id,
            'package_id': self.package_id,
            'version_uuid': self.version_uuid,
            'created_at': self.created_at.isoformat()
        }


# ============================================================================
# Object-Specific Models
# ============================================================================

class Interface(db.Model):
    """Interface objects"""
    __tablename__ = 'interfaces'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    sail_code = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    parameters = db.relationship('InterfaceParameter', backref='interface', lazy='dynamic', cascade='all, delete-orphan')
    security = db.relationship('InterfaceSecurity', backref='interface', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_interface_object_package'),
        db.Index('idx_interface_object_package', 'object_id', 'package_id'),
    )


class InterfaceParameter(db.Model):
    """Interface parameters"""
    __tablename__ = 'interface_parameters'

    id = db.Column(db.Integer, primary_key=True)
    interface_id = db.Column(db.Integer, db.ForeignKey('interfaces.id', ondelete='CASCADE'), nullable=False)
    parameter_name = db.Column(db.String(255), nullable=False)
    parameter_type = db.Column(db.String(100))
    is_required = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.Text)
    display_order = db.Column(db.Integer)


class InterfaceSecurity(db.Model):
    """Interface security settings"""
    __tablename__ = 'interface_security'

    id = db.Column(db.Integer, primary_key=True)
    interface_id = db.Column(db.Integer, db.ForeignKey('interfaces.id', ondelete='CASCADE'), nullable=False)
    role_name = db.Column(db.String(255))
    permission_type = db.Column(db.String(50))

    __table_args__ = (
        db.UniqueConstraint('interface_id', 'role_name', 'permission_type', name='uq_interface_security'),
    )


class ExpressionRule(db.Model):
    """Expression Rule objects"""
    __tablename__ = 'expression_rules'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    sail_code = db.Column(db.Text)
    output_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    inputs = db.relationship('ExpressionRuleInput', backref='rule', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_expression_rule_object_package'),
        db.Index('idx_expression_rule_object_package', 'object_id', 'package_id'),
    )


class ExpressionRuleInput(db.Model):
    """Expression Rule inputs"""
    __tablename__ = 'expression_rule_inputs'

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('expression_rules.id', ondelete='CASCADE'), nullable=False)
    input_name = db.Column(db.String(255), nullable=False)
    input_type = db.Column(db.String(100))
    is_required = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.Text)
    display_order = db.Column(db.Integer)


class ProcessModel(db.Model):
    """Process Model objects"""
    __tablename__ = 'process_models'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    description = db.Column(db.Text)
    total_nodes = db.Column(db.Integer, default=0)
    total_flows = db.Column(db.Integer, default=0)
    complexity_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    nodes = db.relationship('ProcessModelNode', backref='process_model', lazy='dynamic', cascade='all, delete-orphan')
    flows = db.relationship('ProcessModelFlow', backref='process_model', lazy='dynamic', cascade='all, delete-orphan')
    variables = db.relationship('ProcessModelVariable', backref='process_model', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_process_model_object_package'),
        db.Index('idx_process_model_object_package', 'object_id', 'package_id'),
    )


class ProcessModelNode(db.Model):
    """Process Model nodes"""
    __tablename__ = 'process_model_nodes'

    id = db.Column(db.Integer, primary_key=True)
    process_model_id = db.Column(db.Integer, db.ForeignKey('process_models.id', ondelete='CASCADE'), nullable=False)
    node_id = db.Column(db.String(255), nullable=False)
    node_type = db.Column(db.String(100), nullable=False)
    node_name = db.Column(db.String(500))
    properties = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('process_model_id', 'node_id', name='uq_pm_node'),
        db.Index('idx_node_type', 'process_model_id', 'node_type'),
    )


class ProcessModelFlow(db.Model):
    """Process Model flows"""
    __tablename__ = 'process_model_flows'

    id = db.Column(db.Integer, primary_key=True)
    process_model_id = db.Column(db.Integer, db.ForeignKey('process_models.id', ondelete='CASCADE'), nullable=False)
    from_node_id = db.Column(db.Integer, db.ForeignKey('process_model_nodes.id'), nullable=False)
    to_node_id = db.Column(db.Integer, db.ForeignKey('process_model_nodes.id'), nullable=False)
    flow_label = db.Column(db.String(500))
    flow_condition = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_flow_from', 'process_model_id', 'from_node_id'),
        db.Index('idx_flow_to', 'process_model_id', 'to_node_id'),
    )


class ProcessModelVariable(db.Model):
    """Process Model variables"""
    __tablename__ = 'process_model_variables'

    id = db.Column(db.Integer, primary_key=True)
    process_model_id = db.Column(db.Integer, db.ForeignKey('process_models.id', ondelete='CASCADE'), nullable=False)
    variable_name = db.Column(db.String(255), nullable=False)
    variable_type = db.Column(db.String(100))
    is_parameter = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.Text)


class RecordType(db.Model):
    """Record Type objects"""
    __tablename__ = 'record_types'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    description = db.Column(db.Text)
    source_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    fields = db.relationship('RecordTypeField', backref='record_type', lazy='dynamic', cascade='all, delete-orphan')
    relationships = db.relationship('RecordTypeRelationship', backref='record_type', lazy='dynamic', cascade='all, delete-orphan')
    views = db.relationship('RecordTypeView', backref='record_type', lazy='dynamic', cascade='all, delete-orphan')
    actions = db.relationship('RecordTypeAction', backref='record_type', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_record_type_object_package'),
        db.Index('idx_record_type_object_package', 'object_id', 'package_id'),
    )


class RecordTypeField(db.Model):
    """Record Type fields"""
    __tablename__ = 'record_type_fields'

    id = db.Column(db.Integer, primary_key=True)
    record_type_id = db.Column(db.Integer, db.ForeignKey('record_types.id', ondelete='CASCADE'), nullable=False)
    field_name = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.String(100))
    is_primary_key = db.Column(db.Boolean, default=False)
    is_required = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer)


class RecordTypeRelationship(db.Model):
    """Record Type relationships"""
    __tablename__ = 'record_type_relationships'

    id = db.Column(db.Integer, primary_key=True)
    record_type_id = db.Column(db.Integer, db.ForeignKey('record_types.id', ondelete='CASCADE'), nullable=False)
    relationship_name = db.Column(db.String(255))
    related_record_uuid = db.Column(db.String(255))
    relationship_type = db.Column(db.String(50))


class RecordTypeView(db.Model):
    """Record Type views"""
    __tablename__ = 'record_type_views'

    id = db.Column(db.Integer, primary_key=True)
    record_type_id = db.Column(db.Integer, db.ForeignKey('record_types.id', ondelete='CASCADE'), nullable=False)
    view_name = db.Column(db.String(255))
    view_type = db.Column(db.String(50))
    configuration = db.Column(db.Text)


class RecordTypeAction(db.Model):
    """Record Type actions"""
    __tablename__ = 'record_type_actions'

    id = db.Column(db.Integer, primary_key=True)
    record_type_id = db.Column(db.Integer, db.ForeignKey('record_types.id', ondelete='CASCADE'), nullable=False)
    action_name = db.Column(db.String(255))
    action_type = db.Column(db.String(50))
    configuration = db.Column(db.Text)


class CDT(db.Model):
    """Custom Data Type objects"""
    __tablename__ = 'cdts'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    namespace = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    fields = db.relationship('CDTField', backref='cdt', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_cdt_object_package'),
        db.Index('idx_cdt_object_package', 'object_id', 'package_id'),
    )


class CDTField(db.Model):
    """CDT fields"""
    __tablename__ = 'cdt_fields'

    id = db.Column(db.Integer, primary_key=True)
    cdt_id = db.Column(db.Integer, db.ForeignKey('cdts.id', ondelete='CASCADE'), nullable=False)
    field_name = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.String(100))
    is_list = db.Column(db.Boolean, default=False)
    is_required = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer)


class Integration(db.Model):
    """Integration objects"""
    __tablename__ = 'integrations'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    sail_code = db.Column(db.Text)
    connection_info = db.Column(db.Text)
    authentication_info = db.Column(db.Text)
    endpoint = db.Column(db.String(500))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_integration_object_package'),
        db.Index('idx_integration_object_package', 'object_id', 'package_id'),
    )


class WebAPI(db.Model):
    """Web API objects"""
    __tablename__ = 'web_apis'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    sail_code = db.Column(db.Text)
    endpoint = db.Column(db.String(500))
    http_methods = db.Column(db.Text)  # JSON
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_web_api_object_package'),
        db.Index('idx_web_api_object_package', 'object_id', 'package_id'),
    )


class Site(db.Model):
    """Site objects"""
    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    page_hierarchy = db.Column(db.Text)  # JSON
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_site_object_package'),
        db.Index('idx_site_object_package', 'object_id', 'package_id'),
    )


class Group(db.Model):
    """Group objects"""
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    members = db.Column(db.Text)  # JSON
    parent_group_uuid = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_group_object_package'),
        db.Index('idx_group_object_package', 'object_id', 'package_id'),
    )


class Constant(db.Model):
    """Constant objects"""
    __tablename__ = 'constants'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    constant_value = db.Column(db.Text)
    constant_type = db.Column(db.String(100))
    scope = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_constant_object_package'),
        db.Index('idx_constant_object_package', 'object_id', 'package_id'),
    )


class ConnectedSystem(db.Model):
    """Connected System objects"""
    __tablename__ = 'connected_systems'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    system_type = db.Column(db.String(100))
    properties = db.Column(db.Text)  # JSON
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_connected_system_object_package'),
        db.Index('idx_connected_system_object_package', 'object_id', 'package_id'),
    )


class UnknownObject(db.Model):
    """Unknown object types"""
    __tablename__ = 'unknown_objects'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    raw_xml = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_unknown_object_object_package'),
        db.Index('idx_unknown_object_object_package', 'object_id', 'package_id'),
    )


class DataStore(db.Model):
    """Data Store objects"""
    __tablename__ = 'data_stores'

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id', ondelete='CASCADE'), nullable=False, index=True)
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    version_uuid = db.Column(db.String(255))
    description = db.Column(db.Text)
    connection_reference = db.Column(db.Text)
    configuration = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('object_id', 'package_id', name='uq_data_store_object_package'),
        db.Index('idx_data_store_object_package', 'object_id', 'package_id'),
    )


class DataStoreEntity(db.Model):
    """Data Store entity mappings"""
    __tablename__ = 'data_store_entities'

    id = db.Column(db.Integer, primary_key=True)
    data_store_id = db.Column(db.Integer, db.ForeignKey('data_stores.id', ondelete='CASCADE'), nullable=False, index=True)
    cdt_uuid = db.Column(db.String(255), nullable=False, index=True)
    table_name = db.Column(db.String(255), nullable=False)
    column_mappings = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================================
# Comparison Result Models
# ============================================================================

class InterfaceComparison(db.Model):
    """Interface comparison results"""
    __tablename__ = 'interface_comparisons'

    id = db.Column(db.Integer, primary_key=True)
    change_id = db.Column(db.Integer, db.ForeignKey('changes.id', ondelete='CASCADE'), nullable=False, unique=True)
    sail_code_diff = db.Column(db.Text)
    parameters_added = db.Column(db.Text)  # JSON
    parameters_removed = db.Column(db.Text)  # JSON
    parameters_modified = db.Column(db.Text)  # JSON
    security_changes = db.Column(db.Text)  # JSON


class ProcessModelComparison(db.Model):
    """Process Model comparison results"""
    __tablename__ = 'process_model_comparisons'

    id = db.Column(db.Integer, primary_key=True)
    change_id = db.Column(db.Integer, db.ForeignKey('changes.id', ondelete='CASCADE'), nullable=False, unique=True)
    nodes_added = db.Column(db.Text)  # JSON
    nodes_removed = db.Column(db.Text)  # JSON
    nodes_modified = db.Column(db.Text)  # JSON
    flows_added = db.Column(db.Text)  # JSON
    flows_removed = db.Column(db.Text)  # JSON
    flows_modified = db.Column(db.Text)  # JSON
    variables_changed = db.Column(db.Text)  # JSON
    mermaid_diagram = db.Column(db.Text)


class RecordTypeComparison(db.Model):
    """Record Type comparison results"""
    __tablename__ = 'record_type_comparisons'

    id = db.Column(db.Integer, primary_key=True)
    change_id = db.Column(db.Integer, db.ForeignKey('changes.id', ondelete='CASCADE'), nullable=False, unique=True)
    fields_changed = db.Column(db.Text)  # JSON
    relationships_changed = db.Column(db.Text)  # JSON
    views_changed = db.Column(db.Text)  # JSON
    actions_changed = db.Column(db.Text)  # JSON


class ExpressionRuleComparison(db.Model):
    """Expression Rule comparison results"""
    __tablename__ = 'expression_rule_comparisons'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    input_changes = db.Column(db.Text)  # JSON
    return_type_change = db.Column(db.Text)
    logic_diff = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('session_id', 'object_id', name='uq_ercomp_session_object'),
    )


class CDTComparison(db.Model):
    """CDT comparison results"""
    __tablename__ = 'cdt_comparisons'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    field_changes = db.Column(db.Text)  # JSON
    namespace_change = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('session_id', 'object_id', name='uq_cdtcomp_session_object'),
    )


class ConstantComparison(db.Model):
    """Constant comparison results"""
    __tablename__ = 'constant_comparisons'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object_lookup.id', ondelete='CASCADE'), nullable=False, index=True)
    base_value = db.Column(db.Text)
    customer_value = db.Column(db.Text)
    new_vendor_value = db.Column(db.Text)
    type_change = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('session_id', 'object_id', name='uq_constcomp_session_object'),
    )
