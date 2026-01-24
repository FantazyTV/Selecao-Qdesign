#!/usr/bin/env python
"""
Test image data processing through complete pipeline
Downloads images, ingests, embeds, and stores in Qdrant
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.cwd()))

from pipeline.orchestration.pipeline import QDesignPipeline
from pipeline.ingestion.image_ingester import ImageIngester
from pipeline.embedding.fastembed_embedder import FastembedImageEmbedder
from pipeline.collectors.base_collector import BaseCollector, CollectorRecord
from qdrant_client import QdrantClient


class LocalImageCollector(BaseCollector):
    """Collector for local image files"""
    
    def __init__(self, data_type: str = "image"):
        super().__init__("local_images")
        self.data_type = data_type
    
    def collect(self, directory: str, pattern: str = "*", recursive: bool = True):
        """Collect image files from directory"""
        self.records = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"Directory not found: {directory}")
            return self.records
        
        # Find image files
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp"]:
            if recursive:
                files = list(dir_path.rglob(ext))
            else:
                files = list(dir_path.glob(ext))
            
            for file_path in sorted(files):
                try:
                    record = CollectorRecord(
                        data_type=self.data_type,
                        source="local_file",
                        collection=self.collection_name,
                        raw_content=str(file_path),
                        source_url=str(file_path),
                        title=file_path.name,
                        metadata={"file_path": str(file_path), "size": file_path.stat().st_size}
                    )
                    self.add_record(record)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        
        return self.records
    
    def validate(self, record: CollectorRecord) -> bool:
        """Validate image file exists"""
        return Path(record.raw_content).exists()


def create_sample_images():
    """Create sample images for testing if none exist"""
    try:
        from PIL import Image, ImageDraw
        import random
        
        img_dir = Path("../../Data/images/diagrams")
        img_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if images already exist
        existing = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
        if existing:
            print(f"Found {len(existing)} existing images")
            return existing
        
        print("Creating 5 sample images for testing...")
        created = []
        
        for i in range(5):
            # Create image with random colors and patterns
            img = Image.new('RGB', (512, 512), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            # Draw random shapes (represent protein structures/molecules)
            for _ in range(10):
                x0 = random.randint(0, 512)
                y0 = random.randint(0, 512)
                x1 = x0 + random.randint(50, 200)
                y1 = y0 + random.randint(50, 200)
                color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                draw.ellipse([x0, y0, x1, y1], fill=color, outline=color)
            
            # Save image
            filename = img_dir / f"sample_protein_{i+1}.jpg"
            img.save(filename, quality=85)
            created.append(str(filename))
            print(f"  • Created {filename.name}")
        
        return created
    except ImportError:
        print("PIL not available, skipping image creation")
        return []


def test_image_pipeline():
    """Test complete image pipeline"""
    print(f"\n{'='*70}")
    print(f"IMAGE PIPELINE TEST - Download, Ingest, Embed, Store")
    print(f"{'='*70}\n")
    
    # Step 1: Download or create sample images
    print("STEP 1: Prepare images")
    print("-" * 70)
    
    # First try to use existing images
    img_dir = Path("../../Data/images/diagrams")
    existing = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")) if img_dir.exists() else []
    
    if not existing:
        print("Creating sample test images...")
        create_sample_images()
    else:
        print(f"Using existing {len(existing)} images")
    
    # Step 2: Collect local images
    print(f"\nSTEP 2: Collect local images")
    print("-" * 70)
    
    pipeline = QDesignPipeline(name="image_pipeline")
    pipeline.register_collector("local", LocalImageCollector("image"))
    pipeline.register_ingester("image", ImageIngester())
    pipeline.register_embedder("image", FastembedImageEmbedder())
    
    start = datetime.now()
    collected = pipeline.collect("local", "../../Data", recursive=True)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"Collected {len(collected)} images in {elapsed:.2f}s")
    
    if not collected:
        print("No images found! Please download first or check data directory.")
        return False
    
    for i, record in enumerate(collected[:10], 1):
        size_mb = record.metadata.get('size', 0) / (1024 * 1024)
        print(f"  {i}. {record.title} ({size_mb:.2f} MB)")
    
    if len(collected) > 10:
        print(f"  ... and {len(collected) - 10} more")
    
    # Step 3: Ingest images
    print(f"\nSTEP 3: Ingest images")
    print("-" * 70)
    
    start = datetime.now()
    pipeline.ingest(collected)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"Ingested {len(collected)} images in {elapsed:.2f}s")
    
    # Step 4: Embed images
    print(f"\nSTEP 4: Embed images to vectors")
    print("-" * 70)
    
    start = datetime.now()
    pipeline.embed()
    elapsed = (datetime.now() - start).total_seconds()
    
    embedded_count = sum(1 for r in pipeline.records if r.embedding is not None and len(r.embedding) > 0 and not r.error)
    print(f"Embedded {embedded_count} images in {elapsed:.2f}s")
    
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
    
    # Count records with embeddings and no errors
    embedded_count = sum(1 for r in pipeline.records if r.embedding is not None and len(r.embedding) > 0 and not r.error)
    
    print(f"Total images processed: {len(pipeline.records)}")
    print(f"Successfully embedded: {embedded_count}")
    print(f"Stored in Qdrant: {stored}")
    print(f"Errors: {sum(1 for r in pipeline.records if r.error)}")
    print(f"Status: {'SUCCESS' if embedded_count > 0 and stored > 0 else 'FAILED'}")
    print(f"{'='*70}\n")
    
    return embedded_count > 0 and stored > 0


if __name__ == "__main__":
    try:
        success = test_image_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
