"""
Human-in-the-Loop API Routes

Endpoints for managing workflow checkpoints and human intervention.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..orchestration.checkpoints import (
    CheckpointManager,
    CheckpointStatus,
    get_checkpoint_manager,
)
from ..orchestration.state_manager import InMemoryStateManager
from ..orchestration.enhanced_runner import run_enhanced_workflow
from ..orchestration.enhanced_config import WorkflowConfig, HITLMode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/hitl", tags=["human-in-the-loop"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ResolveCheckpointRequest(BaseModel):
    """Request to resolve a checkpoint."""
    status: str = Field(..., description="Resolution status: approved, modified, rejected")
    feedback: Optional[str] = Field(None, description="Human feedback or notes")
    modifications: Optional[dict] = Field(None, description="Modifications to agent output")
    override_output: Optional[dict] = Field(None, description="Complete override of agent output")


class HITLRunRequest(BaseModel):
    """Request to start a HITL-enabled workflow."""
    kg_path: Optional[str] = Field(None, description="Path to knowledge graph JSON")
    knowledge_graph: Optional[dict] = Field(None, description="Direct knowledge graph data")
    query: Optional[str] = Field(None, description="Research query")
    concept_a: Optional[str] = Field(None, description="First concept to connect")
    concept_b: Optional[str] = Field(None, description="Second concept to connect")
    exploration_mode: str = Field("balanced", description="Path finding strategy")
    max_iterations: int = Field(3, ge=1, le=10)
    hitl_mode: str = Field("critical", description="HITL mode: disabled, critical, full, custom")
    hitl_stages: Optional[list[str]] = Field(None, description="Custom HITL stages")
    hitl_timeout: int = Field(300, ge=30, le=3600, description="Checkpoint timeout in seconds")
    enable_ontologist: bool = Field(True, description="Enable ontologist agent")
    enable_scientist2: bool = Field(True, description="Enable scientist2 expansion")
    enable_literature_search: bool = Field(True, description="Enable web search for literature")


class CheckpointResponse(BaseModel):
    """Response with checkpoint details."""
    id: str
    run_id: str
    stage: str
    status: str
    summary: str
    options: list[str]
    created_at: str
    timeout_seconds: int
    output_preview: Optional[dict] = None


class PendingCheckpointsResponse(BaseModel):
    """Response with list of pending checkpoints."""
    checkpoints: list[CheckpointResponse]
    total: int


# ============================================================================
# SHARED STATE
# ============================================================================

# Import shared state from workflow routes
from .workflow_routes import get_state


# ============================================================================
# ROUTES
# ============================================================================

@router.post("/run", summary="Start HITL-enabled workflow")
async def start_hitl_workflow(
    request: HITLRunRequest,
    background_tasks: BackgroundTasks
):
    """Start a workflow with human-in-the-loop checkpoints.
    
    The workflow will pause at configured stages and wait for human review.
    Use the /checkpoints endpoints to view and resolve pending checkpoints.
    """
    state = get_state()
    run_id = f"hitl_run_{len(state._runs) + 1}"
    state.create_run(run_id)
    
    # Parse HITL mode
    try:
        hitl_mode = HITLMode(request.hitl_mode)
    except ValueError:
        hitl_mode = HITLMode.CRITICAL_ONLY
    
    # Build config
    config = WorkflowConfig(
        max_iterations=request.max_iterations,
        exploration_mode=request.exploration_mode,
        hitl_mode=hitl_mode,
        hitl_stages=request.hitl_stages or [],
        hitl_timeout=request.hitl_timeout,
        enable_ontologist=request.enable_ontologist,
        enable_scientist2=request.enable_scientist2,
        enable_literature_search=request.enable_literature_search,
    )
    
    # Build payload
    payload = {
        "kg_path": request.kg_path,
        "knowledge_graph": request.knowledge_graph,
        "query": request.query,
        "concept_a": request.concept_a,
        "concept_b": request.concept_b,
        "exploration_mode": request.exploration_mode,
    }
    
    # Start workflow in background
    background_tasks.add_task(
        run_enhanced_workflow,
        state,
        run_id,
        payload,
        config
    )
    
    return {
        "run_id": run_id,
        "status": "RUNNING",
        "hitl_mode": hitl_mode.value,
        "message": "Workflow started. Use /v2/hitl/checkpoints to monitor and resolve checkpoints."
    }


@router.get("/checkpoints", response_model=PendingCheckpointsResponse, summary="Get pending checkpoints")
async def get_pending_checkpoints(run_id: Optional[str] = None):
    """Get all pending checkpoints awaiting human review.
    
    Optionally filter by run_id.
    """
    checkpoint_mgr = get_checkpoint_manager()
    pending = checkpoint_mgr.get_pending_checkpoints(run_id)
    
    checkpoints = []
    for cp in pending:
        # Get truncated output using checkpoint's method
        output_preview = _truncate_output(cp.data.agent_output, max_length=300)
        checkpoints.append(CheckpointResponse(
            id=cp.id,
            run_id=cp.run_id,
            stage=cp.stage.value,
            status=cp.status.value,
            summary=cp.data.summary,
            options=cp.data.options,
            created_at=cp.created_at,
            timeout_seconds=cp.timeout_seconds,
            output_preview=output_preview
        ))
    
    return PendingCheckpointsResponse(
        checkpoints=checkpoints,
        total=len(checkpoints)
    )


def _truncate_output(output: dict, max_length: int = 500) -> dict:
    """Truncate output dictionary values for preview."""
    preview = {}
    for key, value in output.items():
        if isinstance(value, str) and len(value) > max_length:
            preview[key] = value[:max_length] + "..."
        elif isinstance(value, dict):
            preview[key] = _truncate_output(value, max_length)
        elif isinstance(value, list) and len(value) > 5:
            preview[key] = value[:5] + ["..."]
        else:
            preview[key] = value
    return preview


@router.get("/checkpoints/{checkpoint_id}", summary="Get checkpoint details")
async def get_checkpoint(checkpoint_id: str):
    """Get full details of a specific checkpoint."""
    checkpoint_mgr = get_checkpoint_manager()
    checkpoint = checkpoint_mgr.get_checkpoint(checkpoint_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail=f"Checkpoint {checkpoint_id} not found")
    
    return checkpoint.to_dict()


@router.get("/checkpoints/{checkpoint_id}/output", summary="Get full agent output")
async def get_checkpoint_output(checkpoint_id: str):
    """Get the full agent output for a checkpoint (not truncated)."""
    checkpoint_mgr = get_checkpoint_manager()
    checkpoint = checkpoint_mgr.get_checkpoint(checkpoint_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail=f"Checkpoint {checkpoint_id} not found")
    
    return {
        "checkpoint_id": checkpoint_id,
        "stage": checkpoint.stage.value,
        "agent_output": checkpoint.data.agent_output
    }


@router.post("/checkpoints/{checkpoint_id}/resolve", summary="Resolve a checkpoint")
async def resolve_checkpoint(checkpoint_id: str, request: ResolveCheckpointRequest):
    """Resolve a pending checkpoint with human decision.
    
    Status options:
    - **approved**: Accept the agent output as-is
    - **modified**: Accept with modifications (provide modifications dict)
    - **rejected**: Reject and cancel the workflow stage
    """
    checkpoint_mgr = get_checkpoint_manager()
    checkpoint = checkpoint_mgr.get_checkpoint(checkpoint_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail=f"Checkpoint {checkpoint_id} not found")
    
    if checkpoint.status != CheckpointStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Checkpoint already resolved with status: {checkpoint.status.value}"
        )
    
    # Map status string to enum
    status_map = {
        "approved": CheckpointStatus.APPROVED,
        "modified": CheckpointStatus.MODIFIED,
        "rejected": CheckpointStatus.REJECTED,
    }
    
    status = status_map.get(request.status.lower())
    if not status:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}. Must be one of: approved, modified, rejected"
        )
    
    try:
        result = checkpoint_mgr.resolve_checkpoint(
            checkpoint_id=checkpoint_id,
            status=status,
            human_input=request.override_output,
            modifications=request.modifications,
            feedback=request.feedback
        )
        
        return {
            "checkpoint_id": checkpoint_id,
            "status": result.status.value,
            "resolved_at": result.resolved_at,
            "message": f"Checkpoint resolved as {result.status.value}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/checkpoints/{checkpoint_id}/skip", summary="Skip a checkpoint")
async def skip_checkpoint(checkpoint_id: str):
    """Skip a checkpoint (auto-approve without review)."""
    checkpoint_mgr = get_checkpoint_manager()
    checkpoint = checkpoint_mgr.get_checkpoint(checkpoint_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail=f"Checkpoint {checkpoint_id} not found")
    
    if checkpoint.status != CheckpointStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Checkpoint already resolved: {checkpoint.status.value}"
        )
    
    checkpoint_mgr.skip_checkpoint(checkpoint_id)
    
    return {
        "checkpoint_id": checkpoint_id,
        "status": "skipped",
        "message": "Checkpoint skipped"
    }


@router.get("/runs/{run_id}/checkpoints", summary="Get checkpoints for a run")
async def get_run_checkpoints(run_id: str):
    """Get all checkpoints (pending and resolved) for a specific workflow run."""
    checkpoint_mgr = get_checkpoint_manager()
    checkpoints = checkpoint_mgr.get_checkpoints_for_run(run_id)
    
    return {
        "run_id": run_id,
        "checkpoints": [cp.to_dict() for cp in checkpoints],
        "total": len(checkpoints),
        "pending": sum(1 for cp in checkpoints if cp.status == CheckpointStatus.PENDING)
    }


@router.get("/runs/{run_id}/status", summary="Get HITL run status")
async def get_hitl_run_status(run_id: str):
    """Get the status of a HITL-enabled workflow run."""
    state = get_state()
    run = state.get_run(run_id)
    
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    checkpoint_mgr = get_checkpoint_manager()
    pending_checkpoints = checkpoint_mgr.get_pending_checkpoints(run_id)
    
    return {
        "run_id": run_id,
        "status": run.status,
        "pending_checkpoints": len(pending_checkpoints),
        "awaiting_human_input": len(pending_checkpoints) > 0,
        "data_keys": list(run.data.keys()) if run.data else [],
        "created_at": run.created_at
    }
