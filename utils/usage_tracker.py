"""
Usage tracking for Zen MCP Server.

Simple SQLite-based usage tracking without cost calculation.
Tracks: tool calls, provider, model, tokens, duration.
"""

import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class UsageTracker:
    """Lightweight usage tracker using SQLite.
    
    Thread-safe singleton that records all LLM calls for analytics.
    No cost calculation - just raw usage data.
    """
    
    _instance: Optional["UsageTracker"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "UsageTracker":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._db_lock = threading.Lock()
        self._init_db()
        self._initialized = True
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        db_dir = Path.home() / ".zen"
        db_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = db_dir / "usage.db"
        
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tool TEXT,
                provider TEXT,
                model TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                duration_ms INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage(timestamp)")
        conn.commit()
        conn.close()
        logger.debug(f"Usage tracker initialized at {self._db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a new database connection."""
        return sqlite3.connect(str(self._db_path), check_same_thread=False)
    
    def track(
        self,
        tool: str,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: int = 0,
    ) -> None:
        """Record a single LLM call.
        
        Args:
            tool: Name of the tool that made the call
            provider: Provider name (openai, gemini, cli, etc.)
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Call duration in milliseconds
        """
        try:
            with self._db_lock:
                conn = self._get_connection()
                conn.execute(
                    "INSERT INTO usage (timestamp, tool, provider, model, input_tokens, output_tokens, duration_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (datetime.now().isoformat(), tool, provider, model, input_tokens, output_tokens, duration_ms),
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to track usage: {e}")
    
    def get_stats(self, days: int = 30) -> dict:
        """Get usage statistics for the specified period.
        
        Args:
            days: Number of days to include in stats
            
        Returns:
            Dictionary with usage statistics
        """
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            conn = self._get_connection()
            
            # Overall stats
            cur = conn.execute(
                """
                SELECT 
                    COUNT(*) as requests,
                    COALESCE(SUM(input_tokens), 0) as input_tokens,
                    COALESCE(SUM(output_tokens), 0) as output_tokens,
                    COALESCE(AVG(duration_ms), 0) as avg_duration
                FROM usage 
                WHERE timestamp > ?
                """,
                (since,),
            )
            row = cur.fetchone()
            
            # By model breakdown
            cur = conn.execute(
                """
                SELECT provider, model, COUNT(*) as count, 
                       SUM(input_tokens) as in_tokens, SUM(output_tokens) as out_tokens
                FROM usage 
                WHERE timestamp > ?
                GROUP BY provider, model
                ORDER BY count DESC
                """,
                (since,),
            )
            by_model = {
                f"{r[0]}:{r[1]}": {"requests": r[2], "input_tokens": r[3] or 0, "output_tokens": r[4] or 0}
                for r in cur.fetchall()
            }
            
            # By tool breakdown
            cur = conn.execute(
                """
                SELECT tool, COUNT(*) as count
                FROM usage 
                WHERE timestamp > ?
                GROUP BY tool
                ORDER BY count DESC
                """,
                (since,),
            )
            by_tool = {r[0]: r[1] for r in cur.fetchall()}
            
            conn.close()
            
            return {
                "days": days,
                "total_requests": row[0],
                "total_input_tokens": row[1],
                "total_output_tokens": row[2],
                "total_tokens": row[1] + row[2],
                "avg_duration_ms": int(row[3]),
                "by_model": by_model,
                "by_tool": by_tool,
            }
        except Exception as e:
            logger.warning(f"Failed to get usage stats: {e}")
            return {
                "days": days,
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "avg_duration_ms": 0,
                "by_model": {},
                "by_tool": {},
                "error": str(e),
            }


# Global singleton instance
def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    return UsageTracker()


# Convenience function for tracking
def track_usage(
    tool: str,
    provider: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    duration_ms: int = 0,
) -> None:
    """Track a single LLM call (convenience function)."""
    get_usage_tracker().track(tool, provider, model, input_tokens, output_tokens, duration_ms)
