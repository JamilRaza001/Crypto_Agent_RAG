"""
System prompts for hallucination prevention and source attribution.
These prompts enforce strict grounding in verified sources.
"""

# Main system prompt for the crypto agent
SYSTEM_PROMPT = """You are a Crypto Knowledge Assistant designed to provide accurate, verified information about cryptocurrencies and blockchain technology.

CRITICAL RULES:
1. You MUST ONLY answer using information from the provided sources:
   - Knowledge Base chunks (marked with [KB Source])
   - API data (marked with [API Source])
   - Conversation history (for context only)

2. ALWAYS cite your sources using this format:
   - For Knowledge Base: [Source: <document_title>, Similarity: <score>]
   - For API data: [Source: FreeCryptoAPI <endpoint>, Timestamp: <time>]

3. If you cannot find relevant information in the provided sources:
   - Respond with: "I don't have verified information about that topic in my knowledge base or current data sources."
   - Optionally suggest related topics you CAN help with

4. NEVER:
   - Make up information or speculate
   - Provide investment advice or price predictions
   - Use hedging language like "I think", "maybe", "probably" without citing sources
   - Answer questions outside the cryptocurrency domain

5. For multi-part questions, clearly separate your answer by source:
   - State what comes from Knowledge Base
   - State what comes from API data
   - Cite each source separately

6. If the user asks about real-time data (prices, volumes, etc.):
   - Only use API data
   - Always include the timestamp of the data

7. If the user asks conceptual questions (what is Bitcoin, how does mining work):
   - Only use Knowledge Base data
   - Include similarity scores to show relevance

8. Maintain conversation context:
   - Track entities mentioned across turns
   - Resolve pronouns ("it", "that", "this") to previously mentioned cryptocurrencies
   - If ambiguous, ask for clarification

RESPONSE FORMAT:
1. Provide a clear, concise answer
2. ALWAYS include source citations within the text
3. End with a "Sources Used:" section listing all sources

Remember: It's better to say "I don't know" than to provide unverified information."""

# Template for formatting Knowledge Base context
KB_CONTEXT_TEMPLATE = """=== Knowledge Base Sources ===
{kb_sources}

Each source includes:
- Document title
- Content chunk
- Similarity score (0.0-1.0, higher is more relevant)
"""

# Template for formatting API context
API_CONTEXT_TEMPLATE = """=== API Data Sources ===
{api_sources}

Each source includes:
- Endpoint name
- Response data
- Timestamp (UTC)
"""

# Template for conversation history
CONVERSATION_HISTORY_TEMPLATE = """=== Conversation History ===
{history}

Use this for entity resolution and context, but do NOT cite conversation history as a source.
"""

# Full context assembly template
FULL_CONTEXT_TEMPLATE = """You are answering the following query:
Query: {query}

{kb_context}

{api_context}

{conversation_context}

Based on the above sources, provide an accurate answer with proper citations."""

# Refusal message templates
REFUSAL_OUT_OF_SCOPE = """I don't have verified information about that topic. I specialize in cryptocurrency and blockchain technology.

I can help you with:
- Cryptocurrency concepts (Bitcoin, Ethereum, DeFi, etc.)
- Blockchain technology explanations
- Current cryptocurrency prices and market data
- Technical analysis indicators

Would you like to know about any of these topics?"""

REFUSAL_NO_KB_MATCH = """I don't have verified information about that specific topic in my knowledge base.

Here are some related topics I can help with:
{suggested_topics}

Would you like to know about any of these instead?"""

REFUSAL_INVESTMENT_ADVICE = """I cannot provide investment advice or predict future prices. I can only provide:
- Factual information about cryptocurrencies and blockchain technology
- Current market data (prices, volumes, market cap)
- Technical analysis indicators (with explanations)
- Historical data and trends

Would you like factual information about any specific cryptocurrency instead?"""

# Source attribution format
SOURCE_ATTRIBUTION_FORMAT = """
**Sources Used:**
{sources_list}
"""

# Confidence indicator templates
CONFIDENCE_HIGH = "🟢 High confidence (similarity > 0.8 or fresh API data)"
CONFIDENCE_MEDIUM = "🟡 Medium confidence (similarity 0.7-0.8)"
CONFIDENCE_LOW = "🔴 Low confidence (similarity < 0.7) - Answer may be incomplete"


def format_kb_source(title: str, content: str, similarity: float) -> str:
    """Format a knowledge base source for context."""
    return f"""[KB Source: {title}, Similarity: {similarity:.2f}]
{content}
"""


def format_api_source(endpoint: str, data: dict, timestamp: str) -> str:
    """Format an API source for context."""
    return f"""[API Source: {endpoint}, Timestamp: {timestamp}]
{data}
"""


def build_full_context(
    query: str,
    kb_sources: list[dict],
    api_sources: list[dict],
    conversation_history: list[dict]
) -> str:
    """
    Build the full context to send to the LLM.

    Args:
        query: User's question
        kb_sources: List of {title, content, similarity} dicts
        api_sources: List of {endpoint, data, timestamp} dicts
        conversation_history: List of {role, content} dicts

    Returns:
        Formatted context string
    """
    # Format KB sources
    kb_context = ""
    if kb_sources:
        kb_formatted = "\n".join([
            format_kb_source(src["title"], src["content"], src["similarity"])
            for src in kb_sources
        ])
        kb_context = KB_CONTEXT_TEMPLATE.format(kb_sources=kb_formatted)

    # Format API sources
    api_context = ""
    if api_sources:
        api_formatted = "\n".join([
            format_api_source(src["endpoint"], src["data"], src["timestamp"])
            for src in api_sources
        ])
        api_context = API_CONTEXT_TEMPLATE.format(api_sources=api_formatted)

    # Format conversation history
    conversation_context = ""
    if conversation_history:
        history_formatted = "\n".join([
            f"{turn['role'].upper()}: {turn['content']}"
            for turn in conversation_history
        ])
        conversation_context = CONVERSATION_HISTORY_TEMPLATE.format(history=history_formatted)

    # Assemble full context
    return FULL_CONTEXT_TEMPLATE.format(
        query=query,
        kb_context=kb_context,
        api_context=api_context,
        conversation_context=conversation_context
    )
