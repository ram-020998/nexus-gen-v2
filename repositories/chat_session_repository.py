"""
Chat session repository for managing ChatSession model data access.

This module provides data access methods for the ChatSession model,
which handles AI assistant chat interactions.
"""

from typing import List, Optional
from datetime import datetime
from core.base_repository import BaseRepository
from models import ChatSession


class ChatSessionRepository(BaseRepository[ChatSession]):
    """
    Repository for ChatSession model operations.

    Provides data access methods for managing chat sessions with
    the AI assistant, including questions, RAG responses, and answers.

    Example:
        >>> repo = ChatSessionRepository()
        >>> session = repo.create(
        ...     session_id='550e8400-e29b-41d4-a716-446655440000',
        ...     question='How do I create a process model?',
        ...     rag_response='Context about process models...',
        ...     answer='To create a process model...'
        ... )
        >>> history = repo.get_by_session_id(session.session_id)
    """

    def __init__(self):
        """Initialize ChatSessionRepository with ChatSession model."""
        super().__init__(ChatSession)

    def get_by_session_id(self, session_id: str) -> List[ChatSession]:
        """
        Get all chat messages for a specific session.

        Args:
            session_id: UUID of the chat session

        Returns:
            List[ChatSession]: List of chat messages ordered by creation date

        Example:
            >>> messages = repo.get_by_session_id(
            ...     '550e8400-e29b-41d4-a716-446655440000'
            ... )
        """
        return (self.model_class.query
                .filter_by(session_id=session_id)
                .order_by(self.model_class.created_at.asc())
                .all())

    def get_recent_sessions(
        self,
        limit: int = 10
    ) -> List[ChatSession]:
        """
        Get most recent chat sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List[ChatSession]: List of recent chat sessions ordered
                by creation date

        Example:
            >>> recent = repo.get_recent_sessions(limit=5)
        """
        return (self.model_class.query
                .order_by(self.model_class.created_at.desc())
                .limit(limit)
                .all())

    def get_session_count(self, session_id: str) -> int:
        """
        Count messages in a specific session.

        Args:
            session_id: UUID of the chat session

        Returns:
            int: Number of messages in the session

        Example:
            >>> count = repo.get_session_count(
            ...     '550e8400-e29b-41d4-a716-446655440000'
            ... )
        """
        return self.count(session_id=session_id)

    def get_all_session_ids(self) -> List[str]:
        """
        Get all unique session IDs.

        Returns:
            List[str]: List of unique session IDs

        Example:
            >>> session_ids = repo.get_all_session_ids()
        """
        result = (self.db.session.query(self.model_class.session_id)
                  .distinct()
                  .all())
        return [row[0] for row in result]

    def get_sessions_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ChatSession]:
        """
        Get chat sessions within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List[ChatSession]: List of chat sessions created
                within the date range

        Example:
            >>> from datetime import datetime, timedelta
            >>> end = datetime.utcnow()
            >>> start = end - timedelta(days=7)
            >>> recent = repo.get_sessions_by_date_range(start, end)
        """
        return (self.model_class.query
                .filter(self.model_class.created_at >= start_date)
                .filter(self.model_class.created_at <= end_date)
                .order_by(self.model_class.created_at.desc())
                .all())

    def delete_session(self, session_id: str) -> int:
        """
        Delete all messages in a session.

        Args:
            session_id: UUID of the chat session to delete

        Returns:
            int: Number of messages deleted

        Example:
            >>> deleted_count = repo.delete_session(
            ...     '550e8400-e29b-41d4-a716-446655440000'
            ... )
        """
        messages = self.get_by_session_id(session_id)
        count = len(messages)
        for message in messages:
            self.db.session.delete(message)
        self.db.session.commit()
        return count

    def search_by_question(self, search_term: str) -> List[ChatSession]:
        """
        Search chat sessions by question content.

        Args:
            search_term: Term to search for in questions

        Returns:
            List[ChatSession]: List of chat sessions with matching questions

        Example:
            >>> results = repo.search_by_question('process model')
        """
        return (self.model_class.query
                .filter(self.model_class.question.contains(search_term))
                .order_by(self.model_class.created_at.desc())
                .all())

    def get_latest_by_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get the most recent message in a session.

        Args:
            session_id: UUID of the chat session

        Returns:
            Optional[ChatSession]: Latest message if found, None otherwise

        Example:
            >>> latest = repo.get_latest_by_session(
            ...     '550e8400-e29b-41d4-a716-446655440000'
            ... )
        """
        return (self.model_class.query
                .filter_by(session_id=session_id)
                .order_by(self.model_class.created_at.desc())
                .first())

    def update_answer(
        self,
        chat_id: int,
        answer: str
    ) -> Optional[ChatSession]:
        """
        Update the answer for a chat session.

        Args:
            chat_id: ID of the chat session to update
            answer: New answer text

        Returns:
            Optional[ChatSession]: Updated chat session if found,
                None otherwise

        Example:
            >>> chat = repo.update_answer(
            ...     chat_id=1,
            ...     answer='Updated answer text'
            ... )
        """
        chat = self.get_by_id(chat_id)
        if chat:
            chat.answer = answer
            self.update(chat)
        return chat

    def get_sessions_without_answers(self) -> List[ChatSession]:
        """
        Get all chat sessions that don't have answers yet.

        Returns:
            List[ChatSession]: List of chat sessions without answers

        Example:
            >>> unanswered = repo.get_sessions_without_answers()
        """
        return (self.model_class.query
                .filter(
                    (self.model_class.answer.is_(None)) |
                    (self.model_class.answer == '')
                )
                .order_by(self.model_class.created_at.desc())
                .all())
