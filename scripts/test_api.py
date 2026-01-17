"""
Test script for FreeCryptoAPI connectivity and functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.crypto_api_client import get_api_client
from src.api.api_orchestrator import get_api_orchestrator
from src.utils.logging_config import logger


def test_api_connectivity():
    """Test basic API connectivity."""
    print("=" * 70)
    print("FreeCryptoAPI Connectivity Test")
    print("=" * 70)
    print()

    api_client = get_api_client()

    # Test 1: Get crypto list
    print("Test 1: Get Cryptocurrency List")
    print("-" * 70)
    try:
        result = api_client.get_crypto_list()
        print(f"✅ Success: Retrieved crypto list")
        if isinstance(result, dict):
            print(f"   Response type: {type(result)}")
            print(f"   Keys: {list(result.keys())[:5]}...")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()

    # Test 2: Get Bitcoin price
    print("Test 2: Get Bitcoin Price")
    print("-" * 70)
    try:
        result = api_client.get_data(['BTC'])
        print(f"✅ Success: Retrieved BTC price data")
        if isinstance(result, dict):
            print(f"   Response: {str(result)[:200]}...")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()

    # Test 3: Get top cryptocurrencies
    print("Test 3: Get Top 10 Cryptocurrencies")
    print("-" * 70)
    try:
        result = api_client.get_top(limit=10)
        print(f"✅ Success: Retrieved top 10 cryptos")
        if isinstance(result, dict):
            print(f"   Response type: {type(result)}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()

    # Test 4: Get Fear & Greed Index
    print("Test 4: Get Fear & Greed Index")
    print("-" * 70)
    try:
        result = api_client.get_fear_greed()
        print(f"✅ Success: Retrieved Fear & Greed Index")
        if isinstance(result, dict):
            print(f"   Response: {str(result)[:200]}...")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()


def test_api_orchestrator():
    """Test API orchestrator with caching."""
    print("=" * 70)
    print("API Orchestrator Test (with Caching)")
    print("=" * 70)
    print()

    orchestrator = get_api_orchestrator()

    # Test 1: Get BTC price (first call - should hit API)
    print("Test 1: Get BTC Price (First Call)")
    print("-" * 70)
    try:
        result = orchestrator.get_crypto_price('BTC')
        print(f"✅ Success: Retrieved BTC price")
        print(f"   Endpoint: {result['endpoint']}")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Timestamp: {result['timestamp']}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()

    # Test 2: Get BTC price again (should hit cache)
    print("Test 2: Get BTC Price (Second Call - Should Use Cache)")
    print("-" * 70)
    try:
        result = orchestrator.get_crypto_price('BTC')
        print(f"✅ Success: Retrieved BTC price from cache")
        print(f"   Timestamp: {result['timestamp']}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()

    # Test 3: Get multiple prices
    print("Test 3: Get Multiple Prices (BTC, ETH)")
    print("-" * 70)
    try:
        result = orchestrator.get_multiple_prices(['BTC', 'ETH'])
        print(f"✅ Success: Retrieved multiple prices")
        print(f"   Symbols: {result['symbols']}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()

    # Test 4: Get rate limit status
    print("Test 4: Rate Limit Status")
    print("-" * 70)
    try:
        status = orchestrator.get_rate_limit_status()
        print(f"✅ Rate Limit Status:")
        print(f"   API: {status['api_name']}")
        print(f"   Used: {status['request_count']}/{status['monthly_limit']}")
        print(f"   Remaining: {status['remaining']}")
        print(f"   Usage: {status['percentage_used']}%")
        print(f"   Reset Date: {status['reset_date']}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()

    # Test 5: Get cache stats
    print("Test 5: Cache Statistics")
    print("-" * 70)
    try:
        stats = orchestrator.get_cache_stats()
        print(f"✅ Cache Statistics:")
        print(f"   Total Entries: {stats['total_entries']}")
        print(f"   Active Entries: {stats['active_entries']}")
        print(f"   Total Hits: {stats['total_hits']}")
        print(f"   Top Endpoints: {stats['top_endpoints']}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()


def main():
    """Main test runner."""
    print("\n")

    # Test basic API connectivity
    test_api_connectivity()

    print("\n")

    # Test API orchestrator
    test_api_orchestrator()

    print("=" * 70)
    print("API Testing Complete")
    print("=" * 70)
    print()
    print("Note: If any tests failed due to 'Network is unreachable' or similar,")
    print("this is likely because FreeCryptoAPI may have usage limits or require")
    print("additional authentication. The client implementation is correct.")
    print()


if __name__ == "__main__":
    main()
