"""
Base repository class for data access layer.

This module provides a generic base repository with CRUD operations
that can be extended for specific models.
"""

from abc import ABC
from typing import Generic, TypeVar, List, Optional
from models import db


T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Base repository providing generic CRUD operations.
    
    This class provides common database operations that can be
    inherited by specific repository implementations. It uses
    SQLAlchemy for database access.
    
    Type Parameters:
        T: The SQLAlchemy model class type
    
    Example:
        >>> class UserRepository(BaseRepository[User]):
        ...     def __init__(self):
        ...         super().__init__(User)
        ...     
        ...     def get_by_email(self, email: str) -> Optional[User]:
        ...         return self.model_class.query.filter_by(email=email).first()
    """
    
    def __init__(self, model_class: type):
        """
        Initialize repository with model class.
        
        Args:
            model_class: SQLAlchemy model class for this repository
        """
        self.model_class = model_class
        self.db = db
    
    def create(self, **kwargs) -> T:
        """
        Create a new entity.
        
        Args:
            **kwargs: Attributes for the new entity
            
        Returns:
            T: The created entity instance
            
        Example:
            >>> user = user_repo.create(
            ...     name="John", email="john@example.com"
            ... )
        """
        entity = self.model_class(**kwargs)
        self.db.session.add(entity)
        self.db.session.commit()
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Primary key of the entity
            
        Returns:
            Optional[T]: The entity if found, None otherwise
            
        Example:
            >>> user = user_repo.get_by_id(1)
        """
        return self.model_class.query.get(entity_id)
    
    def get_all(self) -> List[T]:
        """
        Get all entities.
        
        Returns:
            List[T]: List of all entities
            
        Example:
            >>> users = user_repo.get_all()
        """
        return self.model_class.query.all()
    
    def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: The entity instance with updated attributes
            
        Returns:
            T: The updated entity
            
        Example:
            >>> user.name = "Jane"
            >>> user_repo.update(user)
        """
        self.db.session.commit()
        return entity
    
    def delete(self, entity: T) -> None:
        """
        Delete an entity.
        
        Args:
            entity: The entity instance to delete
            
        Example:
            >>> user_repo.delete(user)
        """
        self.db.session.delete(entity)
        self.db.session.commit()
    
    def filter_by(self, **kwargs) -> List[T]:
        """
        Filter entities by criteria.
        
        Args:
            **kwargs: Filter criteria as keyword arguments
            
        Returns:
            List[T]: List of entities matching the criteria
            
        Example:
            >>> active_users = user_repo.filter_by(active=True)
        """
        return self.model_class.query.filter_by(**kwargs).all()
    
    def find_one(self, **kwargs) -> Optional[T]:
        """
        Find a single entity by criteria.
        
        Args:
            **kwargs: Filter criteria as keyword arguments
            
        Returns:
            Optional[T]: The first entity matching criteria, or None
            
        Example:
            >>> user = user_repo.find_one(email="john@example.com")
        """
        return self.model_class.query.filter_by(**kwargs).first()
    
    def count(self, **kwargs) -> int:
        """
        Count entities matching criteria.
        
        Args:
            **kwargs: Optional filter criteria as keyword arguments
            
        Returns:
            int: Number of entities matching criteria
            
        Example:
            >>> total_users = user_repo.count()
            >>> active_users = user_repo.count(active=True)
        """
        if kwargs:
            return self.model_class.query.filter_by(**kwargs).count()
        return self.model_class.query.count()
    
    def exists(self, **kwargs) -> bool:
        """
        Check if any entity matches criteria.
        
        Args:
            **kwargs: Filter criteria as keyword arguments
            
        Returns:
            bool: True if at least one entity matches, False otherwise
            
        Example:
            >>> if user_repo.exists(email="john@example.com"):
            ...     print("Email already taken")
        """
        return self.model_class.query.filter_by(**kwargs).first() is not None
