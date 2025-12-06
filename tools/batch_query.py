"""
batch_query tool - Parallel execution of multiple models (CLI and API mixed)

This tool enables parallel querying of multiple models simultaneously,
supporting both CLI models (via clink) and API models (via providers).
Results are aggregated and returned in a unified format.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
import json
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mcp.types import TextContent
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from tools.models import ToolModelCategory

from clink import get_registry
from clink.agents import CLIAgentError, create_agent
from systemprompts import CHAT_PROMPT
from tools.models import ToolOutput
from tools.shared.base_models import COMMON_FIELD_DESCRIPTIONS
from tools.shared.base_tool import BaseTool
from tools.shared.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)

# Concurrency limits to prevent resource exhaustion
# These can be adjusted based on system resources and provider rate limits
MAX_CONCURRENT_CLI = 10  # CLI models spawn subprocesses (conservative limit)
MAX_CONCURRENT_API = 50  # API models use network I/O (can be higher than CLI)

# CLI model aliases mapping
CLI_ALIASES = {
    "gcli": "gemini",
    "kcli": "kimi",
    "icli": "iflow",
    "qcli": "qwen",
    "ccli": "claude",
    "ocli": "codex",
    "vcli": "vecli",
}

# All CLI model identifiers (aliases + direct names)
CLI_MODEL_NAMES = set(CLI_ALIASES.keys()) | set(CLI_ALIASES.values())


def is_cli_model(model: str) -> bool:
    """Check if a model is a CLI model."""
    return model.lower() in CLI_MODEL_NAMES or model.lower().startswith("cli:")


def resolve_cli_name(model: str) -> str:
    """Resolve CLI alias to actual CLI name."""
    model_lower = model.lower()
    if model_lower.startswith("cli:"):
        return model_lower[4:]
    return CLI_ALIASES.get(model_lower, model_lower)


class BatchQueryRequest(BaseModel):
    """Request model for batch_query tool."""

    models: list[str] = Field(
        ...,
        description=(
            "List of models to query in parallel. Supports mixed CLI and API models. "
            "CLI models: gcli, kcli, icli, qcli, ccli, ocli, vcli. "
            "API models: pro, flash, glm, qwen3c, longcatt, deepseekr, deepseekv, kimik, etc."
            "Example: ['gcli', 'pro', 'kcli', 'glm']"
        ),
    )
    prompt: str = Field(
        ...,
        description="The prompt to send to all models. Each model will receive the same prompt.",
    )
    role: str = Field(
        default="default",
        description="Role preset for CLI models (e.g., 'default', 'planner', 'codereviewer').",
    )
    absolute_file_paths: list[str] = Field(
        default_factory=list,
        description=COMMON_FIELD_DESCRIPTIONS["absolute_file_paths"],
    )
    images: list[str] = Field(
        default_factory=list,
        description=COMMON_FIELD_DESCRIPTIONS["images"],
    )


class ModelResult(BaseModel):
    """Result from a single model query."""

    model: str
    model_type: str  # "cli" or "api"
    status: str  # "success" or "error"
    content: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchQueryTool(BaseTool):
    """
    Parallel query tool for multiple models (CLI and API mixed).

    This tool enables efficient parallel querying of multiple AI models,
    automatically routing CLI models to clink and API models to providers.

    Key features:
    - Parallel execution using asyncio.gather
    - Mixed CLI/API model support
    - Unified result format
    - Automatic model type detection and routing
    - Per-model error handling (failures don't block other models)
    """

    def __init__(self) -> None:
        super().__init__()
        self._cli_registry = get_registry()
        self._prompt_cache = {}  # Cache system prompt files to reduce disk I/O

    def get_name(self) -> str:
        return "batch_query"

    def get_description(self) -> str:
        return (
            "⚠️ FOR MULTI-MODEL PARALLEL QUERIES: This is the ONLY tool you should use. "
            "Do NOT use 'clink' for CLI models or 'thinkdeep'/'chat' for API models individually. "
            "Parallel query multiple models (CLI and API mixed) with a single prompt. "
            "All models execute concurrently, results aggregated by completion order. "
            "Supports: CLI (gcli, kcli, icli, qcli, ccli, ocli, vcli) and API (pro, flash, glm, qwen3c, longcatt, deepseekr, deepseekv, kimik, etc.). "
            "Use for multi-model synthesis, consensus gathering, comparative analysis, performance optimization analysis, or any task requiring multiple model perspectives simultaneously."
        )

    def get_annotations(self) -> dict[str, Any]:
        return {"readOnlyHint": True}

    def requires_model(self) -> bool:
        """This tool manages its own model calls, doesn't need external model."""
        return False

    def get_model_category(self) -> "ToolModelCategory":
        from tools.models import ToolModelCategory

        return ToolModelCategory.BALANCED

    def get_system_prompt(self) -> str:
        """No system prompt needed - each model uses its own."""
        return ""

    def get_request_model(self):
        """Return the request model for this tool."""
        return BatchQueryRequest

    async def prepare_prompt(self, request: BatchQueryRequest) -> str:
        """Prepare prompt - just return the user's prompt as-is."""
        return request.prompt

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of models to query in parallel. Supports mixed CLI and API models. "
                        "CLI: gcli, kcli, icli, qcli, ccli, ocli, vcli. "
                        "API: pro, flash, glm, qwen3c, longcatt, deepseekr, deepseekv, kimik, etc."
                    ),
                    "minItems": 1,
                },
                "prompt": {
                    "type": "string",
                    "description": "The prompt to send to all models.",
                },
                "role": {
                    "type": "string",
                    "description": "Role preset for CLI models (default: 'default').",
                    "default": "default",
                },
                "absolute_file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": COMMON_FIELD_DESCRIPTIONS["absolute_file_paths"],
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": COMMON_FIELD_DESCRIPTIONS["images"],
                },
            },
            "required": ["models", "prompt"],
            "additionalProperties": False,
        }

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute parallel queries to multiple models with concurrency control."""
        request = BatchQueryRequest(**arguments)

        if not request.models:
            raise ToolExecutionError("At least one model must be specified")

        # Validate model names to prevent tool misuse
        forbidden_models = {"thinkdeep", "chat", "clink", "batch_query"}
        for model in request.models:
            if model.lower() in forbidden_models:
                raise ToolExecutionError(
                    f"Invalid model name '{model}'. Tools like '{model}' cannot be used as models in batch_query. "
                    "Please use actual model names (e.g., 'gemini-pro', 'gpt-4') or CLI aliases."
                )

        # Create semaphores with dynamic concurrency limits based on system resources
        from utils.concurrency_v2 import get_advanced_concurrency_manager, ResourceType
        cm = get_advanced_concurrency_manager()
        
        # Get available resources (use 80% of available capacity to leave buffer)
        available_process = max(1, int(await cm.get_available_capacity(ResourceType.PROCESS) * 0.8))
        available_network = max(1, int(await cm.get_available_capacity(ResourceType.NETWORK) * 0.8))
        
        # Use dynamic limits but do not exceed predefined maximums
        cli_semaphore = asyncio.Semaphore(min(available_process, MAX_CONCURRENT_CLI))
        api_semaphore = asyncio.Semaphore(min(available_network, MAX_CONCURRENT_API))

        async def query_with_limit(model: str) -> ModelResult:
            """Wrap query with appropriate semaphore."""
            if is_cli_model(model):
                async with cli_semaphore:
                    return await self._query_cli_model(model, request)
            else:
                async with api_semaphore:
                    return await self._query_api_model(model, request)

        # Execute all models in parallel with concurrency limits
        start_time = time.time()
        tasks = [query_with_limit(model) for model in request.models]

        # Gather all results (use return_exceptions=True for safety, but our query methods
        # already catch exceptions and return ModelResult with error status)
        gathered_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert any unexpected exceptions to ModelResult
        results = []
        for i, result in enumerate(gathered_results):
            if isinstance(result, Exception):
                # Unexpected exception that wasn't caught - convert to error result
                model = request.models[i]
                logger.exception(f"Unexpected exception for model {model}")
                results.append(
                    ModelResult(
                        model=model,
                        model_type="cli" if is_cli_model(model) else "api",
                        status="error",
                        error=f"Unexpected exception: {result}",
                        duration_seconds=0.0,
                    )
                )
            else:
                results.append(result)

        total_duration = time.time() - start_time

        # Generate batch ID for file saving
        batch_id = uuid.uuid4().hex[:8]

        # Build response
        output = self._format_batch_results(request.models, results, total_duration, batch_id)
        
        # Create batch index file for easy reference
        saved_files = output.metadata.get("saved_files", [])
        model_to_file = output.metadata.get("model_to_file", {})
        if saved_files:
            self._create_batch_index(batch_id, request.models, results, saved_files, model_to_file)
        
        # Conversation memory integration: Add file references to conversation memory
        continuation_id = arguments.get("continuation_id")
        if continuation_id and saved_files:
            from utils.conversation_memory import add_turn
            
            # Add assistant response to conversation memory with file references
            add_turn(
                thread_id=continuation_id,
                role="assistant",
                content=output.content,  # Summary content
                files=saved_files,  # Key: File references for automatic access by subsequent models
                tool_name="batch_query",
                model_metadata={
                    "batch_id": batch_id,
                    "models_queried": request.models,
                    "saved_files": saved_files,
                    "total_models": len(request.models),
                    "succeeded": len([r for r in results if r.status == "success"]),
                    "parallel_duration_seconds": round(total_duration, 3),
                }
            )
            logger.info(f"[BATCH] Added batch results to conversation memory with {len(saved_files)} file references")
        
        return [TextContent(type="text", text=output.model_dump_json())]

    async def _query_cli_model(self, model: str, request: BatchQueryRequest) -> ModelResult:
        """Query a CLI model using clink agent."""
        start_time = time.time()
        cli_name = resolve_cli_name(model)
        logger.info(f"[BATCH] Starting CLI model {model} (alias for {cli_name})")

        try:
            # Get CLI client config
            client_config = self._cli_registry.get_client(cli_name)
            role_config = client_config.get_role(request.role)

            # Build prompt with system prompt (use cache to reduce disk I/O)
            prompt_path_str = str(role_config.prompt_path)
            if prompt_path_str not in self._prompt_cache:
                self._prompt_cache[prompt_path_str] = role_config.prompt_path.read_text(encoding="utf-8")
            system_prompt_text = self._prompt_cache[prompt_path_str]
            prompt_text = self._build_cli_prompt(request.prompt, system_prompt_text)

            # Create and run agent
            agent = create_agent(client_config)
            result = await agent.run(
                role=role_config,
                prompt=prompt_text,
                system_prompt=system_prompt_text if system_prompt_text.strip() else None,
                files=request.absolute_file_paths,
                images=request.images,
            )

            duration = time.time() - start_time
            logger.info(f"[BATCH] Completed CLI model {model} in {duration:.2f}s")
            return ModelResult(
                model=model,
                model_type="cli",
                status="success",
                content=result.parsed.content,
                duration_seconds=round(duration, 3),
                metadata={
                    "cli_name": cli_name,
                    "model_used": result.parsed.metadata.get("model_used"),
                    "parser": result.parser_name,
                },
            )

        except CLIAgentError as e:
            duration = time.time() - start_time
            logger.warning(f"[BATCH] CLI model {model} failed in {duration:.2f}s: {e}")
            return ModelResult(
                model=model,
                model_type="cli",
                status="error",
                error=str(e),
                duration_seconds=round(duration, 3),
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"[BATCH] Unexpected error querying CLI model {model}")
            return ModelResult(
                model=model,
                model_type="cli",
                status="error",
                error=f"Unexpected error: {e}",
                duration_seconds=round(duration, 3),
            )

    async def _query_api_model(self, model: str, request: BatchQueryRequest) -> ModelResult:
        """Query an API model using provider.

        Uses ModelContext for proper alias resolution and provider lookup,
        matching the approach used by other tools (chat, analyze, etc.).
        """
        start_time = time.time()
        logger.info(f"[BATCH] Starting API model {model}")

        try:
            # Use ModelContext like other tools - handles alias resolution and better errors
            from utils.model_context import ModelContext

            model_context = ModelContext(model)
            provider = model_context.provider  # Raises helpful ValueError if not found
            capabilities = model_context.capabilities

            # Get the resolved canonical model name (not the alias)
            resolved_model_name = capabilities.model_name

            logger.info(f"batch_query: Resolved '{model}' -> '{resolved_model_name}' via {provider.__class__.__name__}")

            # Call provider with resolved model name
            # Check if generate_content is a coroutine function
            if inspect.iscoroutinefunction(provider.generate_content):
                response = await provider.generate_content(
                    prompt=request.prompt,
                    model_name=resolved_model_name,
                    system_prompt=CHAT_PROMPT,
                    temperature=0.7,
                )
            else:
                # Synchronous method - run in executor to avoid blocking event loop
                logger.warning(f"Provider {provider.__class__.__name__} is synchronous. This may impact parallel performance.")
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: provider.generate_content(
                        prompt=request.prompt,
                        model_name=resolved_model_name,
                        system_prompt=CHAT_PROMPT,
                        temperature=0.7,
                    ),
                )

            duration = time.time() - start_time
            logger.info(f"[BATCH] Completed API model {model} in {duration:.2f}s")
            return ModelResult(
                model=model,
                model_type="api",
                status="success",
                content=response.content if hasattr(response, "content") else str(response),
                duration_seconds=round(duration, 3),
                metadata={
                    "provider": provider.__class__.__name__,
                    "model_used": resolved_model_name,
                    "model_alias": model if model != resolved_model_name else None,
                },
            )

        except ValueError as e:
            # ModelContext raises ValueError with helpful message including available models
            duration = time.time() - start_time
            logger.warning(f"batch_query: API model '{model}' not available: {e}")
            return ModelResult(
                model=model,
                model_type="api",
                status="error",
                error=str(e),
                duration_seconds=round(duration, 3),
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"Error querying API model {model}")
            return ModelResult(
                model=model,
                model_type="api",
                status="error",
                error=f"Unexpected error: {e}",
                duration_seconds=round(duration, 3),
            )

    def _build_cli_prompt(self, user_prompt: str, system_prompt: str) -> str:
        """Build the full prompt for CLI models."""
        sections = []
        if system_prompt.strip():
            sections.append(system_prompt.strip())
        sections.append("=== USER REQUEST ===")
        sections.append(user_prompt)
        sections.append("\nProvide your response below:")
        return "\n\n".join(sections)

    def _save_model_result_to_file(
        self, 
        model: str, 
        result: ModelResult,
        batch_id: str
    ) -> Path | None:
        """Save individual model result to a file."""
        try:
            output_dir = Path("logs") / "batch_query_results"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            # Use batch_id to group results
            filename = f"batch_{batch_id}_{model}_{timestamp}.md"
            output_path = output_dir / filename
            
            # Save structured content
            content = f"# Model: {model} ({result.model_type.upper()})\n\n"
            content += f"## Status: {result.status}\n"
            content += f"## Duration: {result.duration_seconds:.2f}s\n\n"
            
            if result.status == "success":
                content += "## Full Response:\n"
                content += f"{result.content}\n\n"
            else:
                content += "## Error:\n"
                content += f"{result.error}\n\n"
                
            content += "## Metadata:\n"
            content += json.dumps(result.metadata or {}, indent=2, ensure_ascii=False)
            
            output_path.write_text(content, encoding="utf-8")
            return output_path.resolve()
        except Exception as e:
            logger.warning(f"Failed to save {model} result to file: {e}")
            return None

    def _format_batch_results(
        self,
        models: list[str],
        results: list[ModelResult],
        total_duration: float,
        batch_id: str,
    ) -> ToolOutput:
        """Format batch results into unified output with file saving and truncation.
        
        Results are already in the same order as the input models list
        (asyncio.gather preserves order regardless of completion time).
        """
        successful = [r for r in results if r.status == "success"]
        failed = [r for r in results if r.status == "error"]

        # Calculate sequential estimate and performance metrics
        sequential_estimate = sum(r.duration_seconds for r in results)
        time_saved = sequential_estimate - total_duration
        
        # Calculate per-type statistics
        cli_results = [r for r in results if r.model_type == "cli"]
        api_results = [r for r in results if r.model_type == "api"]
        cli_avg_time = sum(r.duration_seconds for r in cli_results) / len(cli_results) if cli_results else 0
        api_avg_time = sum(r.duration_seconds for r in api_results) / len(api_results) if api_results else 0

        # Save results to files and create mapping
        saved_files = []
        model_to_file = {}  # Map model name to file path for easy lookup
        for result in results:
            if result.status == "success" and result.content:
                file_path = self._save_model_result_to_file(result.model, result, batch_id)
                if file_path:
                    file_path_str = str(file_path)
                    saved_files.append(file_path_str)
                    model_to_file[result.model] = file_path_str

        # Build formatted content
        content_parts = []
        content_parts.append(f"=== Batch Query Results ({len(models)} models) ===\n")
        content_parts.append(f"Batch ID: {batch_id}\n")

        # File references section
        if saved_files:
            content_parts.append("--- IMPORTANT: FULL RESULTS SAVED TO FILES ---")
            content_parts.append(f"Complete results from {len(saved_files)} models saved to:")
            for i, file_path in enumerate(saved_files, 1):
                # Find which model this file belongs to (simple matching since order is preserved)
                # Actually we just appended in order of results, but we should be careful.
                # Let's just list them.
                content_parts.append(f"  - {file_path}")
            content_parts.append("You can reference these files in subsequent tool calls.\n")
            content_parts.append("--- END FILE REFERENCES ---\n")

        for i, result in enumerate(results, 1):
            status_icon = "✅" if result.status == "success" else "❌"
            content_parts.append(
                f"\n[{i}/{len(models)}] {result.model} ({result.model_type.upper()}, "
                f"{result.duration_seconds:.1f}s) {status_icon}"
            )
            content_parts.append("─" * 50)

            if result.status == "success":
                # Smart content extraction: Try to extract SUMMARY tag first, then truncate
                content = result.content or ""
                if len(content) > 500:
                    # Try to extract SUMMARY tag (if model provided it)
                    summary_match = re.search(r"<SUMMARY>(.*?)</SUMMARY>", content, re.IGNORECASE | re.DOTALL)
                    if summary_match:
                        summary = summary_match.group(1).strip()
                        # Limit summary display to avoid token limits
                        if len(summary) > 1000:
                            summary = summary[:1000] + "..."
                        content_parts.append(f"Summary: {summary}")
                        content_parts.append(f"\n[Full content ({len(content):,} chars) saved to file]")
                    else:
                        # Fallback to preview of first 500 characters
                        preview = content[:500].replace("\n", " ")
                        content_parts.append(f"{preview}...")
                        content_parts.append(f"\n[Full content ({len(content):,} chars) saved to file]")
                else:
                    content_parts.append(content)
            else:
                content_parts.append(f"Error: {result.error}")

            content_parts.append("")

        # Summary section
        content_parts.append("\n=== Summary ===")
        content_parts.append(f"- Total models: {len(models)} ({len(cli_results)} CLI, {len(api_results)} API)")
        content_parts.append(f"- Succeeded: {len(successful)}")
        content_parts.append(f"- Failed: {len(failed)}")
        content_parts.append(f"- Parallel time: {total_duration:.1f}s")
        content_parts.append(f"- Sequential estimate: {sequential_estimate:.1f}s")
        if time_saved > 0:
            efficiency = (time_saved / sequential_estimate * 100) if sequential_estimate > 0 else 0
            content_parts.append(f"- Time saved: {time_saved:.1f}s ({efficiency:.0f}% faster)")
        if cli_results and api_results:
            content_parts.append(f"- Avg CLI time: {cli_avg_time:.1f}s | Avg API time: {api_avg_time:.1f}s")

        # Execution timeline analysis (verify parallelization effectiveness)
        if len(results) > 1:
            max_duration = max(r.duration_seconds for r in results)
            min_duration = min(r.duration_seconds for r in results)
            avg_duration = sum(r.duration_seconds for r in results) / len(results)
            
            content_parts.append("\n=== Execution Timeline ===")
            content_parts.append(f"- Fastest model: {min_duration:.1f}s")
            content_parts.append(f"- Slowest model: {max_duration:.1f}s")
            content_parts.append(f"- Average: {avg_duration:.1f}s")
            
            # Calculate parallel efficiency
            if total_duration > 0:
                parallel_efficiency = (avg_duration / total_duration * 100)
                content_parts.append(f"- Parallel efficiency: {parallel_efficiency:.0f}%")
                
                # Check if parallelization is effective
                if total_duration < max_duration * 1.1:
                    content_parts.append("✅ Excellent parallelization (total time ≈ slowest model)")
                elif total_duration < max_duration * 1.5:
                    content_parts.append("⚠️ Good parallelization (some overhead detected)")
                else:
                    content_parts.append("⚠️ Serialization detected (total time >> slowest model)")

        # Prepare metadata with truncated results to save tokens
        metadata_results = []
        for r in results:
            res_dict = r.model_dump()
            # Remove full content from metadata
            if res_dict.get("content") and len(res_dict["content"]) > 200:
                res_dict["content_preview"] = res_dict["content"][:200] + "..."
                del res_dict["content"]
            metadata_results.append(res_dict)

        return ToolOutput(
            status="success",
            content="\n".join(content_parts),
            content_type="text",
            metadata={
                "batch_id": batch_id,
                "saved_files": saved_files,
                "model_to_file": model_to_file,  # Add mapping for easy lookup
                "batch_results": metadata_results,
                "summary": {
                    "total_models": len(models),
                    "succeeded": len(successful),
                    "failed": len(failed),
                    "parallel_duration_seconds": round(total_duration, 3),
                    "sequential_estimate_seconds": round(sequential_estimate, 3),
                    "time_saved_seconds": round(max(0, time_saved), 3),
                },
            },
        )

    async def incremental_synthesis_from_files(
        self,
        model_to_file: dict[str, str],
        results: list[ModelResult],
        synthesis_model: str = "glm",
    ) -> str:
        """Incrementally synthesize multiple model results, reading full content from files to avoid token limits.
        
        This method performs pairwise synthesis, reading complete content from saved files
        rather than using potentially truncated result.content. This enables synthesis of
        large responses without hitting token limits.
        
        Args:
            model_to_file: Dictionary mapping model names to their saved file paths
            results: List of ModelResult objects (for metadata and error handling)
            synthesis_model: Model to use for synthesis (default: "glm")
            
        Returns:
            Synthesized summary string, or "无有效结果" if no valid results
        """
        from utils.model_context import ModelContext
        from utils.file_utils import read_file_safely
        
        model_context = ModelContext(synthesis_model)
        provider = model_context.provider
        
        current_summary = None
        
        # Process only successful results that have saved files
        for result in results:
            if result.status != "success":
                logger.debug(f"Skipping failed model {result.model} in synthesis")
                continue
            
            # Get file path for this model
            file_path = model_to_file.get(result.model)
            if not file_path:
                logger.warning(f"No saved file found for {result.model}, skipping")
                continue
            
            # Read full content from file (key: not limited by token constraints)
            full_content = read_file_safely(file_path)
            if not full_content:
                # Fallback to result.content (may be truncated)
                full_content = result.content or ""
                logger.warning(f"Could not read file {file_path}, using truncated content for {result.model}")
            
            if current_summary is None:
                # First result becomes initial summary
                current_summary = full_content
                logger.debug(f"Initial summary from {result.model}: {len(current_summary)} chars")
                continue
            
            # Incremental synthesis: Merge current summary with new result
            # Limit input length to avoid token limits in synthesis model
            prompt = f"""请综合以下两个分析结果：

