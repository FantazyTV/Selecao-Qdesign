"""
Co-Scientist Orchestration Package

Provides workflow orchestration for multi-agent scientific discovery.
"""

from .state_manager import InMemoryStateManager
from .config import WorkflowConfig
from .runner import run_workflow
from .streaming import run_workflow_streaming

# Enhanced workflow components
from .enhanced_config import (
    WorkflowConfig as EnhancedWorkflowConfig,
    HITLMode,
    default_config,
    hitl_enabled_config,
    full_pipeline_config,
    lightweight_config,
)
from .enhanced_runner import run_enhanced_workflow
from .checkpoints import (
    CheckpointManager,
    CheckpointStage,
    CheckpointStatus,
    Checkpoint,
    CheckpointData,
    CheckpointResult,
    get_checkpoint_manager,
)

# Aliases for backwards compatibility
run_workflow_v2 = run_workflow
run_workflow_v2_streaming = run_workflow_streaming

__all__ = [
    # Core
    "InMemoryStateManager",
    "WorkflowConfig",
    "run_workflow",
    "run_workflow_streaming",
    "run_workflow_v2",
    "run_workflow_v2_streaming",
    # Enhanced
    "EnhancedWorkflowConfig",
    "HITLMode",
    "default_config",
    "hitl_enabled_config",
    "full_pipeline_config",
    "lightweight_config",
    "run_enhanced_workflow",
    # Checkpoints
    "CheckpointManager",
    "CheckpointStage",
    "CheckpointStatus",
    "Checkpoint",
    "CheckpointData",
    "CheckpointResult",
    "get_checkpoint_manager",
]
