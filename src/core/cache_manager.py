"""
Unified caching mechanism using SQLite for API responses and metadata.
Implements LRU eviction with TTL support.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
from pathlib import Path
from config.settings import settings
from src.utils.logging_config import logger


class CacheManager:
    """Manages caching for API responses with TTL and LRU eviction."""

    def __init__(self, db_path: str = None, max_entries: int = 1000):
        """
        Initialize cache manager.

        Args:
            db_path: Path to SQLite database
            max_entries: Maximum number of cache entries (LRU eviction)
        """
        self.db_path = db_path or settings.sqlite_db_path
        self.max_entries = max_entries

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()
        logger.info(f"Cache manager initialized with database: {self.db_path}")

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # API cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL,
                params TEXT,
                response TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                hit_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index for expiration lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at ON api_cache(expires_at)
        """)

        # Index for LRU eviction
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed ON api_cache(last_accessed)
        """)

        # Metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kb_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kb_version TEXT NOT NULL,
                total_documents INTEGER,
                total_chunks INTEGER,
                embedding_model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rate limiting table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                api_name TEXT PRIMARY KEY,
                request_count INTEGER DEFAULT 0,
                reset_date DATE NOT NULL,
                monthly_limit INTEGER NOT NULL
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database schema initialized")

    def _generate_cache_key(self, endpoint: str, params: dict = None) -> str:
        """
        Generate cache key from endpoint and parameters.

        Args:
            endpoint: API endpoint name
            params: Query parameters

        Returns:
            MD5 hash as cache key
        """
        # Create deterministic string from endpoint and params
        key_string = endpoint
        if params:
            # Sort params for consistency
            sorted_params = json.dumps(params, sort_keys=True)
            key_string += sorted_params

        # Generate MD5 hash
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """
        Get cached response if available and not expired.

        Args:
            endpoint: API endpoint name
            params: Query parameters

        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._generate_cache_key(endpoint, params)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT response, expires_at
            FROM api_cache
            WHERE cache_key = ?
        """, (cache_key,))

        result = cursor.fetchone()

        if result is None:
            conn.close()
            logger.debug(f"Cache miss for endpoint: {endpoint}")
            return None

        response_json, expires_at = result
        expires_at_dt = datetime.fromisoformat(expires_at)

        # Check if expired
        if datetime.now() > expires_at_dt:
            # Delete expired entry
            cursor.execute("DELETE FROM api_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
            conn.close()
            logger.debug(f"Cache expired for endpoint: {endpoint}")
            return None

        # Update hit count and last accessed
        cursor.execute("""
            UPDATE api_cache
            SET hit_count = hit_count + 1,
                last_accessed = CURRENT_TIMESTAMP
            WHERE cache_key = ?
        """, (cache_key,))

        conn.commit()
        conn.close()

        logger.info(f"Cache hit for endpoint: {endpoint}")
        return json.loads(response_json)

    def set(self, endpoint: str, params: dict, response: dict, ttl: int):
        """
        Store response in cache with TTL.

        Args:
            endpoint: API endpoint name
            params: Query parameters
            response: API response to cache
            ttl: Time-to-live in seconds
        """
        cache_key = self._generate_cache_key(endpoint, params)
        expires_at = datetime.now() + timedelta(seconds=ttl)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check cache size and evict if necessary
        cursor.execute("SELECT COUNT(*) FROM api_cache")
        count = cursor.fetchone()[0]

        if count >= self.max_entries:
            # Evict least recently accessed entries
            cursor.execute("""
                DELETE FROM api_cache
                WHERE cache_key IN (
                    SELECT cache_key FROM api_cache
                    ORDER BY last_accessed ASC
                    LIMIT 100
                )
            """)
            logger.info("Evicted 100 LRU cache entries")

        # Insert or replace cache entry
        cursor.execute("""
            INSERT OR REPLACE INTO api_cache
            (cache_key, endpoint, params, response, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            cache_key,
            endpoint,
            json.dumps(params) if params else None,
            json.dumps(response),
            expires_at.isoformat()
        ))

        conn.commit()
        conn.close()

        logger.debug(f"Cached response for endpoint: {endpoint}, TTL: {ttl}s")

    def clear_expired(self):
        """Remove all expired cache entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM api_cache
            WHERE expires_at < CURRENT_TIMESTAMP
        """)

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cleared {deleted} expired cache entries")

    def clear_all(self):
        """Clear all cache entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM api_cache")

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cleared all {deleted} cache entries")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total entries
        cursor.execute("SELECT COUNT(*) FROM api_cache")
        total = cursor.fetchone()[0]

        # Expired entries
        cursor.execute("""
            SELECT COUNT(*) FROM api_cache
            WHERE expires_at < CURRENT_TIMESTAMP
        """)
        expired = cursor.fetchone()[0]

        # Total hits
        cursor.execute("SELECT SUM(hit_count) FROM api_cache")
        total_hits = cursor.fetchone()[0] or 0

        # Most accessed endpoints
        cursor.execute("""
            SELECT endpoint, SUM(hit_count) as hits
            FROM api_cache
            GROUP BY endpoint
            ORDER BY hits DESC
            LIMIT 5
        """)
        top_endpoints = cursor.fetchall()

        conn.close()

        return {
            "total_entries": total,
            "expired_entries": expired,
            "active_entries": total - expired,
            "total_hits": total_hits,
            "top_endpoints": [
                {"endpoint": ep, "hits": hits} for ep, hits in top_endpoints
            ]
        }


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
