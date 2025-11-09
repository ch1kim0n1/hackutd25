/**
 * Market Data Service
 * Handles real-time and historical market data
 * Browser-compatible version using fetch API
 */

import { AlpacaClient } from './AlpacaClient';
import type { Bar, Quote, Trade, Snapshot, News } from './alpaca.types';

export class MarketDataService extends AlpacaClient {
  private get dataBaseUrl(): string {
    return this.config.dataBaseUrl || 'https://data.alpaca.markets';
  }

  private get headers() {
    return {
      'APCA-API-KEY-ID': this.config.keyId,
      'APCA-API-SECRET-KEY': this.config.secretKey,
    };
  }

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
    const queryParams = new URLSearchParams({
      ...(params.start && { start: typeof params.start === 'string' ? params.start : params.start.toISOString() }),
      ...(params.end && { end: typeof params.end === 'string' ? params.end : params.end.toISOString() }),
      timeframe: params.timeframe || '1Day',
      ...(params.limit && { limit: params.limit.toString() }),
      ...(params.adjustment && { adjustment: params.adjustment }),
      ...(params.feed && { feed: params.feed }),
    }).toString();

    const response = await fetch(`${this.dataBaseUrl}/v2/stocks/${symbol}/bars?${queryParams}`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data.bars || [];
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
    const result: Record<string, Bar[]> = {};
    
    // Fetch bars for each symbol in parallel
    await Promise.all(
      symbols.map(async (symbol) => {
        try {
          result[symbol] = await this.getBars(symbol, params);
        } catch (error) {
          result[symbol] = [];
        }
      })
    );

    return result;
  }

