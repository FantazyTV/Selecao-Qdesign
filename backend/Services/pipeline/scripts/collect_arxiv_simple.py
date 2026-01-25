"""
Simple ArXiv collection script without complex ingester pipeline
Usage: python scripts/collect_arxiv_simple.py --query "protein design" --max-results 5
"""

import argparse
import sys
from pathlib import Path

# Add Services directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.collectors.arxiv_collector import ArxivCollector
from pipeline.normalization.text_normalizer import TextNormalizer
from pipeline.enrichment.text_enricher import TextEnricher
from pipeline.embedding.gemini_embedder import GeminiEmbedder
from pipeline.storage.qdrant_client import QdrantClient
from pipeline.logger import get_logger
from pipeline.config import get_config

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Collect and process ArXiv papers")
    parser.add_argument("--query", default="protein engineering", help="Search query")
    parser.add_argument("--category", default="q-bio", help="ArXiv category filter")
    parser.add_argument("--max-results", type=int, default=50, help="Max papers to fetch")
    parser.add_argument("--skip-embed", action="store_true", help="Skip embedding stage")
    
    args = parser.parse_args()
    
    # Initialize components
    logger.info("Initializing components...")
    collector = ArxivCollector(max_results=args.max_results)
    normalizer = TextNormalizer()
    enricher = TextEnricher()
    qdrant = QdrantClient()
    
    embedder = None
    if not args.skip_embed:
        try:
            logger.info("Initializing embedder (this may take a moment for first run)...")
            embedder = GeminiEmbedder()
            logger.info(" Embedder initialized")
        except Exception as e:
            logger.warning(f"Could not initialize embedder: {e}")
            logger.warning("Will store vectors without embeddings for now")
            embedder = None
    
    # Collect
    logger.info(f"Starting ArXiv collection: {args.query}")
    records = collector.collect(query=args.query, category=args.category)
    logger.info(f"Collected {len(records)} papers")
    
    if not records:
        logger.warning("No records collected")
        return
    
    # Process each record
    stored_count = 0
    for i, record in enumerate(records, 1):
        try:
            logger.info(f"\n[{i}/{len(records)}] Processing: {record.title[:60]}...")
            
            # Normalize
            normalized_content = normalizer.normalize(record.raw_content)
            logger.info(f"   Normalized ({len(normalized_content)} chars)")
            
            # Enrich
            enriched_metadata = enricher.enrich(normalized_content, record.metadata, "text")
            if isinstance(enriched_metadata, dict):
                record.metadata.update(enriched_metadata)
            logger.info(f"   Enriched")
            
            # Embed
            if embedder:
                try:
                    embedding = embedder.embed(normalized_content, record.metadata)
                    logger.info(f"   Embedded ({len(embedding)} dims)")
                except Exception as e:
                    logger.warning(f"  ⊘ Embedding failed: {e}")
                    embedding = None
            else:
                embedding = None
            
            # Store
            payload = {
                "title": record.title,
                "arxiv_id": record.metadata.get("arxiv_id"),
                "authors": ", ".join(record.metadata.get("authors", [])),
                "source_url": record.source_url,
                "date_published": str(record.date_published) if record.date_published else None,
                "content": normalized_content[:500],
                "keywords": record.metadata.get("keywords", []),
            }
            
            if embedding is not None:
                qdrant.store_vector(
                    collection="qdesign_text",
                    vector=embedding,
                    payload=payload
                )
                logger.info(f"   Stored in Qdrant with embedding")
            else:
                logger.info(f"  ⊘ Skipped Qdrant storage (no embedding available)")
            
            stored_count += 1
        
        except Exception as e:
            logger.error(f"  ✗ Error processing record: {e}")
    
    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info(f" Successfully processed and stored {stored_count}/{len(records)} papers")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
