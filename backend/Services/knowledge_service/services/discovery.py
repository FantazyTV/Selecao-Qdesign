"""Resource discovery service - find relevant materials via Qdrant"""

from typing import List, Dict
import sys
from pathlib import Path
from ..models import KnowledgeBase, KnowledgeResource
from ..utils.extractors import extract_key_terms
from .base import BaseKnowledgeService
from .discovery_search import search_collection
from .discovery_filters import filter_and_rank, deduplicate_results

# Add Services to path for Qdrant imports
services_dir = Path(__file__).parent.parent.parent
if str(services_dir) not in sys.path:
    sys.path.insert(0, str(services_dir))


class DiscoveryService(BaseKnowledgeService):
    """Orchestrates discovery of resources from Qdrant"""

    def __init__(self, db, qdrant_client=None, embedder=None):
        """Initialize discovery service with Qdrant connection"""
        super().__init__(db, qdrant_client, embedder)
        self._init_qdrant()
        self._init_embedder()

    def _init_qdrant(self):
        """Initialize Qdrant client"""
        if self.qdrant is not None:
            return
        try:
            from pipeline.storage.qdrant_client import QdrantClient
            self.qdrant = QdrantClient()
            collections = self.qdrant.client.get_collections()
            num = len(collections.collections) if collections else 0
            self.logger.info(f"✓ Connected to Qdrant - {num} collections available")
        except Exception as e:
            self.logger.error(f"✗ Qdrant failed: {e}")
            self.qdrant = None

    def _init_embedder(self):
        """Initialize Gemini embedder (3072-dim)"""
        if self.embedder is not None:
            return
        try:
            from pipeline.embedding import GeminiEmbedder
            self.embedder = GeminiEmbedder()
            self.logger.info("✓ Initialized GeminiEmbedder (3072-dim)")
        except Exception as e:
            self.logger.error(f"✗ GeminiEmbedder failed: {e}")
            self.embedder = None

    def discover_resources(
        self,
        project_id: str,
        project_description: str,
        top_k: int = 20,
        min_relevance: float = 0.3
    ) -> KnowledgeBase:
        """Discover relevant resources for project from Qdrant"""
        if not self.qdrant or not self.embedder:
            raise RuntimeError("Qdrant and embedder required for discovery")

        key_terms = extract_key_terms(project_description)
        self.logger.info(f"Extracted {len(key_terms)} key terms")

        proteins = search_collection(self.qdrant, self.embedder, "qdesign_structures", key_terms, top_k, "protein")
        papers = search_collection(self.qdrant, self.embedder, "qdesign_text", key_terms, top_k, "paper")
        images = search_collection(self.qdrant, self.embedder, "qdesign_images", key_terms, top_k, "image")
        sequences = search_collection(self.qdrant, self.embedder, "qdesign_sequences", key_terms, top_k, "sequence")

        all_resources = proteins + papers + images + sequences
        self.logger.info(f"Found {len(all_resources)} results")

        all_resources = deduplicate_results(all_resources)
        filtered = filter_and_rank(all_resources, min_relevance, top_k)
        self.logger.info(f"Returning {len(filtered)} resources")

        return self._create_knowledge_base(project_id, filtered)

    def _create_knowledge_base(self, project_id: str, resources: List[Dict]) -> KnowledgeBase:
        """Create KB in database with resources"""
        kb = KnowledgeBase(project_id=project_id, status="discovering")
        for idx, res in enumerate(resources):
            resource = KnowledgeResource(
                knowledge_base_id=kb.id,
                resource_type=res["resource_type"],
                source=res["source"],
                external_id=res.get("external_id"),
                title=res["title"],
                url=res.get("url"),
                relevance_score=res["relevance_score"],
                matching_keywords=res["matching_keywords"],
                explanation=res["explanation"],
                resource_metadata=res.get("resource_metadata", {}),
                order=idx
            )
            kb.resources.append(resource)
        kb.total_resources = len(resources)
        self.db.add(kb)
        self.db.commit()
        return kb
