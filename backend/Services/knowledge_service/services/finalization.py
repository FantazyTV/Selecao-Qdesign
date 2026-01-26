"""Knowledge base finalization service"""

from typing import Dict
from datetime import datetime

from ..models import KnowledgeBase
from .base import BaseKnowledgeService


class FinalizationService(BaseKnowledgeService):
    """Finalize and export knowledge bases"""

    def finalize(self, kb_id: str) -> bool:
        """Mark knowledge base as ready for graph construction"""
        kb = self.db.query(KnowledgeBase).filter_by(id=kb_id).first()
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")

        kb.status = "active"
        kb.updated_at = datetime.utcnow()
        self.db.commit()
        self.logger.info(f"Finalized knowledge base {kb_id}")
        return True

    def export_for_graph(self, kb_id: str) -> Dict:
        """Export validated KB for graph construction service"""
        kb = self.db.query(KnowledgeBase).filter_by(id=kb_id).first()
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")

        resources = [r for r in kb.resources if r.included]

        return {
            "knowledge_base_id": kb.id,
            "project_id": kb.project_id,
            "exported_at": datetime.utcnow().isoformat(),
            "total_resources": len(resources),
            "resources": [
                {
                    "id": r.id,
                    "type": r.resource_type,
                    "source": r.source,
                    "external_id": r.external_id,
                    "title": r.title,
                    "url": r.url,
                    "relevance_score": r.relevance_score,
                    "metadata": r.resource_metadata,
                    "annotations": [
                        {
                            "comment": a.comment,
                            "tags": a.tags,
                            "confidence": a.confidence_score
                        }
                        for a in r.annotations
                    ]
                }
                for r in resources
            ]
        }
