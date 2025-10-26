"""
Process Tracking Service - Track processing timeline and metadata
"""
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional


class ProcessTracker:
    """Track processing steps and metadata for requests"""
    
    def __init__(self, request_id: int, action_type: str):
        self.request_id = request_id
        self.action_type = action_type
        self.start_time = time.time()
        self.steps = {}
        self.metadata = {
            'agent_name': None,
            'model_name': 'amazon.nova-pro-v1:0',  # Default
            'parameters': {
                'temperature': 0.2,
                'maxTokens': 4000,
                'topP': 0.8
            },
            'kb_id': 'WAQ6NJLGKN'
        }
        self.confidence_metrics = {
            'rag_similarity_avg': 0.0,
            'json_valid': True,
            'response_length': 0,
            'error_recovery_used': False
        }
        self.errors = []
        self.raw_agent_output = ""  # Store raw agent output
        
    def start_step(self, step_name: str):
        """Start timing a processing step"""
        self.steps[step_name] = {
            'start_time': time.time(),
            'end_time': None,
            'duration': None
        }
        
    def end_step(self, step_name: str):
        """End timing a processing step"""
        if step_name in self.steps:
            self.steps[step_name]['end_time'] = time.time()
            self.steps[step_name]['duration'] = round(
                self.steps[step_name]['end_time'] - self.steps[step_name]['start_time'], 2
            )
    
    def set_agent_metadata(self, agent_name: str, model_name: str = None):
        """Set agent and model information"""
        self.metadata['agent_name'] = agent_name
        if model_name:
            self.metadata['model_name'] = model_name
    
    def set_rag_metrics(self, results: list):
        """Calculate and set RAG similarity metrics"""
        if results:
            scores = [r.get('score', 0) for r in results if 'score' in r]
            if scores:
                self.confidence_metrics['rag_similarity_avg'] = round(sum(scores) / len(scores), 3)
    
    def set_json_validity(self, is_valid: bool):
        """Set JSON validity flag"""
        self.confidence_metrics['json_valid'] = is_valid
    
    def set_response_length(self, response: str):
        """Set response length metric"""
        if response:
            self.confidence_metrics['response_length'] = len(response.split())
    
    def add_error(self, error_msg: str, step: str = None):
        """Add error to tracking"""
        self.errors.append({
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'message': error_msg
        })
        self.confidence_metrics['error_recovery_used'] = True
    
    def get_total_time(self) -> float:
        """Get total processing time"""
        return round(time.time() - self.start_time, 2)
    
    def get_timeline_data(self) -> Dict[str, Any]:
        """Get formatted timeline data"""
        timeline = []
        for step_name, step_data in self.steps.items():
            if step_data['duration'] is not None:
                timeline.append({
                    'step': step_name,
                    'start_time': datetime.fromtimestamp(step_data['start_time']).strftime('%H:%M:%S'),
                    'end_time': datetime.fromtimestamp(step_data['end_time']).strftime('%H:%M:%S'),
                    'duration': step_data['duration']
                })
        return timeline
    
    def get_confidence_badges(self) -> Dict[str, str]:
        """Get confidence indicators as badge data"""
        badges = {}
        
        # RAG Similarity badge
        rag_score = self.confidence_metrics['rag_similarity_avg']
        if rag_score > 0.7:
            badges['rag_similarity'] = f"RAG Similarity: {rag_score:.2f} ✅"
        elif rag_score > 0.4:
            badges['rag_similarity'] = f"RAG Similarity: {rag_score:.2f} ⚠️"
        else:
            badges['rag_similarity'] = f"RAG Similarity: {rag_score:.2f} ❌"
        
        # JSON Validity badge
        if self.confidence_metrics['json_valid']:
            badges['json_validity'] = "Output Format: Valid JSON ✅"
        else:
            badges['json_validity'] = "Output Format: Invalid JSON ❌"
        
        # Processing Time badge
        total_time = self.get_total_time()
        if total_time < 30:
            badges['processing_time'] = f"Processing Time: {total_time}s ✅"
        elif total_time < 60:
            badges['processing_time'] = f"Processing Time: {total_time}s ⚠️"
        else:
            badges['processing_time'] = f"Processing Time: {total_time}s ❌"
        
        # Error Recovery badge
        if self.confidence_metrics['error_recovery_used']:
            badges['error_recovery'] = "Error Recovery: Yes ⚠️"
        else:
            badges['error_recovery'] = "Error Recovery: No ✅"
        
        return badges
    
    def get_summary_data(self) -> Dict[str, Any]:
        """Get complete summary for database storage"""
        return {
            'reference_id': f"RQ_{self.action_type.upper()[:2]}_{self.request_id:03d}",
            'agent_name': self.metadata['agent_name'],
            'model_name': self.metadata['model_name'],
            'parameters': json.dumps(self.metadata['parameters']),
            'total_time': int(self.get_total_time()),
            'step_durations': json.dumps(self.get_timeline_data()),
            'raw_agent_output': self.raw_agent_output,
            'rag_similarity_avg': self.confidence_metrics['rag_similarity_avg'],
            'json_valid': self.confidence_metrics['json_valid'],
            'error_log': json.dumps(self.errors) if self.errors else None
        }
