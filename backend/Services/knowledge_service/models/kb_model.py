"""Knowledge base ORM model"""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

from .base import Base


class KnowledgeBase(Base):
    """Main knowledge base container for a project"""
    __tablename__ = "knowledge_bases"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String, nullable=False)  # String reference, no FK constraint for flexibility
    status = Column(String, default="discovering")  # discovering, ready, active
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_resources = Column(Integer, default=0)
    total_annotations = Column(Integer, default=0)

    resources = relationship("KnowledgeResource", back_populates="knowledge_base", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KnowledgeBase({self.project_id}, {self.total_resources} resources)>"
