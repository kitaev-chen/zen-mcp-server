"""
Tests for vector store functionality.

Tests the VectorStore class including add, search, and delete operations.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest


class TestVectorStore:
    """Test suite for VectorStore."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary directory for test database."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def vector_store(self, temp_db_path):
        """Create a VectorStore instance with temp path."""
        try:
            from utils.vector_store import VectorStore
            store = VectorStore(db_path=temp_db_path)
            # Test if chromadb embedding works by adding a test chunk
            store.add_chunks("/test/init.py", [{"content": "test", "start_line": 1, "end_line": 1}])
            store.clear()
            return store
        except ImportError:
            pytest.skip("chromadb not installed")
        except Exception as e:
            if "tokenizer" in str(e).lower() or "module" in str(e).lower():
                pytest.skip(f"chromadb dependencies issue: {e}")
            raise

    def test_add_chunks(self, vector_store):
        """Test adding chunks to the store."""
        chunks1 = [
            {
                "content": "def hello_world():\n    print('Hello, World!')",
                "start_line": 1,
                "end_line": 2,
            },
        ]
        chunks2 = [
            {
                "content": "def goodbye():\n    print('Goodbye!')",
                "start_line": 1,
                "end_line": 2,
            },
        ]
        
        added1 = vector_store.add_chunks("/test/hello.py", chunks1)
        added2 = vector_store.add_chunks("/test/goodbye.py", chunks2)
        assert added1 == 1
        assert added2 == 1
        
        stats = vector_store.get_stats()
        assert stats["total_chunks"] == 2

    def test_search(self, vector_store):
        """Test searching for chunks."""
        auth_chunks = [
            {
                "content": "def authenticate_user(username, password):\n    # Check credentials",
                "start_line": 1,
                "end_line": 2,
            },
        ]
        math_chunks = [
            {
                "content": "def calculate_sum(a, b):\n    return a + b",
                "start_line": 1,
                "end_line": 2,
            },
        ]
        
        vector_store.add_chunks("/test/auth.py", auth_chunks)
        vector_store.add_chunks("/test/math.py", math_chunks)
        
        # Search for authentication-related code
        results = vector_store.search("user authentication login", limit=5)
        
        assert len(results) > 0
        # The auth.py file should be more relevant
        assert any("/test/auth.py" in r["file_path"] for r in results)

    def test_delete_file(self, vector_store):
        """Test deleting chunks for a specific file."""
        file1_chunks = [
            {
                "content": "def func1(): pass",
                "start_line": 1,
                "end_line": 1,
            },
            {
                "content": "def func2(): pass",
                "start_line": 3,
                "end_line": 3,
            },
        ]
        file2_chunks = [
            {
                "content": "def func3(): pass",
                "start_line": 1,
                "end_line": 1,
            },
        ]
        
        vector_store.add_chunks("/test/file1.py", file1_chunks)
        vector_store.add_chunks("/test/file2.py", file2_chunks)
        
        # Verify initial state
        stats = vector_store.get_stats()
        assert stats["total_chunks"] == 3
        
        # Delete file1.py chunks
        deleted = vector_store.delete_file("/test/file1.py")
        assert deleted == 2
        
        # Verify only file2.py chunks remain
        stats = vector_store.get_stats()
        assert stats["total_chunks"] == 1

    def test_clear(self, vector_store):
        """Test clearing all chunks."""
        chunks = [
            {
                "content": "some code",
                "start_line": 1,
                "end_line": 1,
            },
        ]
        
        vector_store.add_chunks("/test/file.py", chunks)
        assert vector_store.get_stats()["total_chunks"] == 1
        
        vector_store.clear()
        assert vector_store.get_stats()["total_chunks"] == 0

    def test_get_stats(self, vector_store):
        """Test getting store statistics."""
        stats = vector_store.get_stats()
        
        assert "total_chunks" in stats
        assert stats["total_chunks"] == 0

    def test_empty_search(self, vector_store):
        """Test searching empty store."""
        results = vector_store.search("anything")
        assert results == []

    def test_duplicate_handling(self, vector_store):
        """Test that duplicate chunks are not added twice."""
        chunk = {
            "content": "def unique(): pass",
            "start_line": 1,
            "end_line": 1,
        }
        
        # Add same chunk twice
        vector_store.add_chunks("/test/unique.py", [chunk])
        vector_store.add_chunks("/test/unique.py", [chunk])
        
        # Should only have one chunk (deduplicated by hash)
        stats = vector_store.get_stats()
        assert stats["total_chunks"] == 1
