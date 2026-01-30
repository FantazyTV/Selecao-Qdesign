"""
Enhanced Workflow Configuration

Extended settings for the multi-agent workflow with HITL support.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .checkpoints import CheckpointStage


class HITLMode(str, Enum):
    """Human-in-the-loop modes."""
    DISABLED = "disabled"          # No checkpoints, fully automated
    CRITICAL_ONLY = "critical"     # Only at critical stages (post-hypothesis, final)
    FULL = "full"                  # Checkpoint at every stage
    CUSTOM = "custom"              # Custom checkpoint stages


@dataclass
class WorkflowConfig:
    """Enhanced configuration for the multi-agent workflow."""
    
    # Iteration settings
    max_iterations: int = 3
    min_approval_score: float = 7.0
    
    # Exploration settings  
    exploration_mode: str = "balanced"  # diverse, conservative, balanced, direct
    
    # Streaming
    streaming_enabled: bool = True
    
    # Human-in-the-loop settings
    hitl_mode: HITLMode = HITLMode.DISABLED
    hitl_stages: list[str] = field(default_factory=list)
    hitl_timeout: int = 300  # seconds
    
    # Agent settings
    enable_ontologist: bool = True
    enable_scientist2: bool = True
    enable_literature_search: bool = True
    
    # Novelty assessment
    enable_novelty_check: bool = False
    novelty_min_score: int = 5
    
    def get_active_hitl_stages(self) -> list[str]:
        """Get list of stages where HITL is active."""
        if self.hitl_mode == HITLMode.DISABLED:
            return []
        elif self.hitl_mode == HITLMode.CRITICAL_ONLY:
            return ["post_hypothesis", "final_review"]
        elif self.hitl_mode == HITLMode.FULL:
            return [
                "post_planning",
                "post_ontology",
                "post_hypothesis",
                "post_expansion",
                "post_critique",
                "final_review"
            ]
        else:  # CUSTOM
            return self.hitl_stages
    
    def should_checkpoint(self, stage) -> bool:
        """Check if a checkpoint should be created at the given stage.
        
        Args:
            stage: CheckpointStage enum value
            
        Returns:
            True if checkpoint should be created
        """
        active_stages = self.get_active_hitl_stages()
        # Handle both string and enum stage values
        stage_value = stage.value if hasattr(stage, 'value') else str(stage)
        return stage_value in active_stages


def build_planner_state(payload: dict, config: WorkflowConfig) -> dict:
    """Build the initial state for the Planner agent."""
    return {
        "kg_path": payload.get("kg_path"),
        "knowledge_graph": payload.get("knowledge_graph"),  # Direct KG data
        "query": payload.get("query", ""),
        "concept_a": payload.get("concept_a"),
        "concept_b": payload.get("concept_b"),
        "exploration_mode": config.exploration_mode,
        "max_paths": 3
    }


def build_ontologist_state(planner_output: dict, query: str) -> dict:
    """Build state for the Ontologist agent."""
    return {
        "planner_output": planner_output,
        "user_query": query
    }


def build_scientist_state(
    planner_output: dict,
    query: str,
    ontologist_output: Optional[dict] = None
) -> dict:
    """Build the initial state for the Scientist agent."""
    state = {
        "planner_output": planner_output,
        "user_query": query
    }
    if ontologist_output:
        state["ontologist_output"] = ontologist_output
    return state


def build_scientist2_state(
    hypothesis: dict,
    planner_output: dict,
    query: str,
    ontologist_output: Optional[dict] = None
) -> dict:
    """Build state for the Scientist2 agent."""
    state = {
        "hypothesis": hypothesis,
        "planner_output": planner_output,
        "user_query": query
    }
    if ontologist_output:
        state["ontologist_output"] = ontologist_output
    return state


def build_critic_state(
    hypothesis: dict,
    planner_output: dict,
    iteration: int,
    expanded_hypothesis: Optional[dict] = None
) -> dict:
    """Build the state for the Critic agent."""
    state = {
        "hypothesis": hypothesis,
        "planner_output": planner_output,
        "iteration": iteration
    }
    if expanded_hypothesis:
        state["expanded_hypothesis"] = expanded_hypothesis
    return state


def build_final_output(
    hypothesis: dict,
    evaluation: dict,
    planner_output: dict,
    iterations: int,
    expanded_hypothesis: Optional[dict] = None,
    ontologist_output: Optional[dict] = None,
    novelty_assessment: Optional[dict] = None,
    literature_references: Optional[list] = None
) -> dict:
    """Assemble the final workflow output with all components."""
    output = {
        "hypothesis": hypothesis,
        "evaluation": evaluation,
        "subgraph": planner_output.get("subgraph"),
        "natural_language_context": planner_output.get("natural_language_context"),
        "iterations_completed": iterations,
        "kg_metadata": planner_output.get("kg_metadata")
    }
    
    if expanded_hypothesis:
        output["expanded_hypothesis"] = expanded_hypothesis
    
    if ontologist_output:
        output["ontological_interpretation"] = ontologist_output
    
    if novelty_assessment:
        output["novelty_assessment"] = novelty_assessment
    
    if literature_references:
        output["literature_references"] = literature_references
    
    return output


# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

def default_config() -> WorkflowConfig:
    """Create a default configuration (no HITL, all agents enabled)."""
    return WorkflowConfig(
        hitl_mode=HITLMode.DISABLED,
        enable_ontologist=True,
        enable_scientist2=True,
        enable_literature_search=True
    )


def hitl_enabled_config(mode: HITLMode = HITLMode.CRITICAL_ONLY) -> WorkflowConfig:
    """Create a configuration with HITL enabled.
    
    Args:
        mode: HITL mode to use
        
    Returns:
        WorkflowConfig with HITL enabled
    """
    return WorkflowConfig(
        hitl_mode=mode,
        hitl_timeout=300,
        enable_ontologist=True,
        enable_scientist2=True,
        enable_literature_search=True
    )


def full_pipeline_config() -> WorkflowConfig:
    """Create a configuration with all features enabled including HITL."""
    return WorkflowConfig(
        hitl_mode=HITLMode.FULL,
        hitl_timeout=600,
        enable_ontologist=True,
        enable_scientist2=True,
        enable_literature_search=True,
        enable_novelty_check=True,
        max_iterations=5
    )


def lightweight_config() -> WorkflowConfig:
    """Create a lightweight configuration for fast execution."""
    return WorkflowConfig(
        hitl_mode=HITLMode.DISABLED,
        enable_ontologist=False,
        enable_scientist2=False,
        enable_literature_search=False,
        max_iterations=1
    )
