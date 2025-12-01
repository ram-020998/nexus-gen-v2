"""
Test Repository Layer

Tests for base and core repositories.
"""

import pytest
from models import (
    db, ObjectLookup, PackageObjectMapping, DeltaComparisonResult,
    Change, MergeSession, Package
)
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.package_object_mapping_repository import (
    PackageObjectMappingRepository
)
from repositories.delta_comparison_repository import (
    DeltaComparisonRepository
)
from repositories.change_repository import ChangeRepository


class TestObjectLookupRepository:
    """Test ObjectLookupRepository"""
    
    def test_find_or_create_new_object(self, app):
        """Test creating a new object"""
        with app.app_context():
            repo = ObjectLookupRepository()
            
            obj = repo.find_or_create(
                uuid="test-uuid-1",
                name="Test Object",
                object_type="Interface",
                description="Test description"
            )
            
            assert obj.id is not None
            assert obj.uuid == "test-uuid-1"
            assert obj.name == "Test Object"
            assert obj.object_type == "Interface"
            
            db.session.rollback()
    
    def test_find_or_create_existing_object(self, app):
        """Test finding existing object (no duplicate)"""
        with app.app_context():
            repo = ObjectLookupRepository()
            
            # Create first time
            obj1 = repo.find_or_create(
                uuid="test-uuid-2",
                name="Test Object",
                object_type="Interface"
            )
            db.session.commit()
            
            # Try to create again with same UUID
            obj2 = repo.find_or_create(
                uuid="test-uuid-2",
                name="Test Object Updated",
                object_type="Interface"
            )
            
            # Should return same object
            assert obj1.id == obj2.id
            assert obj2.name == "Test Object Updated"  # Name updated
            
            db.session.rollback()
    
    def test_find_by_uuid(self, app):
        """Test finding object by UUID"""
        with app.app_context():
            repo = ObjectLookupRepository()
            
            # Create object
            obj = repo.find_or_create(
                uuid="test-uuid-3",
                name="Test Object",
                object_type="Process Model"
            )
            db.session.commit()
            
            # Find by UUID
            found = repo.find_by_uuid("test-uuid-3")
            assert found is not None
            assert found.id == obj.id
            
            db.session.rollback()
    
    def test_get_duplicate_uuids(self, app):
        """Test duplicate detection (should be empty)"""
        with app.app_context():
            repo = ObjectLookupRepository()
            
            # Create objects using find_or_create
            repo.find_or_create(
                uuid="test-uuid-4",
                name="Object 1",
                object_type="Interface"
            )
            repo.find_or_create(
                uuid="test-uuid-4",
                name="Object 1",
                object_type="Interface"
            )
            db.session.commit()
            
            # Check for duplicates
            duplicates = repo.get_duplicate_uuids()
            assert len(duplicates) == 0  # No duplicates!
            
            db.session.rollback()


class TestPackageObjectMappingRepository:
    """Test PackageObjectMappingRepository"""
    
    def test_create_mapping(self, app):
        """Test creating a package-object mapping"""
        with app.app_context():
            # Create session and package
            session = MergeSession(reference_id="TEST-001", status="processing")
            db.session.add(session)
            db.session.flush()
            
            package = Package(
                session_id=session.id,
                package_type="base",
                filename="test.zip"
            )
            db.session.add(package)
            db.session.flush()
            
            # Create object
            obj_repo = ObjectLookupRepository()
            obj = obj_repo.find_or_create(
                uuid="test-uuid-5",
                name="Test Object",
                object_type="Interface"
            )
            
            # Create mapping
            mapping_repo = PackageObjectMappingRepository()
            mapping = mapping_repo.create_mapping(
                package_id=package.id,
                object_id=obj.id
            )
            
            assert mapping.id is not None
            assert mapping.package_id == package.id
            assert mapping.object_id == obj.id
            
            db.session.rollback()
    
    def test_get_objects_in_package(self, app):
        """Test getting all objects in a package"""
        with app.app_context():
            # Create session and package
            session = MergeSession(reference_id="TEST-002", status="processing")
            db.session.add(session)
            db.session.flush()
            
            package = Package(
                session_id=session.id,
                package_type="base",
                filename="test.zip"
            )
            db.session.add(package)
            db.session.flush()
            
            # Create objects
            obj_repo = ObjectLookupRepository()
            obj1 = obj_repo.find_or_create(
                uuid="test-uuid-6",
                name="Object 1",
                object_type="Interface"
            )
            obj2 = obj_repo.find_or_create(
                uuid="test-uuid-7",
                name="Object 2",
                object_type="Process Model"
            )
            
            # Create mappings
            mapping_repo = PackageObjectMappingRepository()
            mapping_repo.create_mapping(package.id, obj1.id)
            mapping_repo.create_mapping(package.id, obj2.id)
            db.session.commit()
            
            # Get objects in package
            objects = mapping_repo.get_objects_in_package(package.id)
            assert len(objects) == 2
            
            db.session.rollback()


