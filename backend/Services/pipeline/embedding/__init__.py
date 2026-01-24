"""
Embedding package with all available embedders
"""

from .base_embedder import BaseEmbedder
from .fastembed_embedder import FastembedTextEmbedder, FastembedImageEmbedder, FastembedSequenceEmbedder, StructureEmbedder
from .esm_embedder import ESMSequenceEmbedder, ESMStructureEmbedder

__all__ = [
    "BaseEmbedder",
    "FastembedTextEmbedder",
    "FastembedImageEmbedder",
    "FastembedSequenceEmbedder",  # Lightweight alternative, no torch
    "StructureEmbedder",           # Lightweight structure embedder, no dependencies
    "ESMSequenceEmbedder",
    "ESMStructureEmbedder",
]
