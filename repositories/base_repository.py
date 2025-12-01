"""
Base Repository Interface

Provides generic CRUD operations following the Repository pattern.
All repositories should inherit from this base class.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any
from models import db

T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Base repository interface following Repository pattern.
    
    Provides CRUD operations for domain entities.
    """
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[T]:
        """Find entity by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[T]:
        """Find all entities"""
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """Save entity"""
        pass
    
    @abstractmethod
    def delete(self, entity: T) -> None:
        """Delete entity"""
        pass


class BaseRepository(IRepository[T], Generic[T]):
    """
    Base repository implementation with common database operations.
    
    Provides concrete implementations of CRUD operations using SQLAlchemy.
    """
    
    def __init__(self, model_class: type):
        """
        Initialize repository with model class.
        
        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
        self.db = db
    
    def find_by_id(self, id: int) -> Optional[T]:
        """
        Find entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Entity or None if not found
        """
        return self.db.session.query(self.model_class).get(id)
    
    def find_all(self) -> List[T]:
        """
        Find all entities.
        
        Returns:
            List of all entities
        """
        return self.db.session.query(self.model_class).all()
    
    def save(self, entity: T) -> T:
        """
        Save entity (insert or update).
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity
        """
        self.db.session.add(entity)
        self.db.session.flush()
        return entity
    
    def delete(self, entity: T) -> None:
        """
        Delete entity.
        
        Args:
            entity: Entity to delete
        """
        self.db.session.delete(entity)
        self.db.session.flush()
    
    def find_one(self, **filters) -> Optional[T]:
        """
        Find one entity by filters.
        
        Args:
            **filters: Filter criteria
            
        Returns:
            Entity or None if not found
        """
        return self.db.session.query(self.model_class).filter_by(**filters).first()
    
    def filter_by(self, **filters) -> List[T]:
        """
        Find entities by filters.
        
        Args:
            **filters: Filter criteria
            
        Returns:
            List of matching entities
        """
        return self.db.session.query(self.model_class).filter_by(**filters).all()
    
    def count(self, **filters) -> int:
        """
        Count entities by filters.
        
        Args:
            **filters: Filter criteria
            
        Returns:
            Count of matching entities
        """
        return self.db.session.query(self.model_class).filter_by(**filters).count()
    
    def commit(self) -> None:
        """Commit current transaction"""
        self.db.session.commit()
    
    def rollback(self) -> None:
        """Rollback current transaction"""
        self.db.session.rollback()
