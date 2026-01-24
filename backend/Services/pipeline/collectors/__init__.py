"""
Collectors package with all available collectors
"""

from .base_collector import BaseCollector, CollectorRecord
from .arxiv_collector import ArxivCollector
from .biorxiv_collector import BiorxivCollector

__all__ = [
    "BaseCollector",
    "CollectorRecord",
    "ArxivCollector",
    "BiorxivCollector",
]
