"""
Index Code tool - Index code files for semantic search.

This tool indexes code files into a vector store for semantic search.
Supports incremental indexing and multiple file types.
"""

import logging
import os
import time
from typing import Any, Optional

from mcp.types import TextContent

from tools.shared.base_models import ToolRequest
from tools.shared.base_tool import BaseTool
from utils.security_config import EXCLUDED_DIRS

logger = logging.getLogger(__name__)

# Default extensions to index
DEFAULT_EXTENSIONS = [".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".txt", ".json", ".yaml", ".yml"]


class IndexCodeTool(BaseTool):
    """
    Index code files for semantic search.
    
    This tool scans a directory, chunks code files, and stores them
    in a vector database for later semantic search via search_code.
    Does not require an AI model.
    """

    def get_name(self) -> str:
        return "index_code"

    def get_description(self) -> str:
        return (
            "Index code files in a directory for semantic search. "
            "Run this before using search_code to enable natural language code search. "
            "Indexes Python, JavaScript, TypeScript, Markdown, and other text files."
        )

    def get_request_model(self):
        return ToolRequest

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to index. Defaults to current directory.",
                    "default": ".",
                },
                "extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": f"File extensions to index. Defaults to: {DEFAULT_EXTENSIONS}",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force re-indexing of all files.",
                    "default": False,
                },
                "chunk_size": {
                    "type": "integer",
                    "description": "Lines per chunk (default: 50).",
                    "default": 50,
                    "minimum": 10,
                    "maximum": 200,
                },
            },
            "required": [],
            "additionalProperties": False,
        }

    def get_annotations(self) -> Optional[dict[str, Any]]:
        """This tool modifies the vector index."""
        return {"readOnlyHint": False}

    def get_system_prompt(self) -> str:
        """No AI model needed for this tool."""
        return ""

    def requires_model(self) -> bool:
        return False

    async def prepare_prompt(self, request: ToolRequest) -> str:
        """Not used for this utility tool."""
        return ""

    def format_response(self, response: str, request: ToolRequest, model_info: dict = None) -> str:
        """Not used for this utility tool."""
        return response

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute the indexing operation."""
        path = arguments.get("path", ".")
        extensions = arguments.get("extensions") or DEFAULT_EXTENSIONS
        force = arguments.get("force", False)
        chunk_size = arguments.get("chunk_size", 50)

        # Resolve path
        if not os.path.isabs(path):
            # Try to get working directory from context
            working_dir = arguments.get("working_directory_absolute_path", os.getcwd())
            path = os.path.join(working_dir, path)
        
        path = os.path.abspath(path)

        if not os.path.exists(path):
            return [TextContent(type="text", text=f"❌ Path does not exist: {path}")]

        if not os.path.isdir(path):
            return [TextContent(type="text", text=f"❌ Path is not a directory: {path}")]

        # Import vector store (lazy to avoid startup cost)
        try:
            from utils.vector_store import get_vector_store
            store = get_vector_store()
        except ImportError as e:
            return [TextContent(type="text", text=f"❌ Vector search not available: {e}\nInstall with: pip install chromadb")]

        # Clear existing index if force
        if force:
            store.clear()

        # Find files to index
        files_to_index = self._find_files(path, extensions)
        
        if not files_to_index:
            return [TextContent(type="text", text=f"ℹ️ No files found to index in {path} with extensions {extensions}")]

        # Index files
        start_time = time.time()
        total_chunks = 0
        indexed_files = 0
        errors = []

        for file_path in files_to_index:
            try:
                chunks = self._chunk_file(file_path, chunk_size)
                if chunks:
                    count = store.add_chunks(file_path, chunks)
                    total_chunks += count
                    indexed_files += 1
            except Exception as e:
                errors.append(f"{file_path}: {e}")
                logger.warning(f"Failed to index {file_path}: {e}")

        elapsed = time.time() - start_time
        
        # Build response
        result = [
            f"✅ Indexed {indexed_files} files ({total_chunks} chunks) in {elapsed:.1f}s",
            f"📁 Directory: {path}",
            f"📝 Extensions: {', '.join(extensions)}",
        ]
        
        if errors:
            result.append(f"\n⚠️ {len(errors)} files had errors:")
            for err in errors[:5]:  # Show first 5 errors
                result.append(f"  - {err}")
            if len(errors) > 5:
                result.append(f"  ... and {len(errors) - 5} more")
        
        result.append("\n💡 Use `search_code` to search the indexed code.")
        
        return [TextContent(type="text", text="\n".join(result))]

    def _find_files(self, directory: str, extensions: list[str]) -> list[str]:
        """Find all files matching the extensions."""
        files = []
        extensions_set = set(ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions)
        
        for root, dirs, filenames in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
            
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions_set:
                    files.append(os.path.join(root, filename))
        
        return files

    def _chunk_file(self, file_path: str, chunk_size: int) -> list[dict]:
        """Split a file into chunks for indexing."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            logger.warning(f"Cannot read {file_path}: {e}")
            return []

        if not lines:
            return []

        chunks = []
        # Use overlapping chunks for better search results
        overlap = chunk_size // 4
        
        i = 0
        while i < len(lines):
            end = min(i + chunk_size, len(lines))
            content = "".join(lines[i:end])
            
            # Skip very small chunks or empty content
            if len(content.strip()) > 20:
                chunks.append({
                    "start_line": i + 1,  # 1-indexed
                    "end_line": end,
                    "content": content,
                })
            
            i += chunk_size - overlap
            if i + overlap >= len(lines):
                break

        return chunks
