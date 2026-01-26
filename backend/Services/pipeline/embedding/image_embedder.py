"""Image embedding using CLIP"""

from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from .base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class CLIPImageEmbedder(BaseEmbedder):
    """Embed images using CLIP (512-dim)"""

    def __init__(self, model_name: str = "ViT-B/32"):
        """Initialize CLIP image embedder
        
        Args:
            model_name: CLIP model variant (ViT-B-32, ViT-L-14, etc.)
        """
        config = get_config()
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        self.model_name = model_name
        self.dimension = 512
        self.model = None
        self.preprocess = None

        try:
            import clip
            # Normalize model name for CLIP (expects names like "ViT-B/32")
            if model_name == "ViT-B-32":
                model_name = "ViT-B/32"
            self.model, self.preprocess = clip.load(model_name, device=self.device)
            self.model.eval()
            logger.info(f"✓ Initialized CLIP image embedder: {model_name} (512-dim)")
        except ImportError:
            raise ImportError("Install CLIP: pip install openai-clip")
        except Exception as e:
            logger.error(f"✗ Failed to load CLIP: {e}")
            raise

    def embed(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Embed single image"""
        image_path = metadata.get("image_path") if metadata else content

        if not image_path:
            return np.zeros(self.dimension)

        try:
            from PIL import Image
            import torch
            
            path = Path(image_path)
            if not path.is_absolute() and not path.exists():
                path = Path(__file__).parent.parent.parent.parent / image_path

            if not path.exists():
                logger.warning(f"Image not found: {image_path}")
                return np.zeros(self.dimension)

            image = Image.open(str(path)).convert('RGB')
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                embedding = self.model.encode_image(image_input)
                embedding = embedding.cpu().numpy().astype(np.float32)[0]

            if self.normalize:
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error embedding image: {e}")
            return np.zeros(self.dimension)

    def embed_batch(self, contents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> np.ndarray:
        """Embed multiple images"""
        if metadata:
            image_paths = [m.get("image_path", c) for m, c in zip(metadata, contents)]
        else:
            image_paths = contents

        valid_paths = [p for p in image_paths if p]

        if not valid_paths:
            return np.zeros((len(contents), self.dimension))

        try:
            from PIL import Image
            import torch
            
            embeddings = []
            for path_str in image_paths:
                try:
                    path = Path(path_str)
                    if not path.is_absolute() and not path.exists():
                        path = Path(__file__).parent.parent.parent.parent / path_str

                    if not path.exists():
                        embeddings.append(np.zeros(self.dimension, dtype=np.float32))
                        continue

                    image = Image.open(str(path)).convert('RGB')
                    image_input = self.preprocess(image).unsqueeze(0).to(self.device)

                    with torch.no_grad():
                        embedding = self.model.encode_image(image_input)
                        embedding = embedding.cpu().numpy().astype(np.float32)[0]

                    if self.normalize:
                        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

                    embeddings.append(embedding)
                except Exception as e:
                    logger.warning(f"Failed to embed image {path_str}: {e}")
                    embeddings.append(np.zeros(self.dimension, dtype=np.float32))

            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            return np.zeros((len(contents), self.dimension))

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension

    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "image"
