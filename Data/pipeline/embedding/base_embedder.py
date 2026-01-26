"""
Base embedder class
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np


class BaseEmbedder(ABC):
    """Abstract base class for all embedders"""
    
    @abstractmethod
    def embed(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Embed content into a vector
        
        Args:
            content: Content to embed
            metadata: Optional metadata
        
        Returns:
            Numpy array of shape (embedding_dim,)
        """
        pass
    
    @abstractmethod
    def embed_batch(
        self,
        contents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Embed multiple contents at once
        
        Args:
            contents: List of contents to embed
            metadata: Optional list of metadata dicts
        
        Returns:
            Numpy array of shape (num_items, embedding_dim)
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the embedding dimension
        
        Returns:
            Dimension of embeddings produced by this embedder
        """
        pass
    
    @abstractmethod
    def is_applicable(self, data_type: str) -> bool:
        """
        Check if this embedder applies to the given data type
        
        Args:
            data_type: Type of data (text, structure, sequence, image)
        
        Returns:
            True if applicable
        """
        pass
