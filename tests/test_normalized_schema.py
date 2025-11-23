"""
Tests for the normalized database schema.

This test file verifies that all new tables, indexes, and constraints
were created correctly for the merge assistant refactoring.
"""

import pytest
from app import create_app
from models import (
    db,
    Package,
    PackageObjectTypeCount,
    AppianObject,
    ProcessModelMetadata,
    ProcessModelNode,
    ProcessModelFlow,
    Change,
    MergeGuidance,
    MergeConflict,
    MergeChange,
    ObjectDependency,
    ChangeReview,
    MergeSession
)
from sqlalchemy import inspect


@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Enable foreign key constraints for SQLite
        db.session.execute(db.text("PRAGMA foreign_keys=ON"))
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


def test_all_tables_exist(app):
    """Test that all required tables exist"""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'packages',
            'package_object_type_counts',
            'appian_objects',
            'process_model_metadata',
            'process_model_nodes',
            'process_model_flows',
            'changes',
            'merge_guidance',
            'merge_conflicts',
            'merge_changes',
            'object_dependencies',
            'change_reviews',
            'merge_sessions'
        ]
        
        for table in required_tables:
            assert table in tables, f"Table '{table}' not found"


def test_package_model(app):
    """Test Package model creation and relationships"""
    with app.app_context():
        # Create a merge session
        session = MergeSession(
            reference_id='TEST_001',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        # Create a package
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package',
            total_objects=10
        )
        db.session.add(package)
        db.session.commit()
        
        # Verify package was created
        assert package.id is not None
        assert package.session_id == session.id
        assert package.package_type == 'base'
        assert package.package_name == 'Test Package'


