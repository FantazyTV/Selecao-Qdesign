"""Knowledge base retrieval service"""

from typing import Dict

from ..models import KnowledgeBase, ResourceAnnotation
from .base import BaseKnowledgeService


class RetrievalService(BaseKnowledgeService):
    """Retrieve and format knowledge bases"""

    def get_knowledge_base(self, kb_id: str) -> Dict:
        """Get full knowledge base with resources and annotations"""
        kb = self.db.query(KnowledgeBase).filter_by(id=kb_id).first()
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")

        resources_data = [self._format_resource(r) for r in kb.resources if r.included]

        return {
            "id": kb.id,
            "project_id": kb.project_id,
            "status": kb.status,
            "total_resources": len(resources_data),
            "total_annotations": kb.total_annotations,
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat(),
            "resources": resources_data
        }

    def _format_resource(self, resource) -> Dict:
        """Format resource with annotations"""
        annotations = self.db.query(ResourceAnnotation).filter_by(resource_id=resource.id).all()

        return {
            "id": resource.id,
            "type": resource.resource_type,
            "source": resource.source,
            "external_id": resource.external_id,
            "title": resource.title,
            "url": resource.url,
            "relevance_score": resource.relevance_score,
            "matching_keywords": resource.matching_keywords or [],
            "explanation": resource.explanation,
            "metadata": resource.resource_metadata or {},
            "order": resource.order,
            "annotations": [self._format_annotation(a) for a in annotations]
        }

    def _format_annotation(self, ann) -> Dict:
        """Format annotation response"""
        return {
            "id": ann.id,
            "comment": ann.comment,
            "tags": ann.tags or [],
            "confidence_score": ann.confidence_score,
            "created_by": ann.created_by,
            "created_at": ann.created_at.isoformat()
        }
