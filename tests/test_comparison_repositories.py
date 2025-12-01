"""
Test Comparison Repositories

Tests for comparison result repositories that store detailed differences
for object-specific comparisons.
"""

import pytest
import uuid
from models import (
    db, MergeSession, Package, ObjectLookup, Change,
    InterfaceComparison, ProcessModelComparison, RecordTypeComparison
)
from repositories.comparison.interface_comparison_repository import (
    InterfaceComparisonRepository
)
from repositories.comparison.process_model_comparison_repository import (
    ProcessModelComparisonRepository
)
from repositories.comparison.record_type_comparison_repository import (
    RecordTypeComparisonRepository
)


class TestInterfaceComparisonRepository:
    """Test InterfaceComparisonRepository"""

    def test_create_comparison(self, app):
        """Test creating an interface comparison"""
        with app.app_context():
            # Create test data
            session = MergeSession(
                reference_id=f'test-session-{uuid.uuid4()}',
                status='processing'
            )
            db.session.add(session)
            db.session.flush()

            obj_lookup = ObjectLookup(
                uuid=f'test-uuid-{uuid.uuid4()}',
                name='Test Interface',
                object_type='Interface'
            )
            db.session.add(obj_lookup)
            db.session.flush()

            change = Change(
                session_id=session.id,
                object_id=obj_lookup.id,
                classification='CONFLICT',
                display_order=1
            )
            db.session.add(change)
            db.session.flush()

            # Create comparison
            repo = InterfaceComparisonRepository()
            comparison = repo.create_comparison(
                change_id=change.id,
                sail_code_diff="- old code\n+ new code",
                parameters_added=[
                    {
                        "parameter_name": "newParam",
                        "parameter_type": "Text",
                        "is_required": True
                    }
                ],
                parameters_removed=[
                    {
                        "parameter_name": "oldParam",
                        "parameter_type": "Number"
                    }
                ],
                parameters_modified=[
                    {
                        "parameter_name": "modifiedParam",
                        "old_type": "Text",
                        "new_type": "Number"
                    }
                ],
                security_changes=[
                    {
                        "change_type": "ADDED",
                        "role_name": "Admin",
                        "permission_type": "EDIT"
                    }
                ]
            )

            db.session.commit()

            # Verify
            assert comparison.id is not None
            assert comparison.change_id == change.id
            assert comparison.sail_code_diff == "- old code\n+ new code"
            assert comparison.parameters_added is not None
            assert comparison.parameters_removed is not None
            assert comparison.parameters_modified is not None
            assert comparison.security_changes is not None

    def test_get_by_change_id(self, app):
        """Test retrieving comparison by change ID"""
        with app.app_context():
            # Create test data
            session = MergeSession(
                reference_id=f'test-session-{uuid.uuid4()}',
                status='processing'
            )
            db.session.add(session)
            db.session.flush()

            obj_lookup = ObjectLookup(
                uuid=f'test-uuid-{uuid.uuid4()}',
                name='Test Interface',
                object_type='Interface'
            )
            db.session.add(obj_lookup)
            db.session.flush()

            change = Change(
                session_id=session.id,
                object_id=obj_lookup.id,
                classification='CONFLICT',
                display_order=1
            )
            db.session.add(change)
            db.session.flush()

            repo = InterfaceComparisonRepository()
            comparison = repo.create_comparison(
                change_id=change.id,
                sail_code_diff="test diff"
            )
            db.session.commit()

            # Retrieve
            retrieved = repo.get_by_change_id(change.id)
            assert retrieved is not None
            assert retrieved.id == comparison.id
            assert retrieved.sail_code_diff == "test diff"

    def test_get_parameters_added(self, app):
        """Test retrieving added parameters as JSON"""
        with app.app_context():
            # Create test data
            session = MergeSession(
                reference_id=f'test-session-{uuid.uuid4()}',
                status='processing'
            )
            db.session.add(session)
            db.session.flush()

            obj_lookup = ObjectLookup(
                uuid=f'test-uuid-{uuid.uuid4()}',
                name='Test Interface',
                object_type='Interface'
            )
            db.session.add(obj_lookup)
            db.session.flush()

            change = Change(
                session_id=session.id,
                object_id=obj_lookup.id,
                classification='CONFLICT',
                display_order=1
            )
            db.session.add(change)
            db.session.flush()

            repo = InterfaceComparisonRepository()
            params_added = [
                {"parameter_name": "param1", "parameter_type": "Text"}
            ]
            comparison = repo.create_comparison(
                change_id=change.id,
                parameters_added=params_added
            )
            db.session.commit()

            # Retrieve as JSON
            retrieved_params = repo.get_parameters_added(change.id)
            assert retrieved_params is not None
            assert len(retrieved_params) == 1
            assert retrieved_params[0]["parameter_name"] == "param1"


