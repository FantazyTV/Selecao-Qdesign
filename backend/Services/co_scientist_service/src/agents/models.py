"""
Agent Data Models - Context and Input structures for agents.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PlannerContext:
    """Context extracted by planner for downstream agents."""
    subgraph_dict: dict
    natural_language_context: str
    path_strategy: str
    concepts_connected: tuple[str, str]
    main_objective: str


@dataclass
class ScientistInput:
    """Prepared input for Scientist LLM prompt."""
    main_objective: str
    secondary_objectives: list[str]
    user_query: str
    natural_language_context: str
    nodes: list[dict]
    edges: list[dict]
    primary_path: dict
    num_paths: int
    planner_rationale: list
    key_concepts: list
    graph_statistics: dict


@dataclass
class CriticInput:
    """Prepared input for Critic LLM prompt."""
    iteration: int
    main_objective: str
    hypothesis_title: str
    hypothesis_statement: str
    full_hypothesis: dict
    mechanism_steps: list
    num_mechanism_steps: int
    subgraph_nodes: list
    subgraph_edges: list
    nodes_cited: list
    edges_cited: list
    edge_confidence_distribution: dict
    proposed_validation: dict
    novelty_claims: dict
    comparison_claims: dict


@dataclass
class EvaluationResult:
    """Result from Critic evaluation."""
    decision: str  # APPROVE, REVISE, REJECT
    scores: dict
    strengths: list[dict]
    weaknesses: list[dict]
    required_revisions: list[str]
    improvement_suggestions: list[str]
    scientific_questions: list[str]
    computed_metrics: Optional[dict] = None
