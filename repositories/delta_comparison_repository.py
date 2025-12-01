"""
Delta Comparison Repository

Provides data access for delta_comparison_results table.
Stores results of A→C comparison (vendor delta).
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload
from models import db, DeltaComparisonResult, ObjectLookup
from repositories.base_repository import BaseRepository


class DeltaComparisonRepository(BaseRepository[DeltaComparisonResult]):
    """
    Repository for DeltaComparisonResult entities.
    
    Manages delta comparison results from A→C package comparison.
    Each result represents a change in the vendor package (NEW, MODIFIED, DEPRECATED).
    
    Key Methods:
        - create_result: Create single delta result
        - bulk_create_results: Optimized bulk creation
        - get_by_session: Get all delta results for a session
        - get_by_category: Filter by change category
        - count_by_category: Statistics by category
    """
    
    def __init__(self):
        """Initialize repository with DeltaComparisonResult model."""
        super().__init__(DeltaComparisonResult)
    
    def create_result(
        self,
        session_id: int,
        object_id: int,
        change_category: str,
        change_type: str,
        version_changed: bool = False,
        content_changed: bool = False
    ) -> DeltaComparisonResult:
        """
        Create a delta comparison result.
        
        Args:
            session_id: Merge session ID
            object_id: Object ID (from object_lookup)
            change_category: NEW, MODIFIED, or DEPRECATED
            change_type: ADDED, MODIFIED, or REMOVED
            version_changed: Whether version UUID changed
            content_changed: Whether content changed
            
        Returns:
            DeltaComparisonResult: Created result
            
        Example:
            >>> result = repo.create_result(
            ...     session_id=1,
            ...     object_id=42,
            ...     change_category="MODIFIED",
            ...     change_type="MODIFIED",
            ...     version_changed=True,
            ...     content_changed=True
            ... )
        """
        result = DeltaComparisonResult(
            session_id=session_id,
            object_id=object_id,
            change_category=change_category,
            change_type=change_type,
            version_changed=version_changed,
            content_changed=content_changed
        )
        self.db.session.add(result)
        self.db.session.flush()
        return result
    
    def bulk_create_results(
        self,
        results: List[Dict[str, Any]]
    ) -> None:
        """
        Optimized bulk creation of delta results.
        
        Args:
            results: List of dicts with keys:
                - session_id
                - object_id
                - change_category
                - change_type
                - version_changed (optional)
                - content_changed (optional)
                
        Example:
            >>> results = [
            ...     {
            ...         "session_id": 1,
            ...         "object_id": 10,
            ...         "change_category": "NEW",
            ...         "change_type": "ADDED"
            ...     },
            ...     {
            ...         "session_id": 1,
            ...         "object_id": 11,
            ...         "change_category": "MODIFIED",
            ...         "change_type": "MODIFIED",
            ...         "version_changed": True
            ...     }
            ... ]
            >>> repo.bulk_create_results(results)
        """
        if not results:
            return
        
        # Create result objects
        result_objects = [
            DeltaComparisonResult(
                session_id=r['session_id'],
                object_id=r['object_id'],
                change_category=r['change_category'],
                change_type=r['change_type'],
                version_changed=r.get('version_changed', False),
                content_changed=r.get('content_changed', False)
            )
            for r in results
        ]
        
        # Bulk insert
        self.db.session.bulk_save_objects(result_objects)
        self.db.session.flush()
    
    def get_by_session(
        self,
        session_id: int
    ) -> List[DeltaComparisonResult]:
        """
        Get all delta results for a session with eager loading.
        
        Uses joinedload to fetch object_lookup data in a single query.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of DeltaComparisonResult objects
            
        Example:
            >>> results = repo.get_by_session(session_id=1)
            >>> print(f"Found {len(results)} delta changes")
        """
        return self.db.session.query(DeltaComparisonResult).options(
            joinedload(DeltaComparisonResult.object)
        ).filter(
            DeltaComparisonResult.session_id == session_id
        ).all()
    
    def get_by_session_with_objects(
        self,
        session_id: int
    ) -> List[tuple]:
        """
        Get delta results with object details.
        
        Joins with object_lookup to include object name and type.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of tuples (DeltaComparisonResult, ObjectLookup)
            
        Example:
            >>> results = repo.get_by_session_with_objects(session_id=1)
            >>> for delta, obj in results:
            ...     print(f"{delta.change_category}: {obj.name}")
        """
        return self.db.session.query(
            DeltaComparisonResult,
            ObjectLookup
        ).join(
            ObjectLookup,
            DeltaComparisonResult.object_id == ObjectLookup.id
        ).filter(
            DeltaComparisonResult.session_id == session_id
        ).all()
    
    def get_by_category(
        self,
        session_id: int,
        change_category: str
    ) -> List[DeltaComparisonResult]:
        """
        Get delta results filtered by category with eager loading.
        
        Args:
            session_id: Merge session ID
            change_category: NEW, MODIFIED, or DEPRECATED
            
        Returns:
            List of DeltaComparisonResult objects
            
        Example:
            >>> new_objects = repo.get_by_category(
            ...     session_id=1,
            ...     change_category="NEW"
            ... )
        """
        return self.db.session.query(DeltaComparisonResult).options(
            joinedload(DeltaComparisonResult.object)
        ).filter(
            and_(
                DeltaComparisonResult.session_id == session_id,
                DeltaComparisonResult.change_category == change_category
            )
        ).all()
    
    def count_by_category(
        self,
        session_id: int
    ) -> Dict[str, int]:
        """
        Count delta results by category.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Dict mapping category to count
            
        Example:
            >>> counts = repo.count_by_category(session_id=1)
            >>> print(f"NEW: {counts.get('NEW', 0)}")
            >>> print(f"MODIFIED: {counts.get('MODIFIED', 0)}")
            >>> print(f"DEPRECATED: {counts.get('DEPRECATED', 0)}")
        """
        results = self.db.session.query(
            DeltaComparisonResult.change_category,
            func.count(DeltaComparisonResult.id).label('count')
        ).filter(
            DeltaComparisonResult.session_id == session_id
        ).group_by(
            DeltaComparisonResult.change_category
        ).all()
        
        return {category: count for category, count in results}
    
    def get_modified_with_version_change(
        self,
        session_id: int
    ) -> List[DeltaComparisonResult]:
        """
        Get MODIFIED objects where version changed with eager loading.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of DeltaComparisonResult objects
            
        Example:
            >>> results = repo.get_modified_with_version_change(session_id=1)
        """
        return self.db.session.query(DeltaComparisonResult).options(
            joinedload(DeltaComparisonResult.object)
        ).filter(
            and_(
                DeltaComparisonResult.session_id == session_id,
                DeltaComparisonResult.change_category == 'MODIFIED',
                DeltaComparisonResult.version_changed == True
            )
        ).all()
    
    def get_modified_with_content_change(
        self,
        session_id: int
    ) -> List[DeltaComparisonResult]:
        """
        Get MODIFIED objects where content changed (but version didn't) with eager loading.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of DeltaComparisonResult objects
            
        Example:
            >>> results = repo.get_modified_with_content_change(session_id=1)
        """
        return self.db.session.query(DeltaComparisonResult).options(
            joinedload(DeltaComparisonResult.object)
        ).filter(
            and_(
                DeltaComparisonResult.session_id == session_id,
                DeltaComparisonResult.change_category == 'MODIFIED',
                DeltaComparisonResult.content_changed == True
            )
        ).all()
    
    def find_by_object(
        self,
        session_id: int,
        object_id: int
    ) -> Optional[DeltaComparisonResult]:
        """
        Find delta result for a specific object.
        
        Args:
            session_id: Merge session ID
            object_id: Object ID
            
        Returns:
            DeltaComparisonResult if found, None otherwise
            
        Example:
            >>> result = repo.find_by_object(session_id=1, object_id=42)
            >>> if result:
            ...     print(f"Category: {result.change_category}")
        """
        return self.find_one(session_id=session_id, object_id=object_id)
    
    def count_total(
        self,
        session_id: int
    ) -> int:
        """
        Count total delta results for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Total count
            
        Example:
            >>> total = repo.count_total(session_id=1)
            >>> print(f"Total delta changes: {total}")
        """
        return self.count(session_id=session_id)
    
    def get_statistics(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Dict with statistics:
                - total: Total delta results
                - by_category: Count by category
                - version_changes: Count with version changes
                - content_changes: Count with content changes
                
        Example:
            >>> stats = repo.get_statistics(session_id=1)
            >>> print(f"Total: {stats['total']}")
            >>> print(f"NEW: {stats['by_category'].get('NEW', 0)}")
        """
        total = self.count_total(session_id)
        by_category = self.count_by_category(session_id)
        
        version_changes = self.db.session.query(
            func.count(DeltaComparisonResult.id)
        ).filter(
            and_(
                DeltaComparisonResult.session_id == session_id,
                DeltaComparisonResult.version_changed == True
            )
        ).scalar()
        
        content_changes = self.db.session.query(
            func.count(DeltaComparisonResult.id)
        ).filter(
            and_(
                DeltaComparisonResult.session_id == session_id,
                DeltaComparisonResult.content_changed == True
            )
        ).scalar()
        
        return {
            'total': total,
            'by_category': by_category,
            'version_changes': version_changes,
            'content_changes': content_changes
        }
    
    def delete_by_session(
        self,
        session_id: int
    ) -> int:
        """
        Delete all delta results for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Number of results deleted
            
        Example:
            >>> deleted = repo.delete_by_session(session_id=1)
        """
        count = self.count_total(session_id)
        self.db.session.query(DeltaComparisonResult).filter(
            DeltaComparisonResult.session_id == session_id
        ).delete()
        self.db.session.flush()
        return count
