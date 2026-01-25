"""
Comprehensive AlphaFold Full Pipeline Test
Tests: Collection -> Enrichment -> Ingestion -> Embedding -> Storage -> Retrieval
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import numpy as np

# Add backend Services to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.collectors.alphafold_collector import AlphaFoldCollector
from pipeline.enrichment.alphafold_enricher import AlphaFoldEnricher
from pipeline.embedding.gemini_embedder import GeminiEmbedder
from pipeline.storage.qdrant_client import QdrantClient
from pipeline.logger import get_logger
from pipeline.config import get_config

logger = get_logger(__name__)


class FullPipelineTest:
    """Complete pipeline test for AlphaFold integration"""
    
    def __init__(self):
        """Initialize test components"""
        self.config = get_config()
        self.collector = AlphaFoldCollector()
        self.enricher = AlphaFoldEnricher()
        self.embedder = GeminiEmbedder()
        self.qdrant = QdrantClient()
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "stages": {}
        }
    
    def run_full_test(self):
        """Run the complete pipeline test"""
        print("\n" + "="*80)
        print("AlphaFold Full Pipeline Test")
        print("Collection -> Enrichment -> Embedding -> Storage -> Retrieval")
        print("="*80 + "\n")
        
        test_uniprot_ids = ["P69905", "P68871", "Q99895"]
        
        # Stage 1: Collection
        print("STAGE 1: DATA COLLECTION")
        print("-" * 80)
        collected_records = self._stage_collection(test_uniprot_ids)
        
        if not collected_records:
            print("✗ Collection failed")
            return False
        
        # Stage 2: Enrichment
        print("\n\nSTAGE 2: METADATA ENRICHMENT")
        print("-" * 80)
        enriched_records = self._stage_enrichment(collected_records)
        
        if not enriched_records:
            print("✗ Enrichment failed")
            return False
        
        # Stage 3: Embedding
        print("\n\nSTAGE 3: CONTENT EMBEDDING")
        print("-" * 80)
        embedded_records = self._stage_embedding(enriched_records)
        
        if not embedded_records:
            print("✗ Embedding failed")
            return False
        
        # Stage 4: Storage
        print("\n\nSTAGE 4: VECTOR STORAGE (Qdrant)")
        print("-" * 80)
        stored_records = self._stage_storage(embedded_records)
        
        if not stored_records:
            print("✗ Storage failed")
            return False
        
        # Stage 5: Retrieval & Search
        print("\n\nSTAGE 5: RETRIEVAL & SEMANTIC SEARCH")
        print("-" * 80)
        search_results = self._stage_retrieval(embedded_records)
        
        if search_results is None:
            print("✗ Retrieval failed")
            return False
        
        # Summary
        self._print_summary()
        self._save_results()
        
        return True
    
    def _stage_collection(self, uniprot_ids: list) -> list:
        """Stage 1: Collect data from AlphaFold API"""
        print(f"\nCollecting AlphaFold structures for {len(uniprot_ids)} proteins...")
        
        records = self.collector.collect(uniprot_ids)
        valid_records = self.collector.get_valid_records()
        
        print(f"✓ Collected {len(valid_records)} structures")
        
        # Store stage results
        self.results["stages"]["collection"] = {
            "total": len(records),
            "valid": len(valid_records),
            "errors": len(self.collector.get_error_records()),
            "proteins": [r.metadata.get("uniprot_id") for r in valid_records]
        }
        
        # Print details
        for record in valid_records:
            metadata = record.metadata
            print(f"\n  📦 {metadata.get('uniprot_id')}")
            print(f"     Title: {record.title}")
            print(f"     Models: {metadata.get('models', {}).get('count')}")
            print(f"     pLDDT Scores: {metadata.get('models', {}).get('plddt_scores')}")
            print(f"     Content Length: {len(record.raw_content or '')}")
        
        return valid_records
    
    def _stage_enrichment(self, records: list) -> list:
        """Stage 2: Enrich metadata"""
        print(f"\nEnriching {len(records)} records with quality analysis...")
        
        enriched = []
        for record in records:
            try:
                enriched_metadata = self.enricher.enrich(
                    content=record.raw_content or "",
                    metadata=record.metadata.copy(),
                    data_type="structure"
                )
                record.metadata = enriched_metadata
                enriched.append(record)
            except Exception as e:
                logger.error(f"Failed to enrich {record.metadata.get('uniprot_id')}: {e}")
        
        print(f"✓ Enriched {len(enriched)} records")
        
        # Store stage results
        enrichment_details = []
        for record in enriched:
            metadata = record.metadata
            enrichment_details.append({
                "uniprot_id": metadata.get("uniprot_id"),
                "quality_classification": metadata.get("quality_classification"),
                "plddt_analysis": metadata.get("models", {}).get("plddt_analysis"),
                "use_cases": metadata.get("use_case_recommendations")[:3]
            })
            
            print(f"\n  ✨ {metadata.get('uniprot_id')}")
            if "plddt_analysis" in metadata.get("models", {}):
                plddt = metadata["models"]["plddt_analysis"]
                print(f"     pLDDT Average: {plddt.get('average')}")
                print(f"     Confidence: {plddt.get('overall_confidence')}")
            print(f"     Quality: {metadata.get('quality_classification')}")
            print(f"     Recommendations: {len(metadata.get('use_case_recommendations', []))} use cases")
        
        self.results["stages"]["enrichment"] = enrichment_details
        return enriched
    
    def _stage_embedding(self, records: list) -> list:
        """Stage 3: Generate embeddings"""
        print(f"\nGenerating embeddings for {len(records)} records...")
        
        embedded = []
        for record in records:
            try:
                # Embed the content summary
                content = record.raw_content or ""
                if not content:
                    print(f"\n  ⚠ No content for {record.metadata.get('uniprot_id')}")
                    continue
                
                embedding = self.embedder.embed(content)
                record.embedding = embedding
                embedded.append(record)
                
                uniprot_id = record.metadata.get("uniprot_id")
                print(f"\n  ✓ {uniprot_id}")
                print(f"     Embedding Dimension: {len(embedding)}")
                print(f"     Vector Norm: {np.linalg.norm(embedding):.4f}")
                print(f"     Sample Values: {embedding[:5]}")
                
            except Exception as e:
                logger.error(f"Failed to embed {record.metadata.get('uniprot_id')}: {e}")
        
        print(f"\n✓ Generated {len(embedded)} embeddings")
        
        # Store stage results
        self.results["stages"]["embedding"] = {
            "total_embedded": len(embedded),
            "embedding_dimension": self.embedder.get_dimension(),
            "proteins": [r.metadata.get("uniprot_id") for r in embedded]
        }
        
        return embedded
    
    def _stage_storage(self, records: list) -> list:
        """Stage 4: Store in Qdrant vector database"""
        print(f"\nStoring {len(records)} records in Qdrant...")
        
        # Ensure structure collection exists
        collection_name = self.config.storage.qdrant_collection_structures
        self.qdrant.ensure_collection(collection_name, self.embedder.get_dimension())
        
        stored = []
        for record in records:
            try:
                embedding = record.embedding
                metadata = record.metadata
                
                # Prepare payload with metadata
                payload = {
                    "uniprot_id": metadata.get("uniprot_id"),
                    "title": record.title,
                    "source": record.source,
                    "data_type": record.data_type,
                    "plddt_score": float(metadata.get("models", {}).get("plddt_analysis", {}).get("average", 0)),
                    "quality": metadata.get("quality_classification", {}),
                    "protein_name": metadata.get("uniprot", {}).get("protein_name", ""),
                    "sequence_length": int(metadata.get("uniprot", {}).get("sequence_length", 0)),
                    "organism": metadata.get("uniprot", {}).get("organism", {}),
                    "metadata": json.dumps(metadata, default=str)  # Store full metadata as JSON string
                }
                
                # Upsert to Qdrant
                success = self.qdrant.upsert_vector(
                    collection_name=collection_name,
                    record_id=record.id,
                    vector=embedding,
                    metadata=payload
                )
                
                if success:
                    stored.append(record)
                    uniprot_id = metadata.get("uniprot_id")
                    print(f"\n  💾 {uniprot_id}")
                    print(f"     ID: {record.id}")
                    print(f"     Collection: {collection_name}")
                    print(f"     pLDDT: {payload['plddt_score']}")
                else:
                    logger.error(f"Failed to store {record.id}")
                    
            except Exception as e:
                logger.error(f"Failed to store record: {e}")
        
        print(f"\n✓ Stored {len(stored)} records")
        
        # Store stage results
        self.results["stages"]["storage"] = {
            "collection": collection_name,
            "total_stored": len(stored),
            "vector_dimension": self.embedder.get_dimension(),
            "record_ids": [r.id for r in stored]
        }
        
        return stored
    
    def _stage_retrieval(self, records: list) -> dict:
        """Stage 5: Test retrieval and semantic search"""
        print(f"\nTesting retrieval and semantic search...")
        
        collection_name = self.config.storage.qdrant_collection_structures
        
        # Test 1: Get all points
        print(f"\n  Test 1: Retrieve all stored points")
        try:
            points = self.qdrant.client.get_collection(collection_name)
            point_count = points.points_count
            print(f"  ✓ Collection has {point_count} points")
        except Exception as e:
            print(f"  ✗ Failed to get collection info: {e}")
            return None
        
        # Test 2: Semantic search
        print(f"\n  Test 2: Semantic search")
        if records:
            # Use the first record's embedding as query
            query_record = records[0]
            query_embedding = query_record.embedding
            query_id = query_record.metadata.get("uniprot_id")
            
            print(f"     Query: {query_id}")
            
            try:
                # Use the search method from our Qdrant client wrapper
                search_results = self.qdrant.search(
                    collection_name=collection_name,
                    vector=query_embedding,
                    limit=10
                )
                
                print(f"  ✓ Found {len(search_results)} similar structures")
                
                for i, result in enumerate(search_results, 1):
                    score = result.get("score", "N/A")
                    payload = result.get("metadata", {})
                    print(f"\n     [{i}] Score: {score}")
                    print(f"         UniProt: {payload.get('uniprot_id')}")
                    print(f"         pLDDT: {payload.get('plddt_score')}")
                    
            except Exception as e:
                print(f"  ✗ Search failed: {e}")
                logger.error(f"Search error: {e}", exc_info=True)
                return None
        
        # Test 3: Metadata filtering
        print(f"\n  Test 3: Metadata filtering (high confidence)")
        try:
            high_conf_results = self.qdrant.client.scroll(
                collection_name=collection_name,
                limit=100
            )
            
            if high_conf_results and hasattr(high_conf_results, 'points'):
                high_conf = [p for p in high_conf_results.points 
                           if p.payload.get('plddt_score', 0) >= 70]
                
                print(f"  ✓ Found {len(high_conf)} high-confidence structures (pLDDT >= 70)")
                for result in high_conf:
                    payload = result.payload
                    print(f"     - {payload.get('uniprot_id')}: {payload.get('plddt_score')}")
                    
        except Exception as e:
            print(f"  ✗ Filtering failed: {e}")
            return None
        
        # Store stage results
        self.results["stages"]["retrieval"] = {
            "collection_points": point_count,
            "search_results": len(search_results) if 'search_results' in locals() else 0,
            "high_confidence_count": len(high_conf) if 'high_conf' in locals() else 0
        }
        
        return {"success": True}
    
    def _print_summary(self):
        """Print test summary"""
        print("\n\n" + "="*80)
        print("PIPELINE TEST SUMMARY")
        print("="*80)
        
        stages = self.results.get("stages", {})
        
        print("\n✓ Collection Stage:")
        collection = stages.get("collection", {})
        print(f"  - Proteins collected: {collection.get('valid', 0)}")
        print(f"  - Errors: {collection.get('errors', 0)}")
        
        print("\n✓ Enrichment Stage:")
        enrichment = stages.get("enrichment", [])
        print(f"  - Records enriched: {len(enrichment)}")
        
        print("\n✓ Embedding Stage:")
        embedding = stages.get("embedding", {})
        print(f"  - Records embedded: {embedding.get('total_embedded', 0)}")
        print(f"  - Embedding dimension: {embedding.get('embedding_dimension', 0)}")
        
        print("\n✓ Storage Stage:")
        storage = stages.get("storage", {})
        print(f"  - Records stored: {storage.get('total_stored', 0)}")
        print(f"  - Collection: {storage.get('collection', 'N/A')}")
        
        print("\n✓ Retrieval Stage:")
        retrieval = stages.get("retrieval", {})
        print(f"  - Points in collection: {retrieval.get('collection_points', 0)}")
        print(f"  - Semantic search results: {retrieval.get('search_results', 0)}")
        print(f"  - High-confidence structures: {retrieval.get('high_confidence_count', 0)}")
        
        print("\n" + "="*80)
        print("✅ FULL PIPELINE TEST COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
    
    def _save_results(self):
        """Save test results to file"""
        output_file = Path(__file__).parent / "tests" / "alphafold_full_pipeline_test_output.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"Results saved to: {output_file}")


def main():
    """Run full pipeline test"""
    try:
        tester = FullPipelineTest()
        success = tester.run_full_test()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
