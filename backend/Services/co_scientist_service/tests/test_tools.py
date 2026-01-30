"""
Tests for Web Search Tools

Simplified tests focusing on core functionality.
Tests cover:
- Rate limiter functionality
- Tool initialization
- Tool registry functionality
"""

import asyncio
import pytest
import time

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.base_tool import RateLimiter, BaseTool, ToolResult
from tools.arxiv_tool import ArxivSearchTool
from tools.biorxiv_tool import BiorxivSearchTool
from tools.semantic_scholar_tool import SemanticScholarTool
from tools.tool_registry import ToolRegistry


# ============================================================================
# RATE LIMITER TESTS
# ============================================================================

class TestRateLimiter:
    """Tests for token bucket rate limiter."""
    
    def test_initialization(self):
        """Test rate limiter initializes correctly."""
        limiter = RateLimiter(requests_per_second=2.0, burst_size=5)
        assert limiter.rate == 2.0
        assert limiter.capacity == 5
        assert limiter.tokens == 5  # Starts full
    
    @pytest.mark.asyncio
    async def test_acquire_single_token(self):
        """Test acquiring a single token."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=10)
        
        # Should succeed immediately (return 0 wait time)
        wait_time = await limiter.acquire()
        assert wait_time == 0.0
        assert limiter.tokens == 9
    
    @pytest.mark.asyncio
    async def test_acquire_depletes_tokens(self):
        """Test that tokens get depleted."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=3)
        
        await limiter.acquire()  # tokens = 2
        await limiter.acquire()  # tokens = 1
        await limiter.acquire()  # tokens = 0
        
        # Next acquire should wait
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start
        
        # Should have waited some time
        assert elapsed > 0.05
    
    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self):
        """Test that tokens refill based on time passed."""
        limiter = RateLimiter(requests_per_second=100.0, burst_size=1)
        
        # Deplete tokens
        await limiter.acquire()
        
        # Wait for refill (15ms = 1.5 tokens at 100/sec)
        await asyncio.sleep(0.015)
        
        # Should be able to acquire immediately
        wait_time = await limiter.acquire()
        assert wait_time < 0.01  # Near-instant
    
    @pytest.mark.asyncio
    async def test_async_wait_multiple_acquires(self):
        """Test multiple consecutive acquires."""
        limiter = RateLimiter(requests_per_second=50.0, burst_size=2)
        
        # First two should be fast
        t1 = await limiter.acquire()
        t2 = await limiter.acquire()
        
        assert t1 == 0.0
        assert t2 == 0.0
        
        # Third should wait
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start
        
        # Should have waited ~20ms (1/50 seconds)
        assert elapsed >= 0.01


# ============================================================================
# TOOL RESULT TESTS
# ============================================================================

class TestToolResult:
    """Tests for ToolResult dataclass."""
    
    def test_success_result(self):
        """Test creating a success result."""
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            data={"key": "value"}
        )
        
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
    
    def test_error_result(self):
        """Test creating an error result."""
        result = ToolResult(
            tool_name="test_tool",
            success=False,
            data=None,
            error="Something went wrong"
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"
    
    def test_to_dict(self):
        """Test serialization to dict."""
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            data={"papers": []}
        )
        
        d = result.to_dict()
        assert "tool_name" in d
        assert "success" in d
        assert "data" in d
        assert "timestamp" in d


# ============================================================================
# TOOL INITIALIZATION TESTS
# ============================================================================

class TestToolInitialization:
    """Tests for tool initialization."""
    
    def test_arxiv_tool_init(self):
        """Test ArXiv tool initializes."""
        tool = ArxivSearchTool()
        assert tool is not None
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'search')
    
    def test_biorxiv_tool_init(self):
        """Test BioRxiv tool initializes."""
        tool = BiorxivSearchTool()
        assert tool is not None
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'search')
    
    def test_semantic_scholar_tool_init(self):
        """Test Semantic Scholar tool initializes."""
        tool = SemanticScholarTool()
        assert tool is not None
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'search')


# ============================================================================
# TOOL REGISTRY TESTS
# ============================================================================

class TestToolRegistry:
    """Tests for tool registry."""
    
    @pytest.fixture
    def registry(self):
        return ToolRegistry()
    
    def test_initialization(self, registry):
        """Test registry initializes correctly."""
        assert registry is not None
    
    def test_get_arxiv(self, registry):
        """Test getting ArXiv tool."""
        tool = registry.get_arxiv()
        assert tool is not None
        assert "arxiv" in tool.name.lower()
    
    def test_get_biorxiv(self, registry):
        """Test getting BioRxiv tool."""
        tool = registry.get_biorxiv()
        assert tool is not None
        assert "biorxiv" in tool.name.lower()
    
    def test_get_semantic_scholar(self, registry):
        """Test getting Semantic Scholar tool."""
        tool = registry.get_semantic_scholar()
        assert tool is not None
        assert "semantic" in tool.name.lower()
    
    def test_list_tools(self, registry):
        """Test listing all tools."""
        tools = registry.list_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 3  # At least arxiv, biorxiv, semantic_scholar


# ============================================================================
# INTEGRATION TESTS (require network - mark for selective running)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestToolsIntegration:
    """Integration tests that make real API calls.
    
    Run with: pytest -m integration
    """
    
    async def test_arxiv_real_search(self):
        """Test real ArXiv search."""
        tool = ArxivSearchTool()
        result = await tool.search("machine learning proteins", max_results=2)
        
        # ArXiv should generally work
        if result.success:
            assert isinstance(result.data, list)
    
    async def test_biorxiv_real_search(self):
        """Test real BioRxiv search."""
        tool = BiorxivSearchTool()
        result = await tool.search("CRISPR", max_results=2)
        
        # BioRxiv may have rate limits or be down
        # Just check result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])
