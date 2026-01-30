"""
Asynchronous FastAPI router for retrieval service endpoints.
Single entry point that processes data pools and returns graph analysis asynchronously.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
from datetime import datetime
import asyncio
import json

from utils.models import ProcessingRequest, GraphAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])

# In-memory job storage (use Redis or database in production)
job_results: Dict[str, Dict[str, Any]] = {}


async def _process_data_pool_background(job_id: str, request: ProcessingRequest):
    """Background task that immediately returns test data."""
    try:
        job_results[job_id] = {
            "status": "processing", 
            "started_at": datetime.now().isoformat()
        }
        
        # Wait 10 seconds for testing
        await asyncio.sleep(10)
        
        # Load the test JSON file
        with open('retrieval_response_20260130_025858.json', 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # Set job as completed with test response
        job_results[job_id] = {
            "status": "completed",
            "result": test_data["response"],
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {str(e)}")
        job_results[job_id] = {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }


@router.post("/process")
async def process_data_pool(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """
    Main entry point for processing data pools asynchronously.
    
    Accepts a simplified request and returns a job ID for polling.
    """
    try:
        logger.info(f"Processing request: {request.name} with {len(request.dataPool)} items")
        
        # Validate request
        if not request.dataPool:
            raise HTTPException(status_code=400, detail="Data pool cannot be empty")
        if not request.mainObjective:
            raise HTTPException(status_code=400, detail="Main objective is required")
        
        # Generate job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(request.dict())) % 10000}"
        
        # Start background processing
        background_tasks.add_task(_process_data_pool_background, job_id, request)
        
        return {
            "jobId": job_id,
            "status": "processing",
            "message": "Data pool analysis started. Use /status endpoint to check progress.",
            "estimatedCompletion": "10 seconds"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_data_pool: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of an async analysis job."""
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_results[job_id]


@router.get("/result/{job_id}", response_model=GraphAnalysisResponse)
async def get_job_result(job_id: str) -> GraphAnalysisResponse:
    """Get the result of a completed analysis job."""
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_results[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=202, detail="Job still processing")
    elif job["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"Job failed: {job.get('error')}")
    elif job["status"] == "completed":
        return GraphAnalysisResponse(**job["result"])
    else:
        raise HTTPException(status_code=500, detail="Unknown job status")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "retrieval_service",
        "version": "2.0.0"
    }


@router.get("/stats")
async def get_service_stats():
    """Get service statistics."""
    active_jobs = len([job for job in job_results.values() if job["status"] == "processing"])
    completed_jobs = len([job for job in job_results.values() if job["status"] == "completed"])
    failed_jobs = len([job for job in job_results.values() if job["status"] == "failed"])

    return {
        "active_jobs": active_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "total_jobs": len(job_results),
        "executor_stats": {
            "max_workers": executor._max_workers,
            "current_threads": len(executor._threads) if hasattr(executor, '_threads') else 0
        }
    }