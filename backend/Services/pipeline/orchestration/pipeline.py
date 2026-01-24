"""
Main pipeline orchestrator
Coordinates all pipeline stages
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from pipeline.collectors.base_collector import BaseCollector, CollectorRecord
from pipeline.ingestion.base_ingester import BaseIngester, IngestedRecord
from pipeline.normalization.normalizer import BaseNormalizer
from pipeline.enrichment.base_enricher import BaseEnricher
from pipeline.embedding.base_embedder import BaseEmbedder
from pipeline.storage.qdrant_client import QdrantClient
from pipeline.config import get_config
from pipeline.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineRecord:
    """Record flowing through the pipeline"""
    id: str
    data_type: str
    source: str
    collection: str
    
    # Original content
    raw_content: Any = None
    
    # Processed content
    content: str = ""
    normalized_content: str = ""
    
    # Embeddings
    embedding: Optional[List[float]] = None
    
    # Metadata (enriched throughout pipeline)
    metadata: Dict[str, Any] = None
    
    # Status tracking
    processed: bool = False
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QDesignPipeline:
    """Main orchestrator for QDesign data pipeline"""
    
    def __init__(self, name: str = "qdesign_pipeline"):
        """
        Initialize pipeline
        
        Args:
            name: Pipeline name
        """
        self.name = name
        self.config = get_config()
        self.qdrant = QdrantClient()
        
        # Component registries
        self.collectors: Dict[str, BaseCollector] = {}
        self.ingesters: Dict[str, BaseIngester] = {}
        self.normalizers: Dict[str, BaseNormalizer] = {}
        self.enrichers: Dict[str, BaseEnricher] = {}
        self.embedders: Dict[str, BaseEmbedder] = {}
        
        # Pipeline state
        self.records: List[PipelineRecord] = []
        
        logger.info(f"Initialized {name}")
    
    def register_collector(self, name: str, collector: BaseCollector) -> None:
        """Register a collector"""
        self.collectors[name] = collector
        logger.debug(f"Registered collector: {name}")
    
    def register_ingester(self, name: str, ingester: BaseIngester) -> None:
        """Register an ingester"""
        self.ingesters[name] = ingester
        logger.debug(f"Registered ingester: {name}")
    
    def register_normalizer(self, name: str, normalizer: BaseNormalizer) -> None:
        """Register a normalizer"""
        self.normalizers[name] = normalizer
        logger.debug(f"Registered normalizer: {name}")
    
    def register_enricher(self, name: str, enricher: BaseEnricher) -> None:
        """Register an enricher"""
        self.enrichers[name] = enricher
        logger.debug(f"Registered enricher: {name}")
    
    def register_embedder(self, name: str, embedder: BaseEmbedder) -> None:
        """Register an embedder"""
        self.embedders[name] = embedder
        logger.debug(f"Registered embedder: {name}")
    
    def collect(self, collector_name: str, *args, **kwargs) -> List[CollectorRecord]:
        """
        Run collection stage
        
        Args:
            collector_name: Name of registered collector
            *args, **kwargs: Arguments for collector
        
        Returns:
            List of collected records
        """
        if collector_name not in self.collectors:
            logger.error(f"Collector not found: {collector_name}")
            return []
        
        logger.info(f"Starting collection with {collector_name}")
        collector = self.collectors[collector_name]
        records = collector.collect(*args, **kwargs)
        logger.info(f"Collected {len(records)} records")
        
        return records
    
    def ingest(self, records: List[CollectorRecord]) -> List[PipelineRecord]:
        """
        Run ingestion stage
        
        Args:
            records: List of collected records
        
        Returns:
            List of ingested records
        """
        logger.info(f"Starting ingestion for {len(records)} records")
        
        pipeline_records = []
        
        for i, record in enumerate(records):
            try:
                # Find appropriate ingester
                source = str(record.raw_content)[:100]
                
                ingester = None
                for ing_name, ing in self.ingesters.items():
                    if ing.can_ingest(str(record.raw_content)):
                        ingester = ing
                        break
                
                if not ingester:
                    logger.warning(f"No ingester found for record {record.id}")
                    continue
                
                # Ingest
                ingested = ingester.ingest(
                    str(record.raw_content),
                    record.id,
                    collection=record.collection
                )
                
                # Convert to pipeline record
                p_record = PipelineRecord(
                    id=record.id,
                    data_type=record.data_type,
                    source=record.source,
                    collection=record.collection,
                    raw_content=record.raw_content,
                    content=ingested.content,
                    metadata=record.metadata or {}
                )
                
                if ingested.error:
                    p_record.error = ingested.error
                else:
                    # Merge ingested metadata into pipeline record metadata
                    p_record.metadata.update(ingested.metadata)
                    p_record.metadata.update({
                        "file_size": ingested.file_size,
                        "content_length": ingested.content_length
                    })
                
                pipeline_records.append(p_record)
                
            except Exception as e:
                logger.error(f"Error ingesting record {record.id}: {e}")
        
        logger.info(f"Ingested {len(pipeline_records)} records")
        self.records = pipeline_records
        return pipeline_records
    
    def normalize(self) -> List[PipelineRecord]:
        """
        Run normalization stage
        
        Returns:
            List of normalized records
        """
        logger.info(f"Starting normalization for {len(self.records)} records")
        
        for record in self.records:
            if record.error:
                continue
            
            # Find appropriate normalizer
            normalizer = None
            for norm_name, norm in self.normalizers.items():
                if norm.is_applicable(record.data_type):
                    normalizer = norm
                    break
            
            if normalizer:
                try:
                    record.normalized_content = normalizer.normalize(
                        record.content,
                        record.metadata
                    )
                except Exception as e:
                    logger.warning(f"Normalization failed for {record.id}: {e}")
                    record.normalized_content = record.content
            else:
                record.normalized_content = record.content
        
        logger.info("Normalization complete")
        return self.records
    
    def enrich(self) -> List[PipelineRecord]:
        """
        Run enrichment stage
        
        Returns:
            List of enriched records
        """
        logger.info(f"Starting enrichment for {len(self.records)} records")
        
        for record in self.records:
            if record.error:
                continue
            
            # Find applicable enrichers
            for enricher_name, enricher in self.enrichers.items():
                if enricher.is_applicable(record.data_type):
                    try:
                        content = record.normalized_content or record.content
                        enriched_metadata = enricher.enrich(
                            content,
                            record.metadata,
                            record.data_type
                        )
                        record.metadata.update(enriched_metadata)
                    except Exception as e:
                        logger.warning(f"Enrichment failed for {record.id}: {e}")
        
        logger.info("Enrichment complete")
        return self.records
    
    def embed(self) -> List[PipelineRecord]:
        """
        Run embedding stage
        
        Returns:
            List of embedded records
        """
        logger.info(f"Starting embedding for {len(self.records)} records")
        
        for record in self.records:
            if record.error:
                continue
            
            # Find appropriate embedder
            embedder = None
            for emb_name, emb in self.embedders.items():
                if emb.is_applicable(record.data_type):
                    embedder = emb
                    break
            
            if embedder:
                try:
                    content = record.normalized_content or record.content
                    embedding = embedder.embed(content, record.metadata)
                    record.embedding = embedding.tolist()
                except Exception as e:
                    logger.warning(f"Embedding failed for {record.id}: {e}")
                    record.error = str(e)
            else:
                logger.warning(f"No embedder found for {record.data_type}")
        
        logger.info("Embedding complete")
        return self.records
    
    def store(self) -> int:
        """
        Store vectors to Qdrant
        
        Returns:
            Number of stored records
        """
        logger.info(f"Starting storage for {len(self.records)} records")
        
        stored_count = 0
        
        for record in self.records:
            if record.error or not record.embedding:
                continue
            
            # Determine collection based on data type
            if record.data_type == "text":
                collection = self.config.qdrant_text_collection
            elif record.data_type == "sequence":
                collection = self.config.qdrant_sequence_collection
            elif record.data_type == "structure":
                collection = self.config.qdrant_structure_collection
            elif record.data_type == "image":
                collection = self.config.qdrant_image_collection
            else:
                logger.warning(f"Unknown data type: {record.data_type}")
                continue
            
            # Store metadata
            payload = {
                "id": record.id,
                "data_type": record.data_type,
                "source": record.source,
                "collection": record.collection,
            }
            payload.update(record.metadata)
            
            # Upsert to Qdrant
            import numpy as np
            if self.qdrant.upsert_vector(
                collection,
                record.id,
                np.array(record.embedding),
                payload
            ):
                stored_count += 1
                record.processed = True
        
        logger.info(f"Stored {stored_count} vectors to Qdrant")
        return stored_count
    
    def run(self, collector_name: str, *args, **kwargs) -> int:
        """
        Run complete pipeline
        
        Args:
            collector_name: Name of collector to use
            *args, **kwargs: Arguments for collector
        
        Returns:
            Number of processed records
        """
        logger.info(f"Starting full pipeline with collector {collector_name}")
        
        # Collection
        collected = self.collect(collector_name, *args, **kwargs)
        
        # Ingestion
        self.ingest(collected)
        
        # Normalization
        self.normalize()
        
        # Enrichment
        self.enrich()
        
        # Embedding
        self.embed()
        
        # Storage
        stored = self.store()
        
        logger.info(f"Pipeline complete. Processed {stored} records")
        return stored
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        total_records = len(self.records)
        processed_records = sum(1 for r in self.records if r.processed)
        error_records = sum(1 for r in self.records if r.error)
        
        return {
            "total_records": total_records,
            "processed_records": processed_records,
            "error_records": error_records,
            "success_rate": processed_records / total_records if total_records > 0 else 0
        }