  /**
   * Get latest bar for a symbol
   */
  async getLatestBar(symbol: string): Promise<Bar> {
    const response = await fetch(`${this.dataBaseUrl}/v2/stocks/${symbol}/bars/latest`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data.bar;
  }

  // ==================== QUOTES ====================

  /**
   * Get latest quote for a symbol
   */
  async getLatestQuote(symbol: string): Promise<Quote> {
    const response = await fetch(`${this.dataBaseUrl}/v2/stocks/${symbol}/quotes/latest`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data.quote;
  }

  /**
   * Get quotes for multiple symbols
   */
  async getLatestQuotes(symbols: string[]): Promise<Record<string, Quote>> {
    const symbolsParam = symbols.join(',');
    const response = await fetch(`${this.dataBaseUrl}/v2/stocks/quotes/latest?symbols=${symbolsParam}`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data.quotes || {};
  }

  // ==================== TRADES ====================

  /**
   * Get latest trade for a symbol
   */
  async getLatestTrade(symbol: string): Promise<Trade> {
    const response = await fetch(`${this.dataBaseUrl}/v2/stocks/${symbol}/trades/latest`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data.trade;
  }

  /**
   * Get trades for multiple symbols
   */
  async getLatestTrades(symbols: string[]): Promise<Record<string, Trade>> {
    const symbolsParam = symbols.join(',');
    const response = await fetch(`${this.dataBaseUrl}/v2/stocks/trades/latest?symbols=${symbolsParam}`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data.trades || {};
  }

  // ==================== SNAPSHOTS ====================

  /**
   * Get snapshot for a symbol (comprehensive current data)
   */
  async getSnapshot(symbol: string): Promise<Snapshot> {
    const response = await fetch(`${this.dataBaseUrl}/v2/stocks/${symbol}/snapshot`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data;
  }

  /**
   * Get snapshots for multiple symbols
   */
  async getSnapshots(symbols: string[]): Promise<Record<string, Snapshot>> {
    const symbolsParam = symbols.join(',');
    const response = await fetch(`${this.dataBaseUrl}/v2/stocks/snapshots?symbols=${symbolsParam}`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data || {};
  }

  // ==================== NEWS ====================

  /**
   * Get news articles
   */
  async getNews(params?: {
    symbols?: string | string[];
    start?: string | Date;
    end?: string | Date;
    limit?: number;
    sort?: 'asc' | 'desc';
  }): Promise<News[]> {
    const queryParams = new URLSearchParams({
      ...(params?.symbols && {
        symbols: Array.isArray(params.symbols) ? params.symbols.join(',') : params.symbols
      }),
      ...(params?.start && { start: typeof params.start === 'string' ? params.start : params.start.toISOString() }),
      ...(params?.end && { end: typeof params.end === 'string' ? params.end : params.end.toISOString() }),
      ...(params?.limit && { limit: params.limit.toString() }),
      ...(params?.sort && { sort: params.sort }),
    }).toString();

    const response = await fetch(`${this.dataBaseUrl}/v1beta1/news?${queryParams}`, {
      headers: this.headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError({ response: { status: response.status, data: error }, message: error.message });
    }

    const data = await response.json();
    return data.news || [];
  }

  // ==================== ANALYSIS & UTILITIES ====================

  /**
   * Get current price for a symbol (using latest trade)
   */
  async getCurrentPrice(symbol: string): Promise<number> {
    const trade = await this.getLatestTrade(symbol);
    return trade.p;
  }

  /**
   * Get current prices for multiple symbols
   */
  async getCurrentPrices(symbols: string[]): Promise<Record<string, number>> {
    const trades = await this.getLatestTrades(symbols);
    const prices: Record<string, number> = {};
    
    for (const [symbol, trade] of Object.entries(trades)) {
      prices[symbol] = trade.p;
    }
    
    return prices;
  }

  /**
   * Get price with quote data (bid/ask spread)
   */
  async getPriceWithSpread(symbol: string): Promise<{
    price: number;
    bid: number;
    ask: number;
    spread: number;
    spreadPercent: number;
  }> {
    const quote = await this.getLatestQuote(symbol);
    const spread = quote.ap - quote.bp;
    const spreadPercent = (spread / quote.bp) * 100;

    return {
      price: (quote.bp + quote.ap) / 2,
      bid: quote.bp,
      ask: quote.ap,
      spread,
      spreadPercent,
    };
  }

  /**
   * Get simple price summary
   */
  async getPriceSummary(symbol: string): Promise<{
    symbol: string;
    currentPrice: number;
    dayHigh: number;
    dayLow: number;
    dayOpen: number;
    volume: number;
  }> {
    const snapshot = await this.getSnapshot(symbol);
    
    return {
      symbol,
      currentPrice: snapshot.latestTrade?.p || 0,
      dayHigh: snapshot.dailyBar?.h || 0,
      dayLow: snapshot.dailyBar?.l || 0,
      dayOpen: snapshot.dailyBar?.o || 0,
      volume: snapshot.dailyBar?.v || 0,
    };
  }

  /**
   * Calculate percentage change
   */
  async getPriceChange(symbol: string): Promise<{
    currentPrice: number;
    previousClose: number;
    change: number;
    changePercent: number;
  }> {
    const snapshot = await this.getSnapshot(symbol);
    const currentPrice = snapshot.latestTrade?.p || 0;
    const previousClose = snapshot.prevDailyBar?.c || 0;
    const change = currentPrice - previousClose;
    const changePercent = previousClose > 0 ? (change / previousClose) * 100 : 0;

    return {
      currentPrice,
      previousClose,
      change,
      changePercent,
    };
  }

  /**
   * Check if symbol is trading
   */
  async isTrading(symbol: string): Promise<boolean> {
    try {
      const quote = await this.getLatestQuote(symbol);
      // Check if quote is recent (within last 5 minutes)
      const quoteTime = new Date(quote.t).getTime();
      const now = Date.now();
      const fiveMinutes = 5 * 60 * 1000;
      return now - quoteTime < fiveMinutes;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get market movers
   */
  async getMarketMovers(symbols: string[], count: number = 10): Promise<{
    topGainers: Array<{ symbol: string; changePercent: number; price: number }>;
    topLosers: Array<{ symbol: string; changePercent: number; price: number }>;
  }> {
    const changes = await Promise.all(
      symbols.map(async (symbol) => {
        try {
          const change = await this.getPriceChange(symbol);
          return { symbol, ...change };
        } catch (error) {
          return null;
        }
      })
    );

    const validChanges = changes.filter((c): c is NonNullable<typeof c> => c !== null);
    
    const sorted = [...validChanges].sort((a, b) => b.changePercent - a.changePercent);
    
    return {
      topGainers: sorted.slice(0, count).map(c => ({
        symbol: c.symbol,
        changePercent: c.changePercent,
        price: c.currentPrice,
      })),
      topLosers: sorted.slice(-count).reverse().map(c => ({
        symbol: c.symbol,
        changePercent: c.changePercent,
        price: c.currentPrice,
      })),
    };
  }
}

export default MarketDataService;
