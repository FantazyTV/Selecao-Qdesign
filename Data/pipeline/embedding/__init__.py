"""
Embedding package with specialized embedders
"""

from .base_embedder import BaseEmbedder

# Import proper embedders
try:
    from .text_embedder import SentenceTransformerTextEmbedder
except ImportError:
    SentenceTransformerTextEmbedder = None

try:
    from .image_embedder import CLIPImageEmbedder
except ImportError:
    CLIPImageEmbedder = None

try:
    from .sequence_embedder import ESMSequenceEmbedder
except ImportError:
    ESMSequenceEmbedder = None

try:
    from .structure_embedder import StructureEmbedder
except ImportError:
    StructureEmbedder = None

__all__ = [
    "BaseEmbedder",
    "SentenceTransformerTextEmbedder",
    "CLIPImageEmbedder",
    "ESMSequenceEmbedder",
    "StructureEmbedder",
]
