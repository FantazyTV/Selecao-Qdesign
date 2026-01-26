"""
Base monitor class for all monitoring components
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
import json


@dataclass
class MetricSnapshot:
    """A snapshot of metrics at a point in time"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics
        }
    
    def __str__(self) -> str:
        """Pretty print metrics"""
        lines = [f"Timestamp: {self.timestamp.isoformat()}"]
        for key, value in self.metrics.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)


class BaseMonitor(ABC):
    """Abstract base class for all monitors"""
    
    def __init__(self, name: str):
        """
        Initialize monitor
        
        Args:
            name: Monitor name
        """
        self.name = name
        self.history: List[MetricSnapshot] = []
        self.current_snapshot: MetricSnapshot = MetricSnapshot()
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Collect metrics from current state
        
        Returns:
            Dictionary of collected metrics
        """
        pass
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze collected metrics
        
        Returns:
            Dictionary of analysis results
        """
        pass
    
    def take_snapshot(self) -> MetricSnapshot:
        """Take a snapshot of current metrics"""
        metrics = self.collect()
        self.current_snapshot = MetricSnapshot(metrics=metrics)
        self.history.append(self.current_snapshot)
        return self.current_snapshot
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.current_snapshot.metrics.copy()
    
    def get_history(self, last_n: int = None) -> List[MetricSnapshot]:
        """Get historical snapshots"""
        if last_n:
            return self.history[-last_n:]
        return self.history.copy()
    
    def reset(self):
        """Reset monitor state"""
        self.history = []
        self.current_snapshot = MetricSnapshot()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, snapshots={len(self.history)})"
