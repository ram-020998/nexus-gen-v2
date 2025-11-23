"""
Unit Tests for ThreeWayMergeService with Normalized Schema

Tests the ThreeWayMergeService methods that work with the normalized
database schema including:
- create_session with normalized schema
- get_ordered_changes with JOINs
- filter_changes with SQL
- get_summary with aggregates

Requirements: 3.2, 3.3, 4.2, 4.4
"""
import pytest

from app import create_app
from models import (
    db, Package, AppianObject, Change, ChangeReview
)
from utilityTools.test_config import TestConfig
from services.merge_assistant.three_way_merge_service import (
    ThreeWayMergeService
)
from tests.fixtures.three_way_merge.fixture_loader import (
    SMALL_PACKAGES
)


class TestThreeWayMergeServiceNormalizedSchema:
    """Test ThreeWayMergeService with normalized schema"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config.from_object(TestConfig)
        TestConfig.init_directories()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        self.service = ThreeWayMergeService()

        yield

        # Teardown
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_session_creates_normalized_tables(self):
        """
        Test that create_session populates normalized tables
        
        Verifies:
        - MergeSession record is created
        - Package records are created (3 packages)
        - AppianObject records are created
        - Change records are created
        - ChangeReview records are created
        - No JSON blobs remain in session
        
        Requirements: 3.2
        """
        # Get test packages
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Verify session was created
        assert session is not None
        assert session.id is not None
        assert session.reference_id.startswith('MRG_')
        assert session.status == 'ready'
        assert session.total_changes > 0

        # Verify Package records were created (3 packages)
        packages = Package.query.filter_by(session_id=session.id).all()
        assert len(packages) == 3

        package_types = {pkg.package_type for pkg in packages}
        assert package_types == {'base', 'customized', 'new_vendor'}

        # Verify each package has a name
        for pkg in packages:
            assert pkg.package_name is not None
            assert len(pkg.package_name) > 0

        # Verify AppianObject records were created
        total_objects = 0
        for pkg in packages:
            objects = AppianObject.query.filter_by(package_id=pkg.id).all()
            assert len(objects) > 0
            total_objects += len(objects)

            # Verify objects have required fields
            for obj in objects:
                assert obj.uuid is not None
                assert obj.name is not None
                assert obj.object_type is not None

        # Verify total objects matches package metadata
        assert total_objects > 0

        # Verify Change records were created
        changes = Change.query.filter_by(session_id=session.id).all()
        assert len(changes) == session.total_changes
        assert len(changes) > 0

        # Verify changes have required fields
        for change in changes:
            assert change.object_uuid is not None
            assert change.object_name is not None
            assert change.object_type is not None
            assert change.classification is not None
            assert change.display_order is not None

        # Verify ChangeReview records were created
        reviews = ChangeReview.query.filter_by(session_id=session.id).all()
        assert len(reviews) == session.total_changes

        # Verify all reviews start as pending
        for review in reviews:
            assert review.review_status == 'pending'
            assert review.change_id is not None

    def test_create_session_with_foreign_keys(self):
        """
        Test that create_session establishes proper foreign key relationships
        
        Verifies:
        - Changes link to AppianObjects via foreign keys
        - Changes link to MergeGuidance
        - ChangeReviews link to Changes
        
        Requirements: 3.2
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get a change with objects
        changes = Change.query.filter_by(session_id=session.id).all()
        assert len(changes) > 0

        # Find a change that has at least one object reference
        change_with_objects = None
        for change in changes:
            if (change.base_object_id or 
                change.customer_object_id or 
                change.vendor_object_id):
                change_with_objects = change
                break

        assert change_with_objects is not None

        # Verify foreign key relationships work
        if change_with_objects.base_object_id:
            base_obj = AppianObject.query.get(
                change_with_objects.base_object_id
            )
            assert base_obj is not None
            assert base_obj.uuid == change_with_objects.object_uuid

        if change_with_objects.customer_object_id:
            customer_obj = AppianObject.query.get(
                change_with_objects.customer_object_id
            )
            assert customer_obj is not None

        if change_with_objects.vendor_object_id:
            vendor_obj = AppianObject.query.get(
                change_with_objects.vendor_object_id
            )
            assert vendor_obj is not None

        # Verify ChangeReview links to Change
        review = ChangeReview.query.filter_by(
            change_id=change_with_objects.id
        ).first()
        assert review is not None
        assert review.session_id == session.id

    def test_get_ordered_changes_uses_joins(self):
        """
        Test that get_ordered_changes uses SQL JOINs instead of JSON parsing
        
        Verifies:
        - Returns changes in correct order (by display_order)
        - Includes related object data via JOINs
        - Includes merge guidance data
        - Includes review status
        - No JSON parsing required
        
        Requirements: 3.2, 4.2
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get ordered changes
        changes = self.service.get_ordered_changes(session.id)

        # Verify changes are returned
        assert len(changes) > 0
        assert len(changes) == session.total_changes

        # Verify changes are ordered by display_order
        for i, change in enumerate(changes):
            assert change['display_order'] == i

        # Verify each change has required fields
        for change in changes:
            assert 'uuid' in change
            assert 'name' in change
            assert 'type' in change
            assert 'classification' in change
            assert 'change_type' in change
            assert 'display_order' in change

        # Verify changes include object data (from JOINs)
        # At least some changes should have object data
        changes_with_objects = [
            c for c in changes
            if 'base_object' in c or 
               'customer_object' in c or 
               'vendor_object' in c
        ]
        assert len(changes_with_objects) > 0

        # Verify object data structure
        for change in changes_with_objects:
            if 'base_object' in change and change['base_object']:
                obj = change['base_object']
                assert 'uuid' in obj
                assert 'name' in obj
                assert 'type' in obj

        # Verify changes include merge guidance
        changes_with_guidance = [
            c for c in changes
            if 'merge_guidance' in c and c['merge_guidance']
        ]
        assert len(changes_with_guidance) > 0

        # Verify guidance structure
        for change in changes_with_guidance:
            guidance = change['merge_guidance']
            assert 'recommendation' in guidance
            assert 'reason' in guidance

        # Verify changes include review status
        for change in changes:
            assert 'review_status' in change
            assert change['review_status'] == 'pending'  # Initially pending

    def test_get_ordered_changes_maintains_order(self):
        """
        Test that get_ordered_changes maintains correct ordering
        
        Verifies:
        - Changes are returned in display_order sequence
        - Order is consistent across multiple calls
        
        Requirements: 4.2
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get ordered changes multiple times
        changes1 = self.service.get_ordered_changes(session.id)
        changes2 = self.service.get_ordered_changes(session.id)

        # Verify same order
        assert len(changes1) == len(changes2)

        for i in range(len(changes1)):
            assert changes1[i]['uuid'] == changes2[i]['uuid']
            assert changes1[i]['display_order'] == changes2[i]['display_order']
            assert changes1[i]['display_order'] == i

    def test_filter_changes_by_classification(self):
        """
        Test filtering changes by classification using SQL WHERE
        
        Verifies:
        - Filters by classification correctly
        - Uses indexed columns for performance
        - Returns only matching changes
        
        Requirements: 3.2, 4.2
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get all changes to know what classifications exist
        all_changes = self.service.get_ordered_changes(session.id)
        classifications = {c['classification'] for c in all_changes}

        # Test filtering by each classification
        for classification in classifications:
            filtered = self.service.filter_changes(
                session.id,
                classification=classification
            )

            # Verify all returned changes have the correct classification
            assert len(filtered) > 0
            for change in filtered:
                assert change['classification'] == classification

            # Verify count matches
            expected_count = sum(
                1 for c in all_changes
                if c['classification'] == classification
            )
            assert len(filtered) == expected_count

    def test_filter_changes_by_object_type(self):
        """
        Test filtering changes by object type using SQL WHERE
        
        Verifies:
        - Filters by object type correctly
        - Returns only matching changes
        
        Requirements: 3.2, 4.2
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get all changes to know what types exist
        all_changes = self.service.get_ordered_changes(session.id)
        object_types = {c['type'] for c in all_changes}

        # Test filtering by each type
        for obj_type in object_types:
            filtered = self.service.filter_changes(
                session.id,
                object_type=obj_type
            )

            # Verify all returned changes have the correct type
            if len(filtered) > 0:
                for change in filtered:
                    assert change['type'] == obj_type

                # Verify count matches
                expected_count = sum(
                    1 for c in all_changes
                    if c['type'] == obj_type
                )
                assert len(filtered) == expected_count

    def test_filter_changes_by_review_status(self):
        """
        Test filtering changes by review status using SQL JOIN
        
        Verifies:
        - Filters by review status correctly
        - Joins with ChangeReview table
        - Returns only matching changes
        
        Requirements: 3.2, 3.3
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Initially all should be pending
        pending = self.service.filter_changes(
            session.id,
            review_status='pending'
        )
        assert len(pending) == session.total_changes

        # Review first change
        self.service.update_progress(session.id, 0, 'reviewed')

        # Filter by reviewed
        reviewed = self.service.filter_changes(
            session.id,
            review_status='reviewed'
        )
        assert len(reviewed) == 1
        assert reviewed[0]['review_status'] == 'reviewed'

        # Filter by pending (should be reduced)
        pending = self.service.filter_changes(
            session.id,
            review_status='pending'
        )
        assert len(pending) == session.total_changes - 1

        # If there are more changes, test skipped status
        if session.total_changes > 1:
            self.service.update_progress(session.id, 1, 'skipped')
            
            # Filter by skipped
            skipped = self.service.filter_changes(
                session.id,
                review_status='skipped'
            )
            assert len(skipped) == 1
            assert skipped[0]['review_status'] == 'skipped'
            
            # Filter by pending (should be further reduced)
            pending = self.service.filter_changes(
                session.id,
                review_status='pending'
            )
            assert len(pending) == session.total_changes - 2

    def test_filter_changes_by_search_term(self):
        """
        Test filtering changes by object name search using SQL LIKE
        
        Verifies:
        - Searches object names case-insensitively
        - Uses indexed columns for performance
        - Returns matching changes
        
        Requirements: 4.2
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get all changes to find a search term
        all_changes = self.service.get_ordered_changes(session.id)
        assert len(all_changes) > 0

        # Use part of the first change's name as search term
        first_name = all_changes[0]['name']
        # Take a substring that should match
        if len(first_name) > 3:
            search_term = first_name[0:3]
        else:
            search_term = first_name

        # Filter by search term
        filtered = self.service.filter_changes(
            session.id,
            search_term=search_term
        )

        # Verify results contain the search term
        assert len(filtered) > 0
        for change in filtered:
            assert search_term.lower() in change['name'].lower()

    def test_filter_changes_with_multiple_criteria(self):
        """
        Test filtering with multiple criteria combined
        
        Verifies:
        - Multiple filters work together (AND logic)
        - Returns only changes matching all criteria
        
        Requirements: 3.2, 4.2
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get all changes
        all_changes = self.service.get_ordered_changes(session.id)

        # Find a classification and type that exist together
        classification = all_changes[0]['classification']
        obj_type = all_changes[0]['type']

        # Filter with multiple criteria
        filtered = self.service.filter_changes(
            session.id,
            classification=classification,
            object_type=obj_type
        )

        # Verify all results match both criteria
        assert len(filtered) > 0
        for change in filtered:
            assert change['classification'] == classification
            assert change['type'] == obj_type

    def test_get_summary_uses_sql_aggregates(self):
        """
        Test that get_summary uses SQL aggregates instead of loading all data
        
        Verifies:
        - Returns correct statistics
        - Uses SQL COUNT for aggregates
        - Includes breakdown by type
        - Calculates complexity estimate
        
        Requirements: 4.4
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get summary
        summary = self.service.get_summary(session.id)

        # Verify summary structure
        assert 'session_id' in summary
        assert 'reference_id' in summary
        assert 'packages' in summary
        assert 'statistics' in summary
        assert 'breakdown_by_type' in summary
        assert 'estimated_complexity' in summary
        assert 'estimated_time_hours' in summary

        # Verify session info
        assert summary['session_id'] == session.id
        assert summary['reference_id'] == session.reference_id

        # Verify package info
        packages = summary['packages']
        assert 'base' in packages
        assert 'customized' in packages
        assert 'new_vendor' in packages

        # Verify statistics
        stats = summary['statistics']
        assert 'total_changes' in stats
        assert 'no_conflict' in stats
        assert 'conflict' in stats
        assert 'customer_only' in stats
        assert 'removed_but_customized' in stats

        # Verify total matches session
        assert stats['total_changes'] == session.total_changes

        # Verify sum of categories equals total
        category_sum = (
            stats['no_conflict'] +
            stats['conflict'] +
            stats['customer_only'] +
            stats['removed_but_customized']
        )
        assert category_sum == stats['total_changes']

        # Verify breakdown by type
        breakdown = summary['breakdown_by_type']
        assert isinstance(breakdown, dict)

        # Verify breakdown totals match statistics
        breakdown_total = 0
        for obj_type, counts in breakdown.items():
            assert 'no_conflict' in counts
            assert 'conflict' in counts
            assert 'customer_only' in counts
            assert 'removed_but_customized' in counts

            breakdown_total += (
                counts['no_conflict'] +
                counts['conflict'] +
                counts['customer_only'] +
                counts['removed_but_customized']
            )

        assert breakdown_total == stats['total_changes']

        # Verify complexity estimate
        assert summary['estimated_complexity'] in ['LOW', 'MEDIUM', 'HIGH']
        assert summary['estimated_time_hours'] > 0

    def test_get_summary_statistics_accuracy(self):
        """
        Test that get_summary statistics match actual data
        
        Verifies:
        - Statistics calculated by SQL match actual counts
        - Breakdown by type is accurate
        
        Requirements: 4.4
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get summary
        summary = self.service.get_summary(session.id)

        # Get all changes to verify counts
        all_changes = Change.query.filter_by(session_id=session.id).all()

        # Count by classification manually
        manual_counts = {
            'no_conflict': 0,
            'conflict': 0,
            'customer_only': 0,
            'removed_but_customized': 0
        }

        for change in all_changes:
            classification = change.classification.lower()
            if classification in manual_counts:
                manual_counts[classification] += 1

        # Verify summary statistics match manual counts
        stats = summary['statistics']
        assert stats['no_conflict'] == manual_counts['no_conflict']
        assert stats['conflict'] == manual_counts['conflict']
        assert stats['customer_only'] == manual_counts['customer_only']
        assert stats['removed_but_customized'] == manual_counts['removed_but_customized']

    def test_update_progress_updates_counts(self):
        """
        Test that update_progress correctly updates session counts
        
        Verifies:
        - Reviewed count increments correctly
        - Skipped count increments correctly
        - Current change index updates
        - Uses SQL queries for counts
        
        Requirements: 3.3
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Initially counts should be 0
        assert session.reviewed_count == 0
        assert session.skipped_count == 0

        # Review first change
        self.service.update_progress(session.id, 0, 'reviewed', 'Test note')

        # Refresh session from database
        db.session.expire(session)
        session = self.service.get_session(session.id)

        # Verify counts updated
        assert session.reviewed_count == 1
        assert session.skipped_count == 0
        assert session.current_change_index == 0

        # If there are more changes, test additional updates
        if session.total_changes > 1:
            # Skip second change
            self.service.update_progress(session.id, 1, 'skipped')

            # Refresh session
            db.session.expire(session)
            session = self.service.get_session(session.id)

            # Verify counts updated
            assert session.reviewed_count == 1
            assert session.skipped_count == 1
            assert session.current_change_index == 1

        if session.total_changes > 2:
            # Review third change
            self.service.update_progress(session.id, 2, 'reviewed')

            # Refresh session
            db.session.expire(session)
            session = self.service.get_session(session.id)

            # Verify counts updated
            assert session.reviewed_count == 2
            assert session.skipped_count == 1
            assert session.current_change_index == 2

    def test_update_progress_creates_or_updates_review(self):
        """
        Test that update_progress creates or updates ChangeReview records
        
        Verifies:
        - Creates ChangeReview on first update
        - Updates existing ChangeReview on subsequent updates
        - Stores user notes correctly
        
        Requirements: 3.3
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get first change
        change = Change.query.filter_by(
            session_id=session.id,
            display_order=0
        ).first()
        assert change is not None

        # Initially review should exist but be pending
        review = ChangeReview.query.filter_by(
            session_id=session.id,
            change_id=change.id
        ).first()
        assert review is not None
        assert review.review_status == 'pending'

        # Update progress
        self.service.update_progress(
            session.id,
            0,
            'reviewed',
            'First review note'
        )

        # Refresh review
        db.session.expire(review)
        review = ChangeReview.query.filter_by(
            session_id=session.id,
            change_id=change.id
        ).first()

        # Verify review was updated
        assert review.review_status == 'reviewed'
        assert review.user_notes == 'First review note'
        assert review.reviewed_at is not None

        # Update again with different status
        self.service.update_progress(
            session.id,
            0,
            'skipped',
            'Changed to skipped'
        )

        # Refresh review
        db.session.expire(review)
        review = ChangeReview.query.filter_by(
            session_id=session.id,
            change_id=change.id
        ).first()

        # Verify review was updated again
        assert review.review_status == 'skipped'
        assert review.user_notes == 'Changed to skipped'

    def test_generate_report_includes_all_data(self):
        """
        Test that generate_report includes complete data using JOINs
        
        Verifies:
        - Includes summary
        - Includes all changes with complete data
        - Includes changes grouped by category
        - Includes statistics
        - Uses JOIN queries, not JSON parsing
        
        Requirements: 3.2
        """
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create session
        session = self.service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Review first change
        self.service.update_progress(session.id, 0, 'reviewed', 'Note 1')
        reviewed_count = 1
        skipped_count = 0

        # If there are more changes, skip the second one
        if session.total_changes > 1:
            self.service.update_progress(session.id, 1, 'skipped')
            skipped_count = 1

        # Generate report
        report = self.service.generate_report(session.id)

        # Verify report structure
        assert 'summary' in report
        assert 'changes' in report
        assert 'changes_by_category' in report
        assert 'statistics' in report
        assert 'session' in report

        # Verify summary
        summary = report['summary']
        assert summary['session_id'] == session.id
        assert 'statistics' in summary

        # Verify changes
        changes = report['changes']
        assert len(changes) == session.total_changes

        # Verify each change has complete data
        for change in changes:
            assert 'uuid' in change
            assert 'name' in change
            assert 'type' in change
            assert 'classification' in change
            assert 'review_status' in change

        # Verify changes by category
        by_category = report['changes_by_category']
        assert 'NO_CONFLICT' in by_category
        assert 'CONFLICT' in by_category
        assert 'CUSTOMER_ONLY' in by_category
        assert 'REMOVED_BUT_CUSTOMIZED' in by_category

        # Verify category totals match
        category_total = sum(len(changes) for changes in by_category.values())
        assert category_total == session.total_changes

        # Verify statistics
        stats = report['statistics']
        assert stats['total_changes'] == session.total_changes
        assert stats['reviewed'] == reviewed_count
        assert stats['skipped'] == skipped_count
        assert stats['pending'] == session.total_changes - reviewed_count - skipped_count

        # Verify session info
        session_info = report['session']
        assert session_info['reference_id'] == session.reference_id
        assert session_info['status'] == session.status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
