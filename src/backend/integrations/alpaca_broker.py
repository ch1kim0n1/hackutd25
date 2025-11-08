import alpaca_trade_api as tradeapi
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import os

class AlpacaBroker:
    """
    Alpaca broker integration for live trading.
    Supports both paper trading (for demos) and live trading.
    """
    def __init__(self, paper: bool = True):
        self.api_key = os.getenv('ALPACA_API_KEY', 'demo-key')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY', 'demo-secret')
        self.paper = paper
        self.base_url = 'https://paper-api.alpaca.markets' if paper else 'https://api.alpaca.markets'
        self.api = None
        self.socket = None

    async def initialize(self):
        self.api = tradeapi.REST(
            self.api_key,
            self.secret_key,
            self.base_url,
            api_version='v2'
        )
        return {"status": "connected", "mode": "paper" if self.paper else "live"}

    async def get_account(self) -> Dict:
        try:
            account = self.api.get_account()
            return {
                "portfolio_value": float(account.portfolio_value),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "positions_count": len(self.api.list_positions())
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_positions(self) -> List[Dict]:
        try:
            positions = self.api.list_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "qty": float(pos.qty),
                    "avg_fill_price": float(pos.avg_fill_price),
                    "market_value": float(pos.market_value),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                    "current_price": float(pos.current_price)
                }
                for pos in positions
            ]
        except Exception as e:
            return {"error": str(e)}

    async def get_portfolio_value(self) -> float:
        try:
            account = self.api.get_account()
            return float(account.portfolio_value)
        except Exception:
            return 0.0

    async def buy(self, symbol: str, qty: int, order_type: str = 'market', limit_price: Optional[float] = None) -> Dict:
        try:
            if order_type == 'limit' and limit_price:
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='limit',
                    limit_price=limit_price,
                    time_in_force='day'
                )
            else:
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
            
            return {
                "order_id": order.id,
                "symbol": order.symbol,
                "qty": order.qty,
                "side": order.side,
                "status": order.status,
                "filled_at": order.filled_at,
                "filled_qty": order.filled_qty,
                "filled_avg_price": order.filled_avg_price
            }
        except Exception as e:
            return {"error": str(e)}

    async def sell(self, symbol: str, qty: int, order_type: str = 'market', limit_price: Optional[float] = None) -> Dict:
        try:
            if order_type == 'limit' and limit_price:
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='limit',
                    limit_price=limit_price,
                    time_in_force='day'
                )
            else:
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='day'
                )
            
            return {
                "order_id": order.id,
                "symbol": order.symbol,
                "qty": order.qty,
                "side": order.side,
                "status": order.status,
                "filled_at": order.filled_at
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_order_status(self, order_id: str) -> Dict:
        try:
            order = self.api.get_order(order_id)
            return {
                "order_id": order.id,
                "status": order.status,
                "filled_qty": order.filled_qty,
                "filled_avg_price": order.filled_avg_price,
                "created_at": order.created_at
            }
        except Exception as e:
            return {"error": str(e)}

    async def cancel_order(self, order_id: str) -> bool:
        try:
            self.api.cancel_order(order_id)
            return True
        except Exception:
            return False

    async def get_market_data(self, symbol: str) -> Dict:
        try:
            bars = self.api.get_barset(symbol, 'day', limit=1)
            bar = bars[symbol][0]
            
            return {
                "symbol": symbol,
                "open": bar.o,
                "high": bar.h,
                "low": bar.l,
                "close": bar.c,
                "volume": bar.v,
                "time": bar.t.isoformat() if bar.t else None
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_historical_data(self, symbol: str, timeframe: str = 'day', limit: int = 100) -> List[Dict]:
        try:
            bars = self.api.get_barset(symbol, timeframe, limit=limit)
            return [
                {
                    "open": bar.o,
                    "high": bar.h,
                    "low": bar.l,
                    "close": bar.c,
                    "volume": bar.v,
                    "time": bar.t.isoformat() if bar.t else None
                }
                for bar in bars[symbol]
            ]
        except Exception as e:
            return {"error": str(e)}

    async def liquidate_all(self) -> Dict:
        try:
            orders = self.api.close_all_positions()
            return {
                "liquidated_count": len(orders) if orders else 0,
                "status": "success"
            }
        except Exception as e:
            return {"error": str(e)}

