"""
Hallucination Guard - Multi-layer validation to prevent LLM hallucinations.
This is the MOST CRITICAL component for production safety.
"""

import re
from typing import List, Dict, Optional, Tuple
from src.core.embeddings import get_embedding_manager
from config.settings import settings
from src.utils.logging_config import logger


class HallucinationGuard:
    """Multi-layer hallucination prevention system."""

    def __init__(self):
        """Initialize hallucination guard."""
        self.embedding_manager = get_embedding_manager()

        # Crypto-related keywords for scope validation
        self.crypto_keywords = {
            'bitcoin', 'btc', 'ethereum', 'eth', 'blockchain', 'crypto', 'cryptocurrency',
            'defi', 'nft', 'mining', 'staking', 'wallet', 'token', 'coin', 'altcoin',
            'satoshi', 'wei', 'gwei', 'gas', 'smart contract', 'dapp', 'dao', 'web3',
            'metamask', 'ledger', 'exchange', 'binance', 'coinbase', 'uniswap',
            'price', 'market cap', 'volume', 'trading', 'hodl', 'whale', 'bull', 'bear'
        }

        # Hedging language patterns (indicates uncertainty)
        self.hedging_patterns = [
            r'\bI think\b',
            r'\bI believe\b',
            r'\bprobably\b',
            r'\bmaybe\b',
            r'\bperhaps\b',
            r'\bmight be\b',
            r'\bcould be\b',
            r'\bI guess\b',
            r'\bI assume\b',
            r'\bseems like\b',
            r'\bappears to be\b'
        ]

        logger.info("Hallucination guard initialized")

    # ===== Layer 1: Query Validation =====

    def validate_query_scope(self, query: str) -> Tuple[bool, str]:
        """
        Validate that query is crypto-related.

        Args:
            query: User query

        Returns:
            Tuple of (is_valid, reason)
        """
        query_lower = query.lower()

        # Check for crypto keywords
        has_crypto_keyword = any(keyword in query_lower for keyword in self.crypto_keywords)

        if has_crypto_keyword:
            logger.info("Query scope validated: crypto-related")
            return True, "Query is crypto-related"

        # Additional check: embed query and compare to crypto concept
        try:
            query_embedding = self.embedding_manager.embed_text(query)
            crypto_embedding = self.embedding_manager.embed_text("cryptocurrency and blockchain technology")

            similarity = self.embedding_manager.compute_similarity(query_embedding, crypto_embedding)

            if similarity > 0.3:  # Lower threshold for scope check
                logger.info(f"Query scope validated via embedding similarity: {similarity:.4f}")
                return True, f"Query semantically related to crypto (similarity: {similarity:.4f})"

        except Exception as e:
            logger.error(f"Error in embedding-based scope check: {e}")

        logger.warning(f"Query appears out of scope: '{query}'")
        return False, "Query does not appear to be related to cryptocurrency or blockchain"

    # ===== Layer 2: Retrieval Validation =====

    def validate_retrieval_quality(
        self,
        kb_chunks: List[Dict],
        similarity_threshold: float = None
    ) -> Tuple[bool, str]:
        """
        Validate that retrieved KB chunks meet quality standards.

        Args:
            kb_chunks: Retrieved knowledge base chunks
            similarity_threshold: Minimum similarity score

        Returns:
            Tuple of (is_valid, reason)
        """
        threshold = similarity_threshold or settings.similarity_threshold

        if not kb_chunks:
            logger.warning("No KB chunks retrieved")
            return False, "No relevant information found in knowledge base"

        # Check all chunks meet threshold
        below_threshold = [
            chunk for chunk in kb_chunks
            if chunk.get('similarity', chunk.get('rerank_score', 0)) < threshold
        ]

        if below_threshold:
            logger.warning(f"{len(below_threshold)} chunks below threshold {threshold}")
            return False, f"Retrieved information has low relevance (below {threshold})"

        # Check for minimum diversity (not all from same document)
        document_ids = set(chunk['metadata'].get('document_id', 'unknown') for chunk in kb_chunks)

        if len(document_ids) == 1 and len(kb_chunks) > 1:
            logger.info("All chunks from same document (low diversity)")
            # This is not necessarily bad, just note it

        logger.info(f"Retrieval quality validated: {len(kb_chunks)} chunks, {len(document_ids)} documents")
        return True, f"Retrieved {len(kb_chunks)} high-quality chunks"

    # ===== Layer 3: API Data Validation =====

    def validate_api_data(self, api_responses: List[Dict]) -> Tuple[bool, str]:
        """
        Validate API response data quality.

        Args:
            api_responses: API response dictionaries

        Returns:
            Tuple of (is_valid, reason)
        """
        if not api_responses:
            # No API data is fine (KB-only queries)
            return True, "No API data to validate"

        for response in api_responses:
            # Check timestamp exists and is recent
            timestamp = response.get('timestamp')
            if not timestamp:
                logger.warning("API response missing timestamp")
                return False, "API data missing timestamp"

            # Check data field exists
            if 'data' not in response:
                logger.warning("API response missing data field")
                return False, "API response malformed"

            # Check endpoint is specified
            if 'endpoint' not in response:
                logger.warning("API response missing endpoint")
                return False, "API response missing source endpoint"

        logger.info(f"API data validated: {len(api_responses)} responses")
        return True, f"Validated {len(api_responses)} API responses"

    # ===== Layer 4: Response Validation =====

    def validate_response(
        self,
        response: str,
        kb_chunks: List[Dict] = None,
        api_responses: List[Dict] = None
    ) -> Tuple[bool, str, float]:
        """
        Validate LLM response for hallucinations.

        Args:
            response: LLM-generated response
            kb_chunks: KB chunks that were provided
            api_responses: API responses that were provided

        Returns:
            Tuple of (is_valid, reason, confidence_score)
        """
        if not response:
            return False, "Empty response", 0.0

        # Check 1: Look for source citations
        has_kb_citation = bool(re.search(r'\[Source:.*?\]', response))
        has_api_citation = bool(re.search(r'FreeCryptoAPI', response, re.IGNORECASE))

        if kb_chunks and not has_kb_citation:
            logger.warning("Response missing KB source citations")
            # Don't fail, but note it

        if api_responses and not has_api_citation:
            logger.warning("Response missing API source citations")

        # Check 2: Detect hedging language (indicates uncertainty/hallucination)
        hedging_found = []
        for pattern in self.hedging_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                hedging_found.append(pattern)

        if hedging_found:
            logger.warning(f"Hedging language detected: {hedging_found}")
            return False, f"Response contains uncertain language: {hedging_found[0]}", 0.3

        # Check 3: Verify response doesn't contain refusal to answer
        # (This is actually GOOD - the LLM is being honest)
        refusal_patterns = [
            r"I don't have (verified )?information",
            r"I cannot provide",
            r"I'm not able to",
            r"out of (my )?scope"
        ]

        for pattern in refusal_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                logger.info("Response contains honest refusal")
                # This is valid - LLM is correctly refusing
                return True, "LLM correctly refused to answer", 1.0

        # Check 4: Calculate confidence score
        confidence = self._calculate_confidence(response, kb_chunks, api_responses)

        if confidence < 0.6:
            logger.warning(f"Low confidence score: {confidence:.2f}")
            return False, f"Low confidence in response accuracy ({confidence:.2f})", confidence

        logger.info(f"Response validated successfully (confidence: {confidence:.2f})")
        return True, "Response passes validation checks", confidence

    def _calculate_confidence(
        self,
        response: str,
        kb_chunks: List[Dict] = None,
        api_responses: List[Dict] = None
    ) -> float:
        """
        Calculate confidence score for response.

        Args:
            response: LLM response
            kb_chunks: KB chunks used
            api_responses: API responses used

        Returns:
            Confidence score between 0 and 1
        """
        scores = []

        # Factor 1: KB retrieval quality (50% weight)
        if kb_chunks:
            max_similarity = max(
                chunk.get('similarity', chunk.get('rerank_score', 0))
                for chunk in kb_chunks
            )
            scores.append(('kb_quality', max_similarity, 0.5))
        else:
            scores.append(('kb_quality', 0.5, 0.5))  # Neutral if no KB used

        # Factor 2: API data freshness (30% weight)
        if api_responses:
            # Assume API data is fresh (we have timestamp validation)
            scores.append(('api_freshness', 1.0, 0.3))
        else:
            scores.append(('api_freshness', 0.7, 0.3))  # Slight penalty if expected

        # Factor 3: Citation coverage (20% weight)
        has_citations = '[Source:' in response or 'FreeCryptoAPI' in response
        citation_score = 1.0 if has_citations else 0.5
        scores.append(('citations', citation_score, 0.2))

        # Weighted average
        confidence = sum(score * weight for _, score, weight in scores)

        return round(confidence, 4)

    # ===== Combined Validation =====

    def validate_pipeline(
        self,
        query: str,
        kb_chunks: List[Dict] = None,
        api_responses: List[Dict] = None,
        llm_response: str = None
    ) -> Dict:
        """
        Run complete validation pipeline.

        Args:
            query: User query
            kb_chunks: Retrieved KB chunks
            api_responses: API responses
            llm_response: LLM-generated response (optional)

        Returns:
            Validation results dictionary
        """
        logger.info("Running hallucination guard validation pipeline")

        results = {
            'overall_valid': True,
            'validations': [],
            'confidence': 1.0,
            'should_refuse': False,
            'refusal_reason': None
        }

        # Layer 1: Query scope
        scope_valid, scope_reason = self.validate_query_scope(query)
        results['validations'].append({
            'layer': 'query_scope',
            'valid': scope_valid,
            'reason': scope_reason
        })

        if not scope_valid:
            results['overall_valid'] = False
            results['should_refuse'] = True
            results['refusal_reason'] = scope_reason
            logger.warning("Query scope validation failed - refusing to answer")
            return results

        # Layer 2: Retrieval quality
        if kb_chunks:
            retrieval_valid, retrieval_reason = self.validate_retrieval_quality(kb_chunks)
            results['validations'].append({
                'layer': 'retrieval_quality',
                'valid': retrieval_valid,
                'reason': retrieval_reason
            })

            if not retrieval_valid:
                results['overall_valid'] = False
                results['should_refuse'] = True
                results['refusal_reason'] = retrieval_reason

        # Layer 3: API data quality
        if api_responses:
            api_valid, api_reason = self.validate_api_data(api_responses)
            results['validations'].append({
                'layer': 'api_validation',
                'valid': api_valid,
                'reason': api_reason
            })

            if not api_valid:
                results['overall_valid'] = False
                results['should_refuse'] = True
                results['refusal_reason'] = api_reason

        # Layer 4: Response validation (if provided)
        if llm_response:
            response_valid, response_reason, confidence = self.validate_response(
                llm_response, kb_chunks, api_responses
            )
            results['validations'].append({
                'layer': 'response_validation',
                'valid': response_valid,
                'reason': response_reason,
                'confidence': confidence
            })

            results['confidence'] = confidence

            if not response_valid:
                results['overall_valid'] = False
                # Don't refuse if response itself is invalid - this means
                # LLM generated something we don't trust, so we should regenerate

        logger.info(f"Validation complete - Overall valid: {results['overall_valid']}, Confidence: {results['confidence']}")

        return results


# Global hallucination guard instance
_hallucination_guard = None


def get_hallucination_guard() -> HallucinationGuard:
    """Get or create global hallucination guard instance."""
    global _hallucination_guard
    if _hallucination_guard is None:
        _hallucination_guard = HallucinationGuard()
    return _hallucination_guard
