"""
Tool orchestrator - routes queries to appropriate tools (KB vs API vs both).
Core decision-making component for the agent.
"""

from typing import Dict, List, Optional, Tuple
from src.rag.retriever import get_retriever
from src.rag.reranker import get_reranker
from src.api.api_orchestrator import get_api_orchestrator
from src.utils.logging_config import logger


class ToolOrchestrator:
    """Orchestrates tool selection and execution."""

    def __init__(self):
        """Initialize tool orchestrator."""
        self.retriever = get_retriever()
        self.reranker = get_reranker()
        self.api_orchestrator = get_api_orchestrator()

        logger.info("Tool orchestrator initialized")

    def route_query(self, query_analysis: Dict) -> Dict:
        """
        Determine which tools to use based on query analysis.

        Args:
            query_analysis: Query analysis from QueryProcessor

        Returns:
            Routing decision dictionary
        """
        query_type = query_analysis['query_type']
        needs_kb = query_analysis['needs_kb']
        needs_api = query_analysis['needs_api']
        symbols = query_analysis['symbols']

        routing = {
            'use_kb': False,
            'use_api': False,
            'strategy': None,
            'api_endpoints': []
        }

        # Route based on query type
        if query_type == 'conceptual':
            # Conceptual questions -> KB only
            routing['use_kb'] = True
            routing['strategy'] = 'kb_only'
            logger.info("Routing strategy: KB only (conceptual query)")

        elif query_type == 'real-time':
            # Real-time data -> API only
            routing['use_api'] = True
            routing['strategy'] = 'api_only'

            # Determine which API endpoints
            if symbols:
                routing['api_endpoints'].append('getData')
            else:
                routing['api_endpoints'].append('getTop')

            logger.info(f"Routing strategy: API only (real-time query, endpoints: {routing['api_endpoints']})")

        elif query_type == 'technical':
            # Technical analysis -> API + KB (for explanation)
            routing['use_kb'] = True
            routing['use_api'] = True
            routing['strategy'] = 'hybrid'
            routing['api_endpoints'].append('getTechnicalAnalysis')
            logger.info("Routing strategy: Hybrid (technical query)")

        elif query_type == 'historical':
            # Historical data -> API + KB
            routing['use_kb'] = True
            routing['use_api'] = True
            routing['strategy'] = 'hybrid'
            routing['api_endpoints'].append('getHistory')
            logger.info("Routing strategy: Hybrid (historical query)")

        else:
            # General queries -> Check KB first
            routing['use_kb'] = True
            routing['strategy'] = 'kb_first'
            logger.info("Routing strategy: KB first (general query)")

        return routing

    def execute_kb_retrieval(
        self,
        query: str,
        top_k: int = 5,
        use_reranking: bool = True
    ) -> List[Dict]:
        """
        Execute knowledge base retrieval.

        Args:
            query: Query string
            top_k: Number of results
            use_reranking: Whether to apply re-ranking

        Returns:
            List of retrieved and optionally re-ranked documents
        """
        logger.info(f"Executing KB retrieval for: '{query[:50]}...'")

        # Retrieve from KB
        results = self.retriever.retrieve(query, top_k=top_k * 2)  # Get more for re-ranking

        if not results:
            logger.warning("No KB results retrieved")
            return []

        # Re-rank if enabled
        if use_reranking and len(results) > 1:
            logger.info("Applying re-ranking")
            results = self.reranker.rerank(query, results, top_k=top_k)

        logger.info(f"KB retrieval complete: {len(results)} results")
        return results

    def execute_api_calls(
        self,
        endpoints: List[str],
        symbols: List[str] = None,
        params: Dict = None
    ) -> List[Dict]:
        """
        Execute API calls.

        Args:
            endpoints: List of endpoint names
            symbols: Crypto symbols (if applicable)
            params: Additional parameters

        Returns:
            List of API responses
        """
        responses = []

        for endpoint in endpoints:
            try:
                logger.info(f"Calling API endpoint: {endpoint}")

                if endpoint == 'getData' and symbols:
                    response = self.api_orchestrator.get_crypto_price(symbols[0])
                elif endpoint == 'getTop':
                    response = self.api_orchestrator.get_top_cryptocurrencies(limit=10)
                elif endpoint == 'getTechnicalAnalysis' and symbols:
                    response = self.api_orchestrator.get_technical_indicators(symbols[0])
                elif endpoint == 'getHistory' and symbols:
                    response = self.api_orchestrator.get_historical_data(symbols[0], days=30)
                elif endpoint == 'getFearGreed':
                    response = self.api_orchestrator.get_market_sentiment()
                elif endpoint == 'getGlobalData':
                    response = self.api_orchestrator.get_global_market_stats()
                elif endpoint == 'getTrending':
                    response = self.api_orchestrator.get_trending_coins()
                elif endpoint == 'getNews':
                    response = self.api_orchestrator.get_crypto_news(limit=5)
                else:
                    logger.warning(f"Unknown or unsupported endpoint: {endpoint}")
                    continue

                responses.append(response)
                logger.info(f"API call successful: {endpoint}")

            except Exception as e:
                logger.error(f"API call failed for {endpoint}: {e}")
                # Continue with other endpoints

        return responses

    def orchestrate(
        self,
        query_analysis: Dict,
        top_k_kb: int = 5
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Orchestrate tool execution based on routing decision.

        Args:
            query_analysis: Query analysis with routing info
            top_k_kb: Number of KB results to retrieve

        Returns:
            Tuple of (kb_results, api_responses)
        """
        query = query_analysis['resolved_query']
        symbols = query_analysis['symbols']

        # Determine routing
        routing = self.route_query(query_analysis)

        kb_results = []
        api_responses = []

        # Execute based on strategy
        if routing['use_kb']:
            kb_results = self.execute_kb_retrieval(query, top_k=top_k_kb)

        if routing['use_api']:
            api_responses = self.execute_api_calls(
                endpoints=routing['api_endpoints'],
                symbols=symbols
            )

        logger.info(f"Orchestration complete: {len(kb_results)} KB results, {len(api_responses)} API responses")

        return kb_results, api_responses


# Global tool orchestrator instance
_tool_orchestrator = None


def get_tool_orchestrator() -> ToolOrchestrator:
    """Get or create global tool orchestrator instance."""
    global _tool_orchestrator
    if _tool_orchestrator is None:
        _tool_orchestrator = ToolOrchestrator()
    return _tool_orchestrator
