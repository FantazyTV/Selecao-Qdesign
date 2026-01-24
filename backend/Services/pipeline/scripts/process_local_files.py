"""
Example script: Process local files
Usage: python scripts/process_local_files.py --input-dir /path/to/files --data-type text
"""

import argparse
import sys
from pathlib import Path

# Add Services directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestration.pipeline import QDesignPipeline
from pipeline.ingestion.text_ingester import TextIngester, PDFIngester
from pipeline.ingestion.protein_ingester import SequenceIngester, StructureIngester
from pipeline.ingestion.image_ingester import ImageIngester
from pipeline.normalization.text_normalizer import TextNormalizer
from pipeline.normalization.protein_normalizer import SequenceNormalizer, StructureNormalizer
from pipeline.enrichment.text_enricher import TextEnricher
from pipeline.enrichment.protein_enricher import SequenceEnricher, StructureEnricher
from pipeline.embedding.fastembed_embedder import FastembedTextEmbedder, FastembedImageEmbedder
from pipeline.embedding.esm_embedder import ESMSequenceEmbedder, ESMStructureEmbedder
from pipeline.collectors.base_collector import BaseCollector, CollectorRecord
from pipeline.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


class LocalFileCollector(BaseCollector):
    """Collector for local files"""
    
    def __init__(self, data_type: str):
        super().__init__("local_files")
        self.data_type = data_type
    
    def collect(self, directory: str, pattern: str = "*", recursive: bool = True):
        """Collect files from directory"""
        self.records = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory}")
            return self.records
        
        # Find files matching pattern
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))
        
        logger.info(f"Found {len(files)} files in {directory}")
        
        for file_path in files:
            try:
                record = CollectorRecord(
                    data_type=self.data_type,
                    source="local_file",
                    collection=self.collection_name,
                    raw_content=str(file_path),  # Store file path
                    source_url=str(file_path),
                    title=file_path.name,
                    metadata={"file_path": str(file_path)}
                )
                self.add_record(record)
            except Exception as e:
                logger.warning(f"Failed to create record for {file_path}: {e}")
        
        return self.records
    
    def validate(self, record: CollectorRecord) -> bool:
        """Validate file collector record"""
        return Path(record.raw_content).exists()


def main():
    parser = argparse.ArgumentParser(description="Process local files")
    parser.add_argument("--input-dir", required=True, help="Input directory")
    parser.add_argument("--data-type", default="text", 
                        choices=["text", "sequence", "structure", "image"],
                        help="Data type")
    parser.add_argument("--pattern", default="*", help="File pattern")
    parser.add_argument("--recursive", action="store_true", default=True, help="Recursive search")
    parser.add_argument("--skip-embed", action="store_true", help="Skip embedding")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = QDesignPipeline(name="local_file_pipeline")
    
    # Register collector
    pipeline.register_collector("local", LocalFileCollector(args.data_type))
    
    # Register ingesters based on data type
    if args.data_type == "text":
        pipeline.register_ingester("text", TextIngester())
        pipeline.register_ingester("pdf", PDFIngester())
        pipeline.register_normalizer("text", TextNormalizer())
        pipeline.register_enricher("text", TextEnricher())
        if not args.skip_embed:
            try:
                pipeline.register_embedder("text", FastembedTextEmbedder())
            except Exception as e:
                logger.warning(f"Could not load text embedder: {e}")
    
    elif args.data_type == "sequence":
        pipeline.register_ingester("sequence", SequenceIngester())
        pipeline.register_normalizer("sequence", SequenceNormalizer())
        pipeline.register_enricher("sequence", SequenceEnricher())
        if not args.skip_embed:
            try:
                pipeline.register_embedder("sequence", ESMSequenceEmbedder())
            except Exception as e:
                logger.warning(f"Could not load sequence embedder: {e}")
    
    elif args.data_type == "structure":
        pipeline.register_ingester("structure", StructureIngester())
        pipeline.register_normalizer("structure", StructureNormalizer())
        pipeline.register_enricher("structure", StructureEnricher())
        if not args.skip_embed:
            try:
                pipeline.register_embedder("structure", ESMStructureEmbedder())
            except Exception as e:
                logger.warning(f"Could not load structure embedder: {e}")
    
    elif args.data_type == "image":
        pipeline.register_ingester("image", ImageIngester())
        if not args.skip_embed:
            try:
                pipeline.register_embedder("image", FastembedImageEmbedder())
            except Exception as e:
                logger.warning(f"Could not load image embedder: {e}")
    
    # Run pipeline
    logger.info(f"Processing {args.data_type} files from {args.input_dir}")
    
    collected = pipeline.collect("local", args.input_dir, args.pattern, args.recursive)
    logger.info(f"Collected {len(collected)} files")
    
    pipeline.ingest(collected)
    
    if args.data_type != "image":
        pipeline.normalize()
        pipeline.enrich()
    
    if not args.skip_embed:
        pipeline.embed()
        pipeline.store()
    
    # Statistics
    stats = pipeline.get_stats()
    logger.info("=" * 50)
    logger.info(f"Processing Complete:")
    logger.info(f"  Files: {stats['total_records']}")
    logger.info(f"  Stored: {stats['processed_records']}")
    logger.info(f"  Errors: {stats['error_records']}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
