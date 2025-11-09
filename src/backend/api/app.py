from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.core.agent_network import AgentNetwork
from backend.services.db import get_db
from backend.api.auth import login_user, get_current_user
from backend.api.strategy import run_strategy
from backend.api.portfolio import get_portfolio
from backend.api.trades import place_order, get_positions
from backend.api.market import get_market_data
from backend.services.alpaca import initialize_broker
import asyncio

app = FastAPI(title="APEX Backend API")

#Work
# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent network
agent_network = AgentNetwork()

@app.on_event("startup")
async def startup_event():
    await agent_network.initialize()
    # Run listener in background
    asyncio.create_task(agent_network.listen())

# ---------------------
# Auth endpoints
# ---------------------
@app.post("/login")
async def login(username: str, password: str):
    return await login_user(username, password)

@app.get("/me")
async def me(user=Depends(get_current_user)):
    return user

# ---------------------
# Strategy endpoints
# ---------------------
@app.post("/strategy/run")
async def strategy_run(strategy_id: str, user=Depends(get_current_user)):
    """
    Submits a strategy to be executed by agents.
    """
    result = await run_strategy(agent_network, strategy_id, user.id)
    return result

# ---------------------
# Portfolio endpoints
# ---------------------
@app.get("/portfolio")
async def portfolio(user=Depends(get_current_user), db=Depends(get_db)):
    return await get_portfolio(user.id, db)

# ---------------------
# Trade endpoints
# ---------------------
@app.post("/trade/buy")
async def buy(symbol: str, qty: int, user=Depends(get_current_user)):
    return await place_order(agent_network, user.id, symbol, qty, "buy")

@app.post("/trade/sell")
async def sell(symbol: str, qty: int, user=Depends(get_current_user)):
    return await place_order(agent_network, user.id, symbol, qty, "sell")

@app.get("/trade/positions")
async def positions(user=Depends(get_current_user)):
    return await get_positions(agent_network, user.id)

# ---------------------
# Market endpoints
# ---------------------
@app.get("/market/{symbol}")
async def market(symbol: str):
    return await get_market_data(symbol)


@app.on_event("startup")
async def startup_event():
    await agent_network.initialize()
    asyncio.create_task(agent_network.listen())
    await initialize_broker()
