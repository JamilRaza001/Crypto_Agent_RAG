"""
Google Gemini API client with retry logic and streaming support.
"""

from typing import Generator, Optional
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings
from src.utils.logging_config import logger


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, api_key: str = None, model_name: str = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Google Gemini API key
            model_name: Model to use (default: gemini-1.5-flash)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        # Initialize model with safety settings
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": settings.temperature,
                "max_output_tokens": settings.max_tokens,
            },
            # Disable safety filters for crypto content (sometimes flagged)
            safety_settings={
                "HARASSMENT": "BLOCK_NONE",
                "HATE_SPEECH": "BLOCK_NONE",
                "SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )

        logger.info(f"Gemini client initialized with model: {self.model_name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generate response from Gemini API with retry logic.

        Args:
            prompt: User prompt
            system_instruction: System instruction (optional)

        Returns:
            Generated response text
        """
        try:
            # Create full prompt with system instruction if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"

            logger.debug(f"Generating response for prompt length: {len(full_prompt)}")

            response = self.model.generate_content(full_prompt)
            result = response.text

            logger.info(f"Generated response of length: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_stream(
        self,
        prompt: str,
        system_instruction: str = None
    ) -> Generator[str, None, None]:
        """
        Generate streaming response from Gemini API.

        Args:
            prompt: User prompt
            system_instruction: System instruction (optional)

        Yields:
            Response text chunks
        """
        try:
            # Create full prompt
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"

            logger.debug(f"Starting stream generation for prompt length: {len(full_prompt)}")

            response = self.model.generate_content(full_prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

            logger.info("Stream generation completed")

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimate (4 chars per token)
            return len(text) // 4


# Global Gemini client instance
_gemini_client = None


def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
