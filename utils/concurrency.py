import asyncio
import os
from typing import Optional
from contextlib import asynccontextmanager

class ConcurrencyManager:
    """Centralized concurrency control for MCP server."""
    
    def __init__(self):
        # Provider-specific limits (prevent API overwhelm)
        self.provider_semaphores = {
            'gemini': asyncio.Semaphore(10),  # Gemini rate limits
            'openai': asyncio.Semaphore(20),  # OpenAI rate limits
            'openrouter': asyncio.Semaphore(15),
            'custom': asyncio.Semaphore(5),
        }
        
        # Memory protection
        self.memory_limit_mb = int(os.getenv('MEMORY_LIMIT_MB', '2048'))
        self.current_memory_mb = 0
        self._memory_lock = asyncio.Lock()
        
        # Request queue management
        self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', '50'))
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
    
    @asynccontextmanager
    async def acquire_request_slot(self):
        """Acquire a request processing slot."""
        async with self.request_semaphore:
            yield
    
    @asynccontextmanager
    async def acquire_provider_slot(self, provider_type: str):
        """Acquire a provider-specific slot."""
        semaphore = self.provider_semaphores.get(provider_type.lower())
        if not semaphore:
            # Fallback to generic limit
            semaphore = asyncio.Semaphore(5)
        
        async with semaphore:
            yield
    
    async def check_memory_available(self, estimated_mb: float) -> bool:
        """Check if memory is available for operation."""
        async with self._memory_lock:
            return (self.current_memory_mb + estimated_mb) <= self.memory_limit_mb
    
    async def track_memory_usage(self, delta_mb: float):
        """Track memory allocation/deallocation."""
        async with self._memory_lock:
            self.current_memory_mb += delta_mb

# Global instance
_manager: Optional[ConcurrencyManager] = None

def get_concurrency_manager() -> ConcurrencyManager:
    """Get the global concurrency manager."""
    global _manager
    if _manager is None:
        _manager = ConcurrencyManager()
    return _manager