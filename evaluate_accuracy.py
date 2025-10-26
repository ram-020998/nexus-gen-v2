#!/usr/bin/env python3
"""
Continuous Tuning Evaluation Script
Tracks accuracy metrics for NexusGen outputs
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from services.q_agent_service import QAgentService
from services.bedrock_rag_service import BedrockRAGService
from services.document_service import DocumentService

logger = logging.getLogger(__name__)

class AccuracyEvaluator:
    """Evaluate and track accuracy metrics"""
    
    def __init__(self):
        self.q_service = QAgentService()
        self.rag_service = BedrockRAGService()
        self.doc_service = DocumentService()
        self.metrics_file = Path("accuracy_metrics.json")
    
    def evaluate_json_validity(self, output_dir: Path) -> dict:
        """Evaluate JSON validity rate"""
        json_files = list(output_dir.glob("*/*.json"))
        valid_count = 0
        total_count = len(json_files)
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    json.load(f)
                valid_count += 1
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON: {json_file}")
        
        return {
            "valid_json_rate": valid_count / total_count if total_count > 0 else 0,
            "total_files": total_count,
            "valid_files": valid_count
        }
    
    def evaluate_bedrock_relevance(self, test_queries: list) -> dict:
        """Evaluate Bedrock RAG relevance scores"""
        scores = []
        
        for query in test_queries:
            result = self.rag_service.query("breakdown", query)
            if result.get('status') == 'success':
                results = result.get('results', [])
                if results:
                    avg_score = sum(r.get('score', 0) for r in results) / len(results)
                    scores.append(avg_score)
        
        return {
            "avg_relevance_score": sum(scores) / len(scores) if scores else 0,
            "queries_processed": len(scores),
            "high_relevance_rate": sum(1 for s in scores if s > 0.7) / len(scores) if scores else 0
        }
    
    def evaluate_output_consistency(self, test_file: str, iterations: int = 3) -> dict:
        """Evaluate output consistency across multiple runs"""
        if not Path(test_file).exists():
            return {"consistency_rate": 0, "error": "Test file not found"}
        
        content = self.doc_service.extract_content(test_file)
        bedrock_context = self.rag_service.query("breakdown", content)
        
        outputs = []
        for i in range(iterations):
            result, tracker = self.q_service.process_breakdown(9999 + i, content, bedrock_context)
            outputs.append(result)
        
        # Simple consistency check - compare structure
        consistent_count = 0
        base_keys = set(outputs[0].keys()) if outputs else set()
        
        for output in outputs[1:]:
            if set(output.keys()) == base_keys:
                consistent_count += 1
        
        return {
            "consistency_rate": consistent_count / (iterations - 1) if iterations > 1 else 0,
            "iterations": iterations
        }
    
    def run_evaluation(self) -> dict:
        """Run complete evaluation suite"""
        timestamp = datetime.now().isoformat()
        logger.info("Starting accuracy evaluation")
        
        # Test queries for Bedrock evaluation
        test_queries = [
            "user story acceptance criteria requirements",
            "design document verification components",
            "system architecture objects services"
        ]
        
        # Run evaluations
        json_metrics = self.evaluate_json_validity(Path("outputs"))
        bedrock_metrics = self.evaluate_bedrock_relevance(test_queries)
        
        # Try consistency evaluation with a test file
        test_file = "uploads/1_test.txt"
        consistency_metrics = self.evaluate_output_consistency(test_file)
        
        evaluation_result = {
            "timestamp": timestamp,
            "json_validity": json_metrics,
            "bedrock_relevance": bedrock_metrics,
            "output_consistency": consistency_metrics
        }
        
        # Save metrics
        self.save_metrics(evaluation_result)
        
        logger.info(f"Evaluation completed: JSON validity {json_metrics['valid_json_rate']:.2%}")
        return evaluation_result
    
    def save_metrics(self, metrics: dict):
        """Save metrics to file"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(metrics)
        
        # Keep only last 50 evaluations
        if len(history) > 50:
            history = history[-50:]
        
        with open(self.metrics_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def print_summary(self):
        """Print evaluation summary"""
        if not self.metrics_file.exists():
            print("No evaluation history found")
            return
        
        with open(self.metrics_file, 'r') as f:
            history = json.load(f)
        
        if not history:
            print("No evaluation data available")
            return
        
        latest = history[-1]
        print(f"\n=== Latest Evaluation ({latest['timestamp'][:19]}) ===")
        print(f"JSON Validity Rate: {latest['json_validity']['valid_json_rate']:.2%}")
        print(f"Bedrock Avg Relevance: {latest['bedrock_relevance']['avg_relevance_score']:.3f}")
        print(f"Output Consistency: {latest['output_consistency']['consistency_rate']:.2%}")
        
        if len(history) > 1:
            prev = history[-2]
            json_change = latest['json_validity']['valid_json_rate'] - prev['json_validity']['valid_json_rate']
            print(f"JSON Validity Change: {json_change:+.2%}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    evaluator = AccuracyEvaluator()
    evaluator.run_evaluation()
    evaluator.print_summary()
