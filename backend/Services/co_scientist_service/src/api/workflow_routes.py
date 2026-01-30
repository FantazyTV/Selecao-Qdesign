"""
Workflow API Routes - Endpoints for workflow execution.
"""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Optional

from .models import RunRequest, RunResponse
from ..monitoring.metrics import REQUESTS
from ..orchestration.state_manager import InMemoryStateManager
from ..orchestration import (
    run_workflow, run_workflow_streaming, WorkflowConfig
)

router = APIRouter(tags=["workflow"])
state = InMemoryStateManager()


def get_state():
    """Get shared state manager."""
    return state


@router.post("/run", response_model=RunResponse)
async def run(payload: RunRequest):
    """Run legacy workflow."""
    REQUESTS.labels("/run").inc()
    run_id = f"run_{len(state._runs) + 1}"
    state.create_run(run_id)
    await run_workflow(state, run_id, payload.model_dump())
    return RunResponse(run_id=run_id, status="COMPLETED")


@router.post("/run/stream")
async def run_streaming(payload: RunRequest):
    """Run workflow with real-time streaming."""
    REQUESTS.labels("/run/stream").inc()
    run_id = f"run_{len(state._runs) + 1}"
    state.create_run(run_id)

    async def event_generator():
        yield f"data: {json.dumps({'event': 'workflow_start', 'run_id': run_id})}\n\n"
        async for event_line in run_workflow_streaming(state, run_id, payload.model_dump()):
            yield f"data: {event_line}\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/v2/run")
async def run_v2(
    kg_path: str, query: Optional[str] = None,
    concept_a: Optional[str] = None, concept_b: Optional[str] = None,
    exploration_mode: str = "balanced", max_iterations: int = 3
):
    """Run SciAgents-inspired workflow with pre-built knowledge graph."""
    REQUESTS.labels("/v2/run").inc()
    run_id = f"run_v2_{len(state._runs) + 1}"
    state.create_run(run_id)

    payload = {"kg_path": kg_path, "query": query, "concept_a": concept_a,
               "concept_b": concept_b, "exploration_mode": exploration_mode}
    config = WorkflowConfig(max_iterations=max_iterations, exploration_mode=exploration_mode)

    await run_workflow(state, run_id, payload, config)
    run_state = state.get_run(run_id)
    return {"run_id": run_id, "status": run_state.status, "final_output": run_state.data.get("final_output")}


@router.post("/v2/run/stream")
async def run_v2_streaming(
    kg_path: str, query: Optional[str] = None,
    concept_a: Optional[str] = None, concept_b: Optional[str] = None,
    exploration_mode: str = "balanced", max_iterations: int = 3
):
    """Run SciAgents-inspired workflow with real-time streaming."""
    REQUESTS.labels("/v2/run/stream").inc()
    run_id = f"run_v2_{len(state._runs) + 1}"
    state.create_run(run_id)

    payload = {"kg_path": kg_path, "query": query, "concept_a": concept_a,
               "concept_b": concept_b, "exploration_mode": exploration_mode}
    config = WorkflowConfig(max_iterations=max_iterations, exploration_mode=exploration_mode)

    async def event_generator():
        async for event_line in run_workflow_streaming(state, run_id, payload, config):
            yield f"data: {event_line}\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
