"""
Response generator - generates LLM responses with strict hallucination prevention.
Uses Gemini API with carefully crafted prompts.
"""

from typing import Dict, List, Optional, Generator
from src.core.llm_client import get_gemini_client
from src.rag.context_builder import get_context_builder
from src.rag.hallucination_guard import get_hallucination_guard
from config.prompts import SYSTEM_PROMPT, REFUSAL_OUT_OF_SCOPE, REFUSAL_NO_KB_MATCH
from src.utils.logging_config import logger


class ResponseGenerator:
    """Generates responses using LLM with hallucination prevention."""

    def __init__(self):
        """Initialize response generator."""
        self.llm_client = get_gemini_client()
        self.context_builder = get_context_builder()
        self.hallucination_guard = get_hallucination_guard()

        logger.info("Response generator initialized")

    def generate(
        self,
        query: str,
        kb_chunks: List[Dict] = None,
        api_responses: List[Dict] = None,
        conversation_history: List[Dict] = None,
        stream: bool = False
    ) -> Dict:
        """
        Generate response with hallucination prevention.

        Args:
            query: User query
            kb_chunks: Knowledge base chunks
            api_responses: API response data
            conversation_history: Conversation history
            stream: Whether to stream response

        Returns:
            Response dictionary with text, sources, and validation
        """
        logger.info(f"Generating response for query: '{query[:50]}...'")

        # Run hallucination guard validation (pre-generation)
        validation = self.hallucination_guard.validate_pipeline(
            query=query,
            kb_chunks=kb_chunks,
            api_responses=api_responses
        )

        # Check if we should refuse
        if validation['should_refuse']:
            logger.warning(f"Refusing to answer: {validation['refusal_reason']}")

            return {
                'text': self._generate_refusal(validation['refusal_reason'], kb_chunks),
                'sources': [],
                'validation': validation,
                'refused': True
            }

        # Build context
        context = self.context_builder.build_full_context(
            query=query,
            kb_chunks=kb_chunks,
            api_responses=api_responses,
            conversation_history=conversation_history
        )

        # Generate response
        try:
            if stream:
                response_text = self._generate_streaming(context)
            else:
                response_text = self._generate_complete(context)

            # Post-generation validation
            response_valid, reason, confidence = self.hallucination_guard.validate_response(
                response_text,
                kb_chunks=kb_chunks,
                api_responses=api_responses
            )

            # Extract sources
            sources = self.context_builder.extract_sources_from_context(
                kb_chunks=kb_chunks,
                api_responses=api_responses
            )

            # Update validation
            validation['confidence'] = confidence
            validation['overall_valid'] = validation['overall_valid'] and response_valid

            logger.info(f"Response generated (valid: {response_valid}, confidence: {confidence:.2f})")

            return {
                'text': response_text,
                'sources': sources,
                'validation': validation,
                'refused': False,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")

            return {
                'text': "I encountered an error while generating a response. Please try again.",
                'sources': [],
                'validation': validation,
                'refused': False,
                'error': str(e)
            }

    def _generate_complete(self, context: str) -> str:
        """
        Generate complete response (non-streaming).

        Args:
            context: Full context string

        Returns:
            Generated response text
        """
        # Combine system prompt and context
        full_prompt = f"{SYSTEM_PROMPT}\n\n{context}"

        response = self.llm_client.generate(full_prompt)

        return response

    def _generate_streaming(self, context: str) -> str:
        """
        Generate streaming response.

        Args:
            context: Full context string

        Returns:
            Complete response text (accumulated from stream)
        """
        full_prompt = f"{SYSTEM_PROMPT}\n\n{context}"

        response_chunks = []

        for chunk in self.llm_client.generate_stream(full_prompt):
            response_chunks.append(chunk)

        return ''.join(response_chunks)

    def generate_stream(
        self,
        query: str,
        kb_chunks: List[Dict] = None,
        api_responses: List[Dict] = None,
        conversation_history: List[Dict] = None
    ) -> Generator[str, None, None]:
        """
        Generate streaming response (yields chunks).

        Args:
            query: User query
            kb_chunks: KB chunks
            api_responses: API responses
            conversation_history: Conversation history

        Yields:
            Response text chunks
        """
        logger.info(f"Generating streaming response for: '{query[:50]}...'")

        # Validation
        validation = self.hallucination_guard.validate_pipeline(
            query=query,
            kb_chunks=kb_chunks,
            api_responses=api_responses
        )

        if validation['should_refuse']:
            refusal = self._generate_refusal(validation['refusal_reason'], kb_chunks)
            yield refusal
            return

        # Build context
        context = self.context_builder.build_full_context(
            query=query,
            kb_chunks=kb_chunks,
            api_responses=api_responses,
            conversation_history=conversation_history
        )

        # Stream response
        full_prompt = f"{SYSTEM_PROMPT}\n\n{context}"

        for chunk in self.llm_client.generate_stream(full_prompt):
            yield chunk

    def _generate_refusal(self, reason: str, kb_chunks: List[Dict] = None) -> str:
        """
        Generate refusal message.

        Args:
            reason: Refusal reason
            kb_chunks: KB chunks (to suggest alternatives)

        Returns:
            Refusal message
        """
        # Check reason type
        if 'out of scope' in reason.lower() or 'not.*related' in reason.lower():
            return REFUSAL_OUT_OF_SCOPE

        # No KB matches
        if kb_chunks:
            # Suggest related topics
            categories = set(chunk['metadata'].get('category', '') for chunk in kb_chunks)
            suggested = ', '.join(categories) if categories else 'Bitcoin, Ethereum, DeFi, Blockchain'

            return REFUSAL_NO_KB_MATCH.format(suggested_topics=suggested)

        # Generic refusal
        return f"I don't have verified information about that topic. {reason}"


# Global response generator instance
_response_generator = None


def get_response_generator() -> ResponseGenerator:
    """Get or create global response generator instance."""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator
