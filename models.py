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
    
    # Analysis results (JSON strings)
    base_blueprint = db.Column(db.Text)  # Blueprint A
    customized_blueprint = db.Column(db.Text)  # Blueprint B
    new_vendor_blueprint = db.Column(db.Text)  # Blueprint C
    
    vendor_changes = db.Column(db.Text)  # A→C comparison results
    customer_changes = db.Column(db.Text)  # A→B comparison results
    classification_results = db.Column(db.Text)  # Classified changes
    ordered_changes = db.Column(db.Text)  # Smart-ordered change list
    
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


class ChangeReview(db.Model):
    """Stores user review actions for each change"""
    __tablename__ = 'change_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('merge_sessions.id'), nullable=False, index=True)
    
    # Change identification
    object_uuid = db.Column(db.String(255), nullable=False)
    object_name = db.Column(db.String(255), nullable=False)
    object_type = db.Column(db.String(50), nullable=False)
    classification = db.Column(db.String(50), nullable=False)  # NO_CONFLICT, CONFLICT, etc.
    
    # Review status
    review_status = db.Column(db.String(20), default='pending')  # 'pending', 'reviewed', 'skipped'
    user_notes = db.Column(db.Text)
    
    # Timestamps
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'object_uuid': self.object_uuid,
            'object_name': self.object_name,
            'object_type': self.object_type,
            'classification': self.classification,
            'review_status': self.review_status,
            'user_notes': self.user_notes,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
