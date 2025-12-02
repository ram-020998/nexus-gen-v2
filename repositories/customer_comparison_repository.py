"""
Customer Comparison Repository

Handles database operations for customer comparison results.
"""

from typing import List, Dict, Any
from core.base_repository import BaseRepository
from models import db, CustomerComparisonResult


class CustomerComparisonRepository(BaseRepository):
    """Repository for customer comparison results."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__(CustomerComparisonResult)
    
    def bulk_create_results(self, results: List[Dict[str, Any]]) -> None:
        """
        Bulk create customer comparison results.
        
        Args:
            results: List of result dictionaries
        """
        for result in results:
            record = CustomerComparisonResult(**result)
            db.session.add(record)
        
        db.session.flush()
    
    def get_by_session(self, session_id: int) -> List[CustomerComparisonResult]:
        """
        Get all customer comparison results for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of CustomerComparisonResult entities
        """
        return db.session.query(CustomerComparisonResult).filter_by(
            session_id=session_id
        ).all()
    
    def get_statistics(self, session_id: int) -> Dict[str, Any]:
        """
        Get statistics for customer comparison results.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Dict with statistics
        """
        from sqlalchemy import func
        
        # Total count
        total = db.session.query(CustomerComparisonResult).filter_by(
            session_id=session_id
        ).count()
        
        # Count by category
        results = db.session.query(
            CustomerComparisonResult.change_category,
            func.count(CustomerComparisonResult.id).label('count')
        ).filter_by(
            session_id=session_id
        ).group_by(
            CustomerComparisonResult.change_category
        ).all()
        
        by_category = {category: count for category, count in results}
        
        return {
            'total': total,
            'by_category': by_category
        }
