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
