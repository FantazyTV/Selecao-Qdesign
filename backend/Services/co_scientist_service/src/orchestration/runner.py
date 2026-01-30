"""
Workflow Runner - Non-streaming workflow execution.
"""

from typing import Optional
import traceback

from .state_manager import InMemoryStateManager
from .config import (
    WorkflowConfig,
    build_planner_state,
    build_scientist_state,
    build_critic_state,
    build_final_output,
)
from ..agents import PlannerAgent, ScientistAgent, CriticAgent


async def run_workflow(
    state: InMemoryStateManager,
    run_id: str,
    payload: dict,
    config: Optional[WorkflowConfig] = None
):
    """Run the SciAgents-inspired workflow (non-streaming)."""
    config = config or WorkflowConfig()
    state.update_run(run_id, status="RUNNING")

    try:
        # Phase 1: Planning
        planner = PlannerAgent()
        planner_result = await planner.run(build_planner_state(payload, config))
        state.update_run(run_id, data={"planner": planner_result.__dict__})

        if "error" in planner_result.output:
            state.update_run(run_id, status="FAILED")
            return

        # Phase 2: Hypothesis Generation
        scientist = ScientistAgent()
        scientist_state = build_scientist_state(planner_result.output, payload.get("query", ""))
        scientist_result = await scientist.run(scientist_state)
        state.update_run(run_id, data={**state.get_run(run_id).data, "scientist": scientist_result.__dict__})

        # Phase 3: Critique & Iteration
        critic = CriticAgent()
        iteration = 1
        current_hypothesis = scientist_result.output
        critic_result = None

        while iteration <= config.max_iterations:
            critic_state = build_critic_state(current_hypothesis, planner_result.output, iteration)
            critic_result = await critic.run(critic_state)
            state.update_run(run_id, data={
                **state.get_run(run_id).data,
                f"critic_iteration_{iteration}": critic_result.__dict__
            })

            if not critic.should_continue_iteration(critic_result.output, config.max_iterations, iteration):
                break

            if iteration < config.max_iterations:
                revision_guidance = critic.get_revision_guidance(critic_result.output)
                scientist_state["revision_guidance"] = revision_guidance
                scientist_state["previous_hypothesis"] = current_hypothesis
                scientist_result = await scientist.run(scientist_state)
                current_hypothesis = scientist_result.output
                state.update_run(run_id, data={
                    **state.get_run(run_id).data,
                    f"scientist_revision_{iteration}": scientist_result.__dict__
                })

            iteration += 1

        # Phase 4: Final Assembly
        final_output = build_final_output(
            current_hypothesis,
            critic_result.output if critic_result else {},
            planner_result.output,
            iteration
        )
        state.update_run(run_id, data={**state.get_run(run_id).data, "final_output": final_output})
        state.update_run(run_id, status="COMPLETED")

    except Exception as e:
        state.update_run(run_id, status="FAILED", data={
            "error": str(e), "traceback": traceback.format_exc()
        })
