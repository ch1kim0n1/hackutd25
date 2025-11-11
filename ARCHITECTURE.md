# APEX Platform Architecture

## Overview

APEX is a multi-agent financial investment platform with AI-powered portfolio management, trading capabilities, and personal finance integration. The platform consists of a FastAPI backend with multiple AI agents, a React/TypeScript frontend, and local JSON-based data storage.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + TypeScript)           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Client App (Vite + React 18 + TailwindCSS 4)       │   │
│  │  - Trading Dashboard                                  │   │
│  │  - Portfolio Management                               │   │
│  │  - AI Chat Interface                                  │   │
│  │  - Personal Finance Dashboard                         │   │
│  │  - War Room (Real-time Agent Orchestration)          │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓ HTTP/WebSocket                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI + Python)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Layer (REST + WebSocket)                        │   │
│  │  - Authentication (JWT)                               │   │
│  │  - Trading Endpoints                                  │   │
│  │  - Portfolio Management                               │   │
│  │  - Goal Tracking                                      │   │
│  │  - Voice Commands                                     │   │
│  │  - RAG Query Engine                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Agent Orchestrator (Multi-Agent System)             │   │
│  │  - Market Analysis Agent                              │   │
│  │  - Risk Management Agent                              │   │
│  │  - Execution Agent                                    │   │
│  │  - Research Agent                                     │   │
│  │  - News Sentiment Agent                               │   │
│  │  - Risk-Reward Agent                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Services Layer                                       │   │
│  │  - JSON Storage (Local File System)                  │   │
│  │  - Alpaca Broker Integration                          │   │
│  │  - OpenAI / Anthropic Integration                     │   │
│  │  - RAG System (ChromaDB)                              │   │
│  │  - Voice Processing (Whisper + TTS)                   │   │
│  │  - Plaid Integration                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA STORAGE (Local JSON)                  │
│  /data/                                                      │
│  ├── users/          (User accounts & profiles)             │
│  ├── portfolios/     (Portfolio data)                       │
│  ├── trades/         (Trade history)                        │
│  ├── goals/          (Financial goals)                      │
│  ├── accounts/       (Linked accounts)                      │
│  ├── transactions/   (Transaction history)                  │
│  └── rag_documents/  (RAG embeddings metadata)              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                 EXTERNAL SERVICES (APIs)                    │
│  - Alpaca Markets (Trading & Market Data)                   │
│  - OpenAI (GPT-4, Embeddings)                               │
│  - Anthropic (Claude)                                       │
│  - Plaid (Banking Integration)                              │
│  - Redis (Optional Caching)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
hackutd25/
├── client/                      # Frontend application
│   ├── front/                   # Primary React/TypeScript app
│   │   ├── src/
│   │   │   ├── components/      # React components
│   │   │   ├── pages/           # Page components
│   │   │   ├── services/        # API services
│   │   │   │   ├── BackendAPI.ts        # Backend API client
│   │   │   │   ├── WebSocketClient.ts   # WebSocket client
│   │   │   │   ├── AlpacaClient.ts      # Direct Alpaca (legacy)
│   │   │   │   └── AIService.ts         # AI service
│   │   │   ├── hooks/           # Custom React hooks
│   │   │   ├── ui/              # UI components (shadcn)
│   │   │   └── lib/             # Utilities
│   │   ├── vite.config.ts       # Vite configuration (with proxy)
│   │   └── .env.example         # Frontend environment variables
│   └── electron/                # Electron wrapper (optional)
│
├── src/backend/                 # Backend application
│   ├── server.py                # Main FastAPI server
│   ├── orchestrator.py          # Agent orchestrator
│   ├── api/
│   │   └── auth.py              # Authentication endpoints
│   ├── models/
│   │   └── pydantic_models.py   # Pydantic data models
│   ├── services/
│   │   ├── json_storage_service.py  # JSON storage layer
│   │   ├── dao/
│   │   │   └── json_dao.py      # Data access objects
│   │   ├── security.py          # Password & JWT services
│   │   ├── voice.py             # Voice processing
│   │   ├── rag/                 # RAG system
│   │   │   ├── chroma_service.py
│   │   │   └── query_engine.py
│   │   └── finance_adapter.py   # Plaid integration
│   ├── agents/                  # AI agents
│   │   ├── market_agent.py
│   │   ├── risk_agent.py
│   │   ├── execution_agent.py
│   │   ├── research_agent.py
│   │   └── news_agent.py
│   ├── integrations/
│   │   └── alpaca_broker.py     # Alpaca API wrapper
│   ├── middleware/
│   │   ├── auth.py              # Auth middleware
│   │   └── exception_handler.py # Global error handling
│   └── requirements.txt         # Python dependencies
│
├── data/                        # Local JSON data storage
│   ├── users/
│   ├── portfolios/
│   ├── trades/
│   ├── goals/
│   ├── accounts/
│   ├── transactions/
│   └── rag_documents/
│
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests
│   │   ├── test_market_agent.py
│   │   ├── test_risk_agent.py
│   │   └── test_json_storage.py
│   └── integration/             # Integration tests
│       └── test_api_endpoints.py
│
├── demos/                       # Demo scripts
│   └── orchestration_demo_live.py
│
├── scripts/                     # Utility scripts
│   ├── setup-phase1.ps1
│   ├── start-backend.ps1
│   └── start-frontend.ps1
│
├── .env.example                 # Backend environment variables
├── ARCHITECTURE.md              # This file
└── README.md                    # Project documentation
```

## Technology Stack

### Frontend
- **Framework**: React 18.3 with TypeScript
- **Build Tool**: Vite 6
- **Styling**: TailwindCSS 4.x
- **UI Components**: shadcn/ui (Radix UI primitives)
- **State Management**: React hooks + context
- **HTTP Client**: Native Fetch API
- **WebSocket**: Native WebSocket API
- **Desktop Wrapper**: Electron (optional)

### Backend
- **Framework**: FastAPI 0.110.0
- **Language**: Python 3.10+
- **API**: REST + WebSocket
- **Authentication**: JWT (PyJWT)
- **Data Storage**: Local JSON files (thread-safe)
- **AI/ML**: OpenAI, Anthropic Claude
- **Trading**: Alpaca Markets API
- **RAG**: ChromaDB + Sentence Transformers
- **Voice**: Faster Whisper + Edge TTS
- **Caching**: Redis (optional)

## Key Components

### 1. Frontend-Backend Communication

#### REST API
The frontend communicates with the backend via RESTful API calls proxied through Vite during development:

```typescript
// Example: Using BackendAPI service
import BackendAPI from '@/services/BackendAPI';

