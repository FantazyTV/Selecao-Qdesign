"""
Qdrant vector database client
"""

from typing import List, Dict, Any, Optional
import numpy as np
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class QdrantClient:
    """Client for Qdrant vector database"""
    
    def __init__(self):
        """Initialize Qdrant client"""
        try:
            from qdrant_client import QdrantClient as QC
            from qdrant_client.models import Distance, VectorParams, PointStruct
            
            self.QC = QC
            self.Distance = Distance
            self.VectorParams = VectorParams
            self.PointStruct = PointStruct
            
            config = get_config()
            self.client = QC(url=config.storage.qdrant_url)
            self.text_collection = config.storage.qdrant_collection_text
            self.structure_collection = config.storage.qdrant_collection_structures
            self.sequence_collection = config.storage.qdrant_collection_sequences
            self.image_collection = config.storage.qdrant_collection_images
            self.vector_size = config.storage.vector_size
            
            logger.info(f"Connected to Qdrant at {config.storage.qdrant_url}")
            
        except ImportError:
            raise ImportError("qdrant-client not installed. Install with: pip install qdrant-client")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Qdrant: {e}")
    
    def ensure_collection(self, collection_name: str, vector_size: int) -> bool:
        """
        Ensure collection exists, create if needed
        
        Args:
            collection_name: Collection name
            vector_size: Vector dimension
        
        Returns:
            True if collection exists or was created
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                logger.info(f"Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=self.VectorParams(
                        size=vector_size,
                        distance=self.Distance.COSINE
                    )
                )
                logger.info(f"Collection created: {collection_name}")
            else:
                logger.info(f"Collection exists: {collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring collection {collection_name}: {e}")
            return False
    
    def upsert_vector(
        self,
        collection_name: str,
        record_id: str,
        vector: np.ndarray,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Upsert a single vector with metadata
        
        Args:
            collection_name: Collection name
            record_id: Record ID
            vector: Embedding vector
            metadata: Metadata payload
        
        Returns:
            True if successful
        """
        try:
            # Ensure collection exists
            if not self.ensure_collection(collection_name, len(vector)):
                return False
            
            # Convert numpy array to list if needed
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            
            # Create point
            point = self.PointStruct(
                id=hash(record_id) % (2**31),  # Convert string ID to positive int
                vector=vector,
                payload=metadata
            )
            
            # Upsert
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.debug(f"Upserted vector to {collection_name}: {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting vector: {e}")
            return False
    
    def upsert_batch(
        self,
        collection_name: str,
        record_ids: List[str],
        vectors: np.ndarray,
        metadatas: List[Dict[str, Any]]
    ) -> int:
        """
        Upsert multiple vectors
        
        Args:
            collection_name: Collection name
            record_ids: List of record IDs
            vectors: Batch of vectors (n_samples, embedding_dim)
            metadatas: List of metadata dicts
        
        Returns:
            Number of successfully upserted vectors
        """
        try:
            # Ensure collection exists
            if len(vectors) > 0:
                if not self.ensure_collection(collection_name, len(vectors[0])):
                    return 0
            
            # Convert to list if needed
            if isinstance(vectors, np.ndarray):
                vectors = vectors.tolist()
            
            # Create points
            points = []
            for record_id, vector, metadata in zip(record_ids, vectors, metadatas):
                point = self.PointStruct(
                    id=hash(record_id) % (2**31),
                    vector=vector,
                    payload=metadata
                )
                points.append(point)
            
            # Upsert batch
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Upserted {len(points)} vectors to {collection_name}")
            return len(points)
            
        except Exception as e:
            logger.error(f"Error upserting batch: {e}")
            return 0
    
    def search(
        self,
        collection_name: str,
        vector: np.ndarray,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using query API
        
        Args:
            collection_name: Collection name
            vector: Query vector
            limit: Number of results
            score_threshold: Minimum score threshold
        
        Returns:
            List of results with metadata
        """
        try:
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            
            # Use query_points API (standard in modern Qdrant)
            result_obj = self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit,
                score_threshold=score_threshold
            )
            results = result_obj.points if hasattr(result_obj, 'points') else result_obj
            
            return [
                {
                    "id": str(r.id),
                    "score": float(r.score) if hasattr(r, 'score') else 0.0,
                    "metadata": dict(r.payload) if hasattr(r, 'payload') else {}
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Error searching collection '{collection_name}': {type(e).__name__}: {e}")
            return []
    
    def get_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get collection statistics
        
        Args:
            collection_name: Collection name
        
        Returns:
            Collection stats
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            # Handle different Qdrant API versions
            return {
                "name": collection_name,
                "points_count": getattr(collection_info, 'points_count', 0),
                "status": str(getattr(collection_info, 'status', 'unknown'))
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
