"""
Rate limiter for FreeCryptoAPI using token bucket algorithm.
Tracks monthly usage and prevents exceeding limits.
"""

import sqlite3
from datetime import datetime, date
from typing import Optional
from config.settings import settings
from src.utils.logging_config import logger


class RateLimiter:
    """Token bucket rate limiter with persistent storage."""

    def __init__(
        self,
        api_name: str = "FreeCryptoAPI",
        monthly_limit: int = None,
        db_path: str = None
    ):
        """
        Initialize rate limiter.

        Args:
            api_name: Name of the API being rate limited
            monthly_limit: Maximum requests per month
            db_path: Path to SQLite database
        """
        self.api_name = api_name
        self.monthly_limit = monthly_limit or settings.freecrypto_monthly_limit
        self.db_path = db_path or settings.sqlite_db_path

        # Initialize database
        self._init_db()

        # Get or create rate limit entry
        self._init_rate_limit()

        logger.info(f"Rate limiter initialized for {api_name} ({self.monthly_limit}/month)")

    def _init_db(self):
        """Initialize database schema (if not exists)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Rate limits table (created in cache_manager, but ensure it exists)
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

    def _init_rate_limit(self):
        """Initialize or reset rate limit entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = date.today()
        first_of_month = date(today.year, today.month, 1)

        # Check if entry exists
        cursor.execute("""
            SELECT request_count, reset_date FROM rate_limits
            WHERE api_name = ?
        """, (self.api_name,))

        result = cursor.fetchone()

        if result is None:
            # Create new entry
            cursor.execute("""
                INSERT INTO rate_limits (api_name, request_count, reset_date, monthly_limit)
                VALUES (?, 0, ?, ?)
            """, (self.api_name, first_of_month.isoformat(), self.monthly_limit))
            logger.info(f"Created new rate limit entry for {self.api_name}")

        else:
            # Check if we need to reset (new month)
            request_count, reset_date_str = result
            reset_date = date.fromisoformat(reset_date_str)

            if today >= reset_date:
                # Calculate next reset date (first day of next month)
                if today.month == 12:
                    next_reset = date(today.year + 1, 1, 1)
                else:
                    next_reset = date(today.year, today.month + 1, 1)

                # Reset counter
                cursor.execute("""
                    UPDATE rate_limits
                    SET request_count = 0, reset_date = ?
                    WHERE api_name = ?
                """, (next_reset.isoformat(), self.api_name))

                logger.info(f"Reset rate limit for {self.api_name}. Next reset: {next_reset}")

        conn.commit()
        conn.close()

    def check_limit(self) -> bool:
        """
        Check if request is allowed under rate limit.

        Returns:
            True if request is allowed, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT request_count, monthly_limit FROM rate_limits
            WHERE api_name = ?
        """, (self.api_name,))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            logger.error(f"No rate limit entry for {self.api_name}")
            return False

        request_count, monthly_limit = result

        allowed = request_count < monthly_limit

        if not allowed:
            logger.warning(f"Rate limit exceeded for {self.api_name}: {request_count}/{monthly_limit}")

        return allowed

    def increment(self) -> int:
        """
        Increment request counter.

        Returns:
            New request count
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rate_limits
            SET request_count = request_count + 1
            WHERE api_name = ?
        """, (self.api_name,))

        cursor.execute("""
            SELECT request_count FROM rate_limits
            WHERE api_name = ?
        """, (self.api_name,))

        new_count = cursor.fetchone()[0]

        conn.commit()
        conn.close()

        logger.debug(f"Rate limit incremented for {self.api_name}: {new_count}/{self.monthly_limit}")

        # Warning at 80%
        if new_count >= self.monthly_limit * 0.8:
            logger.warning(f"Rate limit at 80% for {self.api_name}: {new_count}/{self.monthly_limit}")

        return new_count

    def get_usage(self) -> dict:
        """
        Get current usage statistics.

        Returns:
            Dictionary with usage stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT request_count, reset_date, monthly_limit FROM rate_limits
            WHERE api_name = ?
        """, (self.api_name,))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            return {
                'api_name': self.api_name,
                'request_count': 0,
                'monthly_limit': self.monthly_limit,
                'remaining': self.monthly_limit,
                'percentage_used': 0,
                'reset_date': None
            }

        request_count, reset_date, monthly_limit = result

        return {
            'api_name': self.api_name,
            'request_count': request_count,
            'monthly_limit': monthly_limit,
            'remaining': monthly_limit - request_count,
            'percentage_used': round((request_count / monthly_limit) * 100, 2),
            'reset_date': reset_date
        }

    def reset(self):
        """Reset rate limit counter (for testing)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rate_limits
            SET request_count = 0
            WHERE api_name = ?
        """, (self.api_name,))

        conn.commit()
        conn.close()

        logger.info(f"Rate limit reset for {self.api_name}")


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
