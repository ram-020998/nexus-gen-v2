"""
Change Repository

Provides data access for changes table (working set).
Stores classified changes for user review.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload
from models import db, Change, ObjectLookup
from repositories.base_repository import BaseRepository


class ChangeRepository(BaseRepository[Change]):
    """
    Repository for Change entities.
    
    Manages the working set of classified changes for user review.
    Each change represents a delta object with classification applied.
    
    Key Methods:
        - create_change: Create single change
        - bulk_create_changes: Optimized bulk creation
        - get_by_session: Get all changes for a session
        - get_by_classification: Filter by classification
        - get_ordered_changes: Get changes in display order
    """
    
    def __init__(self):
        """Initialize repository with Change model."""
        super().__init__(Change)
    
    def create_change(
        self,
        session_id: int,
        object_id: int,
        classification: str,
        display_order: int,
        vendor_change_type: Optional[str] = None,
        customer_change_type: Optional[str] = None,
        change_type: Optional[str] = None
    ) -> Change:
        """
        Create a change record.
        
        Args:
            session_id: Merge session ID
            object_id: Object ID (from object_lookup)
            classification: NO_CONFLICT, CONFLICT, NEW, or DELETED
            display_order: Order for presentation
            vendor_change_type: ADDED, MODIFIED, or REMOVED
            customer_change_type: ADDED, MODIFIED, or REMOVED
            change_type: Legacy field (optional)
            
        Returns:
            Change: Created change
            
        Example:
            >>> change = repo.create_change(
            ...     session_id=1,
            ...     object_id=42,
            ...     classification="CONFLICT",
            ...     display_order=1,
            ...     vendor_change_type="MODIFIED",
            ...     customer_change_type="MODIFIED"
            ... )
        """
        change = Change(
            session_id=session_id,
            object_id=object_id,
            classification=classification,
            display_order=display_order,
            vendor_change_type=vendor_change_type,
            customer_change_type=customer_change_type,
            change_type=change_type
        )
        self.db.session.add(change)
        self.db.session.flush()
        return change
    
    def bulk_create_changes(
        self,
        changes: List[Dict[str, Any]]
    ) -> None:
        """
        Optimized bulk creation of changes.
        
        Args:
            changes: List of dicts with keys:
                - session_id
                - object_id
                - classification
                - display_order
                - vendor_change_type (optional)
                - customer_change_type (optional)
                - change_type (optional)
                
        Example:
            >>> changes = [
            ...     {
            ...         "session_id": 1,
            ...         "object_id": 10,
            ...         "classification": "NEW",
            ...         "display_order": 1,
            ...         "vendor_change_type": "ADDED"
            ...     },
            ...     {
            ...         "session_id": 1,
            ...         "object_id": 11,
            ...         "classification": "CONFLICT",
            ...         "display_order": 2,
            ...         "vendor_change_type": "MODIFIED",
            ...         "customer_change_type": "MODIFIED"
            ...     }
            ... ]
            >>> repo.bulk_create_changes(changes)
        """
        if not changes:
            return
        
        # Create change objects
        change_objects = [
            Change(
                session_id=c['session_id'],
                object_id=c['object_id'],
                classification=c['classification'],
                display_order=c['display_order'],
                vendor_change_type=c.get('vendor_change_type'),
                customer_change_type=c.get('customer_change_type'),
                change_type=c.get('change_type')
            )
            for c in changes
        ]
        
        # Bulk insert
        self.db.session.bulk_save_objects(change_objects)
        self.db.session.flush()
    
    def get_by_session(
        self,
        session_id: int
    ) -> List[Change]:
        """
        Get all changes for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of Change objects
            
        Example:
            >>> changes = repo.get_by_session(session_id=1)
            >>> print(f"Found {len(changes)} changes")
        """
        return self.filter_by(session_id=session_id)
    
    def get_ordered_changes(
        self,
        session_id: int
    ) -> List[Change]:
        """
        Get changes in display order with eager loading of related objects.
        
        Uses joinedload to fetch object_lookup data in a single query,
        avoiding N+1 query problem.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of Change objects ordered by display_order
            
        Example:
            >>> changes = repo.get_ordered_changes(session_id=1)
            >>> for i, change in enumerate(changes, 1):
            ...     print(f"{i}. {change.object.name}")
        """
        return self.db.session.query(Change).options(
            joinedload(Change.object)
        ).filter(
            Change.session_id == session_id
        ).order_by(
            Change.display_order
        ).all()
    
    def get_by_session_with_objects(
        self,
        session_id: int
    ) -> List[tuple]:
        """
        Get changes with object details.
        
        Joins with object_lookup to include object name and type.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of tuples (Change, ObjectLookup)
            
        Example:
            >>> changes = repo.get_by_session_with_objects(session_id=1)
            >>> for change, obj in changes:
            ...     print(f"{change.classification}: {obj.name}")
        """
        return self.db.session.query(
            Change,
            ObjectLookup
        ).join(
            ObjectLookup,
            Change.object_id == ObjectLookup.id
        ).filter(
            Change.session_id == session_id
        ).order_by(
            Change.display_order
        ).all()
    
    def get_by_classification(
        self,
        session_id: int,
        classification: str
    ) -> List[Change]:
        """
        Get changes filtered by classification.
        
        Args:
            session_id: Merge session ID
            classification: NO_CONFLICT, CONFLICT, NEW, or DELETED
            
        Returns:
            List of Change objects
            
        Example:
            >>> conflicts = repo.get_by_classification(
            ...     session_id=1,
            ...     classification="CONFLICT"
            ... )
        """
        return self.filter_by(
            session_id=session_id,
            classification=classification
        )
    
    def get_by_classifications(
        self,
        session_id: int,
        classifications: List[str]
    ) -> List[Change]:
        """
        Get changes filtered by multiple classifications with eager loading.
        
        Args:
            session_id: Merge session ID
            classifications: List of classifications to include
            
        Returns:
            List of Change objects ordered by display_order
            
        Example:
            >>> changes = repo.get_by_classifications(
            ...     session_id=1,
            ...     classifications=["CONFLICT", "DELETED"]
            ... )
        """
        return self.db.session.query(Change).options(
            joinedload(Change.object)
        ).filter(
            and_(
                Change.session_id == session_id,
                Change.classification.in_(classifications)
            )
        ).order_by(
            Change.display_order
        ).all()
    
    def count_by_classification(
        self,
        session_id: int
    ) -> Dict[str, int]:
        """
        Count changes by classification.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Dict mapping classification to count
            
        Example:
            >>> counts = repo.count_by_classification(session_id=1)
            >>> print(f"NO_CONFLICT: {counts.get('NO_CONFLICT', 0)}")
            >>> print(f"CONFLICT: {counts.get('CONFLICT', 0)}")
            >>> print(f"NEW: {counts.get('NEW', 0)}")
            >>> print(f"DELETED: {counts.get('DELETED', 0)}")
        """
        results = self.db.session.query(
            Change.classification,
            func.count(Change.id).label('count')
        ).filter(
            Change.session_id == session_id
        ).group_by(
            Change.classification
        ).all()
        
        return {classification: count for classification, count in results}
    
    def count_total(
        self,
        session_id: int
    ) -> int:
        """
        Count total changes for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Total count
            
        Example:
            >>> total = repo.count_total(session_id=1)
            >>> print(f"Total changes: {total}")
        """
        return self.count(session_id=session_id)
    
    def find_by_object(
        self,
        session_id: int,
        object_id: int
    ) -> Optional[Change]:
        """
        Find change for a specific object.
        
        Args:
            session_id: Merge session ID
            object_id: Object ID
            
        Returns:
            Change if found, None otherwise
            
        Example:
            >>> change = repo.find_by_object(session_id=1, object_id=42)
            >>> if change:
            ...     print(f"Classification: {change.classification}")
        """
        return self.find_one(session_id=session_id, object_id=object_id)
    
    def get_next_display_order(
        self,
        session_id: int
    ) -> int:
        """
        Get next available display order for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Next display order value
            
        Example:
            >>> next_order = repo.get_next_display_order(session_id=1)
        """
        max_order = self.db.session.query(
            func.max(Change.display_order)
        ).filter(
            Change.session_id == session_id
        ).scalar()
        
        return (max_order or 0) + 1
    
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
                - total: Total changes
                - by_classification: Count by classification
                - conflicts: Count of conflicts
                - no_conflicts: Count of no conflicts
                
        Example:
            >>> stats = repo.get_statistics(session_id=1)
            >>> print(f"Total: {stats['total']}")
            >>> print(f"Conflicts: {stats['conflicts']}")
        """
        total = self.count_total(session_id)
        by_classification = self.count_by_classification(session_id)
        
        conflicts = by_classification.get('CONFLICT', 0)
        no_conflicts = by_classification.get('NO_CONFLICT', 0)
        
        return {
            'total': total,
            'by_classification': by_classification,
            'conflicts': conflicts,
            'no_conflicts': no_conflicts,
            'new': by_classification.get('NEW', 0),
            'deleted': by_classification.get('DELETED', 0)
        }
    
    def get_by_object_type(
        self,
        session_id: int,
        object_type: str
    ) -> List[Change]:
        """
        Get changes filtered by object type with eager loading.
        
        Args:
            session_id: Merge session ID
            object_type: Object type to filter by
            
        Returns:
            List of Change objects
            
        Example:
            >>> interface_changes = repo.get_by_object_type(
            ...     session_id=1,
            ...     object_type="Interface"
            ... )
        """
        return self.db.session.query(Change).options(
            joinedload(Change.object)
        ).join(
            ObjectLookup,
            Change.object_id == ObjectLookup.id
        ).filter(
            and_(
                Change.session_id == session_id,
                ObjectLookup.object_type == object_type
            )
        ).order_by(
            Change.display_order
        ).all()
    
    def delete_by_session(
        self,
        session_id: int
    ) -> int:
        """
        Delete all changes for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Number of changes deleted
            
        Example:
            >>> deleted = repo.delete_by_session(session_id=1)
        """
        count = self.count_total(session_id)
        self.db.session.query(Change).filter(
            Change.session_id == session_id
        ).delete()
        self.db.session.flush()
        return count
