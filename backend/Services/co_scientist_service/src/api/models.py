"""
API Request/Response Models - Enhanced Pydantic models with validation.

Provides comprehensive input validation and structured response formats.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# ENUMS
# ============================================================================

class ExplorationMode(str, Enum):
    """Path finding exploration modes."""
    DIVERSE = "diverse"
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    DIRECT = "direct"


class RunStatus(str, Enum):
    """Workflow run status values."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CriticDecision(str, Enum):
    """Critic agent decision values."""
    APPROVE = "APPROVE"
    REVISE = "REVISE"
    REJECT = "REJECT"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class RunRequest(BaseModel):
    """Request model for workflow execution."""
    project_description: Optional[str] = Field(
        None,
        description="Description of the research project"
    )
    concept_a: Optional[str] = Field(
        None,
        description="First concept/node ID to connect"
    )
    concept_b: Optional[str] = Field(
        None,
        description="Second concept/node ID to connect"
    )
    kg_path: Optional[str] = Field(
        None,
        description="Path to knowledge graph JSON file"
    )
    query: Optional[str] = Field(
        None,
        description="Research question or objective"
    )
    exploration_mode: ExplorationMode = Field(
        ExplorationMode.BALANCED,
        description="Path finding strategy to use"
    )
    max_iterations: int = Field(
        3,
        ge=1,
        le=10,
        description="Maximum critique-revise iterations"
    )
    
    @field_validator('max_iterations')
    @classmethod
    def validate_iterations(cls, v):
        if v < 1 or v > 10:
            raise ValueError('max_iterations must be between 1 and 10')
        return v


class V2RunRequest(BaseModel):
    """Request model for V2 workflow execution."""
    kg_path: str = Field(
        ...,
        description="Path to knowledge graph JSON file (required)"
    )
    query: Optional[str] = Field(
        None,
        description="Research question or objective"
    )
    concept_a: Optional[str] = Field(
        None,
        description="First concept/node ID to connect"
    )
    concept_b: Optional[str] = Field(
        None,
        description="Second concept/node ID to connect"
    )
    exploration_mode: ExplorationMode = Field(
        ExplorationMode.BALANCED,
        description="Path finding strategy"
    )
    max_iterations: int = Field(
        3,
        ge=1,
        le=10,
        description="Maximum critique-revise iterations"
    )
    min_approval_score: float = Field(
        7.0,
        ge=1.0,
        le=10.0,
        description="Minimum score for hypothesis approval"
    )
    
    @field_validator('kg_path')
    @classmethod
    def validate_kg_path(cls, v):
        if not v or not v.strip():
            raise ValueError('kg_path cannot be empty')
        return v.strip()


class FeedbackRequest(BaseModel):
    """Request model for user feedback on workflow runs."""
    run_id: str = Field(..., description="ID of the run to provide feedback for")
    stage: str = Field(..., description="Stage of the workflow (planner, scientist, critic)")
    action: str = Field(..., description="Feedback action (approve, revise, reject)")
    notes: Optional[str] = Field(None, description="Additional notes or comments")
    
    @field_validator('stage')
    @classmethod
    def validate_stage(cls, v):
        valid_stages = ['planner', 'scientist', 'critic', 'final']
        if v.lower() not in valid_stages:
            raise ValueError(f'stage must be one of: {", ".join(valid_stages)}')
        return v.lower()
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        valid_actions = ['approve', 'revise', 'reject', 'comment']
        if v.lower() not in valid_actions:
            raise ValueError(f'action must be one of: {", ".join(valid_actions)}')
        return v.lower()


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class RunResponse(BaseModel):
    """Response model for workflow execution."""
    run_id: str = Field(..., description="Unique identifier for this run")
    status: RunStatus = Field(..., description="Current status of the run")
    message: Optional[str] = Field(None, description="Status message")
    created_at: Optional[datetime] = Field(None, description="Run creation timestamp")


