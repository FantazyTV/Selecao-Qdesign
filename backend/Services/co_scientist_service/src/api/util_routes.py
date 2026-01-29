"""
Utility API Routes - Health, metrics, streaming, legacy endpoints.
"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from prometheus_client import generate_latest
from pathlib import Path

from .models import FeedbackRequest, HypothesisResponse, StatusResponse
from .workflow_routes import get_state
from ..monitoring.metrics import REQUESTS
from ..monitoring.audit_log import audit_entry
from ..providers.factory import get_provider

router = APIRouter(tags=["utility"])


@router.get("/status/{run_id}", response_model=StatusResponse)
async def status(run_id: str):
    REQUESTS.labels("/status").inc()
    state = get_state()
    run_state = state.get_run(run_id)
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found")
    return StatusResponse(run_id=run_id, status=run_state.status, data=run_state.data)


@router.post("/human/feedback")
async def feedback(payload: FeedbackRequest):
    REQUESTS.labels("/human/feedback").inc()
    state = get_state()
    run_state = state.get_run(payload.run_id)
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found")
    entry = audit_entry("human_feedback", payload.model_dump())
    state.add_audit(payload.run_id, entry)
    return {"ok": True}


@router.get("/hypothesis/{run_id}", response_model=HypothesisResponse)
async def hypothesis(run_id: str):
    REQUESTS.labels("/hypothesis").inc()
    state = get_state()
    run_state = state.get_run(run_id)
    if not run_state:
        raise HTTPException(status_code=404, detail="Run not found")
    output = run_state.data.get("scientist", {}).get("output", {})
    hypothesis_data = output.get("hypothesis") or output.get("llm")
    return HypothesisResponse(run_id=run_id, hypothesis=hypothesis_data)


@router.get("/metrics")
async def metrics():
    return generate_latest()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/knowledge-graph")
async def get_knowledge_graph():
    """Get the current persisted knowledge graph from Layer 4."""
    REQUESTS.labels("/knowledge-graph").inc()
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