class TestProcessModelComparisonRepository:
    """Test ProcessModelComparisonRepository"""

    def test_create_comparison(self, app):
        """Test creating a process model comparison"""
        with app.app_context():
            # Create test data
            session = MergeSession(
                reference_id=f'test-session-{uuid.uuid4()}',
                status='processing'
            )
            db.session.add(session)
            db.session.flush()

            obj_lookup = ObjectLookup(
                uuid=f'test-uuid-{uuid.uuid4()}',
                name='Test Process Model',
                object_type='Process Model'
            )
            db.session.add(obj_lookup)
            db.session.flush()

            change = Change(
                session_id=session.id,
                object_id=obj_lookup.id,
                classification='CONFLICT',
                display_order=1
            )
            db.session.add(change)
            db.session.flush()

            # Create comparison
            repo = ProcessModelComparisonRepository()
            comparison = repo.create_comparison(
                change_id=change.id,
                nodes_added=[
                    {
                        "node_id": "node_5",
                        "node_type": "SCRIPT_TASK",
                        "node_name": "Calculate"
                    }
                ],
                flows_added=[
                    {
                        "from_node_id": "node_4",
                        "to_node_id": "node_5",
                        "flow_label": "Success"
                    }
                ],
                mermaid_diagram="graph TD\n  A-->B"
            )

            db.session.commit()

            # Verify
            assert comparison.id is not None
            assert comparison.change_id == change.id
            assert comparison.nodes_added is not None
            assert comparison.flows_added is not None
            assert comparison.mermaid_diagram == "graph TD\n  A-->B"

    def test_get_nodes_added(self, app):
        """Test retrieving added nodes as JSON"""
        with app.app_context():
            # Create test data
            session = MergeSession(
                reference_id=f'test-session-{uuid.uuid4()}',
                status='processing'
            )
            db.session.add(session)
            db.session.flush()

            obj_lookup = ObjectLookup(
                uuid=f'test-uuid-{uuid.uuid4()}',
                name='Test Process Model',
                object_type='Process Model'
            )
            db.session.add(obj_lookup)
            db.session.flush()

            change = Change(
                session_id=session.id,
                object_id=obj_lookup.id,
                classification='CONFLICT',
                display_order=1
            )
            db.session.add(change)
            db.session.flush()

            repo = ProcessModelComparisonRepository()
            nodes_added = [
                {"node_id": "node_1", "node_type": "START"}
            ]
            comparison = repo.create_comparison(
                change_id=change.id,
                nodes_added=nodes_added
            )
            db.session.commit()

            # Retrieve as JSON
            retrieved_nodes = repo.get_nodes_added(change.id)
            assert retrieved_nodes is not None
            assert len(retrieved_nodes) == 1
            assert retrieved_nodes[0]["node_id"] == "node_1"


class TestRecordTypeComparisonRepository:
    """Test RecordTypeComparisonRepository"""

    def test_create_comparison(self, app):
        """Test creating a record type comparison"""
        with app.app_context():
            # Create test data
            session = MergeSession(
                reference_id=f'test-session-{uuid.uuid4()}',
                status='processing'
            )
            db.session.add(session)
            db.session.flush()

            obj_lookup = ObjectLookup(
                uuid=f'test-uuid-{uuid.uuid4()}',
                name='Test Record Type',
                object_type='Record Type'
            )
            db.session.add(obj_lookup)
            db.session.flush()

            change = Change(
                session_id=session.id,
                object_id=obj_lookup.id,
                classification='CONFLICT',
                display_order=1
            )
            db.session.add(change)
            db.session.flush()

            # Create comparison
            repo = RecordTypeComparisonRepository()
            comparison = repo.create_comparison(
                change_id=change.id,
                fields_changed=[
                    {
                        "change_type": "ADDED",
                        "field_name": "newField",
                        "field_type": "Text"
                    }
                ],
                relationships_changed=[
                    {
                        "change_type": "ADDED",
                        "relationship_name": "relatedRecords",
                        "relationship_type": "ONE_TO_MANY"
                    }
                ]
            )

            db.session.commit()

            # Verify
            assert comparison.id is not None
            assert comparison.change_id == change.id
            assert comparison.fields_changed is not None
            assert comparison.relationships_changed is not None

    def test_get_fields_changed(self, app):
        """Test retrieving field changes as JSON"""
        with app.app_context():
            # Create test data
            session = MergeSession(
                reference_id=f'test-session-{uuid.uuid4()}',
                status='processing'
            )
            db.session.add(session)
            db.session.flush()

            obj_lookup = ObjectLookup(
                uuid=f'test-uuid-{uuid.uuid4()}',
                name='Test Record Type',
                object_type='Record Type'
            )
            db.session.add(obj_lookup)
            db.session.flush()

            change = Change(
                session_id=session.id,
                object_id=obj_lookup.id,
                classification='CONFLICT',
                display_order=1
            )
            db.session.add(change)
            db.session.flush()

            repo = RecordTypeComparisonRepository()
            fields_changed = [
                {
                    "change_type": "MODIFIED",
                    "field_name": "field1",
                    "old_type": "Text",
                    "new_type": "Number"
                }
            ]
            comparison = repo.create_comparison(
                change_id=change.id,
                fields_changed=fields_changed
            )
            db.session.commit()

            # Retrieve as JSON
            retrieved_fields = repo.get_fields_changed(change.id)
            assert retrieved_fields is not None
            assert len(retrieved_fields) == 1
            assert retrieved_fields[0]["field_name"] == "field1"
            assert retrieved_fields[0]["change_type"] == "MODIFIED"