class TestDeltaComparisonRepository:
    """Test DeltaComparisonRepository"""
    
    def test_create_result(self, app):
        """Test creating a delta comparison result"""
        with app.app_context():
            # Create session
            session = MergeSession(reference_id="TEST-003", status="processing")
            db.session.add(session)
            db.session.flush()
            
            # Create object
            obj_repo = ObjectLookupRepository()
            obj = obj_repo.find_or_create(
                uuid="test-uuid-8",
                name="Test Object",
                object_type="Interface"
            )
            
            # Create delta result
            delta_repo = DeltaComparisonRepository()
            result = delta_repo.create_result(
                session_id=session.id,
                object_id=obj.id,
                change_category="MODIFIED",
                change_type="MODIFIED",
                version_changed=True,
                content_changed=False
            )
            
            assert result.id is not None
            assert result.change_category == "MODIFIED"
            assert result.version_changed is True
            
            db.session.rollback()
    
    def test_count_by_category(self, app):
        """Test counting delta results by category"""
        with app.app_context():
            # Create session
            session = MergeSession(reference_id="TEST-004", status="processing")
            db.session.add(session)
            db.session.flush()
            
            # Create objects
            obj_repo = ObjectLookupRepository()
            obj1 = obj_repo.find_or_create(
                uuid="test-uuid-9",
                name="Object 1",
                object_type="Interface"
            )
            obj2 = obj_repo.find_or_create(
                uuid="test-uuid-10",
                name="Object 2",
                object_type="Interface"
            )
            obj3 = obj_repo.find_or_create(
                uuid="test-uuid-11",
                name="Object 3",
                object_type="Interface"
            )
            
            # Create delta results
            delta_repo = DeltaComparisonRepository()
            delta_repo.create_result(
                session.id, obj1.id, "NEW", "ADDED"
            )
            delta_repo.create_result(
                session.id, obj2.id, "MODIFIED", "MODIFIED"
            )
            delta_repo.create_result(
                session.id, obj3.id, "DEPRECATED", "REMOVED"
            )
            db.session.commit()
            
            # Count by category
            counts = delta_repo.count_by_category(session.id)
            assert counts.get("NEW") == 1
            assert counts.get("MODIFIED") == 1
            assert counts.get("DEPRECATED") == 1
            
            db.session.rollback()


class TestChangeRepository:
    """Test ChangeRepository"""
    
    def test_create_change(self, app):
        """Test creating a change"""
        with app.app_context():
            # Create session
            session = MergeSession(reference_id="TEST-005", status="processing")
            db.session.add(session)
            db.session.flush()
            
            # Create object
            obj_repo = ObjectLookupRepository()
            obj = obj_repo.find_or_create(
                uuid="test-uuid-12",
                name="Test Object",
                object_type="Interface"
            )
            
            # Create change
            change_repo = ChangeRepository()
            change = change_repo.create_change(
                session_id=session.id,
                object_id=obj.id,
                classification="CONFLICT",
                display_order=1,
                vendor_change_type="MODIFIED",
                customer_change_type="MODIFIED"
            )
            
            assert change.id is not None
            assert change.classification == "CONFLICT"
            assert change.display_order == 1
            
            db.session.rollback()
    
    def test_get_ordered_changes(self, app):
        """Test getting changes in display order"""
        with app.app_context():
            # Create session
            session = MergeSession(reference_id="TEST-006", status="processing")
            db.session.add(session)
            db.session.flush()
            
            # Create objects
            obj_repo = ObjectLookupRepository()
            obj1 = obj_repo.find_or_create(
                uuid="test-uuid-13",
                name="Object 1",
                object_type="Interface"
            )
            obj2 = obj_repo.find_or_create(
                uuid="test-uuid-14",
                name="Object 2",
                object_type="Interface"
            )
            
            # Create changes in reverse order
            change_repo = ChangeRepository()
            change_repo.create_change(
                session.id, obj2.id, "NEW", 2
            )
            change_repo.create_change(
                session.id, obj1.id, "CONFLICT", 1
            )
            db.session.commit()
            
            # Get ordered changes
            changes = change_repo.get_ordered_changes(session.id)
            assert len(changes) == 2
            assert changes[0].display_order == 1
            assert changes[1].display_order == 2
            
            db.session.rollback()
    
    def test_count_by_classification(self, app):
        """Test counting changes by classification"""
        with app.app_context():
            # Create session
            session = MergeSession(reference_id="TEST-007", status="processing")
            db.session.add(session)
            db.session.flush()
            
            # Create objects
            obj_repo = ObjectLookupRepository()
            obj1 = obj_repo.find_or_create(
                uuid="test-uuid-15",
                name="Object 1",
                object_type="Interface"
            )
            obj2 = obj_repo.find_or_create(
                uuid="test-uuid-16",
                name="Object 2",
                object_type="Interface"
            )
            obj3 = obj_repo.find_or_create(
                uuid="test-uuid-17",
                name="Object 3",
                object_type="Interface"
            )
            
            # Create changes
            change_repo = ChangeRepository()
            change_repo.create_change(
                session.id, obj1.id, "CONFLICT", 1
            )
            change_repo.create_change(
                session.id, obj2.id, "CONFLICT", 2
            )
            change_repo.create_change(
                session.id, obj3.id, "NO_CONFLICT", 3
            )
            db.session.commit()
            
            # Count by classification
            counts = change_repo.count_by_classification(session.id)
            assert counts.get("CONFLICT") == 2
            assert counts.get("NO_CONFLICT") == 1
            
            db.session.rollback()
