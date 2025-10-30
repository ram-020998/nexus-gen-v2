"""
Request Service - Manage breakdown/verify/create requests
"""
from models import db, Request
from services.data_source_factory import DataSourceFactory
from datetime import datetime


class RequestService:
    """Handle request operations"""

    def __init__(self):
        self.bedrock_service = DataSourceFactory.create_rag_service()

    def create_request(self, action_type: str, filename: str = None, input_text: str = None) -> Request:
        """Create a new request"""
        request = Request(
            action_type=action_type,
            filename=filename,
            input_text=input_text,
            status='processing'
        )

        db.session.add(request)
        db.session.commit()

        return request

    def update_request_status(self, request_id: int, status: str, output_data: str = None) -> Request:
        """Update request status and output"""
        request = Request.query.get(request_id)
        if request:
            request.status = status
            request.updated_at = datetime.utcnow()
            if output_data:
                request.final_output = output_data

            db.session.commit()

        return request

    def get_request(self, request_id: int) -> Request:
        """Get request by ID"""
        return Request.query.get(request_id)

    def get_recent_requests(self, action_type: str = None, limit: int = 10) -> list:
        """Get recent requests"""
        query = Request.query

        if action_type:
            query = query.filter_by(action_type=action_type)

        return query.order_by(Request.created_at.desc()).limit(limit).all()

    def process_with_bedrock(self, request: Request, query_text: str) -> dict:
        """Process request with Bedrock service"""
        # Query Bedrock service
        bedrock_response = self.bedrock_service.query(request.action_type, query_text)

        # Update request with Bedrock data
        request.rag_query = query_text
        request.rag_response = str(bedrock_response)
        db.session.commit()

        return bedrock_response
