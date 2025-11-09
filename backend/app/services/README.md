# APEX Backend Services

Shared services used across the backend.

## Available Services

### `security.py`
Comprehensive security and authentication services including:
- Password hashing and verification
- JWT token management
- Two-factor authentication (2FA)
- Rate limiting
- Encryption services
- Auth functions (login, refresh, logout)

### `voice.py`
Voice processing services including:
- Speech-to-text (STT) and text-to-speech (TTS)
- Voice command parsing and validation
- Goal parsing from voice input
- Voice command security and rate limiting

### `plaid_integration.py`
Real Plaid API integration for financial data.

### `mock_plaid.py`
Mock Plaid data for testing and development.

### `rag/chroma_service.py`
Vector database and RAG (Retrieval-Augmented Generation) services:
- ChromaDB vector storage
- Semantic search capabilities
- Query intent classification
- Historical market data indexing

### `historical_data.py`
Historical market data loader for crash simulations.

**Usage**:
```python
from services.historical_data import HistoricalDataLoader

loader = HistoricalDataLoader()
data = loader.load_scenario("2008_crisis")
```
