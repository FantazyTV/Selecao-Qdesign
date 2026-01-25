"""Resource annotation ORM model"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from .base import Base


class ResourceAnnotation(Base):
    """User annotations on resources"""
    __tablename__ = "resource_annotations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    resource_id = Column(String, ForeignKey("knowledge_resources.id"), nullable=False)
    comment = Column(String)
    tags = Column(JSON)
    confidence_score = Column(Float)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resource = relationship("KnowledgeResource", back_populates="annotations")

    def __repr__(self):
        return f"<ResourceAnnotation({self.resource_id})>"