// Login
const { access_token } = await BackendAPI.auth.login(username, password);

// Get portfolio
const portfolio = await BackendAPI.portfolio.get();

// Place trade
await BackendAPI.trading.placeTrade({
  symbol: 'AAPL',
  qty: 10,
  side: 'buy'
});
```

#### WebSocket (War Room)
Real-time updates from the agent orchestrator:

```typescript
import { WarRoomWebSocket } from '@/services/WebSocketClient';

const ws = new WarRoomWebSocket(userId);
ws.connect();

ws.onMessage((message) => {
  console.log('Agent update:', message);
});
```

### 2. Authentication Flow

```
1. User submits credentials
   ↓
2. Frontend → POST /auth/login
   ↓
3. Backend validates credentials (JSON storage)
   ↓
4. Generate JWT access token (15 min) + refresh token (7 days)
   ↓
5. Frontend stores tokens in localStorage
   ↓
6. All subsequent requests include: Authorization: Bearer <token>
   ↓
7. Backend validates JWT on each request
   ↓
8. If expired → Auto-refresh using refresh token
```

### 3. Data Storage (Local JSON)

**Thread-Safe JSON Storage**:
- Each entity type (users, portfolios, trades, etc.) has its own directory
- Individual records stored as `{entity_id}.json`
- Index file (`index.json`) for quick lookups
- Automatic backup on updates (`.backup/` subdirectory)
- Thread-safe operations using Python threading locks

**Example Structure**:
```
data/
├── users/
│   ├── index.json
│   ├── user_123.json
│   ├── user_456.json
│   └── .backup/
│       └── user_123_20250110_143022.json
└── portfolios/
    ├── index.json
    └── portfolio_789.json
