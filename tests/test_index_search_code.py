"""
Tests for index_code and search_code tools.

Tests the IndexCodeTool and SearchCodeTool classes.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools import IndexCodeTool, SearchCodeTool


class TestIndexCodeTool:
    """Test suite for IndexCodeTool."""

    @pytest.fixture
    def tool(self):
        """Create IndexCodeTool instance."""
        return IndexCodeTool()

    def test_get_name(self, tool):
        """Test tool name."""
        assert tool.get_name() == "index_code"

    def test_get_description(self, tool):
        """Test tool description."""
        desc = tool.get_description()
        assert "index" in desc.lower()
        assert "semantic search" in desc.lower()

    def test_requires_model(self, tool):
        """Test that this tool does not require a model."""
        assert tool.requires_model() is False

    def test_get_input_schema(self, tool):
        """Test input schema structure."""
        schema = tool.get_input_schema()
        
        assert schema["type"] == "object"
        assert "path" in schema["properties"]
        assert "extensions" in schema["properties"]
        assert "force" in schema["properties"]
        assert "chunk_size" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_invalid_path(self, tool):
        """Test execution with invalid path."""
        result = await tool.execute({"path": "/nonexistent/path/xyz123"})
        
        assert len(result) == 1
        assert "not exist" in result[0].text.lower() or "error" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_execute_with_temp_directory(self, tool):
        """Test execution with a real temporary directory."""
        # Create temp directory with some Python files
        temp_dir = tempfile.mkdtemp()
        try:
            # Create test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def hello():\n    print('Hello')\n")
            
            # Mock vector store to avoid actual indexing
            with patch("utils.vector_store.get_vector_store") as mock_get_store:
                mock_store = MagicMock()
                mock_store.add_chunks.return_value = 1
                mock_store.get_stats.return_value = {"total_chunks": 1}
                mock_get_store.return_value = mock_store
                
                result = await tool.execute({
                    "path": temp_dir,
                    "extensions": [".py"],
                })
                
                assert len(result) == 1
                # Should report success
                text = result[0].text
                assert "indexed" in text.lower() or "chunk" in text.lower()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestSearchCodeTool:
    """Test suite for SearchCodeTool."""

    @pytest.fixture
    def tool(self):
        """Create SearchCodeTool instance."""
        return SearchCodeTool()

    def test_get_name(self, tool):
        """Test tool name."""
        assert tool.get_name() == "search_code"

    def test_get_description(self, tool):
        """Test tool description."""
        desc = tool.get_description()
        assert "search" in desc.lower()

    def test_requires_model(self, tool):
        """Test that this tool does not require a model."""
        assert tool.requires_model() is False

    def test_get_input_schema(self, tool):
        """Test input schema structure."""
        schema = tool.get_input_schema()
        
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "min_score" in schema["properties"]
        assert "query" in schema.get("required", [])

    @pytest.mark.asyncio
    async def test_execute_empty_query(self, tool):
        """Test execution with empty query."""
        result = await tool.execute({"query": ""})
        
        assert len(result) == 1
        assert "provide" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_execute_no_index(self, tool):
        """Test execution when no index exists."""
        with patch("utils.vector_store.get_vector_store") as mock_get_store:
            mock_store = MagicMock()
            mock_store.get_stats.return_value = {"total_chunks": 0}
            mock_get_store.return_value = mock_store
            
            result = await tool.execute({"query": "test query"})
            
            assert len(result) == 1
            assert "no code has been indexed" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_execute_with_results(self, tool):
        """Test execution with search results."""
        with patch("utils.vector_store.get_vector_store") as mock_get_store:
            mock_store = MagicMock()
            mock_store.get_stats.return_value = {"total_chunks": 10}
            mock_store.search.return_value = [
                {
                    "file_path": "/test/auth.py",
                    "start_line": 1,
                    "end_line": 5,
                    "score": 0.85,
                    "content": "def authenticate(): pass",
                }
            ]
            mock_get_store.return_value = mock_store
            
            result = await tool.execute({"query": "authentication"})
            
            assert len(result) == 1
            text = result[0].text
            assert "auth.py" in text
            assert "0.85" in text or "85" in text

    @pytest.mark.asyncio
    async def test_execute_no_results(self, tool):
        """Test execution with no matching results."""
        with patch("utils.vector_store.get_vector_store") as mock_get_store:
            mock_store = MagicMock()
            mock_store.get_stats.return_value = {"total_chunks": 10}
            mock_store.search.return_value = []
            mock_get_store.return_value = mock_store
            
            result = await tool.execute({"query": "nonexistent function xyz"})
            
            assert len(result) == 1
            assert "no results" in result[0].text.lower()


class TestUsageTracker:
    """Test suite for UsageTracker."""

    def test_tracker_singleton(self):
        """Test that tracker is a singleton."""
        from utils.usage_tracker import get_usage_tracker
        
        tracker1 = get_usage_tracker()
        tracker2 = get_usage_tracker()
        
        assert tracker1 is tracker2

    def test_track_usage(self):
        """Test tracking usage."""
        from utils.usage_tracker import get_usage_tracker, track_usage
        
        tracker = get_usage_tracker()
        
        # Track a test usage
        track_usage(
            tool="test_tool",
            provider="test_provider",
            model="test_model",
            input_tokens=100,
            output_tokens=50,
            duration_ms=500,
        )
        
        # Get stats
        stats = tracker.get_stats(days=1)
        
        assert stats["total_requests"] >= 1
        assert stats["total_input_tokens"] >= 100
        assert stats["total_output_tokens"] >= 50


class TestProviderManager:
    """Test suite for ProviderManager."""

    def test_manager_singleton(self):
        """Test that manager is a singleton."""
        from utils.provider_manager import get_provider_manager
        
        manager1 = get_provider_manager()
        manager2 = get_provider_manager()
        
        assert manager1 is manager2

    def test_get_configured_providers(self):
        """Test getting configured providers."""
        from utils.provider_manager import get_provider_manager
        
        manager = get_provider_manager()
        providers = manager.get_configured_providers()
        
        # CLI should always be available
        assert "cli" in providers

    def test_is_provider_configured(self):
        """Test checking if provider is configured."""
        from utils.provider_manager import get_provider_manager
        
        manager = get_provider_manager()
        
        # CLI should always be configured
        assert manager.is_provider_configured("cli") is True

    def test_get_preferred_provider(self):
        """Test getting preferred provider."""
        from utils.provider_manager import get_provider_manager
        
        manager = get_provider_manager()
        preferred = manager.get_preferred_provider()
        
        # Should return something (at least CLI)
        assert preferred is not None
