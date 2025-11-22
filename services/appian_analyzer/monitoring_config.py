"""
Monitoring Configuration for Process Model Enhancement

This module provides monitoring and alerting capabilities for process model
parsing and comparison operations. It tracks failure rates, performance
metrics, and can trigger alerts when thresholds are exceeded.
"""
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class MetricThreshold:
    """
    Threshold configuration for a metric
    
    Attributes:
        metric_name: Name of the metric to monitor
        warning_threshold: Value that triggers a warning alert
        error_threshold: Value that triggers an error alert
        critical_threshold: Value that triggers a critical alert
        comparison: Comparison operator ('gt', 'lt', 'eq', 'gte', 'lte')
    """
    metric_name: str
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    comparison: str = 'gt'  # 'gt', 'lt', 'eq', 'gte', 'lte'
    
    def check_threshold(self, value: float) -> Optional[AlertLevel]:
        """
        Check if value exceeds any threshold
        
        Args:
            value: Current metric value
            
        Returns:
            AlertLevel if threshold exceeded, None otherwise
        """
        if self.comparison == 'gt':
            if value > self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value > self.error_threshold:
                return AlertLevel.ERROR
            elif value > self.warning_threshold:
                return AlertLevel.WARNING
        elif self.comparison == 'lt':
            if value < self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value < self.error_threshold:
                return AlertLevel.ERROR
            elif value < self.warning_threshold:
                return AlertLevel.WARNING
        elif self.comparison == 'gte':
            if value >= self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value >= self.error_threshold:
                return AlertLevel.ERROR
            elif value >= self.warning_threshold:
                return AlertLevel.WARNING
        elif self.comparison == 'lte':
            if value <= self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value <= self.error_threshold:
                return AlertLevel.ERROR
            elif value <= self.warning_threshold:
                return AlertLevel.WARNING
        
        return None


