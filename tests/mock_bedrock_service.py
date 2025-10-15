"""
Mock Bedrock Service for Testing
"""

class MockBedrockService:
    """Mock Bedrock service for testing"""
    
    def query(self, action_type, query_text):
        """Mock query method"""
        return {
            'results': [
                {
                    'content': f'Mock result for {action_type}: {query_text[:50]}...',
                    'score': 0.95,
                    'source': 'test_document.pdf'
                }
            ],
            'summary': f'Mock summary for {action_type} query'
        }
