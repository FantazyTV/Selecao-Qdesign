# Pipeline Monitoring System

Comprehensive monitoring for pipeline health, data quality, and modality balance.

## Overview

The monitoring system tracks three key aspects of pipeline operation:

### 1. **Health Monitoring** (`HealthMonitor`)
Tracks pipeline operational health and data freshness:

- **Ingestion Success Rate**: Percentage of successful ingestion attempts
- **Failed Sources**: Identifies sources with high failure rates
- **Data Freshness**: Hours since last successful ingestion (alerts if stale)
- **Source Details**: Per-source success rates and recent errors
- **Thresholds**:
  - ✅ Success rate: 90%+ (warning below 95%)
  - ✅ Data freshness: < 168 hours old (7 days)
  - ✅ Monitor individual source health

### 2. **Quality Monitoring** (`QualityMonitor`)
Tracks data quality and consistency:

- **Duplicate Detection**: Identifies duplicate records by content hash
- **Missing Metadata**: Tracks completeness of required fields (title, source, date, etc.)
- **Embedding Consistency**: 
  - Validates embedding dimensions
  - Checks for NaN/Inf values
  - Tracks norm distributions
- **Error Rate**: Percentage of records with ingestion errors
- **Thresholds**:
  - ✅ Error rate: < 5% (warning above 1%)
  - ✅ Duplicate rate: < 5% (warning above 1%)
  - ✅ Metadata completeness: 80%+ (warning below 90%)

### 3. **Balance Monitoring** (`BalanceMonitor`)
Tracks modality distribution and diversity:

- **Modality Distribution**: 
  - Images, Text, Sequences, Structures
  - Ideal balance: 25% each
  - Tolerance: ±10%
- **Source Diversity**: Number of sources per modality
- **Gini Coefficient**: Measures distribution inequality (0=perfect balance, 1=complete imbalance)
- **Collection Distribution**: Breakdown by data collection

## Components

### BaseMonitor
Abstract base class for all monitors:
```python
class BaseMonitor(ABC):
    def collect(self) -> Dict[str, Any]: ...  # Collect raw metrics
    def analyze(self) -> Dict[str, Any]: ...  # Analyze and identify issues
    def take_snapshot(self) -> MetricSnapshot: ...  # Record metrics over time
```

### HealthMonitor
```python
monitor = HealthMonitor()
monitor.record_ingest_attempt("arxiv", success=True)
monitor.record_ingest_attempt("local_file", success=False, error="File not found")
report = monitor.analyze()
```

### QualityMonitor
```python
monitor = QualityMonitor()
monitor.record_ingested_record("rec-1", {"title": "...", "error": None})
monitor.record_embedding("text", "rec-1", np.array([...]))
report = monitor.analyze()
```

### BalanceMonitor
```python
monitor = BalanceMonitor()
monitor.record_data("image", source="arxiv", collection="images")
monitor.record_data("text", source="arxiv", collection="papers")
report = monitor.analyze()
```

### MonitoringDashboard
Central orchestrator combining all monitors:

```python
dashboard = MonitoringDashboard()

# Record events
dashboard.record_ingest_attempt("arxiv", success=True)
dashboard.record_ingested_record("rec-1", "text", "arxiv", record_dict)
dashboard.record_embedding("text", "rec-1", embedding)

# Get reports
health_report = dashboard.get_health_report()
quality_report = dashboard.get_quality_report()
balance_report = dashboard.get_balance_report()
comprehensive_report = dashboard.get_comprehensive_report()

# Print formatted report
print(dashboard.print_report())
```

## Report Format

### Health Report
```python
{
    "status": "HEALTHY",
    "issues": [],
    "warnings": [],
    "metrics": {
        "total_attempts": 100,
        "successful_ingestions": 95,
        "failed_ingestions": 5,
        "success_rate_percent": 95.0,
        "data_freshness_hours": 2.5,
        "active_sources": 3,
        "failed_sources": [("source_x", 2)],
        "source_details": {...}
    }
}
```

### Quality Report
```python
{
    "status": "HEALTHY",
    "issues": [],
    "warnings": [],
    "metrics": {
        "total_records": 1000,
        "error_rate_percent": 0.5,
        "duplicate_rate_percent": 0.2,
        "average_metadata_completeness_percent": 92.5,
        "embedding_statistics": {
            "text": {
                "count": 250,
                "valid_count": 250,
                "validity_rate_percent": 100.0,
                "norm_stats": {...}
            }
        },
        "consistency_issues_count": 0
    }
}
```

