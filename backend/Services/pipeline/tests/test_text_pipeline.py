#!/usr/bin/env python3
"""
Test text pipeline: collect, ingest, embed, and store text data
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestration.pipeline import QDesignPipeline, CollectorRecord
from pipeline.collectors.base_collector import BaseCollector
from pipeline.ingestion.text_ingester import TextIngester
from pipeline.embedding.fastembed_embedder import FastembedTextEmbedder
from qdrant_client import QdrantClient


class LocalTextCollector(BaseCollector):
    """Collect text files from local filesystem"""
    
    def validate(self, source: str) -> bool:
        """Validate if source is a text file"""
        return source.lower().endswith('.txt')
    
    def collect(self, root_dir: str, **kwargs) -> list:
        """Collect text files"""
        from pathlib import Path
        records = []
        root = Path(root_dir)
        
        for txt_file in root.rglob("*.txt"):
            if txt_file.is_file():
                try:
                    record = CollectorRecord(
                        id=f"text-{txt_file.stem}",
                        data_type="text",
                        source="file",
                        collection=self.collection_name,
                        title=txt_file.name,
                        raw_content=str(txt_file),
                        metadata={
                            "filename": txt_file.name,
                            "size": txt_file.stat().st_size,
                            "path": str(txt_file)
                        }
                    )
                    records.append(record)
                except Exception as e:
                    pass
        
        return records


def create_sample_text_files():
    """Create sample text files for testing"""
    text_dir = Path("../../Data/text")
    text_dir.mkdir(parents=True, exist_ok=True)
    
    samples = {
        "protein_design_01.txt": """
Protein Design and Engineering

Protein design is a computational discipline aimed at designing novel proteins
with specific functions. Modern approaches leverage deep learning, molecular dynamics,
and physics-based scoring functions. Key techniques include:

1. Template-based design: Building on known protein structures
2. De novo design: Creating proteins from scratch
3. Protein modification: Engineering existing proteins for new functions

Applications include enzyme engineering, therapeutic proteins, and biosensors.
        """,
        "dna_binding_02.txt": """
DNA Binding Proteins and Transcription Factors

DNA-binding proteins are essential for gene regulation. They recognize specific
DNA sequences and modulate gene expression. Common DNA-binding domains include:

- Zinc fingers
- Helix-turn-helix motifs
- Basic leucine zippers
- Helix-loop-helix structures

Understanding DNA-protein interactions is crucial for synthetic biology applications.
        """,
        "enzyme_catalysis_03.txt": """
Enzyme Catalysis and Mechanism

Enzymes are biological catalysts that accelerate chemical reactions. The enzyme-substrate
interaction follows the Michaelis-Menten model. Key concepts:

- Activation energy reduction
- Transition state stabilization
- Product release kinetics
- Cofactor requirements

Industrial applications include biofuel production and pharmaceutical synthesis.
        """,
        "folding_prediction_04.txt": """
Protein Folding Prediction Methods

AlphaFold and related methods revolutionized protein structure prediction. These
deep learning models predict 3D structures from amino acid sequences with high accuracy.

Main approaches:
- Multiple sequence alignment (MSA) analysis
- Attention mechanisms
- Confidence scoring
- Template-based refinement

Applications span structural biology, drug discovery, and systems biology.
        """,
        "structural_biology_05.txt": """
Structural Biology and X-ray Crystallography

X-ray crystallography remains a gold standard for determining protein structures.
The process involves:

1. Protein expression and purification
2. Crystal growth and optimization
3. Data collection at synchrotrons
4. Structure determination and refinement

Recent advances include time-resolved crystallography and micro-crystallography.
        """,
    }
    
    created = []
    for filename, content in samples.items():
        filepath = text_dir / filename
        filepath.write_text(content.strip())
        created.append(filename)
        print(f"  • Created {filename}")
    
    return created


def test_text_pipeline():
    """Test complete text pipeline"""
    print(f"\n{'='*70}")
    print(f"TEXT PIPELINE TEST - Collect, Ingest, Embed, Store")
    print(f"{'='*70}\n")
    
    # Step 1: Create sample text files
    print("STEP 1: Prepare text files")
    print("-" * 70)
    
    created = create_sample_text_files()
    print(f"Created {len(created)} text files\n")
    
    # Step 2: Collect text files
    print("STEP 2: Collect local text files")
    print("-" * 70)
    
    pipeline = QDesignPipeline(name="text_pipeline")
    pipeline.register_collector("local", LocalTextCollector("text"))
    pipeline.register_ingester("text", TextIngester())
    pipeline.register_embedder("text", FastembedTextEmbedder())
    
    start = datetime.now()
    collected = pipeline.collect("local", "../../Data", recursive=True)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"Collected {len(collected)} text files in {elapsed:.2f}s")
    
    if not collected:
        print("No text files found!")
        return False
    
    for i, record in enumerate(collected[:5], 1):
        size_mb = record.metadata.get('size', 0) / (1024 * 1024)
        print(f"  {i}. {record.title} ({size_mb:.2f} MB)")
    
    if len(collected) > 5:
        print(f"  ... and {len(collected) - 5} more")
    
    # Step 3: Ingest text files
    print(f"\nSTEP 3: Ingest text files")
    print("-" * 70)
    
    start = datetime.now()
    pipeline.ingest(collected)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"Ingested {len(collected)} text files in {elapsed:.2f}s")
    
    # Step 4: Embed text
    print(f"\nSTEP 4: Embed text to vectors")
    print("-" * 70)
    
    start = datetime.now()
    pipeline.embed()
    elapsed = (datetime.now() - start).total_seconds()
    
    embedded_count = sum(1 for r in pipeline.records if r.embedding is not None and len(r.embedding) > 0 and not r.error)
    print(f"Embedded {embedded_count} texts in {elapsed:.2f}s")
    
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
    
    print(f"Total texts processed: {len(collected)}")
    print(f"Successfully embedded: {embedded_count}")
    print(f"Stored in Qdrant: {stored}")
    print(f"Errors: {sum(1 for r in pipeline.records if r.error)}")
    print(f"Status: {'SUCCESS' if embedded_count > 0 and stored > 0 else 'FAILED'}")
    print(f"{'='*70}\n")
    
    return embedded_count > 0 and stored > 0


if __name__ == "__main__":
    try:
        success = test_text_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
