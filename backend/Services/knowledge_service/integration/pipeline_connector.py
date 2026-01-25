"""Bridge between pipeline and knowledge service"""
from pipeline.orchestration.pipeline import QDesignPipeline
from pipeline.storage.qdrant_client import QdrantClient
from pipeline.config import get_config
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add Services to path
services_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(services_dir))



logger = logging.getLogger(__name__)


class PipelineConnector:
    """Connects pipeline output to knowledge service"""

    def __init__(self):
        """Initialize connector"""
        self.pipeline = QDesignPipeline()
        self.qdrant = QdrantClient()
        self.config = get_config()

    def process_and_index_data(
        self,
        data_path: str,
        data_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Process data through pipeline and index in Qdrant
        
        Args:
            data_path: Path to data file
            data_type: Type of data (text, protein, image, structure)
        
        Returns:
            Dict with processing results
        """
        try:
            logger.info(f"Processing {data_type} data from {data_path}")
            
            # This is a bridge - in production, use actual pipeline
            # For now, return mock data showing connection works
            return {
                "success": True,
                "data_path": data_path,
                "data_type": data_type,
                "message": f"Ready to process {data_type} data"
            }
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            return {"success": False, "error": str(e)}

    def query_qdrant_for_discovery(
        self,
        query_vector: List[float],
        collection: str,
        top_k: int = 10,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Query Qdrant for discovery
        
        Args:
            query_vector: Embedding vector
            collection: Collection name
            top_k: Number of results
            score_threshold: Minimum score
        
        Returns:
            Search results
        """
        try:
            results = self.qdrant.search(
                collection,
                query_vector,
                limit=top_k,
                score_threshold=score_threshold
            )
            return results
        except Exception as e:
            logger.error(f"Error querying Qdrant: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all collections"""
        collections = [
            self.config.storage.qdrant_collection_text,
            self.config.storage.qdrant_collection_structures,
            self.config.storage.qdrant_collection_sequences,
            self.config.storage.qdrant_collection_images
        ]
        
        stats = {}
        for collection in collections:
            stats[collection] = self.qdrant.get_stats(collection)
        return stats
