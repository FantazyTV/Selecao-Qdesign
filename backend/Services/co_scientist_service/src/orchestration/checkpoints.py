"""
Human-in-the-Loop (HITL) Checkpoint System

Provides infrastructure for human intervention at key workflow stages.
Allows users to:
- Review and approve/modify agent outputs
- Inject guidance or constraints
- Override agent decisions
- Pause and resume workflows
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional, Awaitable
import uuid

logger = logging.getLogger(__name__)


class CheckpointStage(str, Enum):
    """Stages where checkpoints can occur."""
    POST_PLANNING = "post_planning"
    POST_ONTOLOGY = "post_ontology"
    POST_HYPOTHESIS = "post_hypothesis"
    POST_EXPANSION = "post_expansion"
    POST_CRITIQUE = "post_critique"
    PRE_REVISION = "pre_revision"
    FINAL_REVIEW = "final_review"


class CheckpointStatus(str, Enum):
    """Status of a checkpoint."""
    PENDING = "pending"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class CheckpointData:
    """Data associated with a checkpoint."""
    stage: CheckpointStage
    agent_output: dict
    summary: str
    options: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class CheckpointResult:
    """Result of checkpoint resolution."""
    checkpoint_id: str = ""
    status: CheckpointStatus = CheckpointStatus.PENDING
    final_output: Optional[dict] = None
    human_input: Optional[dict] = None
    modifications: Optional[dict] = None
    feedback: Optional[str] = None
    resolved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "status": self.status.value,
            "final_output": self.final_output,
            "human_input": self.human_input,
            "modifications": self.modifications,
            "feedback": self.feedback,
            "resolved_at": self.resolved_at
        }


@dataclass
class Checkpoint:
    """Represents a workflow checkpoint awaiting human review."""
    id: str
    run_id: str
    stage: CheckpointStage
    data: CheckpointData
    status: CheckpointStatus = CheckpointStatus.PENDING
    result: Optional[CheckpointResult] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timeout_seconds: int = 300  # 5 minute default timeout
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "stage": self.stage.value,
            "status": self.status.value,
            "data": {
                "stage": self.data.stage.value,
                "summary": self.data.summary,
                "options": self.data.options,
                "metadata": self.data.metadata,
                # Include truncated output for preview
                "output_preview": self._truncate_output(self.data.agent_output)
            },
            "result": self.result.__dict__ if self.result else None,
            "created_at": self.created_at,
            "timeout_seconds": self.timeout_seconds
        }
    
    def _truncate_output(self, output: dict, max_length: int = 500) -> dict:
        """Truncate output for preview."""
        preview = {}
        for key, value in output.items():
            if isinstance(value, str) and len(value) > max_length:
                preview[key] = value[:max_length] + "..."
            elif isinstance(value, dict):
                preview[key] = self._truncate_output(value, max_length)
            else:
                preview[key] = value
        return preview


class CheckpointManager:
    """Manages checkpoints for human-in-the-loop workflows.
    
    Handles:
    - Creating checkpoints at workflow stages
    - Waiting for human resolution
    - Applying human modifications
    - Timeout handling
    """
    
    def __init__(self, default_timeout: int = 300):
        """Initialize checkpoint manager.
        
        Args:
            default_timeout: Default timeout in seconds for checkpoints
        """
        self.default_timeout = default_timeout
        self._checkpoints: dict[str, Checkpoint] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._callbacks: dict[CheckpointStage, list[Callable]] = {}
    
    def create_checkpoint(
        self,
        run_id: str,
        stage: CheckpointStage,
        agent_output: dict,
        summary: str,
        options: Optional[list[str]] = None,
        timeout_seconds: Optional[int] = None,
        metadata: Optional[dict] = None
    ) -> Checkpoint:
        """Create a new checkpoint.
        
        Args:
            run_id: Workflow run ID
            stage: Checkpoint stage
            agent_output: Output from the agent
            summary: Human-readable summary
            options: Available options for user
            timeout_seconds: Custom timeout
            metadata: Additional metadata
            
        Returns:
            Created Checkpoint object
        """
        checkpoint_id = f"cp_{uuid.uuid4().hex[:12]}"
        
        data = CheckpointData(
            stage=stage,
            agent_output=agent_output,
            summary=summary,
            options=options or ["approve", "modify", "reject"],
            metadata=metadata or {}
        )
        
        checkpoint = Checkpoint(
            id=checkpoint_id,
            run_id=run_id,
            stage=stage,
            data=data,
            timeout_seconds=timeout_seconds or self.default_timeout
        )
        
        self._checkpoints[checkpoint_id] = checkpoint
        self._events[checkpoint_id] = asyncio.Event()
        
        logger.info(f"Created checkpoint {checkpoint_id} at stage {stage.value} for run {run_id}")
        
        return checkpoint
    
    async def wait_for_resolution(
        self,
        checkpoint_id: str,
        timeout: Optional[int] = None
    ) -> CheckpointResult:
        """Wait for checkpoint to be resolved by human.
        
        Args:
            checkpoint_id: ID of the checkpoint
            timeout: Custom timeout (overrides checkpoint timeout)
            
        Returns:
            CheckpointResult with human input
            
        Raises:
            TimeoutError: If checkpoint times out
            KeyError: If checkpoint not found
        """
        if checkpoint_id not in self._checkpoints:
            raise KeyError(f"Checkpoint {checkpoint_id} not found")
        
        checkpoint = self._checkpoints[checkpoint_id]
        event = self._events[checkpoint_id]
        timeout = timeout or checkpoint.timeout_seconds
        
        logger.info(f"Waiting for resolution of checkpoint {checkpoint_id} (timeout: {timeout}s)")
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Checkpoint {checkpoint_id} timed out")
            checkpoint.status = CheckpointStatus.TIMEOUT
            checkpoint.result = CheckpointResult(
                checkpoint_id=checkpoint_id,
                status=CheckpointStatus.TIMEOUT,
                final_output=checkpoint.data.agent_output,
                feedback="Checkpoint timed out without human response"
            )
            return checkpoint.result
        
        return checkpoint.result
    
    def resolve_checkpoint(
        self,
        checkpoint_id: str,
        status: CheckpointStatus,
        human_input: Optional[dict] = None,
        modifications: Optional[dict] = None,
        feedback: Optional[str] = None
    ) -> CheckpointResult:
        """Resolve a checkpoint with human input.
        
        Args:
            checkpoint_id: ID of the checkpoint
            status: Resolution status
            human_input: Direct human input/override
            modifications: Modifications to agent output
            feedback: Human feedback/notes
            
        Returns:
            CheckpointResult
            
        Raises:
            KeyError: If checkpoint not found
            ValueError: If checkpoint already resolved
        """
        if checkpoint_id not in self._checkpoints:
            raise KeyError(f"Checkpoint {checkpoint_id} not found")
        
        checkpoint = self._checkpoints[checkpoint_id]
        
        if checkpoint.status != CheckpointStatus.PENDING:
            raise ValueError(f"Checkpoint {checkpoint_id} already resolved: {checkpoint.status}")
        
        # Determine final output based on resolution type
        original_output = checkpoint.data.agent_output
        if human_input:
            # Complete override
            final_output = human_input
        elif modifications:
            # Merge modifications
            final_output = self._deep_merge(original_output, modifications)
        else:
            # Use original output
            final_output = original_output
        
        result = CheckpointResult(
            checkpoint_id=checkpoint_id,
            status=status,
            final_output=final_output,
            human_input=human_input,
            modifications=modifications,
            feedback=feedback
        )
        
        checkpoint.status = status
        checkpoint.result = result
        
        # Signal waiting coroutine
        if checkpoint_id in self._events:
            self._events[checkpoint_id].set()
        
        logger.info(f"Resolved checkpoint {checkpoint_id} with status {status.value}")
        
        return result
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a checkpoint by ID."""
        return self._checkpoints.get(checkpoint_id)
    
    def get_pending_checkpoints(self, run_id: Optional[str] = None) -> list[Checkpoint]:
        """Get all pending checkpoints, optionally filtered by run_id."""
        checkpoints = [
            cp for cp in self._checkpoints.values()
            if cp.status == CheckpointStatus.PENDING
        ]
        if run_id:
            checkpoints = [cp for cp in checkpoints if cp.run_id == run_id]
        return checkpoints
    
    def get_checkpoints_for_run(self, run_id: str) -> list[Checkpoint]:
        """Get all checkpoints for a workflow run."""
        return [cp for cp in self._checkpoints.values() if cp.run_id == run_id]
    
    def skip_checkpoint(self, checkpoint_id: str) -> None:
        """Skip a checkpoint (auto-approve with no modifications)."""
        self.resolve_checkpoint(
            checkpoint_id,
            status=CheckpointStatus.SKIPPED,
            feedback="Checkpoint skipped"
        )
    
    def apply_modifications(
        self,
        original_output: dict,
        result: CheckpointResult
    ) -> dict:
        """Apply human modifications to agent output.
        
        Args:
            original_output: Original agent output
            result: Checkpoint result with modifications
            
        Returns:
            Modified output
        """
        if result.status == CheckpointStatus.REJECTED:
            # Return rejection marker
            return {"_rejected": True, "reason": result.feedback}
        
        if result.human_input:
            # Full override with human input
            return result.human_input
        
        if result.modifications:
            # Merge modifications into original
            return self._deep_merge(original_output, result.modifications)
        
        # No modifications, return original
        return original_output
    
    def _deep_merge(self, base: dict, updates: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def cleanup_run(self, run_id: str) -> None:
        """Clean up all checkpoints for a completed run."""
        checkpoint_ids = [
            cp.id for cp in self._checkpoints.values()
            if cp.run_id == run_id
        ]
        for cp_id in checkpoint_ids:
            if cp_id in self._events:
                del self._events[cp_id]
            del self._checkpoints[cp_id]
        logger.info(f"Cleaned up {len(checkpoint_ids)} checkpoints for run {run_id}")


# Global checkpoint manager instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Get or create the global checkpoint manager."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