=== 当前汇总 ===
{current_summary[:3000]}

=== 新结果 ({result.model}) ===
{full_content[:3000]}

请：
1. 提取两个结果的核心观点
2. 识别共识和分歧
3. 生成一个综合摘要（不超过 2000 字）

综合摘要："""
            
            try:
                response = await provider.generate_content(
                    prompt=prompt,
                    model_name=model_context.capabilities.model_name,
                    temperature=0.7,
                )
                
                current_summary = response.content
                logger.debug(f"Synthesized with {result.model}: new summary length {len(current_summary)} chars")
            except Exception as e:
                logger.warning(f"Failed to synthesize with {result.model}: {e}")
                # Continue with previous summary
                continue
        
        return current_summary or "无有效结果"

    def _create_batch_index(
        self,
        batch_id: str,
        models: list[str],
        results: list[ModelResult],
        saved_files: list[str],
        model_to_file: dict[str, str] | None = None,
    ) -> Path | None:
        """Create batch index file for easy reference and querying.
        
        Creates a JSON index file that maps batch_id to all results and file paths,
        enabling easy lookup of batch query results for subsequent analysis or synthesis.
        
        Args:
            batch_id: Unique batch identifier
            models: List of model names queried
            results: List of ModelResult objects
            saved_files: List of file paths containing full results
            model_to_file: Optional dictionary mapping model names to file paths
            
        Returns:
            Path to created index file, or None if creation failed
        """
        try:
            output_dir = Path("logs") / "batch_query_results"
            index_path = output_dir / f"batch_{batch_id}_index.json"
            
            # Use provided model_to_file or create from saved_files if not provided
            if model_to_file is None:
                model_to_file = {}
                # Try to match files to results by index (less reliable)
                file_idx = 0
                for result in results:
                    if result.status == "success" and file_idx < len(saved_files):
                        model_to_file[result.model] = saved_files[file_idx]
                        file_idx += 1
            
            index_data = {
                "batch_id": batch_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "models": models,
                "results": [
                    {
                        "model": r.model,
                        "model_type": r.model_type,
                        "status": r.status,
                        "duration_seconds": r.duration_seconds,
                        "file_path": model_to_file.get(r.model),
                        "content_length": len(r.content) if r.content else 0,
                        "metadata": r.metadata,
                    }
                    for r in results
                ],
                "summary": {
                    "total_models": len(models),
                    "succeeded": len([r for r in results if r.status == "success"]),
                    "failed": len([r for r in results if r.status == "error"]),
                }
            }
            
            index_path.write_text(
                json.dumps(index_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            logger.info(f"[BATCH] Created index file: {index_path}")
            return index_path.resolve()
        except Exception as e:
            logger.warning(f"Failed to create batch index: {e}")
            return None
