"""
State Manager - Enhanced workflow state management with persistence.

Features:
- In-memory state with optional disk persistence
- Run history tracking
- Audit logging
- State recovery after restart
"""

import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RunStatus(str, Enum):
    """Workflow run status values."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class AuditEntry:
    """Audit log entry for tracking state changes."""
    timestamp: str
    action: str
    agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "agent": self.agent,
            "details": self.details,
        }


@dataclass
class RunState:
    """Complete state for a workflow run."""
    run_id: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    data: dict = field(default_factory=dict)
    audit: list[dict] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    
    # Iteration tracking
    current_iteration: int = 0
    max_iterations: int = 3
    current_phase: str = "initialized"
    
    # Error tracking
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "data": self.data,
            "audit": self.audit,
            "config": self.config,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "current_phase": self.current_phase,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RunState":
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
            completed_at=data.get("completed_at"),
            data=data.get("data", {}),
            audit=data.get("audit", []),
            config=data.get("config", {}),
            current_iteration=data.get("current_iteration", 0),
            max_iterations=data.get("max_iterations", 3),
            current_phase=data.get("current_phase", "initialized"),
            error_message=data.get("error_message"),
            error_traceback=data.get("error_traceback"),
        )


class InMemoryStateManager:
    """
    Enhanced in-memory state manager with optional persistence.
    
    Features:
    - Thread-safe operations
    - Optional disk persistence for recovery
    - Run history with configurable retention
    - Detailed audit logging
    """
    
    def __init__(
        self,
        persist_path: Optional[Path] = None,
        max_history: int = 100,
        auto_persist: bool = False
    ):
        """
        Initialize state manager.
        
        Args:
            persist_path: Path for state persistence (optional)
            max_history: Maximum number of runs to keep in history
            auto_persist: Whether to auto-persist on every update
        """
        self._runs: Dict[str, RunState] = {}
        self._lock = threading.RLock()
        self._persist_path = persist_path
        self._max_history = max_history
        self._auto_persist = auto_persist
        
        # Load persisted state if available
        if persist_path and persist_path.exists():
            self._load_from_disk()

    def create_run(
        self,
        run_id: str,
        config: Optional[dict] = None
    ) -> RunState:
        """Create a new workflow run."""
        with self._lock:
            ts = datetime.now(timezone.utc).isoformat()
            state = RunState(
                run_id=run_id,
                status=RunStatus.CREATED.value,
                created_at=ts,
                updated_at=ts,
                config=config or {},
            )
            
            # Add creation audit entry
            state.audit.append(AuditEntry(
                timestamp=ts,
                action="created",
                details={"config": config}
            ).to_dict())
            
            self._runs[run_id] = state
            self._cleanup_old_runs()
            
            if self._auto_persist:
                self._persist_to_disk()
            
            logger.info(f"Created run: {run_id}")
            return state

    def get_run(self, run_id: str) -> Optional[RunState]:
        """Get a run by ID."""
        with self._lock:
            return self._runs.get(run_id)

    def update_run(
        self,
        run_id: str,
        status: Optional[str] = None,
        data: Optional[dict] = None,
        phase: Optional[str] = None,
        iteration: Optional[int] = None,
        error: Optional[str] = None,
        traceback: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Update a run's state.
        
        Args:
            run_id: Run identifier
            status: New status (optional)
            data: Data to merge into run data (optional)
            phase: Current workflow phase (optional)
            iteration: Current iteration number (optional)
            error: Error message if failed (optional)
            traceback: Error traceback if failed (optional)
        """
        with self._lock:
            state = self._runs.get(run_id)
            if not state:
                logger.warning(f"Run not found: {run_id}")
                return
            
            ts = datetime.now(timezone.utc).isoformat()
            state.updated_at = ts
            
            changes = {}
            
            if status:
                changes["status"] = {"from": state.status, "to": status}
                state.status = status
                
                if status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value):
                    state.completed_at = ts
            
            if data:
                state.data.update(data)
                changes["data_keys"] = list(data.keys())
            
            if phase:
                changes["phase"] = {"from": state.current_phase, "to": phase}
                state.current_phase = phase
            
            if iteration is not None:
                changes["iteration"] = iteration
                state.current_iteration = iteration
            
            if error:
                state.error_message = error
                changes["error"] = error
            
            if traceback:
                state.error_traceback = traceback
            
            # Handle additional kwargs
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            
            # Add audit entry
            if changes:
                state.audit.append(AuditEntry(
                    timestamp=ts,
                    action="updated",
                    details=changes
                ).to_dict())
            
            if self._auto_persist:
                self._persist_to_disk()

    def add_audit(
        self,
        run_id: str,
        action: str,
        agent: Optional[str] = None,
        details: Optional[dict] = None
    ) -> None:
        """Add an audit entry to a run."""
        with self._lock:
            state = self._runs.get(run_id)
            if not state:
                return
            
            state.audit.append(AuditEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                action=action,
                agent=agent,
                details=details,
            ).to_dict())
            
            if self._auto_persist:
                self._persist_to_disk()

    def list_runs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[RunState]:
        """
        List runs with optional filtering.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum runs to return
            offset: Number of runs to skip
        """
        with self._lock:
            runs = list(self._runs.values())
            
            if status:
                runs = [r for r in runs if r.status == status]
            
            # Sort by created_at descending
            runs.sort(key=lambda r: r.created_at, reverse=True)
            
            return runs[offset:offset + limit]

    def get_statistics(self) -> dict:
        """Get run statistics."""
        with self._lock:
            runs = list(self._runs.values())
            
            status_counts = {}
            for run in runs:
                status_counts[run.status] = status_counts.get(run.status, 0) + 1
            
            return {
                "total_runs": len(runs),
                "by_status": status_counts,
                "active_runs": sum(
                    1 for r in runs 
                    if r.status in (RunStatus.CREATED.value, RunStatus.RUNNING.value)
                ),
            }

    def delete_run(self, run_id: str) -> bool:
        """Delete a run from state."""
        with self._lock:
            if run_id in self._runs:
                del self._runs[run_id]
                
                if self._auto_persist:
                    self._persist_to_disk()
                
                logger.info(f"Deleted run: {run_id}")
                return True
            return False

    def persist(self) -> None:
        """Manually persist state to disk."""
        self._persist_to_disk()

    def _persist_to_disk(self) -> None:
        """Save current state to disk."""
        if not self._persist_path:
            return
        
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": "2.0",
                "persisted_at": datetime.now(timezone.utc).isoformat(),
                "runs": {
                    run_id: state.to_dict()
                    for run_id, state in self._runs.items()
                }
            }
            
            with open(self._persist_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Persisted {len(self._runs)} runs to disk")
        except Exception as e:
            logger.error(f"Failed to persist state: {e}")

    def _load_from_disk(self) -> None:
        """Load state from disk."""
        try:
            with open(self._persist_path, "r") as f:
                data = json.load(f)
            
            for run_id, run_data in data.get("runs", {}).items():
                self._runs[run_id] = RunState.from_dict(run_data)
            
            logger.info(f"Loaded {len(self._runs)} runs from disk")
        except Exception as e:
            logger.error(f"Failed to load persisted state: {e}")

    def _cleanup_old_runs(self) -> None:
        """Remove old runs if over the limit."""
        if len(self._runs) <= self._max_history:
            return
        
        # Sort runs by created_at
        sorted_runs = sorted(
            self._runs.items(),
            key=lambda x: x[1].created_at
        )
        
        # Remove oldest completed/failed runs
        to_remove = len(self._runs) - self._max_history
        removed = 0
        
        for run_id, state in sorted_runs:
            if removed >= to_remove:
                break
            if state.status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value):
                del self._runs[run_id]
                removed += 1
                logger.debug(f"Cleaned up old run: {run_id}")


# Global instance for backward compatibility
_global_state_manager: Optional[InMemoryStateManager] = None


def get_state_manager(
    persist_path: Optional[Path] = None,
    auto_persist: bool = False
) -> InMemoryStateManager:
    """Get or create the global state manager."""
    global _global_state_manager
    
    if _global_state_manager is None:
        _global_state_manager = InMemoryStateManager(
            persist_path=persist_path,
            auto_persist=auto_persist
        )
    
    return _global_state_manager
