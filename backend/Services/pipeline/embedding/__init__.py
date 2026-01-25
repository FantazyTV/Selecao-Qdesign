"""
Embedding package with specialized embedders
"""

from .base_embedder import BaseEmbedder
from .gemini_embedder import GeminiEmbedder

# Import optional embedders with graceful fallback
_fastembed_available = False
try:
    from .text_embedder import FastembedTextEmbedder
    from .image_embedder import FastembedImageEmbedder
    from .sequence_embedder import FastembedSequenceEmbedder
    from .structure_embedder import StructureEmbedder
    _fastembed_available = True
except ImportError:
    FastembedTextEmbedder = None
    FastembedImageEmbedder = None
    FastembedSequenceEmbedder = None
    StructureEmbedder = None

_esm_available = False
try:
    from .esm_embedder import ESMSequenceEmbedder, ESMStructureEmbedder
    _esm_available = True
except ImportError:
    ESMSequenceEmbedder = None
    ESMStructureEmbedder = None

__all__ = [
    "BaseEmbedder",
    "GeminiEmbedder",
]

# Add optional embedders to exports if available
if _fastembed_available:
    __all__.extend([
        "FastembedTextEmbedder",
        "FastembedImageEmbedder",
        "FastembedSequenceEmbedder",
        "StructureEmbedder",
    ])

if _esm_available:
    __all__.extend([
        "ESMSequenceEmbedder",
        "ESMStructureEmbedder",
    ])
