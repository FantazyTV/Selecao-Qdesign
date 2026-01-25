"""Finalization API routes"""

from fastapi import APIRouter, HTTPException, Depends, Request
from ..services.finalization import FinalizationService

router_finalization = APIRouter(tags=["finalization"])


async def get_finalization_service(request: Request) -> FinalizationService:
    """Inject finalization service with DB from app"""
    db = next(request.app.get_db())
    return FinalizationService(db=db)


@router_finalization.post("/{kb_id}/finalize", response_model=dict)
async def finalize_knowledge_base(
    kb_id: str,
    service: FinalizationService = Depends(get_finalization_service)
):
    """Finalize knowledge base for graph construction"""
    try:
        service.finalize(kb_id)
        return {"success": True, "message": "KB finalized"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_finalization.get("/{kb_id}/export", response_model=dict)
async def export_for_graph(
    kb_id: str,
    service: FinalizationService = Depends(get_finalization_service)
):
    """Export KB for graph construction service"""
    try:
        return service.export_for_graph(kb_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
