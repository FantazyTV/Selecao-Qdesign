"""
Monitoring dashboard and orchestrator

Aggregates all monitoring data and provides comprehensive health reports
"""

from typing import Dict, Any, List
from datetime import datetime
from .health_monitor import HealthMonitor
from .quality_monitor import QualityMonitor
from .balance_monitor import BalanceMonitor
from ..logger import get_logger

logger = get_logger(__name__)


class MonitoringDashboard:
    """Central monitoring dashboard aggregating all monitors"""
    
    def __init__(self):
        """Initialize monitoring dashboard"""
        self.health_monitor = HealthMonitor()
        self.quality_monitor = QualityMonitor()
        self.balance_monitor = BalanceMonitor()
        
        self.start_time = datetime.utcnow()
        self.last_report_time: datetime = None
    
    def record_ingest_attempt(self, source: str, success: bool, error: str = None):
        """Record an ingestion attempt"""
        self.health_monitor.record_ingest_attempt(source, success, error)
    
    def record_ingested_record(self, record_id: str, data_type: str, 
                               source: str, record_dict: Dict[str, Any]):
        """Record an ingested record for quality and balance monitoring"""
        self.quality_monitor.record_ingested_record(record_id, record_dict)
        self.balance_monitor.record_data(data_type, source, record_dict.get("collection", "unknown"))
    
    def record_embedding(self, data_type: str, record_id: str, embedding):
        """Record an embedding for quality monitoring"""
        import numpy as np
        if embedding is not None:
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)
            self.quality_monitor.record_embedding(data_type, record_id, embedding)
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get health monitoring report"""
        self.health_monitor.take_snapshot()
        return self.health_monitor.analyze()
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Get quality monitoring report"""
        self.quality_monitor.take_snapshot()
        return self.quality_monitor.analyze()
    
    def get_balance_report(self) -> Dict[str, Any]:
        """Get balance monitoring report"""
        self.balance_monitor.take_snapshot()
        return self.balance_monitor.analyze()
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive monitoring report"""
        self.last_report_time = datetime.utcnow()
        uptime = (self.last_report_time - self.start_time).total_seconds() / 3600
        
        health_report = self.get_health_report()
        quality_report = self.get_quality_report()
        balance_report = self.get_balance_report()
        
        # Determine overall status
        statuses = [health_report["status"], quality_report["status"], balance_report["status"]]
        overall_status = "HEALTHY" if "UNHEALTHY" not in statuses and "IMBALANCED" not in statuses else "WARNING"
        
        all_issues = health_report["issues"] + quality_report["issues"] + balance_report["issues"]
        all_warnings = health_report["warnings"] + quality_report["warnings"] + balance_report["warnings"]
        
        return {
            "timestamp": self.last_report_time.isoformat(),
            "overall_status": overall_status,
            "uptime_hours": round(uptime, 2),
            "total_issues": len(all_issues),
            "total_warnings": len(all_warnings),
            "issues": all_issues,
            "warnings": all_warnings,
            "health_report": health_report,
            "quality_report": quality_report,
            "balance_report": balance_report
        }
    
    def print_report(self, include_metrics: bool = True):
        """Pretty print comprehensive report"""
        report = self.get_comprehensive_report()
        
        lines = []
        lines.append("\n" + "="*80)
        lines.append("PIPELINE MONITORING DASHBOARD")
        lines.append("="*80)
        lines.append(f"Timestamp: {report['timestamp']}")
        lines.append(f"Uptime: {report['uptime_hours']} hours")
        lines.append(f"Overall Status: {report['overall_status']}")
        lines.append("")
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Issues: {report['total_issues']}")
        lines.append(f"Total Warnings: {report['total_warnings']}")
        
        # Issues
        if report["issues"]:
            lines.append("")
            lines.append("🚨 CRITICAL ISSUES")
            for issue in report["issues"]:
                lines.append(f"  • {issue}")
        
        # Warnings
        if report["warnings"]:
            lines.append("")
            lines.append("⚠️ WARNINGS")
            for warning in report["warnings"]:
                lines.append(f"  • {warning}")
        
        # Detailed reports
        if include_metrics:
            lines.append("")
            lines.append("HEALTH REPORT")
            lines.append("-" * 80)
            lines.append(f"Status: {report['health_report']['status']}")
            metrics = report["health_report"]["metrics"]
            lines.append(f"  Success Rate: {metrics['success_rate_percent']}%")
            lines.append(f"  Total Attempts: {metrics['total_attempts']}")
            lines.append(f"  Active Sources: {metrics['active_sources']}")
            if metrics.get("data_freshness_hours"):
                lines.append(f"  Data Freshness: {metrics['data_freshness_hours']} hours")
            
            lines.append("")
            lines.append("QUALITY REPORT")
            lines.append("-" * 80)
            lines.append(f"Status: {report['quality_report']['status']}")
            q_metrics = report["quality_report"]["metrics"]
            lines.append(f"  Total Records: {q_metrics['total_records']}")
            lines.append(f"  Error Rate: {q_metrics['error_rate_percent']}%")
            lines.append(f"  Duplicate Rate: {q_metrics['duplicate_rate_percent']}%")
            lines.append(f"  Metadata Completeness: {q_metrics['average_metadata_completeness_percent']}%")
            
            lines.append("")
            lines.append("BALANCE REPORT")
            lines.append("-" * 80)
            lines.append(f"Status: {report['balance_report']['status']}")
            b_metrics = report["balance_report"]["metrics"]
            lines.append(f"  Gini Coefficient: {b_metrics['gini_coefficient']}")
            if b_metrics["modality_distribution"]:
                lines.append("  Modality Distribution:")
                for modality, dist in b_metrics["modality_distribution"].items():
                    lines.append(f"    {modality}: {dist['count']} ({dist['percentage']}%)")
        
        lines.append("")
        lines.append("="*80)
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset all monitors"""
        self.health_monitor.reset()
        self.quality_monitor.reset()
        self.balance_monitor.reset()
        self.start_time = datetime.utcnow()
    
    def __repr__(self) -> str:
        return (
            f"MonitoringDashboard("
            f"health={self.health_monitor}, "
            f"quality={self.quality_monitor}, "
            f"balance={self.balance_monitor})"
        )
