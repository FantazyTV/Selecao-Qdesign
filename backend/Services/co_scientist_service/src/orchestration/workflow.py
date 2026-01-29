"""
SciAgents-inspired Workflow

Multi-agent scientific discovery workflow. Re-exports from split modules.
"""

from .config import WorkflowConfig
from .runner import run_workflow
from .streaming import run_workflow_streaming

# Aliases for backwards compatibility
run_workflow_v2 = run_workflow
run_workflow_v2_streaming = run_workflow_streaming

__all__ = [
    "WorkflowConfig",
    "run_workflow",
    "run_workflow_streaming",
    "run_workflow_v2",
    "run_workflow_v2_streaming",
]