### Balance Report
```python
{
    "status": "BALANCED",
    "issues": [],
    "warnings": [],
    "metrics": {
        "total_records": 1000,
        "modality_distribution": {
            "image": {"count": 250, "percentage": 25.0},
            "text": {"count": 250, "percentage": 25.0},
            "sequence": {"count": 250, "percentage": 25.0},
            "structure": {"count": 250, "percentage": 25.0}
        },
        "gini_coefficient": 0.0,
        "is_balanced": true
    }
}
```

## Integration with Pipeline

### Recording Ingestion
```python
try:
    records = collector.collect(source)
    dashboard.record_ingest_attempt(collector_name, success=True)
except Exception as e:
    dashboard.record_ingest_attempt(collector_name, success=False, error=str(e))
```

### Recording Processed Records
```python
for record in ingested_records:
    dashboard.record_ingested_record(
        record.id,
        record.data_type,
        record.source,
        asdict(record)
    )
```

### Recording Embeddings
```python
for record in embedded_records:
    dashboard.record_embedding(
        record.data_type,
        record.id,
        np.array(record.embedding)
    )
```

## Usage Examples

### Basic Monitoring
```python
from pipeline.monitoring import MonitoringDashboard

dashboard = MonitoringDashboard()

# Simulate pipeline operations
dashboard.record_ingest_attempt("arxiv", success=True)
dashboard.record_ingest_attempt("arxiv", success=False, error="Network timeout")
dashboard.record_ingested_record("r1", "text", "arxiv", {"title": "Paper"})
dashboard.record_embedding("text", "r1", np.random.rand(384))

# Get report
report = dashboard.get_comprehensive_report()
print(f"Status: {report['overall_status']}")
print(f"Issues: {report['issues']}")
print(f"Warnings: {report['warnings']}")
```

### Printing Formatted Report
```python
print(dashboard.print_report())
```

Output:
```
================================================================================
PIPELINE MONITORING DASHBOARD
================================================================================
Timestamp: 2024-01-24T12:34:56.789123
Uptime: 1.5 hours
Overall Status: HEALTHY

SUMMARY
----------------
Total Issues: 0
Total Warnings: 2

⚠️ WARNINGS
  • Duplicate records found: 0.5%
  • Some distribution imbalance (Gini: 0.12)

HEALTH REPORT
----------------
Status: HEALTHY
  Success Rate: 95.0%
  Total Attempts: 100
  Active Sources: 3
  Data Freshness: 2.5 hours

...
================================================================================
```

### Tracking Over Time
```python
dashboard.health_monitor.take_snapshot()
dashboard.quality_monitor.take_snapshot()
dashboard.balance_monitor.take_snapshot()

# Get history
health_history = dashboard.health_monitor.get_history(last_n=10)
for snapshot in health_history:
    print(f"{snapshot.timestamp}: {snapshot.metrics['success_rate_percent']}%")
```

## Metrics Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Success Rate | < 95% | < 90% |
| Error Rate | > 1% | > 5% |
| Duplicate Rate | > 1% | > 5% |
| Metadata Completeness | < 90% | < 80% |
| Data Freshness | > 72h | > 168h |
| Gini Coefficient | > 0.15 | > 0.3 |
| Embedding Validity | < 99% | < 95% |

## Architecture

```
MonitoringDashboard
├── HealthMonitor
│   └── Tracks: success rates, sources, freshness
├── QualityMonitor
│   └── Tracks: duplicates, metadata, embeddings
├── BalanceMonitor
│   └── Tracks: modality distribution, diversity
└── MetricSnapshot (history for each monitor)
```

## Best Practices

1. **Record all events**: Record every ingestion attempt and result
2. **Monitor continuously**: Take snapshots periodically to track trends
3. **Act on warnings**: Investigate warnings before they become critical issues
4. **Review reports regularly**: Weekly or daily depending on data volume
5. **Set appropriate thresholds**: Adjust tolerance based on your pipeline's normal behavior
6. **Track trends**: Use historical data to identify patterns and degradation

## Extending the System

Create custom monitors by extending `BaseMonitor`:

```python
from pipeline.monitoring.base_monitor import BaseMonitor

class CustomMonitor(BaseMonitor):
    def __init__(self):
        super().__init__(name="custom_monitor")
    
    def collect(self) -> Dict[str, Any]:
        # Your metric collection logic
        pass
    
    def analyze(self) -> Dict[str, Any]:
        # Your analysis logic
        pass
```

Then integrate with the dashboard:

```python
dashboard.custom_monitor = CustomMonitor()
```
