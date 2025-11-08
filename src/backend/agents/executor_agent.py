import asyncio
from typing import Dict, List
from datetime import datetime
import uuid
import numpy as np

class ExecutorAgent:
    def __init__(self, agent_network, broker):
        self.agent_network = agent_network
        self.name = "Executor Agent"
        self.pending_orders = []
        self.execution_history = []
        self.broker = broker

    async def initialize(self):
        await self.agent_network.subscribe("execute_trade", self.handle_trade_request)
        await self.agent_network.subscribe("execute_emergency_sell", self.handle_emergency_sell)
        return {"status": "initialized", "agent": self.name}

    async def handle_trade_request(self, message):
        trade_data = message.get("data", {})
        result = await self.execute_trade(trade_data)
        
        await self.agent_network.publish("trade_executed", {
            "trade_id": result["trade_id"],
            "status": result["status"],
            "execution_details": result
        })

    async def execute_trade(self, trade_data: Dict) -> Dict:
        trade_id = str(uuid.uuid4())
        
        orders = self.create_orders(trade_data)
        
        execution_report = {
            "trade_id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "orders": [],
            "total_value": trade_data.get("total_value", 0),
            "status": "pending"
        }
        
        for order in orders:
            order_result = await self.execute_single_order(order)
            execution_report["orders"].append(order_result)
        
        slippage_total = sum(order["slippage"] for order in execution_report["orders"])
        execution_report["total_slippage"] = slippage_total
        execution_report["status"] = "completed"
        
        self.execution_history.append(execution_report)
        
        await self.agent_network.broadcast_agent_communication(
            self.name,
            "Explainer Agent",
            f"Trade execution complete. Total slippage: {slippage_total:.2f}%"
        )
        
        return execution_report

    def create_orders(self, trade_data: Dict) -> List[Dict]:
        orders = []
        
        trades = trade_data.get("trades", [])
        for symbol, details in trades.items():
            order = {
                "symbol": symbol,
                "side": details.get("side", "buy"),
                "quantity": details.get("quantity", 0),
                "order_type": details.get("order_type", "market"),
                "price_limit": details.get("price_limit"),
                "time_in_force": details.get("time_in_force", "day"),
                "algo": details.get("algo", "vwap")
            }
            orders.append(order)
        
        return orders

    async def execute_single_order(self, order: Dict) -> Dict:
        symbol = order["symbol"]
        side = order["side"]
        quantity = order["quantity"]
        order_type = order["order_type"]
        
        execution_price = await self.get_market_price(symbol)
        if order_type == "limit" and order.get("price_limit"):
            execution_price = self.apply_limit_price(execution_price, order["price_limit"], side)
        
        slippage = self.calculate_slippage(order_type, execution_price, quantity)
        
        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "execution_price": execution_price,
            "order_type": order_type,
            "slippage": slippage,
            "execution_time": np.random.uniform(0.5, 5.0),
            "exchange": "SMART",
            "status": "filled"
        }

    async def get_market_price(self, symbol: str) -> float:
        try:
            market_data = await self.broker.get_market_data(symbol)
            return market_data["close"]
        except Exception:
            np.random.seed(hash(symbol) % 1000)
            base_prices = {
                "QQQ": 487.23,
                "ARKK": 51.89,
                "XLP": 79.12,
                "XLU": 68.45,
                "GLD": 189.34
            }
            
            base_price = base_prices.get(symbol, 100.0)
            return base_price * np.random.uniform(0.98, 1.02)

    def apply_limit_price(self, market_price: float, limit_price: float, side: str) -> float:
        if side == "buy" and market_price > limit_price:
            return None
        elif side == "sell" and market_price < limit_price:
            return None
        return market_price

    def calculate_slippage(self, order_type: str, price: float, quantity: int) -> float:
        base_slippage = 0.15 if order_type == "market" else 0.05
        
        if quantity > 1000:
            base_slippage *= 1.5
        
        return np.random.uniform(0, base_slippage)

    async def handle_emergency_sell(self, message):
        positions = message.get("positions", [])
        urgency = message.get("urgency", "normal")
        
        for position in positions:
            emergency_order = {
                "symbol": position,
                "side": "sell",
                "quantity": 100,
                "order_type": "market",
                "algo": "urgent"
            }
            
            result = await self.execute_single_order(emergency_order)
            
            await self.agent_network.broadcast_agent_communication(
                self.name,
                "Risk Agent",
                f"Emergency sell complete for {position}. Price: ${result['execution_price']}"
            )

    async def optimize_order_execution(self, orders: List[Dict]) -> List[Dict]:
        return orders

    async def execute_rebalance(self, current_allocation: Dict, target_allocation: Dict) -> Dict:
        rebalance_trades = {}
        
        for asset in current_allocation:
            current_pct = current_allocation[asset]
            target_pct = target_allocation.get(asset, current_pct)
            
            if abs(current_pct - target_pct) > 2:
                diff_pct = target_pct - current_pct
                trade_value = 10000 * diff_pct / 100
                
                rebalance_trades[asset] = {
                    "side": "buy" if diff_pct > 0 else "sell",
                    "value": abs(trade_value)
                }
        
        result = await self.execute_trade({
            "trades": rebalance_trades,
            "reason": "Portfolio rebalance"
        })
        
        return result

