"""Knowledge resource ORM model"""

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from .base import Base


class KnowledgeResource(Base):
    """Individual resource in knowledge base"""
    __tablename__ = "knowledge_resources"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    knowledge_base_id = Column(String, ForeignKey("knowledge_bases.id"), nullable=False)
    resource_type = Column(String)  # protein, paper, image, custom
    source = Column(String)  # alphafold, arxiv, manual
    external_id = Column(String)
    title = Column(String, nullable=False)
    url = Column(String)
    relevance_score = Column(Float)
    matching_keywords = Column(JSON)
    explanation = Column(String)
    resource_metadata = Column(JSON)
    included = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    order = Column(Integer)

    knowledge_base = relationship("KnowledgeBase", back_populates="resources")
    annotations = relationship("ResourceAnnotation", back_populates="resource", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KnowledgeResource({self.resource_type}: {self.title})>"
