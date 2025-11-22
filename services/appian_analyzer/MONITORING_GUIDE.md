# Process Model Enhancement Monitoring Guide

## Overview

The monitoring system tracks performance metrics, failure rates, and generates alerts when issues are detected in process model parsing, comparison, and visualization operations.

## Features

- **Real-time Metrics Collection** - Tracks parsing time, comparison time, failure rates
- **Threshold-Based Alerting** - Automatic alerts when metrics exceed configured thresholds
- **Health Status Monitoring** - Overall system health with percentile metrics
- **Flexible Alert Handlers** - Extensible system for email, Slack, or custom notifications
- **Sliding Window Analytics** - Tracks recent metrics for trend analysis

## Quick Start

### Basic Usage

```python
from services.appian_analyzer.monitoring_config import get_monitoring_service
import time

# Get monitoring service
monitor = get_monitoring_service()

# Record a parsing attempt
start_time = time.time()
try:
    # ... parsing logic ...
    success = True
except Exception as e:
    success = False
finally:
    parsing_time = time.time() - start_time
    monitor.record_parsing_attempt(
        process_model_name="MyProcessModel",
        success=success,
        parsing_time=parsing_time,
        node_count=25
    )

# Check health status
health = monitor.get_health_status()
print(f"System status: {health['status']}")
print(f"Parsing failure rate: {health['failure_rates']['parsing']}%")
```

### Adding Custom Alert Handlers

```python
from services.appian_analyzer.monitoring_config import (
    get_monitoring_service,
    Alert,
    AlertLevel
)

def custom_alert_handler(alert: Alert):
    """Custom handler for alerts"""
    if alert.level == AlertLevel.CRITICAL:
        # Send urgent notification
        send_urgent_notification(alert.message)
    elif alert.level == AlertLevel.ERROR:
        # Log to error tracking system
        log_to_error_tracker(alert)

# Register the handler
monitor = get_monitoring_service()
monitor.add_alert_handler(custom_alert_handler)
```

## Metrics Tracked

### Parsing Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `parsing_success` | Number of successful parsing attempts | count |
| `parsing_failure` | Number of failed parsing attempts | count |
| `parsing_time` | Time taken to parse process model | seconds |
| `nodes_parsed` | Number of nodes successfully parsed | count |
| `parsing_failure_rate` | Percentage of parsing attempts that failed | percentage |

### Comparison Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `comparison_success` | Number of successful comparisons | count |
| `comparison_failure` | Number of failed comparisons | count |
| `comparison_time` | Time taken to compare process models | seconds |
| `changes_detected` | Number of changes found | count |
| `comparison_failure_rate` | Percentage of comparisons that failed | percentage |

### UUID Resolution Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `uuid_resolution_success` | Number of successful UUID resolutions | count |
| `uuid_resolution_failure` | Number of failed UUID resolutions | count |
| `uuid_resolution_failure_rate` | Percentage of resolutions that failed | percentage |

### Diagram Generation Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `diagram_generation_success` | Number of successful diagram generations | count |
| `diagram_generation_failure` | Number of failed diagram generations | count |
| `diagram_generation_time` | Time taken to generate diagram | seconds |
| `diagram_nodes` | Number of nodes in generated diagram | count |
| `diagram_edges` | Number of edges in generated diagram | count |

## Default Thresholds

### Parsing Thresholds

| Threshold | Warning | Error | Critical |
|-----------|---------|-------|----------|
| Failure Rate | 5% | 10% | 25% |
| Parsing Time | 5s | 10s | 30s |

### Comparison Thresholds

| Threshold | Warning | Error | Critical |
|-----------|---------|-------|----------|
| Failure Rate | 5% | 10% | 25% |
| Comparison Time | 10s | 30s | 60s |

### Diagram Generation Thresholds

| Threshold | Warning | Error | Critical |
|-----------|---------|-------|----------|
| Failure Rate | 5% | 10% | 25% |
| Generation Time | 2s | 5s | 10s |

### UUID Resolution Thresholds

| Threshold | Warning | Error | Critical |
|-----------|---------|-------|----------|
| Failure Rate | 10% | 25% | 50% |

## Customizing Thresholds

```python
from services.appian_analyzer.monitoring_config import (
    get_monitoring_service,
    MetricThreshold
)

monitor = get_monitoring_service()

# Add custom threshold
custom_threshold = MetricThreshold(
    metric_name='parsing_time',
    warning_threshold=3.0,   # 3 seconds
    error_threshold=7.0,     # 7 seconds
    critical_threshold=15.0,  # 15 seconds
    comparison='gt'  # Greater than
)

monitor.add_threshold(custom_threshold)
```

## Alert Levels

### INFO
- Informational messages
- No action required
- Used for tracking normal operations

### WARNING
- Potential issues detected
- Monitor closely
- May require investigation

### ERROR
- Significant issues detected
- Action recommended
- May impact functionality

### CRITICAL
- Severe issues detected
- Immediate action required
- System functionality impaired

## Integration Examples

