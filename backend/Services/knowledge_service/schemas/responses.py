"""Response validation schemas"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class AnnotationResponse(BaseModel):
    """Annotation details"""
    id: str
    comment: Optional[str]
    tags: Optional[List[str]]
    confidence_score: Optional[float]
    created_by: Optional[str]
    created_at: datetime


class ResourceResponse(BaseModel):
    """Single resource with annotations"""
    id: str
    resource_type: str
    source: str
    external_id: Optional[str]
    title: str
    url: Optional[str]
    relevance_score: float
    matching_keywords: List[str]
    explanation: Optional[str]
    metadata: Dict[str, Any]
    order: int
    annotations: List[AnnotationResponse]


class KnowledgeBaseResponse(BaseModel):
    """Complete knowledge base"""
    id: str
    project_id: str
    status: str
    total_resources: int
    total_annotations: int
    created_at: datetime
    updated_at: datetime
    resources: List[ResourceResponse]
