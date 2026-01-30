"""
Co-Scientist Agent Package - SciAgents-inspired Implementation
"""

from .base_agent import BaseAgent, AgentResult
from .models import PlannerContext, ScientistInput, CriticInput, EvaluationResult
from .confidence import (
    calculate_planner_confidence,
    calculate_scientist_confidence,
    calculate_critic_confidence,
)
from .planner_agent import PlannerAgent
from .scientist_agent import ScientistAgent
from .critic_agent import CriticAgent
from .ontologist_agent import OntologistAgent
from .scientist2_agent import Scientist2Agent

__all__ = [
    # Base
    "BaseAgent",
    "AgentResult",
    # Models
    "PlannerContext",
    "ScientistInput",
    "CriticInput",
    "EvaluationResult",
    # Confidence
    "calculate_planner_confidence",
    "calculate_scientist_confidence",
    "calculate_critic_confidence",
    # Agents
    "PlannerAgent",
    "ScientistAgent",
    "CriticAgent",
    "OntologistAgent",
    "Scientist2Agent",
]
