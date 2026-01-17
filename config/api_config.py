"""
FreeCryptoAPI endpoint configurations and definitions.
"""

# Base URL for FreeCryptoAPI
FREECRYPTO_BASE_URL = "https://freecryptoapi.com/api/v1"

# Endpoint definitions with their TTL (cache time-to-live in seconds)
ENDPOINTS = {
    # List all available cryptocurrencies
    "getCryptoList": {
        "path": "/getCryptoList",
        "method": "GET",
        "ttl": 86400,  # 24 hours (relatively static data)
        "description": "Get list of all available cryptocurrencies"
    },

    # Get real-time data for specific symbols
    "getData": {
        "path": "/getData",
        "method": "GET",
        "ttl": 60,  # 1 minute (price data)
        "description": "Get current price and market data for cryptocurrencies",
        "params": ["symbols"]  # Required: symbols (e.g., "BTC,ETH")
    },

    # Get top cryptocurrencies by market cap
    "getTop": {
        "path": "/getTop",
        "method": "GET",
        "ttl": 300,  # 5 minutes
        "description": "Get top cryptocurrencies by market cap",
        "params": ["limit"]  # Optional: limit (default 200)
    },

    # Get historical price data
    "getHistory": {
        "path": "/getHistory",
        "method": "GET",
        "ttl": 3600,  # 1 hour (historical data doesn't change)
        "description": "Get historical OHLCV data",
        "params": ["symbol", "days"]  # Required: symbol, Optional: days
    },

    # Get technical analysis indicators
    "getTechnicalAnalysis": {
        "path": "/getTechnicalAnalysis",
        "method": "GET",
        "ttl": 300,  # 5 minutes
        "description": "Get technical indicators (RSI, MACD, etc.)",
        "params": ["symbol"]  # Required: symbol
    },

    # Get Fear & Greed Index
    "getFearGreed": {
        "path": "/getFearGreed",
        "method": "GET",
        "ttl": 3600,  # 1 hour
        "description": "Get current Fear & Greed Index"
    },

    # Get global crypto market data
    "getGlobalData": {
        "path": "/getGlobalData",
        "method": "GET",
        "ttl": 300,  # 5 minutes
        "description": "Get global cryptocurrency market statistics"
    },

    # Get trending cryptocurrencies
    "getTrending": {
        "path": "/getTrending",
        "method": "GET",
        "ttl": 600,  # 10 minutes
        "description": "Get currently trending cryptocurrencies"
    },

    # Get exchange information
    "getExchanges": {
        "path": "/getExchanges",
        "method": "GET",
        "ttl": 3600,  # 1 hour
        "description": "Get list of cryptocurrency exchanges"
    },

    # Get news articles
    "getNews": {
        "path": "/getNews",
        "method": "GET",
        "ttl": 600,  # 10 minutes
        "description": "Get latest cryptocurrency news",
        "params": ["limit"]  # Optional: limit
    },

    # Get social media sentiment
    "getSocialSentiment": {
        "path": "/getSocialSentiment",
        "method": "GET",
        "ttl": 600,  # 10 minutes
        "description": "Get social media sentiment data",
        "params": ["symbol"]  # Required: symbol
    },

    # Get DeFi protocols data
    "getDefiProtocols": {
        "path": "/getDefiProtocols",
        "method": "GET",
        "ttl": 3600,  # 1 hour
        "description": "Get DeFi protocol statistics"
    },

    # Get NFT data
    "getNFTData": {
        "path": "/getNFTData",
        "method": "GET",
        "ttl": 600,  # 10 minutes
        "description": "Get NFT market data"
    },

    # Get blockchain statistics
    "getBlockchainStats": {
        "path": "/getBlockchainStats",
        "method": "GET",
        "ttl": 600,  # 10 minutes
        "description": "Get blockchain statistics",
        "params": ["blockchain"]  # Required: blockchain name
    }
}

# Common cryptocurrency symbol mappings
SYMBOL_ALIASES = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "ethereum": "ETH",
    "eth": "ETH",
    "ether": "ETH",
    "binance coin": "BNB",
    "bnb": "BNB",
    "cardano": "ADA",
    "ada": "ADA",
    "ripple": "XRP",
    "xrp": "XRP",
    "solana": "SOL",
    "sol": "SOL",
    "polkadot": "DOT",
    "dot": "DOT",
    "dogecoin": "DOGE",
    "doge": "DOGE",
    "avalanche": "AVAX",
    "avax": "AVAX",
    "polygon": "MATIC",
    "matic": "MATIC",
    "litecoin": "LTC",
    "ltc": "LTC",
    "chainlink": "LINK",
    "link": "LINK",
    "tron": "TRX",
    "trx": "TRX",
    "stellar": "XLM",
    "xlm": "XLM"
}


def get_endpoint_config(endpoint_name: str) -> dict:
    """Get configuration for a specific endpoint."""
    if endpoint_name not in ENDPOINTS:
        raise ValueError(f"Unknown endpoint: {endpoint_name}")
    return ENDPOINTS[endpoint_name]


def normalize_symbol(symbol: str) -> str:
    """Normalize cryptocurrency symbol (e.g., 'bitcoin' -> 'BTC')."""
    symbol_lower = symbol.lower().strip()
    return SYMBOL_ALIASES.get(symbol_lower, symbol.upper())


def build_endpoint_url(endpoint_name: str, params: dict = None) -> str:
    """
    Build full URL for an endpoint with parameters.

    Args:
        endpoint_name: Name of the endpoint (e.g., 'getData')
        params: Dictionary of query parameters

    Returns:
        Full URL string
    """
    config = get_endpoint_config(endpoint_name)
    url = f"{FREECRYPTO_BASE_URL}{config['path']}"

    if params:
        # Normalize symbols if present
        if 'symbols' in params:
            symbols = params['symbols']
            if isinstance(symbols, list):
                params['symbols'] = ','.join([normalize_symbol(s) for s in symbols])
            else:
                params['symbols'] = normalize_symbol(params['symbols'])

        if 'symbol' in params:
            params['symbol'] = normalize_symbol(params['symbol'])

        # Build query string
        query_parts = [f"{k}={v}" for k, v in params.items()]
        url += "?" + "&".join(query_parts)

    return url
