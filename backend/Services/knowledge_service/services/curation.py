"""Resource curation service - CRUD operations"""

from typing import List, Optional, Dict

from ..models import KnowledgeBase, KnowledgeResource, ResourceAnnotation
from .base import BaseKnowledgeService


class CurationService(BaseKnowledgeService):
    """Manage knowledge base resources and annotations"""

    def delete_resource(self, resource_id: str) -> bool:
        """Soft delete resource"""
        resource = self.db.query(KnowledgeResource).filter_by(id=resource_id).first()
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")
        resource.included = False
        self.db.commit()
        self.logger.info(f"Deleted resource {resource_id}")
        return True

    def add_custom_resource(
        self,
        kb_id: str,
        resource_type: str,
        title: str,
        url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        comment: Optional[str] = None
    ) -> KnowledgeResource:
        """Add manually provided resource"""
        kb = self.db.query(KnowledgeBase).filter_by(id=kb_id).first()
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")

        resource = KnowledgeResource(
            knowledge_base_id=kb_id,
            resource_type=resource_type,
            source="manual",
            title=title,
            url=url,
            relevance_score=100.0,
            matching_keywords=["user-provided"],
            explanation="User manually added",
            resource_metadata=metadata or {}
        )
        kb.resources.append(resource)
        self.db.add(resource)
        self.db.commit()

        if comment:
            self.annotate_resource(resource.id, comment=comment)

        return resource

    def annotate_resource(
        self,
        resource_id: str,
        user_id: Optional[str] = None,
        comment: Optional[str] = None,
        tags: Optional[List[str]] = None,
        confidence_score: Optional[float] = None
    ) -> ResourceAnnotation:
        """Add annotation to resource"""
        resource = self.db.query(KnowledgeResource).filter_by(id=resource_id).first()
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        annotation = ResourceAnnotation(
            resource_id=resource_id,
            created_by=user_id,
            comment=comment,
            tags=tags,
            confidence_score=confidence_score
        )
        self.db.add(annotation)
        resource.knowledge_base.total_annotations += 1
        self.db.commit()
        return annotation

    def reorder_resources(self, kb_id: str, resource_ids: List[str]) -> bool:
        """Reorder resources by priority"""
        kb = self.db.query(KnowledgeBase).filter_by(id=kb_id).first()
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")

        for idx, rid in enumerate(resource_ids):
            r = self.db.query(KnowledgeResource).filter_by(id=rid).first()
            if r:
                r.order = idx
        self.db.commit()
        return True
