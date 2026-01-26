#!/usr/bin/env python3
"""
Test structure pipeline: collect, ingest, embed, and store protein structure data
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestration.pipeline import QDesignPipeline, CollectorRecord
from pipeline.collectors.base_collector import BaseCollector
from pipeline.ingestion.protein_ingester import StructureIngester
from pipeline.embedding.fastembed_embedder import StructureEmbedder
from qdrant_client import QdrantClient


class LocalStructureCollector(BaseCollector):
    """Collect protein structure files from local filesystem"""
    
    def validate(self, source: str) -> bool:
        """Validate if source is a PDB file"""
        return source.lower().endswith('.pdb')
    
    def collect(self, root_dir: str, **kwargs) -> list:
        """Collect PDB structure files"""
        from pathlib import Path
        records = []
        root = Path(root_dir)
        
        for pdb_file in root.rglob("*.pdb"):
            if pdb_file.is_file():
                try:
                    record = CollectorRecord(
                        id=f"struct-{pdb_file.stem}",
                        data_type="structure",
                        source="file",
                        collection=self.collection_name,
                        title=pdb_file.name,
                        raw_content=str(pdb_file),
                        metadata={
                            "filename": pdb_file.name,
                            "size": pdb_file.stat().st_size,
                            "path": str(pdb_file)
                        }
                    )
                    records.append(record)
                except Exception as e:
                    pass
        
        return records


def create_sample_structure_files():
    """Create sample PDB structure files for testing"""
    struct_dir = Path("../../Data/structures")
    struct_dir.mkdir(parents=True, exist_ok=True)
    
    # Minimal PDB format with CA atoms
    samples = {
        "1MBN.pdb": """HEADER    PROTEIN STRUCTURE
TITLE     SAMPLE PROTEIN STRUCTURE
REMARK    Test PDB file with C-alpha atoms
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C
ATOM      2  CA  ALA A   2       3.800   0.000   0.000  1.00  0.00           C
ATOM      3  CA  ALA A   3       7.600   0.000   0.000  1.00  0.00           C
ATOM      4  CA  ALA A   4      11.400   0.000   0.000  1.00  0.00           C
ATOM      5  CA  LEU A   5      15.200   0.000   0.000  1.00  0.00           C
ATOM      6  CA  GLU A   6      19.000   0.000   0.000  1.00  0.00           C
ATOM      7  CA  ASP A   7      22.800   0.000   0.000  1.00  0.00           C
ATOM      8  CA  VAL A   8      26.600   0.000   0.000  1.00  0.00           C
ATOM      9  CA  ILE A   9      30.400   0.000   0.000  1.00  0.00           C
ATOM     10  CA  PRO A  10      34.200   0.000   0.000  1.00  0.00           C
END
""",
        "2MBN.pdb": """HEADER    PROTEIN STRUCTURE
TITLE     SAMPLE PROTEIN STRUCTURE 2
REMARK    Test PDB file with alpha helix
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00  0.00           C
ATOM      2  CA  ALA A   2       1.500   2.700   0.000  1.00  0.00           C
ATOM      3  CA  ALA A   3       1.500   5.400   1.500  1.00  0.00           C
ATOM      4  CA  LEU A   4       0.000   8.100   1.500  1.00  0.00           C
ATOM      5  CA  GLU A   5      -1.500   5.400   3.000  1.00  0.00           C
ATOM      6  CA  ASP A   6      -1.500   2.700   3.000  1.00  0.00           C
ATOM      7  CA  VAL A   7       0.000   0.000   4.500  1.00  0.00           C
ATOM      8  CA  ILE A   8       1.500  -2.700   4.500  1.00  0.00           C
ATOM      9  CA  PRO A   9       1.500  -5.400   6.000  1.00  0.00           C
ATOM     10  CA  SER A  10       0.000  -8.100   6.000  1.00  0.00           C
END
""",
        "3MBN.pdb": """HEADER    PROTEIN STRUCTURE
TITLE     SAMPLE PROTEIN STRUCTURE 3
REMARK    Test PDB file with beta sheet
ATOM      1  CA  VAL A   1       0.000   0.000   0.000  1.00  0.00           C
ATOM      2  CA  ILE A   2       3.300   0.000   0.000  1.00  0.00           C
ATOM      3  CA  THR A   3       6.600   0.000   0.000  1.00  0.00           C
ATOM      4  CA  VAL A   4       9.900   0.000   0.000  1.00  0.00           C
ATOM      5  CA  LEU A   5      13.200   0.000   0.000  1.00  0.00           C
ATOM      6  CA  GLY A   6      16.500   0.000   0.000  1.00  0.00           C
ATOM      7  CA  ALA A   7      19.800   0.000   0.000  1.00  0.00           C
ATOM      8  CA  PHE A   8      23.100   0.000   0.000  1.00  0.00           C
ATOM      9  CA  TRP A   9      26.400   0.000   0.000  1.00  0.00           C
ATOM     10  CA  TYR A  10      29.700   0.000   0.000  1.00  0.00           C
END
""",
        "4MBN.pdb": """HEADER    PROTEIN STRUCTURE
