import asyncio
import time
from typing import Callable, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 3,
        name: str = "unnamed"
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                else:
                    raise Exception(f"Circuit breaker '{self.name}' is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= self.success_threshold:
                        self.state = CircuitState.CLOSED
                        self.failure_count = 0
                        self.success_count = 0
                        logger.info(f"Circuit breaker '{self.name}' recovered to CLOSED state")
                else:
                    self.failure_count = 0
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.state == CircuitState.HALF_OPEN:
                    # Still failing, go back to OPEN
                    self.state = CircuitState.OPEN
                    self.success_count = 0
                    logger.warning(f"Circuit breaker '{self.name}' failed in HALF_OPEN, returning to OPEN")
                elif self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.error(f"Circuit breaker '{self.name}' triggered OPEN state after {self.failure_count} failures")
                
                raise
    
    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }

class ProviderCircuitBreakers:
    """Circuit breakers for each provider type."""
    
    def __init__(self):
        self.breakers = {
            'gemini': CircuitBreaker(failure_threshold=3, recovery_timeout=30, name="gemini"),
            'openai': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="openai"),
            'openrouter': CircuitBreaker(failure_threshold=10, recovery_timeout=120, name="openrouter"),
            'custom': CircuitBreaker(failure_threshold=2, recovery_timeout=45, name="custom"),
            'azure': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="azure"),
            'xai': CircuitBreaker(failure_threshold=3, recovery_timeout=45, name="xai"),
            'dial': CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="dial"),
            'cli': CircuitBreaker(failure_threshold=2, recovery_timeout=30, name="cli"),
        }
    
    async def call_provider(self, provider_type: str, func: Callable, *args, **kwargs):
        """Call provider through circuit breaker."""
        breaker = self.breakers.get(provider_type.lower())
        if not breaker:
            # No circuit breaker for this provider, call directly
            logger.warning(f"No circuit breaker for provider type '{provider_type}', calling directly")
            return await func(*args, **kwargs)
        
        return await breaker.call(func, *args, **kwargs)
    
    def get_provider_stats(self, provider_type: str) -> Optional[dict]:
        """Get statistics for a specific provider."""
        breaker = self.breakers.get(provider_type.lower())
        if breaker:
            return breaker.get_stats()
        return None
    
    def get_all_stats(self) -> dict:
        """Get statistics for all providers."""
        stats = {}
        for provider_type, breaker in self.breakers.items():
            stats[provider_type] = breaker.get_stats()
        return stats