"""
API Routes - Aggregates all route modules.
"""

from fastapi import APIRouter

from .workflow_routes import router as workflow_router
from .kg_routes import router as kg_router
from .util_routes import router as util_router

# Main router that includes all sub-routers
router = APIRouter()
router.include_router(workflow_router)
router.include_router(kg_router)
router.include_router(util_router)

__all__ = ["router"]