def test_appian_object_model(app):
    """Test AppianObject model creation"""
    with app.app_context():
        # Create session and package
        session = MergeSession(
            reference_id='TEST_002',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        # Create an object
        obj = AppianObject(
            package_id=package.id,
            uuid='test-uuid-123',
            name='Test Interface',
            object_type='Interface',
            sail_code='a!textField()',
            version_uuid='version-uuid-123'
        )
        db.session.add(obj)
        db.session.commit()
        
        # Verify object was created
        assert obj.id is not None
        assert obj.package_id == package.id
        assert obj.uuid == 'test-uuid-123'
        assert obj.name == 'Test Interface'
        assert obj.object_type == 'Interface'


def test_change_model(app):
    """Test Change model creation"""
    with app.app_context():
        # Create session
        session = MergeSession(
            reference_id='TEST_003',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        # Create a change
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid-456',
            object_name='Test Object',
            object_type='Interface',
            classification='NO_CONFLICT',
            change_type='MODIFIED',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        # Verify change was created
        assert change.id is not None
        assert change.session_id == session.id
        assert change.object_uuid == 'test-uuid-456'
        assert change.classification == 'NO_CONFLICT'
        assert change.display_order == 1


def test_change_review_with_change_id(app):
    """Test ChangeReview model with change_id foreign key"""
    with app.app_context():
        # Create session
        session = MergeSession(
            reference_id='TEST_004',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        # Create a change
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid-789',
            object_name='Test Object',
            object_type='Interface',
            classification='CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        # Create a review linked to the change
        review = ChangeReview(
            session_id=session.id,
            change_id=change.id,
            review_status='reviewed',
            user_notes='Looks good'
        )
        db.session.add(review)
        db.session.commit()
        
        # Verify review was created
        assert review.id is not None
        assert review.change_id == change.id
        assert review.review_status == 'reviewed'


def test_process_model_tables(app):
    """Test ProcessModel normalization tables"""
    with app.app_context():
        # Create session, package, and object
        session = MergeSession(
            reference_id='TEST_005',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='pm-uuid-123',
            name='Test Process Model',
            object_type='Process Model'
        )
        db.session.add(obj)
        db.session.commit()
        
        # Create process model metadata
        pm_metadata = ProcessModelMetadata(
            appian_object_id=obj.id,
            total_nodes=3,
            total_flows=2
        )
        db.session.add(pm_metadata)
        db.session.commit()
        
        # Create nodes
        node1 = ProcessModelNode(
            process_model_id=pm_metadata.id,
            node_id='node-1',
            node_type='Start',
            node_name='Start Node'
        )
        node2 = ProcessModelNode(
            process_model_id=pm_metadata.id,
            node_id='node-2',
            node_type='End',
            node_name='End Node'
        )
        db.session.add_all([node1, node2])
        db.session.commit()
        
        # Create flow
        flow = ProcessModelFlow(
            process_model_id=pm_metadata.id,
            from_node_id=node1.id,
            to_node_id=node2.id,
            flow_label='Default'
        )
        db.session.add(flow)
        db.session.commit()
        
        # Verify all were created
        assert pm_metadata.id is not None
        assert node1.id is not None
        assert node2.id is not None
        assert flow.id is not None
        assert flow.from_node_id == node1.id
        assert flow.to_node_id == node2.id


def test_merge_guidance_tables(app):
    """Test MergeGuidance normalization tables"""
    with app.app_context():
        # Create session and change
        session = MergeSession(
            reference_id='TEST_006',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid-999',
            object_name='Test Object',
            object_type='Interface',
            classification='CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        # Create merge guidance
        guidance = MergeGuidance(
            change_id=change.id,
            recommendation='MANUAL_MERGE',
            reason='Conflicting changes detected'
        )
        db.session.add(guidance)
        db.session.commit()
        
        # Create conflict
        conflict = MergeConflict(
            guidance_id=guidance.id,
            field_name='sail_code',
            conflict_type='CONTENT_CONFLICT',
            description='Different SAIL code in both versions'
        )
        db.session.add(conflict)
        db.session.commit()
        
        # Create change detail
        change_detail = MergeChange(
            guidance_id=guidance.id,
            field_name='label',
            change_description='Label changed',
            old_value='Old Label',
            new_value='New Label'
        )
        db.session.add(change_detail)
        db.session.commit()
        
        # Verify all were created
        assert guidance.id is not None
        assert conflict.id is not None
        assert change_detail.id is not None


def test_object_dependency_model(app):
    """Test ObjectDependency model"""
    with app.app_context():
        # Create session and package
        session = MergeSession(
            reference_id='TEST_007',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        # Create dependency
        dependency = ObjectDependency(
            package_id=package.id,
            parent_uuid='parent-uuid-123',
            child_uuid='child-uuid-456',
            dependency_type='reference'
        )
        db.session.add(dependency)
        db.session.commit()
        
        # Verify dependency was created
        assert dependency.id is not None
        assert dependency.parent_uuid == 'parent-uuid-123'
        assert dependency.child_uuid == 'child-uuid-456'


def test_cascade_delete(app):
    """Test that cascade delete works correctly"""
    with app.app_context():
        # Create session with package and objects
        session = MergeSession(
            reference_id='TEST_008',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='cascade-test-uuid',
            name='Test Object',
            object_type='Interface'
        )
        db.session.add(obj)
        db.session.commit()
        
        package_id = package.id
        object_id = obj.id
        
        # Delete session
        db.session.delete(session)
        db.session.commit()
        
        # Verify package and object were also deleted
        assert Package.query.get(package_id) is None
        assert AppianObject.query.get(object_id) is None


def test_foreign_key_constraint_package_session(app):
    """Test that invalid session_id in Package is rejected"""
    with app.app_context():
        # Try to create package with non-existent session_id
        package = Package(
            session_id=99999,  # Non-existent session
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):  # SQLAlchemy raises IntegrityError
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_appian_object_package(app):
    """Test that invalid package_id in AppianObject is rejected"""
    with app.app_context():
        # Try to create object with non-existent package_id
        obj = AppianObject(
            package_id=99999,  # Non-existent package
            uuid='test-uuid',
            name='Test Object',
            object_type='Interface'
        )
        db.session.add(obj)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_change_session(app):
    """Test that invalid session_id in Change is rejected"""
    with app.app_context():
        # Try to create change with non-existent session_id
        change = Change(
            session_id=99999,  # Non-existent session
            object_uuid='test-uuid',
            object_name='Test Object',
            object_type='Interface',
            classification='NO_CONFLICT',
            display_order=1
        )
        db.session.add(change)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_change_object_references(app):
    """Test that invalid object_id references in Change are rejected"""
    with app.app_context():
        # Create session
        session = MergeSession(
            reference_id='TEST_FK_001',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        # Try to create change with non-existent base_object_id
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid',
            object_name='Test Object',
            object_type='Interface',
            classification='NO_CONFLICT',
            display_order=1,
            base_object_id=99999  # Non-existent object
        )
        db.session.add(change)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_change_review(app):
    """Test that invalid change_id in ChangeReview is rejected"""
    with app.app_context():
        # Create session
        session = MergeSession(
            reference_id='TEST_FK_002',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        # Try to create review with non-existent change_id
        review = ChangeReview(
            session_id=session.id,
            change_id=99999,  # Non-existent change
            review_status='pending'
        )
        db.session.add(review)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_process_model_metadata(app):
    """Test that invalid appian_object_id in ProcessModelMetadata is rejected"""
    with app.app_context():
        # Try to create process model metadata with non-existent object
        pm_metadata = ProcessModelMetadata(
            appian_object_id=99999,  # Non-existent object
            total_nodes=5,
            total_flows=4
        )
        db.session.add(pm_metadata)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_process_model_node(app):
    """Test that invalid process_model_id in ProcessModelNode is rejected"""
    with app.app_context():
        # Try to create node with non-existent process_model_id
        node = ProcessModelNode(
            process_model_id=99999,  # Non-existent process model
            node_id='node-1',
            node_type='Start'
        )
        db.session.add(node)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_process_model_flow(app):
    """Test that invalid node references in ProcessModelFlow are rejected"""
    with app.app_context():
        # Create session, package, object, and process model
        session = MergeSession(
            reference_id='TEST_FK_003',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='pm-uuid',
            name='Test PM',
            object_type='Process Model'
        )
        db.session.add(obj)
        db.session.commit()
        
        pm_metadata = ProcessModelMetadata(
            appian_object_id=obj.id,
            total_nodes=2,
            total_flows=1
        )
        db.session.add(pm_metadata)
        db.session.commit()
        
        # Try to create flow with non-existent from_node_id
        flow = ProcessModelFlow(
            process_model_id=pm_metadata.id,
            from_node_id=99999,  # Non-existent node
            to_node_id=99998,  # Non-existent node
            flow_label='Test'
        )
        db.session.add(flow)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_merge_guidance(app):
    """Test that invalid change_id in MergeGuidance is rejected"""
    with app.app_context():
        # Try to create guidance with non-existent change_id
        guidance = MergeGuidance(
            change_id=99999,  # Non-existent change
            recommendation='ACCEPT_VENDOR',
            reason='Test'
        )
        db.session.add(guidance)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_merge_conflict(app):
    """Test that invalid guidance_id in MergeConflict is rejected"""
    with app.app_context():
        # Try to create conflict with non-existent guidance_id
        conflict = MergeConflict(
            guidance_id=99999,  # Non-existent guidance
            field_name='test_field',
            conflict_type='CONTENT_CONFLICT'
        )
        db.session.add(conflict)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_foreign_key_constraint_object_dependency(app):
    """Test that invalid package_id in ObjectDependency is rejected"""
    with app.app_context():
        # Try to create dependency with non-existent package_id
        dependency = ObjectDependency(
            package_id=99999,  # Non-existent package
            parent_uuid='parent-uuid',
            child_uuid='child-uuid',
            dependency_type='reference'
        )
        db.session.add(dependency)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_cascade_delete_session_packages(app):
    """Test that deleting session cascades to packages"""
    with app.app_context():
        # Create session with packages
        session = MergeSession(
            reference_id='TEST_CASCADE_001',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package1 = Package(
            session_id=session.id,
            package_type='base',
            package_name='Package 1'
        )
        package2 = Package(
            session_id=session.id,
            package_type='customized',
            package_name='Package 2'
        )
        db.session.add_all([package1, package2])
        db.session.commit()
        
        package1_id = package1.id
        package2_id = package2.id
        
        # Delete session
        db.session.delete(session)
        db.session.commit()
        
        # Verify packages were deleted
        assert Package.query.get(package1_id) is None
        assert Package.query.get(package2_id) is None


def test_cascade_delete_package_objects(app):
    """Test that deleting package cascades to objects"""
    with app.app_context():
        # Create session and package with objects
        session = MergeSession(
            reference_id='TEST_CASCADE_002',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj1 = AppianObject(
            package_id=package.id,
            uuid='obj-1',
            name='Object 1',
            object_type='Interface'
        )
        obj2 = AppianObject(
            package_id=package.id,
            uuid='obj-2',
            name='Object 2',
            object_type='Rule'
        )
        db.session.add_all([obj1, obj2])
        db.session.commit()
        
        obj1_id = obj1.id
        obj2_id = obj2.id
        
        # Delete package
        db.session.delete(package)
        db.session.commit()
        
        # Verify objects were deleted
        assert AppianObject.query.get(obj1_id) is None
        assert AppianObject.query.get(obj2_id) is None


def test_cascade_delete_session_changes(app):
    """Test that deleting session cascades to changes"""
    with app.app_context():
        # Create session with changes
        session = MergeSession(
            reference_id='TEST_CASCADE_003',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change1 = Change(
            session_id=session.id,
            object_uuid='uuid-1',
            object_name='Change 1',
            object_type='Interface',
            classification='NO_CONFLICT',
            display_order=1
        )
        change2 = Change(
            session_id=session.id,
            object_uuid='uuid-2',
            object_name='Change 2',
            object_type='Rule',
            classification='CONFLICT',
            display_order=2
        )
        db.session.add_all([change1, change2])
        db.session.commit()
        
        change1_id = change1.id
        change2_id = change2.id
        
        # Delete session
        db.session.delete(session)
        db.session.commit()
        
        # Verify changes were deleted
        assert Change.query.get(change1_id) is None
        assert Change.query.get(change2_id) is None


def test_cascade_delete_change_review(app):
    """Test that deleting change cascades to review"""
    with app.app_context():
        # Create session, change, and review
        session = MergeSession(
            reference_id='TEST_CASCADE_004',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='uuid-1',
            object_name='Change 1',
            object_type='Interface',
            classification='NO_CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        review = ChangeReview(
            session_id=session.id,
            change_id=change.id,
            review_status='pending'
        )
        db.session.add(review)
        db.session.commit()
        
        review_id = review.id
        
        # Delete change
        db.session.delete(change)
        db.session.commit()
        
        # Verify review was deleted
        assert ChangeReview.query.get(review_id) is None


def test_cascade_delete_change_guidance(app):
    """Test that deleting change cascades to merge guidance"""
    with app.app_context():
        # Create session, change, and guidance
        session = MergeSession(
            reference_id='TEST_CASCADE_005',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='uuid-1',
            object_name='Change 1',
            object_type='Interface',
            classification='CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        guidance = MergeGuidance(
            change_id=change.id,
            recommendation='MANUAL_MERGE',
            reason='Conflicting changes'
        )
        db.session.add(guidance)
        db.session.commit()
        
        guidance_id = guidance.id
        
        # Delete change
        db.session.delete(change)
        db.session.commit()
        
        # Verify guidance was deleted
        assert MergeGuidance.query.get(guidance_id) is None


def test_cascade_delete_guidance_conflicts(app):
    """Test that deleting guidance cascades to conflicts"""
    with app.app_context():
        # Create session, change, guidance, and conflicts
        session = MergeSession(
            reference_id='TEST_CASCADE_006',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='uuid-1',
            object_name='Change 1',
            object_type='Interface',
            classification='CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        guidance = MergeGuidance(
            change_id=change.id,
            recommendation='MANUAL_MERGE',
            reason='Conflicting changes'
        )
        db.session.add(guidance)
        db.session.commit()
        
        conflict1 = MergeConflict(
            guidance_id=guidance.id,
            field_name='field1',
            conflict_type='CONTENT_CONFLICT'
        )
        conflict2 = MergeConflict(
            guidance_id=guidance.id,
            field_name='field2',
            conflict_type='STRUCTURE_CONFLICT'
        )
        db.session.add_all([conflict1, conflict2])
        db.session.commit()
        
        conflict1_id = conflict1.id
        conflict2_id = conflict2.id
        
        # Delete guidance
        db.session.delete(guidance)
        db.session.commit()
        
        # Verify conflicts were deleted
        assert MergeConflict.query.get(conflict1_id) is None
        assert MergeConflict.query.get(conflict2_id) is None


def test_cascade_delete_process_model_nodes(app):
    """Test that deleting process model cascades to nodes"""
    with app.app_context():
        # Create full hierarchy
        session = MergeSession(
            reference_id='TEST_CASCADE_007',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='pm-uuid',
            name='Test PM',
            object_type='Process Model'
        )
        db.session.add(obj)
        db.session.commit()
        
        pm_metadata = ProcessModelMetadata(
            appian_object_id=obj.id,
            total_nodes=2,
            total_flows=1
        )
        db.session.add(pm_metadata)
        db.session.commit()
        
        node1 = ProcessModelNode(
            process_model_id=pm_metadata.id,
            node_id='node-1',
            node_type='Start'
        )
        node2 = ProcessModelNode(
            process_model_id=pm_metadata.id,
            node_id='node-2',
            node_type='End'
        )
        db.session.add_all([node1, node2])
        db.session.commit()
        
        node1_id = node1.id
        node2_id = node2.id
        
        # Delete process model metadata
        db.session.delete(pm_metadata)
        db.session.commit()
        
        # Verify nodes were deleted
        assert ProcessModelNode.query.get(node1_id) is None
        assert ProcessModelNode.query.get(node2_id) is None


def test_unique_constraint_package_object_uuid(app):
    """Test that duplicate UUID within same package is rejected"""
    with app.app_context():
        # Create session and package
        session = MergeSession(
            reference_id='TEST_UNIQUE_001',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        # Create first object
        obj1 = AppianObject(
            package_id=package.id,
            uuid='duplicate-uuid',
            name='Object 1',
            object_type='Interface'
        )
        db.session.add(obj1)
        db.session.commit()
        
        # Try to create second object with same UUID in same package
        obj2 = AppianObject(
            package_id=package.id,
            uuid='duplicate-uuid',  # Duplicate UUID
            name='Object 2',
            object_type='Rule'
        )
        db.session.add(obj2)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_unique_constraint_allows_same_uuid_different_packages(app):
    """Test that same UUID in different packages is allowed"""
    with app.app_context():
        # Create session and two packages
        session = MergeSession(
            reference_id='TEST_UNIQUE_002',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package1 = Package(
            session_id=session.id,
            package_type='base',
            package_name='Package 1'
        )
        package2 = Package(
            session_id=session.id,
            package_type='customized',
            package_name='Package 2'
        )
        db.session.add_all([package1, package2])
        db.session.commit()
        
        # Create object in first package
        obj1 = AppianObject(
            package_id=package1.id,
            uuid='same-uuid',
            name='Object 1',
            object_type='Interface'
        )
        db.session.add(obj1)
        db.session.commit()
        
        # Create object with same UUID in second package - should succeed
        obj2 = AppianObject(
            package_id=package2.id,
            uuid='same-uuid',  # Same UUID but different package
            name='Object 2',
            object_type='Interface'
        )
        db.session.add(obj2)
        db.session.commit()
        
        # Verify both objects exist
        assert obj1.id is not None
        assert obj2.id is not None
        assert obj1.uuid == obj2.uuid
        assert obj1.package_id != obj2.package_id


def test_unique_constraint_package_object_type_count(app):
    """Test that duplicate object_type within same package is rejected"""
    with app.app_context():
        # Create session and package
        session = MergeSession(
            reference_id='TEST_UNIQUE_003',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        # Create first count record
        count1 = PackageObjectTypeCount(
            package_id=package.id,
            object_type='Interface',
            count=10
        )
        db.session.add(count1)
        db.session.commit()
        
        # Try to create second count record with same object_type
        count2 = PackageObjectTypeCount(
            package_id=package.id,
            object_type='Interface',  # Duplicate object_type
            count=20
        )
        db.session.add(count2)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_unique_constraint_process_model_node(app):
    """Test that duplicate node_id within same process model is rejected"""
    with app.app_context():
        # Create full hierarchy
        session = MergeSession(
            reference_id='TEST_UNIQUE_004',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='pm-uuid',
            name='Test PM',
            object_type='Process Model'
        )
        db.session.add(obj)
        db.session.commit()
        
        pm_metadata = ProcessModelMetadata(
            appian_object_id=obj.id,
            total_nodes=2,
            total_flows=1
        )
        db.session.add(pm_metadata)
        db.session.commit()
        
        # Create first node
        node1 = ProcessModelNode(
            process_model_id=pm_metadata.id,
            node_id='duplicate-node',
            node_type='Start'
        )
        db.session.add(node1)
        db.session.commit()
        
        # Try to create second node with same node_id
        node2 = ProcessModelNode(
            process_model_id=pm_metadata.id,
            node_id='duplicate-node',  # Duplicate node_id
            node_type='End'
        )
        db.session.add(node2)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_unique_constraint_object_dependency(app):
    """Test that duplicate dependency within same package is rejected"""
    with app.app_context():
        # Create session and package
        session = MergeSession(
            reference_id='TEST_UNIQUE_005',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        # Create first dependency
        dep1 = ObjectDependency(
            package_id=package.id,
            parent_uuid='parent-uuid',
            child_uuid='child-uuid',
            dependency_type='reference'
        )
        db.session.add(dep1)
        db.session.commit()
        
        # Try to create duplicate dependency
        dep2 = ObjectDependency(
            package_id=package.id,
            parent_uuid='parent-uuid',  # Same parent
            child_uuid='child-uuid',  # Same child
            dependency_type='contains'  # Different type but still duplicate
        )
        db.session.add(dep2)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_unique_constraint_change_review_change_id(app):
    """Test that duplicate change_id in ChangeReview is rejected"""
    with app.app_context():
        # Create session and change
        session = MergeSession(
            reference_id='TEST_UNIQUE_006',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid',
            object_name='Test Object',
            object_type='Interface',
            classification='NO_CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        # Create first review
        review1 = ChangeReview(
            session_id=session.id,
            change_id=change.id,
            review_status='pending'
        )
        db.session.add(review1)
        db.session.commit()
        
        # Try to create second review for same change
        review2 = ChangeReview(
            session_id=session.id,
            change_id=change.id,  # Duplicate change_id
            review_status='reviewed'
        )
        db.session.add(review2)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_unique_constraint_merge_guidance_change_id(app):
    """Test that duplicate change_id in MergeGuidance is rejected"""
    with app.app_context():
        # Create session and change
        session = MergeSession(
            reference_id='TEST_UNIQUE_007',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid',
            object_name='Test Object',
            object_type='Interface',
            classification='CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        # Create first guidance
        guidance1 = MergeGuidance(
            change_id=change.id,
            recommendation='MANUAL_MERGE',
            reason='Conflicting changes'
        )
        db.session.add(guidance1)
        db.session.commit()
        
        # Try to create second guidance for same change
        guidance2 = MergeGuidance(
            change_id=change.id,  # Duplicate change_id
            recommendation='ACCEPT_VENDOR',
            reason='Different reason'
        )
        db.session.add(guidance2)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_unique_constraint_process_model_metadata_object_id(app):
    """Test that duplicate appian_object_id in ProcessModelMetadata is rejected"""
    with app.app_context():
        # Create session, package, and object
        session = MergeSession(
            reference_id='TEST_UNIQUE_008',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='pm-uuid',
            name='Test PM',
            object_type='Process Model'
        )
        db.session.add(obj)
        db.session.commit()
        
        # Create first metadata
        pm_metadata1 = ProcessModelMetadata(
            appian_object_id=obj.id,
            total_nodes=5,
            total_flows=4
        )
        db.session.add(pm_metadata1)
        db.session.commit()
        
        # Try to create second metadata for same object
        pm_metadata2 = ProcessModelMetadata(
            appian_object_id=obj.id,  # Duplicate appian_object_id
            total_nodes=10,
            total_flows=8
        )
        db.session.add(pm_metadata2)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_unique_constraint_merge_session_reference_id(app):
    """Test that duplicate reference_id in MergeSession is rejected"""
    with app.app_context():
        # Create first session
        session1 = MergeSession(
            reference_id='DUPLICATE_REF',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session1)
        db.session.commit()
        
        # Try to create second session with same reference_id
        session2 = MergeSession(
            reference_id='DUPLICATE_REF',  # Duplicate reference_id
            base_package_name='Base2',
            customized_package_name='Custom2',
            new_vendor_package_name='Vendor2'
        )
        db.session.add(session2)
        
        # Should raise IntegrityError
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()


def test_referential_integrity_no_orphaned_packages(app):
    """Test that packages cannot exist without a session"""
    with app.app_context():
        # Create session and package
        session = MergeSession(
            reference_id='TEST_REF_001',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        # Verify package exists
        assert package.id is not None
        
        # Delete session (should cascade to package)
        db.session.delete(session)
        db.session.commit()
        
        # Verify package was deleted (no orphan)
        assert db.session.get(Package, package.id) is None


def test_referential_integrity_no_orphaned_objects(app):
    """Test that objects cannot exist without a package"""
    with app.app_context():
        # Create session, package, and object
        session = MergeSession(
            reference_id='TEST_REF_002',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='test-uuid',
            name='Test Object',
            object_type='Interface'
        )
        db.session.add(obj)
        db.session.commit()
        
        obj_id = obj.id
        
        # Delete package (should cascade to object)
        db.session.delete(package)
        db.session.commit()
        
        # Verify object was deleted (no orphan)
        assert db.session.get(AppianObject, obj_id) is None


def test_referential_integrity_no_orphaned_changes(app):
    """Test that changes cannot exist without a session"""
    with app.app_context():
        # Create session and change
        session = MergeSession(
            reference_id='TEST_REF_003',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid',
            object_name='Test Object',
            object_type='Interface',
            classification='NO_CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        change_id = change.id
        
        # Delete session (should cascade to change)
        db.session.delete(session)
        db.session.commit()
        
        # Verify change was deleted (no orphan)
        assert db.session.get(Change, change_id) is None


def test_referential_integrity_no_orphaned_reviews(app):
    """Test that reviews cannot exist without a change"""
    with app.app_context():
        # Create session, change, and review
        session = MergeSession(
            reference_id='TEST_REF_004',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid',
            object_name='Test Object',
            object_type='Interface',
            classification='NO_CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        review = ChangeReview(
            session_id=session.id,
            change_id=change.id,
            review_status='pending'
        )
        db.session.add(review)
        db.session.commit()
        
        review_id = review.id
        
        # Delete change (should cascade to review)
        db.session.delete(change)
        db.session.commit()
        
        # Verify review was deleted (no orphan)
        assert db.session.get(ChangeReview, review_id) is None


def test_referential_integrity_update_maintains_relationships(app):
    """Test that updating records maintains referential integrity"""
    with app.app_context():
        # Create session and package
        session = MergeSession(
            reference_id='TEST_REF_005',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Original Name'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='test-uuid',
            name='Test Object',
            object_type='Interface'
        )
        db.session.add(obj)
        db.session.commit()
        
        # Update package name
        package.package_name = 'Updated Name'
        db.session.commit()
        
        # Verify object still references correct package
        db.session.refresh(obj)
        assert obj.package_id == package.id
        assert obj.package.package_name == 'Updated Name'


def test_referential_integrity_change_object_references(app):
    """Test that change maintains valid object references"""
    with app.app_context():
        # Create session and packages
        session = MergeSession(
            reference_id='TEST_REF_006',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        base_package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Base Package'
        )
        customer_package = Package(
            session_id=session.id,
            package_type='customized',
            package_name='Customer Package'
        )
        db.session.add_all([base_package, customer_package])
        db.session.commit()
        
        base_obj = AppianObject(
            package_id=base_package.id,
            uuid='obj-uuid',
            name='Base Object',
            object_type='Interface'
        )
        customer_obj = AppianObject(
            package_id=customer_package.id,
            uuid='obj-uuid',
            name='Customer Object',
            object_type='Interface'
        )
        db.session.add_all([base_obj, customer_obj])
        db.session.commit()
        
        # Create change with object references
        change = Change(
            session_id=session.id,
            object_uuid='obj-uuid',
            object_name='Test Object',
            object_type='Interface',
            classification='MODIFIED',
            display_order=1,
            base_object_id=base_obj.id,
            customer_object_id=customer_obj.id
        )
        db.session.add(change)
        db.session.commit()
        
        # Verify change has valid references
        db.session.refresh(change)
        assert change.base_object is not None
        assert change.customer_object is not None
        assert change.base_object.id == base_obj.id
        assert change.customer_object.id == customer_obj.id


def test_referential_integrity_process_model_hierarchy(app):
    """Test that process model hierarchy maintains referential integrity"""
    with app.app_context():
        # Create full hierarchy
        session = MergeSession(
            reference_id='TEST_REF_007',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        obj = AppianObject(
            package_id=package.id,
            uuid='pm-uuid',
            name='Test PM',
            object_type='Process Model'
        )
        db.session.add(obj)
        db.session.commit()
        
        pm_metadata = ProcessModelMetadata(
            appian_object_id=obj.id,
            total_nodes=2,
            total_flows=1
        )
        db.session.add(pm_metadata)
        db.session.commit()
        
        node1 = ProcessModelNode(
            process_model_id=pm_metadata.id,
            node_id='node-1',
            node_type='Start'
        )
        node2 = ProcessModelNode(
            process_model_id=pm_metadata.id,
            node_id='node-2',
            node_type='End'
        )
        db.session.add_all([node1, node2])
        db.session.commit()
        
        flow = ProcessModelFlow(
            process_model_id=pm_metadata.id,
            from_node_id=node1.id,
            to_node_id=node2.id,
            flow_label='Default'
        )
        db.session.add(flow)
        db.session.commit()
        
        # Verify all relationships are intact
        db.session.refresh(pm_metadata)
        assert pm_metadata.appian_object.id == obj.id
        assert len(pm_metadata.nodes) == 2
        assert len(pm_metadata.flows) == 1
        
        db.session.refresh(flow)
        assert flow.from_node.id == node1.id
        assert flow.to_node.id == node2.id


def test_referential_integrity_merge_guidance_hierarchy(app):
    """Test that merge guidance hierarchy maintains referential integrity"""
    with app.app_context():
        # Create session, change, and guidance hierarchy
        session = MergeSession(
            reference_id='TEST_REF_008',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        change = Change(
            session_id=session.id,
            object_uuid='test-uuid',
            object_name='Test Object',
            object_type='Interface',
            classification='CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        guidance = MergeGuidance(
            change_id=change.id,
            recommendation='MANUAL_MERGE',
            reason='Conflicting changes'
        )
        db.session.add(guidance)
        db.session.commit()
        
        conflict = MergeConflict(
            guidance_id=guidance.id,
            field_name='sail_code',
            conflict_type='CONTENT_CONFLICT'
        )
        merge_change = MergeChange(
            guidance_id=guidance.id,
            field_name='label',
            change_description='Label changed'
        )
        db.session.add_all([conflict, merge_change])
        db.session.commit()
        
        # Verify all relationships are intact
        db.session.refresh(guidance)
        assert guidance.change.id == change.id
        assert len(guidance.conflicts) == 1
        assert len(guidance.changes) == 1
        
        db.session.refresh(conflict)
        assert conflict.guidance.id == guidance.id


def test_referential_integrity_dependency_relationships(app):
    """Test that dependencies maintain referential integrity"""
    with app.app_context():
        # Create session and package
        session = MergeSession(
            reference_id='TEST_REF_009',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='Test Package'
        )
        db.session.add(package)
        db.session.commit()
        
        parent_obj = AppianObject(
            package_id=package.id,
            uuid='parent-uuid',
            name='Parent Object',
            object_type='Interface'
        )
        child_obj = AppianObject(
            package_id=package.id,
            uuid='child-uuid',
            name='Child Object',
            object_type='Rule'
        )
        db.session.add_all([parent_obj, child_obj])
        db.session.commit()
        
        # Create dependency
        dependency = ObjectDependency(
            package_id=package.id,
            parent_uuid='parent-uuid',
            child_uuid='child-uuid',
            dependency_type='reference'
        )
        db.session.add(dependency)
        db.session.commit()
        
        # Verify dependency references are intact
        db.session.refresh(dependency)
        assert dependency.package.id == package.id
        
        # Delete package (should cascade to dependency)
        package_id = package.id
        db.session.delete(package)
        db.session.commit()
        
        # Verify dependency was deleted (no orphan)
        remaining_deps = ObjectDependency.query.filter_by(package_id=package_id).all()
        assert len(remaining_deps) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
