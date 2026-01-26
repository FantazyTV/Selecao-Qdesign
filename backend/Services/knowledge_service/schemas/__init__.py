"""Request/Response validation schemas"""

from .requests import (
    DiscoverResourcesRequest,
    AddCustomResourceRequest,
    AnnotateResourceRequest,
    ReorderResourcesRequest,
)
from .responses import (
    AnnotationResponse,
    ResourceResponse,
    KnowledgeBaseResponse,
)

__all__ = [
    "DiscoverResourcesRequest",
    "AddCustomResourceRequest",
    "AnnotateResourceRequest",
    "ReorderResourcesRequest",
    "AnnotationResponse",
    "ResourceResponse",
    "KnowledgeBaseResponse",
]
