"""Curation API routes"""

from fastapi import APIRouter, HTTPException, Depends, Request, Body
from ..schemas.requests import AddCustomResourceRequest, AnnotateResourceRequest, ReorderResourcesRequest
from ..services.curation import CurationService

router_curation = APIRouter(tags=["curation"])


async def get_curation_service(request: Request) -> CurationService:
    """Inject curation service with DB from app"""
    db = next(request.app.get_db())
    return CurationService(db=db)


@router_curation.delete("/resources/{resource_id}", response_model=dict)
async def delete_resource(
    resource_id: str,
    service: CurationService = Depends(get_curation_service)
):
    """Remove resource from knowledge base"""
    try:
        service.delete_resource(resource_id)
        return {"success": True, "message": f"Deleted {resource_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_curation.post("/resources/custom", response_model=dict)
async def add_custom_resource(
    body: AddCustomResourceRequest = Body(...),
    service: CurationService = Depends(get_curation_service)
):
    """Add custom resource to knowledge base"""
    try:
        # Get kb_id from request body (using knowledge_base_id field)
        kb_id = getattr(body, 'knowledge_base_id', None) or getattr(body, 'kb_id', None)
        resource = service.add_custom_resource(
            kb_id=kb_id,
            resource_type=body.resource_type,
            title=body.title,
            url=body.url,
            metadata=body.metadata,
            comment=body.comment
        )
        return {"id": resource.id, "title": resource.title}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_curation.post("/resources/{resource_id}/annotate", response_model=dict)
async def annotate_resource(
    resource_id: str,
    request: AnnotateResourceRequest,
    service: CurationService = Depends(get_curation_service)
):
    """Add annotation to resource"""
    try:
        annotation = service.annotate_resource(
            resource_id=resource_id,
            comment=request.comment,
            tags=request.tags,
            confidence_score=request.confidence_score
        )
        return {"id": annotation.id, "message": "Annotation added"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_curation.post("/{kb_id}/reorder", response_model=dict)
async def reorder_resources(
    kb_id: str,
    request: ReorderResourcesRequest,
    service: CurationService = Depends(get_curation_service)
):
    """Reorder resources by priority"""
    try:
        service.reorder_resources(kb_id, request.resource_ids)
        return {"success": True, "message": "Reordered"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
