"""
Bedrock Knowledge Base RAG Service
"""
from typing import Dict, Any, Optional
from core.base_service import BaseService
from core.dependency_container import DependencyContainer

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception


class BedrockRAGService(BaseService):
    """Bedrock Knowledge Base RAG service with dependency injection"""

    def __init__(self, container: Optional[DependencyContainer] = None):
        """
        Initialize Bedrock RAG service
        
        Args:
            container: Dependency injection container
        """
        super().__init__(container)
        self.bedrock_client = None
        self._initialize_bedrock_client()

    def _initialize_dependencies(self):
        """Initialize service dependencies"""
        # Get configuration from container if needed
        pass

    def _initialize_bedrock_client(self):
        """Initialize Bedrock Agent Runtime client"""
        if not BOTO3_AVAILABLE:
            # Bedrock client not available - using fallback mode
            return
        
        try:
            from config import Config
            # Initialize Bedrock Agent Runtime client
            self.bedrock_client = boto3.client(
                'bedrock-agent-runtime',
                region_name=Config.AWS_REGION
            )
            # Bedrock client initialized
        except Exception:
            # Failed to initialize Bedrock client
            self.bedrock_client = None

    def query(self, action_type: str, query_text: str) -> Dict[str, Any]:
        """
        Query Bedrock Knowledge Base using retrieve method for detailed results
        
        Args:
            action_type: Type of action (breakdown, verify, create, chat)
            query_text: Query text to search for
            
        Returns:
            Dictionary containing query results with status, results, and summary
        """
        if not self.bedrock_client:
            return self._get_fallback_response(action_type)

        try:
            from config import Config
            # Use retrieve method to get detailed KB results like direct testing
            response = self.bedrock_client.retrieve(
                knowledgeBaseId=Config.BEDROCK_KB_ID,
                retrievalQuery={'text': query_text},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10
                    }
                }
            )

            return self._format_retrieve_response(response, action_type)

        except ClientError:
            # Bedrock API error
            return self._get_fallback_response(action_type)
        except Exception:
            # Unexpected error
            return self._get_fallback_response(action_type)

    def _format_retrieve_response(self, bedrock_response: dict, action_type: str) -> Dict[str, Any]:
        """
        Format Bedrock retrieve response to match expected structure
        
        Args:
            bedrock_response: Raw response from Bedrock API
            action_type: Type of action for context
            
        Returns:
            Formatted response dictionary
        """
        try:
            retrieval_results = bedrock_response.get('retrievalResults', [])

            # Extract content from retrieval results
            results = []
            for result in retrieval_results:
                content = result.get('content', {}).get('text', '')
                score = result.get('score', 0)
                location = result.get('location', {})

                results.append({
                    'content': content,
                    'score': score,
                    'source': location.get('s3Location', {}).get('uri', 'Unknown'),
                    'metadata': result.get('metadata', {})
                })

            # Create summary from top results
            summary_parts = []
            for i, result in enumerate(results[:3]):
                if result['content']:
                    summary_parts.append(f"[{i + 1}] {result['content'][:200]}...")

            summary = "Based on the retrieved results: " + \
                " ".join(summary_parts) if summary_parts else "No relevant information found."

            return {
                'status': 'success',
                'results': results,
                'summary': summary,
                'total_results': len(results)
            }

        except Exception:
            # Error formatting retrieve response
            return self._get_fallback_response(action_type)

    def _get_fallback_response(self, action_type: str) -> Dict[str, Any]:
        """
        Fallback response when Bedrock is unavailable
        
        Args:
            action_type: Type of action for context
            
        Returns:
            Fallback response dictionary
        """
        fallback_responses = {
            'breakdown': "Sample breakdown context for development",
            'verify': "Sample verification context for development",
            'create': "Sample creation context for development",
            'chat': "Sample chat context for development"
        }

        return {
            'status': 'fallback',
            'results': [{
                'content': fallback_responses.get(action_type, "Sample context"),
                'source': 'fallback',
                'metadata': {'type': 'fallback'}
            }],
            'summary': f"Using fallback response for {action_type} action"
        }
