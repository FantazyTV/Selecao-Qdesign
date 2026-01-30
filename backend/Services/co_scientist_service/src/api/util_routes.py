"""
Utility API Routes - Health, metrics, run history, and status endpoints.
"""

import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from prometheus_client import generate_latest
from pathlib import Path

from .models import (
    HypothesisResponse, StatusResponse,
    HealthResponse, MetricsResponse
)
from .workflow_routes import get_state
from ..monitoring.metrics import REQUESTS, update_uptime
from ..providers.factory import get_provider

router = APIRouter(tags=["utility"])

_start_time = time.time()


# ============================================================================
# HEALTH & METRICS ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health():
    """Detailed health check endpoint."""
    uptime = time.time() - _start_time
    
    components = {
        "api": "healthy",
        "state_manager": "healthy",
    }
    
    # Check provider
    try:
        provider = get_provider()
        components["llm_provider"] = "healthy" if provider else "degraded"
    except Exception:
        components["llm_provider"] = "unhealthy"
    
    # Check knowledge graph directory
    kg_dir = Path("data/knowledge_graphs")
    if kg_dir.exists():
        kg_files = list(kg_dir.glob("*.json"))
        components["knowledge_graphs"] = f"healthy ({len(kg_files)} files)"
    else:
        components["knowledge_graphs"] = "no data"
    
    overall = "healthy"
    if any(v == "unhealthy" for v in components.values()):
        overall = "unhealthy"
    elif any(v == "degraded" for v in components.values()):
        overall = "degraded"
    
    return HealthResponse(
        status=overall,
        version="2.0.0",
        uptime_seconds=uptime,
        components=components,
    )


@router.get("/metrics", summary="Prometheus metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    update_uptime()
    return generate_latest()


@router.get("/metrics/summary", response_model=MetricsResponse, summary="Metrics summary")
async def metrics_summary():
    """Get a summary of service metrics."""
    REQUESTS.labels(endpoint="/metrics/summary", method="GET", status="success").inc()
    state = get_state()
    stats = state.get_statistics()
    uptime = time.time() - _start_time
    
    return MetricsResponse(
        total_runs=stats["total_runs"],
        successful_runs=stats["by_status"].get("COMPLETED", 0),
        failed_runs=stats["by_status"].get("FAILED", 0),
        active_runs=stats["active_runs"],
        uptime_seconds=uptime,
    )


# ============================================================================
# RUN MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/status/{run_id}", response_model=StatusResponse, summary="Get run status")
async def status(run_id: str):
    """Get detailed status of a specific workflow run."""
    REQUESTS.labels(endpoint="/status", method="GET", status="success").inc()
    state = get_state()
    run_state = state.get_run(run_id)
    
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return StatusResponse(
        run_id=run_id,
        status=run_state.status,
        created_at=run_state.created_at,
        updated_at=run_state.updated_at,
        current_phase=run_state.current_phase,
        iterations_completed=run_state.current_iteration,
        data=run_state.data
    )


@router.get("/runs", summary="List all runs")
async def list_runs(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip")
):
    """List all workflow runs with optional filtering and pagination."""
    REQUESTS.labels(endpoint="/runs", method="GET", status="success").inc()
    state = get_state()
    
    runs = state.list_runs(status=status_filter, limit=limit, offset=offset)
    stats = state.get_statistics()
    
    return {
        "runs": [
            {
                "run_id": r.run_id,
                "status": r.status,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
                "completed_at": r.completed_at,
                "current_phase": r.current_phase,
                "iterations": r.current_iteration,
            }
            for r in runs
        ],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": stats["total_runs"],
            "returned": len(runs),
        },
        "statistics": stats,
    }


@router.delete("/runs/{run_id}", summary="Delete a run")
async def delete_run(run_id: str):
    """Delete a workflow run from history."""
    REQUESTS.labels(endpoint="/runs/delete", method="DELETE", status="success").inc()
    state = get_state()
    
    if state.delete_run(run_id):
        return {"deleted": True, "run_id": run_id}
    
    raise HTTPException(status_code=404, detail="Run not found")


@router.get("/runs/{run_id}/audit", summary="Get run audit log")
async def get_run_audit(run_id: str):
    """Get audit log for a specific run."""
    REQUESTS.labels(endpoint="/runs/audit", method="GET", status="success").inc()
    state = get_state()
    run_state = state.get_run(run_id)
    
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "run_id": run_id,
        "audit_entries": run_state.audit,
        "total_entries": len(run_state.audit),
    }


# ============================================================================
# HYPOTHESIS ENDPOINT
# ============================================================================

@router.get("/hypothesis/{run_id}", response_model=HypothesisResponse, summary="Get hypothesis")
async def hypothesis(run_id: str):
    """Get the generated hypothesis for a completed run."""
    REQUESTS.labels(endpoint="/hypothesis", method="GET", status="success").inc()
    state = get_state()
    run_state = state.get_run(run_id)
    
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Try to get hypothesis from different locations
    scientist_data = run_state.data.get("scientist", {})
    output = scientist_data.get("output", {})
    hypothesis_data = output.get("hypothesis") or output.get("llm")
    
    # Also get final output if available
    final_output = run_state.data.get("final_output", {})
    evaluation = final_output.get("evaluation", {})
    
    return HypothesisResponse(
        run_id=run_id,
        status=run_state.status,
        hypothesis=hypothesis_data,
        evaluation=evaluation if evaluation else None,
        iterations=run_state.current_iteration,
        final_decision=final_output.get("decision"),
    )
