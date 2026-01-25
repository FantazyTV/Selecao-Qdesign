"""Qdrant search operations for discovery service"""

from typing import List, Dict
import logging
from ..models import KnowledgeResource

logger = logging.getLogger(__name__)


def search_collection(
    qdrant_client,
    embedder,
    collection: str,
    terms: List[str],
    top_k: int,
    resource_type: str
) -> List[Dict]:
    """Search Qdrant collection using unified Gemini embeddings"""
    if not qdrant_client:
        raise RuntimeError(f"✗ Qdrant client not available for collection '{collection}'")
    if not embedder:
        raise RuntimeError("✗ Gemini embedder not available for generating search vectors")

    results = []
    seen = set()

    for term in terms:
        try:
            vector = embedder.embed(term)
            logger.debug(f"Searching '{collection}' for: {term}")
            
            hits = qdrant_client.search(
                collection_name=collection,
                vector=vector,
                limit=top_k,
                score_threshold=0.1
            )

            logger.debug(f"Got {len(hits)} hits in '{collection}' for '{term}'")

            for hit in hits:
                payload = hit.get("metadata", {})
                record_id = hit.get("id")
                score = hit.get("score", 0.0)
                
                if not record_id or record_id in seen:
                    continue
                seen.add(record_id)

                results.append({
                    "resource_type": resource_type,
                    "source": payload.get("source", "qdrant"),
                    "external_id": record_id,
                    "title": payload.get("title", f"{resource_type.title()} {record_id[:8]}"),
                    "url": payload.get("url", payload.get("file_path", "")),
                    "relevance_score": score * 100,
                    "matching_keywords": [term],
                    "explanation": f"Found {resource_type} with relevance {score*100:.1f}%",
                    "resource_metadata": {
                        k: v for k, v in payload.items()
                        if k not in ["title", "url", "file_path", "source", "id", "content"]
                    }
                })

        except Exception as e:
            logger.error(f"Error searching '{collection}' for '{term}': {e}")
            continue

    if not results:
        logger.warning(f"⚠ No results found in '{collection}' for {len(terms)} search terms")

    return results
