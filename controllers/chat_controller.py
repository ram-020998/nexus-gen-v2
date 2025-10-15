"""
Chat Controller - Handle AI chat assistant
"""
from flask import Blueprint, render_template, request, jsonify, session
from services.request_service import RequestService
from services.q_agent_service import QAgentService
from models import db, ChatSession
import uuid

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

request_service = RequestService()
q_agent_service = QAgentService()

@chat_bp.route('/')
def index():
    """Chat assistant page"""
    # Create or get session ID
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())
    
    # Get recent chat history
    chat_history = ChatSession.query.filter_by(
        session_id=session['chat_session_id']
    ).order_by(ChatSession.created_at.asc()).limit(20).all()
    
    return render_template('chat/index.html', chat_history=chat_history)

@chat_bp.route('/message', methods=['POST'])
def send_message():
    """Process chat message"""
    try:
        data = request.get_json()
        question = data.get('message', '').strip()
        
        if not question:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get or create session ID
        if 'chat_session_id' not in session:
            session['chat_session_id'] = str(uuid.uuid4())
        
        session_id = session['chat_session_id']
        
        # Process with Bedrock to get context
        bedrock_response = request_service.bedrock_service.query('chat', question)
        
        # Process with Q agent
        answer = q_agent_service.process_chat(question, bedrock_response)
        
        # Save chat session
        chat_session = ChatSession(
            session_id=session_id,
            question=question,
            rag_response=str(bedrock_response),
            answer=answer
        )
        
        db.session.add(chat_session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'answer': answer,
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/history')
def get_history():
    """Get chat history for current session"""
    if 'chat_session_id' not in session:
        return jsonify({'history': []})
    
    chat_history = ChatSession.query.filter_by(
        session_id=session['chat_session_id']
    ).order_by(ChatSession.created_at.asc()).all()
    
    return jsonify({
        'history': [chat.to_dict() for chat in chat_history]
    })

@chat_bp.route('/clear', methods=['POST'])
def clear_history():
    """Clear chat history for current session"""
    if 'chat_session_id' in session:
        ChatSession.query.filter_by(
            session_id=session['chat_session_id']
        ).delete()
        db.session.commit()
        
        # Create new session
        session['chat_session_id'] = str(uuid.uuid4())
    
    return jsonify({'success': True})
