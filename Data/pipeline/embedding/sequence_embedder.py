"""Sequence embedding using ESM (Evolutionary Scale Modeling) for proteins"""

from typing import List, Dict, Any, Optional
import numpy as np
from .base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class ESMSequenceEmbedder(BaseEmbedder):
    """Embed protein sequences using Meta's ESM models (1280-dim for ESM-2)"""

    def __init__(self, model_name: str = "esm2_t12_35M_UR50D"):
        """Initialize ESM sequence embedder for protein sequences
        
        Args:
            model_name: ESM model name
                - esm2_t6_8M_UR50D: 6 layers, 8M params (small, fast)
                - esm2_t12_35M_UR50D: 12 layers, 35M params (medium, recommended)
                - esm2_t33_650M_UR50D: 33 layers, 650M params (large, slow)
        """
        config = get_config()
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        self.model_name = model_name
        self.dimension = 1280  # ESM-2 default output dimension (may be updated after load)
        self.model = None
        self.alphabet = None
        self.layer_index = None

        try:
            import esm
            import torch

            pretrained = getattr(esm, "pretrained", None)
            if pretrained is None:
                try:
                    import esm.pretrained as pretrained  # type: ignore
                except Exception as e:
                    raise ImportError(
                        "fair-esm not available or wrong 'esm' package installed. "
                        "Uninstall 'esm' and install 'fair-esm'."
                    ) from e

            # Load ESM model and alphabet (supports multiple fair-esm versions)
            if hasattr(pretrained, "load_model_and_alphabet"):
                self.model, self.alphabet = pretrained.load_model_and_alphabet(model_name)
            elif hasattr(pretrained, "load_model_and_alphabet_local"):
                # Only use local loader if model_name is a valid path
                from pathlib import Path
                model_path = Path(model_name)
                if not model_path.exists():
                    raise FileNotFoundError(
                        f"Local ESM model not found: {model_name}. "
                        "Provide a valid path or use a model name."
                    )
                self.model, self.alphabet = pretrained.load_model_and_alphabet_local(str(model_path))
            elif hasattr(pretrained, model_name):
                self.model, self.alphabet = getattr(pretrained, model_name)()
            else:
                # Try with esm2_ prefix variants if model_name was custom
                alt_name = model_name.replace("-", "_")
                if hasattr(pretrained, alt_name):
                    self.model, self.alphabet = getattr(pretrained, alt_name)()
                else:
                    raise AttributeError("No compatible ESM loader found in fair-esm")

            self.model = self.model.to(self.device)
            self.model.eval()

            # Determine correct last layer index and embedding dimension
            self.layer_index = getattr(self.model, "num_layers", None)
            if self.layer_index is None:
                self.layer_index = 12
            self.dimension = int(getattr(self.model, "embed_dim", self.dimension))

            logger.info(
                f"✓ Initialized ESM sequence embedder: {model_name} "
                f"(layer={self.layer_index}, dim={self.dimension})"
            )
        except ImportError:
            raise ImportError("Install ESM: pip install fair-esm")
        except Exception as e:
            logger.error(f"✗ Failed to load ESM model: {e}")
            raise

    def embed(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Embed single protein sequence"""
        if not content or not content.strip():
            return np.zeros(self.dimension)

        try:
            import torch
            
            # Clean sequence (remove whitespace)
            sequence = content.replace(" ", "").replace("\n", "").upper()
            
            # Verify valid amino acids
            if not self._is_valid_protein(sequence):
                logger.warning(f"Invalid protein sequence: {sequence[:50]}")
                return np.zeros(self.dimension)

            # Convert sequence to tokens
            batch_converter = self.alphabet.get_batch_converter()
            data = [("protein_1", sequence)]
            batch_labels, batch_strs, batch_tokens = batch_converter(data)

            # Get embedding
            batch_tokens = batch_tokens.to(self.device)
            with torch.no_grad():
                results = self.model(batch_tokens, repr_layers=[self.layer_index])
                embedding = results["representations"][self.layer_index].squeeze(0).mean(dim=0)
            
            embedding = embedding.cpu().numpy().astype(np.float32)

            if self.normalize:
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error embedding sequence: {e}")
            return np.zeros(self.dimension)

    def embed_batch(self, contents: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> np.ndarray:
        """Embed multiple protein sequences"""
        valid_contents = [
            c.replace(" ", "").replace("\n", "").upper() 
            for c in contents 
            if c and self._is_valid_protein(c.replace(" ", "").replace("\n", "").upper())
        ]

        if not valid_contents:
            return np.zeros((len(contents), self.dimension))

        try:
            import torch
            
            # Convert sequences to tokens
            batch_converter = self.alphabet.get_batch_converter()
            data = [(f"protein_{i}", seq) for i, seq in enumerate(valid_contents)]
            batch_labels, batch_strs, batch_tokens = batch_converter(data)

            # Get embeddings
            batch_tokens = batch_tokens.to(self.device)
            with torch.no_grad():
                results = self.model(batch_tokens, repr_layers=[self.layer_index])
                embeddings_tensor = results["representations"][self.layer_index]
                embeddings = embeddings_tensor.mean(dim=1)  # Average over sequence length

            embeddings = embeddings.cpu().numpy().astype(np.float32)

            if self.normalize:
                embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            return np.zeros((len(contents), self.dimension))

    def _is_valid_protein(self, sequence: str) -> bool:
        """Check if sequence contains only valid amino acids"""
        valid_aa = set('ACDEFGHIKLMNPQRSTVWY')
        return all(c in valid_aa for c in sequence.upper())

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension

    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type in ("sequence", "protein")
