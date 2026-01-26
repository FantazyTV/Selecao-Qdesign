#!/usr/bin/env python3
"""
Validation script for QDesign embedding configuration
Checks that all components are properly configured and compatible
"""

import sys
from pathlib import Path

# Add services to path
services_dir = Path(__file__).parent / "backend" / "Services"
sys.path.insert(0, str(services_dir))

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}\n")

def check_imports():
    """Check that all required packages are installed"""
    print_section("Checking Imports")
    
    packages = {
        "numpy": "numpy",
        "requests": "requests",
        "pydantic": "pydantic",
        "qdrant_client": "qdrant-client",
        "sentence_transformers": "sentence-transformers",
        "PIL": "pillow",
        "biopython": "biopython",
    }
    
    optional_packages = {
        "clip": "openai-clip",
        "torch": "torch",
        "esm": "fair-esm",
    }
    
    print("Required packages:")
    for package, pip_name in packages.items():
        try:
            __import__(package)
            print(f"  ✓ {package} ({pip_name})")
        except ImportError:
            print(f"  ✗ {package} ({pip_name}) - MISSING")
            return False
    
    print("\nOptional packages:")
    for package, pip_name in optional_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {package} ({pip_name})")
        except ImportError:
            print(f"  ⚠ {package} ({pip_name}) - NOT installed")
    
    return True

def check_config():
    """Check configuration"""
    print_section("Checking Configuration")
    
    try:
        from pipeline.config import get_config
        config = get_config()
        
        print("Embedding Configuration:")
        print(f"  Device: {config.device}")
        print(f"  Batch Size: {config.batch_size}")
        print(f"  Normalize: {config.normalize_embeddings}")
        print(f"  ESM Model: {config.esm_model}")
        
        print("\nStorage Configuration:")
        print(f"  Qdrant URL: {config.qdrant_url}")
        print(f"  Text Collection: {config.storage.qdrant_collection_text}")
        print(f"  Sequence Collection: {config.storage.qdrant_collection_sequences}")
        print(f"  Structure Collection: {config.storage.qdrant_collection_structures}")
        print(f"  Image Collection: {config.storage.qdrant_collection_images}")
        
        print("\nVector Sizes:")
        print(f"  Text: {config.storage.vector_size_text} (SentenceTransformer)")
        print(f"  Sequence: {config.storage.vector_size_sequence} (ESM-2)")
        print(f"  Structure: {config.storage.vector_size_structure} (PDB features)")
        print(f"  Image: {config.storage.vector_size_image} (CLIP)")
        
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def check_embedders():
    """Check embedder initialization"""
    print_section("Checking Embedders")
    
    try:
        from pipeline.embedding import (
            SentenceTransformerTextEmbedder,
            CLIPImageEmbedder,
            ESMSequenceEmbedder,
            StructureEmbedder
        )
        
        # Check text embedder
        print("Text Embedder (SentenceTransformer):")
        try:
            text_embedder = SentenceTransformerTextEmbedder()
            dim = text_embedder.get_dimension()
            print(f"  ✓ Initialized - {dim}-dim")
            
            # Test embedding
            test_text = "protein binding affinity"
            embedding = text_embedder.embed(test_text)
            if embedding is not None and len(embedding) == dim:
                print(f"  ✓ Test embedding successful")
            else:
                print(f"  ✗ Test embedding failed")
                return False
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False
        
        # Check image embedder
        print("\nImage Embedder (CLIP):")
        try:
            image_embedder = CLIPImageEmbedder()
            dim = image_embedder.get_dimension()
            print(f"  ✓ Initialized - {dim}-dim")
        except Exception as e:
            print(f"  ⚠ Not available: {e}")
        
        # Check sequence embedder
        print("\nSequence Embedder (ESM-2):")
        try:
            seq_embedder = ESMSequenceEmbedder()
            dim = seq_embedder.get_dimension()
            print(f"  ✓ Initialized - {dim}-dim")
        except Exception as e:
            print(f"  ⚠ Not available: {e}")
        
        # Check structure embedder
        print("\nStructure Embedder (PDB Features):")
        try:
            struct_embedder = StructureEmbedder()
            dim = struct_embedder.get_dimension()
            print(f"  ✓ Initialized - {dim}-dim")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Embedder import error: {e}")
        return False

def check_qdrant():
    """Check Qdrant connectivity"""
    print_section("Checking Qdrant Connection")
    
    try:
        from pipeline.storage.qdrant_client import QdrantClient
        
        try:
            qdrant = QdrantClient()
            print("✓ Connected to Qdrant")
            
            # Get collections
            collections = qdrant.client.get_collections()
            num_collections = len(collections.collections) if collections else 0
            print(f"  Available collections: {num_collections}")
            
            if collections:
                for col in collections.collections:
                    stats = qdrant.get_stats(col.name)
                    print(f"    - {col.name}: {stats.get('points_count', 0)} points")
            
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            print("  Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant:latest")
            return False
            
    except Exception as e:
        print(f"✗ Qdrant client error: {e}")
        return False

def check_pipeline():
    """Check pipeline initialization"""
    print_section("Checking Pipeline")
    
    try:
        from pipeline.orchestration.pipeline import QDesignPipeline
        
        pipeline = QDesignPipeline()
        print("✓ Pipeline initialized")
        
        return True
    except Exception as e:
        print(f"✗ Pipeline initialization failed: {e}")
        return False

def check_knowledge_service():
    """Check knowledge service"""
    print_section("Checking Knowledge Service")
    
    try:
        from knowledge_service.services.discovery import DiscoveryService
        from knowledge_service.services.retrieval import RetrievalService
        
        print("✓ Knowledge service modules available")
        return True
    except Exception as e:
        print(f"✗ Knowledge service error: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("QDesign - Configuration Validation".center(60))
    print("="*60)
    
    checks = [
        ("Package Imports", check_imports),
        ("Configuration", check_config),
        ("Embedders", check_embedders),
        ("Qdrant", check_qdrant),
        ("Pipeline", check_pipeline),
        ("Knowledge Service", check_knowledge_service),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n✗ {check_name} failed with exception: {e}")
            results[check_name] = False
    
    # Summary
    print_section("Validation Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {check_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} checks passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All checks passed! System is ready.\n")
        return 0
    else:
        print("⚠️  Some checks failed. Please review the errors above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
