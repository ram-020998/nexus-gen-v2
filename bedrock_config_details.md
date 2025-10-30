# AWS Bedrock Configuration Details

## 🔧 Service Configuration

### **1. AWS Service & Endpoint**
```python
# Service: AWS Bedrock Agent Runtime
service_name = 'bedrock-agent-runtime'

# Endpoint URL (automatically constructed by boto3)
# Format: https://bedrock-agent-runtime.{region}.amazonaws.com
endpoint_url = 'https://bedrock-agent-runtime.us-east-1.amazonaws.com'
```

### **2. Authentication**
```python
# Uses AWS Default Credential Chain:
# 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# 2. AWS credentials file (~/.aws/credentials)
# 3. IAM roles (if running on EC2/Lambda)
# 4. AWS CLI configuration

# Client initialization with automatic authentication
self.bedrock_client = boto3.client(
    'bedrock-agent-runtime',
    region_name='us-east-1'  # From config
)
```

### **3. Required IAM Permissions**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1:*:knowledge-base/WAQ6NJLGKN"
            ]
        }
    ]
}
```

## 📡 API Call Details

### **1. Retrieve Method (Primary)**
```python
response = self.bedrock_client.retrieve(
    knowledgeBaseId='WAQ6NJLGKN',           # Knowledge Base ID
    retrievalQuery={
        'text': 'Your search query here'    # Query text
    },
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 10,           # Max results to return
            'overrideSearchType': 'HYBRID'   # Optional: SEMANTIC, HYBRID
        }
    }
)
```

### **2. HTTP Request Details**
```http
POST https://bedrock-agent-runtime.us-east-1.amazonaws.com/knowledgebases/WAQ6NJLGKN/retrieve
Content-Type: application/x-amz-json-1.1
Authorization: AWS4-HMAC-SHA256 Credential=...
X-Amz-Target: AWSBedrockAgentRuntimeService.Retrieve

{
    "retrievalQuery": {
        "text": "Find similar spec breakdowns for: User authentication system..."
    },
    "retrievalConfiguration": {
        "vectorSearchConfiguration": {
            "numberOfResults": 10
        }
    }
}
```

### **3. Response Structure**
```json
{
    "retrievalResults": [
        {
            "content": {
                "text": "Document content from knowledge base..."
            },
            "location": {
                "type": "S3",
                "s3Location": {
                    "uri": "s3://your-bucket/path/document.pdf"
                }
            },
            "score": 0.85,
            "metadata": {
                "x-amz-bedrock-kb-source-uri": "s3://bucket/file.pdf"
            }
        }
    ],
    "nextToken": "optional-pagination-token"
}
```

## ⚙️ Configuration Parameters

### **1. Environment Variables**
```bash
# Required
export AWS_REGION=us-east-1
export BEDROCK_KB_ID=WAQ6NJLGKN

# Optional (if not using default credential chain)
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_SESSION_TOKEN=your-session-token  # If using temporary credentials
```

### **2. Boto3 Client Configuration**
```python
# Full client configuration options
self.bedrock_client = boto3.client(
    'bedrock-agent-runtime',
    region_name='us-east-1',
    aws_access_key_id='optional-override',
    aws_secret_access_key='optional-override',
    aws_session_token='optional-for-temp-creds',
    endpoint_url='https://bedrock-agent-runtime.us-east-1.amazonaws.com',
    config=Config(
        retries={'max_attempts': 3},
        read_timeout=60,
        connect_timeout=10
    )
)
```

### **3. Query Parameters**
```python
# Retrieval configuration options
retrievalConfiguration = {
    'vectorSearchConfiguration': {
        'numberOfResults': 10,              # 1-100, default 20
        'overrideSearchType': 'HYBRID',     # SEMANTIC, HYBRID
        'filter': {                         # Optional metadata filtering
            'equals': {
                'key': 'document_type',
                'value': 'specification'
            }
        }
    }
}
```

## 🔍 Query Processing Flow

### **1. Query Preparation**
```python
def _create_summary_query(self, document_text: str) -> str:
    # Truncate to 4000 chars max
    truncated = document_text[:4000]
    
    # Extract key terms
    key_terms = ['requirement', 'user story', 'epic', 'feature']
    found_terms = [term for term in key_terms if term in truncated.lower()]
    
    # Create optimized query
    if found_terms:
        return f"Key concepts: {', '.join(found_terms)}. Context: {truncated[:1000]}"
    return truncated[:1000]
```

### **2. Response Processing**
```python
def _format_response(self, bedrock_response: dict) -> dict:
    results = []
    for item in bedrock_response.get('retrievalResults', []):
        # Quality filtering - only scores > 0.6
        if item.get('score', 0) > 0.6:
            results.append({
                'content': item['content']['text'],
                'score': item['score'],
                'source': item['location']['s3Location']['uri'],
                'metadata': item.get('metadata', {})
            })
    
    return {
        'status': 'success',
        'results': results,
        'total_results': len(results)
    }
```

## 🛡️ Error Handling

### **1. Common Errors**
```python
try:
    response = self.bedrock_client.retrieve(...)
except ClientError as e:
    error_code = e.response['Error']['Code']
    
    if error_code == 'ValidationException':
        # Invalid parameters
    elif error_code == 'ResourceNotFoundException':
        # Knowledge base not found
    elif error_code == 'AccessDeniedException':
        # Insufficient permissions
    elif error_code == 'ThrottlingException':
        # Rate limit exceeded
```

### **2. Fallback Mechanism**
```python
def _get_fallback_response(self, action_type: str) -> dict:
    return {
        'status': 'fallback',
        'results': [{
            'content': f'Sample {action_type} context for development',
            'source': 'fallback',
            'metadata': {'type': 'fallback'}
        }],
        'summary': f'Using fallback response for {action_type} action'
    }
```

## 📊 Monitoring & Logging

### **1. Request Logging**
```python
logger.info(f"Bedrock query for {action_type}, query length: {len(query_text)}")
logger.debug(f"Summary query: {summary_query}")
logger.info(f"Bedrock query successful: {total_results} results")
```

### **2. Performance Tracking**
```python
# Track in ProcessTracker
tracker.start_step('Bedrock Query')
bedrock_response = self._execute_bedrock_query(query)
tracker.set_rag_metrics(bedrock_response.get('retrievalResults', []))
tracker.end_step('Bedrock Query')
```

This configuration provides secure, scalable access to AWS Bedrock Knowledge Base with proper error handling and monitoring.