"""
Simplified FastAPI router for retrieval service endpoints.
Single entry point that processes data pools and returns graph analysis.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime
import json

from utils.models import ProcessingRequest, GraphAnalysisResponse
from agent.agent import MultiModalRetrievalAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])

@router.post("/process", response_model=GraphAnalysisResponse)
async def process_data_pool(request: ProcessingRequest) -> GraphAnalysisResponse:
    """
    Main entry point for processing data pools.
    
    Accepts a simplified request with:
    - name: string
    - mainObjective: string
    - secondaryObjectives: string[]
    - constraints: string[]
    - notes: string[]
    - description?: string
    - dataPool: DataPoolItem[]
    
    Returns graph analysis with summary and processing stats.
    """
    try:
        logger.info(f"Processing request: {request.name} with {len(request.dataPool)} items")
        
        # Validate request
        if not request.dataPool:
            raise HTTPException(status_code=400, detail="Data pool cannot be empty")
        if not request.mainObjective:
            raise HTTPException(status_code=400, detail="Main objective is required")
        
        # Process using simplified agent
        agent = MultiModalRetrievalAgent()
        result = agent.process_data_pool_request(request)
        
        # Save input and response to JSON file with timestamp
        response = result
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'retrieval_response_{ts}.json'
        try:
            payload = {
                "input": request.dict() if hasattr(request, 'dict') else request,
                "response": response.dict() if hasattr(response, 'dict') else response
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            print(f"[DEBUG] Saved input and response to {filename}")
        except Exception as e:
            print(f"[ERROR] Could not save input/response to {filename}: {str(e)}")
        
        logger.info(f"Successfully processed {request.name}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_data_pool: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "retrieval_service",
        "version": "2.0.0"
    }
