"""
Asynchronous FastAPI router for expand service endpoints.
Expands a node by retrieving similar items from Qdrant and updating the knowledge graph.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
from datetime import datetime
import asyncio
import json
from agent.high_level_tools.protein_graph_from_sequence import build_protein_graph_from_sequence
from agent.high_level_tools.protein_graph_from_cif import build_protein_graph_from_cif
from agent.high_level_tools.protein_graph_from_pdf import build_protein_graph_from_pdf
from agent.high_level_tools.pdf_graph_from_image import build_pdf_graph_from_image
from agent.high_level_tools.protein_graph_from_query import normalize_graph
from graph.graph_merge_utils import merge_graphs
from agent.tools.embedder import esm2_embed, text_embed, clip_embed
from agent.tools.vector_search import retrieve_similar_fasta, retrieve_similar_cif, retrieve_similar_pdfs, retrieve_similar_text_chunks, retrieve_similar_images
from agent.tools.qdrant_retrieval import get_cif_by_pdb_id, get_fasta_by_uniprot_id

router = APIRouter(prefix="/api/v1/expand", tags=["expand"])

# In-memory job storage (use Redis or database in production)
expand_job_results: Dict[str, Dict[str, Any]] = {}

async def _expand_node_background(job_id: str, node_id: str, current_graph: dict):
    """Background task that immediately returns test data."""
    try:
        expand_job_results[job_id] = {
            "status": "processing", 
            "started_at": datetime.now().isoformat()
        }
        
        # Wait 10 seconds for testing
        await asyncio.sleep(10)
        
        # Load the test JSON file
        with open('expand_20260130_130921.json', 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # Set job as completed with test response
        expand_job_results[job_id] = {
            "status": "completed",
            "result": test_data,
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {str(e)}")
        expand_job_results[job_id] = {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }

@router.post("/process")
async def expand_process(request: dict, background_tasks: BackgroundTasks):
    """
    Expand a node by retrieving similar items and returning a job ID. Returns the full knowledgeGraph in result.
    """
    try:
        node_data = request.get("node")
        if not node_data:
            raise HTTPException(status_code=400, detail="node is required")
        node_id = node_data.get("nodeId")
        current_graph = node_data.get("knowledgeGraph")
        if not node_id:
            raise HTTPException(status_code=400, detail="nodeId is required")
        if not current_graph:
            raise HTTPException(status_code=400, detail="knowledgeGraph is required")
        job_id = f"expand_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(node_id)) % 10000}"
        background_tasks.add_task(_expand_node_background, job_id, node_id, current_graph)
        return {
            "jobId": job_id,
            "status": "processing",
            "message": "Expand started. Use /status endpoint to check progress.",
            "estimatedCompletion": "10 seconds"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status/{job_id}")
async def get_expand_status(job_id: str):
    if job_id not in expand_job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    return expand_job_results[job_id]

@router.get("/result/{job_id}")
async def get_expand_result(job_id: str):
    if job_id not in expand_job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    job = expand_job_results[job_id]
    if job["status"] == "processing":
        raise HTTPException(status_code=202, detail="Job still processing")
    elif job["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"Job failed: {job.get('error')}")
    elif job["status"] == "completed":
        return job["result"]
    else:
        raise HTTPException(status_code=500, detail="Unknown job status")