TITLE     SAMPLE PROTEIN STRUCTURE 4
REMARK    Complex structure with turns
ATOM      1  CA  SER A   1       0.000   0.000   0.000  1.00  0.00           C
ATOM      2  CA  ASP A   2       2.000   2.000   1.000  1.00  0.00           C
ATOM      3  CA  ASN A   3       4.000   0.000   2.000  1.00  0.00           C
ATOM      4  CA  GLN A   4       6.000   3.000   1.000  1.00  0.00           C
ATOM      5  CA  CYS A   5       8.000   1.000   3.000  1.00  0.00           C
ATOM      6  CA  HIS A   6      10.000   4.000   2.000  1.00  0.00           C
ATOM      7  CA  LYS A   7      12.000   2.000   4.000  1.00  0.00           C
ATOM      8  CA  ARG A   8      14.000   5.000   3.000  1.00  0.00           C
ATOM      9  CA  MET A   9      16.000   3.000   5.000  1.00  0.00           C
ATOM     10  CA  TRP A  10      18.000   6.000   4.000  1.00  0.00           C
END
""",
        "5MBN.pdb": """HEADER    PROTEIN STRUCTURE
TITLE     SAMPLE PROTEIN STRUCTURE 5
REMARK    Extended conformation
ATOM      1  CA  GLY A   1       0.000   0.000   0.000  1.00  0.00           C
ATOM      2  CA  ALA A   2       3.700   0.000   0.000  1.00  0.00           C
ATOM      3  CA  GLY A   3       7.400   0.000   0.000  1.00  0.00           C
ATOM      4  CA  ALA A   4      11.100   0.000   0.000  1.00  0.00           C
ATOM      5  CA  GLY A   5      14.800   0.000   0.000  1.00  0.00           C
ATOM      6  CA  ALA A   6      18.500   0.000   0.000  1.00  0.00           C
ATOM      7  CA  GLY A   7      22.200   0.000   0.000  1.00  0.00           C
ATOM      8  CA  ALA A   8      25.900   0.000   0.000  1.00  0.00           C
ATOM      9  CA  GLY A   9      29.600   0.000   0.000  1.00  0.00           C
ATOM     10  CA  ALA A  10      33.300   0.000   0.000  1.00  0.00           C
END
""",
    }
    
    created = []
    for filename, content in samples.items():
        filepath = struct_dir / filename
        filepath.write_text(content.strip())
        created.append(filename)
        print(f"  • Created {filename}")
    
    return created


def test_structure_pipeline():
    """Test complete structure pipeline"""
    print(f"\n{'='*70}")
    print(f"STRUCTURE PIPELINE TEST - Collect, Ingest, Embed, Store")
    print(f"{'='*70}\n")
    
    # Step 1: Create sample structure files
    print("STEP 1: Prepare structure files")
    print("-" * 70)
    
    created = create_sample_structure_files()
    print(f"Created {len(created)} structure files\n")
    
    # Step 2: Collect structure files
    print("STEP 2: Collect local structure files")
    print("-" * 70)
    
    pipeline = QDesignPipeline(name="structure_pipeline")
    pipeline.register_collector("local", LocalStructureCollector("structure"))
    pipeline.register_ingester("structure", StructureIngester())
    pipeline.register_embedder("structure", StructureEmbedder())
    
    start = datetime.now()
    collected = pipeline.collect("local", "../../Data", recursive=True)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"Collected {len(collected)} structure files in {elapsed:.2f}s")
    
    if not collected:
        print("No structure files found!")
        return False
    
    for i, record in enumerate(collected[:5], 1):
        size_mb = record.metadata.get('size', 0) / (1024 * 1024)
        print(f"  {i}. {record.title} ({size_mb:.2f} MB)")
    
    if len(collected) > 5:
        print(f"  ... and {len(collected) - 5} more")
    
    # Step 3: Ingest structure files
    print(f"\nSTEP 3: Ingest structure files")
    print("-" * 70)
    
    start = datetime.now()
    pipeline.ingest(collected)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"Ingested {len(collected)} structure files in {elapsed:.2f}s")
    
    # Step 4: Embed structures
    print(f"\nSTEP 4: Embed structures to vectors")
    print("-" * 70)
    
    start = datetime.now()
    pipeline.embed()
    elapsed = (datetime.now() - start).total_seconds()
    
    embedded_count = sum(1 for r in pipeline.records if r.embedding is not None and len(r.embedding) > 0 and not r.error)
    print(f"Embedded {embedded_count} structures in {elapsed:.2f}s")
    
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
    
    print(f"Total structures processed: {len(collected)}")
    print(f"Successfully embedded: {embedded_count}")
    print(f"Stored in Qdrant: {stored}")
    print(f"Errors: {sum(1 for r in pipeline.records if r.error)}")
    print(f"Status: {'SUCCESS' if embedded_count > 0 and stored > 0 else 'FAILED'}")
    print(f"{'='*70}\n")
    
    return embedded_count > 0 and stored > 0


if __name__ == "__main__":
    try:
        success = test_structure_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