```

### 4. Multi-Agent System

The orchestrator coordinates multiple AI agents:

1. **Market Analysis Agent**: Technical analysis, price predictions
2. **Risk Management Agent**: Position sizing, stop-loss recommendations
3. **Execution Agent**: Trade execution and monitoring
4. **Research Agent**: Fundamental analysis, company research
5. **News Sentiment Agent**: News analysis and sentiment scoring
6. **Risk-Reward Agent**: Risk/reward ratio calculations

**Orchestration Flow**:
```
User Input → Orchestrator → Agents (parallel execution)
                ↓
         Consensus Building
                ↓
         Decision Making
                ↓
         Action Execution
```

### 5. RAG System (Retrieval-Augmented Generation)

- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Use Cases**:
  - Financial document analysis
  - Earnings reports
  - Market research
  - User-uploaded documents

## Security Considerations

### Backend Security
- ✅ JWT authentication with expiration and refresh
- ✅ Password hashing (bcrypt)
- ✅ Credential encryption (Fernet)
- ✅ CORS restrictions
- ✅ Input validation (Pydantic models)
- ✅ Rate limiting (recommended: add Redis)
- ⚠️ HTTPS enforcement (disabled by default, enable in production)

### Frontend Security
- ✅ Token storage in localStorage (consider httpOnly cookies for production)
- ✅ Automatic token refresh
- ✅ API key proxy through backend (recommended)
- ⚠️ Direct API keys in .env (only for development)

## Development Workflow

### Starting the Application

**Backend**:
```bash
cd src/backend
pip install -r requirements.txt
python server.py
# Server runs on http://localhost:8000
```

**Frontend**:
```bash
cd client/front
npm install
npm run dev
# App runs on http://localhost:5173
```

### Environment Configuration

1. Copy `.env.example` to `.env` in root directory
2. Copy `client/front/.env.example` to `client/front/.env`
3. Fill in API keys:
   - Alpaca (trading)
   - OpenAI (AI agents)
   - Anthropic (Claude)
   - Plaid (optional, personal finance)

### Proxy Configuration

During development, Vite proxies API requests to the backend:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/auth': 'http://localhost:8000',
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true
    }
  }
}
```

## Testing Strategy

### Backend Tests
```bash
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
```

### Frontend Tests
```bash
cd client/front
npm test                    # Vitest
```

## Deployment Considerations

### Production Checklist
- [ ] Change JWT_SECRET_KEY to a strong random value
- [ ] Enable HTTPS (set FORCE_HTTPS=true)
- [ ] Use httpOnly cookies for token storage
- [ ] Proxy all API calls through backend (no direct client API keys)
- [ ] Set up proper logging and monitoring
- [ ] Configure rate limiting
- [ ] Use production Redis for caching
- [ ] Migrate from JSON storage to PostgreSQL (for scale)
- [ ] Enable CORS only for specific origins
- [ ] Set up CI/CD pipeline
- [ ] Configure backup strategy for data/

### Scaling Considerations
- Current JSON storage is suitable for < 1000 users
- For larger scale, migrate to PostgreSQL or MongoDB
- Use Redis for session management and caching
- Consider Docker deployment
- Load balancing for multiple backend instances

## Future Enhancements

1. **Database Migration**: PostgreSQL/MongoDB for production scale
2. **Real-time Market Data**: WebSocket streams from Alpaca
3. **Advanced Analytics**: More sophisticated AI models
4. **Mobile App**: React Native version
5. **Backtesting Engine**: Historical strategy testing
6. **Social Trading**: Share strategies and insights
7. **Compliance**: Audit logs and regulatory reporting

## Contact & Support

For questions or issues, please refer to the main README.md or open an issue on GitHub.
