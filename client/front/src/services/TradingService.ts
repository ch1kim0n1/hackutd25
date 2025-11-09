/**
 * Trading Service
 * Handles all trading operations: orders, positions, and executions
 */

import { AlpacaClient } from './AlpacaClient';
import type { 
  Order, 
  Position, 
  CreateOrderRequest,
  OrderSide,
  OrderType,
  TimeInForce,
  OrderStatus
} from './alpaca.types';

export class TradingService extends AlpacaClient {
  // ==================== ORDERS ====================

  /**
   * Create a new order
   */
  async createOrder(orderRequest: CreateOrderRequest): Promise<Order> {
    try {
      const order = await this.client.createOrder(orderRequest);
      return order as Order;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Place a market order (simplified)
   */
  async marketOrder(
    symbol: string,
    qty: number,
    side: OrderSide,
    timeInForce: TimeInForce = 'gtc'
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: 'market',
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
    timeInForce: TimeInForce = 'gtc'
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: 'limit',
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
    timeInForce: TimeInForce = 'gtc'
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: 'stop',
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
    timeInForce: TimeInForce = 'gtc'
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: 'stop_limit',
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
    timeInForce: TimeInForce = 'gtc'
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: 'trailing_stop',
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
    stopLossPrice: number
  ): Promise<Order> {
    return this.createOrder({
      symbol,
      qty,
      side,
      type: 'limit',
      limit_price: entryPrice,
      time_in_force: 'gtc',
      order_class: 'bracket',
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
    status?: OrderStatus | 'all' | 'open' | 'closed';
    limit?: number;
    after?: string;
    until?: string;
    direction?: 'asc' | 'desc';
    nested?: boolean;
    symbols?: string;
  }): Promise<Order[]> {
    try {
      const orders = await this.client.getOrders(params);
      return orders as Order[];
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get a specific order by ID
   */
  async getOrder(orderId: string): Promise<Order> {
    try {
      const order = await this.client.getOrder(orderId);
      return order as Order;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get order by client order ID
   */
  async getOrderByClientId(clientOrderId: string): Promise<Order> {
    try {
      const order = await this.client.getOrderByClientOrderId(clientOrderId);
      return order as Order;
    } catch (error) {
      return this.handleError(error);
    }
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
    }
  ): Promise<Order> {
    try {
      const order = await this.client.replaceOrder(orderId, updates);
      return order as Order;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Cancel an order
   */
  async cancelOrder(orderId: string): Promise<void> {
    try {
      await this.client.cancelOrder(orderId);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Cancel all orders
   */
  async cancelAllOrders(): Promise<Order[]> {
    try {
      const cancelledOrders = await this.client.cancelAllOrders();
      return cancelledOrders as Order[];
    } catch (error) {
      return this.handleError(error);
    }
  }

  // ==================== POSITIONS ====================

  /**
   * Get all open positions
   */
  async getPositions(): Promise<Position[]> {
    try {
      const positions = await this.client.getPositions();
      return positions as Position[];
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get a specific position by symbol
   */
  async getPosition(symbol: string): Promise<Position> {
    try {
      const position = await this.client.getPosition(symbol);
      return position as Position;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Close a position
   */
  async closePosition(symbol: string, qty?: number, percentage?: number): Promise<Order> {
    try {
      const order = await this.client.closePosition(symbol, { qty, percentage });
      return order as Order;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Close all positions
   */
  async closeAllPositions(cancelOrders: boolean = false): Promise<Order[]> {
    try {
      const orders = await this.client.closeAllPositions({ cancel_orders: cancelOrders });
      return orders as Order[];
    } catch (error) {
      return this.handleError(error);
    }
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
      
      const totalValue = positions.reduce((sum, pos) => sum + parseFloat(pos.market_value), 0);
      const totalProfitLoss = positions.reduce((sum, pos) => sum + parseFloat(pos.unrealized_pl), 0);
      const totalCostBasis = positions.reduce((sum, pos) => sum + parseFloat(pos.cost_basis), 0);
      const totalProfitLossPercent = totalCostBasis > 0 ? (totalProfitLoss / totalCostBasis) * 100 : 0;

      const sortedByPL = [...positions].sort((a, b) => 
        parseFloat(b.unrealized_plpc) - parseFloat(a.unrealized_plpc)
      );

      return {
        totalPositions: positions.length,
        totalValue,
        totalProfitLoss,
        totalProfitLossPercent,
        longPositions: positions.filter(p => p.side === 'long').length,
        shortPositions: positions.filter(p => p.side === 'short').length,
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
      const orders = await this.getOrders({ status: 'open' });
      
      const totalValue = orders.reduce((sum, order) => {
        const price = parseFloat(order.limit_price || order.stop_price || '0');
        const qty = parseFloat(order.qty || '0');
        return sum + (price * qty);
      }, 0);

      const ordersByType = orders.reduce((acc, order) => {
        acc[order.type] = (acc[order.type] || 0) + 1;
        return acc;
      }, {} as Record<OrderType, number>);

      return {
        totalOrders: orders.length,
        buyOrders: orders.filter(o => o.side === 'buy').length,
        sellOrders: orders.filter(o => o.side === 'sell').length,
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
    return this.marketOrder(symbol, qty, 'buy');
  }

  /**
   * Quick sell - market order sell
   */
  async sell(symbol: string, qty: number): Promise<Order> {
    return this.marketOrder(symbol, qty, 'sell');
  }

  /**
   * Buy with dollar amount instead of quantity
   */
  async buyDollarAmount(symbol: string, dollarAmount: number): Promise<Order> {
    return this.createOrder({
      symbol,
      notional: dollarAmount,
      side: 'buy',
      type: 'market',
      time_in_force: 'day',
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
