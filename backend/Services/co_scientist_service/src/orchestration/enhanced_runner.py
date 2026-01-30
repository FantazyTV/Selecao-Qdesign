"""
Enhanced Workflow Runner

Multi-agent workflow with:
- Ontologist for deep KG interpretation
- Scientist2 for hypothesis expansion
- Human-in-the-loop checkpoints
- Literature search integration
- Novelty assessment
"""

import logging
import traceback
from typing import Optional

from .state_manager import InMemoryStateManager
from .enhanced_config import (
    WorkflowConfig,
    HITLMode,
    build_planner_state,
    build_ontologist_state,
    build_scientist_state,
    build_scientist2_state,
    build_critic_state,
    build_final_output,
)
from .checkpoints import (
    CheckpointManager,
    CheckpointStage,
    CheckpointStatus,
    get_checkpoint_manager,
)
from ..agents import PlannerAgent, ScientistAgent, CriticAgent
from ..agents.ontologist_agent import OntologistAgent
from ..agents.scientist2_agent import Scientist2Agent

logger = logging.getLogger(__name__)


async def run_enhanced_workflow(
    state: InMemoryStateManager,
    run_id: str,
    payload: dict,
    config: Optional[WorkflowConfig] = None
) -> dict:
    """Run the enhanced multi-agent workflow.
    
    Pipeline:
    1. Planner: Load KG, extract subgraph → [HITL checkpoint]
    2. Ontologist: Interpret KG relationships → [HITL checkpoint]
    3. Scientist1: Generate initial hypothesis → [HITL checkpoint]
    4. Scientist2: Expand with details → [HITL checkpoint]
    5. Critic: Evaluate → [HITL checkpoint]
    6. Iteration loop if needed
    7. Final assembly → [HITL checkpoint]
    
    Args:
        state: State manager for run tracking
        run_id: Unique run identifier
        payload: Request payload with KG path, query, etc.
        config: Workflow configuration
        
    Returns:
        Final output dictionary
    """
    config = config or WorkflowConfig()
    checkpoint_mgr = get_checkpoint_manager() if config.hitl_mode != HITLMode.DISABLED else None
    active_hitl_stages = config.get_active_hitl_stages()
    
    state.update_run(run_id, status="RUNNING")
    
    ontologist_output = None
    expanded_hypothesis = None
    literature_refs = []
    
    try:
        # ============================================================
        # PHASE 1: PLANNING
        # ============================================================
        logger.info(f"[{run_id}] Phase 1: Planning")
        
        planner = PlannerAgent()
        planner_result = await planner.run(build_planner_state(payload, config))
        
        state.update_run(run_id, data={"planner": planner_result.__dict__})
        
        if "error" in planner_result.output:
            state.update_run(run_id, status="FAILED")
            return {"error": planner_result.output["error"]}
        
        # HITL Checkpoint: Post-Planning
        if checkpoint_mgr and "post_planning" in active_hitl_stages:
            planner_result.output = await _handle_checkpoint(
                checkpoint_mgr, run_id, CheckpointStage.POST_PLANNING,
                planner_result.output,
                "Review extracted subgraph and path selection",
                config.hitl_timeout
            )
            if planner_result.output.get("_rejected"):
                state.update_run(run_id, status="CANCELLED")
                return {"error": "Workflow cancelled at planning stage", "reason": planner_result.output.get("reason")}
        
        # ============================================================
        # PHASE 2: ONTOLOGICAL INTERPRETATION (Optional)
        # ============================================================
        if config.enable_ontologist:
            logger.info(f"[{run_id}] Phase 2: Ontological Interpretation")
            
            ontologist = OntologistAgent()
            ontologist_state = build_ontologist_state(planner_result.output, payload.get("query", ""))
            ontologist_result = await ontologist.run(ontologist_state)
            
            state.update_run(run_id, data={**state.get_run(run_id).data, "ontologist": ontologist_result.__dict__})
            
            if "error" not in ontologist_result.output:
                ontologist_output = ontologist_result.output
                
                # HITL Checkpoint: Post-Ontology
                if checkpoint_mgr and "post_ontology" in active_hitl_stages:
                    ontologist_output = await _handle_checkpoint(
                        checkpoint_mgr, run_id, CheckpointStage.POST_ONTOLOGY,
                        ontologist_output,
                        "Review ontological interpretation of knowledge graph",
                        config.hitl_timeout
                    )
        
        # ============================================================
        # PHASE 3: INITIAL HYPOTHESIS GENERATION
        # ============================================================
        logger.info(f"[{run_id}] Phase 3: Hypothesis Generation")
        
        scientist = ScientistAgent()
        scientist_state = build_scientist_state(
            planner_result.output,
            payload.get("query", ""),
            ontologist_output
        )
        scientist_result = await scientist.run(scientist_state)
        
        state.update_run(run_id, data={**state.get_run(run_id).data, "scientist": scientist_result.__dict__})
        
        if "error" in scientist_result.output:
            state.update_run(run_id, status="FAILED")
            return {"error": scientist_result.output["error"]}
        
        current_hypothesis = scientist_result.output
        
        # HITL Checkpoint: Post-Hypothesis
        if checkpoint_mgr and "post_hypothesis" in active_hitl_stages:
            current_hypothesis = await _handle_checkpoint(
                checkpoint_mgr, run_id, CheckpointStage.POST_HYPOTHESIS,
                current_hypothesis,
                "Review initial hypothesis before expansion",
                config.hitl_timeout
            )
            if current_hypothesis.get("_rejected"):
                state.update_run(run_id, status="CANCELLED")
                return {"error": "Workflow cancelled at hypothesis stage", "reason": current_hypothesis.get("reason")}
        
        # ============================================================
        # PHASE 4: HYPOTHESIS EXPANSION (Optional)
        # ============================================================
        if config.enable_scientist2:
            logger.info(f"[{run_id}] Phase 4: Hypothesis Expansion")
            
            scientist2 = Scientist2Agent(enable_literature_search=config.enable_literature_search)
            scientist2_state = build_scientist2_state(
                current_hypothesis,
                planner_result.output,
                payload.get("query", ""),
                ontologist_output
            )
            scientist2_result = await scientist2.run(scientist2_state)
            
            state.update_run(run_id, data={**state.get_run(run_id).data, "scientist2": scientist2_result.__dict__})
            
            if "error" not in scientist2_result.output:
                expanded_hypothesis = scientist2_result.output
                
                # Extract literature references
                if expanded_hypothesis.get("citations"):
                    literature_refs = expanded_hypothesis["citations"]
                
                # HITL Checkpoint: Post-Expansion
                if checkpoint_mgr and "post_expansion" in active_hitl_stages:
                    expanded_hypothesis = await _handle_checkpoint(
                        checkpoint_mgr, run_id, CheckpointStage.POST_EXPANSION,
                        expanded_hypothesis,
                        "Review expanded hypothesis with quantitative details",
                        config.hitl_timeout
                    )
        
        # ============================================================
        # PHASE 5: CRITIQUE & ITERATION
        # ============================================================
        logger.info(f"[{run_id}] Phase 5: Critique & Iteration")
        
        critic = CriticAgent()
        iteration = 1
        critic_result = None
        
        while iteration <= config.max_iterations:
            logger.info(f"[{run_id}] Iteration {iteration}/{config.max_iterations}")
            
            # Use expanded hypothesis for critique if available
            hypothesis_to_critique = expanded_hypothesis or current_hypothesis
            
            critic_state = build_critic_state(
                hypothesis_to_critique,
                planner_result.output,
                iteration,
                expanded_hypothesis
            )
            critic_result = await critic.run(critic_state)
            
            state.update_run(run_id, data={
                **state.get_run(run_id).data,
                f"critic_iteration_{iteration}": critic_result.__dict__
            })
            
            # HITL Checkpoint: Post-Critique
            if checkpoint_mgr and "post_critique" in active_hitl_stages:
                critic_result.output = await _handle_checkpoint(
                    checkpoint_mgr, run_id, CheckpointStage.POST_CRITIQUE,
                    critic_result.output,
                    f"Review critique (iteration {iteration})",
                    config.hitl_timeout
                )
            
            # Check if we should continue
            if not critic.should_continue_iteration(critic_result.output, config.max_iterations, iteration):
                logger.info(f"[{run_id}] Hypothesis approved or max iterations reached")
                break
            
            # Prepare for revision
            if iteration < config.max_iterations:
                revision_guidance = critic.get_revision_guidance(critic_result.output)
                
                # HITL Checkpoint: Pre-Revision
                if checkpoint_mgr and "pre_revision" in active_hitl_stages:
                    revision_guidance = await _handle_checkpoint(
                        checkpoint_mgr, run_id, CheckpointStage.PRE_REVISION,
                        revision_guidance,
                        "Review revision guidance before scientist revises",
                        config.hitl_timeout
                    )
                
                # Revise hypothesis
                scientist_state["revision_guidance"] = revision_guidance
                scientist_state["previous_hypothesis"] = current_hypothesis
                scientist_result = await scientist.run(scientist_state)
                current_hypothesis = scientist_result.output
                
                state.update_run(run_id, data={
                    **state.get_run(run_id).data,
                    f"scientist_revision_{iteration}": scientist_result.__dict__
                })
                
                # Re-expand if enabled
                if config.enable_scientist2 and "error" not in current_hypothesis:
                    scientist2_state["hypothesis"] = current_hypothesis
                    scientist2_result = await scientist2.run(scientist2_state)
                    if "error" not in scientist2_result.output:
                        expanded_hypothesis = scientist2_result.output
            
            iteration += 1
        
        # ============================================================
        # PHASE 6: FINAL ASSEMBLY
        # ============================================================
        logger.info(f"[{run_id}] Phase 6: Final Assembly")
        
        final_output = build_final_output(
            hypothesis=current_hypothesis,
            evaluation=critic_result.output if critic_result else {},
            planner_output=planner_result.output,
            iterations=iteration,
            expanded_hypothesis=expanded_hypothesis,
            ontologist_output=ontologist_output,
            literature_references=literature_refs
        )
        
        # HITL Checkpoint: Final Review
        if checkpoint_mgr and "final_review" in active_hitl_stages:
            final_output = await _handle_checkpoint(
                checkpoint_mgr, run_id, CheckpointStage.FINAL_REVIEW,
                final_output,
                "Final review before completing workflow",
                config.hitl_timeout
            )
            if final_output.get("_rejected"):
                state.update_run(run_id, status="CANCELLED")
                return {"error": "Workflow cancelled at final review", "reason": final_output.get("reason")}
        
        state.update_run(run_id, data={**state.get_run(run_id).data, "final_output": final_output})
        state.update_run(run_id, status="COMPLETED")
        
        logger.info(f"[{run_id}] Workflow completed successfully")
        
        return final_output
        
    except Exception as e:
        logger.error(f"[{run_id}] Workflow failed: {e}")
        state.update_run(run_id, status="FAILED", data={
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return {"error": str(e)}
    
    finally:
        # Cleanup checkpoints
        if checkpoint_mgr:
            checkpoint_mgr.cleanup_run(run_id)


async def _handle_checkpoint(
    checkpoint_mgr: CheckpointManager,
    run_id: str,
    stage: CheckpointStage,
    output: dict,
    summary: str,
    timeout: int
) -> dict:
    """Handle a HITL checkpoint.
    
    Args:
        checkpoint_mgr: Checkpoint manager
        run_id: Run ID
        stage: Checkpoint stage
        output: Agent output to review
        summary: Summary for human
        timeout: Timeout in seconds
        
    Returns:
        Potentially modified output
    """
    checkpoint = checkpoint_mgr.create_checkpoint(
        run_id=run_id,
        stage=stage,
        agent_output=output,
        summary=summary,
        timeout_seconds=timeout
    )
    
    logger.info(f"Checkpoint created: {checkpoint.id} at {stage.value}")
    
    result = await checkpoint_mgr.wait_for_resolution(checkpoint.id, timeout)
    
    if result.status in [CheckpointStatus.APPROVED, CheckpointStatus.SKIPPED, CheckpointStatus.TIMEOUT]:
        return output
    
    return checkpoint_mgr.apply_modifications(output, result)
