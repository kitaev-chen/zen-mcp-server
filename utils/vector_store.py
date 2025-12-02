"""
Vector store for semantic code search.

Uses chromadb for vector storage and similarity search.
Designed to be lightweight and easy to maintain.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy import chromadb to avoid startup cost if not used
_chromadb = None


def _get_chromadb():
    """Lazy import chromadb."""
    global _chromadb
    if _chromadb is None:
        try:
            import chromadb
            _chromadb = chromadb
        except ImportError:
            raise ImportError(
                "chromadb is required for vector search. "
                "Install with: pip install chromadb"
            )
    return _chromadb


class VectorStore:
    """Simple vector store using chromadb.
    
    Provides code indexing and semantic search capabilities.
    Uses chromadb's built-in embedding function for simplicity.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize vector store.
        
        Args:
            db_path: Path to store the vector database. 
                     Defaults to ~/.zen/vectors
        """
        chromadb = _get_chromadb()
        
        if db_path is None:
            db_path = str(Path.home() / ".zen" / "vectors")
        
        Path(db_path).mkdir(parents=True, exist_ok=True)
        
        self._client = chromadb.PersistentClient(path=db_path)
        self._collection = self._client.get_or_create_collection(
            name="code_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        logger.debug(f"Vector store initialized at {db_path}")
    
    def _generate_id(self, file_path: str, start_line: int) -> str:
        """Generate a unique ID for a code chunk."""
        content = f"{file_path}:{start_line}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_chunks(self, file_path: str, chunks: list[dict]) -> int:
        """Add code chunks from a file.
        
        Args:
            file_path: Absolute path to the source file
            chunks: List of chunk dicts with keys:
                    - content: The code content
                    - start_line: Starting line number
                    - end_line: Ending line number
        
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            chunk_id = self._generate_id(file_path, chunk["start_line"])
            ids.append(chunk_id)
            documents.append(chunk["content"])
            metadatas.append({
                "file_path": file_path,
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
            })
        
        # Upsert to handle re-indexing
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        
        return len(chunks)
    
    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search for code chunks matching the query.
        
        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching chunks with file_path, start_line, end_line, content, score
        """
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
            
            if not results["ids"][0]:
                return []
            
            matches = []
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                content = results["documents"][0][i]
                # Convert distance to similarity score (chromadb uses L2/cosine distance)
                distance = results["distances"][0][i] if results["distances"] else 0
                score = max(0, 1 - distance)  # Convert to similarity
                
                matches.append({
                    "file_path": metadata["file_path"],
                    "start_line": metadata["start_line"],
                    "end_line": metadata["end_line"],
                    "content": content,
                    "score": round(score, 3),
                })
            
            return matches
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def delete_file(self, file_path: str) -> int:
        """Delete all chunks from a specific file.
        
        Args:
            file_path: Path of the file to remove from index
            
        Returns:
            Number of chunks deleted (approximate)
        """
        try:
            # Get existing chunks for this file
            results = self._collection.get(
                where={"file_path": file_path},
                include=[],
            )
            
            if results["ids"]:
                self._collection.delete(ids=results["ids"])
                return len(results["ids"])
            return 0
        except Exception as e:
            logger.error(f"Failed to delete file from index: {e}")
            return 0
    
    def clear(self) -> None:
        """Clear all indexed data."""
        try:
            self._client.delete_collection("code_chunks")
            self._collection = self._client.create_collection(
                name="code_chunks",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
    
    def get_stats(self) -> dict:
        """Get statistics about the indexed data."""
        try:
            count = self._collection.count()
            return {
                "total_chunks": count,
                "collection_name": "code_chunks",
            }
        except Exception as e:
            logger.error(f"Failed to get vector store stats: {e}")
            return {"total_chunks": 0, "error": str(e)}


# Convenience function to get a shared instance
_shared_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get the shared vector store instance."""
    global _shared_store
    if _shared_store is None:
        _shared_store = VectorStore()
    return _shared_store
