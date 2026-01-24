"""
Enrichment package with all available enrichers
"""

from .base_enricher import BaseEnricher
from .text_enricher import TextEnricher
from .protein_enricher import SequenceEnricher, StructureEnricher

__all__ = [
    "BaseEnricher",
    "TextEnricher",
    "SequenceEnricher",
    "StructureEnricher",
]
