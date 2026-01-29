"""
Workflow Configuration - Settings for the SciAgents workflow.
"""

from dataclasses import dataclass


@dataclass
class WorkflowConfig:
    """Configuration for the SciAgents workflow."""
    max_iterations: int = 3
    exploration_mode: str = "balanced"  # diverse, conservative, balanced, direct
    streaming_enabled: bool = True
    min_approval_score: float = 7.0


def build_planner_state(payload: dict, config: WorkflowConfig) -> dict:
    """Build the initial state for the Planner agent."""
    return {
        "kg_path": payload.get("kg_path"),
        "query": payload.get("query", ""),
        "concept_a": payload.get("concept_a"),
        "concept_b": payload.get("concept_b"),
        "exploration_mode": config.exploration_mode,
        "max_paths": 3
    }


def build_scientist_state(planner_output: dict, query: str) -> dict:
    """Build the initial state for the Scientist agent."""
    return {
        "planner_output": planner_output,
        "user_query": query
    }


def build_critic_state(hypothesis: dict, planner_output: dict, iteration: int) -> dict:
    """Build the state for the Critic agent."""
    return {
        "hypothesis": hypothesis,
        "planner_output": planner_output,
        "iteration": iteration
    }


def build_final_output(hypothesis: dict, evaluation: dict, planner_output: dict, iterations: int) -> dict:
    """Assemble the final workflow output."""
    return {
        "hypothesis": hypothesis,
        "evaluation": evaluation,
        "subgraph": planner_output.get("subgraph"),
        "natural_language_context": planner_output.get("natural_language_context"),
        "iterations_completed": iterations,
        "kg_metadata": planner_output.get("kg_metadata")
    }
