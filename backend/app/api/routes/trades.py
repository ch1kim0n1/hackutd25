# backend/api/routes/trades.py
from app.services.alpaca import buy_stock, sell_stock

async def place_order(agent_network, user_id: str, symbol: str, qty: int, side: str):
    # Publish to agent network if needed
    await agent_network.publish("trade_order", {"user_id": user_id, "symbol": symbol, "qty": qty, "side": side})
    
    # Execute trade via Alpaca
    if side.lower() == "buy":
        result = await buy_stock(symbol, qty)
    else:
        result = await sell_stock(symbol, qty)
    
    return result
