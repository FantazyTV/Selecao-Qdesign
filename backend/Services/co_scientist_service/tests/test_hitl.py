"""
Tests for Human-in-the-Loop Checkpoint System

Tests cover:
- Checkpoint creation and management
- Checkpoint resolution (approve, modify, reject)
- Timeout handling
- HITL mode configuration
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os

# Add the src directory to path for direct module imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

# Import directly from modules to avoid __init__.py circular imports
import importlib.util

# Load checkpoints module directly
checkpoints_path = os.path.join(src_path, 'orchestration', 'checkpoints.py')
spec = importlib.util.spec_from_file_location("checkpoints", checkpoints_path)
checkpoints_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoints_module)

CheckpointManager = checkpoints_module.CheckpointManager
CheckpointStage = checkpoints_module.CheckpointStage
CheckpointStatus = checkpoints_module.CheckpointStatus
Checkpoint = checkpoints_module.Checkpoint
CheckpointData = checkpoints_module.CheckpointData
CheckpointResult = checkpoints_module.CheckpointResult

# Load enhanced_config module directly  
enhanced_config_path = os.path.join(src_path, 'orchestration', 'enhanced_config.py')
spec2 = importlib.util.spec_from_file_location("enhanced_config", enhanced_config_path)
enhanced_config_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(enhanced_config_module)

HITLMode = enhanced_config_module.HITLMode
WorkflowConfig = enhanced_config_module.WorkflowConfig


# ============================================================================
# CHECKPOINT MANAGER TESTS
# ============================================================================

class TestCheckpointManager:
    """Tests for CheckpointManager."""
    
    @pytest.fixture
    def manager(self):
        """Create fresh checkpoint manager for each test."""
        return CheckpointManager()
    
    def test_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager is not None
        assert len(manager._checkpoints) == 0
    
    def test_create_checkpoint(self, manager):
        """Test creating a new checkpoint."""
        checkpoint = manager.create_checkpoint(
            run_id="test_run_1",
            stage=CheckpointStage.POST_HYPOTHESIS,
            agent_output={"hypothesis": "Test hypothesis"},
            summary="Review generated hypothesis",
            timeout_seconds=300
        )
        
        assert checkpoint.id is not None
        assert checkpoint.run_id == "test_run_1"
        assert checkpoint.stage == CheckpointStage.POST_HYPOTHESIS
        assert checkpoint.status == CheckpointStatus.PENDING
        assert checkpoint.timeout_seconds == 300
    
    def test_get_checkpoint(self, manager):
        """Test retrieving checkpoint by ID."""
        checkpoint = manager.create_checkpoint(
            run_id="test_run_2",
            stage=CheckpointStage.POST_PLANNING,
            agent_output={"plan": "Test plan"},
            summary="Review plan"
        )
        
        retrieved = manager.get_checkpoint(checkpoint.id)
        
        assert retrieved is not None
        assert retrieved.id == checkpoint.id
    
    def test_get_nonexistent_checkpoint(self, manager):
        """Test getting non-existent checkpoint returns None."""
        result = manager.get_checkpoint("nonexistent_id")
        assert result is None
    
    def test_get_pending_checkpoints(self, manager):
        """Test filtering for pending checkpoints."""
        # Create mix of checkpoints
        cp1 = manager.create_checkpoint(
            run_id="run_1",
            stage=CheckpointStage.POST_PLANNING,
            agent_output={},
            summary="CP 1"
        )
        cp2 = manager.create_checkpoint(
            run_id="run_1",
            stage=CheckpointStage.POST_HYPOTHESIS,
            agent_output={},
            summary="CP 2"
        )
        
        # Resolve one
        manager.resolve_checkpoint(
            cp1.id,
            status=CheckpointStatus.APPROVED
        )
        
        pending = manager.get_pending_checkpoints()
        
        assert len(pending) == 1
        assert pending[0].id == cp2.id
    
    def test_get_pending_checkpoints_by_run(self, manager):
        """Test filtering pending checkpoints by run_id."""
        manager.create_checkpoint(
            run_id="run_A",
            stage=CheckpointStage.POST_PLANNING,
            agent_output={},
            summary="Run A checkpoint"
        )
        manager.create_checkpoint(
            run_id="run_B",
            stage=CheckpointStage.POST_PLANNING,
            agent_output={},
            summary="Run B checkpoint"
        )
        
        pending_a = manager.get_pending_checkpoints(run_id="run_A")
        pending_b = manager.get_pending_checkpoints(run_id="run_B")
        
        assert len(pending_a) == 1
        assert len(pending_b) == 1
        assert pending_a[0].run_id == "run_A"


# ============================================================================
# CHECKPOINT RESOLUTION TESTS
# ============================================================================

class TestCheckpointResolution:
    """Tests for checkpoint resolution."""
    
    @pytest.fixture
    def manager_with_checkpoint(self):
        """Create manager with a pending checkpoint."""
        manager = CheckpointManager()
        checkpoint = manager.create_checkpoint(
            run_id="test_run",
            stage=CheckpointStage.POST_HYPOTHESIS,
            agent_output={"hypothesis": "Original hypothesis"},
            summary="Review this hypothesis"
        )
        return manager, checkpoint
    
    def test_approve_checkpoint(self, manager_with_checkpoint):
        """Test approving a checkpoint."""
        manager, checkpoint = manager_with_checkpoint
        
        result = manager.resolve_checkpoint(
            checkpoint.id,
            status=CheckpointStatus.APPROVED
        )
        
        assert result.status == CheckpointStatus.APPROVED
        assert result.final_output == {"hypothesis": "Original hypothesis"}
        assert result.resolved_at is not None
    
    def test_modify_checkpoint(self, manager_with_checkpoint):
        """Test modifying checkpoint output."""
        manager, checkpoint = manager_with_checkpoint
        
        modifications = {"hypothesis": "Modified hypothesis", "added_field": "new value"}
        
        result = manager.resolve_checkpoint(
            checkpoint.id,
            status=CheckpointStatus.MODIFIED,
            modifications=modifications
        )
        
        assert result.status == CheckpointStatus.MODIFIED
        assert result.final_output["hypothesis"] == "Modified hypothesis"
        assert result.final_output["added_field"] == "new value"
    
    def test_override_checkpoint(self, manager_with_checkpoint):
        """Test completely overriding checkpoint output."""
        manager, checkpoint = manager_with_checkpoint
        
        override = {"completely": "different", "output": "structure"}
        
        result = manager.resolve_checkpoint(
            checkpoint.id,
            status=CheckpointStatus.MODIFIED,
            human_input=override
        )
        
        assert result.final_output == override
    
    def test_reject_checkpoint(self, manager_with_checkpoint):
        """Test rejecting a checkpoint."""
        manager, checkpoint = manager_with_checkpoint
        
        result = manager.resolve_checkpoint(
            checkpoint.id,
            status=CheckpointStatus.REJECTED,
            feedback="Hypothesis is not scientifically valid"
        )
        
        assert result.status == CheckpointStatus.REJECTED
        assert result.feedback == "Hypothesis is not scientifically valid"
    
    def test_cannot_resolve_already_resolved(self, manager_with_checkpoint):
        """Test that resolved checkpoints cannot be resolved again."""
        manager, checkpoint = manager_with_checkpoint
        
        # First resolution
        manager.resolve_checkpoint(checkpoint.id, status=CheckpointStatus.APPROVED)
        
        # Second resolution should fail or be ignored
        with pytest.raises((ValueError, Exception)):
            manager.resolve_checkpoint(checkpoint.id, status=CheckpointStatus.REJECTED)


# ============================================================================
# CHECKPOINT TIMEOUT TESTS
# ============================================================================

class TestCheckpointTimeout:
    """Tests for checkpoint timeout handling."""
    
    @pytest.fixture
    def manager(self):
        return CheckpointManager()
    
    def test_checkpoint_stores_timeout(self, manager):
        """Test checkpoint stores timeout value."""
        checkpoint = manager.create_checkpoint(
            run_id="test",
            stage=CheckpointStage.POST_CRITIQUE,
            agent_output={},
            summary="Test",
            timeout_seconds=600
        )
        
        assert checkpoint.timeout_seconds == 600
    
    def test_default_timeout(self, manager):
        """Test default timeout value."""
        checkpoint = manager.create_checkpoint(
            run_id="test",
            stage=CheckpointStage.POST_CRITIQUE,
            agent_output={},
            summary="Test"
        )
        
        # Default should be 300 seconds (5 minutes)
        assert checkpoint.timeout_seconds == 300
    
    @pytest.mark.asyncio
    async def test_wait_for_resolution_with_approval(self, manager):
        """Test async waiting for checkpoint resolution."""
        checkpoint = manager.create_checkpoint(
            run_id="test",
            stage=CheckpointStage.POST_HYPOTHESIS,
            agent_output={"data": "test"},
            summary="Test"
        )
        
        # Resolve in background after short delay
        async def resolve_later():
            await asyncio.sleep(0.1)
            manager.resolve_checkpoint(checkpoint.id, status=CheckpointStatus.APPROVED)
        
        asyncio.create_task(resolve_later())
        
        result = await manager.wait_for_resolution(checkpoint.id, timeout=5)
        
        assert result.status == CheckpointStatus.APPROVED
    
    @pytest.mark.asyncio
    async def test_wait_for_resolution_timeout(self, manager):
        """Test timeout while waiting for resolution."""
        checkpoint = manager.create_checkpoint(
            run_id="test",
            stage=CheckpointStage.POST_HYPOTHESIS,
            agent_output={},
            summary="Test"
        )
        
        # Don't resolve - let it timeout
        result = await manager.wait_for_resolution(checkpoint.id, timeout=0.1)
        
        assert result.status == CheckpointStatus.TIMEOUT


# ============================================================================
# HITL MODE CONFIGURATION TESTS
# ============================================================================

class TestHITLModeConfig:
    """Tests for HITL mode configuration."""
    
    def test_disabled_mode(self):
        """Test HITL disabled mode."""
        config = WorkflowConfig(hitl_mode=HITLMode.DISABLED)
        
        assert config.hitl_mode == HITLMode.DISABLED
        assert not config.should_checkpoint(CheckpointStage.POST_HYPOTHESIS)
    
    def test_critical_only_mode(self):
        """Test HITL critical-only mode."""
        config = WorkflowConfig(hitl_mode=HITLMode.CRITICAL_ONLY)
        
        # Should checkpoint at hypothesis and final stages
        assert config.should_checkpoint(CheckpointStage.POST_HYPOTHESIS)
        assert config.should_checkpoint(CheckpointStage.FINAL_REVIEW)
        
        # Should not checkpoint at other stages
        assert not config.should_checkpoint(CheckpointStage.POST_PLANNING)
    
    def test_full_mode(self):
        """Test HITL full mode."""
        config = WorkflowConfig(hitl_mode=HITLMode.FULL)
        
        # Should checkpoint at all stages
        assert config.should_checkpoint(CheckpointStage.POST_PLANNING)
        assert config.should_checkpoint(CheckpointStage.POST_ONTOLOGY)
        assert config.should_checkpoint(CheckpointStage.POST_HYPOTHESIS)
        assert config.should_checkpoint(CheckpointStage.POST_EXPANSION)
        assert config.should_checkpoint(CheckpointStage.POST_CRITIQUE)
        assert config.should_checkpoint(CheckpointStage.FINAL_REVIEW)
    
    def test_custom_mode(self):
        """Test HITL custom mode with specific stages."""
        config = WorkflowConfig(
            hitl_mode=HITLMode.CUSTOM,
            hitl_stages=["post_planning", "final_review"]
        )
        
        assert config.should_checkpoint(CheckpointStage.POST_PLANNING)
        assert config.should_checkpoint(CheckpointStage.FINAL_REVIEW)
        assert not config.should_checkpoint(CheckpointStage.POST_HYPOTHESIS)


# ============================================================================
# CHECKPOINT DATA SERIALIZATION TESTS
# ============================================================================

class TestCheckpointSerialization:
    """Tests for checkpoint serialization."""
    
    def test_checkpoint_to_dict(self):
        """Test checkpoint serialization to dict."""
        manager = CheckpointManager()
        checkpoint = manager.create_checkpoint(
            run_id="test",
            stage=CheckpointStage.POST_HYPOTHESIS,
            agent_output={"hypothesis": "Test"},
            summary="Review hypothesis",
            options=["approve", "modify", "reject"]
        )
        
        data = checkpoint.to_dict()
        
        assert "id" in data
        assert "run_id" in data
        assert data["stage"] == "post_hypothesis"
        assert data["status"] == "pending"
        assert "created_at" in data
    
    def test_checkpoint_result_to_dict(self):
        """Test checkpoint result serialization."""
        result = CheckpointResult(
            checkpoint_id="cp_123",
            status=CheckpointStatus.MODIFIED,
            final_output={"modified": "output"},
            feedback="Made some changes",
            resolved_at="2024-01-01T12:00:00Z"
        )
        
        data = result.to_dict()
        
        assert data["checkpoint_id"] == "cp_123"
        assert data["status"] == "modified"
        assert data["final_output"]["modified"] == "output"


# ============================================================================
# INTEGRATION WITH WORKFLOW TESTS
# ============================================================================

class TestHITLWorkflowIntegration:
    """Tests for HITL integration with workflow."""
    
    @pytest.mark.asyncio
    async def test_workflow_pauses_at_checkpoint(self):
        """Test that workflow pauses at checkpoint."""
        manager = CheckpointManager()
        
        # Simulate workflow creating checkpoint
        checkpoint = manager.create_checkpoint(
            run_id="workflow_1",
            stage=CheckpointStage.POST_HYPOTHESIS,
            agent_output={"hypothesis": "Generated hypothesis"},
            summary="Please review the hypothesis"
        )
        
        # Workflow should be waiting
        assert checkpoint.status == CheckpointStatus.PENDING
        
        # Human approves
        manager.resolve_checkpoint(checkpoint.id, status=CheckpointStatus.APPROVED)
        
        # Now workflow can continue
        updated = manager.get_checkpoint(checkpoint.id)
        assert updated.status == CheckpointStatus.APPROVED
    
    @pytest.mark.asyncio
    async def test_multiple_checkpoints_in_workflow(self):
        """Test workflow with multiple checkpoints."""
        manager = CheckpointManager()
        run_id = "multi_checkpoint_run"
        
        # Create checkpoints at different stages
        stages = [
            CheckpointStage.POST_PLANNING,
            CheckpointStage.POST_HYPOTHESIS,
            CheckpointStage.POST_CRITIQUE,
        ]
        
        checkpoints = []
        for stage in stages:
            cp = manager.create_checkpoint(
                run_id=run_id,
                stage=stage,
                agent_output={"stage": stage.value},
                summary=f"Review {stage.value}"
            )
            checkpoints.append(cp)
        
        # All should be pending
        pending = manager.get_pending_checkpoints(run_id)
        assert len(pending) == 3
        
        # Approve first one
        manager.resolve_checkpoint(checkpoints[0].id, status=CheckpointStatus.APPROVED)
        
        pending = manager.get_pending_checkpoints(run_id)
        assert len(pending) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
