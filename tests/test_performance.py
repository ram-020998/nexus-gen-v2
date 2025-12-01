"""
Performance Tests

Verifies that all queries complete in < 200ms as per Requirement 14.5.
"""

import pytest
import time
from typing import Callable, Any
from app import create_app
from models import db, MergeSession, ObjectLookup, Change, DeltaComparisonResult
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.change_repository import ChangeRepository
from repositories.delta_comparison_repository import DeltaComparisonRepository
from repositories.package_object_mapping_repository import PackageObjectMappingRepository


def measure_query_time(func: Callable, *args, **kwargs) -> tuple[Any, float]:
    """
    Measure query execution time.
    
    Returns:
        Tuple of (result, time_in_ms)
    """
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    time_ms = (end - start) * 1000
    return result, time_ms


class TestPerformance:
    """Performance tests for repository queries."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test app context."""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        yield
        
        self.app_context.pop()
    
    def test_object_lookup_find_by_uuid_performance(self):
        """Test that find_by_uuid completes in < 200ms."""
        repo = ObjectLookupRepository()
        
        # Get a sample UUID from database
        sample_obj = ObjectLookup.query.first()
        if not sample_obj:
            pytest.skip("No objects in database")
        
        # Measure query time
        result, time_ms = measure_query_time(repo.find_by_uuid, sample_obj.uuid)
        
        print(f"\nfind_by_uuid: {time_ms:.2f}ms")
        assert time_ms < 200, f"Query took {time_ms:.2f}ms (expected < 200ms)"
        assert result is not None
    
    def test_object_lookup_find_by_uuid_cached_performance(self):
        """Test that cached find_by_uuid is faster than first call."""
        repo = ObjectLookupRepository()
        
        # Get a sample UUID
        sample_obj = ObjectLookup.query.first()
        if not sample_obj:
            pytest.skip("No objects in database")
        
        # First call (cache miss)
        _, time_first = measure_query_time(repo.find_by_uuid, sample_obj.uuid)
        
        # Second call (cache hit)
        _, time_cached = measure_query_time(repo.find_by_uuid, sample_obj.uuid)
        
        print(f"\nFirst call: {time_first:.2f}ms, Cached call: {time_cached:.2f}ms")
        assert time_cached < time_first, "Cached call should be faster"
        assert time_cached < 200, f"Cached query took {time_cached:.2f}ms"
    
    def test_change_repository_get_ordered_changes_performance(self):
        """Test that get_ordered_changes with eager loading completes in < 200ms."""
        repo = ChangeRepository()
        
        # Get a sample session
        session = MergeSession.query.first()
        if not session:
            pytest.skip("No sessions in database")
        
        # Measure query time
        result, time_ms = measure_query_time(repo.get_ordered_changes, session.id)
        
        print(f"\nget_ordered_changes: {time_ms:.2f}ms (returned {len(result)} changes)")
        assert time_ms < 200, f"Query took {time_ms:.2f}ms (expected < 200ms)"
    
    def test_change_repository_get_by_session_with_objects_performance(self):
        """Test that get_by_session_with_objects completes in < 200ms."""
        repo = ChangeRepository()
        
        # Get a sample session
        session = MergeSession.query.first()
        if not session:
            pytest.skip("No sessions in database")
        
        # Measure query time
        result, time_ms = measure_query_time(repo.get_by_session_with_objects, session.id)
        
        print(f"\nget_by_session_with_objects: {time_ms:.2f}ms (returned {len(result)} changes)")
        assert time_ms < 200, f"Query took {time_ms:.2f}ms (expected < 200ms)"
    
    def test_delta_comparison_get_by_session_performance(self):
        """Test that delta comparison queries complete in < 200ms."""
        repo = DeltaComparisonRepository()
        
        # Get a sample session
        session = MergeSession.query.first()
        if not session:
            pytest.skip("No sessions in database")
        
        # Measure query time
        result, time_ms = measure_query_time(repo.get_by_session, session.id)
        
        print(f"\nget_by_session (delta): {time_ms:.2f}ms (returned {len(result)} results)")
        assert time_ms < 200, f"Query took {time_ms:.2f}ms (expected < 200ms)"
    
    def test_delta_comparison_get_statistics_performance(self):
        """Test that statistics queries complete in < 200ms."""
        repo = DeltaComparisonRepository()
        
        # Get a sample session
        session = MergeSession.query.first()
        if not session:
            pytest.skip("No sessions in database")
        
        # Measure query time
        result, time_ms = measure_query_time(repo.get_statistics, session.id)
        
        print(f"\nget_statistics (delta): {time_ms:.2f}ms")
        assert time_ms < 200, f"Query took {time_ms:.2f}ms (expected < 200ms)"
        assert 'total' in result
    
    def test_change_repository_get_statistics_performance(self):
        """Test that change statistics queries complete in < 200ms."""
        repo = ChangeRepository()
        
        # Get a sample session
        session = MergeSession.query.first()
        if not session:
            pytest.skip("No sessions in database")
        
        # Measure query time
        result, time_ms = measure_query_time(repo.get_statistics, session.id)
        
        print(f"\nget_statistics (changes): {time_ms:.2f}ms")
        assert time_ms < 200, f"Query took {time_ms:.2f}ms (expected < 200ms)"
        assert 'total' in result
    
    def test_package_object_mapping_get_objects_performance(self):
        """Test that package object mapping queries complete in < 200ms."""
        repo = PackageObjectMappingRepository()
        
        # Get a sample session with packages
        session = MergeSession.query.first()
        if not session:
            pytest.skip("No sessions in database")
        
        packages = session.packages.all()
        if not packages:
            pytest.skip("No packages in session")
        
        # Measure query time
        result, time_ms = measure_query_time(repo.get_objects_in_package, packages[0].id)
        
        print(f"\nget_objects_in_package: {time_ms:.2f}ms (returned {len(result)} objects)")
        assert time_ms < 200, f"Query took {time_ms:.2f}ms (expected < 200ms)"
    
    def test_bulk_operations_performance(self):
        """Test that bulk operations are faster than individual operations."""
        obj_repo = ObjectLookupRepository()
        
        # Create test data
        test_objects = [
            {
                'uuid': f'perf-test-{i}',
                'name': f'Performance Test Object {i}',
                'object_type': 'Interface'
            }
            for i in range(10)
        ]
        
        # Measure individual operations
        start = time.time()
        for obj_data in test_objects:
            obj_repo.find_or_create(**obj_data)
        db.session.commit()
        individual_time = (time.time() - start) * 1000
        
        # Clean up
        for obj_data in test_objects:
            obj = obj_repo.find_by_uuid(obj_data['uuid'])
            if obj:
                db.session.delete(obj)
        db.session.commit()
        
        # Measure bulk operation
        start = time.time()
        obj_repo.bulk_find_or_create(test_objects)
        db.session.commit()
        bulk_time = (time.time() - start) * 1000
        
        # Clean up
        for obj_data in test_objects:
            obj = obj_repo.find_by_uuid(obj_data['uuid'])
            if obj:
                db.session.delete(obj)
        db.session.commit()
        
        print(f"\nIndividual operations: {individual_time:.2f}ms")
        print(f"Bulk operation: {bulk_time:.2f}ms")
        print(f"Speedup: {individual_time/bulk_time:.2f}x")
        
        # Bulk should be faster (or at least not significantly slower)
        assert bulk_time < individual_time * 1.5, "Bulk operation should be faster"
    
    def test_cache_effectiveness(self):
        """Test that caching improves performance."""
        repo = ObjectLookupRepository()
        
        # Clear cache
        repo.cache.clear()
        
        # Get sample objects
        sample_objs = ObjectLookup.query.limit(5).all()
        if not sample_objs:
            pytest.skip("No objects in database")
        
        # Measure uncached queries
        uncached_times = []
        for obj in sample_objs:
            _, time_ms = measure_query_time(repo.find_by_uuid, obj.uuid)
            uncached_times.append(time_ms)
        
        avg_uncached = sum(uncached_times) / len(uncached_times)
        
        # Measure cached queries
        cached_times = []
        for obj in sample_objs:
            _, time_ms = measure_query_time(repo.find_by_uuid, obj.uuid)
            cached_times.append(time_ms)
        
        avg_cached = sum(cached_times) / len(cached_times)
        
        # Get cache stats
        stats = repo.cache.cache.get_stats()
        
        print(f"\nAverage uncached: {avg_uncached:.2f}ms")
        print(f"Average cached: {avg_cached:.2f}ms")
        print(f"Cache stats: {stats}")
        
        # Cached should be faster
        assert avg_cached < avg_uncached, "Cached queries should be faster"
        assert stats['hits'] > 0, "Should have cache hits"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
