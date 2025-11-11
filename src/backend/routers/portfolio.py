"""
Portfolio & Trading Router
Handles portfolio information, account data, positions, orders, and trade execution.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.logging_service import logger as structured_logger, RequestLogger

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["portfolio"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# Pydantic Models
class TradeRequest(BaseModel):
    symbol: str
    side: str
    qty: float
    type: str = 'market'
    time_in_force: str = 'day'
    limit_price: Optional[float] = None


# Endpoints
@router.get("/portfolio")
async def get_portfolio(current_user: dict = Depends(None)):  # Will be injected from main app
    """
    Get user's portfolio information.

    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from api.auth import get_current_user
    from server import alpaca_broker

    if current_user is None:
        # Fallback to direct auth
        current_user = Depends(get_current_user)

    user_id = current_user.id

    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")

    try:
        RequestLogger.log_request(
            structured_logger,
            "get_portfolio",
            user_id=str(user_id)
        )

        account = await alpaca_broker.get_account()
        positions = await alpaca_broker.get_positions()

        total_pl = sum(float(pos.get('unrealized_pl', 0)) for pos in positions) if isinstance(positions, list) else 0
        total_value = account.get('portfolio_value', 0)
        initial_value = float(total_value) - total_pl

        return {
            "total_value": total_value,
            "day_return": total_pl / initial_value * 100 if initial_value > 0 else 0,
            "total_return": (float(total_value) - 100000) / 100000 * 100,
        }
    except Exception as e:
        logger.error(f"Error fetching portfolio for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account")
async def get_account():
    """Get account information"""
    from server import alpaca_broker

    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")

    try:
        account = await alpaca_broker.get_account()
        return {
            "portfolio_value": account.get('portfolio_value', 0),
            "cash": account.get('cash', 0),
            "buying_power": account.get('buying_power', 0),
            "equity": account.get('equity', 0),
            "status": "ACTIVE"
        }
    except Exception as e:
        logger.error(f"Error fetching account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(
    limit: int = Query(100, ge=1, le=500, description="Number of positions to return"),
    offset: int = Query(0, ge=0, description="Number of positions to skip")
):
    """
    Get positions with pagination.

    Args:
        limit: Maximum number of positions to return (1-500, default 100)
        offset: Number of positions to skip (default 0)

    Returns:
        Paginated list of positions
    """
    from server import alpaca_broker

    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")

    try:
        positions = await alpaca_broker.get_positions()
        if isinstance(positions, dict) and 'error' in positions:
            return {"positions": [], "total": 0, "limit": limit, "offset": offset}

        formatted_positions = [
            {
                "symbol": pos['symbol'],
                "qty": pos['qty'],
                "avg_entry_price": pos.get('avg_fill_price', 0),
                "current_price": pos.get('current_price', 0),
                "market_value": pos.get('market_value', 0),
                "unrealized_pl": pos.get('unrealized_pl', 0),
                "unrealized_plpc": pos.get('unrealized_plpc', 0),
                "side": "long"
            }
            for pos in positions
        ]

        # Apply pagination
        total = len(formatted_positions)
        paginated_positions = formatted_positions[offset:offset + limit]

        return {
            "positions": paginated_positions,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return {"positions": [], "total": 0, "limit": limit, "offset": offset}


@router.get("/orders")
async def get_orders(
    limit: int = Query(100, ge=1, le=500, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip")
):
    """
    Get orders with pagination.

    Args:
        limit: Maximum number of orders to return (1-500, default 100)
        offset: Number of orders to skip (default 0)

    Returns:
        Paginated list of orders
    """
    from server import alpaca_broker

    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")

    try:
        orders = await alpaca_broker.get_orders()
        if isinstance(orders, dict) and 'error' in orders:
            return {"orders": [], "total": 0, "limit": limit, "offset": offset}

        # Apply pagination
        total = len(orders) if isinstance(orders, list) else 0
        paginated_orders = orders[offset:offset + limit] if isinstance(orders, list) else []

        return {
            "orders": paginated_orders,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return {"orders": [], "total": 0, "limit": limit, "offset": offset}


@router.post("/trade")
@limiter.limit("30/minute")  # Max 30 trades per minute
async def place_trade(request: Request, trade: TradeRequest, current_user = Depends(None)):
    """
    Place a buy or sell order.

    Requires authentication header:
        Authorization: Bearer <access_token>
    """
    from api.auth import get_current_user
    from server import alpaca_broker, manager

    if current_user is None:
        current_user = Depends(get_current_user)

    user_id = current_user.id

    if not alpaca_broker:
        raise HTTPException(status_code=503, detail="Alpaca broker not initialized")

    try:
        # Log trade request with user context
        RequestLogger.log_request(
            structured_logger,
            "place_trade",
            user_id=str(user_id),
            data={"symbol": trade.symbol, "qty": trade.qty, "side": trade.side}
        )

        if trade.side == 'buy':
            result = await alpaca_broker.buy(
                symbol=trade.symbol,
                qty=int(trade.qty),
                order_type=trade.type,
                limit_price=trade.limit_price
            )
        else:
            result = await alpaca_broker.sell(
                symbol=trade.symbol,
                qty=int(trade.qty),
                order_type=trade.type,
                limit_price=trade.limit_price
            )

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        await manager.broadcast({
            "type": "executor",
            "from": "executor",
            "to": "all",
            "content": f"⚡ Order placed: {trade.side.upper()} {trade.qty} {trade.symbol} @ {trade.type.upper()}",
            "timestamp": datetime.now().isoformat(),
            "data": {"order": result}
        })

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing trade for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
