"""Main router combining all domain routers"""

from fastapi import APIRouter
from .discovery_routes import router_discovery
from .retrieval_routes import router_retrieval
from .curation_routes import router_curation
from .finalization_routes import router_finalization

# Combine all routers under /api/v1/knowledge
router = APIRouter(prefix="/api/v1/knowledge")
router.include_router(router_discovery)
router.include_router(router_retrieval)
router.include_router(router_curation)
router.include_router(router_finalization)

__all__ = ["router"]
