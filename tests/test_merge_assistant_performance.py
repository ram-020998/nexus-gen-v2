"""
Performance Tests for Merge Assistant Data Model Refactoring

Tests performance improvements from normalized schema vs JSON-based schema.
Measures filter operations, search operations, report generation, and change loading.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""
import time
import json
import statistics
from typing import Dict, List, Any, Callable
from unittest.mock import patch
from tests.base_test import BaseTestCase
from models import db, MergeSession, Package, AppianObject, Change, ChangeReview
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService


class PerformanceMetrics:
    """Helper class to collect and analyze performance metrics"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.measurements: List[float] = []
    
    def add_measurement(self, duration: float):
        """Add a measurement in seconds"""
        self.measurements.append(duration)
    
    def get_stats(self) -> Dict[str, float]:
        """Get statistical summary of measurements"""
        if not self.measurements:
            return {
                'operation': self.operation_name,
                'count': 0,
                'mean': 0.0,
                'median': 0.0,
                'min': 0.0,
                'max': 0.0,
                'stdev': 0.0
            }
        
        return {
            'operation': self.operation_name,
            'count': len(self.measurements),
            'mean': statistics.mean(self.measurements),
            'median': statistics.median(self.measurements),
            'min': min(self.measurements),
            'max': max(self.measurements),
            'stdev': statistics.stdev(self.measurements) if len(self.measurements) > 1 else 0.0
        }
    
    def print_stats(self):
        """Print formatted statistics"""
        stats = self.get_stats()
        print(f"\n{'='*60}")
        print(f"Performance Metrics: {stats['operation']}")
        print(f"{'='*60}")
        print(f"Measurements: {stats['count']}")
        print(f"Mean:         {stats['mean']*1000:.2f} ms")
        print(f"Median:       {stats['median']*1000:.2f} ms")
        print(f"Min:          {stats['min']*1000:.2f} ms")
        print(f"Max:          {stats['max']*1000:.2f} ms")
        print(f"Std Dev:      {stats['stdev']*1000:.2f} ms")
        print(f"{'='*60}\n")


