"""
Advanced concurrency and resource management for Zen MCP Server.

This module provides sophisticated concurrency control, resource pooling,
and intelligent scheduling for optimal performance and reliability.
"""

import asyncio
import os
import time
import psutil
import weakref
from abc import ABC, abstractmethod
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from typing_extensions import TypedDict


class TaskPriority(Enum):
    """Task priority levels for intelligent scheduling."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class ResourceType(Enum):
    """Types of resources that can be limited."""
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    PROCESS = "process"


@dataclass
class TaskProfile:
    """Profile of a task for scheduling decisions."""
    task_id: str
    priority: TaskPriority
    estimated_duration: float  # seconds
    resource_requirements: Dict[ResourceType, float]
    task_type: str  # "cli", "api", "consensus", etc.
    created_at: float = field(default_factory=time.time)
    model_name: Optional[str] = None
    token_estimate: Optional[int] = None


@dataclass
class ResourceSnapshot:
    """Snapshot of current resource usage."""
    memory_mb: float
    cpu_percent: float
    network_concurrent: int
    process_count: int
    timestamp: float = field(default_factory=time.time)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    success_threshold: int = 3
    half_open_max_calls: int = 3


class CircuitBreaker:
    """Circuit breaker for provider fault tolerance."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time > self.config.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise asyncio.TimeoutError(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure()
            raise
    
    async def _record_success(self):
        """Record successful call."""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0
    
    async def _record_failure(self):
        """Record failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
            elif (self.state == CircuitBreakerState.CLOSED and 
                  self.failure_count >= self.config.failure_threshold):
                self.state = CircuitBreakerState.OPEN
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state for monitoring."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "success_count": self.success_count if self.state == CircuitBreakerState.HALF_OPEN else 0
        }


class ProcessPoolManager:
    """Manages pool of reusable CLI processes for reduced overhead."""
    
    def __init__(self, max_idle: int = 3, idle_timeout: float = 300.0):
        self.max_idle = max_idle
        self.idle_timeout = idle_timeout
        self._pools: Dict[str, List[asyncio.subprocess.Process]] = {}
        self._idle_since: Dict[asyncio.subprocess.Process, float] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
    
    async def acquire(self, cli_name: str) -> Optional[asyncio.subprocess.Process]:
        """Acquire a process from pool or create new one."""
        async with self._lock:
            pool = self._pools.get(cli_name, [])
            
            while pool:
                process = pool.pop(0)
                if process.returncode is None:  # Still alive
                    self._idle_since.pop(process, None)
                    return process
            
            return None
    
    async def release(self, cli_name: str, process: asyncio.subprocess.Process):
        """Release process back to pool for reuse."""
        if process.returncode is not None:
            return  # Don't pool dead processes
        
        async with self._lock:
            pool = self._pools.setdefault(cli_name, [])
            
            if len(pool) >= self.max_idle:
                # Pool full, terminate oldest
                oldest = pool.pop(0)
                try:
                    oldest.terminate()
                    await asyncio.sleep(0.1)  # Give it time to cleanup
                except ProcessLookupError:
                    pass
            
            pool.append(process)
            self._idle_since[process] = time.time()
    
    async def start_cleanup(self):
        """Start background cleanup of idle processes."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup(self):
        """Stop cleanup and terminate all pooled processes."""
        self._stop_event.set()
        if self._cleanup_task:
            await self._cleanup_task
        
        async with self._lock:
            for cli_name, pool in self._pools.items():
                for process in pool:
                    try:
                        process.terminate()
                    except ProcessLookupError:
                        pass
            self._pools.clear()
            self._idle_since.clear()
    
    async def _cleanup_loop(self):
        """Background loop to cleanup idle processes."""
        while not self._stop_event.is_set():
            try:
                async with self._lock:
                    now = time.time()
                    to_remove = []
                    
                    for process, idle_since in self._idle_since.items():
                        if now - idle_since > self.idle_timeout:
                            to_remove.append(process)
                    
                    for process in to_remove:
                        process.terminate()
                        self._idle_since.pop(process, None)
                        
                        # Remove from pools
                        for cli_name, pool in self._pools.items():
                            if process in pool:
                                pool.remove(process)
                                break
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Cleanup error: {e}")
                await asyncio.sleep(60)


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on success/failure rates."""
    
    def __init__(self, initial_rate: float, min_rate: float = 1.0, max_rate: float = 100.0):
        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self._tokens = initial_rate
        self._last_update = time.time()
        self._success_count = 0
        self._failure_count = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire token for request."""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_update
            
            # Replenish tokens based on elapsed time
            self._tokens = min(self.current_rate, self._tokens + elapsed * self.current_rate)
            self._last_update = now
            
            if self._tokens < 1.0:
                # Wait for token
                wait_time = (1.0 - self._tokens) / self.current_rate
                await asyncio.sleep(wait_time)
                self._tokens = 0.0
            else:
                self._tokens -= 1.0
    
    async def record_success(self):
        """Record successful request."""
        async with self._lock:
            self._success_count += 1
            # Slowly increase rate on success
            if self._success_count > 10 and self.current_rate < self.max_rate:
                self.current_rate = min(self.max_rate, self.current_rate * 1.1)
                self._success_count = 0
    
    async def record_failure(self):
        """Record failed request."""
        async with self._lock:
            self._failure_count += 1
            # Decrease rate quickly on failure
            if self._failure_count > 3:
                self.current_rate = max(self.min_rate, self.current_rate * 0.5)
                self._failure_count = 0
                self._success_count = 0


