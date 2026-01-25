"""Image embedding using CLIP and PIL"""

from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from .base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class FastembedImageEmbedder(BaseEmbedder):
    """Embed images using CLIP or PIL fallback"""

    def __init__(self):
        """Initialize image embedder"""
        config = get_config()
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        self.model = None
        self.use_fastembed = False
        self.dimension = 512

        try:
            from fastembed import ImageEmbedding
            self.model = ImageEmbedding(model_name="Qdrant/clip-ViT-B-32-vision", device=self.device)
            self.use_fastembed = True
            logger.info("Initialized FastembedImageEmbedder using CLIP")
        except Exception as e:
            logger.warning(f"CLIP not available: {e}, using PIL fallback")
            try:
                from PIL import Image
                self.pil_available = True
                self.dimension = 3072
                logger.info("Initialized FastembedImageEmbedder using PIL")
            except ImportError:
                self.pil_available = False
                logger.warning("PIL not available, using zero embeddings")

    def _extract_pil_features(self, image_path: str) -> np.ndarray:
        """Extract features from image using PIL"""
        try:
            from PIL import Image
            path = Path(image_path)

            if not path.is_absolute() and not path.exists():
                path = Path(__file__).parent.parent.parent / image_path

            if not path.exists():
                logger.warning(f"Image not found: {image_path}")
                return np.zeros(self.dimension)

            img = Image.open(str(path)).convert('RGB')
            features = []

            # Histogram features
            for channel in img.split():
                hist = np.array(channel.histogram(), dtype=np.float32)
                hist = hist / (hist.sum() + 1e-8)
                features.append(hist)

            # Image properties
            img_array = np.array(img, dtype=np.float32)
            props = [img_array.mean(), img_array.std(), img_array.min(), img_array.max()]

            for channel in img.split():
                ch_array = np.array(channel, dtype=np.float32)
                props.extend([ch_array.mean(), ch_array.std()])

            props.extend([float(img.width), float(img.height)])
            props.append(float(img.width) / (img.height + 1e-8))

            # Edge features
            try:
                import scipy.ndimage
                edges = scipy.ndimage.sobel(np.array(img.convert('L'), dtype=np.float32))
                edge_features = [edges.flatten()[min(i * len(edges.flatten()) // 128, len(edges.flatten())-1)] for i in range(128)]
                features.append(np.array(edge_features))
            except:
                features.append(np.zeros(128))

            all_features = np.concatenate([np.concatenate(features[:3]), np.array(props), features[-1]])

            if len(all_features) < self.dimension:
                all_features = np.pad(all_features, (0, self.dimension - len(all_features)))
            else:
                all_features = all_features[:self.dimension]

            if self.normalize:
                all_features = all_features / (np.linalg.norm(all_features) + 1e-8)

            return np.array(all_features, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error extracting PIL features: {e}")
            return np.zeros(self.dimension)

    def embed(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Embed single image"""
        image_path = metadata.get("image_path") if metadata else content

        if not image_path:
            return np.zeros(self.dimension)

        try:
            if self.use_fastembed and self.model:
                try:
                    embeddings = list(self.model.embed([image_path]))
                    return np.array(embeddings[0], dtype=np.float32)
                except Exception as e:
                    logger.warning(f"CLIP failed, using PIL: {e}")
            return self._extract_pil_features(image_path)
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

        embeddings = [self.embed(path, {"image_path": path}) for path in valid_paths]
        return np.array(embeddings, dtype=np.float32)

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension

    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "image"
