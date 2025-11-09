/**
 * Trading Service
 * Handles all trading operations: orders, positions, and executions
 */

import type {
  Order,
  Position,
  CreateOrderRequest,
  OrderSide,
  OrderType,
  TimeInForce,
  OrderStatus,
} from "./alpaca.types";

import { AlpacaClient } from "./AlpacaClient";

export class TradingService extends AlpacaClient {
  // ==================== ORDERS ====================

  /**
   * Create a new order
   */
  async createOrder(orderRequest: CreateOrderRequest): Promise<Order> {
    return this.request<Order>("POST", "/v2/orders", orderRequest);
  }

  /**
   * Place a market order (simplified)
   */
  async marketOrder(
    symbol: string,
    qty: number,
    side: OrderSide,
    timeInForce: TimeInForce = "gtc",
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: "market",
      time_in_force: timeInForce,
    });
  }

  /**
   * Place a limit order (simplified)
   */
  async limitOrder(
    symbol: string,
    qty: number,
    side: OrderSide,
    limitPrice: number,
    timeInForce: TimeInForce = "gtc",
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: "limit",
      limit_price: limitPrice,
      time_in_force: timeInForce,
    });
  }

  /**
   * Place a stop order (simplified)
   */
  async stopOrder(
    symbol: string,
    qty: number,
    side: OrderSide,
    stopPrice: number,
    timeInForce: TimeInForce = "gtc",
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: "stop",
      stop_price: stopPrice,
      time_in_force: timeInForce,
    });
  }

  /**
   * Place a stop limit order (simplified)
   */
  async stopLimitOrder(
    symbol: string,
    qty: number,
    side: OrderSide,
    stopPrice: number,
    limitPrice: number,
    timeInForce: TimeInForce = "gtc",
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: "stop_limit",
      stop_price: stopPrice,
      limit_price: limitPrice,
      time_in_force: timeInForce,
    });
  }

  /**
   * Place a trailing stop order (simplified)
   */
  async trailingStopOrder(
    symbol: string,
    qty: number,
    side: OrderSide,
    trailPercent: number,
    timeInForce: TimeInForce = "gtc",
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: "trailing_stop",
      trail_percent: trailPercent,
      time_in_force: timeInForce,
    });
  }

  /**
   * Place a bracket order (entry with take profit and stop loss)
   */
  async bracketOrder(
    symbol: string,
    qty: number,
    side: OrderSide,
    entryPrice: number,
    takeProfitPrice: number,
    stopLossPrice: number,
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: "limit",
      limit_price: entryPrice,
      time_in_force: "gtc",
      order_class: "bracket",
      take_profit: {
        limit_price: takeProfitPrice,
      },
      stop_loss: {
        stop_price: stopLossPrice,
      },
    });
  }

  /**
   * Get all orders
   */
  async getOrders(params?: {
    status?: OrderStatus | "all" | "open" | "closed";
    limit?: number;
    after?: string;
    until?: string;
    direction?: "asc" | "desc";
    nested?: boolean;
    symbols?: string;
  }): Promise<Order[]> {
    const queryParams = new URLSearchParams(params as any).toString();
    const endpoint = `/v2/orders${queryParams ? `?${queryParams}` : ""}`;

    return this.request<Order[]>("GET", endpoint);
  }

  /**
   * Get a specific order by ID
   */
  async getOrder(orderId: string): Promise<Order> {
    return this.request<Order>("GET", `/v2/orders/${orderId}`);
  }

  /**
   * Get order by client order ID
   */
  async getOrderByClientId(clientOrderId: string): Promise<Order> {
    return this.request<Order>(
      "GET",
      `/v2/orders:by_client_order_id?client_order_id=${clientOrderId}`,
    );
  }

  /**
   * Replace an existing order
   */
  async replaceOrder(
    orderId: string,
    updates: {
      qty?: number;
      limit_price?: number;
      stop_price?: number;
      trail?: number;
      time_in_force?: TimeInForce;
      client_order_id?: string;
    },
  ): Promise<Order> {
    return this.request<Order>("PATCH", `/v2/orders/${orderId}`, updates);
  }

  /**
   * Cancel an order
   */
  async cancelOrder(orderId: string): Promise<void> {
    await this.request<void>("DELETE", `/v2/orders/${orderId}`);
  }

  /**
   * Cancel all orders
   */
  async cancelAllOrders(): Promise<Order[]> {
    return this.request<Order[]>("DELETE", "/v2/orders");
  }

  // ==================== POSITIONS ====================

  /**
   * Get all open positions
   */
  async getPositions(): Promise<Position[]> {
    return this.request<Position[]>("GET", "/v2/positions");
  }

  /**
   * Get a specific position by symbol
   */
  async getPosition(symbol: string): Promise<Position> {
    return this.request<Position>("GET", `/v2/positions/${symbol}`);
  }

  /**
   * Close a position
   */
  async closePosition(
    symbol: string,
    qty?: number,
    percentage?: number,
  ): Promise<Order> {
    const params: any = {};

    if (qty) params.qty = qty;
    if (percentage) params.percentage = percentage;
    const queryParams = new URLSearchParams(params).toString();
    const endpoint = `/v2/positions/${symbol}${queryParams ? `?${queryParams}` : ""}`;

    return this.request<Order>("DELETE", endpoint);
  }

  /**
   * Close all positions
   */
  async closeAllPositions(cancelOrders: boolean = false): Promise<Order[]> {
    const endpoint = `/v2/positions?cancel_orders=${cancelOrders}`;

    return this.request<Order[]>("DELETE", endpoint);
  }

  // ==================== ANALYSIS & UTILITIES ====================

  /**
   * Get position summary
   */
  async getPositionsSummary(): Promise<{
    totalPositions: number;
    totalValue: number;
    totalProfitLoss: number;
    totalProfitLossPercent: number;
    longPositions: number;
    shortPositions: number;
    topGainers: Position[];
    topLosers: Position[];
  }> {
    try {
      const positions = await this.getPositions();

      const totalValue = positions.reduce(
        (sum, pos) => sum + parseFloat(pos.market_value),
        0,
      );
      const totalProfitLoss = positions.reduce(
        (sum, pos) => sum + parseFloat(pos.unrealized_pl),
        0,
      );
      const totalCostBasis = positions.reduce(
        (sum, pos) => sum + parseFloat(pos.cost_basis),
        0,
      );
      const totalProfitLossPercent =
        totalCostBasis > 0 ? (totalProfitLoss / totalCostBasis) * 100 : 0;

      const sortedByPL = [...positions].sort(
        (a, b) => parseFloat(b.unrealized_plpc) - parseFloat(a.unrealized_plpc),
      );

      return {
        totalPositions: positions.length,
        totalValue,
        totalProfitLoss,
        totalProfitLossPercent,
        longPositions: positions.filter((p) => p.side === "long").length,
        shortPositions: positions.filter((p) => p.side === "short").length,
        topGainers: sortedByPL.slice(0, 5),
        topLosers: sortedByPL.slice(-5).reverse(),
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get open orders summary
   */
  async getOpenOrdersSummary(): Promise<{
    totalOrders: number;
    buyOrders: number;
    sellOrders: number;
    totalValue: number;
    ordersByType: Record<OrderType, number>;
  }> {
    try {
      const orders = await this.getOrders({ status: "open" });

      const totalValue = orders.reduce((sum, order) => {
        const price = parseFloat(order.limit_price || order.stop_price || "0");
        const qty = parseFloat(order.qty || "0");

        return sum + price * qty;
      }, 0);

      const ordersByType = orders.reduce(
        (acc, order) => {
          acc[order.type] = (acc[order.type] || 0) + 1;

          return acc;
        },
        {} as Record<OrderType, number>,
      );

      return {
        totalOrders: orders.length,
        buyOrders: orders.filter((o) => o.side === "buy").length,
        sellOrders: orders.filter((o) => o.side === "sell").length,
        totalValue,
        ordersByType,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Quick buy - market order buy
   */
  async buy(symbol: string, qty: number): Promise<Order> {
    return this.marketOrder(symbol, qty, "buy");
  }

  /**
   * Quick sell - market order sell
   */
  async sell(symbol: string, qty: number): Promise<Order> {
    return this.marketOrder(symbol, qty, "sell");
  }

  /**
   * Buy with dollar amount instead of quantity
   */
  async buyDollarAmount(symbol: string, dollarAmount: number): Promise<Order> {
    return this.createOrder({
      symbol,
      notional: dollarAmount,
      side: "buy",
      type: "market",
      time_in_force: "day",
    });
  }

  /**
   * Sell entire position
   */
  async sellAll(symbol: string): Promise<Order> {
    return this.closePosition(symbol);
  }
}

export default TradingService;
