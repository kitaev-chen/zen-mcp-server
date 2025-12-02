"""
Search Code tool - Semantic search across indexed codebase.

This tool performs natural language search across code that has been
indexed by the index_code tool.
"""

import logging
from typing import Any, Optional

from mcp.types import TextContent

from tools.shared.base_models import ToolRequest
from tools.shared.base_tool import BaseTool

logger = logging.getLogger(__name__)


class SearchCodeTool(BaseTool):
    """
    Semantic search across indexed codebase.
    
    This tool searches for code using natural language queries.
    It finds semantically similar code, not just exact text matches.
    Does not require an AI model.
    
    Example queries:
    - "authentication logic"
    - "database connection handling"
    - "error handling patterns"
    - "API endpoint definitions"
    """

    def get_name(self) -> str:
        return "search_code"

    def get_description(self) -> str:
        return (
            "Semantic search across indexed code. Use natural language to find relevant code. "
            "Unlike grep, this finds semantically similar code even without exact keyword matches. "
            "Run index_code first to index the codebase."
        )

    def get_request_model(self):
        return ToolRequest

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query describing what you're looking for.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 10).",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
                "min_score": {
                    "type": "number",
                    "description": "Minimum similarity score 0-1 (default: 0.3).",
                    "default": 0.3,
                    "minimum": 0,
                    "maximum": 1,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        }

    def get_annotations(self) -> Optional[dict[str, Any]]:
        """This tool is read-only."""
        return {"readOnlyHint": True}

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
        """Execute the search operation."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        min_score = arguments.get("min_score", 0.3)

        if not query.strip():
            return [TextContent(type="text", text="❌ Please provide a search query.")]

        # Import vector store (lazy to avoid startup cost)
        try:
            from utils.vector_store import get_vector_store
            store = get_vector_store()
        except ImportError as e:
            return [TextContent(type="text", text=f"❌ Vector search not available: {e}\nInstall with: pip install chromadb")]

        # Check if index exists
        stats = store.get_stats()
        if stats.get("total_chunks", 0) == 0:
            return [TextContent(type="text", text=(
                "ℹ️ No code has been indexed yet.\n\n"
                "Run `index_code` first to index your codebase:\n"
                "```\nindex_code(path=\"/path/to/your/project\")\n```"
            ))]

        # Perform search
        results = store.search(query, limit=limit)
        
        if not results:
            return [TextContent(type="text", text=f"🔍 No results found for: \"{query}\"\n\nTry a different query or re-index with `index_code`.")]

        # Filter by minimum score
        filtered_results = [r for r in results if r["score"] >= min_score]
        
        if not filtered_results:
            return [TextContent(type="text", text=(
                f"🔍 No results above score threshold ({min_score}).\n"
                f"Found {len(results)} results with lower scores.\n"
                f"Try lowering min_score or using a different query."
            ))]

        # Format results
        output = [f"## 🔍 Found {len(filtered_results)} matches for: \"{query}\"\n"]
        
        for i, result in enumerate(filtered_results, 1):
            file_path = result["file_path"]
            start_line = result["start_line"]
            end_line = result["end_line"]
            score = result["score"]
            content = result["content"]
            
            # Truncate long content
            max_preview = 500
            preview = content[:max_preview]
            if len(content) > max_preview:
                preview += "\n... (truncated)"
            
            output.append(f"### {i}. {file_path}")
            output.append(f"**Lines {start_line}-{end_line}** | Score: {score:.2f}\n")
            output.append(f"```")
            output.append(preview)
            output.append("```\n")

        # Add stats
        output.append(f"---\n📊 Searched {stats['total_chunks']} indexed chunks")
        
        return [TextContent(type="text", text="\n".join(output))]