class StatusResponse(BaseModel):
    """Response model for run status queries."""
    run_id: str
    status: RunStatus
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    current_phase: Optional[str] = None
    iterations_completed: int = 0
    data: dict = Field(default_factory=dict)


class HypothesisResponse(BaseModel):
    """Response model for hypothesis retrieval."""
    run_id: str
    status: RunStatus
    hypothesis: Optional[dict] = None
    evaluation: Optional[dict] = None
    subgraph: Optional[dict] = None
    iterations: int = 0
    final_decision: Optional[CriticDecision] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# KNOWLEDGE GRAPH MODELS
# ============================================================================

class KGNodeResponse(BaseModel):
    """Response model for knowledge graph nodes."""
    id: str
    label: str
    type: str
    trust_level: float = 0.5
    biological_features: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class KGEdgeResponse(BaseModel):
    """Response model for knowledge graph edges."""
    id: Optional[str] = None
    source: str
    target: str
    label: str
    strength: float = 0.5
    correlation_type: str = ""
    explanation: str = ""


class KGLoadResponse(BaseModel):
    """Response model for knowledge graph loading."""
    loaded: bool
    statistics: dict = Field(default_factory=dict)
    hub_nodes: list[KGNodeResponse] = Field(default_factory=list)
    main_objective: Optional[str] = None
    secondary_objectives: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PathResponse(BaseModel):
    """Response model for path finding results."""
    source: str
    target: str
    path: list[str]
    path_length: int
    total_strength: float
    strategy: str
    nodes: list[KGNodeResponse] = Field(default_factory=list)
    edges: list[KGEdgeResponse] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class SubgraphResponse(BaseModel):
    """Response model for subgraph extraction."""
    nodes: list[KGNodeResponse]
    edges: list[KGEdgeResponse]
    statistics: dict = Field(default_factory=dict)
    natural_language: Optional[str] = None


# ============================================================================
# WORKFLOW OUTPUT MODELS
# ============================================================================

class PlannerOutput(BaseModel):
    """Structured planner agent output."""
    subgraph: SubgraphResponse
    natural_language_context: str
    path_strategy: str
    concepts_connected: dict
    kg_metadata: dict
    statistics: dict
    enriched_analysis: Optional[dict] = None


class ScientistOutput(BaseModel):
    """Structured scientist agent output (7-point framework)."""
    hypothesis: dict = Field(..., description="Hypothesis statement with title and description")
    expected_outcomes: dict = Field(..., description="Quantifiable predictions")
    mechanisms: dict = Field(..., description="Step-by-step mechanistic explanation")
    design_principles: dict = Field(..., description="Structural/functional principles")
    unexpected_properties: Optional[dict] = Field(None, description="Emergent behaviors")
    comparison: dict = Field(..., description="Comparison with existing knowledge")
    novelty: dict = Field(..., description="What is genuinely new")
    citations: Optional[dict] = Field(None, description="Evidence from knowledge graph")


class CriticOutput(BaseModel):
    """Structured critic agent output."""
    decision: CriticDecision
    scores: dict = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[dict] = Field(default_factory=list)
    required_revisions: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)
    overall_assessment: Optional[str] = None


class WorkflowOutput(BaseModel):
    """Complete workflow output model."""
    run_id: str
    status: RunStatus
    hypothesis: Optional[ScientistOutput] = None
    evaluation: Optional[CriticOutput] = None
    planner: Optional[PlannerOutput] = None
    iterations: int = 0
    total_duration_seconds: Optional[float] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============================================================================
# HEALTH & METRICS MODELS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    version: str = "2.0.0"
    uptime_seconds: float = 0.0
    components: dict = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    """Metrics summary response model."""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    active_runs: int = 0
    avg_duration_seconds: float = 0.0
    cache_hit_rate: float = 0.0
    llm_calls_total: int = 0
    uptime_seconds: float = 0.0
