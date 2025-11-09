/**
 * Alpaca Services Index
 * Main export file for all Alpaca trading services
 * 
 * @example
 * ```typescript
 * // Use the unified service
 * import { AlpacaService } from '@/services';
 * const alpaca = new AlpacaService();
 * 
 * // Or use individual services
 * import { TradingService, MarketDataService } from '@/services';
 * 
 * // Or use React hooks
 * import { useDashboard, useStockPrice } from '@/services/hooks';
 * ```
 */

// Core Client
export { AlpacaClient } from './AlpacaClient';

// Services
export { AccountService } from './AccountService';
export { TradingService } from './TradingService';
export { AssetService } from './AssetService';
export { MarketDataService } from './MarketDataService';
export { WatchlistService } from './WatchlistService';
export { ClockService } from './ClockService';

// Configuration
export { getAlpacaConfig, ALPACA_URLS } from './alpaca.config';
export type { AlpacaConfig } from './alpaca.config';

// Types
export type {
  Account,
  Position,
  Order,
  CreateOrderRequest,
  OrderSide,
  OrderType,
  OrderStatus,
  TimeInForce,
  Asset,
  Watchlist,
  CreateWatchlistRequest,
  Clock,
  Calendar,
  PortfolioHistory,
  Bar,
  Quote,
  Trade,
  Snapshot,
  News,
  Activity,
  ActivityType,
  AlpacaError,
} from './alpaca.types';

// Utilities
export { AlpacaUtils } from './utils';
export * from './utils';

// ==================== UNIFIED ALPACA SERVICE ====================

import { AccountService } from './AccountService';
import { TradingService } from './TradingService';
import { AssetService } from './AssetService';
import { MarketDataService } from './MarketDataService';
import { WatchlistService } from './WatchlistService';
import { ClockService } from './ClockService';
import type { AlpacaConfig } from './alpaca.config';
import type { Account, Position, Order, Asset, Snapshot, News } from './alpaca.types';

/**
 * Unified Alpaca Service
 * All-in-one service that combines all Alpaca functionality
 */
export class AlpacaService {
  public account: AccountService;
  public trading: TradingService;
  public assets: AssetService;
  public marketData: MarketDataService;
  public watchlists: WatchlistService;
  public clock: ClockService;

  constructor(config?: Partial<AlpacaConfig>) {
    this.account = new AccountService(config);
    this.trading = new TradingService(config);
    this.assets = new AssetService(config);
    this.marketData = new MarketDataService(config);
    this.watchlists = new WatchlistService(config);
    this.clock = new ClockService(config);
  }

  /**
   * Quick initialization check
   */
  async initialize(): Promise<{
    success: boolean;
    account?: Account;
    marketOpen?: boolean;
    error?: string;
  }> {
    try {
      const [account, clock] = await Promise.all([
        this.account.getAccount(),
        this.clock.getClock(),
      ]);

      return {
        success: true,
        account,
        marketOpen: clock.is_open,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Initialization failed',
      };
    }
  }

  /**
   * Get comprehensive dashboard data
   */
  async getDashboardData(): Promise<{
    account: Account;
    positions: Position[];
    openOrders: Order[];
    marketStatus: any;
    portfolioValue: number;
    todayProfitLoss: number;
    todayProfitLossPercent: number;
  }> {
    const [account, positions, openOrders, marketStatus] = await Promise.all([
      this.account.getAccount(),
      this.trading.getPositions(),
      this.trading.getOrders({ status: 'open' }),
      this.clock.getMarketStatus(),
    ]);

    const portfolioValue = parseFloat(account.portfolio_value);
    const lastEquity = parseFloat(account.last_equity);
    const todayProfitLoss = portfolioValue - lastEquity;
    const todayProfitLossPercent = lastEquity > 0 ? (todayProfitLoss / lastEquity) * 100 : 0;

    return {
      account,
      positions,
      openOrders,
      marketStatus,
      portfolioValue,
      todayProfitLoss,
      todayProfitLossPercent,
    };
  }

  /**
   * Quick buy with validation
   */
  async quickBuy(symbol: string, qty: number): Promise<Order> {
    // Validate asset
    const asset = await this.assets.getAsset(symbol);
    if (!asset.tradable) {
      throw new Error(`${symbol} is not tradable`);
    }

    // Check market status
    const canTrade = await this.account.canTrade();
    if (!canTrade.canTrade) {
      throw new Error(`Cannot trade: ${canTrade.reasons.join(', ')}`);
    }

    // Place order
    return await this.trading.buy(symbol, qty);
  }

  /**
   * Quick sell with validation
   */
  async quickSell(symbol: string, qty: number): Promise<Order> {
    // Check if we have a position
    try {
      const position = await this.trading.getPosition(symbol);
      const availableQty = parseFloat(position.qty_available);
      
      if (qty > availableQty) {
        throw new Error(`Insufficient quantity. Available: ${availableQty}`);
      }
    } catch (error) {
      throw new Error(`No position found for ${symbol}`);
    }

    // Place order
    return await this.trading.sell(symbol, qty);
  }

  /**
   * Get symbol overview with all relevant data
   */
  async getSymbolOverview(symbol: string): Promise<{
    asset: Asset;
    currentPrice: number;
    priceChange: any;
    snapshot: Snapshot;
    position?: Position;
    hasPosition: boolean;
    news: News[];
  }> {
    const [asset, snapshot, news] = await Promise.all([
      this.assets.getAsset(symbol),
      this.marketData.getSnapshot(symbol),
      this.marketData.getNews({ symbols: symbol, limit: 10 }),
    ]);

    const priceChange = await this.marketData.getPriceChange(symbol);
    
    let position: Position | undefined;
    let hasPosition = false;
    
    try {
      position = await this.trading.getPosition(symbol);
      hasPosition = true;
    } catch (error) {
      // No position
    }

    return {
      asset,
      currentPrice: snapshot.latestTrade.p,
      priceChange,
      snapshot,
      position,
      hasPosition,
      news,
    };
  }
}

// Create a default instance
let defaultInstance: AlpacaService | null = null;

/**
 * Get or create the default Alpaca service instance
 */
export function getAlpacaService(config?: Partial<AlpacaConfig>): AlpacaService {
  if (!defaultInstance || config) {
    defaultInstance = new AlpacaService(config);
  }
  return defaultInstance;
}

export default AlpacaService;