class PriorityTaskQueue:
    """Priority-based task queue with resource awareness."""
    
    def __init__(self, concurrency_manager: 'AdvancedConcurrencyManager'):
        self.concurrency_manager = concurrency_manager
        self._queues: Dict[TaskPriority, deque] = {p: deque() for p in TaskPriority}
        self._processing: Set[str] = set()
        self._lock = asyncio.Lock()
        self._wakeup_event = asyncio.Event()
    
    async def enqueue(self, task: TaskProfile, coro: Callable):
        """Add task to queue."""
        async with self._lock:
            task_data = {"task": task, "coro": coro, "future": asyncio.Future()}
            self._queues[task.priority].append(task_data)
            self._wakeup_event.set()
        
        # Wait for task completion
        return await task_data["future"]
    
    async def dequeue_next(self) -> Optional[Dict[str, Any]]:
        """Get next task based on priority and resource availability."""
        async with self._lock:
            for priority in TaskPriority:
                if self._queues[priority]:
                    task_data = self._queues[priority][0]
                    
                    # Check if resources available
                    if await self._can_execute(task_data["task"]):
                        self._queues[priority].popleft()
                        self._processing.add(task_data["task"].task_id)
                        return task_data
        
        return None
    
    async def _can_execute(self, task: TaskProfile) -> bool:
        """Check if task can be executed given current resources."""
        snapshot = await self.concurrency_manager.get_resource_snapshot()
        
        for resource_type, required in task.resource_requirements.items():
            available = await self.concurrency_manager.get_available_capacity(resource_type)
            if required > available * 0.8:  # Reserve 20% buffer
                return False
        
        return True
    
    async def task_completed(self, task_id: str):
        """Mark task as completed."""
        async with self._lock:
            self._processing.discard(task_id)
            self._wakeup_event.set()


