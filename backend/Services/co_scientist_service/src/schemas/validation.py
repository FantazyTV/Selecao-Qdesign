"""
Response Validation Schemas for LLM Agents

Pydantic models to validate and parse LLM-generated responses.
Ensures agents return properly structured data.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class CriticDecision(str, Enum):
    """Critic agent decision types."""
    APPROVE = "APPROVE"
    REVISE = "REVISE"
    REJECT = "REJECT"


# ============================================================================
# Planner Agent Schemas
# ============================================================================

class PlannerPathInfo(BaseModel):
    """Information about a selected path in the knowledge graph."""
    source_node: str = Field(description="Starting node ID")
    target_node: str = Field(description="Target node ID")
    path_length: int = Field(ge=0, description="Number of nodes in path")
    path_nodes: List[str] = Field(description="List of node IDs in path")
    average_confidence: float = Field(ge=0, le=1, description="Average edge confidence")
    strategy_used: str = Field(description="Path finding strategy")


class PlannerSubgraphStats(BaseModel):
    """Statistics about the extracted subgraph."""
    total_nodes: int = Field(ge=0)
    total_edges: int = Field(ge=0)
    node_types: Dict[str, int] = Field(default_factory=dict)
    hub_nodes: List[str] = Field(default_factory=list)


class PlannerAnalysis(BaseModel):
    """LLM-generated analysis of the subgraph."""
    key_concepts: List[str] = Field(description="Important biological concepts")
    biological_context: str = Field(description="Natural language context")
    research_opportunities: List[str] = Field(default_factory=list)
    potential_mechanisms: List[str] = Field(default_factory=list)


class PlannerResponse(BaseModel):
    """Complete response from Planner Agent."""
    path_info: PlannerPathInfo
    subgraph_stats: PlannerSubgraphStats
    analysis: PlannerAnalysis
    rationale: str = Field(description="Why this path was selected")
    confidence: float = Field(ge=0, le=10, description="Planner confidence (0-10)")


# ============================================================================
# Scientist Agent Schemas (7-Point Framework)
# ============================================================================

class HypothesisStatement(BaseModel):
    """Main hypothesis statement."""
    statement: str = Field(description="Clear, testable hypothesis")
    scope: str = Field(description="Scope of applicability")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions")


class ExpectedOutcomes(BaseModel):
    """Quantifiable predictions."""
    primary_outcomes: List[str] = Field(description="Main expected results")
    measurable_metrics: List[str] = Field(description="How to measure outcomes")
    success_criteria: str = Field(description="What defines success")


class MechanisticExplanation(BaseModel):
    """Step-by-step mechanism."""
    overview: str = Field(description="High-level mechanistic overview")
    steps: List[str] = Field(description="Detailed mechanistic steps")
    key_interactions: List[str] = Field(description="Critical molecular interactions")
    intermediate_states: List[str] = Field(default_factory=list)


class DesignPrinciples(BaseModel):
    """Structural and functional design principles."""
    structural_features: List[str] = Field(description="Key structural elements")
    functional_principles: List[str] = Field(description="Functional design rules")
    evolutionary_context: Optional[str] = None


class UnexpectedProperties(BaseModel):
    """Emergent or non-obvious properties."""
    emergent_behaviors: List[str] = Field(description="Unexpected system behaviors")
    synergistic_effects: List[str] = Field(default_factory=list)
    counterintuitive_findings: List[str] = Field(default_factory=list)


class Comparison(BaseModel):
    """Comparison with existing knowledge."""
    differs_from: List[str] = Field(description="How it differs from current understanding")
    builds_upon: List[str] = Field(description="What existing knowledge it extends")
    contradicts: List[str] = Field(default_factory=list, description="Any contradictions")


class NoveltyAssessment(BaseModel):
    """What is genuinely new."""
    novel_aspects: List[str] = Field(description="Truly novel components")
    innovation_level: str = Field(description="Incremental, significant, or breakthrough")
    potential_impact: str = Field(description="Expected scientific impact")


class CitationsAndEvidence(BaseModel):
    """Supporting evidence and references."""
    graph_nodes_cited: List[str] = Field(description="KG nodes used as evidence")
    graph_edges_cited: List[str] = Field(default_factory=list)
    literature_references: List[str] = Field(default_factory=list)
    confidence_level: float = Field(ge=0, le=10, description="Overall confidence (0-10)")


class ScientistResponse(BaseModel):
    """Complete response from Scientist Agent (7-point framework)."""
    hypothesis: HypothesisStatement
    expected_outcomes: ExpectedOutcomes
    mechanisms: MechanisticExplanation
    design_principles: DesignPrinciples
    unexpected_properties: UnexpectedProperties
    comparison: Comparison
    novelty: NoveltyAssessment
    citations: CitationsAndEvidence
    
    # Metadata
    iteration: int = Field(ge=0, description="Which iteration this is")
    based_on_feedback: Optional[str] = None


# ============================================================================
# Critic Agent Schemas
# ============================================================================

class LogicalConsistency(BaseModel):
    """Evaluation of logical flow."""
    score: float = Field(ge=0, le=10)
    issues: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)


class EvidenceGrounding(BaseModel):
    """How well hypothesis is grounded in evidence."""
    score: float = Field(ge=0, le=10)
    well_supported: List[str] = Field(description="Well-supported claims")
    weakly_supported: List[str] = Field(description="Claims needing more evidence")
    missing_evidence: List[str] = Field(default_factory=list)


class MechanisticPlausibility(BaseModel):
    """Biological/chemical plausibility."""
    score: float = Field(ge=0, le=10)
    plausible_mechanisms: List[str] = Field(default_factory=list)
    questionable_mechanisms: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list, description="Known principle violations")


class NoveltyEvaluation(BaseModel):
    """Assessment of novelty."""
    score: float = Field(ge=0, le=10)
    truly_novel: List[str] = Field(description="Genuinely new ideas")
    incremental: List[str] = Field(description="Incremental advances")
    already_known: List[str] = Field(default_factory=list)


class FeasibilityCheck(BaseModel):
    """Practical feasibility."""
    score: float = Field(ge=0, le=10)
    testable_aspects: List[str] = Field(description="What can be tested")
    challenges: List[str] = Field(description="Experimental challenges")
    required_resources: List[str] = Field(default_factory=list)


class RevisionSuggestions(BaseModel):
    """Specific suggestions for improvement."""
    critical_issues: List[str] = Field(description="Must fix")
    improvements: List[str] = Field(description="Suggested enhancements")
    focus_areas: List[str] = Field(description="What to emphasize in revision")


class CriticResponse(BaseModel):
    """Complete response from Critic Agent."""
    decision: CriticDecision
    overall_score: float = Field(ge=0, le=10, description="Overall quality score")
    
    # Detailed evaluations
    logical_consistency: LogicalConsistency
    evidence_grounding: EvidenceGrounding
    mechanistic_plausibility: MechanisticPlausibility
    novelty_evaluation: NoveltyEvaluation
    feasibility: FeasibilityCheck
    
    # Feedback
    revision_suggestions: Optional[RevisionSuggestions] = None
    rejection_reasons: Optional[List[str]] = None
    approval_highlights: Optional[List[str]] = None
    
    # Summary
    summary: str = Field(description="Brief summary of evaluation")
    key_strengths: List[str] = Field(default_factory=list)
    key_weaknesses: List[str] = Field(default_factory=list)


# ============================================================================
# Validation Helpers
# ============================================================================

class ValidationResult(BaseModel):
    """Result of schema validation."""
    valid: bool
    data: Optional[Any] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def validate_agent_response(
    response_data: dict,
    agent_type: str
) -> ValidationResult:
    """
    Validate agent response against appropriate schema.
    
    Args:
        response_data: Raw response dictionary
        agent_type: "planner", "scientist", or "critic"
        
    Returns:
        ValidationResult with validated data or errors
    """
    schema_map = {
        "planner": PlannerResponse,
        "scientist": ScientistResponse,
        "critic": CriticResponse
    }
    
    if agent_type not in schema_map:
        return ValidationResult(
            valid=False,
            errors=[f"Unknown agent type: {agent_type}"]
        )
    
    schema_class = schema_map[agent_type]
    
    try:
        validated_data = schema_class(**response_data)
        return ValidationResult(valid=True, data=validated_data)
    except Exception as e:
        return ValidationResult(
            valid=False,
            errors=[f"Validation error: {str(e)}"],
            data=response_data  # Return raw data for inspection
        )
