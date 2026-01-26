"""
Fixed ArXiv collection script - Simple and reliable
Usage: python scripts/collect_arxiv_working.py --query "protein design" --max-results 5
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


def main():
    parser = argparse.ArgumentParser(description="Collect and process ArXiv papers")
    parser.add_argument("--query", default="protein engineering", help="Search query")
    parser.add_argument("--category", default="q-bio", help="ArXiv category filter")
    parser.add_argument("--max-results", type=int, default=50, help="Max papers to fetch")
    parser.add_argument("--skip-embed", action="store_true", help="Skip embedding stage")
    
    args = parser.parse_args()
    
    try:
        # Initialize components
        print("Initializing components...")
        collector = ArxivCollector(max_results=args.max_results)
        normalizer = TextNormalizer()
        enricher = TextEnricher()
        qdrant = QdrantClient()
        
        embedder = None
        if not args.skip_embed:
            try:
                print("Initializing embedder...")
                embedder = GeminiEmbedder()
                print(" Embedder ready")
            except Exception as e:
                print(f"⚠ Could not initialize embedder: {e}")
        
        # Collect from arXiv
        print(f"Starting ArXiv collection: query='{args.query}', category='{args.category}'")
        records = collector.collect(query=args.query, category=args.category)
        print(f" Collected {len(records)} papers")
        
        if not records:
            print("⚠ No records collected")
            return
        
        # Process each record
        stored_count = 0
        error_count = 0
        
        for i, record in enumerate(records, 1):
            try:
                print(f"\n[{i}/{len(records)}] {record.title[:60]}...")
                
                # Normalize
                normalized_content = normalizer.normalize(record.raw_content)
                print(f"   Normalized ({len(normalized_content)} chars)")
                
                # Enrich
                enriched_metadata = enricher.enrich(normalized_content, record.metadata, "text")
                if isinstance(enriched_metadata, dict):
                    record.metadata.update(enriched_metadata)
                print(f"   Enriched ({enriched_metadata.get('word_count', 0)} words)")
                
                # Embed and store
                if embedder:
                    try:
                        embedding = embedder.embed(normalized_content, record.metadata)
                        print(f"   Embedded ({len(embedding)} dims)")
                        
                        # Store in Qdrant
                        qdrant.upsert_vector(
                            collection_name="qdesign_text",
                            record_id=record.metadata.get("arxiv_id", record.id),
                            vector=embedding,
                            metadata={
                                "title": record.title,
                                "arxiv_id": record.metadata.get("arxiv_id"),
                                "authors": ", ".join(record.metadata.get("authors", [])),
                                "source_url": record.source_url,
                                "date_published": str(record.date_published) if record.date_published else None,
                                "content": normalized_content[:500],
                                "keywords": record.metadata.get("keywords", []),
                                "word_count": enriched_metadata.get("word_count", 0),
                            }
                        )
                        print(f"   Stored in Qdrant")
                        stored_count += 1
                    except Exception as e:
                        print(f"  ✗ Embedding/storage failed: {e}")
                        error_count += 1
                else:
                    print(f"  ⊘ Skipped storage (embeddings disabled)")
                    stored_count += 1
                    
            except Exception as e:
                print(f"  ✗ Error processing record: {e}")
                error_count += 1
        
        # Print summary
        print("\n" + "="*60)
        print(f" COMPLETE")
        print("="*60)
        print(f"Collected:  {len(records)} papers")
        print(f"Processed:  {stored_count} successfully")
        print(f"Errors:     {error_count}")
        print(f"Success:    {100*stored_count/len(records):.1f}%")
        print("="*60)
        
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
