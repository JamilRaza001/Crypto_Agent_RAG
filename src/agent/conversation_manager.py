"""
Conversation manager - manages conversation history and context.
Maintains sliding window of recent turns with entity tracking.
"""

from typing import List, Dict, Optional
from collections import deque
from src.knowledge_base.entity_resolver import get_entity_resolver
from src.utils.logging_config import logger


class ConversationManager:
    """Manages conversation state and history."""

    def __init__(self, max_turns: int = 10):
        """
        Initialize conversation manager.

        Args:
            max_turns: Maximum number of turns to keep in memory
        """
        self.max_turns = max_turns
        self.conversation_history = deque(maxlen=max_turns)
        self.entity_resolver = get_entity_resolver()
        self.conversation_id = None

        logger.info(f"Conversation manager initialized (max_turns: {max_turns})")

    def add_turn(
        self,
        user_message: str,
        assistant_message: str,
        sources: List[Dict] = None,
        confidence: float = None
    ) -> None:
        """
        Add a conversation turn.

        Args:
            user_message: User's message
            assistant_message: Assistant's response
            sources: Sources used in response
            confidence: Response confidence score
        """
        turn = {
            'role': 'user',
            'content': user_message,
            'timestamp': None  # Could add datetime if needed
        }

        self.conversation_history.append(turn)

        turn = {
            'role': 'assistant',
            'content': assistant_message,
            'sources': sources or [],
            'confidence': confidence,
            'timestamp': None
        }

        self.conversation_history.append(turn)

        # Update entity resolver
        self.entity_resolver.update(user_message, assistant_message)

        logger.info(f"Added conversation turn. History length: {len(self.conversation_history)}")

    def get_history(self, num_turns: int = None) -> List[Dict]:
        """
        Get conversation history.

        Args:
            num_turns: Number of recent turns (None = all)

        Returns:
            List of conversation turns
        """
        if num_turns is None:
            return list(self.conversation_history)

        # Get last N turns
        return list(self.conversation_history)[-num_turns:]

    def get_context_for_llm(self, num_turns: int = 8) -> List[Dict]:
        """
        Get conversation context formatted for LLM.

        Args:
            num_turns: Number of recent turns to include

        Returns:
            List of turn dictionaries with role and content
        """
        history = self.get_history(num_turns)

        # Filter to just role and content
        context = [
            {'role': turn['role'], 'content': turn['content']}
            for turn in history
        ]

        return context

    def get_entities(self) -> List[str]:
        """
        Get entities tracked in conversation.

        Returns:
            List of entity strings
        """
        return self.entity_resolver.get_context_entities()

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        self.entity_resolver.reset()
        logger.info("Conversation history cleared")

    def get_summary(self) -> Dict:
        """
        Get conversation summary.

        Returns:
            Summary dictionary
        """
        return {
            'num_turns': len(self.conversation_history),
            'max_turns': self.max_turns,
            'entities': self.get_entities(),
            'conversation_id': self.conversation_id
        }


# Global conversation manager instance
_conversation_manager = None


def get_conversation_manager() -> ConversationManager:
    """Get or create global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
