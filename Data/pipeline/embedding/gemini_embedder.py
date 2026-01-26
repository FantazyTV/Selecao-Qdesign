"""
Gemini-based embeddings for text and images
Uses Google's free embedding models for both modalities
"""

import os
from typing import List, Dict, Any, Optional
import numpy as np
from .base_embedder import BaseEmbedder
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class GeminiEmbedder(BaseEmbedder):
    """Unified embedder for text and images using Google Gemini
    
    Advantages:
    - Free models for both text and images
    - Native multimodal support
    - Simple API
    - No local model downloads needed
    """
    
    def __init__(self):
        """Initialize Gemini embedder with API key from env"""
        self.model = None
        self.dimension = 3072  # Gemini embedding dimension
        
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            genai.configure(api_key=api_key)
            self.genai = genai
            self.model = genai
            
            logger.info("✓ GeminiEmbedder initialized successfully (3072-dim, gemini-embedding-001)")
        except ImportError:
            logger.error("✗ google-generativeai not installed. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"✗ Failed to initialize GeminiEmbedder: {e}")
            raise
    
    def embed(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Embed text or image using Gemini
        
        Args:
            content: Text to embed or image file path
            metadata: Optional metadata with 'is_text' flag
        
        Returns:
            Embedding vector (768-dim)
        """
        if not content:
            logger.warning("Empty content provided for embedding")
            return np.zeros(self.dimension)
        
        try:
            is_text = metadata.get("is_text", True) if metadata else True
            
            if is_text:
                # Text embedding
                result = self.genai.embed_content(
                    model="gemini-embedding-001",
                    content=content,
                    task_type="semantic_similarity"
                )
                embedding = np.array(result['embedding'], dtype=np.float32)
            else:
                # Image embedding
                from pathlib import Path
                
                # Verify image exists
                path = Path(content)
                if not path.exists():
                    # Try relative to project root
                    alt_path = Path("/home/ghassen/Projects/Selecao-QDesign") / content
                    if alt_path.exists():
                        path = alt_path
                    else:
                        logger.warning(f"Image not found: {content}")
                        return np.zeros(self.dimension)
                
                # Load and embed image
                with open(str(path), 'rb') as f:
                    image_data = f.read()
                
                result = self.genai.embed_content(
                    model="gemini-embedding-001",
                    content=image_data,
                    task_type="semantic_similarity"
                )
                embedding = np.array(result['embedding'], dtype=np.float32)
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error embedding content: {e}")
            return np.zeros(self.dimension)
    
    def embed_batch(
        self,
        contents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Embed multiple texts or images
        
        Args:
            contents: List of texts or image paths
            metadata: Optional list of metadata dicts
        
        Returns:
            Batch of embeddings (N, 768)
        """
        embeddings = []
        
        for i, content in enumerate(contents):
            meta = metadata[i] if metadata and i < len(metadata) else None
            embedding = self.embed(content, meta)
            embeddings.append(embedding)
        
        return np.array(embeddings, dtype=np.float32)
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def is_applicable(self, data_type: str) -> bool:
        """Check if applicable to data type"""
        return data_type in ["text", "image", "sequence", "structure"]
