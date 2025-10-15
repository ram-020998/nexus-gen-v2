"""
Bedrock RAG Service - Amazon Bedrock Knowledge Base integration
"""
import json
import time
from typing import Dict, List, Any
from config import Config

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

class BedrockRAGService:
    """Bedrock Knowledge Base RAG service"""
    
    def __init__(self):
        self.config = Config
        if not BOTO3_AVAILABLE:
            print("Warning: boto3 not available, falling back to mock responses")
            self.bedrock_client = None
        else:
            try:
                self.bedrock_client = boto3.client(
                    'bedrock-agent-runtime',
                    region_name=self.config.AWS_REGION
                )
            except (NoCredentialsError, Exception) as e:
                print(f"Warning: Could not initialize Bedrock client: {e}")
                self.bedrock_client = None
    
    def query(self, action_type: str, query_text: str) -> Dict[str, Any]:
        """Query Bedrock Knowledge Base"""
        if not self.bedrock_client:
            return self._get_fallback_response(action_type)
        
        try:
            response = self.bedrock_client.retrieve_and_generate(
                input={'text': query_text},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.config.BEDROCK_KB_ID,
                        'modelArn': f'arn:aws:bedrock:{self.config.AWS_REGION}::foundation-model/amazon.nova-pro-v1:0'
                    }
                }
            )
            
            return self._format_bedrock_response(response, action_type)
            
        except ClientError as e:
            print(f"Bedrock API error: {e}")
            return self._get_fallback_response(action_type)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return self._get_fallback_response(action_type)
    
    def _format_bedrock_response(self, bedrock_response: dict, action_type: str) -> Dict[str, Any]:
        """Format Bedrock response to match expected structure"""
        try:
            output_text = bedrock_response.get('output', {}).get('text', '')
            citations = bedrock_response.get('citations', [])
            
            # Extract relevant information from citations
            results = []
            for citation in citations[:3]:  # Limit to top 3 results
                for reference in citation.get('retrievedReferences', []):
                    content = reference.get('content', {}).get('text', '')
                    location = reference.get('location', {})
                    
                    results.append({
                        'document_id': location.get('s3Location', {}).get('uri', 'unknown'),
                        'title': f"{action_type.title()} Reference",
                        'content': content[:500] + '...' if len(content) > 500 else content,
                        'similarity_score': 0.85,  # Bedrock doesn't provide scores
                        'metadata': {
                            'type': action_type,
                            'source': 'bedrock_kb'
                        }
                    })
            
            return {
                'status': 'success',
                'results': results,
                'summary': output_text[:200] + '...' if len(output_text) > 200 else output_text
            }
            
        except Exception as e:
            print(f"Error formatting Bedrock response: {e}")
            return self._get_fallback_response(action_type)
    
    def _get_fallback_response(self, action_type: str) -> Dict[str, Any]:
        """Fallback response when Bedrock is unavailable"""
        fallback_responses = {
            'breakdown': {
                'status': 'success',
                'results': [{
                    'document_id': 'fallback_001',
                    'title': 'Fallback Spec Breakdown Pattern',
                    'content': 'Epic: Feature Implementation\nStory: Core functionality\nAcceptance Criteria: GIVEN system is ready WHEN user performs action THEN expected result occurs',
                    'similarity_score': 0.7,
                    'metadata': {'type': 'breakdown', 'source': 'fallback'}
                }],
                'summary': 'Using fallback breakdown pattern (Bedrock unavailable)'
            },
            'verify': {
                'status': 'success',
                'results': [{
                    'document_id': 'fallback_002',
                    'title': 'Fallback Design Verification',
                    'content': 'Standard verification checks: Error handling, validation, logging components',
                    'similarity_score': 0.7,
                    'metadata': {'type': 'verification', 'source': 'fallback'}
                }],
                'summary': 'Using fallback verification pattern (Bedrock unavailable)'
            },
            'create': {
                'status': 'success',
                'results': [{
                    'document_id': 'fallback_003',
                    'title': 'Fallback Design Template',
                    'content': 'Standard objects: Service, Validator, Manager components',
                    'similarity_score': 0.7,
                    'metadata': {'type': 'template', 'source': 'fallback'}
                }],
                'summary': 'Using fallback design template (Bedrock unavailable)'
            },
            'chat': {
                'status': 'success',
                'results': [{
                    'document_id': 'fallback_004',
                    'title': 'Fallback Documentation',
                    'content': 'General documentation context available',
                    'similarity_score': 0.7,
                    'metadata': {'type': 'documentation', 'source': 'fallback'}
                }],
                'summary': 'Using fallback documentation context (Bedrock unavailable)'
            }
        }
        
        return fallback_responses.get(action_type, {
            'status': 'error',
            'results': [],
            'summary': 'Service unavailable'
        })
