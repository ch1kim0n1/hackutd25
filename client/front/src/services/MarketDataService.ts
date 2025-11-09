/**
 * Market Data Service
 * Handles real-time and historical market data
 */

import { AlpacaClient } from './AlpacaClient';
import type { Bar, Quote, Trade, Snapshot, News } from './alpaca.types';

export class MarketDataService extends AlpacaClient {
  // ==================== BARS (CANDLES) ====================

  /**
   * Get historical bars for a symbol
   */
  async getBars(
    symbol: string,
    params: {
      start?: string | Date;
      end?: string | Date;
      timeframe?: '1Min' | '5Min' | '15Min' | '30Min' | '1Hour' | '1Day' | '1Week' | '1Month';
      limit?: number;
      adjustment?: 'raw' | 'split' | 'dividend' | 'all';
      feed?: 'iex' | 'sip';
    }
  ): Promise<Bar[]> {
    try {
      const response = await this.client.getBarsV2(symbol, {
        start: params.start,
        end: params.end,
        timeframe: params.timeframe || '1Day',
        limit: params.limit,
        adjustment: params.adjustment,
        feed: params.feed,
      });
      
      const bars: Bar[] = [];
      for await (const bar of response) {
        bars.push(bar as Bar);
      }
      return bars;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get bars for multiple symbols
   */
  async getMultiBars(
    symbols: string[],
    params: {
      start?: string | Date;
      end?: string | Date;
      timeframe?: '1Min' | '5Min' | '15Min' | '30Min' | '1Hour' | '1Day' | '1Week' | '1Month';
      limit?: number;
      adjustment?: 'raw' | 'split' | 'dividend' | 'all';
      feed?: 'iex' | 'sip';
    }
  ): Promise<Record<string, Bar[]>> {
    try {
      const response = await this.client.getMultiBarsV2(symbols, {
        start: params.start,
        end: params.end,
        timeframe: params.timeframe || '1Day',
        limit: params.limit,
        adjustment: params.adjustment,
        feed: params.feed,
      });

      const result: Record<string, Bar[]> = {};
      for (const symbol of symbols) {
        result[symbol] = [];
      }

      for await (const bar of response) {
        const symbol = (bar as any).Symbol || (bar as any).symbol;
        if (symbol && result[symbol]) {
          result[symbol].push(bar as Bar);
        }
      }

      return result;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get latest bar for a symbol
   */
  async getLatestBar(symbol: string): Promise<Bar> {
    try {
      const bar = await this.client.getLatestBar(symbol);
      return bar as Bar;
    } catch (error) {
      return this.handleError(error);
    }
  }

  // ==================== QUOTES ====================

  /**
   * Get latest quote for a symbol
   */
  async getLatestQuote(symbol: string): Promise<Quote> {
    try {
      const quote = await this.client.getLatestQuote(symbol);
      return quote as Quote;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get quotes for multiple symbols
   */
  async getLatestQuotes(symbols: string[]): Promise<Record<string, Quote>> {
    try {
      const quotes = await this.client.getLatestQuotes(symbols);
      return quotes as Record<string, Quote>;
    } catch (error) {
      return this.handleError(error);
    }
  }

  // ==================== TRADES ====================

  /**
   * Get latest trade for a symbol
   */
  async getLatestTrade(symbol: string): Promise<Trade> {
    try {
      const trade = await this.client.getLatestTrade(symbol);
      return trade as Trade;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get trades for multiple symbols
   */
  async getLatestTrades(symbols: string[]): Promise<Record<string, Trade>> {
    try {
      const trades = await this.client.getLatestTrades(symbols);
      return trades as Record<string, Trade>;
    } catch (error) {
      return this.handleError(error);
    }
  }

  // ==================== SNAPSHOTS ====================

  /**
   * Get snapshot for a symbol (comprehensive current data)
   */
  async getSnapshot(symbol: string): Promise<Snapshot> {
    try {
      const snapshot = await this.client.getSnapshot(symbol);
      return snapshot as Snapshot;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get snapshots for multiple symbols
   */
  async getSnapshots(symbols: string[]): Promise<Record<string, Snapshot>> {
    try {
      const snapshots = await this.client.getSnapshots(symbols);
      return snapshots as Record<string, Snapshot>;
    } catch (error) {
      return this.handleError(error);
    }
  }

  // ==================== NEWS ====================

  /**
   * Get news articles
   */
  async getNews(params?: {
    symbols?: string | string[];
    start?: string;
    end?: string;
    limit?: number;
    sort?: 'asc' | 'desc';
    include_content?: boolean;
    exclude_contentless?: boolean;
  }): Promise<News[]> {
    try {
      const news = await this.client.getNews(params);
      return news as News[];
    } catch (error) {
      return this.handleError(error);
    }
  }

  // ==================== HELPER METHODS ====================

  /**
   * Get current price for a symbol
   */
  async getCurrentPrice(symbol: string): Promise<number> {
    try {
      const trade = await this.getLatestTrade(symbol);
      return trade.p;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get current prices for multiple symbols
   */
  async getCurrentPrices(symbols: string[]): Promise<Record<string, number>> {
    try {
      const trades = await this.getLatestTrades(symbols);
      const prices: Record<string, number> = {};
      
      for (const [symbol, trade] of Object.entries(trades)) {
        prices[symbol] = trade.p;
      }
      
      return prices;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get intraday data (today's bars)
   */
  async getIntradayBars(
    symbol: string,
    timeframe: '1Min' | '5Min' | '15Min' | '30Min' | '1Hour' = '5Min'
  ): Promise<Bar[]> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return this.getBars(symbol, {
      start: today,
      timeframe,
    });
  }

  /**
   * Get historical daily bars
   */
  async getDailyBars(
    symbol: string,
    days: number = 30
  ): Promise<Bar[]> {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    
    return this.getBars(symbol, {
      start,
      end,
      timeframe: '1Day',
    });
  }

  /**
   * Calculate simple moving average
   */
  async getSMA(
    symbol: string,
    period: number,
    timeframe: '1Min' | '5Min' | '15Min' | '30Min' | '1Hour' | '1Day' = '1Day'
  ): Promise<number | null> {
    try {
      const bars = await this.getBars(symbol, {
        timeframe,
        limit: period,
      });

      if (bars.length < period) {
        return null;
      }

      const sum = bars.reduce((acc, bar) => acc + bar.c, 0);
      return sum / period;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get price change information
   */
  async getPriceChange(symbol: string): Promise<{
    currentPrice: number;
    previousClose: number;
    change: number;
    changePercent: number;
  }> {
    try {
      const snapshot = await this.getSnapshot(symbol);
      const currentPrice = snapshot.latestTrade.p;
      const previousClose = snapshot.prevDailyBar.c;
      const change = currentPrice - previousClose;
      const changePercent = (change / previousClose) * 100;

      return {
        currentPrice,
        previousClose,
        change,
        changePercent,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get market overview for multiple symbols
   */
  async getMarketOverview(symbols: string[]): Promise<Array<{
    symbol: string;
    price: number;
    change: number;
    changePercent: number;
    volume: number;
    high: number;
    low: number;
  }>> {
    try {
      const snapshots = await this.getSnapshots(symbols);
      
      return symbols.map(symbol => {
        const snapshot = snapshots[symbol];
        if (!snapshot) {
          return {
            symbol,
            price: 0,
            change: 0,
            changePercent: 0,
            volume: 0,
            high: 0,
            low: 0,
          };
        }

        const currentPrice = snapshot.latestTrade.p;
        const previousClose = snapshot.prevDailyBar.c;
        const change = currentPrice - previousClose;
        const changePercent = (change / previousClose) * 100;

        return {
          symbol,
          price: currentPrice,
          change,
          changePercent,
          volume: snapshot.dailyBar.v,
          high: snapshot.dailyBar.h,
          low: snapshot.dailyBar.l,
        };
      });
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get volatility (standard deviation of returns)
   */
  async getVolatility(
    symbol: string,
    period: number = 30,
    timeframe: '1Day' | '1Hour' = '1Day'
  ): Promise<number | null> {
    try {
      const bars = await this.getBars(symbol, {
        timeframe,
        limit: period + 1,
      });

      if (bars.length < period + 1) {
        return null;
      }

      // Calculate daily returns
      const returns: number[] = [];
      for (let i = 1; i < bars.length; i++) {
        const returnVal = (bars[i].c - bars[i - 1].c) / bars[i - 1].c;
        returns.push(returnVal);
      }

      // Calculate mean
      const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;

      // Calculate variance
      const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / returns.length;

      // Return standard deviation (volatility)
      return Math.sqrt(variance) * 100; // as percentage
    } catch (error) {
      return null;
    }
  }
}

export default MarketDataService;
