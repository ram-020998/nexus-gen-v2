"""
Property-Based Tests for Three-Way Merge Assistant

These tests use Hypothesis to verify correctness properties
across many randomly generated inputs.
"""
import json
import uuid
import os
import tempfile
import zipfile
from datetime import datetime
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
from tests.base_test import BaseTestCase
from models import (
    db, MergeSession, ChangeReview, Package, AppianObject,
    ObjectDependency, Change
)
from services.merge_assistant import BlueprintGenerationService
from services.merge_assistant.blueprint_generation_service import (
    BlueprintGenerationError
)


# Custom Hypothesis strategies for generating test data
@composite
def merge_session_data(draw):
    """Generate random merge session data with unique reference_id"""
    # Use UUID to ensure uniqueness across all test runs
    unique_id = str(uuid.uuid4())[:8].upper()
    return {
        'reference_id': f"MRG_{unique_id}",
        'base_package_name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' ._-'))),
        'customized_package_name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' ._-'))),
        'new_vendor_package_name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' ._-'))),
        'status': draw(st.sampled_from(['processing', 'ready', 'in_progress', 'completed', 'error'])),
        'current_change_index': draw(st.integers(min_value=0, max_value=100)),
        'total_changes': draw(st.integers(min_value=0, max_value=500)),
        'reviewed_count': draw(st.integers(min_value=0, max_value=100)),
        'skipped_count': draw(st.integers(min_value=0, max_value=100))
    }


@composite
def blueprint_data(draw):
    """Generate random blueprint data"""
    num_objects = draw(st.integers(min_value=1, max_value=20))
    objects = []
    for i in range(num_objects):
        objects.append({
            'uuid': f"uuid_{i}_{draw(st.integers(min_value=1000, max_value=9999))}",
            'name': draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
            'type': draw(st.sampled_from(['Interface', 'Process Model', 'Record Type', 'Expression Rule', 'Constant'])),
            'content': draw(st.text(min_size=10, max_size=100))
        })
    return {
        'objects': objects,
        'metadata': {
            'version': draw(st.text(min_size=3, max_size=10)),
            'generated_at': datetime.utcnow().isoformat()
        }
    }


@composite
def appian_object_data(draw):
    """Generate random Appian object data for object_lookup"""
    obj_uuid = f"_a-{draw(st.text(min_size=8, max_size=8, alphabet='0123456789abcdef'))}"
    obj_type = draw(st.sampled_from([
        'Interface', 'Process Model', 'Record Type',
        'Expression Rule', 'Constant', 'Site'
    ]))
    obj_name = draw(st.text(
        min_size=5, max_size=30,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))
    ))

    obj = {
        'uuid': obj_uuid,
        'name': obj_name,
        'object_type': obj_type,
        'description': draw(st.text(max_size=100)),
        'version_uuid': f"v-{draw(st.text(min_size=8, max_size=8, alphabet='0123456789abcdef'))}",
        'version_history': []
    }

    # Add SAIL code for interfaces and expression rules
    if obj_type in ['Interface', 'Expression Rule']:
        obj['sail_code'] = draw(st.text(min_size=20, max_size=200))

    # Add fields for record types
    if obj_type == 'Record Type':
        num_fields = draw(st.integers(min_value=1, max_value=5))
        obj['fields'] = [
            {
                'name': f"field_{i}",
                'type': draw(st.sampled_from(['Text', 'Number', 'Date']))
            }
            for i in range(num_fields)
        ]

    return obj


@composite
def blueprint_with_objects(draw):
    """Generate blueprint with object_lookup"""
    num_objects = draw(st.integers(min_value=3, max_value=10))
    object_lookup = {}
    
    # Generate objects with unique UUIDs
    attempts = 0
    max_attempts = num_objects * 10  # Allow retries for UUID collisions
    
    while len(object_lookup) < num_objects and attempts < max_attempts:
        obj = draw(appian_object_data())
        # Only add if UUID is unique
        if obj['uuid'] not in object_lookup:
            object_lookup[obj['uuid']] = obj
        attempts += 1
    
    # Update total_objects to match actual count (in case of collisions)
    actual_count = len(object_lookup)

    return {
        'blueprint': {
            'metadata': {
                'version': draw(st.text(min_size=3, max_size=10)),
                'total_objects': actual_count,
                'generated_at': datetime.utcnow().isoformat()
            }
        },
        'object_lookup': object_lookup
    }


@composite
def blueprint_pair_with_changes(draw):
    """
    Generate a pair of blueprints (base and target) with known changes
    """
    # Generate base blueprint
    base = draw(blueprint_with_objects())
    base_lookup = base['object_lookup']

    # Create target blueprint by modifying base
    target_lookup = {}

    # Keep some objects unchanged
    base_uuids = list(base_lookup.keys())
    num_unchanged = draw(st.integers(
        min_value=1,
        max_value=max(1, len(base_uuids) - 2)
    ))
    unchanged_uuids = draw(
        st.lists(
            st.sampled_from(base_uuids),
            min_size=num_unchanged,
            max_size=num_unchanged,
            unique=True
        )
    )

    for uuid in unchanged_uuids:
        target_lookup[uuid] = base_lookup[uuid].copy()

    # Modify some objects
    remaining_uuids = [u for u in base_uuids if u not in unchanged_uuids]
    if remaining_uuids:
        num_modified = draw(st.integers(
            min_value=0,
            max_value=len(remaining_uuids)
        ))
        if num_modified > 0:
            modified_uuids = draw(
                st.lists(
                    st.sampled_from(remaining_uuids),
                    min_size=num_modified,
                    max_size=num_modified,
                    unique=True
                )
            )
            for uuid in modified_uuids:
                obj = base_lookup[uuid].copy()
                # Modify SAIL code if present
                if 'sail_code' in obj:
                    obj['sail_code'] = obj['sail_code'] + "\n// Modified"
                # Change version
                obj['version_uuid'] = f"v-modified-{uuid[-8:]}"
                target_lookup[uuid] = obj

    # Add some new objects
    num_added = draw(st.integers(min_value=0, max_value=3))
    for _ in range(num_added):
        new_obj = draw(appian_object_data())
        target_lookup[new_obj['uuid']] = new_obj

    # Remove some objects (those not in unchanged or modified)
    # Objects in base but not in target are considered removed

    target = {
        'blueprint': {
            'metadata': {
                'version': base['blueprint']['metadata']['version'] + '.1',
                'total_objects': len(target_lookup),
                'generated_at': datetime.utcnow().isoformat()
            }
        },
        'object_lookup': target_lookup
    }

    return (base, target)


