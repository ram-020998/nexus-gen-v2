"""
Bedrock Knowledge Base RAG Service
"""
from typing import Dict, Any
from config import Config

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception


class BedrockRAGService:
    """Bedrock Knowledge Base RAG service"""

    def __init__(self):
        self.config = Config
        if not BOTO3_AVAILABLE:
            self.bedrock_client = None
            # Bedrock client not available - using fallback mode
        else:
            try:
                # Initialize Bedrock Agent Runtime client
                self.bedrock_client = boto3.client(
                    'bedrock-agent-runtime',
                    region_name=self.config.AWS_REGION
                )
                # Bedrock client initialized
            except Exception:
                # Failed to initialize Bedrock client
                self.bedrock_client = None

    def query(self, action_type: str, query_text: str) -> Dict[str, Any]:
        """Query Bedrock Knowledge Base using retrieve method for detailed results"""
        if not self.bedrock_client:
            return self._get_fallback_response(action_type)

        try:
            # Use retrieve method to get detailed KB results like direct testing
            response = self.bedrock_client.retrieve(
                knowledgeBaseId=self.config.BEDROCK_KB_ID,
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
        """Format Bedrock retrieve response to match expected structure"""
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
        """Fallback response when Bedrock is unavailable"""
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
