"""Retrieval API routes"""

from fastapi import APIRouter, HTTPException, Depends, Request
from ..services.retrieval import RetrievalService

router_retrieval = APIRouter(tags=["retrieval"])


async def get_retrieval_service(request: Request) -> RetrievalService:
    """Inject retrieval service with DB from app"""
    db = next(request.app.get_db())
    return RetrievalService(db=db)


@router_retrieval.get("/{kb_id}", response_model=dict)
async def get_knowledge_base(
    kb_id: str,
    service: RetrievalService = Depends(get_retrieval_service)
):
    """Get knowledge base with resources and annotations"""
    try:
        return service.get_knowledge_base(kb_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
