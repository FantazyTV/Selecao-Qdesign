"""
Utility API Routes - Health, metrics, streaming, run history, and legacy endpoints.

Enhanced with:
- Run history and listing
- Detailed health checks
- Metrics summary
- Enhanced status responses
"""

import json
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from prometheus_client import generate_latest
from pathlib import Path
from datetime import datetime, timezone

from .models import (
    FeedbackRequest, HypothesisResponse, StatusResponse,
    HealthResponse, MetricsResponse, ErrorResponse
)
from .workflow_routes import get_state
from ..monitoring.metrics import (
    REQUESTS, update_uptime,
    WORKFLOW_RUNS, ACTIVE_WORKFLOWS,
    LLM_CACHE_HITS, LLM_CACHE_MISSES,
)
from ..monitoring.audit_log import audit_entry
from ..providers.factory import get_provider

router = APIRouter(tags=["utility"])

_start_time = time.time()


# ============================================================================
# STATUS & HISTORY ENDPOINTS
# ============================================================================

@router.get("/status/{run_id}", response_model=StatusResponse)
async def status(run_id: str):
    """Get detailed status of a specific run."""
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


@router.get("/runs")
async def list_runs(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip")
):
    """
    List all workflow runs with optional filtering.
    
    Returns paginated list of runs sorted by creation time (newest first).
    """
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


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str):
    """Delete a workflow run from history."""
    REQUESTS.labels(endpoint="/runs/delete", method="DELETE", status="success").inc()
    state = get_state()
    
    if state.delete_run(run_id):
        return {"deleted": True, "run_id": run_id}
    
    raise HTTPException(status_code=404, detail="Run not found")


@router.get("/runs/{run_id}/audit")
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
# FEEDBACK & HYPOTHESIS ENDPOINTS
# ============================================================================

@router.post("/human/feedback")
async def feedback(payload: FeedbackRequest):
    """Submit human feedback for a workflow run."""
    REQUESTS.labels(endpoint="/human/feedback", method="POST", status="success").inc()
    state = get_state()
    run_state = state.get_run(payload.run_id)
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found")
    
    entry = audit_entry("human_feedback", payload.model_dump())
    state.add_audit(payload.run_id, "human_feedback", details=payload.model_dump())
    
    return {
        "ok": True,
        "run_id": payload.run_id,
        "feedback_recorded": {
            "stage": payload.stage,
            "action": payload.action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }


@router.get("/hypothesis/{run_id}", response_model=HypothesisResponse)
async def hypothesis(run_id: str):
    """Get the generated hypothesis for a run."""
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


# ============================================================================
# HEALTH & METRICS ENDPOINTS
# ============================================================================

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    update_uptime()
    return generate_latest()


@router.get("/metrics/summary", response_model=MetricsResponse)
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


@router.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check endpoint."""
    uptime = time.time() - _start_time
    
    # Check components
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


# ============================================================================
# KNOWLEDGE GRAPH ENDPOINTS
# ============================================================================

@router.get("/knowledge-graph")
async def get_knowledge_graph():
    """Get the current persisted knowledge graph from Layer 4."""
    REQUESTS.labels(endpoint="/knowledge-graph", method="GET", status="success").inc()
    graph_file = Path("data/kb_store/layer4_graph/graph.json")
    if not graph_file.exists():
        raise HTTPException(status_code=404, detail="Knowledge base not yet built")
    with open(graph_file, "r") as f:
        graph_data = json.load(f)
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    return {
        "status": "success",
        "metadata": {
            "node_count": len(nodes), "edge_count": len(edges),
            "entity_types": list(set(n.get("entity_type") for n in nodes if "entity_type" in n)),
            "relation_types": list(set(e.get("relation_type") for e in edges if "relation_type" in e))
        },
        "graph": {"nodes": nodes, "edges": edges}
    }


@router.post("/stream")
async def stream_response(payload: dict):
    """Stream reasoning from an agent in real-time (SSE)."""
    REQUESTS.labels("/stream").inc()
    agent_name = payload.get("agent", "scientist")
    state_dict = payload.get("state", {})
    provider = get_provider()
    from ..prompts.loader import load_prompt
    prompt_text = load_prompt(agent_name)
    messages = [{"role": "system", "content": prompt_text}, {"role": "user", "content": json.dumps(state_dict, indent=2)}]

    async def generate():
        try:
            async for chunk in provider.stream(messages):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
