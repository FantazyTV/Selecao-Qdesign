"""
Pipeline health monitoring

Tracks ingestion success rates, failed sources, and data freshness
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from ..logger import get_logger
from .base_monitor import BaseMonitor

logger = get_logger(__name__)


class HealthMonitor(BaseMonitor):
    """Monitor pipeline health metrics"""
    
    def __init__(self):
        """Initialize health monitor"""
        super().__init__(name="health_monitor")
        
        # Track ingestion attempts
        self.ingestion_attempts = 0
        self.ingestion_successes = 0
        self.ingestion_failures = 0
        
        # Track sources
        self.sources: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "last_success": None,
            "last_failure": None,
            "error_messages": []
        })
        
        # Track data freshness
        self.last_ingest_time: datetime = None
        self.last_successful_ingest: datetime = None
        self.data_age_threshold = timedelta(days=7)  # Alert if data older than 7 days
    
    def record_ingest_attempt(self, source: str, success: bool, error: str = None):
        """
        Record an ingestion attempt
        
        Args:
            source: Source name (arxiv, biorxiv, local_file, etc)
            success: Whether ingestion was successful
            error: Error message if failed
        """
        self.ingestion_attempts += 1
        
        if success:
            self.ingestion_successes += 1
            self.last_successful_ingest = datetime.utcnow()
            self.sources[source]["successful"] += 1
            self.sources[source]["last_success"] = datetime.utcnow()
        else:
            self.ingestion_failures += 1
            self.sources[source]["failed"] += 1
            self.sources[source]["last_failure"] = datetime.utcnow()
            if error:
                self.sources[source]["error_messages"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": error
                })
                # Keep only last 10 errors per source
                if len(self.sources[source]["error_messages"]) > 10:
                    self.sources[source]["error_messages"] = \
                        self.sources[source]["error_messages"][-10:]
        
        self.sources[source]["total"] += 1
        self.last_ingest_time = datetime.utcnow()
    
    def collect(self) -> Dict[str, Any]:
        """Collect health metrics"""
        success_rate = (
            self.ingestion_successes / self.ingestion_attempts * 100
            if self.ingestion_attempts > 0
            else 0
        )
        
        # Calculate data freshness
        data_freshness = None
        data_stale = False
        if self.last_successful_ingest:
            age = datetime.utcnow() - self.last_successful_ingest
            data_freshness = age.total_seconds() / 3600  # Hours
            data_stale = age > self.data_age_threshold
        
        # Identify failed sources
        failed_sources = [
            (source, metrics["failed"])
            for source, metrics in self.sources.items()
            if metrics["failed"] > 0
        ]
        failed_sources.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "total_attempts": self.ingestion_attempts,
            "successful_ingestions": self.ingestion_successes,
            "failed_ingestions": self.ingestion_failures,
            "success_rate_percent": round(success_rate, 2),
            "data_freshness_hours": round(data_freshness, 2) if data_freshness else None,
            "data_is_stale": data_stale,
            "last_ingest_time": self.last_ingest_time.isoformat() if self.last_ingest_time else None,
            "last_successful_ingest": self.last_successful_ingest.isoformat() if self.last_successful_ingest else None,
            "active_sources": len(self.sources),
            "failed_sources": [(src, count) for src, count in failed_sources],
            "source_details": {
                src: {
                    "total": metrics["total"],
                    "successful": metrics["successful"],
                    "failed": metrics["failed"],
                    "success_rate": round(metrics["successful"] / metrics["total"] * 100, 2) if metrics["total"] > 0 else 0,
                    "last_success": metrics["last_success"].isoformat() if metrics["last_success"] else None,
                    "last_failure": metrics["last_failure"].isoformat() if metrics["last_failure"] else None,
                    "recent_errors": metrics["error_messages"][-3:] if metrics["error_messages"] else []
                }
                for src, metrics in self.sources.items()
            }
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze health metrics"""
        metrics = self.collect()
        
        issues = []
        warnings = []
        
        # Check success rate
        if metrics["success_rate_percent"] < 90:
            issues.append(f"Low success rate: {metrics['success_rate_percent']}% (threshold: 90%)")
        elif metrics["success_rate_percent"] < 95:
            warnings.append(f"Acceptable success rate: {metrics['success_rate_percent']}%")
        
        # Check data freshness
        if metrics["data_is_stale"]:
            issues.append(f"Data is stale: {metrics['data_freshness_hours']} hours old (threshold: 168 hours)")
        
        # Check for failing sources
        if metrics["failed_sources"]:
            top_failing = metrics["failed_sources"][:3]
            warnings.append(f"Sources with failures: {top_failing}")
        
        # Check if any ingestions have occurred
        if metrics["total_attempts"] == 0:
            issues.append("No ingestion attempts recorded")
        
        return {
            "status": "HEALTHY" if not issues else "UNHEALTHY",
            "issues": issues,
            "warnings": warnings,
            "metrics": metrics
        }
    
    def get_source_summary(self) -> Dict[str, Tuple[int, float]]:
        """Get summary of sources (success_count, success_rate)"""
        return {
            src: (metrics["successful"], metrics["successful"] / metrics["total"] * 100 if metrics["total"] > 0 else 0)
            for src, metrics in self.sources.items()
        }
    
    def __repr__(self) -> str:
        metrics = self.collect()
        return (
            f"HealthMonitor(success_rate={metrics['success_rate_percent']}%, "
            f"total_attempts={metrics['total_attempts']}, "
            f"active_sources={metrics['active_sources']})"
        )
