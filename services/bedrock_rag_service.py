"""
Bedrock Knowledge Base RAG Service
"""
import logging
from typing import Dict, Any
from config import Config

# Configure logging
logger = logging.getLogger(__name__)

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
        logger.info(f"Bedrock query for {action_type}, query length: {len(query_text)}")
        
        if not self.bedrock_client:
            logger.warning("Bedrock client unavailable, using fallback")
            return self._get_fallback_response(action_type)

        try:
            # Create summary query for better relevance
            summary_query = self._create_summary_query(query_text)
            logger.debug(f"Summary query created, length: {len(summary_query)}")
            
            # Use retrieve method to get detailed KB results like direct testing
            response = self.bedrock_client.retrieve(
                knowledgeBaseId=self.config.BEDROCK_KB_ID,
                retrievalQuery={'text': summary_query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10
                    }
                }
            )

            result = self._format_retrieve_response(response, action_type)
            total_results = result.get('total_results', 0)
            logger.info(f"Bedrock query successful: {total_results} results")
            return result

        except ClientError as e:
            logger.error(f"Bedrock API error: {str(e)}")
            return self._get_fallback_response(action_type)
        except Exception as e:
            logger.error(f"Unexpected Bedrock error: {str(e)}")
            return self._get_fallback_response(action_type)

    def _create_summary_query(self, document_text: str) -> str:
        """Create a focused summary query for better Bedrock retrieval"""
        # Truncate long documents and extract key terms
        truncated_text = document_text[:4000] if len(document_text) > 4000 else document_text
        
        # Extract key terms (simple approach)
        key_terms = []
        common_patterns = ['requirement', 'acceptance criteria', 'user story', 'epic', 'feature', 'design', 'component']
        
        for pattern in common_patterns:
            if pattern.lower() in truncated_text.lower():
                key_terms.append(pattern)
        
        if key_terms:
            return f"Key concepts: {', '.join(key_terms)}. Context: {truncated_text[:1000]}"
        else:
            return truncated_text[:1000]

    def _format_retrieve_response(self, bedrock_response: dict, action_type: str) -> Dict[str, Any]:
        """Format Bedrock retrieve response to match expected structure"""
        try:
            retrieval_results = bedrock_response.get('retrievalResults', [])

            # Extract content from retrieval results with similarity filtering
            results = []
            for result in retrieval_results:
                content = result.get('content', {}).get('text', '')
                score = result.get('score', 0)
                location = result.get('location', {})

                # Apply similarity filtering - only include high-quality matches
                if score > 0.6:  # Threshold for relevance
                    results.append({
                        'content': content,
                        'score': score,
                        'source': location.get('s3Location', {}).get('uri', 'Unknown'),
                        'metadata': result.get('metadata', {})
                    })

            # If no high-quality matches, fall back to default prompt
            if not results:
                return self._get_fallback_response(action_type)

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
