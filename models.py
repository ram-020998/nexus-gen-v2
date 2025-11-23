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


class ComparisonRequest(db.Model):
    """Comparison requests table for Appian application analysis"""
    __tablename__ = 'comparison_requests'

    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(20), unique=True)  # CMP_001 format
    old_app_name = db.Column(db.String(255), nullable=False)
    new_app_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='processing')  # 'processing', 'completed', 'error'
    
    # Analysis results
    old_app_blueprint = db.Column(db.Text)  # JSON string
    new_app_blueprint = db.Column(db.Text)  # JSON string
    comparison_results = db.Column(db.Text)  # JSON string
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_time = db.Column(db.Integer)  # Processing time in seconds
    error_log = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'reference_id': self.reference_id,
            'old_app_name': self.old_app_name,
            'new_app_name': self.new_app_name,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'total_time': self.total_time
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


class MergeSession(db.Model):
    """Stores three-way merge session data"""
    __tablename__ = 'merge_sessions'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # MRG_001
    
    # Package information
    base_package_name = db.Column(db.String(255), nullable=False)  # A
    customized_package_name = db.Column(db.String(255), nullable=False)  # B
    new_vendor_package_name = db.Column(db.String(255), nullable=False)  # C
    
    # Status tracking
    status = db.Column(db.String(20), default='processing')  # 'processing', 'ready', 'in_progress', 'completed', 'error'
    current_change_index = db.Column(db.Integer, default=0)
    
    # Progress tracking
    total_changes = db.Column(db.Integer, default=0)
    reviewed_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    total_time = db.Column(db.Integer)  # seconds
    error_log = db.Column(db.Text)
    
    # Relationships
    packages = db.relationship('Package', backref='session', lazy=True, cascade='all, delete-orphan')
    changes = db.relationship('Change', backref='session', lazy=True, cascade='all, delete-orphan')
    change_reviews = db.relationship('ChangeReview', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'reference_id': self.reference_id,
            'base_package_name': self.base_package_name,
            'customized_package_name': self.customized_package_name,
            'new_vendor_package_name': self.new_vendor_package_name,
            'status': self.status,
            'current_change_index': self.current_change_index,
            'total_changes': self.total_changes,
            'reviewed_count': self.reviewed_count,
            'skipped_count': self.skipped_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_time': self.total_time
        }


