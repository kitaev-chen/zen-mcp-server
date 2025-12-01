import asyncio
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Single performance measurement."""
    timestamp: float
    operation: str
    duration_ms: float
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricsCollector:
    """Collect and aggregate performance metrics."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.aggregates = defaultdict(lambda: {'count': 0, 'total_ms': 0, 'errors': 0})
        self._lock = asyncio.Lock()
    
    async def record_operation(
        self, 
        operation: str, 
        duration_ms: float, 
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a performance metric."""
        async with self._lock:
            metric = PerformanceMetric(
                timestamp=time.time(),
                operation=operation,
                duration_ms=duration_ms,
                status=status,
                metadata=metadata or {}
            )
            self.metrics.append(metric)
            
            # Update aggregates
            agg = self.aggregates[operation]
            agg['count'] += 1
            agg['total_ms'] += duration_ms
            if status == 'error':
                agg['errors'] += 1
    
    async def get_metrics_summary(self, operation_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary."""
        async with self._lock:
            if operation_filter:
                metrics = [m for m in self.metrics if m.operation == operation_filter]
                agg = {operation_filter: self.aggregates[operation_filter]}
            else:
                metrics = self.metrics
                agg = dict(self.aggregates)
            
            summary = {}
            for op, data in agg.items():
                if data['count'] == 0:
                    continue
                
                avg_duration = data['total_ms'] / data['count']
                error_rate = data['errors'] / data['count']
                
                summary[op] = {
                    'total_operations': data['count'],
                    'average_duration_ms': round(avg_duration, 2),
                    'error_rate': round(error_rate, 4),
                    'total_errors': data['errors']
                }
            
            # Clean up old metrics (keep last 1000)
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
            
            return summary
    
    async def get_recent_metrics(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get recent metrics for analysis."""
        cutoff_time = time.time() - (minutes * 60)
        async with self._lock:
            recent = [
                {
                    'timestamp': m.timestamp,
                    'operation': m.operation,
                    'duration_ms': m.duration_ms,
                    'status': m.status,
                    'metadata': m.metadata
                }
                for m in self.metrics
                if m.timestamp > cutoff_time
            ]
        
        return recent

# Global instance
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector