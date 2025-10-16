"""
Data Source Factory - Create RAG service instances
"""
from config import Config
from services.bedrock_rag_service import BedrockRAGService

class DataSourceFactory:
    """Factory for creating data source services"""
    
    @staticmethod
    def create_rag_service():
        """Create RAG service instance - only Bedrock supported"""
        data_source = Config.DATA_SOURCE
        print(f"Using Bedrock Knowledge Base (KB ID: {Config.BEDROCK_KB_ID})")
        return BedrockRAGService()
