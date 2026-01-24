"""
Example script: Collect and process ArXiv papers
Usage: python scripts/collect_arxiv.py --query "protein folding" --max-results 50
"""

import argparse
import sys
from pathlib import Path

# Add Services directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestration.pipeline import QDesignPipeline
from pipeline.collectors.arxiv_collector import ArxivCollector
from pipeline.ingestion.text_ingester import TextIngester, PDFIngester
from pipeline.normalization.text_normalizer import TextNormalizer
from pipeline.enrichment.text_enricher import TextEnricher
from pipeline.embedding.fastembed_embedder import FastembedTextEmbedder
from pipeline.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Collect and process ArXiv papers")
    parser.add_argument("--query", default="protein engineering", help="Search query")
    parser.add_argument("--category", default="q-bio", help="ArXiv category filter")
    parser.add_argument("--max-results", type=int, default=50, help="Max papers to fetch")
    parser.add_argument("--skip-embed", action="store_true", help="Skip embedding stage")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = QDesignPipeline(name="arxiv_collection_pipeline")
    
    # Register components
    pipeline.register_collector("arxiv", ArxivCollector(max_results=args.max_results))
    pipeline.register_ingester("text", TextIngester())
    pipeline.register_ingester("pdf", PDFIngester())
    pipeline.register_normalizer("text", TextNormalizer())
    pipeline.register_enricher("text", TextEnricher())
    
    if not args.skip_embed:
        try:
            pipeline.register_embedder("text", FastembedTextEmbedder())
        except Exception as e:
            logger.warning(f"Could not initialize embedder: {e}")
    
    # Run pipeline
    logger.info(f"Starting ArXiv collection: {args.query}")
    
    # Collect
    collected = pipeline.collect("arxiv", query=args.query, category=args.category)
    logger.info(f"Collected {len(collected)} papers")
    
    # Process
    pipeline.ingest(collected)
    pipeline.normalize()
    pipeline.enrich()
    
    if not args.skip_embed and "text" in pipeline.embedders:
        pipeline.embed()
        pipeline.store()
    
    # Print statistics
    stats = pipeline.get_stats()
    logger.info("=" * 50)
    logger.info(f"Pipeline Statistics:")
    logger.info(f"  Total records: {stats['total_records']}")
    logger.info(f"  Processed: {stats['processed_records']}")
    logger.info(f"  Errors: {stats['error_records']}")
    logger.info(f"  Success rate: {stats['success_rate']:.1%}")
    logger.info("=" * 50)
    
    # Print sample record
    if pipeline.records:
        sample = pipeline.records[0]
        logger.info("\nSample Record:")
        logger.info(f"  ID: {sample.id}")
        logger.info(f"  Type: {sample.data_type}")
        logger.info(f"  Title: {sample.metadata.get('title', 'N/A')[:60]}...")
        if sample.metadata.get('word_count'):
            logger.info(f"  Words: {sample.metadata.get('word_count')}")


if __name__ == "__main__":
    main()
