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

    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'filename': self.filename,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'export_path': self.export_path
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