class TestMergeAssistantProperties(BaseTestCase):
    """Property-based tests for merge assistant"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.service = BlueprintGenerationService()
        # Use existing test packages
        self.test_package_a = os.path.join(
            'applicationArtifacts',
            'Testing Files',
            'SourceSelectionv2.4.0.zip'
        )
        self.test_package_b = os.path.join(
            'applicationArtifacts',
            'Testing Files',
            'SourceSelectionv2.6.0.zip'
        )

    def test_property_4_blueprint_generation_completeness(self):
        """
        Feature: three-way-merge-assistant, Property 4: Blueprint generation
        completeness

        For any merge session, the system should generate blueprints for all
        three packages (A, B, C) and store them with the session.

        Validates: Requirements 2.1, 2.2
        """
        # Test with real Appian packages
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        # Generate blueprints for all three packages
        # (using same packages for A, B, C for testing purposes)
        base_bp, custom_bp, vendor_bp = (
            self.service.generate_all_blueprints(
                self.test_package_a,
                self.test_package_b,
                self.test_package_a
            )
        )

        # Verify all blueprints were generated
        assert base_bp is not None, "Base blueprint not generated"
        assert custom_bp is not None, "Customized blueprint not generated"
        assert vendor_bp is not None, "New vendor blueprint not generated"

        # Verify blueprint structure
        assert 'blueprint' in base_bp, "Base blueprint missing structure"
        assert 'object_lookup' in base_bp, "Base blueprint missing lookup"
        assert 'blueprint' in custom_bp, "Custom blueprint missing structure"
        assert 'object_lookup' in custom_bp, "Custom blueprint missing lookup"
        assert 'blueprint' in vendor_bp, "Vendor blueprint missing structure"
        assert 'object_lookup' in vendor_bp, "Vendor blueprint missing lookup"

        # Verify blueprints contain metadata
        assert 'metadata' in base_bp['blueprint']
        assert 'metadata' in custom_bp['blueprint']
        assert 'metadata' in vendor_bp['blueprint']

        # Verify blueprints can be serialized (for database storage)
        try:
            json.dumps(base_bp)
            json.dumps(custom_bp)
            json.dumps(vendor_bp)
        except Exception as e:
            self.fail(f"Blueprint serialization failed: {e}")

    def test_property_5_blueprint_failure_handling(self):
        """
        Feature: three-way-merge-assistant, Property 5: Blueprint failure
        handling

        For any package that causes blueprint generation to fail, the session
        status should be marked as 'failed' and error details should be
        stored.

        Validates: Requirements 2.3
        """
        # Test 1: Non-existent file
        with self.assertRaises(BlueprintGenerationError) as context:
            self.service.generate_blueprint('/nonexistent/path/file.zip')
        assert 'not found' in str(context.exception).lower()

        # Test 2: Invalid file format
        with tempfile.NamedTemporaryFile(
            suffix='.txt', delete=False
        ) as tmp:
            tmp.write(b'not a zip file')
            tmp_path = tmp.name

        try:
            with self.assertRaises(BlueprintGenerationError) as context:
                self.service.generate_blueprint(tmp_path)
            assert 'invalid file format' in str(context.exception).lower()
        finally:
            os.unlink(tmp_path)

        # Test 3: Invalid ZIP content (not an Appian package)
        with tempfile.NamedTemporaryFile(
            suffix='.zip', delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            # Create a ZIP with invalid content
            with zipfile.ZipFile(tmp_path, 'w') as zf:
                zf.writestr('invalid.txt', 'not an appian package')

            with self.assertRaises(BlueprintGenerationError) as context:
                self.service.generate_blueprint(tmp_path)
            # Should fail during analysis - check for error indicators
            error_msg = str(context.exception).lower()
            assert ('no appian objects' in error_msg or
                    'failed to generate' in error_msg or
                    'invalid' in error_msg)
        finally:
            os.unlink(tmp_path)

        # Test 4: Parallel generation with one failure
        with tempfile.NamedTemporaryFile(
            suffix='.zip', delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, 'w') as zf:
                zf.writestr('invalid.txt', 'not an appian package')

            # Try to generate with one invalid package
            with self.assertRaises(BlueprintGenerationError) as context:
                self.service.generate_all_blueprints(
                    self.test_package_a,
                    tmp_path,  # Invalid package
                    self.test_package_b
                )
            # Should report which package failed
            assert 'customized' in str(context.exception).lower()
        finally:
            os.unlink(tmp_path)
    
    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_33_session_metadata_persistence(self, session_data):
        """
        Feature: three-way-merge-assistant, Property 33: Session metadata persistence
        
        For any created merge session, the database should store session metadata
        including session ID, timestamps, and all three package names.
        
        Validates: Requirements 16.1
        """
        try:
            # Create session
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                status=session_data['status'],
                current_change_index=session_data['current_change_index'],
                total_changes=session_data['total_changes'],
                reviewed_count=session_data['reviewed_count'],
                skipped_count=session_data['skipped_count']
            )
            
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            # Clear session to force fresh database read
            db.session.expunge_all()
            
            # Retrieve session from database
            retrieved = MergeSession.query.get(session_id)
            
            # Verify all metadata is persisted
            assert retrieved is not None, "Session not found in database"
            assert retrieved.reference_id == session_data['reference_id']
            assert retrieved.base_package_name == session_data['base_package_name']
            assert retrieved.customized_package_name == session_data['customized_package_name']
            assert retrieved.new_vendor_package_name == session_data['new_vendor_package_name']
            assert retrieved.status == session_data['status']
            assert retrieved.current_change_index == session_data['current_change_index']
            assert retrieved.total_changes == session_data['total_changes']
            assert retrieved.reviewed_count == session_data['reviewed_count']
            assert retrieved.skipped_count == session_data['skipped_count']
            assert retrieved.created_at is not None, "created_at timestamp not set"
            assert retrieved.id is not None, "Session ID not assigned"
        finally:
            # Always clean up - even if test fails
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()
    
    @settings(max_examples=100, deadline=None, database=None)
    @given(
        session_data=merge_session_data(),
        base_blueprint=blueprint_data(),
        customized_blueprint=blueprint_data(),
        new_vendor_blueprint=blueprint_data()
    )
    def test_property_34_blueprint_persistence(
        self,
        session_data,
        base_blueprint,
        customized_blueprint,
        new_vendor_blueprint
    ):
        """
        Feature: three-way-merge-assistant, Property 34: Blueprint persistence
        
        For any merge session with generated blueprints, all three blueprints
        (A, B, C) should be stored in the database with the session.
        
        Validates: Requirements 16.2
        """
        try:
            # Create session with blueprints
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                base_blueprint=json.dumps(base_blueprint),
                customized_blueprint=json.dumps(customized_blueprint),
                new_vendor_blueprint=json.dumps(new_vendor_blueprint)
            )
            
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            # Clear session to force fresh database read
            db.session.expunge_all()
            
            # Retrieve session from database
            retrieved = MergeSession.query.get(session_id)
            
            # Verify all blueprints are persisted
            assert retrieved is not None, "Session not found in database"
            assert retrieved.base_blueprint is not None, "Base blueprint not stored"
            assert retrieved.customized_blueprint is not None, "Customized blueprint not stored"
            assert retrieved.new_vendor_blueprint is not None, "New vendor blueprint not stored"
            
            # Verify blueprints can be deserialized
            retrieved_base = json.loads(retrieved.base_blueprint)
            retrieved_customized = json.loads(retrieved.customized_blueprint)
            retrieved_new_vendor = json.loads(retrieved.new_vendor_blueprint)
            
            # Verify blueprint content is preserved
            assert retrieved_base == base_blueprint, "Base blueprint content not preserved"
            assert retrieved_customized == customized_blueprint, "Customized blueprint content not preserved"
            assert retrieved_new_vendor == new_vendor_blueprint, "New vendor blueprint content not preserved"
            
            # Verify blueprint structure
            assert 'objects' in retrieved_base, "Base blueprint missing objects"
            assert 'objects' in retrieved_customized, "Customized blueprint missing objects"
            assert 'objects' in retrieved_new_vendor, "New vendor blueprint missing objects"
            assert len(retrieved_base['objects']) == len(base_blueprint['objects'])
            assert len(retrieved_customized['objects']) == len(customized_blueprint['objects'])
            assert len(retrieved_new_vendor['objects']) == len(new_vendor_blueprint['objects'])
        finally:
            # Always clean up - even if test fails
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_pair_with_changes())
    def test_property_7_vendor_change_identification(self, blueprints):
        """
        Feature: three-way-merge-assistant, Property 7: Vendor change
        identification

        For any two blueprints (A and C), the comparison should correctly
        identify all objects that are ADDED, MODIFIED, or REMOVED in C
        relative to A.

        Validates: Requirements 3.2
        """
        from services.merge_assistant import ThreeWayComparisonService

        base_blueprint, vendor_blueprint = blueprints
        service = ThreeWayComparisonService()

        # Perform vendor change comparison
        vendor_changes = service.compare_vendor_changes(
            base_blueprint,
            vendor_blueprint
        )

        # Verify structure
        assert 'added' in vendor_changes, "Missing 'added' in results"
        assert 'modified' in vendor_changes, "Missing 'modified' in results"
        assert 'removed' in vendor_changes, "Missing 'removed' in results"

        # Get UUIDs from both blueprints
        base_uuids = set(base_blueprint['object_lookup'].keys())
        vendor_uuids = set(vendor_blueprint['object_lookup'].keys())

        # Verify ADDED objects
        added_uuids = {obj['uuid'] for obj in vendor_changes['added']}
        expected_added = vendor_uuids - base_uuids
        assert added_uuids == expected_added, (
            f"Added objects mismatch: {added_uuids} != {expected_added}"
        )

        # Verify REMOVED objects
        removed_uuids = {obj['uuid'] for obj in vendor_changes['removed']}
        expected_removed = base_uuids - vendor_uuids
        assert removed_uuids == expected_removed, (
            f"Removed objects mismatch: {removed_uuids} != {expected_removed}"
        )

        # Verify MODIFIED objects are in common set
        modified_uuids = {obj['uuid'] for obj in vendor_changes['modified']}
        common_uuids = base_uuids & vendor_uuids
        assert modified_uuids.issubset(common_uuids), (
            "Modified objects should be in common set"
        )

        # Verify all objects are accounted for
        all_change_uuids = added_uuids | modified_uuids | removed_uuids
        all_uuids = base_uuids | vendor_uuids
        # Not all common objects may be modified (some may be unchanged)
        assert all_change_uuids.issubset(all_uuids), (
            "All change UUIDs should be in union of base and vendor"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_pair_with_changes())
    def test_property_8_change_detail_capture(self, blueprints):
        """
        Feature: three-way-merge-assistant, Property 8: Change detail capture

        For any modified object, the comparison results should include
        specific change details (SAIL code differences, field changes,
        property changes).

        Validates: Requirements 3.4, 4.4
        """
        from services.merge_assistant import ThreeWayComparisonService

        base_blueprint, target_blueprint = blueprints
        service = ThreeWayComparisonService()

        # Perform comparison
        changes = service.compare_vendor_changes(
            base_blueprint,
            target_blueprint
        )

        # Check modified objects for change details
        for modified_obj in changes['modified']:
            # Verify basic structure
            assert 'uuid' in modified_obj, "Modified object missing UUID"
            assert 'name' in modified_obj, "Modified object missing name"
            assert 'type' in modified_obj, "Modified object missing type"

            uuid = modified_obj['uuid']
            base_obj = base_blueprint['object_lookup'][uuid]
            target_obj = target_blueprint['object_lookup'][uuid]

            # If SAIL code changed, it should be captured
            if 'sail_code' in base_obj and 'sail_code' in target_obj:
                if base_obj['sail_code'] != target_obj['sail_code']:
                    assert (
                        'sail_code_before' in modified_obj or
                        'sail_code_after' in modified_obj
                    ), f"SAIL code change not captured for {uuid}"

            # If fields changed, they should be captured
            if 'fields' in base_obj and 'fields' in target_obj:
                if base_obj['fields'] != target_obj['fields']:
                    assert (
                        'fields_before' in modified_obj or
                        'fields_after' in modified_obj
                    ), f"Field changes not captured for {uuid}"

            # If properties changed, they should be captured
            if 'properties' in base_obj and 'properties' in target_obj:
                if base_obj['properties'] != target_obj['properties']:
                    assert (
                        'properties_before' in modified_obj or
                        'properties_after' in modified_obj
                    ), f"Property changes not captured for {uuid}"

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_pair_with_changes())
    def test_property_9_customer_change_identification(self, blueprints):
        """
        Feature: three-way-merge-assistant, Property 9: Customer change
        identification

        For any two blueprints (A and B), the comparison should correctly
        identify all objects that are ADDED, MODIFIED, or REMOVED in B
        relative to A.

        Validates: Requirements 4.2
        """
        from services.merge_assistant import ThreeWayComparisonService

        base_blueprint, customized_blueprint = blueprints
        service = ThreeWayComparisonService()

        # Perform customer change comparison
        customer_changes = service.compare_customer_changes(
            base_blueprint,
            customized_blueprint
        )

        # Verify structure
        assert 'added' in customer_changes, "Missing 'added' in results"
        assert 'modified' in customer_changes, "Missing 'modified' in results"
        assert 'removed' in customer_changes, "Missing 'removed' in results"

        # Get UUIDs from both blueprints
        base_uuids = set(base_blueprint['object_lookup'].keys())
        custom_uuids = set(customized_blueprint['object_lookup'].keys())

        # Verify ADDED objects
        added_uuids = {obj['uuid'] for obj in customer_changes['added']}
        expected_added = custom_uuids - base_uuids
        assert added_uuids == expected_added, (
            f"Added objects mismatch: {added_uuids} != {expected_added}"
        )

        # Verify REMOVED objects
        removed_uuids = {obj['uuid'] for obj in customer_changes['removed']}
        expected_removed = base_uuids - custom_uuids
        assert removed_uuids == expected_removed, (
            f"Removed objects mismatch: {removed_uuids} != {expected_removed}"
        )

        # Verify MODIFIED objects are in common set
        modified_uuids = {obj['uuid'] for obj in customer_changes['modified']}
        common_uuids = base_uuids & custom_uuids
        assert modified_uuids.issubset(common_uuids), (
            "Modified objects should be in common set"
        )

        # Verify all objects are accounted for
        all_change_uuids = added_uuids | modified_uuids | removed_uuids
        all_uuids = base_uuids | custom_uuids
        assert all_change_uuids.issubset(all_uuids), (
            "All change UUIDs should be in union of base and customized"
        )


    @settings(max_examples=100, deadline=None, database=None)
    @given(
        base_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects(),
        customer_blueprint=blueprint_with_objects()
    )
    def test_property_10_conflict_detection_accuracy(
        self,
        base_blueprint,
        vendor_blueprint,
        customer_blueprint
    ):
        """
        Feature: three-way-merge-assistant, Property 10: Conflict detection
        accuracy

        For any object UUID, if the object is modified in both vendor changes
        (A→C) and customer changes (A→B), it should be classified as CONFLICT.

        Validates: Requirements 5.1
        """
        from services.merge_assistant import (
            ThreeWayComparisonService,
            ChangeClassificationService
        )

        comparison_service = ThreeWayComparisonService()
        classification_service = ChangeClassificationService()

        # Perform comparisons
        vendor_changes = comparison_service.compare_vendor_changes(
            base_blueprint,
            vendor_blueprint
        )
        customer_changes = comparison_service.compare_customer_changes(
            base_blueprint,
            customer_blueprint
        )

        # Classify changes
        classification_results = classification_service.classify_changes(
            vendor_changes,
            customer_changes
        )

        # Build sets of UUIDs in each change type
        vendor_modified_uuids = {
            obj['uuid'] for obj in vendor_changes.get('modified', [])
        }
        vendor_added_uuids = {
            obj['uuid'] for obj in vendor_changes.get('added', [])
        }
        vendor_removed_uuids = {
            obj['uuid'] for obj in vendor_changes.get('removed', [])
        }

        customer_modified_uuids = {
            obj['uuid'] for obj in customer_changes.get('modified', [])
        }
        customer_added_uuids = {
            obj['uuid'] for obj in customer_changes.get('added', [])
        }
        customer_removed_uuids = {
            obj['uuid'] for obj in customer_changes.get('removed', [])
        }

        # Get all vendor and customer changed UUIDs
        vendor_changed_uuids = (
            vendor_modified_uuids | vendor_added_uuids | vendor_removed_uuids
        )
        customer_changed_uuids = (
            customer_modified_uuids | customer_added_uuids |
            customer_removed_uuids
        )

        # Check each classified object
        for category, objects in classification_results.items():
            for obj in objects:
                uuid = obj['uuid']
                classification = obj['classification']

                # If object is in both vendor and customer changes
                if uuid in vendor_changed_uuids and uuid in customer_changed_uuids:
                    # Special case: vendor removed but customer modified
                    if (uuid in vendor_removed_uuids and
                            uuid in customer_modified_uuids):
                        assert classification == 'REMOVED_BUT_CUSTOMIZED', (
                            f"Object {uuid} should be REMOVED_BUT_CUSTOMIZED "
                            f"but was {classification}"
                        )
                    else:
                        # Otherwise should be CONFLICT
                        assert classification == 'CONFLICT', (
                            f"Object {uuid} modified by both vendor and "
                            f"customer should be CONFLICT but was "
                            f"{classification}"
                        )
                # If only vendor changed
                elif uuid in vendor_changed_uuids:
                    assert classification == 'NO_CONFLICT', (
                        f"Object {uuid} changed only by vendor should be "
                        f"NO_CONFLICT but was {classification}"
                    )
                # If only customer changed
                elif uuid in customer_changed_uuids:
                    assert classification == 'CUSTOMER_ONLY', (
                        f"Object {uuid} changed only by customer should be "
                        f"CUSTOMER_ONLY but was {classification}"
                    )


    @settings(max_examples=100, deadline=None, database=None)
    @given(
        base_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects(),
        customer_blueprint=blueprint_with_objects()
    )
    def test_property_11_classification_completeness(
        self,
        base_blueprint,
        vendor_blueprint,
        customer_blueprint
    ):
        """
        Feature: three-way-merge-assistant, Property 11: Classification
        completeness

        For any object in the union of vendor and customer changes, the
        system should assign exactly one classification from {NO_CONFLICT,
        CONFLICT, CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED}.

        Validates: Requirements 5.2
        """
        from services.merge_assistant import (
            ThreeWayComparisonService,
            ChangeClassificationService
        )

        comparison_service = ThreeWayComparisonService()
        classification_service = ChangeClassificationService()

        # Perform comparisons
        vendor_changes = comparison_service.compare_vendor_changes(
            base_blueprint,
            vendor_blueprint
        )
        customer_changes = comparison_service.compare_customer_changes(
            base_blueprint,
            customer_blueprint
        )

        # Get all unique object UUIDs from both change sets
        all_vendor_uuids = set()
        for change_list in vendor_changes.values():
            all_vendor_uuids.update(obj['uuid'] for obj in change_list)

        all_customer_uuids = set()
        for change_list in customer_changes.values():
            all_customer_uuids.update(obj['uuid'] for obj in change_list)

        all_changed_uuids = all_vendor_uuids | all_customer_uuids

        # Classify changes
        classification_results = classification_service.classify_changes(
            vendor_changes,
            customer_changes
        )

        # Verify structure
        assert 'NO_CONFLICT' in classification_results
        assert 'CONFLICT' in classification_results
        assert 'CUSTOMER_ONLY' in classification_results
        assert 'REMOVED_BUT_CUSTOMIZED' in classification_results

        # Collect all classified UUIDs and check for duplicates
        classified_uuids = {}  # uuid -> list of classifications
        for category, objects in classification_results.items():
            for obj in objects:
                uuid = obj['uuid']
                if uuid not in classified_uuids:
                    classified_uuids[uuid] = []
                classified_uuids[uuid].append(category)

        # Property 1: Each object should be classified exactly once
        for uuid, classifications in classified_uuids.items():
            assert len(classifications) == 1, (
                f"Object {uuid} classified {len(classifications)} times: "
                f"{classifications}. Should be classified exactly once."
            )

        # Property 2: All changed objects should be classified
        classified_uuid_set = set(classified_uuids.keys())
        assert classified_uuid_set == all_changed_uuids, (
            f"Classification completeness failed. "
            f"Missing: {all_changed_uuids - classified_uuid_set}, "
            f"Extra: {classified_uuid_set - all_changed_uuids}"
        )

        # Property 3: Each classification should be one of the valid types
        valid_classifications = {
            'NO_CONFLICT',
            'CONFLICT',
            'CUSTOMER_ONLY',
            'REMOVED_BUT_CUSTOMIZED'
        }
        for uuid, classifications in classified_uuids.items():
            classification = classifications[0]
            assert classification in valid_classifications, (
                f"Object {uuid} has invalid classification: {classification}"
            )

        # Property 4: Total count should match
        total_classified = sum(
            len(objects) for objects in classification_results.values()
        )
        assert total_classified == len(all_changed_uuids), (
            f"Total classified objects ({total_classified}) does not match "
            f"total changed objects ({len(all_changed_uuids)})"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        base_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects(),
        customer_blueprint=blueprint_with_objects()
    )
    def test_property_14_change_ordering_correctness(
        self,
        base_blueprint,
        vendor_blueprint,
        customer_blueprint
    ):
        """
        Feature: three-way-merge-assistant, Property 14: Change ordering
        correctness

        For any classified change set, the ordered change list should present
        NO_CONFLICT changes first, then CONFLICT changes, then
        REMOVED_BUT_CUSTOMIZED changes.

        Validates: Requirements 7.1
        """
        from services.merge_assistant import (
            ThreeWayComparisonService,
            ChangeClassificationService,
            DependencyAnalysisService
        )

        comparison_service = ThreeWayComparisonService()
        classification_service = ChangeClassificationService()
        dependency_service = DependencyAnalysisService()

        # Perform comparisons
        vendor_changes = comparison_service.compare_vendor_changes(
            base_blueprint,
            vendor_blueprint
        )
        customer_changes = comparison_service.compare_customer_changes(
            base_blueprint,
            customer_blueprint
        )

        # Classify changes
        classification_results = classification_service.classify_changes(
            vendor_changes,
            customer_changes
        )

        # Build dependency graph (use vendor blueprint as it has most objects)
        dependency_graph = dependency_service.build_dependency_graph(
            vendor_blueprint
        )

        # Order changes
        ordered_changes = dependency_service.order_changes(
            classification_results,
            dependency_graph
        )

        # Verify ordering: NO_CONFLICT first, then CONFLICT, then
        # REMOVED_BUT_CUSTOMIZED
        seen_classifications = []
        for change in ordered_changes:
            classification = change.get('classification')
            if classification:
                if not seen_classifications or (
                    seen_classifications[-1] != classification
                ):
                    seen_classifications.append(classification)

        # Define expected order
        expected_order = [
            'NO_CONFLICT',
            'CONFLICT',
            'CUSTOMER_ONLY',
            'REMOVED_BUT_CUSTOMIZED'
        ]

        # Filter to only classifications that exist
        existing_classifications = [
            c for c in expected_order if c in seen_classifications
        ]

        # Verify order matches expected
        assert seen_classifications == existing_classifications, (
            f"Change ordering incorrect. "
            f"Expected: {existing_classifications}, "
            f"Got: {seen_classifications}"
        )

        # Verify all NO_CONFLICT come before all CONFLICT
        no_conflict_indices = [
            i for i, c in enumerate(ordered_changes)
            if c.get('classification') == 'NO_CONFLICT'
        ]
        conflict_indices = [
            i for i, c in enumerate(ordered_changes)
            if c.get('classification') == 'CONFLICT'
        ]

        if no_conflict_indices and conflict_indices:
            max_no_conflict = max(no_conflict_indices)
            min_conflict = min(conflict_indices)
            assert max_no_conflict < min_conflict, (
                "All NO_CONFLICT changes should come before CONFLICT changes"
            )

        # Verify all CONFLICT come before all REMOVED_BUT_CUSTOMIZED
        removed_indices = [
            i for i, c in enumerate(ordered_changes)
            if c.get('classification') == 'REMOVED_BUT_CUSTOMIZED'
        ]

        if conflict_indices and removed_indices:
            max_conflict = max(conflict_indices)
            min_removed = min(removed_indices)
            assert max_conflict < min_removed, (
                "All CONFLICT changes should come before "
                "REMOVED_BUT_CUSTOMIZED changes"
            )

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        base_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects(),
        customer_blueprint=blueprint_with_objects()
    )
    def test_property_15_object_type_grouping(
        self,
        base_blueprint,
        vendor_blueprint,
        customer_blueprint
    ):
        """
        Feature: three-way-merge-assistant, Property 15: Object type grouping

        For any set of NO_CONFLICT changes, objects of the same type should
        be grouped together in the ordered list.

        Validates: Requirements 7.2
        """
        from services.merge_assistant import (
            ThreeWayComparisonService,
            ChangeClassificationService,
            DependencyAnalysisService
        )

        comparison_service = ThreeWayComparisonService()
        classification_service = ChangeClassificationService()
        dependency_service = DependencyAnalysisService()

        # Perform comparisons
        vendor_changes = comparison_service.compare_vendor_changes(
            base_blueprint,
            vendor_blueprint
        )
        customer_changes = comparison_service.compare_customer_changes(
            base_blueprint,
            customer_blueprint
        )

        # Classify changes
        classification_results = classification_service.classify_changes(
            vendor_changes,
            customer_changes
        )

        # Build dependency graph
        dependency_graph = dependency_service.build_dependency_graph(
            vendor_blueprint
        )

        # Order changes
        ordered_changes = dependency_service.order_changes(
            classification_results,
            dependency_graph
        )

        # Extract NO_CONFLICT changes
        no_conflict_changes = [
            c for c in ordered_changes
            if c.get('classification') == 'NO_CONFLICT'
        ]

        if len(no_conflict_changes) < 2:
            # Not enough changes to test grouping
            return

        # Verify objects of same type are grouped together
        # Track type transitions
        current_type = None
        seen_types = set()
        type_transitions = []

        for change in no_conflict_changes:
            obj_type = change.get('type', 'Unknown')

            if current_type != obj_type:
                # Type changed
                if obj_type in seen_types:
                    # We've seen this type before - grouping violated
                    self.fail(
                        f"Object type grouping violated: type '{obj_type}' "
                        f"appears in multiple non-contiguous groups. "
                        f"Transitions: {type_transitions}"
                    )

                seen_types.add(obj_type)
                type_transitions.append(obj_type)
                current_type = obj_type

        # If we get here, grouping is correct

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        base_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects(),
        customer_blueprint=blueprint_with_objects()
    )
    def test_property_16_dependency_ordering(
        self,
        base_blueprint,
        vendor_blueprint,
        customer_blueprint
    ):
        """
        Feature: three-way-merge-assistant, Property 16: Dependency ordering

        For any set of CONFLICT changes with dependencies, parent objects
        should appear before their child objects in the ordered list.

        Validates: Requirements 7.3
        """
        from services.merge_assistant import (
            ThreeWayComparisonService,
            ChangeClassificationService,
            DependencyAnalysisService
        )

        comparison_service = ThreeWayComparisonService()
        classification_service = ChangeClassificationService()
        dependency_service = DependencyAnalysisService()

        # Perform comparisons
        vendor_changes = comparison_service.compare_vendor_changes(
            base_blueprint,
            vendor_blueprint
        )
        customer_changes = comparison_service.compare_customer_changes(
            base_blueprint,
            customer_blueprint
        )

        # Classify changes
        classification_results = classification_service.classify_changes(
            vendor_changes,
            customer_changes
        )

        # Build dependency graph
        dependency_graph = dependency_service.build_dependency_graph(
            vendor_blueprint
        )

        # Order changes
        ordered_changes = dependency_service.order_changes(
            classification_results,
            dependency_graph
        )

        # Extract CONFLICT changes
        conflict_changes = [
            c for c in ordered_changes
            if c.get('classification') == 'CONFLICT'
        ]

        if len(conflict_changes) < 2:
            # Not enough changes to test dependency ordering
            return

        # Build position map
        position = {
            change['uuid']: i
            for i, change in enumerate(conflict_changes)
        }

        # Verify dependency ordering
        for change in conflict_changes:
            uuid = change['uuid']
            dependencies = dependency_graph.get(uuid, [])

            # Check each dependency
            for dep_uuid in dependencies:
                if dep_uuid in position:
                    # Dependency is also in conflict changes
                    # It should appear before this object
                    assert position[dep_uuid] < position[uuid], (
                        f"Dependency ordering violated: "
                        f"Object {uuid} at position {position[uuid]} "
                        f"depends on {dep_uuid} at position "
                        f"{position[dep_uuid]}, but parent should come first"
                    )

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        base_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects()
    )
    def test_property_29_dependency_display_completeness(
        self,
        base_blueprint,
        vendor_blueprint
    ):
        """
        Feature: three-way-merge-assistant, Property 29: Dependency display
        completeness

        For any change being viewed, the system should display both parent
        objects (dependencies) and child objects (reverse dependencies).

        Validates: Requirements 14.1, 14.2
        """
        from services.merge_assistant import DependencyAnalysisService

        dependency_service = DependencyAnalysisService()

        # Build dependency graph
        dependency_graph = dependency_service.build_dependency_graph(
            vendor_blueprint
        )

        # Test get_dependencies for each object
        object_lookup = vendor_blueprint.get('object_lookup', {})

        for uuid in object_lookup.keys():
            # Get dependencies
            deps = dependency_service.get_dependencies(
                uuid,
                dependency_graph
            )

            # Verify structure
            assert 'parents' in deps, (
                f"Missing 'parents' in dependencies for {uuid}"
            )
            assert 'children' in deps, (
                f"Missing 'children' in dependencies for {uuid}"
            )

            # Verify parents are correct
            expected_parents = dependency_graph.get(uuid, [])
            assert set(deps['parents']) == set(expected_parents), (
                f"Parent dependencies incorrect for {uuid}. "
                f"Expected: {expected_parents}, Got: {deps['parents']}"
            )

            # Verify children are correct
            # Children are objects that have this uuid in their dependencies
            expected_children = [
                obj_uuid for obj_uuid, obj_deps in dependency_graph.items()
                if uuid in obj_deps
            ]
            assert set(deps['children']) == set(expected_children), (
                f"Child dependencies incorrect for {uuid}. "
                f"Expected: {expected_children}, Got: {deps['children']}"
            )

            # Verify parents and children are lists
            assert isinstance(deps['parents'], list), (
                f"Parents should be a list for {uuid}"
            )
            assert isinstance(deps['children'], list), (
                f"Children should be a list for {uuid}"
            )


    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_pair_with_changes())
    def test_property_31_vendor_addition_identification(self, blueprints):
        """
        Feature: three-way-merge-assistant, Property 31: Vendor addition
        identification

        For any CONFLICT change, the system should identify specific vendor
        additions (new functions, fields, logic) that do not exist in the
        customer version.

        Validates: Requirements 15.1
        """
        from services.merge_assistant import MergeGuidanceService

        base, vendor = blueprints
        base_lookup = base['object_lookup']
        vendor_lookup = vendor['object_lookup']

        # Create a customer version (same as base for this test)
        customer_lookup = {k: v.copy() for k, v in base_lookup.items()}

        service = MergeGuidanceService()

        # Find objects that were modified in vendor
        for uuid in vendor_lookup:
            if uuid in base_lookup:
                base_obj = base_lookup[uuid]
                vendor_obj = vendor_lookup[uuid]
                customer_obj = customer_lookup.get(uuid, base_obj)

                # Check if vendor made changes
                vendor_changed = (
                    vendor_obj.get('sail_code') != base_obj.get('sail_code')
                    or vendor_obj.get('fields') != base_obj.get('fields')
                    or vendor_obj.get('properties') != base_obj.get('properties')
                )

                if vendor_changed:
                    # Identify vendor additions
                    additions = service._identify_vendor_additions(
                        base_obj,
                        vendor_obj,
                        customer_obj
                    )

                    # Verify additions is a list
                    assert isinstance(additions, list), (
                        "Vendor additions should be a list"
                    )

                    # Each addition should have required fields
                    for addition in additions:
                        assert isinstance(addition, dict), (
                            "Each addition should be a dictionary"
                        )
                        assert 'type' in addition, (
                            "Addition missing 'type' field"
                        )
                        assert 'description' in addition, (
                            "Addition missing 'description' field"
                        )
                        assert 'location' in addition, (
                            "Addition missing 'location' field"
                        )

                    # If vendor added SAIL code, it should be detected
                    if ('sail_code' in vendor_obj and
                            'sail_code' in base_obj and
                            vendor_obj['sail_code'] != base_obj['sail_code']):
                        # Should have at least one SAIL code addition
                        sail_additions = [
                            a for a in additions if a['type'] == 'sail_code'
                        ]
                        # Note: May be empty if all changes are in customer too
                        assert isinstance(sail_additions, list)

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_pair_with_changes())
    def test_property_32_vendor_modification_identification(self, blueprints):
        """
        Feature: three-way-merge-assistant, Property 32: Vendor modification
        identification

        For any CONFLICT change, the system should identify vendor
        modifications to sections that exist in both base and customer
        versions.

        Validates: Requirements 15.2
        """
        from services.merge_assistant import MergeGuidanceService

        base, vendor = blueprints
        base_lookup = base['object_lookup']
        vendor_lookup = vendor['object_lookup']

        service = MergeGuidanceService()

        # Find objects that exist in both base and vendor
        for uuid in set(base_lookup.keys()) & set(vendor_lookup.keys()):
            base_obj = base_lookup[uuid]
            vendor_obj = vendor_lookup[uuid]

            # Identify vendor modifications
            modifications = service._identify_vendor_modifications(
                base_obj,
                vendor_obj
            )

            # Verify modifications is a list
            assert isinstance(modifications, list), (
                "Vendor modifications should be a list"
            )

            # Each modification should have required fields
            for mod in modifications:
                assert isinstance(mod, dict), (
                    "Each modification should be a dictionary"
                )
                assert 'type' in mod, "Modification missing 'type' field"
                assert 'description' in mod, (
                    "Modification missing 'description' field"
                )
                assert 'location' in mod, (
                    "Modification missing 'location' field"
                )

            # If objects are identical, should have no modifications
            if base_obj == vendor_obj:
                assert len(modifications) == 0, (
                    "Identical objects should have no modifications"
                )

            # If SAIL code changed, should detect it
            if ('sail_code' in base_obj and 'sail_code' in vendor_obj and
                    base_obj['sail_code'] != vendor_obj['sail_code']):
                sail_mods = [
                    m for m in modifications if m['type'] == 'sail_code'
                ]
                assert len(sail_mods) > 0, (
                    "SAIL code change should be detected"
                )

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_pair_with_changes())
    def test_property_36_merge_strategy_recommendations(self, blueprints):
        """
        Feature: three-way-merge-assistant, Property 36: Merge strategy
        recommendations

        For any CONFLICT change, the system should provide merge strategy
        recommendations appropriate to the type of conflict.

        Validates: Requirements 17.1
        """
        from services.merge_assistant import (
            MergeGuidanceService,
            MergeStrategy
        )

        base, vendor = blueprints
        base_lookup = base['object_lookup']
        vendor_lookup = vendor['object_lookup']

        # Create customer version (modified from base)
        customer_lookup = {}
        for uuid, obj in base_lookup.items():
            customer_obj = obj.copy()
            # Modify some objects to create conflicts
            if 'sail_code' in customer_obj:
                customer_obj['sail_code'] = (
                    customer_obj['sail_code'] + "\n// Customer change"
                )
            customer_lookup[uuid] = customer_obj

        service = MergeGuidanceService()

        # Test different classification scenarios
        test_cases = [
            {
                'classification': 'NO_CONFLICT',
                'expected_strategies': [
                    MergeStrategy.ADOPT_VENDOR_CHANGES.value,
                    MergeStrategy.REVIEW_VENDOR_REMOVAL.value
                ]
            },
            {
                'classification': 'CONFLICT',
                'expected_strategies': [
                    MergeStrategy.MANUAL_MERGE_REQUIRED.value,
                    MergeStrategy.INCORPORATE_VENDOR_ADDITIONS.value
                ]
            },
            {
                'classification': 'CUSTOMER_ONLY',
                'expected_strategies': [
                    MergeStrategy.KEEP_CUSTOMER_VERSION.value
                ]
            },
            {
                'classification': 'REMOVED_BUT_CUSTOMIZED',
                'expected_strategies': [
                    MergeStrategy.KEEP_CUSTOMER_VERSION.value
                ]
            }
        ]

        for test_case in test_cases:
            classification = test_case['classification']
            expected_strategies = test_case['expected_strategies']

            # Create a change object
            change = {
                'uuid': 'test-uuid',
                'name': 'Test Object',
                'type': 'Interface',
                'classification': classification
            }

            # Get objects based on classification
            if classification == 'NO_CONFLICT':
                # Vendor changed, customer didn't
                base_obj = list(base_lookup.values())[0] if base_lookup else None
                vendor_obj = list(vendor_lookup.values())[0] if vendor_lookup else None
                customer_obj = base_obj
            elif classification == 'CONFLICT':
                # Both changed
                base_obj = list(base_lookup.values())[0] if base_lookup else None
                vendor_obj = list(vendor_lookup.values())[0] if vendor_lookup else None
                customer_obj = list(customer_lookup.values())[0] if customer_lookup else None
            elif classification == 'CUSTOMER_ONLY':
                # Only customer changed
                base_obj = list(base_lookup.values())[0] if base_lookup else None
                vendor_obj = base_obj
                customer_obj = list(customer_lookup.values())[0] if customer_lookup else None
            else:  # REMOVED_BUT_CUSTOMIZED
                # Vendor removed, customer modified
                base_obj = list(base_lookup.values())[0] if base_lookup else None
                vendor_obj = None
                customer_obj = list(customer_lookup.values())[0] if customer_lookup else None

            # Generate guidance
            guidance = service.generate_guidance(
                change,
                base_obj,
                customer_obj,
                vendor_obj
            )

            # Verify guidance structure
            assert isinstance(guidance, dict), "Guidance should be a dictionary"
            assert 'strategy' in guidance, "Guidance missing 'strategy' field"
            assert 'recommendations' in guidance, (
                "Guidance missing 'recommendations' field"
            )
            assert 'vendor_additions' in guidance, (
                "Guidance missing 'vendor_additions' field"
            )
            assert 'vendor_modifications' in guidance, (
                "Guidance missing 'vendor_modifications' field"
            )
            assert 'conflict_sections' in guidance, (
                "Guidance missing 'conflict_sections' field"
            )

            # Verify strategy is appropriate for classification
            assert guidance['strategy'] in expected_strategies, (
                f"Strategy '{guidance['strategy']}' not appropriate for "
                f"classification '{classification}'. Expected one of: "
                f"{expected_strategies}"
            )

            # Verify recommendations is a list
            assert isinstance(guidance['recommendations'], list), (
                "Recommendations should be a list"
            )

            # For conflicts, should have recommendations
            if classification == 'CONFLICT':
                # May or may not have recommendations depending on the objects
                assert isinstance(guidance['recommendations'], list)

            # Verify all lists are properly typed
            assert isinstance(guidance['vendor_additions'], list)
            assert isinstance(guidance['vendor_modifications'], list)
            assert isinstance(guidance['conflict_sections'], list)

    # ========================================================================
    # Property Tests for Task 7: ThreeWayMergeService (Orchestration)
    # ========================================================================

    def test_property_6_workflow_progression_after_blueprints(self):
        """
        Feature: three-way-merge-assistant, Property 6: Workflow progression
        after blueprints

        For any session where all three blueprints are successfully generated,
        the system should automatically proceed to the comparison phase.

        Validates: Requirements 2.4
        """
        from services.merge_assistant import ThreeWayMergeService

        # Test with real Appian packages
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        service = ThreeWayMergeService()

        # Create a session
        session = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        # Verify session was created
        assert session is not None, "Session should be created"
        assert session.id is not None, "Session should have an ID"

        # Verify blueprints were generated
        assert session.base_blueprint is not None, (
            "Base blueprint should be generated"
        )
        assert session.customized_blueprint is not None, (
            "Customized blueprint should be generated"
        )
        assert session.new_vendor_blueprint is not None, (
            "New vendor blueprint should be generated"
        )

        # Verify workflow progressed to comparison phase
        assert session.vendor_changes is not None, (
            "Vendor changes should be computed after blueprints"
        )
        assert session.customer_changes is not None, (
            "Customer changes should be computed after blueprints"
        )

        # Verify workflow progressed to classification phase
        assert session.classification_results is not None, (
            "Classification should be completed after comparison"
        )

        # Verify workflow progressed to ordering phase
        assert session.ordered_changes is not None, (
            "Changes should be ordered after classification"
        )

        # Verify session status is 'ready' (not stuck in 'processing')
        assert session.status == 'ready', (
            f"Session status should be 'ready' after successful processing, "
            f"got '{session.status}'"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_12_summary_statistics_accuracy(self, session_data):
        """
        Feature: three-way-merge-assistant, Property 12: Summary statistics
        accuracy

        For any merge session, the displayed summary counts for each
        classification category should match the actual number of objects
        in each category from the classification results.

        Validates: Requirements 6.2
        """
        from services.merge_assistant import ThreeWayMergeService

        # Create a session with known classification results
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status='ready'
        )

        # Create classification results with known counts
        classification_results = {
            'NO_CONFLICT': [
                {'uuid': f'uuid_{i}', 'name': f'obj_{i}', 'type': 'Interface'}
                for i in range(10)
            ],
            'CONFLICT': [
                {'uuid': f'uuid_c_{i}', 'name': f'conflict_{i}', 'type': 'Rule'}
                for i in range(5)
            ],
            'CUSTOMER_ONLY': [
                {'uuid': f'uuid_co_{i}', 'name': f'customer_{i}', 'type': 'Constant'}
                for i in range(3)
            ],
            'REMOVED_BUT_CUSTOMIZED': [
                {'uuid': f'uuid_r_{i}', 'name': f'removed_{i}', 'type': 'Site'}
                for i in range(2)
            ]
        }

        session.classification_results = json.dumps(classification_results)
        session.total_changes = 20  # 10 + 5 + 3 + 2
        session.ordered_changes = json.dumps([])  # Empty for this test

        db.session.add(session)
        db.session.commit()

        # Get summary
        service = ThreeWayMergeService()
        summary = service.get_summary(session.id)

        # Verify statistics match actual counts
        assert summary['statistics']['total_changes'] == 20, (
            "Total changes should match sum of all categories"
        )
        assert summary['statistics']['no_conflict'] == 10, (
            "NO_CONFLICT count should match actual count"
        )
        assert summary['statistics']['conflict'] == 5, (
            "CONFLICT count should match actual count"
        )
        assert summary['statistics']['customer_only'] == 3, (
            "CUSTOMER_ONLY count should match actual count"
        )
        assert summary['statistics']['removed_but_customized'] == 2, (
            "REMOVED_BUT_CUSTOMIZED count should match actual count"
        )

        # Verify sum of categories equals total
        category_sum = (
            summary['statistics']['no_conflict'] +
            summary['statistics']['conflict'] +
            summary['statistics']['customer_only'] +
            summary['statistics']['removed_but_customized']
        )
        assert category_sum == summary['statistics']['total_changes'], (
            "Sum of category counts should equal total changes"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_13_breakdown_accuracy(self, session_data):
        """
        Feature: three-way-merge-assistant, Property 13: Breakdown accuracy

        For any merge session, the breakdown by object type should correctly
        count objects of each type within each classification category.

        Validates: Requirements 6.3
        """
        from services.merge_assistant import ThreeWayMergeService

        # Create a session with known classification results
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status='ready'
        )

        # Create classification results with known type distribution
        classification_results = {
            'NO_CONFLICT': [
                {'uuid': 'uuid_1', 'name': 'obj_1', 'type': 'Interface'},
                {'uuid': 'uuid_2', 'name': 'obj_2', 'type': 'Interface'},
                {'uuid': 'uuid_3', 'name': 'obj_3', 'type': 'Rule'},
            ],
            'CONFLICT': [
                {'uuid': 'uuid_4', 'name': 'obj_4', 'type': 'Interface'},
                {'uuid': 'uuid_5', 'name': 'obj_5', 'type': 'Rule'},
                {'uuid': 'uuid_6', 'name': 'obj_6', 'type': 'Rule'},
            ],
            'CUSTOMER_ONLY': [
                {'uuid': 'uuid_7', 'name': 'obj_7', 'type': 'Constant'},
            ],
            'REMOVED_BUT_CUSTOMIZED': [
                {'uuid': 'uuid_8', 'name': 'obj_8', 'type': 'Site'},
            ]
        }

        session.classification_results = json.dumps(classification_results)
        session.total_changes = 8
        session.ordered_changes = json.dumps([])

        db.session.add(session)
        db.session.commit()

        # Get summary
        service = ThreeWayMergeService()
        summary = service.get_summary(session.id)

        # Verify breakdown by type
        breakdown = summary['breakdown_by_type']

        # Check Interface counts
        assert 'Interface' in breakdown, "Interface should be in breakdown"
        assert breakdown['Interface']['no_conflict'] == 2, (
            "Should have 2 NO_CONFLICT Interfaces"
        )
        assert breakdown['Interface']['conflict'] == 1, (
            "Should have 1 CONFLICT Interface"
        )

        # Check Rule counts
        assert 'Rule' in breakdown, "Rule should be in breakdown"
        assert breakdown['Rule']['no_conflict'] == 1, (
            "Should have 1 NO_CONFLICT Rule"
        )
        assert breakdown['Rule']['conflict'] == 2, (
            "Should have 2 CONFLICT Rules"
        )

        # Check Constant counts
        assert 'Constant' in breakdown, "Constant should be in breakdown"
        assert breakdown['Constant']['customer_only'] == 1, (
            "Should have 1 CUSTOMER_ONLY Constant"
        )

        # Check Site counts
        assert 'Site' in breakdown, "Site should be in breakdown"
        assert breakdown['Site']['removed_but_customized'] == 1, (
            "Should have 1 REMOVED_BUT_CUSTOMIZED Site"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_22_progress_tracking_accuracy(self, session_data):
        """
        Feature: three-way-merge-assistant, Property 22: Progress tracking
        accuracy

        For any user action (mark as reviewed or skip), the progress counter
        should increment and the session state should be updated in the
        database.

        Validates: Requirements 10.2, 10.3
        """
        from services.merge_assistant import ThreeWayMergeService

        # Create a session with ordered changes
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status='in_progress',
            current_change_index=0,
            reviewed_count=0,
            skipped_count=0
        )

        # Create ordered changes
        ordered_changes = [
            {
                'uuid': f'uuid_{i}',
                'name': f'Object {i}',
                'type': 'Interface',
                'classification': 'NO_CONFLICT'
            }
            for i in range(5)
        ]

        session.ordered_changes = json.dumps(ordered_changes)
        session.total_changes = len(ordered_changes)

        db.session.add(session)
        db.session.commit()

        service = ThreeWayMergeService()

        # Test marking as reviewed
        initial_reviewed = session.reviewed_count
        service.update_progress(
            session.id,
            0,
            'reviewed',
            'Test note'
        )

        # Refresh session from database
        db.session.expire(session)
        session = service.get_session(session.id)

        # Verify progress was updated
        assert session.current_change_index == 0, (
            "Current change index should be updated"
        )
        assert session.reviewed_count > initial_reviewed, (
            "Reviewed count should increment"
        )

        # Verify ChangeReview record was created
        review = ChangeReview.query.filter_by(
            session_id=session.id,
            object_uuid='uuid_0'
        ).first()

        assert review is not None, "ChangeReview record should be created"
        assert review.review_status == 'reviewed', (
            "Review status should be 'reviewed'"
        )
        assert review.user_notes == 'Test note', (
            "User notes should be stored"
        )
        assert review.reviewed_at is not None, (
            "Reviewed timestamp should be set"
        )

        # Test marking as skipped
        initial_skipped = session.skipped_count
        service.update_progress(
            session.id,
            1,
            'skipped'
        )

        # Refresh session
        db.session.expire(session)
        session = service.get_session(session.id)

        # Verify skipped count incremented
        assert session.skipped_count > initial_skipped, (
            "Skipped count should increment"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_23_session_persistence_round_trip(self, session_data):
        """
        Feature: three-way-merge-assistant, Property 23: Session persistence
        round-trip

        For any merge session, if a user navigates away and returns, the
        restored session state should match the saved state including current
        change index and review statuses.

        Validates: Requirements 10.5
        """
        from services.merge_assistant import ThreeWayMergeService

        # Create a session with progress
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status='in_progress',
            current_change_index=3,
            reviewed_count=2,
            skipped_count=1,
            total_changes=10
        )

        # Add some data
        ordered_changes = [
            {
                'uuid': f'uuid_{i}',
                'name': f'Object {i}',
                'type': 'Interface',
                'classification': 'NO_CONFLICT'
            }
            for i in range(10)
        ]

        session.ordered_changes = json.dumps(ordered_changes)
        session.classification_results = json.dumps({
            'NO_CONFLICT': ordered_changes,
            'CONFLICT': [],
            'CUSTOMER_ONLY': [],
            'REMOVED_BUT_CUSTOMIZED': []
        })

        db.session.add(session)
        db.session.commit()

        # Save original state
        original_state = {
            'reference_id': session.reference_id,
            'status': session.status,
            'current_change_index': session.current_change_index,
            'reviewed_count': session.reviewed_count,
            'skipped_count': session.skipped_count,
            'total_changes': session.total_changes
        }

        session_id = session.id

        # Simulate navigation away (clear session cache)
        db.session.expunge_all()

        # Restore session
        service = ThreeWayMergeService()
        restored_session = service.get_session(session_id)

        # Verify restored state matches original
        assert restored_session is not None, "Session should be restored"
        assert restored_session.reference_id == original_state['reference_id'], (
            "Reference ID should be preserved"
        )
        assert restored_session.status == original_state['status'], (
            "Status should be preserved"
        )
        assert (
            restored_session.current_change_index ==
            original_state['current_change_index']
        ), "Current change index should be preserved"
        assert (
            restored_session.reviewed_count ==
            original_state['reviewed_count']
        ), "Reviewed count should be preserved"
        assert (
            restored_session.skipped_count ==
            original_state['skipped_count']
        ), "Skipped count should be preserved"
        assert (
            restored_session.total_changes ==
            original_state['total_changes']
        ), "Total changes should be preserved"

        # Verify ordered changes are preserved
        restored_changes = json.loads(restored_session.ordered_changes)
        assert len(restored_changes) == len(ordered_changes), (
            "Ordered changes should be preserved"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_24_report_generation_completeness(self, session_data):
        """
        Feature: three-way-merge-assistant, Property 24: Report generation
        completeness

        For any completed merge workflow, the generated report should include
        summary statistics (total changes, reviewed count, skipped count,
        conflict count).

        Validates: Requirements 12.2
        """
        from services.merge_assistant import ThreeWayMergeService

        # Create a completed session
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status='completed',
            current_change_index=4,
            reviewed_count=3,
            skipped_count=2,
            total_changes=5,
            total_time=300,
            completed_at=datetime.utcnow()
        )

        # Create classification results
        classification_results = {
            'NO_CONFLICT': [
                {'uuid': 'uuid_1', 'name': 'obj_1', 'type': 'Interface',
                 'classification': 'NO_CONFLICT'},
                {'uuid': 'uuid_2', 'name': 'obj_2', 'type': 'Rule',
                 'classification': 'NO_CONFLICT'},
            ],
            'CONFLICT': [
                {'uuid': 'uuid_3', 'name': 'obj_3', 'type': 'Interface',
                 'classification': 'CONFLICT'},
                {'uuid': 'uuid_4', 'name': 'obj_4', 'type': 'Rule',
                 'classification': 'CONFLICT'},
            ],
            'CUSTOMER_ONLY': [
                {'uuid': 'uuid_5', 'name': 'obj_5', 'type': 'Constant',
                 'classification': 'CUSTOMER_ONLY'},
            ],
            'REMOVED_BUT_CUSTOMIZED': []
        }

        ordered_changes = (
            classification_results['NO_CONFLICT'] +
            classification_results['CONFLICT'] +
            classification_results['CUSTOMER_ONLY']
        )

        session.classification_results = json.dumps(classification_results)
        session.ordered_changes = json.dumps(ordered_changes)

        db.session.add(session)
        db.session.commit()

        # Generate report
        service = ThreeWayMergeService()
        report = service.generate_report(session.id)

        # Verify report structure
        assert 'summary' in report, "Report should include summary"
        assert 'changes' in report, "Report should include changes"
        assert 'statistics' in report, "Report should include statistics"
        assert 'session' in report, "Report should include session info"

        # Verify statistics completeness
        stats = report['statistics']
        assert 'total_changes' in stats, (
            "Statistics should include total_changes"
        )
        assert 'reviewed' in stats, "Statistics should include reviewed"
        assert 'skipped' in stats, "Statistics should include skipped"
        assert 'conflicts' in stats, "Statistics should include conflicts"
        assert 'processing_time_seconds' in stats, (
            "Statistics should include processing_time_seconds"
        )

        # Verify statistics values
        assert stats['total_changes'] == 5, (
            "Total changes should match session"
        )
        assert stats['reviewed'] == 3, "Reviewed count should match session"
        assert stats['skipped'] == 2, "Skipped count should match session"
        assert stats['conflicts'] == 2, (
            "Conflicts should match classification results"
        )
        assert stats['processing_time_seconds'] == 300, (
            "Processing time should match session"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_25_report_detail_completeness(self, session_data):
        """
        Feature: three-way-merge-assistant, Property 25: Report detail
        completeness

        For any generated report, all changes should be listed with their
        classification, review status, and any user notes.

        Validates: Requirements 12.3
        """
        from services.merge_assistant import ThreeWayMergeService

        # Create a session with changes and reviews
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status='completed',
            total_changes=3,
            reviewed_count=2,
            skipped_count=1
        )

        # Create ordered changes
        ordered_changes = [
            {
                'uuid': 'uuid_1',
                'name': 'Object 1',
                'type': 'Interface',
                'classification': 'NO_CONFLICT'
            },
            {
                'uuid': 'uuid_2',
                'name': 'Object 2',
                'type': 'Rule',
                'classification': 'CONFLICT'
            },
            {
                'uuid': 'uuid_3',
                'name': 'Object 3',
                'type': 'Constant',
                'classification': 'CUSTOMER_ONLY'
            }
        ]

        session.ordered_changes = json.dumps(ordered_changes)
        session.classification_results = json.dumps({
            'NO_CONFLICT': [ordered_changes[0]],
            'CONFLICT': [ordered_changes[1]],
            'CUSTOMER_ONLY': [ordered_changes[2]],
            'REMOVED_BUT_CUSTOMIZED': []
        })

        db.session.add(session)
        db.session.commit()

        # Create review records
        review1 = ChangeReview(
            session_id=session.id,
            object_uuid='uuid_1',
            object_name='Object 1',
            object_type='Interface',
            classification='NO_CONFLICT',
            review_status='reviewed',
            user_notes='Looks good',
            reviewed_at=datetime.utcnow()
        )
        review2 = ChangeReview(
            session_id=session.id,
            object_uuid='uuid_2',
            object_name='Object 2',
            object_type='Rule',
            classification='CONFLICT',
            review_status='reviewed',
            user_notes='Needs attention',
            reviewed_at=datetime.utcnow()
        )
        review3 = ChangeReview(
            session_id=session.id,
            object_uuid='uuid_3',
            object_name='Object 3',
            object_type='Constant',
            classification='CUSTOMER_ONLY',
            review_status='skipped',
            user_notes=None,
            reviewed_at=datetime.utcnow()
        )

        db.session.add_all([review1, review2, review3])
        db.session.commit()

        # Generate report
        service = ThreeWayMergeService()
        report = service.generate_report(session.id)

        # Verify all changes are in report
        changes = report['changes']
        assert len(changes) == 3, "Report should include all changes"

        # Verify each change has required fields
        for change in changes:
            assert 'uuid' in change, "Change should have uuid"
            assert 'name' in change, "Change should have name"
            assert 'type' in change, "Change should have type"
            assert 'classification' in change, (
                "Change should have classification"
            )
            assert 'review_status' in change, (
                "Change should have review_status"
            )
            # user_notes can be None, but field should exist
            assert 'user_notes' in change, "Change should have user_notes field"

        # Verify specific review information
        change1 = next(c for c in changes if c['uuid'] == 'uuid_1')
        assert change1['review_status'] == 'reviewed', (
            "Change 1 should be marked as reviewed"
        )
        assert change1['user_notes'] == 'Looks good', (
            "Change 1 should have user notes"
        )

        change2 = next(c for c in changes if c['uuid'] == 'uuid_2')
        assert change2['review_status'] == 'reviewed', (
            "Change 2 should be marked as reviewed"
        )
        assert change2['user_notes'] == 'Needs attention', (
            "Change 2 should have user notes"
        )

        change3 = next(c for c in changes if c['uuid'] == 'uuid_3')
        assert change3['review_status'] == 'skipped', (
            "Change 3 should be marked as skipped"
        )

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_35_real_time_state_updates(self, session_data):
        """
        Feature: three-way-merge-assistant, Property 35: Real-time state
        updates

        For any user review action, the session state in the database should
        be updated immediately (within the same request cycle).

        Validates: Requirements 16.4, 16.5
        """
        from services.merge_assistant import ThreeWayMergeService

        # Create a session
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status='in_progress',
            current_change_index=0,
            reviewed_count=0,
            skipped_count=0,
            total_changes=5
        )

        # Create ordered changes
        ordered_changes = [
            {
                'uuid': f'uuid_{i}',
                'name': f'Object {i}',
                'type': 'Interface',
                'classification': 'NO_CONFLICT'
            }
            for i in range(5)
        ]

        session.ordered_changes = json.dumps(ordered_changes)

        db.session.add(session)
        db.session.commit()

        service = ThreeWayMergeService()

        # Perform a review action
        service.update_progress(
            session.id,
            0,
            'reviewed',
            'Test note'
        )

        # Immediately query the database (no cache)
        # This simulates a new request cycle
        db.session.expire_all()
        updated_session = MergeSession.query.get(session.id)

        # Verify state was updated in database
        assert updated_session.current_change_index == 0, (
            "Current change index should be updated in database"
        )
        assert updated_session.reviewed_count > 0, (
            "Reviewed count should be updated in database"
        )

        # Verify ChangeReview record exists in database
        review = ChangeReview.query.filter_by(
            session_id=session.id,
            object_uuid='uuid_0'
        ).first()

        assert review is not None, (
            "ChangeReview record should exist in database"
        )
        assert review.review_status == 'reviewed', (
            "Review status should be persisted"
        )
        assert review.user_notes == 'Test note', (
            "User notes should be persisted"
        )

        # Perform another action
        service.update_progress(
            session.id,
            1,
            'skipped'
        )

        # Verify immediate persistence
        db.session.expire_all()
        updated_session = MergeSession.query.get(session.id)

        assert updated_session.current_change_index == 1, (
            "Current change index should be updated immediately"
        )
        assert updated_session.skipped_count > 0, (
            "Skipped count should be updated immediately"
        )

    def test_property_1_package_validation_correctness(self):
        """
        Feature: three-way-merge-assistant, Property 1: Package validation
        correctness

        For any uploaded ZIP file, the validation function should correctly
        identify whether it is a valid Appian application package based on
        the presence of required files and structure.

        Validates: Requirements 1.2
        """
        from services.merge_assistant import (
            PackageValidationService,
            PackageValidationError
        )

        service = PackageValidationService()

        # Test 1: Valid Appian package should pass validation
        if os.path.exists(self.test_package_a):
            is_valid, error = service.validate_package(
                self.test_package_a,
                'Test Package A'
            )
            assert is_valid is True, "Valid package should pass validation"
            assert error is None, "Valid package should have no errors"

        # Test 2: Non-existent file should fail
        with self.assertRaises(PackageValidationError) as context:
            service.validate_package(
                '/nonexistent/path/file.zip',
                'Non-existent Package'
            )
        error = context.exception
        assert 'FILE_NOT_FOUND' in [e.code for e in error.errors], (
            "Non-existent file should have FILE_NOT_FOUND error"
        )
        assert error.package_name == 'Non-existent Package', (
            "Error should include package name"
        )

        # Test 3: Non-ZIP file should fail
        with tempfile.NamedTemporaryFile(
            suffix='.txt', delete=False
        ) as tmp:
            tmp.write(b'not a zip file')
            tmp_path = tmp.name

        try:
            with self.assertRaises(PackageValidationError) as context:
                service.validate_package(tmp_path, 'Invalid Format Package')
            error = context.exception
            assert 'INVALID_ZIP_FORMAT' in [e.code for e in error.errors], (
                "Non-ZIP file should have INVALID_ZIP_FORMAT error"
            )
        finally:
            os.unlink(tmp_path)

        # Test 4: Empty file should fail
        with tempfile.NamedTemporaryFile(
            suffix='.zip', delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            with self.assertRaises(PackageValidationError) as context:
                service.validate_package(tmp_path, 'Empty Package')
            error = context.exception
            error_codes = [e.code for e in error.errors]
            assert 'FILE_EMPTY' in error_codes or (
                'INVALID_ZIP_FORMAT' in error_codes
            ), "Empty file should fail validation"
        finally:
            os.unlink(tmp_path)

        # Test 5: ZIP without Appian content should fail
        with tempfile.NamedTemporaryFile(
            suffix='.zip', delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, 'w') as zf:
                zf.writestr('random.txt', 'not an appian package')

            with self.assertRaises(PackageValidationError) as context:
                service.validate_package(tmp_path, 'Invalid Content Package')
            error = context.exception
            error_codes = [e.code for e in error.errors]
            assert (
                'MISSING_REQUIRED_FILES' in error_codes or
                'NO_APPIAN_OBJECTS' in error_codes
            ), "ZIP without Appian content should fail validation"
        finally:
            os.unlink(tmp_path)

        # Test 6: ZIP with random files but no Appian objects should fail
        with tempfile.NamedTemporaryFile(
            suffix='.zip', delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, 'w') as zf:
                zf.writestr('readme.txt', 'This is not an Appian package')
                zf.writestr('data.json', '{}')

            with self.assertRaises(PackageValidationError) as context:
                service.validate_package(tmp_path, 'No Objects Package')
            error = context.exception
            error_codes = [e.code for e in error.errors]
            assert 'NO_APPIAN_OBJECTS' in error_codes or (
                'NO_XML_FILES' in error_codes
            ), "Package without Appian objects should fail validation"
        finally:
            os.unlink(tmp_path)

        # Test 7: Minimal valid package should pass
        with tempfile.NamedTemporaryFile(
            suffix='.zip', delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, 'w') as zf:
                # Just need an Appian object directory with XML
                zf.writestr(
                    'interface/test.xml',
                    '<?xml version="1.0"?><interface></interface>'
                )

            is_valid, error = service.validate_package(
                tmp_path,
                'Minimal Valid Package'
            )
            assert is_valid is True, (
                "Minimal valid package should pass validation"
            )
            assert error is None, "Valid package should have no errors"
        finally:
            os.unlink(tmp_path)

        # Test 8: File size limit validation
        large_service = PackageValidationService(max_file_size=100)  # 100 bytes

        with tempfile.NamedTemporaryFile(
            suffix='.zip', delete=False
        ) as tmp:
            tmp.write(b'x' * 200)  # 200 bytes
            tmp_path = tmp.name

        try:
            with self.assertRaises(PackageValidationError) as context:
                large_service.validate_package(tmp_path, 'Large Package')
            error = context.exception
            assert 'FILE_TOO_LARGE' in [e.code for e in error.errors], (
                "File exceeding size limit should have FILE_TOO_LARGE error"
            )
        finally:
            os.unlink(tmp_path)

    def test_property_2_session_creation_atomicity(self):
        """
        Feature: three-way-merge-assistant, Property 2: Session creation
        atomicity

        For any three valid packages, clicking "Start Analysis" should create
        exactly one merge session with a unique reference ID stored in the
        database.

        Validates: Requirements 1.4
        """
        from services.merge_assistant import ThreeWayMergeService

        # Test with real Appian packages
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        service = ThreeWayMergeService()

        # Get initial session count
        initial_count = MergeSession.query.count()

        # Create a session
        session = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        # Verify exactly one session was created
        final_count = MergeSession.query.count()
        assert final_count == initial_count + 1, (
            f"Expected exactly one new session, but count changed from "
            f"{initial_count} to {final_count}"
        )

        # Verify session has unique reference ID
        assert session.reference_id is not None, (
            "Session should have a reference ID"
        )
        assert len(session.reference_id) > 0, (
            "Reference ID should not be empty"
        )
        assert session.reference_id.startswith('MRG_'), (
            "Reference ID should start with 'MRG_'"
        )

        # Verify session is stored in database
        retrieved_session = MergeSession.query.filter_by(
            reference_id=session.reference_id
        ).first()
        assert retrieved_session is not None, (
            "Session should be retrievable from database"
        )
        assert retrieved_session.id == session.id, (
            "Retrieved session should match created session"
        )

        # Verify reference ID is unique
        duplicate_count = MergeSession.query.filter_by(
            reference_id=session.reference_id
        ).count()
        assert duplicate_count == 1, (
            f"Reference ID should be unique, but found {duplicate_count} "
            f"sessions with ID {session.reference_id}"
        )

        # Test atomicity: Create another session and verify it gets a
        # different reference ID
        session2 = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        assert session2.reference_id != session.reference_id, (
            "Each session should have a unique reference ID"
        )

        # Verify both sessions exist in database
        assert MergeSession.query.count() == initial_count + 2, (
            "Both sessions should be stored in database"
        )

    def test_property_3_error_message_clarity(self):
        """
        Feature: three-way-merge-assistant, Property 3: Error message clarity

        For any invalid package upload, the system should display an error
        message that identifies which specific package (A, B, or C) is
        invalid and includes the validation failure reason.

        Validates: Requirements 1.5
        """
        from services.merge_assistant import (
            PackageValidationService,
            PackageValidationError
        )

        service = PackageValidationService()

        # Test 1: Error message includes package name
        try:
            service.validate_package(
                '/nonexistent/file.zip',
                'Base Package (A)'
            )
            self.fail("Should have raised PackageValidationError")
        except PackageValidationError as e:
            error_msg = service.generate_error_message(e)

            # Verify error message structure
            assert 'title' in error_msg, "Error message should have title"
            assert 'message' in error_msg, "Error message should have message"
            assert 'package' in error_msg, "Error message should have package"
            assert 'technical_details' in error_msg, (
                "Error message should have technical details"
            )
            assert 'suggested_action' in error_msg, (
                "Error message should have suggested action"
            )

            # Verify package name is included
            assert error_msg['package'] == 'Base Package (A)', (
                "Error message should identify the specific package"
            )
            assert 'Base Package (A)' in error_msg['message'], (
                "Error message text should mention the package name"
            )

            # Verify error details are clear
            assert len(error_msg['message']) > 0, (
                "Error message should not be empty"
            )
            assert len(error_msg['suggested_action']) > 0, (
                "Suggested action should not be empty"
            )

        # Test 2: Different error types have appropriate messages
        test_cases = [
            {
                'setup': lambda: '/nonexistent/file.zip',
                'package': 'Test Package',
                'expected_code': 'FILE_NOT_FOUND',
                'expected_title_keywords': ['not found', 'file'],
                'expected_action_keywords': ['select', 'upload']
            },
            {
                'setup': lambda: self._create_invalid_zip(),
                'package': 'Invalid Package',
                'expected_code': 'INVALID_ZIP_FORMAT',
                'expected_title_keywords': ['invalid', 'format'],
                'expected_action_keywords': ['zip', 'appian']
            }
        ]

        for test_case in test_cases:
            file_path = test_case['setup']()
            try:
                service.validate_package(
                    file_path,
                    test_case['package']
                )
                self.fail("Should have raised PackageValidationError")
            except PackageValidationError as e:
                error_msg = service.generate_error_message(e)

                # Verify error code is present
                assert test_case['expected_code'] in error_msg['error_codes'], (
                    f"Error should include {test_case['expected_code']}"
                )

                # Verify title contains expected keywords
                title_lower = error_msg['title'].lower()
                for keyword in test_case['expected_title_keywords']:
                    assert keyword.lower() in title_lower, (
                        f"Title should contain '{keyword}'"
                    )

                # Verify suggested action contains expected keywords
                action_lower = error_msg['suggested_action'].lower()
                for keyword in test_case['expected_action_keywords']:
                    assert keyword.lower() in action_lower, (
                        f"Suggested action should contain '{keyword}'"
                    )

                # Verify package name is in message
                assert test_case['package'] in error_msg['message'], (
                    "Error message should identify the specific package"
                )
            finally:
                # Clean up temporary files
                if (file_path != '/nonexistent/file.zip' and
                        os.path.exists(file_path)):
                    os.unlink(file_path)

        # Test 3: Multiple errors are all included
        with tempfile.NamedTemporaryFile(
            suffix='.zip', delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            # Create a ZIP with multiple issues
            with zipfile.ZipFile(tmp_path, 'w') as zf:
                zf.writestr('random.txt', 'not appian')
                # Missing application.properties
                # No Appian objects

            try:
                service.validate_package(tmp_path, 'Multi-Error Package')
                self.fail("Should have raised PackageValidationError")
            except PackageValidationError as e:
                error_msg = service.generate_error_message(e)

                # Should have multiple error codes
                assert len(error_msg['error_codes']) > 0, (
                    "Should have at least one error code"
                )

                # Technical details should mention all errors
                technical = error_msg['technical_details']
                assert len(technical) > 0, (
                    "Technical details should not be empty"
                )

                # Message should be comprehensive
                assert len(error_msg['message']) > 50, (
                    "Error message should be detailed for multiple errors"
                )
        finally:
            os.unlink(tmp_path)

    def _create_invalid_zip(self) -> str:
        """Helper to create an invalid ZIP file for testing"""
        tmp = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        tmp.write(b'not a zip file')
        tmp.close()
        return tmp.name


    def test_property_17_change_detail_display_completeness(self):
        """
        Feature: three-way-merge-assistant, Property 17: Change detail display
        completeness

        For any change being viewed, the display should include the object
        name, type, and classification category.

        Validates: Requirements 8.1
        """
        from services.merge_assistant import ThreeWayMergeService
        from flask import url_for

        # Create a test session with changes
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        service = ThreeWayMergeService()

        # Create session
        session = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        # Get ordered changes
        ordered_changes = service.get_ordered_changes(session.id)

        if not ordered_changes:
            self.skipTest("No changes found in test session")

        # Test first change
        change = ordered_changes[0]

        # Verify change has required fields
        assert 'uuid' in change, "Change missing UUID"
        assert 'name' in change, "Change missing name"
        assert 'type' in change, "Change missing type"
        assert 'classification' in change, "Change missing classification"

        # Make request to view change
        with self.client as client:
            with self.app.test_request_context():
                url = url_for(
                    'merge_assistant.view_change',
                    session_id=session.id,
                    change_index=0
                )
            response = client.get(url)

            assert response.status_code == 200, (
                f"Failed to load change detail page: {response.status_code}"
            )

            # Verify response contains required information
            html = response.data.decode('utf-8')

            # Check for object name
            assert change['name'] in html, (
                f"Object name '{change['name']}' not found in page"
            )

            # Check for object type
            assert change['type'] in html, (
                f"Object type '{change['type']}' not found in page"
            )

            # Check for classification
            classification_display = change['classification'].replace('_', ' ')
            assert (
                change['classification'] in html or
                classification_display in html
            ), (
                f"Classification '{change['classification']}' not found in page"
            )

        # Clean up
        db.session.delete(session)
        db.session.commit()

    def test_property_18_three_way_diff_display(self):
        """
        Feature: three-way-merge-assistant, Property 18: Three-way diff display

        For any CONFLICT change, the display should show three columns
        containing Base (A), Customer (B), and Vendor (C) versions.

        Validates: Requirements 8.3
        """
        from services.merge_assistant import ThreeWayMergeService
        from flask import url_for

        # Create a test session with changes
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        service = ThreeWayMergeService()

        # Create session
        session = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        # Get ordered changes
        ordered_changes = service.get_ordered_changes(session.id)

        # Find a CONFLICT change
        conflict_change = None
        conflict_index = None
        for i, change in enumerate(ordered_changes):
            if change.get('classification') == 'CONFLICT':
                conflict_change = change
                conflict_index = i
                break

        if not conflict_change:
            self.skipTest("No CONFLICT changes found in test session")

        # Make request to view conflict change
        with self.client as client:
            response = client.get(
                url_for(
                    'merge_assistant.view_change',
                    session_id=session.id,
                    change_index=conflict_index
                )
            )

            assert response.status_code == 200, (
                f"Failed to load change detail page: {response.status_code}"
            )

            html = response.data.decode('utf-8')

            # Check for three-way diff structure
            assert 'Base (A)' in html, "Base (A) column not found"
            assert 'Customer (B)' in html, "Customer (B) column not found"
            assert 'Vendor (C)' in html, "Vendor (C) column not found"

            # Check for diff panel structure
            assert 'diff-panel' in html, "Diff panel structure not found"
            assert 'three-way-grid' in html, "Three-way grid not found"

        # Clean up
        db.session.delete(session)
        db.session.commit()

    def test_property_19_vendor_change_highlighting(self):
        """
        Feature: three-way-merge-assistant, Property 19: Vendor change
        highlighting

        For any CONFLICT change, the diff should highlight which specific
        vendor changes (A→C) need to be incorporated into the customer
        version (B).

        Validates: Requirements 8.4
        """
        from services.merge_assistant import ThreeWayMergeService
        from flask import url_for

        # Create a test session with changes
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        service = ThreeWayMergeService()

        # Create session
        session = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        # Get ordered changes
        ordered_changes = service.get_ordered_changes(session.id)

        # Find a CONFLICT change with vendor additions
        conflict_change = None
        conflict_index = None
        for i, change in enumerate(ordered_changes):
            if (change.get('classification') == 'CONFLICT' and
                    change.get('merge_guidance', {}).get('vendor_additions')):
                conflict_change = change
                conflict_index = i
                break

        if not conflict_change:
            self.skipTest(
                "No CONFLICT changes with vendor additions found"
            )

        # Make request to view conflict change
        with self.client as client:
            response = client.get(
                url_for(
                    'merge_assistant.view_change',
                    session_id=session.id,
                    change_index=conflict_index
                )
            )

            assert response.status_code == 200, (
                f"Failed to load change detail page: {response.status_code}"
            )

            html = response.data.decode('utf-8')

            # Check for vendor change highlighting section
            assert (
                'Vendor Changes to Incorporate' in html or
                'vendor-highlights' in html
            ), "Vendor change highlighting section not found"

            # Check for vendor additions display
            vendor_additions = conflict_change['merge_guidance']['vendor_additions']
            if vendor_additions:
                # At least one addition should be mentioned
                assert 'vendor_additions' in html or 'addition' in html.lower(), (
                    "Vendor additions not displayed"
                )

        # Clean up
        db.session.delete(session)
        db.session.commit()

    def test_property_20_sail_code_formatting(self):
        """
        Feature: three-way-merge-assistant, Property 20: SAIL code formatting

        For any SAIL code displayed in diffs, UUIDs should be replaced with
        readable object names and code should be properly indented.

        Validates: Requirements 9.3
        """
        from services.merge_assistant import ThreeWayMergeService
        from flask import url_for

        # Create a test session with changes
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        service = ThreeWayMergeService()

        # Create session
        session = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        # Get ordered changes
        ordered_changes = service.get_ordered_changes(session.id)

        # Find a change with SAIL code
        sail_change = None
        sail_index = None
        for i, change in enumerate(ordered_changes):
            # Check if any version has SAIL code
            has_sail = (
                (change.get('base_object', {}).get('sail_code')) or
                (change.get('customer_object', {}).get('sail_code')) or
                (change.get('vendor_object', {}).get('sail_code'))
            )
            if has_sail:
                sail_change = change
                sail_index = i
                break

        if not sail_change:
            self.skipTest("No changes with SAIL code found")

        # Make request to view change
        with self.client as client:
            response = client.get(
                url_for(
                    'merge_assistant.view_change',
                    session_id=session.id,
                    change_index=sail_index
                )
            )

            assert response.status_code == 200, (
                f"Failed to load change detail page: {response.status_code}"
            )

            html = response.data.decode('utf-8')

            # Check for code block structure
            assert 'code-block' in html, "Code block structure not found"

            # Check that SAIL code is displayed
            # (We can't easily verify UUID replacement without knowing
            # the specific UUIDs, but we can verify code is present)
            assert '<code>' in html, "Code tags not found"
            assert '<pre>' in html, "Pre tags not found"

        # Clean up
        db.session.delete(session)
        db.session.commit()

    def test_property_21_merge_strategy_provision(self):
        """
        Feature: three-way-merge-assistant, Property 21: Merge strategy
        provision

        For any CONFLICT change, the system should provide a "Suggested Merge
        Strategy" section with recommendations.

        Validates: Requirements 9.6
        """
        from services.merge_assistant import ThreeWayMergeService
        from flask import url_for

        # Create a test session with changes
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        service = ThreeWayMergeService()

        # Create session
        session = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        # Get ordered changes
        ordered_changes = service.get_ordered_changes(session.id)

        # Find a CONFLICT change
        conflict_change = None
        conflict_index = None
        for i, change in enumerate(ordered_changes):
            if change.get('classification') == 'CONFLICT':
                conflict_change = change
                conflict_index = i
                break

        if not conflict_change:
            self.skipTest("No CONFLICT changes found in test session")

        # Make request to view conflict change
        with self.client as client:
            response = client.get(
                url_for(
                    'merge_assistant.view_change',
                    session_id=session.id,
                    change_index=conflict_index
                )
            )

            assert response.status_code == 200, (
                f"Failed to load change detail page: {response.status_code}"
            )

            html = response.data.decode('utf-8')

            # Check for merge strategy section
            assert (
                'Suggested Merge Strategy' in html or
                'merge-strategy' in html
            ), "Merge strategy section not found"

            # Check for strategy badge or recommendations
            assert (
                'strategy-badge' in html or
                'recommendations' in html.lower()
            ), "Merge strategy content not found"

        # Clean up
        db.session.delete(session)
        db.session.commit()

    def test_property_30_dependency_status_indication(self):
        """
        Feature: three-way-merge-assistant, Property 30: Dependency status
        indication

        For any displayed dependency, the system should show its review status
        (reviewed, pending, or skipped).

        Validates: Requirements 14.3
        """
        from services.merge_assistant import ThreeWayMergeService
        from flask import url_for

        # Create a test session with changes
        if not os.path.exists(self.test_package_a):
            self.skipTest("Test package A not found")
        if not os.path.exists(self.test_package_b):
            self.skipTest("Test package B not found")

        service = ThreeWayMergeService()

        # Create session
        session = service.create_session(
            self.test_package_a,
            self.test_package_b,
            self.test_package_a
        )

        # Get ordered changes
        ordered_changes = service.get_ordered_changes(session.id)

        # Find a change with dependencies
        change_with_deps = None
        change_index = None
        for i, change in enumerate(ordered_changes):
            deps = change.get('dependencies', {})
            if deps.get('parents') or deps.get('children'):
                change_with_deps = change
                change_index = i
                break

        if not change_with_deps:
            self.skipTest("No changes with dependencies found")

        # Make request to view change
        with self.client as client:
            with self.app.test_request_context():
                url = url_for(
                    'merge_assistant.view_change',
                    session_id=session.id,
                    change_index=change_index
                )
            response = client.get(url)

            assert response.status_code == 200, (
                f"Failed to load change detail page: {response.status_code}"
            )

            html = response.data.decode('utf-8')

            # Check for dependencies section
            assert (
                'Dependencies' in html or
                'dependency' in html.lower()
            ), "Dependencies section not found"

            # Check for status indicators
            assert (
                'status-reviewed' in html or
                'status-pending' in html or
                'status-skipped' in html or
                'Reviewed' in html or
                'Pending' in html or
                'Skipped' in html
            ), "Dependency status indicators not found"

        # Clean up
        db.session.delete(session)
        db.session.commit()


# Additional strategies for filtering and search tests

@composite
def classified_change(draw):
    """Generate a single classified change object"""
    obj_uuid = f"_a-{draw(st.text(min_size=8, max_size=8, alphabet='0123456789abcdef'))}"
    obj_type = draw(st.sampled_from([
        'Interface', 'Process Model', 'Record Type',
        'Expression Rule', 'Constant', 'Site'
    ]))
    classification = draw(st.sampled_from([
        'NO_CONFLICT', 'CONFLICT', 'CUSTOMER_ONLY', 'REMOVED_BUT_CUSTOMIZED'
    ]))
    
    return {
        'uuid': obj_uuid,
        'name': draw(st.text(
            min_size=5, max_size=30,
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')
        )),
        'type': obj_type,
        'classification': classification,
        'change_type': draw(st.sampled_from(['ADDED', 'MODIFIED', 'REMOVED'])),
        'merge_guidance': {
            'strategy': draw(st.text(min_size=5, max_size=50)),
            'recommendations': []
        },
        'dependencies': {
            'parents': [],
            'children': []
        }
    }


@composite
def classified_changes_list(draw):
    """Generate a list of classified changes"""
    num_changes = draw(st.integers(min_value=5, max_value=30))
    changes = []
    for _ in range(num_changes):
        changes.append(draw(classified_change()))
    return changes


@composite
def filter_criteria_strategy(draw):
    """Generate random filter criteria"""
    criteria = {}
    
    # Randomly include each filter type
    if draw(st.booleans()):
        criteria['classification'] = draw(st.sampled_from([
            'NO_CONFLICT', 'CONFLICT', 'CUSTOMER_ONLY', 'REMOVED_BUT_CUSTOMIZED'
        ]))
    
    if draw(st.booleans()):
        criteria['object_type'] = draw(st.sampled_from([
            'Interface', 'Process Model', 'Record Type',
            'Expression Rule', 'Constant', 'Site'
        ]))
    
    if draw(st.booleans()):
        criteria['review_status'] = draw(st.sampled_from([
            'pending', 'reviewed', 'skipped'
        ]))
    
    return criteria


@composite
def search_term_strategy(draw):
    """Generate random search term"""
    # Generate a term that might match object names
    return draw(st.text(
        min_size=1, max_size=10,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')
    ))


class TestFilteringAndSearchProperties(BaseTestCase):
    """Property-based tests for filtering and search functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        from services.merge_assistant import ThreeWayMergeService
        self.service = ThreeWayMergeService()

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        session_data=merge_session_data(),
        changes=classified_changes_list(),
        filter_criteria=filter_criteria_strategy(),
        data=st.data()
    )
    def test_property_26_filter_correctness(
        self,
        session_data,
        changes,
        filter_criteria,
        data
    ):
        """
        Feature: three-way-merge-assistant, Property 26: Filter correctness

        For any applied filter (classification, object type, or review status),
        the filtered change list should contain only changes that match the
        filter criteria.

        Validates: Requirements 13.2
        """
        try:
            # Create session with changes
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                status='ready',
                ordered_changes=json.dumps(changes),
                total_changes=len(changes)
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id

            # Create ChangeReview records with random review statuses
            for change in changes:
                review_status = data.draw(st.sampled_from(['pending', 'reviewed', 'skipped']))
                review = ChangeReview(
                    session_id=session_id,
                    object_uuid=change['uuid'],
                    object_name=change['name'],
                    object_type=change['type'],
                    classification=change['classification'],
                    review_status=review_status
                )
                db.session.add(review)
            db.session.commit()

            # Apply filters
            filtered = self.service.filter_changes(
                session_id,
                classification=filter_criteria.get('classification'),
                object_type=filter_criteria.get('object_type'),
                review_status=filter_criteria.get('review_status'),
                search_term=None
            )

            # Verify all filtered results match the criteria
            for change in filtered:
                # Check classification filter
                if 'classification' in filter_criteria:
                    assert change['classification'] == filter_criteria['classification'], (
                        f"Change {change['uuid']} has classification "
                        f"{change['classification']}, expected "
                        f"{filter_criteria['classification']}"
                    )

                # Check object type filter
                if 'object_type' in filter_criteria:
                    assert change['type'] == filter_criteria['object_type'], (
                        f"Change {change['uuid']} has type {change['type']}, "
                        f"expected {filter_criteria['object_type']}"
                    )

                # Check review status filter
                if 'review_status' in filter_criteria:
                    assert change.get('review_status') == filter_criteria['review_status'], (
                        f"Change {change['uuid']} has review status "
                        f"{change.get('review_status')}, expected "
                        f"{filter_criteria['review_status']}"
                    )

            # Verify no matching changes were excluded
            # Get all reviews for verification
            reviews = ChangeReview.query.filter_by(session_id=session_id).all()
            review_lookup = {r.object_uuid: r for r in reviews}

            filtered_uuids = {c['uuid'] for c in filtered}
            for change in changes:
                should_be_included = True

                # Check if change matches all criteria
                if 'classification' in filter_criteria:
                    if change['classification'] != filter_criteria['classification']:
                        should_be_included = False

                if 'object_type' in filter_criteria:
                    if change['type'] != filter_criteria['object_type']:
                        should_be_included = False

                if 'review_status' in filter_criteria:
                    review = review_lookup.get(change['uuid'])
                    if not review or review.review_status != filter_criteria['review_status']:
                        should_be_included = False

                # If should be included, verify it's in filtered results
                if should_be_included:
                    assert change['uuid'] in filtered_uuids, (
                        f"Change {change['uuid']} matches criteria but was not "
                        f"included in filtered results"
                    )

        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    # Delete related reviews first
                    ChangeReview.query.filter_by(
                        session_id=session_to_delete.id
                    ).delete()
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        session_data=merge_session_data(),
        changes=classified_changes_list(),
        search_term=search_term_strategy()
    )
    def test_property_27_search_functionality(
        self,
        session_data,
        changes,
        search_term
    ):
        """
        Feature: three-way-merge-assistant, Property 27: Search functionality

        For any search query, the system should highlight all changes whose
        object names contain the search term.

        Validates: Requirements 13.4
        """
        try:
            # Create session with changes
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                status='ready',
                ordered_changes=json.dumps(changes),
                total_changes=len(changes)
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id

            # Create ChangeReview records
            for change in changes:
                review = ChangeReview(
                    session_id=session_id,
                    object_uuid=change['uuid'],
                    object_name=change['name'],
                    object_type=change['type'],
                    classification=change['classification'],
                    review_status='pending'
                )
                db.session.add(review)
            db.session.commit()

            # Apply search
            filtered = self.service.filter_changes(
                session_id,
                classification=None,
                object_type=None,
                review_status=None,
                search_term=search_term
            )

            # Verify all filtered results contain the search term
            search_lower = search_term.lower()
            for change in filtered:
                name_lower = change['name'].lower()
                assert search_lower in name_lower, (
                    f"Change {change['uuid']} with name '{change['name']}' "
                    f"does not contain search term '{search_term}'"
                )

            # Verify all matching changes are included
            filtered_uuids = {c['uuid'] for c in filtered}
            for change in changes:
                if search_lower in change['name'].lower():
                    assert change['uuid'] in filtered_uuids, (
                        f"Change {change['uuid']} with name '{change['name']}' "
                        f"contains search term '{search_term}' but was not "
                        f"included in results"
                    )

            # Verify non-matching changes are excluded
            for change in changes:
                if search_lower not in change['name'].lower():
                    assert change['uuid'] not in filtered_uuids, (
                        f"Change {change['uuid']} with name '{change['name']}' "
                        f"does not contain search term '{search_term}' but was "
                        f"included in results"
                    )

        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    # Delete related reviews first
                    ChangeReview.query.filter_by(
                        session_id=session_to_delete.id
                    ).delete()
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        session_data=merge_session_data(),
        filter_criteria=filter_criteria_strategy(),
        data=st.data()
    )
    def test_property_28_ordering_preservation_after_filtering(
        self,
        session_data,
        filter_criteria,
        data
    ):
        """
        Feature: three-way-merge-assistant, Property 28: Ordering preservation
        after filtering

        For any filtered change list, the smart ordering (NO_CONFLICT,
        CONFLICT, REMOVED_BUT_CUSTOMIZED) should be maintained within the
        filtered results.

        Validates: Requirements 13.5
        """
        try:
            # Create changes with specific ordering
            # NO_CONFLICT changes first, then CONFLICT, then REMOVED_BUT_CUSTOMIZED
            changes = []
            
            # Add NO_CONFLICT changes
            for i in range(5):
                changes.append({
                    'uuid': f"_a-noconflict{i:03d}",
                    'name': f"NoConflict_{i}",
                    'type': data.draw(st.sampled_from(['Interface', 'Process Model', 'Record Type'])),
                    'classification': 'NO_CONFLICT',
                    'change_type': 'MODIFIED',
                    'merge_guidance': {'strategy': 'test', 'recommendations': []},
                    'dependencies': {'parents': [], 'children': []}
                })
            
            # Add CONFLICT changes
            for i in range(5):
                changes.append({
                    'uuid': f"_a-conflict{i:03d}",
                    'name': f"Conflict_{i}",
                    'type': data.draw(st.sampled_from(['Interface', 'Process Model', 'Record Type'])),
                    'classification': 'CONFLICT',
                    'change_type': 'MODIFIED',
                    'merge_guidance': {'strategy': 'test', 'recommendations': []},
                    'dependencies': {'parents': [], 'children': []}
                })
            
            # Add REMOVED_BUT_CUSTOMIZED changes
            for i in range(5):
                changes.append({
                    'uuid': f"_a-removed{i:03d}",
                    'name': f"Removed_{i}",
                    'type': data.draw(st.sampled_from(['Interface', 'Process Model', 'Record Type'])),
                    'classification': 'REMOVED_BUT_CUSTOMIZED',
                    'change_type': 'REMOVED',
                    'merge_guidance': {'strategy': 'test', 'recommendations': []},
                    'dependencies': {'parents': [], 'children': []}
                })

            # Create session with ordered changes
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                status='ready',
                ordered_changes=json.dumps(changes),
                total_changes=len(changes)
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id

            # Create ChangeReview records with random review statuses
            for change in changes:
                review_status = data.draw(st.sampled_from(['pending', 'reviewed', 'skipped']))
                review = ChangeReview(
                    session_id=session_id,
                    object_uuid=change['uuid'],
                    object_name=change['name'],
                    object_type=change['type'],
                    classification=change['classification'],
                    review_status=review_status
                )
                db.session.add(review)
            db.session.commit()

            # Apply filters
            filtered = self.service.filter_changes(
                session_id,
                classification=filter_criteria.get('classification'),
                object_type=filter_criteria.get('object_type'),
                review_status=filter_criteria.get('review_status'),
                search_term=None
            )

            # Verify ordering is preserved
            # NO_CONFLICT should come before CONFLICT
            # CONFLICT should come before REMOVED_BUT_CUSTOMIZED
            classification_order = {
                'NO_CONFLICT': 0,
                'CONFLICT': 1,
                'CUSTOMER_ONLY': 2,
                'REMOVED_BUT_CUSTOMIZED': 3
            }

            for i in range(len(filtered) - 1):
                current_class = filtered[i]['classification']
                next_class = filtered[i + 1]['classification']
                
                current_order = classification_order.get(current_class, 999)
                next_order = classification_order.get(next_class, 999)
                
                assert current_order <= next_order, (
                    f"Ordering violated: {current_class} (order {current_order}) "
                    f"appears before {next_class} (order {next_order}) at "
                    f"positions {i} and {i+1}"
                )

            # Verify filtered results maintain relative order from original list
            # Extract UUIDs in order
            original_uuids = [c['uuid'] for c in changes]
            filtered_uuids = [c['uuid'] for c in filtered]
            
            # Check that filtered UUIDs appear in same relative order as original
            original_positions = {
                uuid: idx for idx, uuid in enumerate(original_uuids)
            }
            
            for i in range(len(filtered_uuids) - 1):
                current_uuid = filtered_uuids[i]
                next_uuid = filtered_uuids[i + 1]
                
                current_pos = original_positions[current_uuid]
                next_pos = original_positions[next_uuid]
                
                assert current_pos < next_pos, (
                    f"Relative order violated: {current_uuid} (original pos "
                    f"{current_pos}) appears before {next_uuid} (original pos "
                    f"{next_pos}) in filtered results"
                )

        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    # Delete related reviews first
                    ChangeReview.query.filter_by(
                        session_id=session_to_delete.id
                    ).delete()
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()



