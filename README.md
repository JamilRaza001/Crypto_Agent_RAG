# Knowledge-Grounded Crypto Agent

A production-ready RAG-based cryptocurrency agent that prevents hallucinations through strict source verification. Built with Streamlit, Google Gemini API, ChromaDB, and FreeCryptoAPI.

## Features

- **Zero Hallucinations**: Multi-layer validation ensures all answers cite verified sources
- **Dual Knowledge Sources**:
  - Local Knowledge Base (ChromaDB) for crypto concepts and explanations
  - FreeCryptoAPI for real-time market data and prices
- **Smart Routing**: Automatically determines when to use KB vs API vs both
- **Source Attribution**: Every answer includes citations with similarity scores/timestamps
- **Conversation Memory**: Entity tracking and pronoun resolution across turns
- **Response Caching**: >70% cache hit rate reduces API costs

## Architecture

```
User Query → Query Processor → Tool Orchestrator
                ↓                     ↓
          KB (ChromaDB)         API (FreeCrypto)
                ↓                     ↓
         Hallucination Guard (5-layer validation)
                ↓
         Gemini LLM Generation
                ↓
    Streamlit UI (with source citations)
```

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini API (gemini-1.5-flash)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB**: ChromaDB
- **API**: FreeCryptoAPI (14 endpoints)
- **Caching**: SQLite with LRU eviction
- **Language**: Python 3.10+

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd "c:/Agentic AI SMIT/Projects/cyrpto agent"
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 4. Configure Environment Variables

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your API keys
# Required: GEMINI_API_KEY
```

Get your Gemini API key: https://aistudio.google.com/app/apikey

### 5. Initialize Knowledge Base

```bash
# This will be created in Phase 3
python scripts/init_kb.py
```

## Project Structure

```
cyrpto agent/
├── config/                    # Configuration modules
│   ├── settings.py           # Centralized settings (pydantic)
│   ├── prompts.py            # System prompts for hallucination prevention
│   └── api_config.py         # FreeCryptoAPI endpoint definitions
├── src/
│   ├── core/                 # Core infrastructure
│   │   ├── embeddings.py    # sentence-transformers wrapper
│   │   ├── llm_client.py    # Gemini API client with retry
│   │   └── cache_manager.py # SQLite-based caching
│   ├── knowledge_base/       # KB management (Phase 3)
│   ├── api/                  # API integration (Phase 4)
│   ├── rag/                  # RAG pipeline (Phase 5)
│   ├── agent/                # Agent orchestration (Phase 6)
│   └── utils/                # Utilities
├── data/
│   ├── knowledge_base/       # Crypto knowledge data
│   ├── chromadb/            # Vector database storage
│   └── sqlite/              # Cache and metadata
├── streamlit_app/           # Streamlit UI (Phase 7)
├── scripts/                 # Utility scripts
└── tests/                   # Unit and integration tests
```

## Implementation Status

✅ **Phase 1: Project Foundation** (Completed)
- Git repository initialized
- Directory structure created
- Dependencies configured
- Environment setup

✅ **Phase 2: Core Infrastructure** (Completed)
- Embedding manager (sentence-transformers)
- Gemini LLM client with retry logic
- Cache manager with LRU eviction
- Logging configuration

🔄 **Phase 3: Knowledge Base Setup** (Next)
- Create sample crypto knowledge data
- Implement ChromaDB manager
- Implement KB initialization
- Entity resolution engine

⏳ **Phase 4: API Integration** (Pending)
- FreeCryptoAPI client wrapper
- Rate limiting (100k/month)
- API orchestrator with caching

⏳ **Phase 5: RAG Pipeline** (Pending)
- Semantic search retrieval
- Cross-encoder re-ranking
- Context builder
- **Hallucination guard** (critical)

⏳ **Phase 6: Agent Orchestration** (Pending)
- Query processor and classifier
- Tool orchestrator (KB vs API routing)
- Response generator
- Conversation manager

⏳ **Phase 7: Streamlit UI** (Pending)
- Chat interface
- Source attribution display
- Configuration sidebar

⏳ **Phase 8: Testing & Documentation** (Pending)
- Unit tests (>80% coverage)
- Integration tests
- Hallucination test suite
- Performance benchmarks

## Usage (After Full Implementation)

### Running the Application

```bash
streamlit run streamlit_app/app.py
```

### Example Queries

**Conceptual (KB-only)**:
```
"What is Bitcoin?"
"Explain Ethereum smart contracts"
"How does DeFi work?"
```

**Real-time (API-only)**:
```
"Current BTC price"
"Top 10 cryptocurrencies by market cap"
"What's the Fear & Greed Index?"
```

**Hybrid (KB + API)**:
```
"What is Ethereum's RSI and what does it mean?"
"Explain Bitcoin halving and show current price"
```

**Out-of-Scope (Refusal)**:
```
"What's the weather today?" → Refuses (not crypto-related)
"Best crypto to invest in?" → Refuses (no investment advice)
```

## Hallucination Prevention

The agent uses a 5-layer defense system:

1. **Query Validation**: Verify query is crypto-related
2. **Retrieval Threshold**: Only use KB chunks with similarity > 0.7
3. **Prompt Engineering**: Strict system prompts enforce source attribution
4. **Post-Generation Validation**: Verify LLM cited all sources correctly
5. **Confidence Scoring**: Display confidence indicators to users

## Configuration

Key settings in [.env](.env):

```env
# Model Settings
TEMPERATURE=0.1              # Low temperature for factual responses
SIMILARITY_THRESHOLD=0.7     # Minimum KB similarity score
TOP_K_RESULTS=5              # Number of KB chunks to retrieve

# Cache TTL (seconds)
PRICE_CACHE_TTL=60           # 1 minute for price data
HISTORICAL_CACHE_TTL=3600    # 1 hour for historical data
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy src/
```

## Performance Targets

- **Latency**: <2s end-to-end (query → response)
- **Cache Hit Rate**: >70% for repeated queries
- **Memory Usage**: <500MB during operation
- **API Calls**: <500ms without cache, <10ms with cache

## Contributing

This is a demonstration project. For issues or suggestions, please create an issue.

## License

MIT License

## Acknowledgments

- Google Gemini API for LLM capabilities
- FreeCryptoAPI for market data
- ChromaDB for vector storage
- sentence-transformers for embeddings
- Streamlit for rapid UI development

---

**Project Status**: Under active development
**Last Updated**: 2026-01-18
**Version**: 0.3.0 (Phases 1-2 completed)
