#!/usr/bin/env python3
"""
Test sequence pipeline: collect, ingest, embed, and store biological sequence data
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestration.pipeline import QDesignPipeline, CollectorRecord
from pipeline.collectors.base_collector import BaseCollector
from pipeline.ingestion.protein_ingester import SequenceIngester
from pipeline.embedding.fastembed_embedder import FastembedSequenceEmbedder
from qdrant_client import QdrantClient


class LocalSequenceCollector(BaseCollector):
    """Collect biological sequence files from local filesystem"""
    
    def validate(self, source: str) -> bool:
        """Validate if source is a FASTA file"""
        return source.lower().endswith(('.fasta', '.fa'))
    
    def collect(self, root_dir: str, **kwargs) -> list:
        """Collect FASTA sequence files"""
        from pathlib import Path
        records = []
        root = Path(root_dir)
        
        for fasta_file in list(root.rglob("*.fasta")) + list(root.rglob("*.fa")):
            if fasta_file.is_file():
                try:
                    record = CollectorRecord(
                        id=f"seq-{fasta_file.stem}",
                        data_type="sequence",
                        source="file",
                        collection=self.collection_name,
                        title=fasta_file.name,
                        raw_content=str(fasta_file),
                        metadata={
                            "filename": fasta_file.name,
                            "size": fasta_file.stat().st_size,
                            "path": str(fasta_file)
                        }
                    )
                    records.append(record)
                except Exception as e:
                    pass
        
        return records


def create_sample_sequence_files():
    """Create sample biological sequence files for testing"""
    seq_dir = Path("../../Data/sequences")
    seq_dir.mkdir(parents=True, exist_ok=True)
    
    samples = {
        "protein_01.fasta": """>sp|P12345|ProteinA_HUMAN
MSVSTPTSSYGYFPDSDYTDDDDTETPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPT
""",
        "protein_02.fasta": """>sp|P67890|ProteinB_HUMAN
MSDEFGHIKLMNPQRSTVWYLCAGSPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFP
FPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFP
FPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFPFP
""",
        "dna_01.fasta": """>NC_000001|Human chromosome 1
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT
CGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC
TATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATAT
GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC
""",
        "rna_01.fasta": """>NR_000001|RNA sequence
AUGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUA
GCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCU
AGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCUAGCU
""",
        "protein_03.fasta": """>sp|Q12345|ProteinC_HUMAN
MVGGSLPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
""",
    }
    
    created = []
    for filename, content in samples.items():
        filepath = seq_dir / filename
        filepath.write_text(content.strip())
        created.append(filename)
        print(f"  • Created {filename}")
    
    return created


def test_sequence_pipeline():
    """Test complete sequence pipeline"""
    print(f"\n{'='*70}")
    print(f"SEQUENCE PIPELINE TEST - Collect, Ingest, Embed, Store")
    print(f"{'='*70}\n")
    
    # Step 1: Create sample sequence files
    print("STEP 1: Prepare sequence files")
    print("-" * 70)
    
    created = create_sample_sequence_files()
    print(f"Created {len(created)} sequence files\n")
    
    # Step 2: Collect sequence files
    print("STEP 2: Collect local sequence files")
    print("-" * 70)
    
    pipeline = QDesignPipeline(name="sequence_pipeline")
    pipeline.register_collector("local", LocalSequenceCollector("sequence"))
    pipeline.register_ingester("sequence", SequenceIngester())
    pipeline.register_embedder("sequence", FastembedSequenceEmbedder())
    
    start = datetime.now()
    collected = pipeline.collect("local", "../../Data", recursive=True)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"Collected {len(collected)} sequence files in {elapsed:.2f}s")
    
    if not collected:
        print("No sequence files found!")
        return False
    
    for i, record in enumerate(collected[:5], 1):
        size_mb = record.metadata.get('size', 0) / (1024 * 1024)
        print(f"  {i}. {record.title} ({size_mb:.2f} MB)")
    
    if len(collected) > 5:
        print(f"  ... and {len(collected) - 5} more")
    
    # Step 3: Ingest sequence files
    print(f"\nSTEP 3: Ingest sequence files")
    print("-" * 70)
    
    start = datetime.now()
    pipeline.ingest(collected)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"Ingested {len(collected)} sequence files in {elapsed:.2f}s")
    
    # Step 4: Embed sequences
    print(f"\nSTEP 4: Embed sequences to vectors")
    print("-" * 70)
    
    start = datetime.now()
    pipeline.embed()
    elapsed = (datetime.now() - start).total_seconds()
    
    embedded_count = sum(1 for r in pipeline.records if r.embedding is not None and len(r.embedding) > 0 and not r.error)
    print(f"Embedded {embedded_count} sequences in {elapsed:.2f}s")
    
    # Step 5: Store in Qdrant
    print(f"\nSTEP 5: Store vectors in Qdrant")
    print("-" * 70)
    
    try:
        start = datetime.now()
        stored = pipeline.store()
        elapsed = (datetime.now() - start).total_seconds()
        
        print(f"Stored {stored} vectors in {elapsed:.2f}s")
        
        # Verify storage
        client = QdrantClient("localhost", port=6333)
        
        print(f"\nQdrant Status:")
        for collection_name in ["qdesign_sequences", "qdesign_text", "qdesign_images", "qdesign_structures"]:
            try:
                info = client.get_collection(collection_name)
                print(f"  • {collection_name}: {info.points_count} vectors")
            except:
                print(f"  • {collection_name}: 0 vectors")
        
    except Exception as e:
        print(f"Error storing to Qdrant: {e}")
        print("Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant")
        return False
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}")
    
    print(f"Total sequences processed: {len(collected)}")
    print(f"Successfully embedded: {embedded_count}")
    print(f"Stored in Qdrant: {stored}")
    print(f"Errors: {sum(1 for r in pipeline.records if r.error)}")
    print(f"Status: {'SUCCESS' if embedded_count > 0 and stored > 0 else 'FAILED'}")
    print(f"{'='*70}\n")
    
    return embedded_count > 0 and stored > 0


if __name__ == "__main__":
    try:
        success = test_sequence_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