### With ProcessModelParser

```python
from services.appian_analyzer.parsers import ProcessModelParser
from services.appian_analyzer.monitoring_config import get_monitoring_service
import time

class MonitoredProcessModelParser(ProcessModelParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitor = get_monitoring_service()
    
    def parse(self, xml_content, object_lookup):
        start_time = time.time()
        success = False
        node_count = 0
        
        try:
            result = super().parse(xml_content, object_lookup)
            success = True
            node_count = len(result.get('nodes', []))
            return result
        except Exception as e:
            raise
        finally:
            parsing_time = time.time() - start_time
            self.monitor.record_parsing_attempt(
                process_model_name=self.current_pm_name,
                success=success,
                parsing_time=parsing_time,
                node_count=node_count
            )
```

### With NodeComparator

```python
from services.appian_analyzer.process_model_enhancement import NodeComparator
from services.appian_analyzer.monitoring_config import get_monitoring_service
import time

class MonitoredNodeComparator(NodeComparator):
    def __init__(self):
        super().__init__()
        self.monitor = get_monitoring_service()
    
    def compare_nodes(self, base_nodes, target_nodes):
        start_time = time.time()
        success = False
        total_changes = 0
        
        try:
            result = super().compare_nodes(base_nodes, target_nodes)
            success = True
            total_changes = (
                len(result['added']) +
                len(result['removed']) +
                len(result['modified'])
            )
            return result
        except Exception as e:
            raise
        finally:
            comparison_time = time.time() - start_time
            self.monitor.record_comparison_attempt(
                process_model_name="comparison",
                success=success,
                comparison_time=comparison_time,
                total_changes=total_changes
            )
```

### With FlowDiagramGenerator

```python
from services.appian_analyzer.process_model_enhancement import FlowDiagramGenerator
from services.appian_analyzer.monitoring_config import get_monitoring_service
import time

class MonitoredFlowDiagramGenerator(FlowDiagramGenerator):
    def __init__(self):
        super().__init__()
        self.monitor = get_monitoring_service()
    
    def generate_diagram_data(self, nodes, flows, flow_graph):
        start_time = time.time()
        success = False
        node_count = len(nodes)
        edge_count = len(flows)
        
        try:
            result = super().generate_diagram_data(nodes, flows, flow_graph)
            success = True
            return result
        except Exception as e:
            raise
        finally:
            generation_time = time.time() - start_time
            self.monitor.record_diagram_generation(
                process_model_name="diagram",
                success=success,
                generation_time=generation_time,
                node_count=node_count,
                edge_count=edge_count
            )
```

## Health Status API

### Get Current Health

```python
monitor = get_monitoring_service()
health = monitor.get_health_status()

# Example response:
{
    'status': 'healthy',
    'failure_rates': {
        'parsing': 2.5,        # 2.5% failure rate
        'comparison': 1.0,     # 1.0% failure rate
        'uuid_resolution': 5.0  # 5.0% failure rate
    },
    'average_times': {
        'parsing': 3.2,        # 3.2 seconds average
        'comparison': 8.5      # 8.5 seconds average
    },
    'p95_times': {
        'parsing': 6.1,        # 95th percentile: 6.1 seconds
        'comparison': 15.3     # 95th percentile: 15.3 seconds
    },
    'timestamp': '2024-11-22T10:30:00'
}
```

### Interpreting Health Status

**Status Values:**
- `healthy` - All metrics within normal ranges
- `degraded` - Some metrics approaching thresholds
- `unhealthy` - Multiple metrics exceeding thresholds

**Failure Rates:**
- < 5% - Normal operation
- 5-10% - Monitor closely
- 10-25% - Investigation recommended
- > 25% - Immediate action required

**Response Times:**
- Average times show typical performance
- P95 times show worst-case scenarios (95% of requests faster than this)

## Alert Handler Examples

### Email Alert Handler

```python
import smtplib
from email.mime.text import MIMEText
from services.appian_analyzer.monitoring_config import Alert, AlertLevel

def email_alert_handler(alert: Alert):
    """Send email alerts for ERROR and CRITICAL levels"""
    if alert.level not in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
        return
    
    # Configure email settings
    smtp_server = "smtp.example.com"
    smtp_port = 587
    sender = "alerts@example.com"
    recipients = ["admin@example.com"]
    
    # Create message
    subject = f"[{alert.level.value}] Process Model Alert: {alert.metric_name}"
    body = f"""
    Alert Level: {alert.level.value}
    Metric: {alert.metric_name}
    Current Value: {alert.current_value:.2f}
    Threshold: {alert.threshold_value:.2f}
    Message: {alert.message}
    Timestamp: {alert.timestamp.isoformat()}
    """
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    
    # Send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, "password")
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email alert: {e}")

# Register handler
monitor = get_monitoring_service()
monitor.add_alert_handler(email_alert_handler)
```

### Slack Alert Handler