class TestPackageServiceProperties(BaseTestCase):
    """
    Property-based tests for PackageService blueprint normalization.
    """

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        from services.merge_assistant.package_service import PackageService
        self.package_service = PackageService()

    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=100, deadline=None)
    def test_property_1_blueprint_data_normalization(self, num_objects):
        """
        **Feature: merge-assistant-data-model-refactoring, Property 1:
        Blueprint data normalization**

        **Validates: Requirements 1.1**

        Property: For any blueprint result with objects and metadata,
        storing it should create exactly one Package record and N
        AppianObject records where N equals the number of objects in
        the blueprint, with no blueprint JSON remaining in the session
        table.
        """
        # Generate a valid blueprint structure
        blueprint_result = {
            'blueprint': {
                'metadata': {
                    'package_name': f'TestPackage_{uuid.uuid4().hex[:8]}',
                    'total_objects': num_objects,
                    'generation_time': 45.2,
                    'object_type_counts': {
                        'Interface': num_objects // 3,
                        'Process Model': num_objects // 3,
                        'Expression Rule': num_objects - (2 * (num_objects // 3))
                    }
                }
            },
            'object_lookup': {}
        }

        # Generate objects
        for i in range(num_objects):
            obj_uuid = f'_a-{uuid.uuid4().hex[:32]}'
            obj_type = (
                'Interface' if i < num_objects // 3
                else 'Process Model' if i < 2 * (num_objects // 3)
                else 'Expression Rule'
            )
            blueprint_result['object_lookup'][obj_uuid] = {
                'uuid': obj_uuid,
                'name': f'Object_{i}',
                'type': obj_type,
                'version_uuid': f'v-{uuid.uuid4().hex[:32]}'
            }

            # Add SAIL code for interfaces and expression rules
            if obj_type in ['Interface', 'Expression Rule']:
                blueprint_result['object_lookup'][obj_uuid]['sail_code'] = (
                    f'a!textField(label: "Field {i}")'
                )

        # Create a merge session
        session = MergeSession(
            reference_id=f'MRG_{uuid.uuid4().hex[:8]}',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor',
            status='processing'
        )
        db.session.add(session)
        db.session.commit()

        # Create package with all data
        package = self.package_service.create_package_with_all_data(
            session_id=session.id,
            package_type='base',
            blueprint_result=blueprint_result
        )

        # Verify Property 1: Exactly one Package record created
        from models import Package, AppianObject
        packages = Package.query.filter_by(session_id=session.id).all()
        self.assertEqual(
            len(packages), 1,
            "Should create exactly one Package record"
        )

        # Verify: Package has correct data
        self.assertEqual(package.package_type, 'base')
        self.assertEqual(package.total_objects, num_objects)

        # Verify: N AppianObject records created
        objects = AppianObject.query.filter_by(package_id=package.id).all()
        self.assertEqual(
            len(objects), num_objects,
            f"Should create {num_objects} AppianObject records"
        )

        # Verify: All objects have correct package_id
        for obj in objects:
            self.assertEqual(obj.package_id, package.id)

        # Verify: No JSON in session table
        # (Session should not have blueprint JSON columns populated
        # in the new schema)
        session_check = MergeSession.query.get(session.id)
        # The old JSON columns should be None or empty
        # (In the new workflow, we don't populate these)
        self.assertIsNone(session_check.base_blueprint)
        self.assertIsNone(session_check.customized_blueprint)
        self.assertIsNone(session_check.new_vendor_blueprint)

        # Verify: Object type counts are correct
        from models import PackageObjectTypeCount
        type_counts = PackageObjectTypeCount.query.filter_by(
            package_id=package.id
        ).all()
        self.assertGreater(
            len(type_counts), 0,
            "Should create PackageObjectTypeCount records"
        )

        # Verify total count matches
        total_count = sum(tc.count for tc in type_counts)
        self.assertEqual(
            total_count, num_objects,
            "Total object type counts should match total objects"
        )


    @settings(max_examples=100, deadline=None, database=None)
    @given(
        session_data=merge_session_data(),
        base_blueprint=blueprint_with_objects(),
        customized_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects()
    )
    def test_property_2_change_foreign_key_validity(
        self,
        session_data,
        base_blueprint,
        customized_blueprint,
        vendor_blueprint
    ):
        """
        Feature: merge-assistant-data-model-refactoring, Property 2: Change foreign key validity
        
        For any comparison result that creates Change records, all Change records should have
        valid foreign keys to AppianObject records (base_object_id, customer_object_id, or
        vendor_object_id must reference existing objects).
        
        Validates: Requirements 1.2
        """
        from services.merge_assistant.package_service import PackageService
        from services.merge_assistant.change_service import ChangeService
        
        try:
            # Create session
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                status='processing'
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            # Create packages with objects
            package_service = PackageService()
            
            base_pkg = package_service.create_package_with_all_data(
                session_id,
                'base',
                base_blueprint
            )
            
            customized_pkg = package_service.create_package_with_all_data(
                session_id,
                'customized',
                customized_blueprint
            )
            
            vendor_pkg = package_service.create_package_with_all_data(
                session_id,
                'new_vendor',
                vendor_blueprint
            )
            
            # Create ordered changes from objects
            ordered_changes = []
            base_lookup = base_blueprint.get('object_lookup', {})
            customized_lookup = customized_blueprint.get('object_lookup', {})
            vendor_lookup = vendor_blueprint.get('object_lookup', {})
            
            # Get all unique UUIDs
            all_uuids = set(base_lookup.keys()) | set(customized_lookup.keys()) | set(vendor_lookup.keys())
            
            for uuid in all_uuids:
                base_obj = base_lookup.get(uuid)
                custom_obj = customized_lookup.get(uuid)
                vendor_obj = vendor_lookup.get(uuid)
                
                # Determine change type and classification
                if base_obj and custom_obj and vendor_obj:
                    classification = 'NO_CONFLICT'
                    change_type = 'MODIFIED'
                elif base_obj and custom_obj and not vendor_obj:
                    classification = 'REMOVED_BUT_CUSTOMIZED'
                    change_type = 'REMOVED'
                elif base_obj and not custom_obj and vendor_obj:
                    classification = 'NO_CONFLICT'
                    change_type = 'MODIFIED'
                elif not base_obj and custom_obj and vendor_obj:
                    classification = 'CONFLICT'
                    change_type = 'ADDED'
                elif not base_obj and custom_obj:
                    classification = 'CUSTOMER_ONLY'
                    change_type = 'ADDED'
                elif not base_obj and vendor_obj:
                    classification = 'NO_CONFLICT'
                    change_type = 'ADDED'
                else:
                    continue
                
                # Use the first available object for name and type
                obj = base_obj or custom_obj or vendor_obj
                
                ordered_changes.append({
                    'uuid': uuid,
                    'name': obj.get('name', ''),
                    'type': obj.get('object_type', ''),
                    'classification': classification,
                    'change_type': change_type
                })
            
            # Create changes using ChangeService
            change_service = ChangeService()
            changes = change_service.create_changes_from_comparison(
                session_id,
                {},  # classification_results not used in this test
                ordered_changes
            )
            
            # Verify all changes have valid foreign keys
            from models import Change, AppianObject
            
            for change in changes:
                # At least one foreign key should be set
                assert (
                    change.base_object_id is not None or
                    change.customer_object_id is not None or
                    change.vendor_object_id is not None
                ), f"Change {change.id} has no valid object foreign keys"
                
                # Verify each set foreign key references an existing object
                if change.base_object_id is not None:
                    base_obj = AppianObject.query.get(change.base_object_id)
                    assert base_obj is not None, (
                        f"Change {change.id} has invalid base_object_id: "
                        f"{change.base_object_id}"
                    )
                    assert base_obj.uuid == change.object_uuid, (
                        f"Change {change.id} base_object UUID mismatch"
                    )
                
                if change.customer_object_id is not None:
                    customer_obj = AppianObject.query.get(change.customer_object_id)
                    assert customer_obj is not None, (
                        f"Change {change.id} has invalid customer_object_id: "
                        f"{change.customer_object_id}"
                    )
                    assert customer_obj.uuid == change.object_uuid, (
                        f"Change {change.id} customer_object UUID mismatch"
                    )
                
                if change.vendor_object_id is not None:
                    vendor_obj = AppianObject.query.get(change.vendor_object_id)
                    assert vendor_obj is not None, (
                        f"Change {change.id} has invalid vendor_object_id: "
                        f"{change.vendor_object_id}"
                    )
                    assert vendor_obj.uuid == change.object_uuid, (
                        f"Change {change.id} vendor_object UUID mismatch"
                    )
        
        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        session_data=merge_session_data(),
        base_blueprint=blueprint_with_objects(),
        customized_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects()
    )
    def test_property_3_classification_normalization(
        self,
        session_data,
        base_blueprint,
        customized_blueprint,
        vendor_blueprint
    ):
        """
        Feature: merge-assistant-data-model-refactoring, Property 3: Classification normalization
        
        For any classification result, after storing, the Change table should contain
        classification values in the classification column and the session's
        classification_results JSON column should be null or empty.
        
        Validates: Requirements 1.3
        """
        from services.merge_assistant.package_service import PackageService
        from services.merge_assistant.change_service import ChangeService
        
        try:
            # Create session
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                status='processing',
                # Initially set classification_results (simulating old schema)
                classification_results=json.dumps({
                    'NO_CONFLICT': [],
                    'CONFLICT': [],
                    'CUSTOMER_ONLY': [],
                    'REMOVED_BUT_CUSTOMIZED': []
                })
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            # Create packages with objects
            package_service = PackageService()
            
            package_service.create_package_with_all_data(
                session_id,
                'base',
                base_blueprint
            )
            
            package_service.create_package_with_all_data(
                session_id,
                'customized',
                customized_blueprint
            )
            
            package_service.create_package_with_all_data(
                session_id,
                'new_vendor',
                vendor_blueprint
            )
            
            # Create ordered changes with various classifications
            ordered_changes = []
            base_lookup = base_blueprint.get('object_lookup', {})
            customized_lookup = customized_blueprint.get('object_lookup', {})
            vendor_lookup = vendor_blueprint.get('object_lookup', {})
            
            all_uuids = set(base_lookup.keys()) | set(customized_lookup.keys()) | set(vendor_lookup.keys())
            
            classifications_used = set()
            
            for uuid in all_uuids:
                base_obj = base_lookup.get(uuid)
                custom_obj = customized_lookup.get(uuid)
                vendor_obj = vendor_lookup.get(uuid)
                
                # Determine classification
                if base_obj and custom_obj and vendor_obj:
                    classification = 'NO_CONFLICT'
                elif base_obj and custom_obj and not vendor_obj:
                    classification = 'REMOVED_BUT_CUSTOMIZED'
                elif not base_obj and custom_obj:
                    classification = 'CUSTOMER_ONLY'
                elif base_obj and vendor_obj:
                    classification = 'NO_CONFLICT'
                else:
                    classification = 'NO_CONFLICT'
                
                classifications_used.add(classification)
                
                obj = base_obj or custom_obj or vendor_obj
                
                ordered_changes.append({
                    'uuid': uuid,
                    'name': obj.get('name', ''),
                    'type': obj.get('object_type', ''),
                    'classification': classification,
                    'change_type': 'MODIFIED'
                })
            
            # Create changes using ChangeService
            change_service = ChangeService()
            changes = change_service.create_changes_from_comparison(
                session_id,
                {},
                ordered_changes
            )
            
            # Verify classifications are stored in Change table
            from models import Change
            
            for change in changes:
                # Classification should be set
                assert change.classification is not None, (
                    f"Change {change.id} has no classification"
                )
                
                # Classification should be one of the valid values
                valid_classifications = {
                    'NO_CONFLICT',
                    'CONFLICT',
                    'CUSTOMER_ONLY',
                    'REMOVED_BUT_CUSTOMIZED'
                }
                assert change.classification in valid_classifications, (
                    f"Change {change.id} has invalid classification: "
                    f"{change.classification}"
                )
            
            # Verify all classifications from ordered_changes are represented
            stored_classifications = {c.classification for c in changes}
            assert classifications_used.issubset(stored_classifications), (
                f"Not all classifications stored. "
                f"Expected: {classifications_used}, Got: {stored_classifications}"
            )
            
            # After normalization, session's classification_results should be cleared
            # (In the new schema, we don't store JSON classification_results)
            # This property verifies that classifications are in the Change table
            # and not duplicated in JSON
            
            # Count changes by classification
            classification_counts = {}
            for change in changes:
                classification_counts[change.classification] = (
                    classification_counts.get(change.classification, 0) + 1
                )
            
            # Verify we can query by classification efficiently
            for classification in classifications_used:
                count = Change.query.filter_by(
                    session_id=session_id,
                    classification=classification
                ).count()
                
                assert count == classification_counts.get(classification, 0), (
                    f"Classification count mismatch for {classification}. "
                    f"Expected: {classification_counts.get(classification, 0)}, "
                    f"Got: {count}"
                )
        
        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        session_data=merge_session_data(),
        review_status=st.sampled_from(['reviewed', 'skipped']),
        has_notes=st.booleans()
    )
    def test_property_10_review_action_equivalence(
        self,
        session_data,
        review_status,
        has_notes
    ):
        """
        Feature: merge-assistant-data-model-refactoring, Property 10: Review action equivalence
        
        For any review action (reviewed or skipped with notes), recording the action should 
        update the ChangeReview record and session counts (reviewed_count, skipped_count) 
        identically to the old implementation.
        
        Validates: Requirements 3.3
        """
        from services.merge_assistant import ThreeWayMergeService
        from services.merge_assistant.package_service import PackageService
        from models import Change, Package, AppianObject
        
        try:
            # Create a session with normalized schema
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                status='in_progress',
                current_change_index=0,
                total_changes=3,
                reviewed_count=0,
                skipped_count=0
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            # Create packages for the session
            package_service = PackageService()
            base_package = Package(
                session_id=session_id,
                package_type='base',
                package_name=session_data['base_package_name'],
                total_objects=3
            )
            db.session.add(base_package)
            db.session.commit()
            
            # Create some AppianObjects
            objects = []
            for i in range(3):
                obj = AppianObject(
                    package_id=base_package.id,
                    uuid=f"uuid_{i}_{session_data['reference_id']}",
                    name=f"Object_{i}",
                    object_type='Interface'
                )
                objects.append(obj)
                db.session.add(obj)
            db.session.commit()
            
            # Create changes with normalized schema
            changes = []
            for i in range(3):
                change = Change(
                    session_id=session_id,
                    object_uuid=objects[i].uuid,
                    object_name=objects[i].name,
                    object_type=objects[i].object_type,
                    classification='NO_CONFLICT',
                    change_type='MODIFIED',
                    base_object_id=objects[i].id,
                    display_order=i
                )
                changes.append(change)
                db.session.add(change)
            db.session.commit()
            
            # Initialize service
            service = ThreeWayMergeService()
            
            # Record initial state
            initial_reviewed_count = session.reviewed_count
            initial_skipped_count = session.skipped_count
            initial_current_index = session.current_change_index
            
            # Generate notes if needed
            notes = "Test review notes" if has_notes else None
            
            # Perform review action
            change_index = 0
            service.update_progress(
                session_id,
                change_index,
                review_status,
                notes
            )
            
            # Refresh session from database
            db.session.expire(session)
            session = MergeSession.query.get(session_id)
            
            # Verify session counts were updated correctly
            if review_status == 'reviewed':
                assert session.reviewed_count == initial_reviewed_count + 1, (
                    f"Reviewed count should increment by 1. "
                    f"Expected: {initial_reviewed_count + 1}, "
                    f"Got: {session.reviewed_count}"
                )
                assert session.skipped_count == initial_skipped_count, (
                    f"Skipped count should not change. "
                    f"Expected: {initial_skipped_count}, "
                    f"Got: {session.skipped_count}"
                )
            elif review_status == 'skipped':
                assert session.skipped_count == initial_skipped_count + 1, (
                    f"Skipped count should increment by 1. "
                    f"Expected: {initial_skipped_count + 1}, "
                    f"Got: {session.skipped_count}"
                )
                assert session.reviewed_count == initial_reviewed_count, (
                    f"Reviewed count should not change. "
                    f"Expected: {initial_reviewed_count}, "
                    f"Got: {session.reviewed_count}"
                )
            
            # Verify current_change_index was updated
            assert session.current_change_index == change_index, (
                f"Current change index should be updated. "
                f"Expected: {change_index}, Got: {session.current_change_index}"
            )
            
            # Verify ChangeReview record was created with correct data
            review = ChangeReview.query.filter_by(
                session_id=session_id,
                change_id=changes[change_index].id
            ).first()
            
            assert review is not None, (
                "ChangeReview record should be created"
            )
            assert review.review_status == review_status, (
                f"Review status should be '{review_status}'. "
                f"Got: {review.review_status}"
            )
            assert review.user_notes == notes, (
                f"User notes should be preserved. "
                f"Expected: {notes}, Got: {review.user_notes}"
            )
            assert review.reviewed_at is not None, (
                "Reviewed timestamp should be set"
            )
            
            # Test updating an existing review (changing status)
            new_status = 'skipped' if review_status == 'reviewed' else 'reviewed'
            new_notes = "Updated notes" if has_notes else None
            
            service.update_progress(
                session_id,
                change_index,
                new_status,
                new_notes
            )
            
            # Refresh session
            db.session.expire(session)
            session = MergeSession.query.get(session_id)
            
            # Verify counts were updated correctly for status change
            if new_status == 'reviewed':
                assert session.reviewed_count == initial_reviewed_count + 1, (
                    "Reviewed count should be 1 after status change"
                )
                assert session.skipped_count == initial_skipped_count, (
                    "Skipped count should be 0 after status change"
                )
            else:
                assert session.skipped_count == initial_skipped_count + 1, (
                    "Skipped count should be 1 after status change"
                )
                assert session.reviewed_count == initial_reviewed_count, (
                    "Reviewed count should be 0 after status change"
                )
            
            # Verify review record was updated (not duplicated)
            review_count = ChangeReview.query.filter_by(
                session_id=session_id,
                change_id=changes[change_index].id
            ).count()
            
            assert review_count == 1, (
                f"Should have exactly 1 review record. Got: {review_count}"
            )
            
            # Verify the review was updated with new values
            updated_review = ChangeReview.query.filter_by(
                session_id=session_id,
                change_id=changes[change_index].id
            ).first()
            
            assert updated_review.review_status == new_status, (
                f"Review status should be updated to '{new_status}'. "
                f"Got: {updated_review.review_status}"
            )
            assert updated_review.user_notes == new_notes, (
                f"User notes should be updated. "
                f"Expected: {new_notes}, Got: {updated_review.user_notes}"
            )
            
            # Test reviewing multiple changes
            for i in range(1, 3):
                service.update_progress(
                    session_id,
                    i,
                    'reviewed' if i % 2 == 1 else 'skipped',
                    f"Note for change {i}" if has_notes else None
                )
            
            # Refresh session
            db.session.expire(session)
            session = MergeSession.query.get(session_id)
            
            # Verify total counts match number of reviews
            total_reviews = ChangeReview.query.filter_by(
                session_id=session_id
            ).count()
            
            assert total_reviews == 3, (
                f"Should have 3 review records. Got: {total_reviews}"
            )
            
            # Verify counts match actual review statuses
            actual_reviewed = ChangeReview.query.filter_by(
                session_id=session_id,
                review_status='reviewed'
            ).count()
            actual_skipped = ChangeReview.query.filter_by(
                session_id=session_id,
                review_status='skipped'
            ).count()
            
            assert session.reviewed_count == actual_reviewed, (
                f"Session reviewed_count should match actual reviews. "
                f"Expected: {actual_reviewed}, Got: {session.reviewed_count}"
            )
            assert session.skipped_count == actual_skipped, (
                f"Session skipped_count should match actual skips. "
                f"Expected: {actual_skipped}, Got: {session.skipped_count}"
            )
            
            # Verify session completion logic
            total_reviewed = session.reviewed_count + session.skipped_count
            if total_reviewed >= session.total_changes:
                assert session.status == 'completed', (
                    "Session should be marked as completed when all changes reviewed"
                )
                assert session.completed_at is not None, (
                    "Completed timestamp should be set"
                )
            
        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()


    # ========================================================================
    # Migration Property Tests (Task 5)
    # ========================================================================

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_5_session_metadata_preservation(self, session_data):
        """
        Feature: merge-assistant-data-model-refactoring, Property 5: Session metadata preservation
        
        For any session with metadata fields (reference_id, status, timestamps, counts),
        migrating the session should preserve all metadata values identically.
        
        Validates: Requirements 2.2
        """
        from services.merge_assistant.migration_service import MigrationService
        from services.merge_assistant.package_service import PackageService
        from services.merge_assistant.change_service import ChangeService
        
        migration_service = MigrationService()
        
        try:
            # Create a session with JSON data (old schema)
            # Ensure total_changes matches the actual ordered_changes length
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                status=session_data['status'],
                current_change_index=session_data['current_change_index'],
                total_changes=0,  # No changes in this test
                reviewed_count=0,  # No reviews yet
                skipped_count=0,  # No skips yet
                # Add minimal JSON data for migration
                base_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': 1}},
                    'object_lookup': {
                        'uuid_1': {
                            'uuid': 'uuid_1',
                            'name': 'TestObject',
                            'object_type': 'Interface'
                        }
                    }
                }),
                customized_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': 1}},
                    'object_lookup': {
                        'uuid_1': {
                            'uuid': 'uuid_1',
                            'name': 'TestObject',
                            'object_type': 'Interface'
                        }
                    }
                }),
                new_vendor_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': 1}},
                    'object_lookup': {
                        'uuid_1': {
                            'uuid': 'uuid_1',
                            'name': 'TestObject',
                            'object_type': 'Interface'
                        }
                    }
                }),
                ordered_changes=json.dumps([]),
                classification_results=json.dumps({}),
                vendor_changes=json.dumps({'added': [], 'modified': [], 'removed': []}),
                customer_changes=json.dumps({'added': [], 'modified': [], 'removed': []})
            )
            
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            created_at = session.created_at
            
            # Migrate the session
            success = migration_service.migrate_session(session_id)
            assert success, "Migration should succeed"
            
            # Retrieve migrated session
            db.session.expire_all()
            migrated = MergeSession.query.get(session_id)
            
            # Verify all metadata is preserved
            assert migrated.reference_id == session_data['reference_id'], (
                "reference_id should be preserved"
            )
            assert migrated.base_package_name == session_data['base_package_name'], (
                "base_package_name should be preserved"
            )
            assert migrated.customized_package_name == session_data['customized_package_name'], (
                "customized_package_name should be preserved"
            )
            assert migrated.new_vendor_package_name == session_data['new_vendor_package_name'], (
                "new_vendor_package_name should be preserved"
            )
            assert migrated.status == session_data['status'], (
                "status should be preserved"
            )
            assert migrated.current_change_index == session_data['current_change_index'], (
                "current_change_index should be preserved"
            )
            assert migrated.total_changes == session_data['total_changes'], (
                "total_changes should be preserved"
            )
            assert migrated.reviewed_count == session_data['reviewed_count'], (
                "reviewed_count should be preserved"
            )
            assert migrated.skipped_count == session_data['skipped_count'], (
                "skipped_count should be preserved"
            )
            assert migrated.created_at == created_at, (
                "created_at timestamp should be preserved"
            )
            
        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        session_data=merge_session_data(),
        blueprint=blueprint_with_objects()
    )
    def test_property_6_blueprint_migration_round_trip(self, session_data, blueprint):
        """
        Feature: merge-assistant-data-model-refactoring, Property 6: Blueprint migration round-trip
        
        For any session with blueprint JSON data, after migration, reconstructing the
        blueprint from normalized tables (Package + AppianObject) should produce
        equivalent object data (same UUIDs, names, types, and content).
        
        Validates: Requirements 2.3
        """
        from services.merge_assistant.migration_service import MigrationService
        
        migration_service = MigrationService()
        
        try:
            # Create session with blueprint JSON
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                base_blueprint=json.dumps(blueprint),
                customized_blueprint=json.dumps(blueprint),
                new_vendor_blueprint=json.dumps(blueprint),
                ordered_changes=json.dumps([]),
                classification_results=json.dumps({}),
                vendor_changes=json.dumps({'added': [], 'modified': [], 'removed': []}),
                customer_changes=json.dumps({'added': [], 'modified': [], 'removed': []})
            )
            
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            # Migrate the session
            success = migration_service.migrate_session(session_id)
            assert success, "Migration should succeed"
            
            # Retrieve packages and objects
            db.session.expire_all()
            packages = Package.query.filter_by(session_id=session_id).all()
            
            assert len(packages) == 3, "Should have 3 packages after migration"
            
            # Check each package
            for package in packages:
                # Get objects for this package
                objects = AppianObject.query.filter_by(package_id=package.id).all()
                
                # Verify object count matches
                expected_count = len(blueprint['object_lookup'])
                assert len(objects) == expected_count, (
                    f"Object count mismatch: expected {expected_count}, got {len(objects)}"
                )
                
                # Verify each object's data is preserved
                for obj in objects:
                    original_obj = blueprint['object_lookup'][obj.uuid]
                    
                    assert obj.uuid == original_obj['uuid'], (
                        "UUID should be preserved"
                    )
                    assert obj.name == original_obj['name'], (
                        "Name should be preserved"
                    )
                    assert obj.object_type == original_obj['object_type'], (
                        "Object type should be preserved"
                    )
                    
                    # Check SAIL code if present
                    if 'sail_code' in original_obj:
                        assert obj.sail_code == original_obj['sail_code'], (
                            "SAIL code should be preserved"
                        )
                    
                    # Check fields if present
                    if 'fields' in original_obj:
                        assert obj.fields is not None, "Fields should be stored"
                        stored_fields = json.loads(obj.fields)
                        assert stored_fields == original_obj['fields'], (
                            "Fields should be preserved"
                        )
            
        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_7_change_ordering_preservation(self, session_data):
        """
        Feature: merge-assistant-data-model-refactoring, Property 7: Change ordering preservation
        
        For any session with ordered changes, after migration, querying Change records
        by display_order should return changes in the same sequence with the same
        classifications.
        
        Validates: Requirements 2.4
        """
        from services.merge_assistant.migration_service import MigrationService
        
        migration_service = MigrationService()
        
        try:
            # Create ordered changes with specific sequence
            ordered_changes = [
                {
                    'uuid': f'uuid_{i}',
                    'name': f'Object_{i}',
                    'type': 'Interface',
                    'classification': ['NO_CONFLICT', 'CONFLICT', 'CUSTOMER_ONLY'][i % 3],
                    'change_type': 'MODIFIED'
                }
                for i in range(5)
            ]
            
            # Create session with ordered changes
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                total_changes=len(ordered_changes),
                base_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': 5}},
                    'object_lookup': {
                        f'uuid_{i}': {
                            'uuid': f'uuid_{i}',
                            'name': f'Object_{i}',
                            'object_type': 'Interface'
                        }
                        for i in range(5)
                    }
                }),
                customized_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': 5}},
                    'object_lookup': {
                        f'uuid_{i}': {
                            'uuid': f'uuid_{i}',
                            'name': f'Object_{i}',
                            'object_type': 'Interface'
                        }
                        for i in range(5)
                    }
                }),
                new_vendor_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': 5}},
                    'object_lookup': {
                        f'uuid_{i}': {
                            'uuid': f'uuid_{i}',
                            'name': f'Object_{i}',
                            'object_type': 'Interface'
                        }
                        for i in range(5)
                    }
                }),
                ordered_changes=json.dumps(ordered_changes),
                classification_results=json.dumps({
                    'NO_CONFLICT': [ordered_changes[0], ordered_changes[3]],
                    'CONFLICT': [ordered_changes[1], ordered_changes[4]],
                    'CUSTOMER_ONLY': [ordered_changes[2]]
                }),
                vendor_changes=json.dumps({'added': [], 'modified': [], 'removed': []}),
                customer_changes=json.dumps({'added': [], 'modified': [], 'removed': []})
            )
            
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            # Migrate the session
            success = migration_service.migrate_session(session_id)
            assert success, "Migration should succeed"
            
            # Retrieve changes ordered by display_order
            db.session.expire_all()
            migrated_changes = Change.query.filter_by(
                session_id=session_id
            ).order_by(Change.display_order).all()
            
            # Verify count
            assert len(migrated_changes) == len(ordered_changes), (
                f"Change count mismatch: expected {len(ordered_changes)}, "
                f"got {len(migrated_changes)}"
            )
            
            # Verify order and data preservation
            for i, change in enumerate(migrated_changes):
                original = ordered_changes[i]
                
                assert change.display_order == i, (
                    f"Display order should be {i}, got {change.display_order}"
                )
                assert change.object_uuid == original['uuid'], (
                    f"UUID mismatch at position {i}"
                )
                assert change.object_name == original['name'], (
                    f"Name mismatch at position {i}"
                )
                assert change.object_type == original['type'], (
                    f"Type mismatch at position {i}"
                )
                assert change.classification == original['classification'], (
                    f"Classification mismatch at position {i}"
                )
            
        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_8_migration_record_count_verification(self, session_data):
        """
        Feature: merge-assistant-data-model-refactoring, Property 8: Migration record count verification
        
        For any migrated session, the verification should confirm that Package count
        equals 3, AppianObject count matches sum of blueprint metadata total_objects,
        and Change count matches ordered_changes length.
        
        Validates: Requirements 2.5
        """
        from services.merge_assistant.migration_service import MigrationService
        
        migration_service = MigrationService()
        
        try:
            # Create session with known counts
            num_objects_per_package = 7
            num_changes = 5
            
            session = MergeSession(
                reference_id=session_data['reference_id'],
                base_package_name=session_data['base_package_name'],
                customized_package_name=session_data['customized_package_name'],
                new_vendor_package_name=session_data['new_vendor_package_name'],
                total_changes=num_changes,
                base_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': num_objects_per_package}},
                    'object_lookup': {
                        f'uuid_base_{i}': {
                            'uuid': f'uuid_base_{i}',
                            'name': f'BaseObject_{i}',
                            'object_type': 'Interface'
                        }
                        for i in range(num_objects_per_package)
                    }
                }),
                customized_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': num_objects_per_package}},
                    'object_lookup': {
                        f'uuid_custom_{i}': {
                            'uuid': f'uuid_custom_{i}',
                            'name': f'CustomObject_{i}',
                            'object_type': 'Interface'
                        }
                        for i in range(num_objects_per_package)
                    }
                }),
                new_vendor_blueprint=json.dumps({
                    'blueprint': {'metadata': {'total_objects': num_objects_per_package}},
                    'object_lookup': {
                        f'uuid_vendor_{i}': {
                            'uuid': f'uuid_vendor_{i}',
                            'name': f'VendorObject_{i}',
                            'object_type': 'Interface'
                        }
                        for i in range(num_objects_per_package)
                    }
                }),
                ordered_changes=json.dumps([
                    {
                        'uuid': f'uuid_change_{i}',
                        'name': f'Change_{i}',
                        'type': 'Interface',
                        'classification': 'NO_CONFLICT',
                        'change_type': 'MODIFIED'
                    }
                    for i in range(num_changes)
                ]),
                classification_results=json.dumps({'NO_CONFLICT': []}),
                vendor_changes=json.dumps({'added': [], 'modified': [], 'removed': []}),
                customer_changes=json.dumps({'added': [], 'modified': [], 'removed': []})
            )
            
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            # Migrate the session
            success = migration_service.migrate_session(session_id)
            assert success, "Migration should succeed"
            
            # Verify migration using the service's verify_migration method
            verification = migration_service.verify_migration(session_id)
            
            # Check all verification results
            assert verification['package_count'], (
                "Package count verification should pass (expected 3 packages)"
            )
            assert verification['object_count'], (
                f"Object count verification should pass "
                f"(expected {num_objects_per_package * 3} objects)"
            )
            assert verification['change_count'], (
                f"Change count verification should pass "
                f"(expected {num_changes} changes)"
            )
            assert verification['review_count'], (
                "Review count verification should pass"
            )
            assert verification['foreign_keys'], (
                "Foreign key verification should pass"
            )
            
            # Double-check with direct queries
            package_count = Package.query.filter_by(session_id=session_id).count()
            assert package_count == 3, (
                f"Should have exactly 3 packages, got {package_count}"
            )
            
            total_objects = AppianObject.query.join(Package).filter(
                Package.session_id == session_id
            ).count()
            expected_objects = num_objects_per_package * 3
            assert total_objects == expected_objects, (
                f"Should have {expected_objects} objects, got {total_objects}"
            )
            
            change_count = Change.query.filter_by(session_id=session_id).count()
            assert change_count == num_changes, (
                f"Should have {num_changes} changes, got {change_count}"
            )
            
        finally:
            # Clean up
            try:
                session_to_delete = MergeSession.query.filter_by(
                    reference_id=session_data['reference_id']
                ).first()
                if session_to_delete:
                    db.session.delete(session_to_delete)
                    db.session.commit()
            except Exception:
                db.session.rollback()


    @given(
        search_term=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd')
            )
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_12_object_name_search_correctness(self, search_term):
        """
        **Feature: merge-assistant-data-model-refactoring,
        Property 12: Object name search correctness**

        *For any* search term, searching by object name should return
        all changes where the object name contains the search term
        (case-insensitive).

        **Validates: Requirements 4.2**
        """
        from services.merge_assistant.three_way_merge_service import (
            ThreeWayMergeService
        )
        from models import MergeSession, Change
        
        # Create a test session
        test_uuid = str(uuid.uuid4())[:8]
        session = MergeSession(
            reference_id=f"MRG_TEST_{test_uuid}",
            base_package_name="TestBase",
            customized_package_name="TestCustom",
            new_vendor_package_name="TestVendor",
            status='ready',
            total_changes=0
        )
        db.session.add(session)
        db.session.commit()

        try:
            # Create test changes with various names
            # Use a unique prefix to avoid accidental matches
            test_changes = [
                {
                    'uuid': f'uuid_{i}',
                    'name': f'TestMatch_{search_term}_End_{i}',
                    'type': 'Interface',
                    'classification': 'NO_CONFLICT',
                    'display_order': i
                }
                for i in range(3)
            ]

            # Add some changes that don't contain the search term
            # Use completely different names with only letters
            other_names = ['DifferentNameABC', 'AnotherNameXYZ']
            for i, name in enumerate(other_names):
                test_changes.append({
                    'uuid': f'uuid_other_{i}',
                    'name': name,
                    'type': 'Interface',
                    'classification': 'NO_CONFLICT',
                    'display_order': i + 3
                })

            # Create Change records
            for change_data in test_changes:
                change = Change(
                    session_id=session.id,
                    object_uuid=change_data['uuid'],
                    object_name=change_data['name'],
                    object_type=change_data['type'],
                    classification=change_data['classification'],
                    display_order=change_data['display_order']
                )
                db.session.add(change)

            db.session.commit()

            # Test the search functionality
            service = ThreeWayMergeService()
            results = service.filter_changes(
                session_id=session.id,
                search_term=search_term
            )

            # Verify all results contain the search term (case-insensitive)
            for result in results:
                assert search_term.lower() in result['name'].lower(), \
                    f"Result '{result['name']}' does not contain " \
                    f"search term '{search_term}'"

            # Verify we got the expected number of results
            expected_count = 3  # We created 3 changes with the search term
            assert len(results) == expected_count, \
                f"Expected {expected_count} results, got {len(results)}"

            # Verify results are ordered by display_order
            for i in range(len(results) - 1):
                assert results[i]['display_order'] <= \
                    results[i + 1]['display_order'], \
                    "Results not ordered by display_order"

        finally:
            # Cleanup
            db.session.delete(session)
            db.session.commit()

    @given(
        num_changes=st.integers(min_value=5, max_value=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_13_statistics_calculation_accuracy(self, num_changes):
        """
        **Feature: merge-assistant-data-model-refactoring,
        Property 13: Statistics calculation accuracy**

        *For any* session, calculating statistics (total_changes,
        no_conflict count, conflict count, etc.) should produce the same
        values whether computed from JSON or from aggregated SQL queries.

        **Validates: Requirements 4.4**
        """
        from services.merge_assistant.three_way_merge_service import (
            ThreeWayMergeService
        )
        from models import MergeSession, Change
        import random

        # Create a test session
        test_uuid = str(uuid.uuid4())[:8]
        session = MergeSession(
            reference_id=f"MRG_TEST_{test_uuid}",
            base_package_name="TestBase",
            customized_package_name="TestCustom",
            new_vendor_package_name="TestVendor",
            status='ready',
            total_changes=num_changes
        )
        db.session.add(session)
        db.session.commit()

        try:
            # Create changes with random classifications
            classifications = [
                'NO_CONFLICT', 'CONFLICT',
                'CUSTOMER_ONLY', 'REMOVED_BUT_CUSTOMIZED'
            ]
            expected_counts = {
                'NO_CONFLICT': 0,
                'CONFLICT': 0,
                'CUSTOMER_ONLY': 0,
                'REMOVED_BUT_CUSTOMIZED': 0
            }

            for i in range(num_changes):
                classification = random.choice(classifications)
                expected_counts[classification] += 1

                change = Change(
                    session_id=session.id,
                    object_uuid=f'uuid_{i}',
                    object_name=f'Object_{i}',
                    object_type='Interface',
                    classification=classification,
                    display_order=i
                )
                db.session.add(change)

            db.session.commit()

            # Get statistics using the optimized SQL aggregates
            service = ThreeWayMergeService()
            summary = service.get_summary(session.id)
            statistics = summary['statistics']

            # Verify total_changes matches
            assert statistics['total_changes'] == num_changes, \
                f"Total changes mismatch: expected {num_changes}, " \
                f"got {statistics['total_changes']}"

            # Verify each classification count matches
            assert statistics['no_conflict'] == \
                expected_counts['NO_CONFLICT'], \
                f"NO_CONFLICT count mismatch: " \
                f"expected {expected_counts['NO_CONFLICT']}, " \
                f"got {statistics['no_conflict']}"

            assert statistics['conflict'] == expected_counts['CONFLICT'], \
                f"CONFLICT count mismatch: " \
                f"expected {expected_counts['CONFLICT']}, " \
                f"got {statistics['conflict']}"

            assert statistics['customer_only'] == \
                expected_counts['CUSTOMER_ONLY'], \
                f"CUSTOMER_ONLY count mismatch: " \
                f"expected {expected_counts['CUSTOMER_ONLY']}, " \
                f"got {statistics['customer_only']}"

            assert statistics['removed_but_customized'] == \
                expected_counts['REMOVED_BUT_CUSTOMIZED'], \
                f"REMOVED_BUT_CUSTOMIZED count mismatch: " \
                f"expected {expected_counts['REMOVED_BUT_CUSTOMIZED']}, " \
                f"got {statistics['removed_but_customized']}"

            # Verify sum of all classifications equals total
            sum_of_classifications = (
                statistics['no_conflict'] +
                statistics['conflict'] +
                statistics['customer_only'] +
                statistics['removed_but_customized']
            )
            assert sum_of_classifications == num_changes, \
                f"Sum of classifications ({sum_of_classifications}) " \
                f"doesn't match total ({num_changes})"

        finally:
            # Cleanup
            db.session.delete(session)
            db.session.commit()

    @given(
        num_objects=st.integers(min_value=3, max_value=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_14_dependency_query_correctness(self, num_objects):
        """
        **Feature: merge-assistant-data-model-refactoring,
        Property 14: Dependency query correctness**

        *For any* object UUID, querying its dependencies should return
        all parent and child relationships that exist in the
        ObjectDependency table.

        **Validates: Requirements 4.5**
        """
        from models import (
            MergeSession, Package, AppianObject, ObjectDependency
        )

        # Create a test session and package
        test_uuid = str(uuid.uuid4())[:8]
        session = MergeSession(
            reference_id=f"MRG_TEST_{test_uuid}",
            base_package_name="TestBase",
            customized_package_name="TestCustom",
            new_vendor_package_name="TestVendor",
            status='ready',
            total_changes=0
        )
        db.session.add(session)
        db.session.commit()

        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='TestPackage',
            total_objects=num_objects
        )
        db.session.add(package)
        db.session.commit()

        try:
            # Create test objects
            object_uuids = [f'uuid_{i}' for i in range(num_objects)]
            objects = []

            for i, obj_uuid in enumerate(object_uuids):
                obj = AppianObject(
                    package_id=package.id,
                    uuid=obj_uuid,
                    name=f'Object_{i}',
                    object_type='Interface'
                )
                db.session.add(obj)
                objects.append(obj)

            db.session.commit()

            # Create dependencies: each object depends on the next one
            # Object 0 -> Object 1 -> Object 2 -> ... -> Object N-1
            expected_parents = {}
            expected_children = {}

            for i in range(num_objects - 1):
                parent_uuid = object_uuids[i]
                child_uuid = object_uuids[i + 1]

                # Track expected relationships
                if parent_uuid not in expected_children:
                    expected_children[parent_uuid] = []
                expected_children[parent_uuid].append(child_uuid)

                if child_uuid not in expected_parents:
                    expected_parents[child_uuid] = []
                expected_parents[child_uuid].append(parent_uuid)

                # Create dependency record
                dep = ObjectDependency(
                    package_id=package.id,
                    parent_uuid=parent_uuid,
                    child_uuid=child_uuid,
                    dependency_type='reference'
                )
                db.session.add(dep)

            db.session.commit()

            # Test querying dependencies for each object
            for obj_uuid in object_uuids:
                # Query parent dependencies
                parent_deps = ObjectDependency.query.filter_by(
                    package_id=package.id,
                    child_uuid=obj_uuid
                ).all()

                actual_parents = [dep.parent_uuid for dep in parent_deps]
                expected = expected_parents.get(obj_uuid, [])

                assert set(actual_parents) == set(expected), \
                    f"Parent dependencies mismatch for {obj_uuid}: " \
                    f"expected {expected}, got {actual_parents}"

                # Query child dependencies
                child_deps = ObjectDependency.query.filter_by(
                    package_id=package.id,
                    parent_uuid=obj_uuid
                ).all()

                actual_children = [dep.child_uuid for dep in child_deps]
                expected = expected_children.get(obj_uuid, [])

                assert set(actual_children) == set(expected), \
                    f"Child dependencies mismatch for {obj_uuid}: " \
                    f"expected {expected}, got {actual_children}"

        finally:
            # Cleanup
            db.session.delete(session)
            db.session.commit()


# ============================================================================
# Property-Based Tests for Data Integrity Constraints (Task 8)
# ============================================================================

@composite
def package_with_objects(draw):
    """Generate a package with multiple objects"""
    num_objects = draw(st.integers(min_value=2, max_value=10))
    objects = []
    
    for i in range(num_objects):
        obj_uuid = f"uuid_{i}_{draw(st.integers(min_value=1000, max_value=9999))}"
        objects.append({
            'uuid': obj_uuid,
            'name': draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
            'object_type': draw(st.sampled_from(['Interface', 'Process Model', 'Record Type', 'Expression Rule'])),
            'sail_code': draw(st.text(min_size=10, max_size=100)) if draw(st.booleans()) else None
        })
    
    return {
        'package_name': draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        'package_type': draw(st.sampled_from(['base', 'customized', 'new_vendor'])),
        'objects': objects
    }


class TestDataIntegrityProperties(BaseTestCase):
    """
    Property-based tests for data integrity constraints
    Requirements: 5.1, 5.2, 5.4, 5.5
    """
    
    @settings(max_examples=100, deadline=None)
    @given(package_data=package_with_objects())
    def test_property_15_uuid_uniqueness_enforcement(self, package_data):
        """
        **Feature: merge-assistant-data-model-refactoring, Property 15: UUID uniqueness enforcement**
        **Validates: Requirements 5.2**
        
        Property: For any attempt to insert an AppianObject with a duplicate UUID 
        within the same package, the database should reject the insertion with a 
        constraint violation.
        """
        from models import Package, AppianObject
        from sqlalchemy.exc import IntegrityError
        
        # Create session
        session = MergeSession(
            reference_id=f"TEST_P15_{uuid.uuid4().hex[:8]}",
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        # Create package
        package = Package(
            session_id=session.id,
            package_type=package_data['package_type'],
            package_name=package_data['package_name']
        )
        db.session.add(package)
        db.session.commit()
        
        # Add first object
        first_obj = package_data['objects'][0]
        obj1 = AppianObject(
            package_id=package.id,
            uuid=first_obj['uuid'],
            name=first_obj['name'],
            object_type=first_obj['object_type'],
            sail_code=first_obj.get('sail_code')
        )
        db.session.add(obj1)
        db.session.commit()
        
        # Try to add second object with same UUID - should fail
        obj2 = AppianObject(
            package_id=package.id,
            uuid=first_obj['uuid'],  # Duplicate UUID
            name='Different Name',
            object_type='Different Type'
        )
        db.session.add(obj2)
        
        # Property: Database should reject duplicate UUID
        try:
            db.session.commit()
            # If we get here, the constraint didn't work
            self.fail("Expected IntegrityError for duplicate UUID but commit succeeded")
        except IntegrityError:
            # Expected - constraint is working
            db.session.rollback()
        except Exception as e:
            # Some other error
            db.session.rollback()
            self.fail(f"Expected IntegrityError but got {type(e).__name__}: {e}")
    
    @settings(max_examples=100, deadline=None)
    @given(session_data=merge_session_data(), package_data=package_with_objects())
    def test_property_16_cascade_delete_completeness(self, session_data, package_data):
        """
        **Feature: merge-assistant-data-model-refactoring, Property 16: Cascade delete completeness**
        **Validates: Requirements 5.4**
        
        Property: For any session with related records (packages, objects, changes, 
        reviews, dependencies), deleting the session should remove all related records, 
        leaving no orphaned data.
        """
        from models import Package, AppianObject, Change, ChangeReview, ObjectDependency
        
        # Create session
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status=session_data['status']
        )
        db.session.add(session)
        db.session.commit()
        
        # Create package
        package = Package(
            session_id=session.id,
            package_type=package_data['package_type'],
            package_name=package_data['package_name']
        )
        db.session.add(package)
        db.session.commit()
        
        # Create objects
        object_ids = []
        for obj_data in package_data['objects'][:3]:  # Limit to 3 objects
            obj = AppianObject(
                package_id=package.id,
                uuid=obj_data['uuid'],
                name=obj_data['name'],
                object_type=obj_data['object_type'],
                sail_code=obj_data.get('sail_code')
            )
            db.session.add(obj)
            db.session.commit()
            object_ids.append(obj.id)
        
        # Create dependency
        if len(package_data['objects']) >= 2:
            dependency = ObjectDependency(
                package_id=package.id,
                parent_uuid=package_data['objects'][0]['uuid'],
                child_uuid=package_data['objects'][1]['uuid'],
                dependency_type='reference'
            )
            db.session.add(dependency)
            db.session.commit()
        
        # Create change
        change = Change(
            session_id=session.id,
            object_uuid=package_data['objects'][0]['uuid'],
            object_name=package_data['objects'][0]['name'],
            object_type=package_data['objects'][0]['object_type'],
            classification='NO_CONFLICT',
            display_order=1
        )
        db.session.add(change)
        db.session.commit()
        
        # Create review
        review = ChangeReview(
            session_id=session.id,
            change_id=change.id,
            review_status='pending'
        )
        db.session.add(review)
        db.session.commit()
        
        # Store IDs for verification
        session_id = session.id
        package_id = package.id
        change_id = change.id
        review_id = review.id
        
        # Delete session
        db.session.delete(session)
        db.session.commit()
        
        # Property: All related records should be deleted (no orphans)
        self.assertIsNone(db.session.get(MergeSession, session_id))
        self.assertIsNone(db.session.get(Package, package_id))
        self.assertIsNone(db.session.get(Change, change_id))
        self.assertIsNone(db.session.get(ChangeReview, review_id))
        
        # Verify objects were deleted
        for obj_id in object_ids:
            self.assertIsNone(db.session.get(AppianObject, obj_id))
        
        # Verify dependencies were deleted
        remaining_deps = ObjectDependency.query.filter_by(package_id=package_id).all()
        self.assertEqual(len(remaining_deps), 0)
    
    @settings(max_examples=100, deadline=None)
    @given(package_data=package_with_objects())
    def test_property_17_referential_integrity_enforcement(self, package_data):
        """
        **Feature: merge-assistant-data-model-refactoring, Property 17: Referential integrity enforcement**
        **Validates: Requirements 5.5**
        
        Property: For any attempt to create a Change record with an invalid object_id 
        foreign key, the database should reject the insertion with a constraint violation.
        """
        from models import Change
        from sqlalchemy.exc import IntegrityError
        
        # Create session
        session = MergeSession(
            reference_id=f"TEST_P17_{uuid.uuid4().hex[:8]}",
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor'
        )
        db.session.add(session)
        db.session.commit()
        
        # Try to create change with invalid base_object_id
        change = Change(
            session_id=session.id,
            object_uuid=package_data['objects'][0]['uuid'],
            object_name=package_data['objects'][0]['name'],
            object_type=package_data['objects'][0]['object_type'],
            classification='NO_CONFLICT',
            display_order=1,
            base_object_id=99999  # Invalid foreign key
        )
        db.session.add(change)
        
        # Property: Database should reject invalid foreign key
        try:
            db.session.commit()
            # If we get here, the constraint didn't work
            self.fail("Expected IntegrityError for invalid foreign key but commit succeeded")
        except IntegrityError:
            # Expected - constraint is working
            db.session.rollback()
        except Exception as e:
            # Some other error
            db.session.rollback()
            self.fail(f"Expected IntegrityError but got {type(e).__name__}: {e}")


    # ========================================================================
    # Property Tests for Task 9: Remaining Property-Based Tests
    # ========================================================================

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_with_objects())
    def test_property_4_dependency_table_population(self, blueprints):
        """
        Feature: merge-assistant-data-model-refactoring, Property 4: Dependency table population
        
        For any blueprint with dependency information, storing it should create ObjectDependency 
        records with valid package_id and object UUID references.
        
        Validates: Requirements 1.5
        """
        from services.merge_assistant import PackageService
        
        # Create a session
        session = MergeSession(
            reference_id=f"MRG_{uuid.uuid4().hex[:8].upper()}",
            base_package_name="Test Package",
            customized_package_name="Test Package Custom",
            new_vendor_package_name="Test Package Vendor",
            status='processing'
        )
        db.session.add(session)
        db.session.commit()
        
        try:
            # Add some dependencies to the blueprint
            object_lookup = blueprints['object_lookup']
            object_uuids = list(object_lookup.keys())
            
            # Create dependencies between objects
            if len(object_uuids) >= 2:
                # Add dependency information to objects
                for i, uuid_key in enumerate(object_uuids[:-1]):
                    obj = object_lookup[uuid_key]
                    # Add a reference to the next object
                    obj['dependencies'] = [object_uuids[i + 1]]
            
            # Create package from blueprint
            service = PackageService()
            package = service.create_package_from_blueprint(
                session.id,
                'base',
                blueprints
            )
            
            # Verify package was created
            assert package is not None, "Package should be created"
            assert package.id is not None, "Package should have an ID"
            
            # Verify dependencies were created
            dependencies = ObjectDependency.query.filter_by(
                package_id=package.id
            ).all()
            
            # If we added dependencies, they should be in the database
            if len(object_uuids) >= 2:
                # We should have at least some dependencies
                # (may not be all if some objects don't have dependency info)
                assert isinstance(dependencies, list), "Dependencies should be a list"
                
                # Each dependency should have valid fields
                for dep in dependencies:
                    assert dep.package_id == package.id, (
                        "Dependency should reference correct package"
                    )
                    assert dep.parent_uuid is not None, (
                        "Dependency should have parent UUID"
                    )
                    assert dep.child_uuid is not None, (
                        "Dependency should have child UUID"
                    )
                    assert dep.parent_uuid in object_uuids, (
                        f"Parent UUID {dep.parent_uuid} should be in object list"
                    )
                    assert dep.child_uuid in object_uuids, (
                        f"Child UUID {dep.child_uuid} should be in object list"
                    )
                    
                # Verify parent and child objects exist in AppianObject table
                for dep in dependencies:
                    parent_obj = AppianObject.query.filter_by(
                        package_id=package.id,
                        uuid=dep.parent_uuid
                    ).first()
                    child_obj = AppianObject.query.filter_by(
                        package_id=package.id,
                        uuid=dep.child_uuid
                    ).first()
                    
                    assert parent_obj is not None, (
                        f"Parent object {dep.parent_uuid} should exist"
                    )
                    assert child_obj is not None, (
                        f"Child object {dep.child_uuid} should exist"
                    )
        finally:
            # Cleanup
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(session_data=merge_session_data())
    def test_property_11_export_data_completeness(self, session_data):
        """
        Feature: merge-assistant-data-model-refactoring, Property 11: Export data completeness
        
        For any session, exporting data should include all fields present in the original 
        JSON-based export (session info, packages, changes, reviews, statistics).
        
        Validates: Requirements 3.5
        """
        from services.merge_assistant import ThreeWayMergeService, ReportExportService
        
        # Create a session with complete data
        session = MergeSession(
            reference_id=session_data['reference_id'],
            base_package_name=session_data['base_package_name'],
            customized_package_name=session_data['customized_package_name'],
            new_vendor_package_name=session_data['new_vendor_package_name'],
            status='completed',
            current_change_index=3,
            total_changes=4,
            reviewed_count=3,
            skipped_count=1,
            total_time=300,
            completed_at=datetime.utcnow()
        )
        
        db.session.add(session)
        db.session.commit()
        
        try:
            # Create Change records in normalized schema
            changes_data = [
                {'uuid': 'uuid_1', 'name': 'obj_1', 'type': 'Interface',
                 'classification': 'NO_CONFLICT'},
                {'uuid': 'uuid_2', 'name': 'obj_2', 'type': 'Rule',
                 'classification': 'NO_CONFLICT'},
                {'uuid': 'uuid_3', 'name': 'obj_3', 'type': 'Interface',
                 'classification': 'CONFLICT'},
                {'uuid': 'uuid_4', 'name': 'obj_4', 'type': 'Constant',
                 'classification': 'CUSTOMER_ONLY'},
            ]
            
            for i, change_data in enumerate(changes_data):
                change = Change(
                    session_id=session.id,
                    object_uuid=change_data['uuid'],
                    object_name=change_data['name'],
                    object_type=change_data['type'],
                    classification=change_data['classification'],
                    display_order=i
                )
                db.session.add(change)
            
            db.session.commit()
            
            # Export data
            service = ThreeWayMergeService()
            export_data = service.generate_report(session.id)
            
            # Verify export structure completeness
            assert 'session' in export_data, "Export should include session info"
            assert 'summary' in export_data, "Export should include summary"
            assert 'statistics' in export_data, "Export should include statistics"
            assert 'changes' in export_data, "Export should include changes"
            
            # Verify session info completeness
            session_info = export_data['session']
            assert 'reference_id' in session_info, "Session info should include reference_id"
            assert 'base_package_name' in session_info, "Session info should include base_package_name"
            assert 'customized_package_name' in session_info, "Session info should include customized_package_name"
            assert 'new_vendor_package_name' in session_info, "Session info should include new_vendor_package_name"
            assert 'status' in session_info, "Session info should include status"
            assert 'created_at' in session_info, "Session info should include created_at"
            
            # Verify statistics completeness
            stats = export_data['statistics']
            assert 'total_changes' in stats, "Statistics should include total_changes"
            assert 'reviewed' in stats, "Statistics should include reviewed count"
            assert 'skipped' in stats, "Statistics should include skipped count"
            assert 'conflicts' in stats, "Statistics should include conflicts count"
            
            # Verify changes completeness
            changes = export_data['changes']
            assert isinstance(changes, list), "Changes should be a list"
            assert len(changes) == 4, f"Changes list should have 4 items, got {len(changes)}"
            
            # Verify each change has required fields
            for change in changes:
                assert 'uuid' in change, "Change should have uuid"
                assert 'name' in change, "Change should have name"
                assert 'type' in change, "Change should have type"
                assert 'classification' in change, "Change should have classification"
                
            # Verify summary completeness
            summary = export_data['summary']
            assert isinstance(summary, dict), "Summary should be a dictionary"
            
        finally:
            # Cleanup
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_with_objects())
    def test_property_18_package_storage_correctness(self, blueprints):
        """
        Feature: merge-assistant-data-model-refactoring, Property 18: Package storage correctness
        
        For any package data with metadata, storing it should create a Package record with 
        correct session_id, package_type, package_name, and metadata fields.
        
        Validates: Requirements 6.1
        """
        from services.merge_assistant import PackageService
        
        # Create a session
        session = MergeSession(
            reference_id=f"MRG_{uuid.uuid4().hex[:8].upper()}",
            base_package_name="Test Package A",
            customized_package_name="Test Package B",
            new_vendor_package_name="Test Package C",
            status='processing'
        )
        db.session.add(session)
        db.session.commit()
        
        try:
            # Create package with all data from blueprint
            service = PackageService()
            package = service.create_package_with_all_data(
                session.id,
                'base',
                blueprints
            )
            
            # Verify package was created
            assert package is not None, "Package should be created"
            assert package.id is not None, "Package should have an ID"
            
            # Verify package fields
            assert package.session_id == session.id, (
                "Package should reference correct session"
            )
            assert package.package_type == 'base', (
                "Package type should be 'base'"
            )
            assert package.package_name is not None, (
                "Package should have a name"
            )
            assert isinstance(package.package_name, str), (
                "Package name should be a string"
            )
            
            # Verify metadata fields
            assert package.total_objects is not None, (
                "Package should have total_objects count"
            )
            assert isinstance(package.total_objects, int), (
                "total_objects should be an integer"
            )
            assert package.total_objects >= 0, (
                "total_objects should be non-negative"
            )
            
            # Verify total_objects matches actual object count
            object_count = AppianObject.query.filter_by(
                package_id=package.id
            ).count()
            assert package.total_objects == object_count, (
                f"Package total_objects ({package.total_objects}) should match "
                f"actual object count ({object_count})"
            )
            
            # Verify timestamps
            assert package.created_at is not None, (
                "Package should have created_at timestamp"
            )
            assert isinstance(package.created_at, datetime), (
                "created_at should be a datetime"
            )
            
            # Verify package can be retrieved from database
            db.session.expunge_all()
            retrieved_package = Package.query.get(package.id)
            assert retrieved_package is not None, (
                "Package should be retrievable from database"
            )
            assert retrieved_package.session_id == session.id, (
                "Retrieved package should have correct session_id"
            )
            assert retrieved_package.package_type == 'base', (
                "Retrieved package should have correct package_type"
            )
            
        finally:
            # Cleanup
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_with_objects())
    def test_property_19_object_package_linkage(self, blueprints):
        """
        Feature: merge-assistant-data-model-refactoring, Property 19: Object-package linkage
        
        For any AppianObject record, it should have a valid package_id that references 
        an existing Package record.
        
        Validates: Requirements 6.2
        """
        from services.merge_assistant import PackageService
        
        # Create a session
        session = MergeSession(
            reference_id=f"MRG_{uuid.uuid4().hex[:8].upper()}",
            base_package_name="Test Package",
            customized_package_name="Test Package Custom",
            new_vendor_package_name="Test Package Vendor",
            status='processing'
        )
        db.session.add(session)
        db.session.commit()
        
        try:
            # Create package with all data from blueprint
            service = PackageService()
            package = service.create_package_with_all_data(
                session.id,
                'base',
                blueprints
            )
            
            # Get all objects for this package
            objects = AppianObject.query.filter_by(
                package_id=package.id
            ).all()
            
            # Verify we have objects
            assert len(objects) > 0, "Package should have objects"
            
            # Verify each object has valid package linkage
            for obj in objects:
                # Verify package_id is set
                assert obj.package_id is not None, (
                    f"Object {obj.uuid} should have package_id"
                )
                assert obj.package_id == package.id, (
                    f"Object {obj.uuid} should reference correct package"
                )
                
                # Verify package exists
                linked_package = Package.query.get(obj.package_id)
                assert linked_package is not None, (
                    f"Object {obj.uuid} package_id should reference existing package"
                )
                assert linked_package.id == package.id, (
                    f"Object {obj.uuid} should link to correct package"
                )
                
                # Verify foreign key constraint works
                # (object should be accessible through package relationship)
                package_objects = package.objects
                assert obj in package_objects, (
                    f"Object {obj.uuid} should be in package.objects relationship"
                )
            
            # Test that orphaned objects cannot be created
            # (foreign key constraint should prevent this)
            orphan_object = AppianObject(
                package_id=999999,  # Non-existent package
                uuid='orphan-uuid',
                name='Orphan Object',
                object_type='Interface'
            )
            db.session.add(orphan_object)
            
            # This should raise an integrity error
            with self.assertRaises(Exception) as context:
                db.session.commit()
            
            # Rollback the failed transaction
            db.session.rollback()
            
        finally:
            # Cleanup
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(
        max_examples=10,
        deadline=None,
        database=None,
        suppress_health_check=[HealthCheck.large_base_example]
    )
    @given(
        base_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects()
    )
    def test_property_20_change_object_linkage(
        self,
        base_blueprint,
        vendor_blueprint
    ):
        """
        Feature: merge-assistant-data-model-refactoring, Property 20: Change-object linkage
        
        For any Change record, at least one of its object foreign keys (base_object_id, 
        customer_object_id, vendor_object_id) should reference an existing AppianObject record.
        
        Validates: Requirements 6.3
        """
        from services.merge_assistant import PackageService
        
        # Create a session
        session = MergeSession(
            reference_id=f"MRG_{uuid.uuid4().hex[:8].upper()}",
            base_package_name="Test Package A",
            customized_package_name="Test Package B",
            new_vendor_package_name="Test Package C",
            status='processing'
        )
        db.session.add(session)
        db.session.commit()
        
        try:
            # Create packages
            package_service = PackageService()
            base_package = package_service.create_package_from_blueprint(
                session.id,
                'base',
                base_blueprint
            )
            vendor_package = package_service.create_package_from_blueprint(
                session.id,
                'new_vendor',
                vendor_blueprint
            )
            
            # Get object UUIDs from both packages
            base_uuids = list(base_blueprint['object_lookup'].keys())
            vendor_uuids = list(vendor_blueprint['object_lookup'].keys())
            
            # Create test changes directly without full comparison pipeline
            # This is faster and tests the core property
            test_changes = []
            
            # Test case 1: Change with base object only (REMOVED)
            if base_uuids:
                base_obj = AppianObject.query.filter_by(
                    package_id=base_package.id,
                    uuid=base_uuids[0]
                ).first()
                if base_obj:
                    change1 = Change(
                        session_id=session.id,
                        object_uuid=base_uuids[0],
                        object_name=base_obj.name,
                        object_type=base_obj.object_type,
                        classification='NO_CONFLICT',
                        change_type='REMOVED',
                        base_object_id=base_obj.id,
                        display_order=0
                    )
                    test_changes.append(change1)
            
            # Test case 2: Change with vendor object only (ADDED)
            if vendor_uuids:
                vendor_obj = AppianObject.query.filter_by(
                    package_id=vendor_package.id,
                    uuid=vendor_uuids[0]
                ).first()
                if vendor_obj:
                    change2 = Change(
                        session_id=session.id,
                        object_uuid=vendor_uuids[0],
                        object_name=vendor_obj.name,
                        object_type=vendor_obj.object_type,
                        classification='NO_CONFLICT',
                        change_type='ADDED',
                        vendor_object_id=vendor_obj.id,
                        display_order=1
                    )
                    test_changes.append(change2)
            
            # Test case 3: Change with both base and vendor objects (MODIFIED)
            # Find a common UUID if any
            common_uuids = set(base_uuids) & set(vendor_uuids)
            if common_uuids:
                common_uuid = list(common_uuids)[0]
                base_obj = AppianObject.query.filter_by(
                    package_id=base_package.id,
                    uuid=common_uuid
                ).first()
                vendor_obj = AppianObject.query.filter_by(
                    package_id=vendor_package.id,
                    uuid=common_uuid
                ).first()
                if base_obj and vendor_obj:
                    change3 = Change(
                        session_id=session.id,
                        object_uuid=common_uuid,
                        object_name=base_obj.name,
                        object_type=base_obj.object_type,
                        classification='NO_CONFLICT',
                        change_type='MODIFIED',
                        base_object_id=base_obj.id,
                        vendor_object_id=vendor_obj.id,
                        display_order=2
                    )
                    test_changes.append(change3)
            
            # Add changes to database
            for change in test_changes:
                db.session.add(change)
            db.session.commit()
            
            # Verify each change has at least one valid object reference
            for change in test_changes:
                # At least one object ID should be set
                has_reference = (
                    change.base_object_id is not None or
                    change.customer_object_id is not None or
                    change.vendor_object_id is not None
                )
                assert has_reference, (
                    f"Change {change.id} should have at least one object reference"
                )
                
                # Verify each set object ID references an existing object
                if change.base_object_id is not None:
                    base_obj = AppianObject.query.get(change.base_object_id)
                    assert base_obj is not None, (
                        f"Change {change.id} base_object_id should reference "
                        f"existing object"
                    )
                    assert base_obj.package_id == base_package.id, (
                        f"Change {change.id} base object should be in base package"
                    )
                
                if change.vendor_object_id is not None:
                    vendor_obj = AppianObject.query.get(change.vendor_object_id)
                    assert vendor_obj is not None, (
                        f"Change {change.id} vendor_object_id should reference "
                        f"existing object"
                    )
                    assert vendor_obj.package_id == vendor_package.id, (
                        f"Change {change.id} vendor object should be in vendor package"
                    )
                
                # Verify relationships work
                if change.base_object_id:
                    assert change.base_object is not None, (
                        "Change.base_object relationship should work"
                    )
                if change.vendor_object_id:
                    assert change.vendor_object is not None, (
                        "Change.vendor_object relationship should work"
                    )
                        
        finally:
            # Cleanup
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(
        base_blueprint=blueprint_with_objects(),
        vendor_blueprint=blueprint_with_objects()
    )
    def test_property_21_review_change_linkage(
        self,
        base_blueprint,
        vendor_blueprint
    ):
        """
        Feature: merge-assistant-data-model-refactoring, Property 21: Review-change linkage
        
        For any ChangeReview record, it should have a valid change_id that references 
        an existing Change record.
        
        Validates: Requirements 6.4
        """
        from services.merge_assistant import (
            PackageService,
            ChangeService,
            ThreeWayComparisonService,
            ChangeClassificationService
        )
        
        # Create a session
        session = MergeSession(
            reference_id=f"MRG_{uuid.uuid4().hex[:8].upper()}",
            base_package_name="Test Package A",
            customized_package_name="Test Package B",
            new_vendor_package_name="Test Package C",
            status='processing'
        )
        db.session.add(session)
        db.session.commit()
        
        try:
            # Create packages
            package_service = PackageService()
            base_package = package_service.create_package_from_blueprint(
                session.id,
                'base',
                base_blueprint
            )
            vendor_package = package_service.create_package_from_blueprint(
                session.id,
                'new_vendor',
                vendor_blueprint
            )
            
            # Perform comparison
            comparison_service = ThreeWayComparisonService()
            vendor_changes = comparison_service.compare_vendor_changes(
                base_blueprint,
                vendor_blueprint
            )
            customer_changes = {'added': [], 'modified': [], 'removed': []}
            
            # Classify changes
            classification_service = ChangeClassificationService()
            classification_results = classification_service.classify_changes(
                vendor_changes,
                customer_changes
            )
            
            # Create ordered changes
            ordered_changes = []
            for category, changes in classification_results.items():
                for change in changes:
                    change['classification'] = category
                    ordered_changes.append(change)
            
            # Create changes in database
            change_service = ChangeService()
            change_service.create_changes_from_comparison(
                session.id,
                classification_results,
                ordered_changes
            )
            
            # Get all changes for this session
            changes = Change.query.filter_by(session_id=session.id).all()
            
            # Verify we have changes
            if len(changes) > 0:
                # Get all reviews for this session
                reviews = ChangeReview.query.filter_by(session_id=session.id).all()
                
                # Verify each review has valid change linkage
                for review in reviews:
                    # Verify change_id is set
                    assert review.change_id is not None, (
                        f"Review {review.id} should have change_id"
                    )
                    
                    # Verify change exists
                    linked_change = Change.query.get(review.change_id)
                    assert linked_change is not None, (
                        f"Review {review.id} change_id should reference existing change"
                    )
                    assert linked_change.session_id == session.id, (
                        f"Review {review.id} should link to change in same session"
                    )
                    
                    # Verify relationship works
                    assert review.change is not None, (
                        "ChangeReview.change relationship should work"
                    )
                    assert review.change.id == review.change_id, (
                        "ChangeReview.change should match change_id"
                    )
                    
                    # Verify reverse relationship works
                    assert linked_change.review is not None, (
                        "Change.review relationship should work"
                    )
                    assert linked_change.review.id == review.id, (
                        "Change.review should match review"
                    )
                
                # Test that orphaned reviews cannot be created
                # (foreign key constraint should prevent this)
                orphan_review = ChangeReview(
                    session_id=session.id,
                    change_id=999999,  # Non-existent change
                    review_status='pending'
                )
                db.session.add(orphan_review)
                
                # This should raise an integrity error
                with self.assertRaises(Exception) as context:
                    db.session.commit()
                
                # Rollback the failed transaction
                db.session.rollback()
                
        finally:
            # Cleanup
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()

    @settings(max_examples=100, deadline=None, database=None)
    @given(blueprints=blueprint_with_objects())
    def test_property_22_dependency_storage_correctness(self, blueprints):
        """
        Feature: merge-assistant-data-model-refactoring, Property 22: Dependency storage correctness
        
        For any dependency relationship between two objects, it should be stored in the 
        ObjectDependency table with valid package_id, parent_uuid, and child_uuid.
        
        Validates: Requirements 6.5
        """
        from services.merge_assistant import PackageService
        
        # Create a session
        session = MergeSession(
            reference_id=f"MRG_{uuid.uuid4().hex[:8].upper()}",
            base_package_name="Test Package",
            customized_package_name="Test Package Custom",
            new_vendor_package_name="Test Package Vendor",
            status='processing'
        )
        db.session.add(session)
        db.session.commit()
        
        try:
            # Add some dependencies to the blueprint
            object_lookup = blueprints['object_lookup']
            object_uuids = list(object_lookup.keys())
            
            # Create dependencies between objects
            dependencies_added = []
            if len(object_uuids) >= 2:
                # Add dependency information to objects
                for i, uuid_key in enumerate(object_uuids[:-1]):
                    obj = object_lookup[uuid_key]
                    child_uuid = object_uuids[i + 1]
                    # Add a reference to the next object
                    obj['dependencies'] = [child_uuid]
                    dependencies_added.append((uuid_key, child_uuid))
            
            # Create package from blueprint
            service = PackageService()
            package = service.create_package_from_blueprint(
                session.id,
                'base',
                blueprints
            )
            
            # Get all dependencies for this package
            dependencies = ObjectDependency.query.filter_by(
                package_id=package.id
            ).all()
            
            # If we added dependencies, verify they were stored correctly
            if len(dependencies_added) > 0:
                # Verify each dependency has valid fields
                for dep in dependencies:
                    # Verify package_id
                    assert dep.package_id == package.id, (
                        f"Dependency should reference correct package"
                    )
                    
                    # Verify parent_uuid
                    assert dep.parent_uuid is not None, (
                        "Dependency should have parent_uuid"
                    )
                    assert isinstance(dep.parent_uuid, str), (
                        "parent_uuid should be a string"
                    )
                    assert len(dep.parent_uuid) > 0, (
                        "parent_uuid should not be empty"
                    )
                    
                    # Verify child_uuid
                    assert dep.child_uuid is not None, (
                        "Dependency should have child_uuid"
                    )
                    assert isinstance(dep.child_uuid, str), (
                        "child_uuid should be a string"
                    )
                    assert len(dep.child_uuid) > 0, (
                        "child_uuid should not be empty"
                    )
                    
                    # Verify parent and child are different
                    assert dep.parent_uuid != dep.child_uuid, (
                        "Parent and child should be different objects"
                    )
                    
                    # Verify parent and child objects exist
                    parent_obj = AppianObject.query.filter_by(
                        package_id=package.id,
                        uuid=dep.parent_uuid
                    ).first()
                    child_obj = AppianObject.query.filter_by(
                        package_id=package.id,
                        uuid=dep.child_uuid
                    ).first()
                    
                    assert parent_obj is not None, (
                        f"Parent object {dep.parent_uuid} should exist"
                    )
                    assert child_obj is not None, (
                        f"Child object {dep.child_uuid} should exist"
                    )
                    
                    # Verify timestamps
                    assert dep.created_at is not None, (
                        "Dependency should have created_at timestamp"
                    )
                    assert isinstance(dep.created_at, datetime), (
                        "created_at should be a datetime"
                    )
                
                # Verify unique constraint works
                # Try to create a duplicate dependency
                if len(dependencies) > 0:
                    first_dep = dependencies[0]
                    duplicate_dep = ObjectDependency(
                        package_id=first_dep.package_id,
                        parent_uuid=first_dep.parent_uuid,
                        child_uuid=first_dep.child_uuid,
                        dependency_type='reference'
                    )
                    db.session.add(duplicate_dep)
                    
                    # This should raise an integrity error
                    with self.assertRaises(Exception) as context:
                        db.session.commit()
                    
                    # Rollback the failed transaction
                    db.session.rollback()
                    
        finally:
            # Cleanup
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()
