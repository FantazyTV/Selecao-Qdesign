"""Sequence embedding using lightweight methods"""

from typing import List, Dict, Any, Optional
import numpy as np
from .base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class FastembedSequenceEmbedder(BaseEmbedder):
    """Embed protein sequences with lightweight approach"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize sequence embedder"""
        config = get_config()
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        self.model_name = model_name
        self.dimension = 384

        try:
            from fastembed import TextEmbedding
            self.model = TextEmbedding(model_name=self.model_name, device=self.device)
            logger.info("Initialized FastembedSequenceEmbedder (lightweight)")
        except ImportError:
            raise ImportError("Install fastembed: pip install fastembed")

    def embed(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Embed single sequence"""
        if not content or not content.strip():
            return np.zeros(self.dimension)

        try:
            content = content.replace(" ", "").replace("\n", "").upper()
            embeddings = list(self.model.embed([content]))
            embedding = embeddings[0]

            if self.normalize:
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error embedding sequence: {e}")
            return np.zeros(self.dimension)

    def embed_batch(self, contents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> np.ndarray:
        """Embed multiple sequences"""
        valid_contents = [c.replace(" ", "").replace("\n", "").upper() for c in contents if c]

        if not valid_contents:
            return np.zeros((len(contents), self.dimension))

        try:
            embeddings = list(self.model.embed(valid_contents, batch_size=self.batch_size))

            if self.normalize:
                embeddings = [e / (np.linalg.norm(e) + 1e-8) for e in embeddings]

            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error embedding sequence batch: {e}")
            return np.zeros((len(contents), self.dimension))

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension

    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "sequence"
