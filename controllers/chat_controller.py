"""
Chat Controller - Handle AI chat assistant
"""
from flask import Blueprint, request, session
from controllers.base_controller import BaseController
from services.request.request_service import RequestService
from services.ai.q_agent_service import QAgentService
from repositories.chat_session_repository import ChatSessionRepository
from models import db
import uuid

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Create controller instance
controller = BaseController()


@chat_bp.route('/')
def index():
    """Chat assistant page"""
    # Access repository through base controller
    chat_session_repo = controller.get_repository(ChatSessionRepository)
    
    # Create or get session ID
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())

    # Get recent chat history (limited to 20 most recent)
    all_history = chat_session_repo.get_by_session_id(
        session['chat_session_id']
    )
    chat_history = all_history[-20:] if len(all_history) > 20 else all_history

    return controller.render('chat/index.html', chat_history=chat_history)


@chat_bp.route('/message', methods=['POST'])
def send_message():
    """Process chat message"""
    try:
        # Access services and repositories through base controller
        request_service = controller.get_service(RequestService)
        q_agent_service = controller.get_service(QAgentService)
        chat_session_repo = controller.get_repository(ChatSessionRepository)
        
        data = request.get_json()
        question = data.get('message', '').strip()

        if not question:
            return controller.json_error('No message provided', status_code=400)

        # Get or create session ID
        if 'chat_session_id' not in session:
            session['chat_session_id'] = str(uuid.uuid4())

        session_id = session['chat_session_id']

        # Process with Bedrock to get context
        bedrock_response = request_service.bedrock_service.query('chat', question)

        # Process with Q agent
        answer = q_agent_service.process_chat(question, bedrock_response)

        # Save chat session
        chat_session_repo.create(
            session_id=session_id,
            question=question,
            rag_response=str(bedrock_response),
            answer=answer
        )

        # Return with answer at top level for backward compatibility
        return controller.json_response(
            success=True,
            answer=answer,
            session_id=session_id
        )

    except Exception as e:
        return controller.handle_error(e, return_json=True)


@chat_bp.route('/history')
def get_history():
    """Get chat history for current session"""
    # Access repository through base controller
    chat_session_repo = controller.get_repository(ChatSessionRepository)
    
    if 'chat_session_id' not in session:
        return controller.json_success(data={'history': []})

    chat_history = chat_session_repo.get_by_session_id(
        session['chat_session_id']
    )

    return controller.json_success(
        data={'history': [chat.to_dict() for chat in chat_history]}
    )


@chat_bp.route('/clear', methods=['POST'])
def clear_history():
    """Clear chat history for current session"""
    # Access repository through base controller
    chat_session_repo = controller.get_repository(ChatSessionRepository)
    
    if 'chat_session_id' in session:
        chat_session_repo.delete_session(session['chat_session_id'])

        # Create new session
        session['chat_session_id'] = str(uuid.uuid4())

    return controller.json_success()
