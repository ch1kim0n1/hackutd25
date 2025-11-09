# backend/services/alpaca.py
import os
from backend.src.integrations.alpaca_broker import AlpacaBroker

# Global broker instance
broker = AlpacaBroker(paper=True)

async def initialize_broker():
    await broker.initialize()
    return broker

async def buy_stock(symbol: str, qty: int):
    return await broker.buy(symbol, qty)

async def sell_stock(symbol: str, qty: int):
    return await broker.sell(symbol, qty)

async def get_account_info():
    return await broker.get_account()

async def get_positions():
    return await broker.get_positions()
