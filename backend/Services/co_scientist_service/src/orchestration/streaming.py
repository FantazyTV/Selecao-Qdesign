"""
Streaming Workflow - Real-time streaming workflow execution with SSE events.
"""

import json
from typing import AsyncIterator, Optional

from .state_manager import InMemoryStateManager
from .config import (
    WorkflowConfig,
    build_planner_state,
    build_scientist_state,
    build_critic_state,
    build_final_output,
)
from ..agents import PlannerAgent, ScientistAgent, CriticAgent


def _emit(event_type: str, **data) -> str:
    """Emit an SSE-formatted event."""
    return json.dumps({"event": event_type, **data}) + "\n"


async def run_workflow_streaming(
    state: InMemoryStateManager,
    run_id: str,
    payload: dict,
    config: Optional[WorkflowConfig] = None
) -> AsyncIterator[str]:
    """Run the SciAgents-inspired workflow with streaming output."""
    config = config or WorkflowConfig()

    try:
        state.update_run(run_id, status="RUNNING")
        yield _emit("workflow_start", run_id=run_id, config=config.__dict__)

        # Phase 1: Planning
        yield _emit("phase_start", phase="planning", description="Extracting knowledge graph subgraph")
        planner = PlannerAgent()
        planner_result = await planner.run(build_planner_state(payload, config))
        state.update_run(run_id, data={"planner": planner_result.__dict__})

        yield _emit("agent_complete", agent="planner", data={
            "statistics": planner_result.output.get("statistics", {}),
            "kg_metadata": planner_result.output.get("kg_metadata", {}),
            "confidence": planner_result.confidence
        })

        if "error" in planner_result.output:
            yield _emit("error", message=planner_result.output["error"])
            state.update_run(run_id, status="FAILED")
            return

        yield _emit("phase_complete", phase="planning")

        # Phase 2: Hypothesis Generation (Streaming)
        yield _emit("phase_start", phase="hypothesis_generation", description="Generating scientific hypothesis")
        scientist = ScientistAgent()
        scientist_state = build_scientist_state(planner_result.output, payload.get("query", ""))

        full_response = ""
        async for chunk in scientist.run_stream(scientist_state):
            full_response += chunk
            yield _emit("agent_token", agent="scientist", token=chunk)

        try:
            current_hypothesis = json.loads(full_response)
        except json.JSONDecodeError:
            current_hypothesis = {"raw_response": full_response, "parse_error": True}

        scientist_result = scientist._result(current_hypothesis, confidence=0.5)
        state.update_run(run_id, data={**state.get_run(run_id).data, "scientist": scientist_result.__dict__})
        yield _emit("agent_complete", agent="scientist", data={
            "hypothesis_title": current_hypothesis.get("hypothesis", {}).get("title", ""),
            "confidence": scientist_result.confidence
        })
        yield _emit("phase_complete", phase="hypothesis_generation")

        # Phase 3: Critique & Iteration (Streaming)
        async for event in _run_critique_iterations(
            state, run_id, planner_result, current_hypothesis, config
        ):
            yield event

    except Exception as e:
        import traceback
        yield _emit("error", message=str(e), traceback=traceback.format_exc())
        state.update_run(run_id, status="FAILED")


async def _run_critique_iterations(
    state: InMemoryStateManager,
    run_id: str,
    planner_result,
    current_hypothesis: dict,
    config: WorkflowConfig
) -> AsyncIterator[str]:
    """Run the critique and revision iterations."""
    critic = CriticAgent()
    scientist = ScientistAgent()
    iteration = 1
    critic_output = {}

    while iteration <= config.max_iterations:
        yield _emit("phase_start", phase=f"critique_iteration_{iteration}",
                    description=f"Evaluating hypothesis (iteration {iteration}/{config.max_iterations})")

        critic_state = build_critic_state(current_hypothesis, planner_result.output, iteration)
        full_response = ""
        async for chunk in critic.run_stream(critic_state):
            full_response += chunk
            yield _emit("agent_token", agent="critic", token=chunk)

        try:
            critic_output = json.loads(full_response)
        except json.JSONDecodeError:
            critic_output = {"raw_response": full_response, "parse_error": True}

        critic_result = critic._result(critic_output, confidence=0.5)
        state.update_run(run_id, data={
            **state.get_run(run_id).data,
            f"critic_iteration_{iteration}": critic_result.__dict__
        })

        decision = critic_output.get("decision", "REVISE")
        yield _emit("agent_complete", agent="critic", data={
            "decision": decision, "iteration": iteration,
            "overall_score": critic_output.get("scores", {}).get("overall", {}).get("score")
        })
        yield _emit("phase_complete", phase=f"critique_iteration_{iteration}")

        if not critic.should_continue_iteration(critic_output, config.max_iterations, iteration):
            yield _emit("iteration_decision", decision=decision, final=True)
            break

        yield _emit("iteration_decision", decision=decision, final=False, next_iteration=iteration + 1)

        if iteration < config.max_iterations:
            async for event in _run_revision(
                state, run_id, scientist, critic, critic_output, current_hypothesis, planner_result, iteration
            ):
                if isinstance(event, dict):
                    current_hypothesis = event
                else:
                    yield event

        iteration += 1

    # Final Assembly
    yield _emit("phase_start", phase="assembly", description="Assembling final output")
    final_output = build_final_output(current_hypothesis, critic_output, planner_result.output, iteration)
    state.update_run(run_id, data={**state.get_run(run_id).data, "final_output": final_output})
    yield _emit("phase_complete", phase="assembly")
    state.update_run(run_id, status="COMPLETED")
    yield _emit("workflow_complete", run_id=run_id, final_decision=critic_output.get("decision"), iterations=iteration)


async def _run_revision(state, run_id, scientist, critic, critic_output, current_hypothesis, planner_result, iteration):
    """Run a single revision iteration."""
    yield _emit("phase_start", phase=f"revision_{iteration}", description="Revising hypothesis based on feedback")

    revision_guidance = critic.get_revision_guidance(critic_output)
    scientist_state = build_scientist_state(planner_result.output, "")
    scientist_state["revision_guidance"] = revision_guidance
    scientist_state["previous_hypothesis"] = current_hypothesis

    full_response = ""
    async for chunk in scientist.run_stream(scientist_state):
        full_response += chunk
        yield _emit("agent_token", agent="scientist", token=chunk)

    try:
        new_hypothesis = json.loads(full_response)
    except json.JSONDecodeError:
        new_hypothesis = {"raw_response": full_response, "parse_error": True}

    state.update_run(run_id, data={
        **state.get_run(run_id).data,
        f"scientist_revision_{iteration}": {"output": new_hypothesis}
    })

    yield _emit("agent_complete", agent="scientist", mode="revision")
    yield _emit("phase_complete", phase=f"revision_{iteration}")
    yield new_hypothesis  # Return the updated hypothesis
