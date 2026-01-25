"""Knowledge Service Package

Manages knowledge base discovery, curation, and finalization for projects.

Components:
- models: SQLAlchemy database models
- services: Core business logic (discovery, curation, retrieval, finalization)
- api: FastAPI routes
- schemas: Pydantic validation models
- utils: Helper functions
"""

from .services import (
    DiscoveryService,
    CurationService,
    RetrievalService,
    FinalizationService
)
from .models import KnowledgeBase, KnowledgeResource, ResourceAnnotation

__all__ = [
    "DiscoveryService",
    "CurationService",
    "RetrievalService",
    "FinalizationService",
    "KnowledgeBase",
    "KnowledgeResource",
    "ResourceAnnotation",
]