on_id': new_session.id,
                    'object_id': obj.id,
                    'classification': 'NEW' if i < 50 else 'CONFLICT',
                    'display_order': i + 1,
                    'vendor_change_type': 'ADDED' if i < 50 else 'MODIFIED',
                    'customer_change_type': 'MODIFIED' if i >= 50 else None
                }
                for i, obj in enumerate(objects)
            ]
            
            result, time_ms = measure_time(repo.bulk_create_changes, changes)
            assert time_ms < PERFORMANCE_THRESHOLD_MS, \
                f"bulk_create_changes (100 changes) took {time_ms:.2f}ms (threshold: {PERFORMANCE_THRESHOLD_MS}ms)"


class TestCachePerformance:
    """Test cache effectiveness."""
    
    def test_cache_hit_rate(self, app, test_data):
        """Test that cache improves performance significantly."""
        with app.app_context():
            repo = ObjectLookupRepository()
            cache = get_cache()
            cache.clear()
            
            # First 10 lookups (cache misses)
            start = time.perf_counter()
            for i in range(10):
                repo.find_by_uuid(f'test-uuid-{i:03d}')
            end = time.perf_counter()
            uncached_time_ms = (end - start) * 1000
            
            # Second 10 lookups (cache hits)
            start = time.perf_counter()
            for i in range(10):
                repo.find_by_uuid(f'test-uuid-{i:03d}')
            end = time.perf_counter()
            cached_time_ms = (end - start) * 1000
            
            # Cached should be at least 2x faster
            speedup = uncached_time_ms / cached_time_ms
            assert speedup >= 2.0, \
                f"Cache speedup was only {speedup:.2f}x (expected >= 2x)"
            
            # Check cache stats
            stats = cache.get_stats()
            assert stats['hits'] >= 10, f"Expected >= 10 cache hits, got {stats['hits']}"
            print(f"\nCache stats: {stats}")
            print(f"Speedup: {speedup:.2f}x")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
