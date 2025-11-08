# hackutd25

APEX: Multi-Agent Financial Investment System
Hackathon Project Report

🎯 Project Overview
APEX is a desktop AI financial operating system featuring transparent multi-agent collaboration for investment management, personal finance tracking, and real-time financial education. Unlike traditional robo-advisors that operate as black boxes, APEX lets users observe and participate in AI agent discussions via voice or text.
Target Problem: 67% of Americans avoid investing due to lack of knowledge/confidence. Current solutions are either fully automated (opaque) or purely advisory (overwhelming).

🤖 Multi-Agent Architecture
APEX employs 6 specialized AI agents powered by Claude Sonnet 4.5 with GPU-accelerated processing:
Core Agents
Market Agent 🔍 - Scans news, tracks volatility (VIX), analyzes sentiment via web scraping and Alpaca API
Strategy Agent 🧠 - Optimizes portfolios, evaluates opportunities, runs parallel scenario planning
Risk Agent ⚠️ - Enforces risk limits, runs Monte Carlo simulations, stress tests positions
Executor Agent ⚡ - Places trades via Alpaca API, validates orders, handles errors
Explainer Agent 💬 - Translates decisions to plain English, provides adaptive education (ELI5 to advanced)
User Agent 👤 - Human participant who can inject opinions, override decisions, and approve actions via voice/text
REALLY IMPORTANT: emphasize that this makes us especially unique. Other applications like this are completely autonomous, the agents do all the work, not considering the user’s dynamically changing interests and valuable opinions missed by the agents
As soon as the user talks, the agents all pause and let him continue, letting him give his opinion. They then use that information to update their own opinions. Examples: “i actually would like lower risk here”, “You missed so and so important aspect of company x, etc.”
Agents debate in real-time, visible to users in a "War Room" interface.

✨ Key Features
Must-Build Core
Visual Agent War Room - Live multi-agent conversation display with color-coded debate tracking
Voice Interaction - Push-to-talk with "hold on" instant editing and live transcription
Market Crash Simulator - Time-compressed historical scenarios (2008, 2020) comparing APEX vs buy-and-hold strategies at 100x speed
Live Trading - Alpaca paper trading integration with real-time execution
Financial Breadth
Personal Finance Dashboard - Plaid-connected net worth/cash flow tracking with AI health scoring
Top trendy news for easy access + links
Search engine for different stocks
Hover over certain time period → agent does RAG + webscraping for in-depth analysis of why the stock behaved like that
AI Goal Planner - Voice-guided goal setting with timeline projections and compound interest calculations; done during login (?), can be changed easily via voice command asking to do so. 
Smart Subscription Tracker - Auto-detects recurring charges, identifies waste, calculates savings reallocation to investments
Polish Features
Personalized market news digest with portfolio impact assessment
AI expense categorization with peer benchmarking
Performance dashboard vs S&P 500

💡 My Opinion
Strengths:
Differentiated concept - The transparent multi-agent approach and human-in-the-loop design genuinely solves the "scary black box" problem
NVIDIA alignment - GPU-accelerated simulations and parallel agent processing showcase compute capabilities
Practical scope - The feature prioritization (16h core + 12h breadth) is realistic for a hackathon
Voice UX innovation - The "hold on" error correction mechanism is clever and addresses real voice interface pain points
Concerns:
Regulatory complexity - Even paper trading requires disclaimers; live trading could create liability issues for a demo
Agent coordination overhead - Synchronizing 5-6 agents in real-time conversations may be technically complex within 36 hours
Feature creep risk - 36 total hours of features is aggressive; consider cutting subscription tracker or news digest to ensure core works flawlessly
Recommendations:
Prioritize the War Room + Crash Simulator - These are your "wow" demos that judges will remember
Use pre-recorded agent conversations as fallback if real-time orchestration fails
Mock Plaid integration initially (API approval takes time) and show it working with dummy data
Emphasize educational value over actual trading to reduce regulatory concerns

🎓 Technical Innovation
The RAG system with historical market data, GPU-accelerated Monte Carlo simulations, and multi-agent orchestration demonstrate strong technical depth. The voice interface with semantic correction ("hold on") is particularly novel.
Verdict: Strong hackathon concept with clear market need, technical ambition, and impressive scope. Focus execution on core visual elements and agent transparency—that's your competitive edge.


Research
Link sources
Make more credible responses
Focus on core and develop it to perfection
Verdict: pretty unique need good pitching

