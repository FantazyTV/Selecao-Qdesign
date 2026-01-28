"""
FastAPI router for retrieval service endpoints.
Handles data pool requests and returns graph analysis results.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback

from utils.models import DataPoolRequest, GraphAnalysisResponse
from agent.agent import MultiModalRetrievalAgent
from utils.processing import validate_graph_structure, GraphAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])

# Thread pool for CPU-intensive operations
executor = ThreadPoolExecutor(max_workers=2)

# In-memory job storage (use Redis or database in production)
job_results: Dict[str, Dict[str, Any]] = {}


def _process_data_pool_sync(request: DataPoolRequest) -> GraphAnalysisResponse:
    """Synchronous processing function for thread pool execution."""
    agent = MultiModalRetrievalAgent()
    return agent.process_data_pool_request(request)


@router.post("/analyze", response_model=GraphAnalysisResponse)
async def analyze_data_pool(request: DataPoolRequest) -> GraphAnalysisResponse:
    """Main endpoint for analyzing a data pool and generating knowledge graphs."""
    try:
        logger.info(f"Received data pool analysis request with {len(request.dataPool)} entries")
        if not request.dataPool:
            raise HTTPException(status_code=400, detail="Data pool cannot be empty")
        if not request.mainObjective:
            raise HTTPException(status_code=400, detail="Main objective is required")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, _process_data_pool_sync, request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_data_pool: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/analyze-async")
async def analyze_data_pool_async(request: DataPoolRequest, background_tasks: BackgroundTasks):
    """Asynchronous version that starts processing and returns a job ID."""
    try:
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(request.dict())) % 10000}"
        background_tasks.add_task(_process_data_pool_background, job_id, request)
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Data pool analysis started. Use /status endpoint to check progress.",
            "estimated_completion": "2-5 minutes"
        }
    except Exception as e:
        logger.error(f"Error starting async analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_data_pool_background(job_id: str, request: DataPoolRequest):
    """Background task for processing data pool."""
    try:
        job_results[job_id] = {"status": "processing", "started_at": datetime.now().isoformat()}
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, _process_data_pool_sync, request)
        job_results[job_id] = {
            "status": "completed",
            "result": result.dict(),
            "completed_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {str(e)}")
        job_results[job_id] = {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }


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


@router.post("/validate-graph")
async def validate_graph(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate graph structure and return analysis."""
    try:
        validation_result = validate_graph_structure(graph_data)

        if validation_result["valid"]:
            coverage_analysis = GraphAnalyzer.analyze_graph_coverage(
                graph_data,
                {"mainObjective": "general analysis"}
            )
            validation_result["coverage_analysis"] = coverage_analysis

        return validation_result
    except Exception as e:
        logger.error(f"Error validating graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "retrieval_service",
        "version": "1.0.0"
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
            "current_threads": len(executor._threads)
        }
    }


@router.post("/extract-entities")
async def extract_entities_endpoint(content: str, domain: str = "biomedical") -> Dict[str, Any]:
    """Extract entities from text content."""
    try:
        from agent.tools.llm_analysis import extract_entities
        return extract_entities(content, domain)
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-relationships")
async def analyze_relationships_endpoint(
    content1: str,
    content2: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze relationships between two pieces of content."""
    try:
        from agent.tools.llm_analysis import find_relationships
        return find_relationships(content1, content2, context)
    except Exception as e:
        logger.error(f"Error analyzing relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-file")
async def parse_file_endpoint(content: str, file_type: str, file_name: str = "") -> Dict[str, Any]:
    """Parse a single file content."""
    try:
        from agent.tools.file_parser import parse_data_entry

        entry_dict = {
            "_id": f"temp_{hash(content) % 10000}",
            "type": file_type,
            "name": file_name,
            "content": content,
            "description": "",
            "addedBy": "api_user",
            "addedAt": datetime.now().isoformat()
        }

        return parse_data_entry(entry_dict)
    except Exception as e:
        logger.error(f"Error parsing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