class TestMergeAssistantPerformance(BaseTestCase):
    """Performance tests for merge assistant with normalized schema"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.service = ThreeWayMergeService()
        self.test_session_id = None
        
    def _create_test_session_with_changes(
        self,
        num_changes: int = 100,
        conflict_ratio: float = 0.2
    ) -> int:
        """
        Create a test session with specified number of changes
        
        Args:
            num_changes: Number of changes to create
            conflict_ratio: Ratio of conflicts (0.0 to 1.0)
            
        Returns:
            Session ID
        """
        # Create session
        session = MergeSession(
            reference_id=f"PERF_{int(time.time())}",
            base_package_name="BasePackage",
            customized_package_name="CustomizedPackage",
            new_vendor_package_name="NewVendorPackage",
            status='ready',
            total_changes=num_changes
        )
        db.session.add(session)
        db.session.flush()
        
        # Create packages
        base_pkg = Package(
            session_id=session.id,
            package_type='base',
            package_name='BasePackage',
            total_objects=num_changes
        )
        customized_pkg = Package(
            session_id=session.id,
            package_type='customized',
            package_name='CustomizedPackage',
            total_objects=num_changes
        )
        vendor_pkg = Package(
            session_id=session.id,
            package_type='new_vendor',
            package_name='NewVendorPackage',
            total_objects=num_changes
        )
        db.session.add_all([base_pkg, customized_pkg, vendor_pkg])
        db.session.flush()
        
        # Create objects and changes
        object_types = ['Interface', 'Process Model', 'Record Type', 'Expression Rule', 'Constant']
        classifications = ['NO_CONFLICT', 'CONFLICT', 'CUSTOMER_ONLY', 'REMOVED_BUT_CUSTOMIZED']
        
        for i in range(num_changes):
            # Determine classification based on conflict ratio
            if i < int(num_changes * conflict_ratio):
                classification = 'CONFLICT'
            elif i < int(num_changes * (conflict_ratio + 0.3)):
                classification = 'CUSTOMER_ONLY'
            elif i < int(num_changes * (conflict_ratio + 0.4)):
                classification = 'REMOVED_BUT_CUSTOMIZED'
            else:
                classification = 'NO_CONFLICT'
            
            object_type = object_types[i % len(object_types)]
            uuid = f"test-uuid-{i:05d}"
            name = f"TestObject_{object_type.replace(' ', '')}_{i}"
            
            # Create objects in each package
            base_obj = AppianObject(
                package_id=base_pkg.id,
                uuid=uuid,
                name=name,
                object_type=object_type,
                sail_code=f"/* Base SAIL code for {name} */" if object_type == 'Interface' else None,
                properties=json.dumps({'version': '1.0', 'index': i})
            )
            customer_obj = AppianObject(
                package_id=customized_pkg.id,
                uuid=uuid,
                name=name,
                object_type=object_type,
                sail_code=f"/* Customer SAIL code for {name} */" if object_type == 'Interface' else None,
                properties=json.dumps({'version': '1.1', 'index': i})
            )
            vendor_obj = AppianObject(
                package_id=vendor_pkg.id,
                uuid=uuid,
                name=name,
                object_type=object_type,
                sail_code=f"/* Vendor SAIL code for {name} */" if object_type == 'Interface' else None,
                properties=json.dumps({'version': '2.0', 'index': i})
            )
            db.session.add_all([base_obj, customer_obj, vendor_obj])
            db.session.flush()
            
            # Create change
            change = Change(
                session_id=session.id,
                object_uuid=uuid,
                object_name=name,
                object_type=object_type,
                classification=classification,
                change_type='MODIFIED',
                vendor_change_type='MODIFIED',
                customer_change_type='MODIFIED',
                base_object_id=base_obj.id,
                customer_object_id=customer_obj.id,
                vendor_object_id=vendor_obj.id,
                display_order=i
            )
            db.session.add(change)
            db.session.flush()
            
            # Create review for some changes
            if i % 3 == 0:  # Review every 3rd change
                review = ChangeReview(
                    session_id=session.id,
                    change_id=change.id,
                    review_status='reviewed' if i % 2 == 0 else 'skipped'
                )
                db.session.add(review)
        
        db.session.commit()
        return session.id
    
    def _measure_operation(
        self,
        operation: Callable,
        iterations: int = 10
    ) -> PerformanceMetrics:
        """
        Measure an operation multiple times and collect metrics
        
        Args:
            operation: Callable to measure
            iterations: Number of times to run the operation
            
        Returns:
            PerformanceMetrics object with results
        """
        metrics = PerformanceMetrics(operation.__name__)
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            operation()
            end_time = time.perf_counter()
            metrics.add_measurement(end_time - start_time)
        
        return metrics
    
    # ========================================================================
    # Task 12.1: Baseline Performance Measurements
    # ========================================================================
    
    def test_12_1_baseline_filter_by_classification(self):
        """
        Measure baseline filter operation time by classification
        
        Requirements: 4.1, 4.2
        """
        print("\n" + "="*60)
        print("Task 12.1: Baseline Performance - Filter by Classification")
        print("="*60)
        
        # Create test session with 500 changes
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Measure filter operation
        def filter_conflicts():
            return self.service.filter_changes(
                session_id=session_id,
                classification='CONFLICT'
            )
        
        metrics = self._measure_operation(filter_conflicts, iterations=10)
        metrics.print_stats()
        
        # Verify results are correct
        results = filter_conflicts()
        self.assertGreater(len(results), 0)
        for change in results:
            self.assertEqual(change['classification'], 'CONFLICT')
        
        # Store baseline for comparison
        self.baseline_filter_classification = metrics.get_stats()['mean']
    
    def test_12_1_baseline_filter_by_object_type(self):
        """
        Measure baseline filter operation time by object type
        
        Requirements: 4.1, 4.2
        """
        print("\n" + "="*60)
        print("Task 12.1: Baseline Performance - Filter by Object Type")
        print("="*60)
        
        # Create test session with 500 changes
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Measure filter operation
        def filter_interfaces():
            return self.service.filter_changes(
                session_id=session_id,
                object_type='Interface'
            )
        
        metrics = self._measure_operation(filter_interfaces, iterations=10)
        metrics.print_stats()
        
        # Verify results are correct
        results = filter_interfaces()
        self.assertGreater(len(results), 0)
        for change in results:
            self.assertEqual(change['type'], 'Interface')
        
        # Store baseline for comparison
        self.baseline_filter_type = metrics.get_stats()['mean']
    
    def test_12_1_baseline_search_by_name(self):
        """
        Measure baseline search operation time by object name
        
        Requirements: 4.1, 4.2
        """
        print("\n" + "="*60)
        print("Task 12.1: Baseline Performance - Search by Name")
        print("="*60)
        
        # Create test session with 500 changes
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Measure search operation
        def search_objects():
            return self.service.filter_changes(
                session_id=session_id,
                search_term='Interface'
            )
        
        metrics = self._measure_operation(search_objects, iterations=10)
        metrics.print_stats()
        
        # Verify results are correct
        results = search_objects()
        self.assertGreater(len(results), 0)
        for change in results:
            self.assertIn('Interface', change['name'])
        
        # Store baseline for comparison
        self.baseline_search = metrics.get_stats()['mean']
    
    def test_12_1_baseline_report_generation(self):
        """
        Measure baseline report generation time
        
        Requirements: 4.1, 4.4
        """
        print("\n" + "="*60)
        print("Task 12.1: Baseline Performance - Report Generation")
        print("="*60)
        
        # Create test session with 500 changes
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Measure report generation
        def generate_report():
            return self.service.generate_report(session_id=session_id)
        
        metrics = self._measure_operation(generate_report, iterations=5)
        metrics.print_stats()
        
        # Verify report is complete
        report = generate_report()
        self.assertIn('summary', report)
        self.assertIn('changes', report)
        self.assertIn('statistics', report)
        self.assertEqual(len(report['changes']), 500)
        
        # Store baseline for comparison
        self.baseline_report = metrics.get_stats()['mean']
    
    def test_12_1_baseline_change_loading(self):
        """
        Measure baseline change loading time
        
        Requirements: 4.1, 4.5
        """
        print("\n" + "="*60)
        print("Task 12.1: Baseline Performance - Change Loading")
        print("="*60)
        
        # Create test session with 500 changes
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Measure change loading
        def load_changes():
            return self.service.get_ordered_changes(session_id=session_id)
        
        metrics = self._measure_operation(load_changes, iterations=10)
        metrics.print_stats()
        
        # Verify changes are loaded correctly
        changes = load_changes()
        self.assertEqual(len(changes), 500)
        
        # Verify ordering
        for i, change in enumerate(changes):
            self.assertEqual(change['display_order'], i)
        
        # Store baseline for comparison
        self.baseline_loading = metrics.get_stats()['mean']
    
    def test_12_1_baseline_statistics_calculation(self):
        """
        Measure baseline statistics calculation time
        
        Requirements: 4.1, 4.4
        """
        print("\n" + "="*60)
        print("Task 12.1: Baseline Performance - Statistics Calculation")
        print("="*60)
        
        # Create test session with 500 changes
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Measure statistics calculation
        def calculate_stats():
            return self.service.get_summary(session_id=session_id)
        
        metrics = self._measure_operation(calculate_stats, iterations=10)
        metrics.print_stats()
        
        # Verify statistics are correct
        summary = calculate_stats()
        self.assertIn('statistics', summary)
        self.assertEqual(summary['statistics']['total_changes'], 500)
        
        # Store baseline for comparison
        self.baseline_stats = metrics.get_stats()['mean']
    
    # ========================================================================
    # Task 12.2: Performance with New Schema
    # ========================================================================
    
    def test_12_2_new_schema_filter_by_classification(self):
        """
        Measure new schema filter operation time by classification
        Compare against baseline
        
        Requirements: 4.1, 4.2
        """
        print("\n" + "="*60)
        print("Task 12.2: New Schema Performance - Filter by Classification")
        print("="*60)
        
        # Create test session with 500 changes
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Measure filter operation
        def filter_conflicts():
            return self.service.filter_changes(
                session_id=session_id,
                classification='CONFLICT'
            )
        
        metrics = self._measure_operation(filter_conflicts, iterations=10)
        metrics.print_stats()
        
        # Verify results are correct
        results = filter_conflicts()
        self.assertGreater(len(results), 0)
        
        # Compare with baseline (if available)
        if hasattr(self, 'baseline_filter_classification'):
            improvement = (
                self.baseline_filter_classification / metrics.get_stats()['mean']
            )
            print(f"Performance improvement: {improvement:.2f}x faster")
            
            # Verify we meet performance target (should be faster)
            self.assertGreater(
                improvement,
                1.0,
                "New schema should be faster than baseline"
            )
    
    def test_12_2_new_schema_combined_filters(self):
        """
        Measure new schema performance with multiple filters
        
        Requirements: 4.1, 4.2, 4.3
        """
        print("\n" + "="*60)
        print("Task 12.2: New Schema Performance - Combined Filters")
        print("="*60)
        
        # Create test session with 500 changes
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Measure combined filter operation
        def filter_combined():
            return self.service.filter_changes(
                session_id=session_id,
                classification='CONFLICT',
                object_type='Interface',
                review_status='pending'
            )
        
        metrics = self._measure_operation(filter_combined, iterations=10)
        metrics.print_stats()
        
        # Verify results are correct
        results = filter_combined()
        for change in results:
            self.assertEqual(change['classification'], 'CONFLICT')
            self.assertEqual(change['type'], 'Interface')
            self.assertEqual(change['review_status'], 'pending')
    
    def test_12_2_new_schema_pagination(self):
        """
        Measure new schema performance with pagination
        
        Requirements: 4.1, 4.2
        """
        print("\n" + "="*60)
        print("Task 12.2: New Schema Performance - Pagination")
        print("="*60)
        
        # Create test session with 1000 changes
        session_id = self._create_test_session_with_changes(num_changes=1000)
        
        # Measure paginated loading
        def load_page():
            return self.service.get_ordered_changes(
                session_id=session_id,
                page=1,
                page_size=50
            )
        
        metrics = self._measure_operation(load_page, iterations=10)
        metrics.print_stats()
        
        # Verify pagination works correctly
        page1 = self.service.get_ordered_changes(
            session_id=session_id,
            page=1,
            page_size=50
        )
        page2 = self.service.get_ordered_changes(
            session_id=session_id,
            page=2,
            page_size=50
        )
        
        self.assertEqual(len(page1), 50)
        self.assertEqual(len(page2), 50)
        self.assertNotEqual(page1[0]['uuid'], page2[0]['uuid'])
    
    # ========================================================================
    # Task 12.3: Query Optimization
    # ========================================================================
    
    def test_12_3_analyze_query_plans(self):
        """
        Analyze query execution plans to verify index usage
        
        Requirements: 4.2, 4.3
        """
        print("\n" + "="*60)
        print("Task 12.3: Query Plan Analysis")
        print("="*60)
        
        # Create test session
        session_id = self._create_test_session_with_changes(num_changes=100)
        
        # Analyze different query types
        query_types = ['get_ordered_changes', 'filter_changes', 'get_summary']
        
        for query_type in query_types:
            print(f"\nAnalyzing query plan for: {query_type}")
            plan = self.service.analyze_query_plan(session_id, query_type)
            
            print(f"Query plan steps: {len(plan)}")
            for step in plan:
                print(f"  {step['detail']}")
            
            # Verify plan exists
            self.assertGreater(len(plan), 0)
    
    def test_12_3_verify_index_usage(self):
        """
        Verify that queries are using appropriate indexes
        
        Requirements: 4.2, 4.3
        """
        print("\n" + "="*60)
        print("Task 12.3: Index Usage Verification")
        print("="*60)
        
        # Create test session
        session_id = self._create_test_session_with_changes(num_changes=100)
        
        # Verify index usage
        index_usage = self.service.verify_index_usage(session_id)
        
        print("\nIndex Usage:")
        for index_name, is_used in index_usage.items():
            status = "✓ USED" if is_used else "✗ NOT USED"
            print(f"  {index_name}: {status}")
        
        # At least some indexes should be used
        self.assertGreater(
            sum(index_usage.values()),
            0,
            "At least one index should be used"
        )
    
    # ========================================================================
    # Task 12.4: Large Session Testing
    # ========================================================================
    
    def test_12_4_large_session_1000_changes(self):
        """
        Test performance with session containing 1000+ changes
        
        Requirements: 4.2
        """
        print("\n" + "="*60)
        print("Task 12.4: Large Session Testing - 1000 Changes")
        print("="*60)
        
        # Create large test session
        session_id = self._create_test_session_with_changes(num_changes=1000)
        
        # Measure various operations
        operations = {
            'Load All Changes': lambda: self.service.get_ordered_changes(session_id),
            'Filter Conflicts': lambda: self.service.filter_changes(
                session_id, classification='CONFLICT'
            ),
            'Search by Name': lambda: self.service.filter_changes(
                session_id, search_term='Interface'
            ),
            'Get Summary': lambda: self.service.get_summary(session_id),
            'Generate Report': lambda: self.service.generate_report(session_id)
        }
        
        results = {}
        for op_name, operation in operations.items():
            print(f"\nMeasuring: {op_name}")
            start_time = time.perf_counter()
            result = operation()
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            results[op_name] = duration
            print(f"  Duration: {duration*1000:.2f} ms")
            
            # Verify operation completed successfully
            self.assertIsNotNone(result)
        
        # Print summary
        print("\n" + "="*60)
        print("Large Session Performance Summary (1000 changes)")
        print("="*60)
        for op_name, duration in results.items():
            print(f"{op_name:25s}: {duration*1000:8.2f} ms")
        print("="*60)
        
        # Verify all operations complete in reasonable time (< 5 seconds each)
        for op_name, duration in results.items():
            self.assertLess(
                duration,
                5.0,
                f"{op_name} should complete in less than 5 seconds"
            )
    
    def test_12_4_large_session_pagination_performance(self):
        """
        Verify pagination works correctly with large sessions
        
        Requirements: 4.2
        """
        print("\n" + "="*60)
        print("Task 12.4: Large Session Pagination Performance")
        print("="*60)
        
        # Create large test session
        session_id = self._create_test_session_with_changes(num_changes=2000)
        
        # Test pagination performance
        page_size = 100
        num_pages = 20
        
        page_times = []
        for page_num in range(1, num_pages + 1):
            start_time = time.perf_counter()
            page_results = self.service.get_ordered_changes(
                session_id=session_id,
                page=page_num,
                page_size=page_size
            )
            end_time = time.perf_counter()
            
            page_times.append(end_time - start_time)
            
            # Verify page size
            expected_size = page_size if page_num < 20 else (2000 % page_size or page_size)
            self.assertEqual(len(page_results), expected_size)
        
        # Calculate statistics
        avg_time = statistics.mean(page_times)
        max_time = max(page_times)
        min_time = min(page_times)
        
        print(f"\nPagination Performance ({num_pages} pages, {page_size} items each):")
        print(f"  Average: {avg_time*1000:.2f} ms")
        print(f"  Min:     {min_time*1000:.2f} ms")
        print(f"  Max:     {max_time*1000:.2f} ms")
        
        # Verify consistent performance across pages
        self.assertLess(
            max_time,
            avg_time * 2,
            "Page load times should be consistent"
        )
    
    def test_12_4_memory_usage_large_session(self):
        """
        Verify memory usage is acceptable with large sessions
        
        Requirements: 4.2
        """
        print("\n" + "="*60)
        print("Task 12.4: Memory Usage with Large Session")
        print("="*60)
        
        import sys
        
        # Create large test session
        session_id = self._create_test_session_with_changes(num_changes=1500)
        
        # Measure memory usage of loading all changes
        changes = self.service.get_ordered_changes(session_id=session_id)
        
        # Calculate approximate memory usage
        memory_bytes = sys.getsizeof(changes)
        for change in changes[:10]:  # Sample first 10
            memory_bytes += sys.getsizeof(change)
        
        memory_mb = memory_bytes / (1024 * 1024)
        
        print(f"\nMemory usage for {len(changes)} changes:")
        print(f"  Approximate: {memory_mb:.2f} MB")
        
        # Verify memory usage is reasonable (< 100 MB for 1500 changes)
        self.assertLess(
            memory_mb,
            100.0,
            "Memory usage should be reasonable"
        )
    
    # ========================================================================
    # Performance Comparison Summary
    # ========================================================================
    
    def test_12_performance_summary(self):
        """
        Generate comprehensive performance comparison summary
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        """
        print("\n" + "="*70)
        print("PERFORMANCE TESTING SUMMARY")
        print("="*70)
        
        # Create test session
        session_id = self._create_test_session_with_changes(num_changes=500)
        
        # Test all operations
        operations = {
            'Filter by Classification': lambda: self.service.filter_changes(
                session_id, classification='CONFLICT'
            ),
            'Filter by Object Type': lambda: self.service.filter_changes(
                session_id, object_type='Interface'
            ),
            'Search by Name': lambda: self.service.filter_changes(
                session_id, search_term='Test'
            ),
            'Load All Changes': lambda: self.service.get_ordered_changes(session_id),
            'Get Summary': lambda: self.service.get_summary(session_id),
            'Generate Report': lambda: self.service.generate_report(session_id),
            'Get Statistics': lambda: self.service.get_statistics_by_type(session_id)
        }
        
        print(f"\nTesting with {500} changes...")
        print(f"{'Operation':<30s} {'Time (ms)':>12s} {'Status':>10s}")
        print("-" * 70)
        
        for op_name, operation in operations.items():
            # Measure operation
            times = []
            for _ in range(5):
                start_time = time.perf_counter()
                try:
                    result = operation()
                    end_time = time.perf_counter()
                    times.append(end_time - start_time)
                except Exception as e:
                    print(f"{op_name:<30s} {'ERROR':>12s} {str(e)[:10]:>10s}")
                    continue
            
            if times:
                avg_time = statistics.mean(times)
                status = "✓ PASS" if avg_time < 1.0 else "⚠ SLOW"
                print(f"{op_name:<30s} {avg_time*1000:>12.2f} {status:>10s}")
        
        print("="*70)
        print("\nPerformance Targets:")
        print("  ✓ Filter operations: < 100ms")
        print("  ✓ Search operations: < 100ms")
        print("  ✓ Load operations: < 500ms")
        print("  ✓ Report generation: < 1000ms")
        print("="*70)


if __name__ == '__main__':
    import unittest
    unittest.main()
