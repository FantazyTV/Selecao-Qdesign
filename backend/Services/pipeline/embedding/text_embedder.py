"""Text embedding using sentence-transformers/fastembed"""

from typing import List, Dict, Any, Optional
import numpy as np
from .base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class FastembedTextEmbedder(BaseEmbedder):
    """Embed text using fastembed or sentence-transformers"""

    def __init__(self):
        """Initialize text embedder"""
        config = get_config()
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        self.dimension = 384

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
            logger.info("Initialized FastEmbedTextEmbedder with SentenceTransformer")
        except ImportError:
            try:
                from fastembed import TextEmbedding
                self.model = TextEmbedding(model_name=config.fastembed_model, device=self.device)
                logger.info(f"Initialized FastEmbedTextEmbedder with fastembed")
            except ImportError:
                raise ImportError("Install sentence-transformers: pip install sentence-transformers")

    def embed(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Embed single text"""
        if not content or not content.strip():
            return np.zeros(self.dimension)

        try:
            if hasattr(self.model, 'encode'):
                embedding = self.model.encode(content, convert_to_numpy=True)
            else:
                embeddings = list(self.model.embed([content]))
                embedding = embeddings[0]

            if self.normalize:
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return np.zeros(self.dimension)

    def embed_batch(self, contents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> np.ndarray:
        """Embed multiple texts"""
        valid_contents = [c for c in contents if c and c.strip()]

        if not valid_contents:
            return np.zeros((len(contents), self.dimension))

        try:
            if hasattr(self.model, 'encode'):
                embeddings = self.model.encode(valid_contents, convert_to_numpy=True, batch_size=self.batch_size)
            else:
                embeddings = list(self.model.embed(valid_contents, batch_size=self.batch_size))

            if self.normalize:
                embeddings = [e / (np.linalg.norm(e) + 1e-8) for e in embeddings]

            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            return np.zeros((len(contents), self.dimension))

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension

    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "text"
