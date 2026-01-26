"""Request validation schemas"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class DiscoverResourcesRequest(BaseModel):
    """Request to discover resources"""
    project_id: str
    project_description: str
    top_k: int = 20
    min_relevance: float = 0.6


class AddCustomResourceRequest(BaseModel):
    """Request to add custom resource"""
    knowledge_base_id: str
    resource_type: str
    title: str
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None


class AnnotateResourceRequest(BaseModel):
    """Request to annotate resource"""
    comment: Optional[str] = None
    tags: Optional[List[str]] = None
    confidence_score: Optional[float] = None


class ReorderResourcesRequest(BaseModel):
    """Request to reorder resources"""
    resource_ids: List[str]
