"""
Data Source Factory - Create RAG service instances
"""
from services.bedrock_rag_service import BedrockRAGService


class DataSourceFactory:
    """Factory for creating data source services"""

    @staticmethod
    def create_rag_service():
        """Create RAG service instance - only Bedrock supported"""
        # Using Bedrock Knowledge Base
        return BedrockRAGService()
