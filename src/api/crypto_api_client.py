"""
FreeCryptoAPI client wrapper for all 14 endpoints.
Handles HTTP requests with retry logic and error handling.
"""

from typing import Dict, List, Optional, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from config.api_config import FREECRYPTO_BASE_URL, ENDPOINTS, build_endpoint_url
from src.utils.logging_config import logger


class CryptoAPIClient:
    """Client for interacting with FreeCryptoAPI."""

    def __init__(self, base_url: str = None, timeout: int = 10):
        """
        Initialize API client.

        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or FREECRYPTO_BASE_URL
        self.timeout = timeout
        self.session = requests.Session()

        logger.info(f"CryptoAPI client initialized: {self.base_url}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _make_request(self, endpoint_name: str, params: Dict = None) -> Dict:
        """
        Make HTTP request with retry logic.

        Args:
            endpoint_name: Name of the endpoint
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            requests.RequestException: If request fails
        """
        url = build_endpoint_url(endpoint_name, params)

        logger.debug(f"Making request to: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Request successful: {endpoint_name}")
            return data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {endpoint_name}: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout for {endpoint_name}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {endpoint_name}: {e}")
            raise
        except ValueError as e:
            logger.error(f"JSON decode error for {endpoint_name}: {e}")
            raise

    # ===== Endpoint Methods =====

    def get_crypto_list(self) -> Dict:
        """
        Get list of all available cryptocurrencies.

        Returns:
            Dictionary with crypto list
        """
        return self._make_request('getCryptoList')

    def get_data(self, symbols: List[str] = None) -> Dict:
        """
        Get current price and market data for cryptocurrencies.

        Args:
            symbols: List of crypto symbols (e.g., ['BTC', 'ETH'])

        Returns:
            Dictionary with price data
        """
        params = {}
        if symbols:
            params['symbols'] = symbols if isinstance(symbols, str) else ','.join(symbols)

        return self._make_request('getData', params)

    def get_top(self, limit: int = 200) -> Dict:
        """
        Get top cryptocurrencies by market cap.

        Args:
            limit: Number of cryptocurrencies to return

        Returns:
            Dictionary with top cryptocurrencies
        """
        params = {'limit': limit}
        return self._make_request('getTop', params)

    def get_history(self, symbol: str, days: int = 30) -> Dict:
        """
        Get historical OHLCV data.

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC')
            days: Number of days of historical data

        Returns:
            Dictionary with historical data
        """
        params = {
            'symbol': symbol,
            'days': days
        }
        return self._make_request('getHistory', params)

    def get_technical_analysis(self, symbol: str) -> Dict:
        """
        Get technical indicators (RSI, MACD, etc.).

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            Dictionary with technical indicators
        """
        params = {'symbol': symbol}
        return self._make_request('getTechnicalAnalysis', params)

    def get_fear_greed(self) -> Dict:
        """
        Get current Fear & Greed Index.

        Returns:
            Dictionary with Fear & Greed Index data
        """
        return self._make_request('getFearGreed')

    def get_global_data(self) -> Dict:
        """
        Get global cryptocurrency market statistics.

        Returns:
            Dictionary with global market data
        """
        return self._make_request('getGlobalData')

    def get_trending(self) -> Dict:
        """
        Get currently trending cryptocurrencies.

        Returns:
            Dictionary with trending coins
        """
        return self._make_request('getTrending')

    def get_exchanges(self) -> Dict:
        """
        Get list of cryptocurrency exchanges.

        Returns:
            Dictionary with exchange data
        """
        return self._make_request('getExchanges')

    def get_news(self, limit: int = 10) -> Dict:
        """
        Get latest cryptocurrency news.

        Args:
            limit: Number of news articles

        Returns:
            Dictionary with news articles
        """
        params = {'limit': limit}
        return self._make_request('getNews', params)

    def get_social_sentiment(self, symbol: str) -> Dict:
        """
        Get social media sentiment data.

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            Dictionary with sentiment data
        """
        params = {'symbol': symbol}
        return self._make_request('getSocialSentiment', params)

    def get_defi_protocols(self) -> Dict:
        """
        Get DeFi protocol statistics.

        Returns:
            Dictionary with DeFi data
        """
        return self._make_request('getDefiProtocols')

    def get_nft_data(self) -> Dict:
        """
        Get NFT market data.

        Returns:
            Dictionary with NFT data
        """
        return self._make_request('getNFTData')

    def get_blockchain_stats(self, blockchain: str) -> Dict:
        """
        Get blockchain statistics.

        Args:
            blockchain: Blockchain name (e.g., 'bitcoin', 'ethereum')

        Returns:
            Dictionary with blockchain stats
        """
        params = {'blockchain': blockchain}
        return self._make_request('getBlockchainStats', params)

    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.debug("API client session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global API client instance
_api_client = None


def get_api_client() -> CryptoAPIClient:
    """Get or create global API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = CryptoAPIClient()
    return _api_client
