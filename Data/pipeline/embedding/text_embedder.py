"""Text embedding using SentenceTransformers"""

from typing import List, Dict, Any, Optional
import numpy as np
from .base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class SentenceTransformerTextEmbedder(BaseEmbedder):
    """Embed text using Sentence Transformers (384-dim)"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize text embedder with Sentence Transformers
        
        Args:
            model_name: Model name (without 'sentence-transformers/' prefix)
        """
        config = get_config()
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        self.dimension = 384
        self.model_name = model_name

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(f'sentence-transformers/{model_name}', device=self.device)
            logger.info(f"✓ Initialized SentenceTransformer text embedder: {model_name} (384-dim)")
        except ImportError:
            raise ImportError("Install sentence-transformers: pip install sentence-transformers")
        except Exception as e:
            logger.error(f"✗ Failed to load SentenceTransformer: {e}")
            raise

    def embed(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Embed single text"""
        if not content or not content.strip():
            return np.zeros(self.dimension)

        try:
            embedding = self.model.encode(content, convert_to_numpy=True)

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
            embeddings = self.model.encode(valid_contents, convert_to_numpy=True, batch_size=self.batch_size)

            if self.normalize:
                embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

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
