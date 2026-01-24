"""
Protein structure and sequence embedder using ESM
Optional: Only works if torch is installed (heavy dependency)
Fallback: Use FastembedSequenceEmbedder for lightweight alternative
"""

from typing import List, Dict, Any, Optional
import numpy as np
from ..embedding.base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)

# Try to import torch, but make it optional
try:
    import torch
    import esm
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch/ESM not available. Use FastembedSequenceEmbedder instead.")


class ESMSequenceEmbedder(BaseEmbedder):
    """Embed protein sequences using ESM-2
    
    Note: This requires torch (800MB+) and fair-esm (200MB+)
    For slow internet, use FastembedSequenceEmbedder instead (no extra dependencies)
    """
    
    def __init__(self):
        """Initialize ESM-2 for sequence embedding"""
        if not TORCH_AVAILABLE:
            raise ImportError(
                "torch and fair-esm not installed. Install with:\n"
                "  pip install torch fair-esm\n\n"
                "For slow internet, use FastembedSequenceEmbedder instead (no torch needed):\n"
                "  from pipeline.embedding.fastembed_embedder import FastembedSequenceEmbedder\n"
                "  embedder = FastembedSequenceEmbedder()  # Uses fastembed, no torch!"
            )
        
        config = get_config()
        self.model_name = config.esm_model
        self.device = config.device
        self.batch_size = config.batch_size
        self.normalize = config.normalize_embeddings
        
        try:
            self.torch = torch
            self.model, self.alphabet = esm.pretrained.load_model_and_alphabet_local(self.model_name)
            self.model = self.model.eval().to(self.device)
            self.dimension = self.model.embed_dim
            
            logger.info(f"Initialized ESM SequenceEmbedder with model {self.model_name}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load ESM model: {e}")
    
    def embed(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Embed a single sequence
        
        Args:
            content: Protein sequence
            metadata: Optional metadata
        
        Returns:
            Embedding vector
        """
        try:
            # Remove whitespace and validate
            content = content.replace(" ", "").replace("\n", "").upper()
            
            if not content:
                logger.warning("Empty sequence provided for embedding")
                return np.zeros(self.dimension)
            
            # Create ESM tokens
            batch_labels = ["seq"]
            batch_strs = [content]
            
            batch_tokens = self.alphabet.encode(content)
            
            if len(batch_tokens) > 1024:
                logger.warning(f"Sequence too long ({len(batch_tokens)}), truncating to 1024")
                batch_tokens = batch_tokens[:1024]
            
            batch_tokens = self.torch.tensor([batch_tokens]).to(self.device)
            
            with self.torch.no_grad():
                results = self.model(batch_tokens, repr_layers=[self.model.num_layers])
            
            embedding = results["representations"][self.model.num_layers][0, 1:-1, :].mean(dim=0)
            embedding = embedding.cpu().numpy()
            
            if self.normalize:
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding sequence: {e}")
            return np.zeros(self.dimension)
    
    def embed_batch(
        self,
        contents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Embed multiple sequences
        
        Args:
            contents: List of sequences
            metadata: Optional metadata
        
        Returns:
            Batch of embeddings
        """
        try:
            embeddings = []
            
            for i, content in enumerate(contents):
                # Clean sequence
                content = content.replace(" ", "").replace("\n", "").upper()
                
                if not content:
                    logger.warning(f"Empty sequence at index {i}")
                    embeddings.append(np.zeros(self.dimension))
                    continue
                
                embedding = self.embed(content, metadata[i] if metadata else None)
                embeddings.append(embedding)
            
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


class ESMStructureEmbedder(BaseEmbedder):
    """Embed protein structures using ESM-C (contact prediction)"""
    
    def __init__(self):
        """Initialize ESM-C for structure embedding"""
        # For now, we'll use sequence-based embedding for structures
        # Full structure embedding would require 3D coordinate parsing
        self.sequence_embedder = ESMSequenceEmbedder()
        self.dimension = self.sequence_embedder.dimension
    
    def embed(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Embed a structure (uses sequence if available)
        
        Args:
            content: Structure content or extracted sequence
            metadata: Optional metadata (should include 'sequence' if available)
        
        Returns:
            Embedding vector
        """
        try:
            # Try to extract sequence from metadata
            sequence = None
            if metadata and "sequence" in metadata:
                sequence = metadata["sequence"]
            elif metadata and "pdb_id" in metadata:
                # Would need PDB parser here for full implementation
                logger.warning(f"PDB {metadata.get('pdb_id')} structure embedding not fully implemented")
            
            if not sequence:
                logger.warning("No sequence available for structure embedding")
                return np.zeros(self.dimension)
            
            return self.sequence_embedder.embed(sequence, metadata)
            
        except Exception as e:
            logger.error(f"Error embedding structure: {e}")
            return np.zeros(self.dimension)
    
    def embed_batch(
        self,
        contents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Embed multiple structures
        
        Args:
            contents: List of structure contents
            metadata: Optional metadata
        
        Returns:
            Batch of embeddings
        """
        try:
            embeddings = []
            
            for i, content in enumerate(contents):
                m = metadata[i] if metadata else None
                embedding = self.embed(content, m)
                embeddings.append(embedding)
            
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error embedding structure batch: {e}")
            return np.zeros((len(contents), self.dimension))
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type == "structure"
