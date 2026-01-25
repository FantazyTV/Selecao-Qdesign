"""Discovery API routes - requires working Qdrant instance"""

from fastapi import APIRouter, HTTPException, Depends, Request
from ..schemas.requests import DiscoverResourcesRequest
from ..services.discovery import DiscoveryService

router_discovery = APIRouter(tags=["discovery"])


async def get_discovery_service(request: Request) -> DiscoveryService:
    """Inject discovery service with DB from app"""
    db = next(request.app.get_db())
    return DiscoveryService(db=db)


@router_discovery.post("/discover", response_model=dict)
async def discover_resources(
    request: DiscoverResourcesRequest,
    service: DiscoveryService = Depends(get_discovery_service)
):
    """Discover relevant resources for project from Qdrant vector database"""
    try:
        # Check Qdrant initialization
        if not service.qdrant:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Qdrant not initialized",
                    "message": "Qdrant vector database connection failed",
                    "solution": [
                        "1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:latest",
                        "2. Load data: cd pipeline && python scripts/process_local_files.py",
                        "3. Verify: curl http://localhost:6333/collections"
                    ]
                }
            )
        
        if not service.embedder:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Embedder not initialized",
                    "message": "Vector embedding model failed to initialize",
                    "solution": "Install embedder: pip install sentence-transformers"
                }
            )
        
        # Perform discovery with real Qdrant data
        kb = service.discover_resources(
            project_id=request.project_id,
            project_description=request.project_description,
            top_k=request.top_k,
            min_relevance=request.min_relevance
        )
        return {"knowledge_base_id": kb.id, "total_resources": kb.total_resources}
    
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Qdrant search failed",
                "message": str(e),
                "hint": "Ensure Qdrant is running and data has been loaded via pipeline"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Discovery error: {str(e)}"
        )
