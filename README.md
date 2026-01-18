# APEX: Multi-Agent Financial Investment System

> A transparent AI-powered financial platform where users actively participate in investment decisions alongside specialized AI agents

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

APEX is a desktop AI financial operating system featuring **transparent multi-agent collaboration** for investment management, personal finance tracking, and real-time financial education. Unlike traditional robo-advisors that operate as black boxes, APEX lets users observe and participate in AI agent discussions via voice or text.

**The Problem**: 67% of Americans avoid investing due to lack of knowledge/confidence. Current solutions are either fully automated (opaque) or purely advisory (overwhelming).

**Our Solution**: A human-in-the-loop multi-agent system where users are active participants, not passive observers.

## 🤖 Multi-Agent Architecture

APEX employs 6 specialized AI agents powered by Claude Sonnet 4.5:

### Core Agents

- **Market Agent** 🔍 - Scans news, tracks volatility (VIX), analyzes sentiment via web scraping and Alpaca API
- **Strategy Agent** 🧠 - Optimizes portfolios, evaluates opportunities, runs parallel scenario planning
- **Risk Agent** ⚠️ - Enforces risk limits, runs Monte Carlo simulations, stress tests positions
- **Executor Agent** ⚡ - Places trades via Alpaca API, validates orders, handles errors
- **Explainer Agent** 💬 - Translates decisions to plain English, provides adaptive education (ELI5 to advanced)
- **User Agent** 👤 - **You!** Inject opinions, override decisions, and approve actions via voice/text

### What Makes Us Unique

**Human-in-the-loop design**: Unlike fully autonomous trading systems, APEX agents **pause and listen** when you speak. Your input directly updates their analysis in real-time.

Examples:
- "I actually would like lower risk here"
- "You missed X important aspect of company Y"
- "Hold on, let me explain my reasoning..."

Agents debate in real-time, visible in the **War Room** interface—complete transparency, no black boxes.

## ✨ Key Features

### Must-Build Core
- **Visual Agent War Room** - Live multi-agent conversation display with color-coded debate tracking
- **Voice Interaction** - Push-to-talk with "hold on" instant editing and live transcription
- **Market Crash Simulator** - Time-compressed historical scenarios (2008, 2020) comparing APEX vs buy-and-hold strategies at 100x speed
- **Live Trading** - Alpaca paper trading integration with real-time execution

### Financial Breadth
- **Personal Finance Dashboard** - Plaid-connected net worth/cash flow tracking with AI health scoring
- **Top trendy news** for easy access + links
- **Stock Search Engine** with RAG-powered analysis
- **Historical Analysis** - Hover over time periods → agents perform RAG + web scraping for in-depth behavioral analysis
- **AI Goal Planner** - Voice-guided goal setting with timeline projections and compound interest calculations
- **Smart Subscription Tracker** - Auto-detects recurring charges, identifies waste, calculates savings reallocation

### Polish Features
- Personalized market news digest with portfolio impact assessment
- AI expense categorization with peer benchmarking
- Performance dashboard vs S&P 500

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Redis** (optional, for caching)
- API Keys:
  - [Alpaca Markets](https://app.alpaca.markets/) (paper trading account)
  - [OpenAI](https://platform.openai.com/)
  - [Anthropic](https://console.anthropic.com/)
  - [Plaid](https://plaid.com/) (optional, for personal finance features)

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/hackutd25.git
cd hackutd25
```

#### 2. Backend Setup
```bash
cd src/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp ../../.env.example ../../.env
# Edit .env with your API keys
```

#### 3. Frontend Setup
```bash
cd client/front

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
# Edit .env with your backend URL
```

#### 4. Start the Application

**Terminal 1 - Backend:**
```bash
cd src/backend
python server.py
# Server runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd client/front
npm run dev
# App runs on http://localhost:5173
```

#### 5. Open the App
Navigate to [http://localhost:5173](http://localhost:5173) in your browser.

## 📁 Project Structure

```
hackutd25/
├── client/front/          # React/TypeScript frontend
├── src/backend/           # FastAPI backend
├── data/                  # Local JSON storage
├── tests/                 # Test suites
├── demos/                 # Demo scripts
├── scripts/               # Utility scripts
├── .env.example           # Backend environment template
└── ARCHITECTURE.md        # Detailed architecture docs
```

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
```bash
# Required
JWT_SECRET_KEY=your-secret-key-here
ALPACA_API_KEY=your-alpaca-key
ALPACA_SECRET_KEY=your-alpaca-secret
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Optional
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
REDIS_URL=redis://localhost:6379
```

**Frontend** (`client/front/.env`):
```bash
VITE_BACKEND_URL=http://localhost:8000
VITE_BACKEND_WS_URL=ws://localhost:8000
VITE_USE_BACKEND_PROXY=true
```

See [.env.example](.env.example) and [client/front/.env.example](client/front/.env.example) for complete configuration options.

## 🧪 Testing

```bash
# Backend tests
cd src/backend
pytest tests/

# Frontend tests
cd client/front
npm test
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🛠️ Tech Stack

**Frontend:**
- React 18.3 + TypeScript
- Vite 6
- TailwindCSS 4.x
- shadcn/ui components

**Backend:**
- FastAPI 0.110
- Python 3.10+
- OpenAI / Anthropic Claude
- Alpaca Markets API
- ChromaDB (RAG)
- Local JSON storage

## 📖 Features Documentation

### War Room Interface
Real-time multi-agent collaboration visualization with:
- Color-coded agent identities
- Debate tracking
- Decision consensus display
- Human intervention capabilities

### Voice Commands
- Push-to-talk activation
- Live transcription
- "Hold on" error correction
- Natural language understanding

### Market Crash Simulator
- Historical scenario replay (2008, 2020, etc.)
- 100x time compression
- Strategy comparison (APEX vs buy-and-hold)
- Performance metrics

### Personal Finance Dashboard
- Net worth tracking
- Cash flow analysis
- Subscription management
- AI-powered financial health scoring

## 🔒 Security

- JWT authentication with refresh tokens
- Password hashing (bcrypt)
- Credential encryption (Fernet)
- API key proxying (recommended for production)
- CORS restrictions
- Input validation

⚠️ **Note**: This is a demo application. For production use:
- Enable HTTPS
- Use httpOnly cookies for tokens
- Migrate to PostgreSQL from JSON storage
- Implement rate limiting
- Set up proper logging and monitoring

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for HackUTD 2025
- Powered by Anthropic Claude, OpenAI, and Alpaca Markets
- UI components from [shadcn/ui](https://ui.shadcn.com/)

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Disclaimer**: This software is for educational and demonstration purposes only. It is not financial advice. Always consult with a qualified financial advisor before making investment decisions.