```python
import requests
from services.appian_analyzer.monitoring_config import Alert, AlertLevel

def slack_alert_handler(alert: Alert):
    """Post alerts to Slack channel"""
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    # Color code by severity
    colors = {
        AlertLevel.INFO: "#36a64f",      # Green
        AlertLevel.WARNING: "#ff9900",   # Orange
        AlertLevel.ERROR: "#ff0000",     # Red
        AlertLevel.CRITICAL: "#8b0000"   # Dark red
    }
    
    # Create Slack message
    message = {
        "attachments": [{
            "color": colors.get(alert.level, "#808080"),
            "title": f"{alert.level.value}: {alert.metric_name}",
            "text": alert.message,
            "fields": [
                {
                    "title": "Current Value",
                    "value": f"{alert.current_value:.2f}",
                    "short": True
                },
                {
                    "title": "Threshold",
                    "value": f"{alert.threshold_value:.2f}",
                    "short": True
                },
                {
                    "title": "Timestamp",
                    "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "short": False
                }
            ]
        }]
    }
    
    # Post to Slack
    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to post to Slack: {e}")

# Register handler
monitor = get_monitoring_service()
monitor.add_alert_handler(slack_alert_handler)
```

### Database Alert Handler

```python
from datetime import datetime
from services.appian_analyzer.monitoring_config import Alert

def database_alert_handler(alert: Alert):
    """Store alerts in database for historical analysis"""
    from models import db, AlertLog  # Your database models
    
    try:
        alert_log = AlertLog(
            level=alert.level.value,
            metric_name=alert.metric_name,
            current_value=alert.current_value,
            threshold_value=alert.threshold_value,
            message=alert.message,
            timestamp=alert.timestamp
        )
        db.session.add(alert_log)
        db.session.commit()
    except Exception as e:
        print(f"Failed to store alert in database: {e}")
        db.session.rollback()

# Register handler
monitor = get_monitoring_service()
monitor.add_alert_handler(database_alert_handler)
```

## Troubleshooting

### High Failure Rates

**Symptom:** Parsing or comparison failure rate exceeds thresholds

**Possible Causes:**
- Malformed XML in process models
- Missing objects in object lookup
- Memory issues with large process models
- Network issues (if fetching external data)

**Solutions:**
1. Check logs for specific error messages
2. Verify XML structure of failing process models
3. Ensure object lookup is complete
4. Increase memory allocation if needed
5. Add retry logic for transient failures

### Slow Performance

**Symptom:** Parsing or comparison time exceeds thresholds

**Possible Causes:**
- Very large process models (100+ nodes)
- Complex SAIL expressions requiring formatting
- Inefficient UUID resolution
- Database query performance

**Solutions:**
1. Profile code to identify bottlenecks
2. Optimize UUID resolution with caching
3. Batch database queries
4. Consider pagination for large process models
5. Implement lazy loading for diagram generation

### Missing Metrics

**Symptom:** Health status shows None for some metrics

**Possible Causes:**
- No operations recorded yet
- Time window too narrow
- Metrics not being recorded properly

**Solutions:**
1. Verify monitoring code is integrated
2. Check that record_* methods are being called
3. Widen time window for analysis
4. Review logs for recording errors

## Best Practices

1. **Always Record Metrics** - Wrap all parsing, comparison, and diagram operations with monitoring
2. **Use Appropriate Time Windows** - 1 hour for real-time, 24 hours for trends
3. **Set Realistic Thresholds** - Based on your actual performance characteristics
4. **Test Alert Handlers** - Verify they work before relying on them
5. **Monitor the Monitors** - Ensure monitoring system itself is healthy
6. **Review Metrics Regularly** - Look for trends and patterns
7. **Adjust Thresholds** - As system improves, tighten thresholds
8. **Document Incidents** - Track what caused alerts and how they were resolved

## Performance Targets

### Recommended Targets

| Operation | Target | Acceptable | Poor |
|-----------|--------|------------|------|
| Parse small PM (< 10 nodes) | < 1s | < 2s | > 2s |
| Parse medium PM (10-50 nodes) | < 3s | < 5s | > 5s |
| Parse large PM (50+ nodes) | < 5s | < 10s | > 10s |
| Compare PMs | < 5s | < 10s | > 10s |
| Generate diagram | < 1s | < 2s | > 2s |
| UUID resolution | < 10ms | < 50ms | > 50ms |

### Failure Rate Targets

| Operation | Target | Acceptable | Poor |
|-----------|--------|------------|------|
| Parsing | < 1% | < 5% | > 5% |
| Comparison | < 1% | < 5% | > 5% |
| UUID Resolution | < 5% | < 10% | > 10% |
| Diagram Generation | < 1% | < 5% | > 5% |

## Support

For issues with monitoring:
1. Check logs at `logs/appian_analyzer.log`
2. Verify monitoring service is initialized
3. Review threshold configurations
4. Test alert handlers independently
5. Contact system administrator

---

**Version:** 1.0  
**Last Updated:** November 2024  
**Applies To:** NexusGen Process Model Enhancement v1.0+
