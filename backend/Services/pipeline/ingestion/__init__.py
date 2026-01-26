"""
Ingestion package with all available ingesters
"""

from .base_ingester import BaseIngester, IngestedRecord
from .text_ingester import TextIngester, PDFIngester
from .protein_ingester import SequenceIngester, StructureIngester
from .image_ingester import ImageIngester

__all__ = [
    "BaseIngester",
    "IngestedRecord",
    "TextIngester",
    "PDFIngester",
    "SequenceIngester",
    "StructureIngester",
    "ImageIngester",
]