class AdvancedConcurrencyManager:
    """Advanced concurrency manager with intelligent scheduling."""
    
    def __init__(self):
        # Configuration
        self.max_memory_mb = int(os.getenv('MAX_MEMORY_MB', '4096'))
        self.max_cpu_percent = float(os.getenv('MAX_CPU_PERCENT', '80.0'))
        self.max_concurrent_processes = int(os.getenv('MAX_CONCURRENT_PROCESSES', '20'))
        self.max_network_concurrent = int(os.getenv('MAX_NETWORK_CONCURRENT', '30'))
        
        # Resource tracking
        self._current_memory_mb = 0
        self._network_concurrent = 0
        self._active_processes: Set[asyncio.subprocess.Process] = weakref.WeakSet()
        
        # Provider-specific circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._rate_limiters: Dict[str, AdaptiveRateLimiter] = {}
        
        # Process pooling
        self.process_pool = ProcessPoolManager()
        
        # Task queue
        self.task_queue = PriorityTaskQueue(self)
        
        # Locks
        self._resource_lock = asyncio.Lock()
        self._session_lock = asyncio.Lock()
        self._http_session: Optional[aiohttp.ClientSession] = None
        
        # Thread pool for CPU-bound operations (like token counting)
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
    
    async def start(self):
        """Initialize the concurrency manager."""
        await self.process_pool.start_cleanup()
        asyncio.create_task(self._scheduler_loop())
        asyncio.create_task(self._resource_monitor())
    
    async def stop(self):
        """Cleanup resources."""
        await self.process_pool.stop_cleanup()
        if self._http_session:
            await self._http_session.close()
        self._thread_pool.shutdown(wait=False)
    
    def get_circuit_breaker(self, provider_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for provider."""
        if provider_name not in self.circuit_breakers:
            config = CircuitBreakerConfig(
                failure_threshold=int(os.getenv(f'{provider_name.upper()}_CB_THRESHOLD', '5')),
                recovery_timeout=float(os.getenv(f'{provider_name.upper()}_CB_TIMEOUT', '60.0'))
            )
            self.circuit_breakers[provider_name] = CircuitBreaker(provider_name, config)
        
        return self.circuit_breakers[provider_name]
    
    def get_rate_limiter(self, provider_name: str) -> AdaptiveRateLimiter:
        """Get or create rate limiter for provider."""
        if provider_name not in self._rate_limiters:
            initial_rate = float(os.getenv(f'{provider_name.upper()}_INITIAL_RATE', '10.0'))
            self._rate_limiters[provider_name] = AdaptiveRateLimiter(initial_rate)
        
        return self._rate_limiters[provider_name]
    
    async def get_resource_snapshot(self) -> ResourceSnapshot:
        """Get current resource snapshot."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return ResourceSnapshot(
            memory_mb=memory_info.rss / 1024 / 1024,
            cpu_percent=process.cpu_percent(),
            network_concurrent=self._network_concurrent,
            process_count=len(self._active_processes)
        )
    
    async def get_available_capacity(self, resource_type: ResourceType) -> float:
        """Get available capacity for resource type."""
        snapshot = await self.get_resource_snapshot()
        
        if resource_type == ResourceType.MEMORY:
            return self.max_memory_mb - snapshot.memory_mb
        elif resource_type == ResourceType.CPU:
            return max(0, self.max_cpu_percent - snapshot.cpu_percent)
        elif resource_type == ResourceType.NETWORK:
            return self.max_network_concurrent - snapshot.network_concurrent
        elif resource_type == ResourceType.PROCESS:
            return self.max_concurrent_processes - snapshot.process_count
        
        return 0
    
    async def track_memory(self, delta_mb: float):
        """Track memory usage change."""
        async with self._resource_lock:
            self._current_memory_mb += delta_mb
    
    async def get_http_session(self) -> aiohttp.ClientSession:
        """Get shared HTTP session with connection pooling."""
        async with self._session_lock:
            if self._http_session is None or self._http_session.closed:
                connector = aiohttp.TCPConnector(
                    limit=100,  # Connection pool limit
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                    force_close=False
                )
                timeout = aiohttp.ClientTimeout(total=600)
                self._http_session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                )
            
            return self._http_session
    
    def run_in_thread(self, func: Callable, *args, **kwargs):
        """Run CPU-bound operation in thread pool."""
        return asyncio.get_event_loop().run_in_executor(
            self._thread_pool,
            lambda: func(*args, **kwargs)
        )
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while True:
            try:
                task_data = await self.task_queue.dequeue_next()
                
                if task_data:
                    # Execute task
                    asyncio.create_task(self._execute_task(task_data))
                else:
                    # Wait for new tasks or wakeup
                    await asyncio.wait_for(
                        self.task_queue._wakeup_event.wait(),
                        timeout=1.0
                    )
                    self.task_queue._wakeup_event.clear()
            
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task_data: Dict[str, Any]):
        """Execute a single task."""
        task = task_data["task"]
        
        try:
            # Pre-allocate resources
            await self._allocate_resources(task.resource_requirements)
            
            # Execute coroutine
            result = await task_data["coro"]
            task_data["future"].set_result(result)
            
        except Exception as e:
            task_data["future"].set_exception(e)
        
        finally:
            # Release resources
            await self._deallocate_resources(task.resource_requirements)
            await self.task_queue.task_completed(task.task_id)
    
    async def _allocate_resources(self, requirements: Dict[ResourceType, float]):
        """Allocate resources for task."""
        async with self._resource_lock:
            for resource_type, amount in requirements.items():
                if resource_type == ResourceType.MEMORY:
                    self._current_memory_mb += amount
                elif resource_type == ResourceType.NETWORK:
                    self._network_concurrent += int(amount)
                elif resource_type == ResourceType.PROCESS:
                    # Track processes externally
                    pass
    
    async def _deallocate_resources(self, requirements: Dict[ResourceType, float]):
        """Deallocate resources after task completion."""
        async with self._resource_lock:
            for resource_type, amount in requirements.items():
                if resource_type == ResourceType.MEMORY:
                    self._current_memory_mb = max(0, self._current_memory_mb - amount)
                elif resource_type == ResourceType.NETWORK:
                    self._network_concurrent = max(0, self._network_concurrent - int(amount))
    
    async def _resource_monitor(self):
        """Monitor system resources."""
        while True:
            try:
                snapshot = await self.get_resource_snapshot()
                
                # Log high resource usage
                if snapshot.memory_mb > self.max_memory_mb * 0.9:
                    print(f"WARNING: Memory usage {snapshot.memory_mb:.0f}MB > 90% limit")
                
                if snapshot.network_concurrent > self.max_network_concurrent * 0.9:
                    print(f"WARNING: Network concurrency {snapshot.network_concurrent} > 90% limit")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            
            except Exception as e:
                print(f"Resource monitor error: {e}")
                await asyncio.sleep(60)


# Global instance
_manager: Optional[AdvancedConcurrencyManager] = None


def get_advanced_concurrency_manager() -> AdvancedConcurrencyManager:
    """Get global advanced concurrency manager."""
    global _manager
    if _manager is None:
        _manager = AdvancedConcurrencyManager()
    return _manager
