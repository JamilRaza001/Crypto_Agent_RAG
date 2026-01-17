"""
Entity resolution for tracking cryptocurrencies and concepts across conversation turns.
Handles pronoun resolution and entity tracking.
"""

from typing import List, Dict, Optional, Set
from collections import deque
from src.utils.logging_config import logger


class EntityResolver:
    """Resolves entities and pronouns across conversation turns."""

    def __init__(self, max_history: int = 10):
        """
        Initialize entity resolver.

        Args:
            max_history: Maximum number of turns to track
        """
        self.max_history = max_history
        self.entity_history = deque(maxlen=max_history)
        self.entity_salience = {}  # entity -> salience score

        # Common cryptocurrency entities and their aliases
        self.entity_aliases = {
            'bitcoin': ['btc', 'bitcoin', 'bitcoins'],
            'ethereum': ['eth', 'ethereum', 'ether'],
            'binance coin': ['bnb', 'binance coin', 'binance'],
            'cardano': ['ada', 'cardano'],
            'solana': ['sol', 'solana'],
            'ripple': ['xrp', 'ripple'],
            'polkadot': ['dot', 'polkadot'],
            'dogecoin': ['doge', 'dogecoin'],
            'polygon': ['matic', 'polygon'],
            'avalanche': ['avax', 'avalanche'],
            'chainlink': ['link', 'chainlink'],
            'litecoin': ['ltc', 'litecoin'],
        }

        # Pronouns that can refer to previous entities
        self.pronouns = {
            'it', 'its', 'this', 'that', 'these', 'those',
            'the coin', 'the token', 'the cryptocurrency', 'the crypto'
        }

        logger.info("Entity resolver initialized")

    def normalize_entity(self, entity: str) -> str:
        """
        Normalize entity name (convert aliases to canonical form).

        Args:
            entity: Entity string

        Returns:
            Normalized entity name
        """
        entity_lower = entity.lower().strip()

        # Check if it's an alias
        for canonical, aliases in self.entity_aliases.items():
            if entity_lower in aliases:
                return canonical

        return entity_lower

    def extract_entities(self, text: str) -> Set[str]:
        """
        Extract cryptocurrency entities from text.

        Args:
            text: Input text

        Returns:
            Set of extracted entities (normalized)
        """
        text_lower = text.lower()
        entities = set()

        # Check for known crypto entities
        for canonical, aliases in self.entity_aliases.items():
            for alias in aliases:
                if alias in text_lower.split():
                    entities.add(canonical)
                    break

        # Additional common concepts
        concepts = ['defi', 'nft', 'blockchain', 'mining', 'staking', 'dao']
        for concept in concepts:
            if concept in text_lower.split():
                entities.add(concept)

        return entities

    def contains_pronoun(self, text: str) -> bool:
        """
        Check if text contains pronouns that might refer to previous entities.

        Args:
            text: Input text

        Returns:
            True if pronouns found
        """
        text_lower = text.lower()

        for pronoun in self.pronouns:
            if pronoun in text_lower:
                return True

        return False

    def get_most_recent_entity(self) -> Optional[str]:
        """
        Get the most recently mentioned entity.

        Returns:
            Most recent entity or None
        """
        # Search backwards through history
        for turn in reversed(self.entity_history):
            if turn['entities']:
                # Return highest salience entity from this turn
                entities = turn['entities']
                if len(entities) == 1:
                    return entities[0]
                else:
                    # Multiple entities - return most salient
                    return max(entities, key=lambda e: self.entity_salience.get(e, 0))

        return None

    def get_most_salient_entity(self) -> Optional[str]:
        """
        Get the most salient (frequently mentioned) entity.

        Returns:
            Most salient entity or None
        """
        if not self.entity_salience:
            return None

        return max(self.entity_salience.items(), key=lambda x: x[1])[0]

    def resolve_pronouns(self, text: str) -> str:
        """
        Replace pronouns with their referents.

        Args:
            text: Input text with potential pronouns

        Returns:
            Text with pronouns resolved
        """
        if not self.contains_pronoun(text):
            return text

        # Get most likely referent
        referent = self.get_most_recent_entity()

        if not referent:
            logger.debug("No entity found to resolve pronoun")
            return text

        # Replace pronouns
        resolved_text = text

        # Simple pronoun replacement
        replacements = {
            ' it ': f' {referent} ',
            ' its ': f" {referent}'s ",
            ' this ': f' {referent} ',
            ' that ': f' {referent} ',
            ' the coin ': f' {referent} ',
            ' the token ': f' {referent} ',
            ' the cryptocurrency ': f' {referent} ',
            ' the crypto ': f' {referent} ',
        }

        for pronoun, replacement in replacements.items():
            if pronoun in resolved_text.lower():
                # Case-insensitive replacement
                import re
                pattern = re.compile(re.escape(pronoun), re.IGNORECASE)
                resolved_text = pattern.sub(replacement, resolved_text)

        if resolved_text != text:
            logger.info(f"Resolved pronoun: '{text}' -> '{resolved_text}'")

        return resolved_text

    def update(self, user_message: str, assistant_message: str = None) -> None:
        """
        Update entity tracking with new conversation turn.

        Args:
            user_message: User's message
            assistant_message: Assistant's response (optional)
        """
        # Extract entities from user message
        entities = self.extract_entities(user_message)

        # Add to history
        turn = {
            'user_message': user_message,
            'assistant_message': assistant_message,
            'entities': list(entities)
        }
        self.entity_history.append(turn)

        # Update salience scores
        for entity in entities:
            self.entity_salience[entity] = self.entity_salience.get(entity, 0) + 1

        # Decay old entity salience
        for entity in list(self.entity_salience.keys()):
            if entity not in entities:
                self.entity_salience[entity] *= 0.9  # Decay factor

            # Remove if salience too low
            if self.entity_salience[entity] < 0.1:
                del self.entity_salience[entity]

        logger.debug(f"Entity tracking updated. Current entities: {entities}")
        logger.debug(f"Entity salience: {self.entity_salience}")

    def get_context_entities(self) -> List[str]:
        """
        Get all entities mentioned in recent history.

        Returns:
            List of entities sorted by salience
        """
        entities_with_salience = [
            (entity, score)
            for entity, score in self.entity_salience.items()
        ]

        # Sort by salience (descending)
        entities_with_salience.sort(key=lambda x: x[1], reverse=True)

        return [entity for entity, _ in entities_with_salience]

    def reset(self) -> None:
        """Reset entity tracking."""
        self.entity_history.clear()
        self.entity_salience.clear()
        logger.info("Entity tracking reset")


# Global entity resolver instance
_entity_resolver = None


def get_entity_resolver() -> EntityResolver:
    """Get or create global entity resolver instance."""
    global _entity_resolver
    if _entity_resolver is None:
        _entity_resolver = EntityResolver()
    return _entity_resolver
