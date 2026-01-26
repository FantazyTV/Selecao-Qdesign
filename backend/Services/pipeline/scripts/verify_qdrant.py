"""
Example script: Verify Qdrant and show collections
Usage: python scripts/verify_qdrant.py
"""

import sys
from pathlib import Path

# Add Services directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.storage.qdrant_client import QdrantClient
from pipeline.config import get_config
from pipeline.logger import get_logger

logger = get_logger(__name__)


def main():
    logger.info("Verifying Qdrant connection...")
    
    try:
        config = get_config()
        client = QdrantClient()
        
        logger.info(f" Connected to Qdrant at {config.qdrant_url}")
        
        # Show collections
        logger.info("\nAvailable Collections:")
        
        collections = [
            config.qdrant_text_collection,
            config.qdrant_sequence_collection,
            config.qdrant_structure_collection,
            config.qdrant_image_collection,
        ]
        
        for collection_name in collections:
            try:
                stats = client.get_stats(collection_name)
                logger.info(f"\n  {collection_name}:")
                logger.info(f"    Points: {stats.get('points_count', 'N/A')}")
                logger.info(f"    Vectors: {stats.get('vectors_count', 'N/A')}")
            except:
                logger.info(f"\n  {collection_name}: (not created yet)")
        
        logger.info("\n Qdrant verification complete")
        
    except Exception as e:
        logger.error(f"✗ Failed to connect to Qdrant: {e}")
        logger.error("Make sure Qdrant is running: docker-compose up qdrant")
        sys.exit(1)


if __name__ == "__main__":
    main()
