"""
Collectors package with all available collectors
"""

from .base_collector import BaseCollector, CollectorRecord
from .arxiv_collector import ArxivCollector
from .biorxiv_collector import BiorxivCollector
from .alphafold_collector import AlphaFoldCollector

__all__ = [
    "BaseCollector",
    "CollectorRecord",
    "ArxivCollector",
    "BiorxivCollector",
    "AlphaFoldCollector",
]
