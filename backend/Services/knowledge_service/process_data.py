"""
Pipeline Data Processing Script
Demonstrates how to process Data/ files through the pipeline
and store embeddings in Qdrant for knowledge service discovery
"""

import sys
from pathlib import Path
import asyncio
import logging
from typing import List, Dict, Any

# Setup paths
script_file = Path(__file__)
project_root = script_file.parent.parent.parent.parent  # From knowledge_service up to Selecao-QDesign
data_dir = project_root / "Data"
services_dir = project_root / "backend" / "Services"
sys.path.insert(0, str(services_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from pipeline.orchestration.pipeline import QDesignPipeline
    from pipeline.config import get_config
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    logger.warning("Pipeline module not available - running in demo mode")


class DataProcessor:
    """Process Data/ files and store in Qdrant"""

    def __init__(self):
        """Initialize processor"""
        self.data_dir = data_dir
        self.config = get_config() if PIPELINE_AVAILABLE else None
        self.pipeline = QDesignPipeline() if PIPELINE_AVAILABLE else None
        logger.info(f"Data directory: {self.data_dir}")

    def discover_data_files(self) -> Dict[str, List[Path]]:
        """Discover all data files in Data/"""
        files = {
            "text": [],
            "sequences": [],
            "structures": [],
            "images": []
        }
        
        # Text files
        text_dir = self.data_dir / "text"
        if text_dir.exists():
            files["text"] = list(text_dir.glob("*.txt"))
        
        # Sequence files
        seq_dir = self.data_dir / "sequences"
        if seq_dir.exists():
            files["sequences"] = list(seq_dir.glob("*.fasta"))
            files["sequences"] += list((seq_dir / "fasta").glob("*.fasta"))
        
        # Structure files
        struct_dir = self.data_dir / "structures"
        if struct_dir.exists():
            files["structures"] = list(struct_dir.glob("**/*.pdb"))
        
        # Image files
        img_dir = self.data_dir / "images"
        if img_dir.exists():
            files["images"] = list(img_dir.glob("**/*.png"))
            files["images"] += list(img_dir.glob("**/*.jpg"))
        
        return files

    def process_text_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Process text files"""
        logger.info(f"\nProcessing {len(files)} text files...")
        results = []
        
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Create record
                record = {
                    "file": file_path.name,
                    "data_type": "text",
                    "source": "data_text",
                    "title": file_path.stem.replace("_", " ").title(),
                    "content": content[:500],  # First 500 chars
                    "size": len(content),
                    "collection": "qdesign_papers"
                }
                results.append(record)
                logger.info(f"  ✓ {file_path.name} ({len(content)} chars)")
                
            except Exception as e:
                logger.warning(f"  ✗ {file_path.name}: {e}")
        
        return results

    def process_sequences(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Process FASTA sequence files"""
        logger.info(f"\nProcessing {len(files)} sequence files...")
        results = []
        
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Count sequences
                seq_count = content.count(">")
                
                record = {
                    "file": file_path.name,
                    "data_type": "sequence",
                    "source": "data_sequences",
                    "title": f"{seq_count} sequences from {file_path.stem}",
                    "content": content[:500],
                    "sequence_count": seq_count,
                    "size": len(content),
                    "collection": "qdesign_sequences"
                }
                results.append(record)
                logger.info(f"  ✓ {file_path.name} ({seq_count} sequences, {len(content)} chars)")
                
            except Exception as e:
                logger.warning(f"  ✗ {file_path.name}: {e}")
        
        return results

    def process_structures(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Process PDB structure files"""
        logger.info(f"\nProcessing {len(files)} structure files...")
        results = []
        
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                record = {
                    "file": file_path.name,
                    "data_type": "structure",
                    "source": "data_structures",
                    "title": f"PDB structure: {file_path.stem}",
                    "content": content[:500],
                    "format": "pdb",
                    "size": len(content),
                    "collection": "qdesign_structures"
                }
                results.append(record)
                logger.info(f"  ✓ {file_path.name} ({len(content)} chars)")
                
            except Exception as e:
                logger.warning(f"  ✗ {file_path.name}: {e}")
        
        return results

    def process_images(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Process image files"""
        logger.info(f"\nProcessing {len(files)} image files...")
        results = []
        
        for file_path in files:
            try:
                record = {
                    "file": file_path.name,
                    "data_type": "image",
                    "source": "data_images",
                    "title": f"Image: {file_path.stem}",
                    "path": str(file_path),
                    "format": file_path.suffix[1:],
                    "collection": "qdesign_images"
                }
                results.append(record)
                logger.info(f"  ✓ {file_path.name}")
                
            except Exception as e:
                logger.warning(f"  ✗ {file_path.name}: {e}")
        
        return results

    async def process_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Process all data and prepare for Qdrant"""
        logger.info("\n" + "="*70)
        logger.info("DATA PROCESSING PIPELINE")
        logger.info("="*70)
        
        files = self.discover_data_files()
        
        logger.info("\nDiscovered files:")
        for data_type, file_list in files.items():
            logger.info(f"  {data_type}: {len(file_list)} files")
        
        all_records = {
            "text": self.process_text_files(files["text"]),
            "sequences": self.process_sequences(files["sequences"]),
            "structures": self.process_structures(files["structures"]),
            "images": self.process_images(files["images"])
        }
        
        # Summary
        total = sum(len(v) for v in all_records.values())
        logger.info(f"\n✓ Processed {total} files total")
        
        return all_records

    def show_processing_flow(self, records: Dict[str, List[Dict]]):
        """Show how records flow through pipeline"""
        logger.info("\n" + "="*70)
        logger.info("PIPELINE PROCESSING FLOW")
        logger.info("="*70)
        
        flow = """
Data Files (Data/)
       ↓
   [Collector] → Extracts content
       ↓
   [Ingester] → Normalizes format
       ↓
   [Enricher] → Adds metadata
       ↓
   [Normalizer] → Standardizes
       ↓
   [Embedder] → Generates vectors
       ↓
   [Storage] → Upserts to Qdrant
       ↓
Qdrant Database
       ↓
[Discovery Service] → Queries for KB creation
       ↓
Knowledge Base Resources
"""
        logger.info(flow)
        
        logger.info("Data ready for pipeline processing:")
        for data_type, file_records in records.items():
            if file_records:
                logger.info(f"\n{data_type.upper()} ({len(file_records)} items):")
                for record in file_records[:2]:  # Show first 2
                    logger.info(f"  • {record['title']}")
                if len(file_records) > 2:
                    logger.info(f"  ... and {len(file_records) - 2} more")

    def show_integration_steps(self):
        """Show step-by-step integration instructions"""
        logger.info("\n" + "="*70)
        logger.info("INTEGRATION SETUP STEPS")
        logger.info("="*70)
        
        steps = """
1. START QDRANT VECTOR DATABASE:
   docker run -p 6333:6333 qdrant/qdrant

2. RUN PIPELINE TO PROCESS DATA:
   python -m pipeline.scripts.process_local_files \\
     --data-dir Data/ \\
     --output-format qdrant

3. VERIFY DATA IN QDRANT:
   curl http://localhost:6333/collections

4. QUERY KNOWLEDGE SERVICE:
   curl -X POST http://127.0.0.1:8001/api/v1/knowledge/discover \\
     -H "Content-Type: application/json" \\
     -d '{
       "project_id": "protein_design_001",
       "project_description": "Green fluorescent protein engineering"
     }'

5. VERIFY KNOWLEDGE BASE:
   • Discovery automatically searches Qdrant collections
   • Resources are ranked by relevance
   • Knowledge base is persisted in SQLite

RESULT: Complete Pipeline → Qdrant → Knowledge Service Integration
"""
        logger.info(steps)


async def main():
    """Run data processing demonstration"""
    processor = DataProcessor()
    records = await processor.process_all_data()
    processor.show_processing_flow(records)
    processor.show_integration_steps()
    
    logger.info("\n" + "="*70)
    logger.info("NEXT: Run the integration test")
    logger.info("  python test_integration.py")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