class Package(db.Model):
    """Stores individual package information (A, B, or C)"""
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'), nullable=False, index=True)
    
    # Package identification
    package_type = db.Column(db.String(20), nullable=False)  # 'base', 'customized', 'new_vendor'
    package_name = db.Column(db.String(255), nullable=False)
    
    # Metadata from blueprint
    total_objects = db.Column(db.Integer, default=0)
    generation_time = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    objects = db.relationship('AppianObject', backref='package', lazy=True, cascade='all, delete-orphan')
    object_type_counts = db.relationship('PackageObjectTypeCount', backref='package', lazy=True, cascade='all, delete-orphan')
    dependencies = db.relationship('ObjectDependency', backref='package', lazy=True, cascade='all, delete-orphan')
    
    # Composite index for efficient lookups
    __table_args__ = (
        db.Index('idx_package_session_type', 'session_id', 'package_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'package_type': self.package_type,
            'package_name': self.package_name,
            'total_objects': self.total_objects,
            'generation_time': self.generation_time,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PackageObjectTypeCount(db.Model):
    """Stores object type counts for each package"""
    __tablename__ = 'package_object_type_counts'
    
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False, index=True)
    
    # Object type and count
    object_type = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint and index
    __table_args__ = (
        db.UniqueConstraint('package_id', 'object_type', name='uq_package_object_type'),
        db.Index('idx_package_type', 'package_id', 'object_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'package_id': self.package_id,
            'object_type': self.object_type,
            'count': self.count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AppianObject(db.Model):
    """Stores normalized Appian object data"""
    __tablename__ = 'appian_objects'
    
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False, index=True)
    
    # Object identification
    uuid = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False, index=True)
    object_type = db.Column(db.String(50), nullable=False, index=True)
    
    # Object content
    sail_code = db.Column(db.Text)  # For interfaces, expression rules
    fields = db.Column(db.Text)  # JSON: field definitions
    properties = db.Column(db.Text)  # JSON: object properties
    object_metadata = db.Column(db.Text)  # JSON: additional metadata
    
    # Version information
    version_uuid = db.Column(db.String(255), index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    dependencies_as_parent = db.relationship(
        'ObjectDependency',
        foreign_keys='ObjectDependency.parent_uuid',
        primaryjoin='AppianObject.uuid == foreign(ObjectDependency.parent_uuid)',
        backref='parent_object',
        lazy=True
    )
    dependencies_as_child = db.relationship(
        'ObjectDependency',
        foreign_keys='ObjectDependency.child_uuid',
        primaryjoin='AppianObject.uuid == foreign(ObjectDependency.child_uuid)',
        backref='child_object',
        lazy=True
    )
    process_model_metadata = db.relationship('ProcessModelMetadata', backref='appian_object', uselist=False, lazy=True, cascade='all, delete-orphan')
    
    # Composite unique constraint and indexes
    __table_args__ = (
        db.UniqueConstraint('package_id', 'uuid', name='uq_package_object'),
        db.Index('idx_object_type_name', 'object_type', 'name'),
        db.Index('idx_object_uuid', 'uuid'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'package_id': self.package_id,
            'uuid': self.uuid,
            'name': self.name,
            'object_type': self.object_type,
            'version_uuid': self.version_uuid,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ProcessModelMetadata(db.Model):
    """Stores process model metadata"""
    __tablename__ = 'process_model_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    appian_object_id = db.Column(db.Integer, db.ForeignKey('appian_objects.id'), nullable=False, unique=True, index=True)
    
    # Process model specific metadata
    total_nodes = db.Column(db.Integer, default=0)
    total_flows = db.Column(db.Integer, default=0)
    complexity_score = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    nodes = db.relationship('ProcessModelNode', backref='process_model', lazy=True, cascade='all, delete-orphan')
    flows = db.relationship('ProcessModelFlow', backref='process_model', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'appian_object_id': self.appian_object_id,
            'total_nodes': self.total_nodes,
            'total_flows': self.total_flows,
            'complexity_score': self.complexity_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ProcessModelNode(db.Model):
    """Stores individual process model nodes"""
    __tablename__ = 'process_model_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    process_model_id = db.Column(db.Integer, db.ForeignKey('process_model_metadata.id'), nullable=False, index=True)
    
    # Node identification
    node_id = db.Column(db.String(255), nullable=False)
    node_type = db.Column(db.String(100), nullable=False)
    node_name = db.Column(db.String(500))
    
    # Node properties
    properties = db.Column(db.Text)  # JSON: node-specific properties
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    outgoing_flows = db.relationship(
        'ProcessModelFlow',
        foreign_keys='ProcessModelFlow.from_node_id',
        backref='from_node',
        lazy=True
    )
    incoming_flows = db.relationship(
        'ProcessModelFlow',
        foreign_keys='ProcessModelFlow.to_node_id',
        backref='to_node',
        lazy=True
    )
    
    # Composite unique constraint and indexes
    __table_args__ = (
        db.UniqueConstraint('process_model_id', 'node_id', name='uq_process_model_node'),
        db.Index('idx_node_type', 'process_model_id', 'node_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_model_id': self.process_model_id,
            'node_id': self.node_id,
            'node_type': self.node_type,
            'node_name': self.node_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ProcessModelFlow(db.Model):
    """Stores process model flows (connections between nodes)"""
    __tablename__ = 'process_model_flows'
    
    id = db.Column(db.Integer, primary_key=True)
    process_model_id = db.Column(db.Integer, db.ForeignKey('process_model_metadata.id'), nullable=False, index=True)
    
    # Flow identification
    from_node_id = db.Column(db.Integer, db.ForeignKey('process_model_nodes.id'), nullable=False, index=True)
    to_node_id = db.Column(db.Integer, db.ForeignKey('process_model_nodes.id'), nullable=False, index=True)
    
    # Flow properties
    flow_label = db.Column(db.String(500))
    flow_condition = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite indexes
    __table_args__ = (
        db.Index('idx_flow_from', 'process_model_id', 'from_node_id'),
        db.Index('idx_flow_to', 'process_model_id', 'to_node_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_model_id': self.process_model_id,
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'flow_label': self.flow_label,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Change(db.Model):
    """Stores individual change records from comparison"""
    __tablename__ = 'changes'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'), nullable=False, index=True)
    
    # Object identification
    object_uuid = db.Column(db.String(255), nullable=False, index=True)
    object_name = db.Column(db.String(500), nullable=False, index=True)
    object_type = db.Column(db.String(50), nullable=False, index=True)
    
    # Change classification
    classification = db.Column(db.String(50), nullable=False, index=True)
    # Values: NO_CONFLICT, CONFLICT, CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED
    
    # Change details
    change_type = db.Column(db.String(20))  # ADDED, MODIFIED, REMOVED
    vendor_change_type = db.Column(db.String(20))  # A→C change type
    customer_change_type = db.Column(db.String(20))  # A→B change type
    
    # Object references (foreign keys to AppianObject)
    base_object_id = db.Column(db.Integer, db.ForeignKey('appian_objects.id'), index=True)
    customer_object_id = db.Column(db.Integer, db.ForeignKey('appian_objects.id'), index=True)
    vendor_object_id = db.Column(db.Integer, db.ForeignKey('appian_objects.id'), index=True)
    
    # Ordering
    display_order = db.Column(db.Integer, nullable=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    base_object = db.relationship('AppianObject', foreign_keys=[base_object_id], lazy=True)
    customer_object = db.relationship('AppianObject', foreign_keys=[customer_object_id], lazy=True)
    vendor_object = db.relationship('AppianObject', foreign_keys=[vendor_object_id], lazy=True)
    merge_guidance = db.relationship('MergeGuidance', backref='change', uselist=False, lazy=True, cascade='all, delete-orphan')
    review = db.relationship('ChangeReview', backref='change', uselist=False, cascade='all, delete-orphan')
    
    # Composite indexes for efficient queries
    __table_args__ = (
        db.Index('idx_change_session_classification', 'session_id', 'classification'),
        db.Index('idx_change_session_type', 'session_id', 'object_type'),
        db.Index('idx_change_session_order', 'session_id', 'display_order'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'object_uuid': self.object_uuid,
            'object_name': self.object_name,
            'object_type': self.object_type,
            'classification': self.classification,
            'change_type': self.change_type,
            'vendor_change_type': self.vendor_change_type,
            'customer_change_type': self.customer_change_type,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MergeGuidance(db.Model):
    """Stores merge guidance for a change"""
    __tablename__ = 'merge_guidance'
    
    id = db.Column(db.Integer, primary_key=True)
    change_id = db.Column(db.Integer, db.ForeignKey('changes.id'), nullable=False, unique=True, index=True)
    
    # Guidance information
    recommendation = db.Column(db.String(100))  # e.g., "ACCEPT_VENDOR", "MANUAL_MERGE"
    reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conflicts = db.relationship('MergeConflict', backref='guidance', lazy=True, cascade='all, delete-orphan')
    changes = db.relationship('MergeChange', backref='guidance', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'change_id': self.change_id,
            'recommendation': self.recommendation,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MergeConflict(db.Model):
    """Stores individual conflicts within merge guidance"""
    __tablename__ = 'merge_conflicts'
    
    id = db.Column(db.Integer, primary_key=True)
    guidance_id = db.Column(db.Integer, db.ForeignKey('merge_guidance.id'), nullable=False, index=True)
    
    # Conflict details
    field_name = db.Column(db.String(255))
    conflict_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'guidance_id': self.guidance_id,
            'field_name': self.field_name,
            'conflict_type': self.conflict_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MergeChange(db.Model):
    """Stores individual changes within merge guidance"""
    __tablename__ = 'merge_changes'
    
    id = db.Column(db.Integer, primary_key=True)
    guidance_id = db.Column(db.Integer, db.ForeignKey('merge_guidance.id'), nullable=False, index=True)
    
    # Change details
    field_name = db.Column(db.String(255))
    change_description = db.Column(db.Text)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'guidance_id': self.guidance_id,
            'field_name': self.field_name,
            'change_description': self.change_description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ObjectDependency(db.Model):
    """Stores relationships between Appian objects"""
    __tablename__ = 'object_dependencies'
    
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False, index=True)
    
    # Dependency relationship
    parent_uuid = db.Column(db.String(255), nullable=False, index=True)
    child_uuid = db.Column(db.String(255), nullable=False, index=True)
    
    # Dependency type
    dependency_type = db.Column(db.String(50))  # 'reference', 'contains', etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite indexes
    __table_args__ = (
        db.Index('idx_dependency_parent', 'package_id', 'parent_uuid'),
        db.Index('idx_dependency_child', 'package_id', 'child_uuid'),
        db.UniqueConstraint('package_id', 'parent_uuid', 'child_uuid', name='uq_dependency'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'package_id': self.package_id,
            'parent_uuid': self.parent_uuid,
            'child_uuid': self.child_uuid,
            'dependency_type': self.dependency_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ChangeReview(db.Model):
    """Stores user review actions for each change"""
    __tablename__ = 'change_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'), nullable=False, index=True)
    change_id = db.Column(db.Integer, db.ForeignKey('changes.id'), unique=True, index=True)
    
    # Legacy fields (kept for backward compatibility during migration)
    object_uuid = db.Column(db.String(255))
    object_name = db.Column(db.String(255))
    object_type = db.Column(db.String(50))
    classification = db.Column(db.String(50))  # NO_CONFLICT, CONFLICT, etc.
    
    # Review status
    review_status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'reviewed', 'skipped'
    user_notes = db.Column(db.Text)
    
    # Timestamps
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite index
    __table_args__ = (
        db.Index('idx_review_session_status', 'session_id', 'review_status'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'change_id': self.change_id,
            'object_uuid': self.object_uuid,
            'object_name': self.object_name,
            'object_type': self.object_type,
            'classification': self.classification,
            'review_status': self.review_status,
            'user_notes': self.user_notes,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