@dataclass
class Alert:
    """
    Alert notification
    
    Attributes:
        level: Severity level of the alert
        metric_name: Name of the metric that triggered the alert
        current_value: Current value of the metric
        threshold_value: Threshold that was exceeded
        message: Human-readable alert message
        timestamp: When the alert was generated
    """
    level: AlertLevel
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """
    Collects and tracks metrics over time
    
    This class maintains a sliding window of recent metrics and can
    calculate statistics like average, min, max, and failure rates.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize metrics collector
        
        Args:
            window_size: Number of recent metrics to keep in memory
        """
        self.window_size = window_size
        self.metrics: Dict[str, deque] = {}
        self.logger = logging.getLogger(__name__)
    
    def record_metric(self, metric_name: str, value: float, timestamp: datetime = None):
        """
        Record a metric value
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: When the metric was recorded (defaults to now)
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = deque(maxlen=self.window_size)
        
        if timestamp is None:
            timestamp = datetime.now()
        
        self.metrics[metric_name].append({
            'value': value,
            'timestamp': timestamp
        })
    
    def get_average(self, metric_name: str, time_window: timedelta = None) -> Optional[float]:
        """
        Calculate average value for a metric
        
        Args:
            metric_name: Name of the metric
            time_window: Optional time window to consider (e.g., last hour)
            
        Returns:
            Average value or None if no data
        """
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return None
        
        values = self._get_values_in_window(metric_name, time_window)
        
        if not values:
            return None
        
        return sum(values) / len(values)
    
    def get_failure_rate(
        self, 
        success_metric: str, 
        failure_metric: str,
        time_window: timedelta = None
    ) -> Optional[float]:
        """
        Calculate failure rate as percentage
        
        Args:
            success_metric: Name of success count metric
            failure_metric: Name of failure count metric
            time_window: Optional time window to consider
            
        Returns:
            Failure rate as percentage (0-100) or None if no data
        """
        success_values = self._get_values_in_window(success_metric, time_window)
        failure_values = self._get_values_in_window(failure_metric, time_window)
        
        if not success_values and not failure_values:
            return None
        
        total_success = sum(success_values) if success_values else 0
        total_failure = sum(failure_values) if failure_values else 0
        total = total_success + total_failure
        
        if total == 0:
            return 0.0
        
        return (total_failure / total) * 100
    
    def get_percentile(
        self, 
        metric_name: str, 
        percentile: float,
        time_window: timedelta = None
    ) -> Optional[float]:
        """
        Calculate percentile value for a metric
        
        Args:
            metric_name: Name of the metric
            percentile: Percentile to calculate (0-100)
            time_window: Optional time window to consider
            
        Returns:
            Percentile value or None if no data
        """
        values = self._get_values_in_window(metric_name, time_window)
        
        if not values:
            return None
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    def _get_values_in_window(
        self, 
        metric_name: str, 
        time_window: timedelta = None
    ) -> List[float]:
        """
        Get metric values within a time window
        
        Args:
            metric_name: Name of the metric
            time_window: Time window to consider (None = all values)
            
        Returns:
            List of metric values
        """
        if metric_name not in self.metrics:
            return []
        
        if time_window is None:
            return [entry['value'] for entry in self.metrics[metric_name]]
        
        cutoff_time = datetime.now() - time_window
        return [
            entry['value'] 
            for entry in self.metrics[metric_name]
            if entry['timestamp'] >= cutoff_time
        ]


class MonitoringService:
    """
    Monitoring service for process model operations
    
    This service tracks metrics, checks thresholds, and generates alerts
    when issues are detected.
    """
    
    def __init__(self):
        """Initialize monitoring service"""
        self.metrics_collector = MetricsCollector(window_size=1000)
        self.thresholds: Dict[str, MetricThreshold] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.logger = logging.getLogger(__name__)
        
        # Set up default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Configure default monitoring thresholds"""
        # Failure rate thresholds (percentage)
        self.add_threshold(MetricThreshold(
            metric_name='parsing_failure_rate',
            warning_threshold=5.0,  # 5% failure rate
            error_threshold=10.0,   # 10% failure rate
            critical_threshold=25.0,  # 25% failure rate
            comparison='gte'
        ))
        
        # Parsing time thresholds (seconds)
        self.add_threshold(MetricThreshold(
            metric_name='parsing_time',
            warning_threshold=5.0,   # 5 seconds
            error_threshold=10.0,    # 10 seconds
            critical_threshold=30.0,  # 30 seconds
            comparison='gt'
        ))
        
        # Comparison time thresholds (seconds)
        self.add_threshold(MetricThreshold(
            metric_name='comparison_time',
            warning_threshold=10.0,  # 10 seconds
            error_threshold=30.0,    # 30 seconds
            critical_threshold=60.0,  # 60 seconds
            comparison='gt'
        ))
        
        # Diagram generation time thresholds (seconds)
        self.add_threshold(MetricThreshold(
            metric_name='diagram_generation_time',
            warning_threshold=2.0,   # 2 seconds
            error_threshold=5.0,     # 5 seconds
            critical_threshold=10.0,  # 10 seconds
            comparison='gt'
        ))
        
        # UUID resolution failure rate thresholds (percentage)
        self.add_threshold(MetricThreshold(
            metric_name='uuid_resolution_failure_rate',
            warning_threshold=10.0,  # 10% failure rate
            error_threshold=25.0,    # 25% failure rate
            critical_threshold=50.0,  # 50% failure rate
            comparison='gte'
        ))
    
    def add_threshold(self, threshold: MetricThreshold):
        """
        Add a monitoring threshold
        
        Args:
            threshold: Threshold configuration
        """
        self.thresholds[threshold.metric_name] = threshold
        self.logger.info(f"Added threshold for {threshold.metric_name}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """
        Add an alert handler function
        
        Alert handlers are called when alerts are generated. They can
        send emails, post to Slack, write to logs, etc.
        
        Args:
            handler: Function that takes an Alert and handles it
        """
        self.alert_handlers.append(handler)
    
    def record_parsing_attempt(
        self, 
        process_model_name: str,
        success: bool,
        parsing_time: float,
        node_count: int = 0
    ):
        """
        Record a process model parsing attempt
        
        Args:
            process_model_name: Name of the process model
            success: Whether parsing succeeded
            parsing_time: Time taken to parse in seconds
            node_count: Number of nodes parsed
        """
        # Record success/failure
        if success:
            self.metrics_collector.record_metric('parsing_success', 1)
        else:
            self.metrics_collector.record_metric('parsing_failure', 1)
        
        # Record parsing time
        self.metrics_collector.record_metric('parsing_time', parsing_time)
        
        # Record node count
        if node_count > 0:
            self.metrics_collector.record_metric('nodes_parsed', node_count)
        
        # Check thresholds
        self._check_parsing_thresholds(process_model_name, parsing_time)
    
    def record_comparison_attempt(
        self,
        process_model_name: str,
        success: bool,
        comparison_time: float,
        total_changes: int = 0
    ):
        """
        Record a process model comparison attempt
        
        Args:
            process_model_name: Name of the process model
            success: Whether comparison succeeded
            comparison_time: Time taken to compare in seconds
            total_changes: Number of changes detected
        """
        # Record success/failure
        if success:
            self.metrics_collector.record_metric('comparison_success', 1)
        else:
            self.metrics_collector.record_metric('comparison_failure', 1)
        
        # Record comparison time
        self.metrics_collector.record_metric('comparison_time', comparison_time)
        
        # Record change count
        if total_changes > 0:
            self.metrics_collector.record_metric('changes_detected', total_changes)
        
        # Check thresholds
        self._check_comparison_thresholds(process_model_name, comparison_time)
    
    def record_uuid_resolution(self, success: bool):
        """
        Record a UUID resolution attempt
        
        Args:
            success: Whether resolution succeeded
        """
        if success:
            self.metrics_collector.record_metric('uuid_resolution_success', 1)
        else:
            self.metrics_collector.record_metric('uuid_resolution_failure', 1)
    
    def record_diagram_generation(
        self,
        process_model_name: str,
        success: bool,
        generation_time: float,
        node_count: int = 0,
        edge_count: int = 0
    ):
        """
        Record a diagram generation attempt
        
        Args:
            process_model_name: Name of the process model
            success: Whether generation succeeded
            generation_time: Time taken to generate in seconds
            node_count: Number of nodes in diagram
            edge_count: Number of edges in diagram
        """
        # Record success/failure
        if success:
            self.metrics_collector.record_metric('diagram_generation_success', 1)
        else:
            self.metrics_collector.record_metric('diagram_generation_failure', 1)
        
        # Record generation time
        self.metrics_collector.record_metric('diagram_generation_time', generation_time)
        
        # Record diagram size
        if node_count > 0:
            self.metrics_collector.record_metric('diagram_nodes', node_count)
        if edge_count > 0:
            self.metrics_collector.record_metric('diagram_edges', edge_count)
        
        # Check thresholds
        self._check_diagram_thresholds(process_model_name, generation_time)
    
    def _check_parsing_thresholds(self, process_model_name: str, parsing_time: float):
        """Check parsing-related thresholds"""
        # Check parsing time
        if 'parsing_time' in self.thresholds:
            alert_level = self.thresholds['parsing_time'].check_threshold(parsing_time)
            if alert_level:
                self._generate_alert(
                    alert_level,
                    'parsing_time',
                    parsing_time,
                    self.thresholds['parsing_time'],
                    f"Parsing time for {process_model_name} exceeded threshold"
                )
        
        # Check failure rate
        failure_rate = self.metrics_collector.get_failure_rate(
            'parsing_success',
            'parsing_failure',
            time_window=timedelta(hours=1)
        )
        
        if failure_rate is not None and 'parsing_failure_rate' in self.thresholds:
            alert_level = self.thresholds['parsing_failure_rate'].check_threshold(failure_rate)
            if alert_level:
                self._generate_alert(
                    alert_level,
                    'parsing_failure_rate',
                    failure_rate,
                    self.thresholds['parsing_failure_rate'],
                    f"Parsing failure rate exceeded threshold: {failure_rate:.1f}%"
                )
    
    def _check_comparison_thresholds(self, process_model_name: str, comparison_time: float):
        """Check comparison-related thresholds"""
        if 'comparison_time' in self.thresholds:
            alert_level = self.thresholds['comparison_time'].check_threshold(comparison_time)
            if alert_level:
                self._generate_alert(
                    alert_level,
                    'comparison_time',
                    comparison_time,
                    self.thresholds['comparison_time'],
                    f"Comparison time for {process_model_name} exceeded threshold"
                )
    
    def _check_diagram_thresholds(self, process_model_name: str, generation_time: float):
        """Check diagram generation thresholds"""
        if 'diagram_generation_time' in self.thresholds:
            alert_level = self.thresholds['diagram_generation_time'].check_threshold(generation_time)
            if alert_level:
                self._generate_alert(
                    alert_level,
                    'diagram_generation_time',
                    generation_time,
                    self.thresholds['diagram_generation_time'],
                    f"Diagram generation time for {process_model_name} exceeded threshold"
                )
    
    def _generate_alert(
        self,
        level: AlertLevel,
        metric_name: str,
        current_value: float,
        threshold: MetricThreshold,
        message: str
    ):
        """
        Generate and dispatch an alert
        
        Args:
            level: Alert severity level
            metric_name: Name of the metric
            current_value: Current metric value
            threshold: Threshold configuration
            message: Alert message
        """
        # Determine which threshold was exceeded
        if level == AlertLevel.CRITICAL:
            threshold_value = threshold.critical_threshold
        elif level == AlertLevel.ERROR:
            threshold_value = threshold.error_threshold
        else:
            threshold_value = threshold.warning_threshold
        
        alert = Alert(
            level=level,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message
        )
        
        # Log the alert
        log_method = {
            AlertLevel.INFO: self.logger.info,
            AlertLevel.WARNING: self.logger.warning,
            AlertLevel.ERROR: self.logger.error,
            AlertLevel.CRITICAL: self.logger.critical
        }[level]
        
        log_method(
            f"ALERT [{level.value}] {message} "
            f"(current: {current_value:.2f}, threshold: {threshold_value:.2f})"
        )
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}", exc_info=True)
    
    def get_health_status(self) -> Dict[str, any]:
        """
        Get current health status of process model operations
        
        Returns:
            Dictionary with health metrics and status
        """
        # Calculate failure rates
        parsing_failure_rate = self.metrics_collector.get_failure_rate(
            'parsing_success',
            'parsing_failure',
            time_window=timedelta(hours=1)
        )
        
        comparison_failure_rate = self.metrics_collector.get_failure_rate(
            'comparison_success',
            'comparison_failure',
            time_window=timedelta(hours=1)
        )
        
        uuid_resolution_failure_rate = self.metrics_collector.get_failure_rate(
            'uuid_resolution_success',
            'uuid_resolution_failure',
            time_window=timedelta(hours=1)
        )
        
        # Calculate average times
        avg_parsing_time = self.metrics_collector.get_average(
            'parsing_time',
            time_window=timedelta(hours=1)
        )
        
        avg_comparison_time = self.metrics_collector.get_average(
            'comparison_time',
            time_window=timedelta(hours=1)
        )
        
        # Calculate percentiles
        p95_parsing_time = self.metrics_collector.get_percentile(
            'parsing_time',
            95,
            time_window=timedelta(hours=1)
        )
        
        p95_comparison_time = self.metrics_collector.get_percentile(
            'comparison_time',
            95,
            time_window=timedelta(hours=1)
        )
        
        return {
            'status': 'healthy',  # Could be 'healthy', 'degraded', 'unhealthy'
            'failure_rates': {
                'parsing': parsing_failure_rate,
                'comparison': comparison_failure_rate,
                'uuid_resolution': uuid_resolution_failure_rate
            },
            'average_times': {
                'parsing': avg_parsing_time,
                'comparison': avg_comparison_time
            },
            'p95_times': {
                'parsing': p95_parsing_time,
                'comparison': p95_comparison_time
            },
            'timestamp': datetime.now().isoformat()
        }


# Global monitoring service instance
_monitoring_service = None


def get_monitoring_service() -> MonitoringService:
    """Get or create global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


# Example alert handlers

def log_alert_handler(alert: Alert):
    """
    Simple alert handler that logs to file
    
    Args:
        alert: Alert to handle
    """
    logger = logging.getLogger('alerts')
    logger.log(
        logging.getLevelName(alert.level.value),
        f"[{alert.timestamp.isoformat()}] {alert.message} "
        f"(metric: {alert.metric_name}, value: {alert.current_value:.2f}, "
        f"threshold: {alert.threshold_value:.2f})"
    )


def email_alert_handler(alert: Alert):
    """
    Alert handler that sends emails (placeholder)
    
    Args:
        alert: Alert to handle
    """
    # TODO: Implement email sending
    # This would integrate with your email service
    pass


def slack_alert_handler(alert: Alert):
    """
    Alert handler that posts to Slack (placeholder)
    
    Args:
        alert: Alert to handle
    """
    # TODO: Implement Slack integration
    # This would post to a Slack channel
    pass
