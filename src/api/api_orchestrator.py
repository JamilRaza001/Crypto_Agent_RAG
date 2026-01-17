"""
API orchestrator that routes requests, manages caching, and handles rate limiting.
Provides high-level interface for crypto data retrieval.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from config.api_config import ENDPOINTS, get_endpoint_config
from src.api.crypto_api_client import get_api_client
from src.api.rate_limiter import get_rate_limiter
from src.core.cache_manager import get_cache_manager
from src.utils.logging_config import logger


class APIOrchestrator:
    """Orchestrates API calls with caching and rate limiting."""

    def __init__(self):
        """Initialize API orchestrator."""
        self.api_client = get_api_client()
        self.rate_limiter = get_rate_limiter()
        self.cache_manager = get_cache_manager()

        logger.info("API orchestrator initialized")

    def _get_with_cache(
        self,
        endpoint_name: str,
        params: Dict = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Get data from API with caching and rate limiting.

        Args:
            endpoint_name: Name of the endpoint
            params: Query parameters
            use_cache: Whether to use cache

        Returns:
            API response data
        """
        # Check cache first
        if use_cache:
            cached = self.cache_manager.get(endpoint_name, params)
            if cached:
                logger.info(f"Cache hit for {endpoint_name}")
                return cached

        # Check rate limit
        if not self.rate_limiter.check_limit():
            logger.warning(f"Rate limit exceeded, using stale cache if available")
            # Try to get stale cache (ignore TTL)
            # For now, just raise an error
            raise Exception(f"Rate limit exceeded for {endpoint_name}")

        # Make API request
        logger.info(f"Making API request to {endpoint_name}")

        try:
            # Call the appropriate client method
            client_method = getattr(self.api_client, f"get_{endpoint_name.replace('get', '').lower()}", None)

            if client_method is None:
                raise ValueError(f"Unknown endpoint: {endpoint_name}")

            # Call with params if provided
            if params:
                response = client_method(**params)
            else:
                response = client_method()

            # Increment rate limit
            self.rate_limiter.increment()

            # Cache the response
            endpoint_config = get_endpoint_config(endpoint_name)
            ttl = endpoint_config['ttl']

            self.cache_manager.set(endpoint_name, params or {}, response, ttl)

            logger.info(f"API request successful: {endpoint_name}, cached with TTL={ttl}s")

            return response

        except Exception as e:
            logger.error(f"API request failed for {endpoint_name}: {e}")
            raise

    # ===== High-level API methods =====

    def get_crypto_price(self, symbol: str) -> Dict:
        """
        Get current price for a cryptocurrency.

        Args:
            symbol: Crypto symbol (e.g., 'BTC')

        Returns:
            Price data with timestamp
        """
        response = self._get_with_cache('getData', {'symbols': [symbol]})

        return {
            'endpoint': 'getData',
            'symbol': symbol,
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_multiple_prices(self, symbols: List[str]) -> Dict:
        """
        Get prices for multiple cryptocurrencies.

        Args:
            symbols: List of crypto symbols

        Returns:
            Price data for all symbols
        """
        response = self._get_with_cache('getData', {'symbols': symbols})

        return {
            'endpoint': 'getData',
            'symbols': symbols,
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_top_cryptocurrencies(self, limit: int = 10) -> Dict:
        """
        Get top cryptocurrencies by market cap.

        Args:
            limit: Number of cryptocurrencies

        Returns:
            Top crypto data
        """
        response = self._get_with_cache('getTop', {'limit': limit})

        return {
            'endpoint': 'getTop',
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_historical_data(self, symbol: str, days: int = 30) -> Dict:
        """
        Get historical price data.

        Args:
            symbol: Crypto symbol
            days: Number of days

        Returns:
            Historical data
        """
        response = self._get_with_cache('getHistory', {'symbol': symbol, 'days': days})

        return {
            'endpoint': 'getHistory',
            'symbol': symbol,
            'days': days,
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_technical_indicators(self, symbol: str) -> Dict:
        """
        Get technical analysis indicators.

        Args:
            symbol: Crypto symbol

        Returns:
            Technical indicators (RSI, MACD, etc.)
        """
        response = self._get_with_cache('getTechnicalAnalysis', {'symbol': symbol})

        return {
            'endpoint': 'getTechnicalAnalysis',
            'symbol': symbol,
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_market_sentiment(self) -> Dict:
        """
        Get Fear & Greed Index for market sentiment.

        Returns:
            Fear & Greed Index data
        """
        response = self._get_with_cache('getFearGreed')

        return {
            'endpoint': 'getFearGreed',
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_global_market_stats(self) -> Dict:
        """
        Get global cryptocurrency market statistics.

        Returns:
            Global market data
        """
        response = self._get_with_cache('getGlobalData')

        return {
            'endpoint': 'getGlobalData',
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_trending_coins(self) -> Dict:
        """
        Get currently trending cryptocurrencies.

        Returns:
            Trending coins data
        """
        response = self._get_with_cache('getTrending')

        return {
            'endpoint': 'getTrending',
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_crypto_news(self, limit: int = 10) -> Dict:
        """
        Get latest cryptocurrency news.

        Args:
            limit: Number of news articles

        Returns:
            News data
        """
        response = self._get_with_cache('getNews', {'limit': limit})

        return {
            'endpoint': 'getNews',
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_social_data(self, symbol: str) -> Dict:
        """
        Get social media sentiment.

        Args:
            symbol: Crypto symbol

        Returns:
            Social sentiment data
        """
        response = self._get_with_cache('getSocialSentiment', {'symbol': symbol})

        return {
            'endpoint': 'getSocialSentiment',
            'symbol': symbol,
            'data': response,
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_rate_limit_status(self) -> Dict:
        """
        Get current rate limit usage.

        Returns:
            Rate limit statistics
        """
        return self.rate_limiter.get_usage()

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Cache statistics
        """
        return self.cache_manager.get_stats()

    def clear_cache(self):
        """Clear all cached API responses."""
        self.cache_manager.clear_all()
        logger.info("API cache cleared")

    def clear_expired_cache(self):
        """Clear expired cache entries."""
        self.cache_manager.clear_expired()
        logger.info("Expired cache entries cleared")


# Global API orchestrator instance
_api_orchestrator = None


def get_api_orchestrator() -> APIOrchestrator:
    """Get or create global API orchestrator instance."""
    global _api_orchestrator
    if _api_orchestrator is None:
        _api_orchestrator = APIOrchestrator()
    return _api_orchestrator
