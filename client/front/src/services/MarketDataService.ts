/**
 * Market Data Service
 * Proxies market data requests through the backend API for security
 * All Alpaca credentials and direct API access is managed server-side
 */

import type { Bar, Quote, Trade, Snapshot, News } from "./alpaca.types";
import { BackendAPI } from "./BackendAPI";

export class MarketDataService {
  // ==================== QUOTES ====================

  /**
   * Get latest quote for a symbol through backend API
   */
  async getLatestQuote(symbol: string): Promise<Quote> {
    return await BackendAPI.market.getQuote(symbol);
  }

  /**
   * Get quotes for multiple symbols
   */
  async getLatestQuotes(symbols: string[]): Promise<Record<string, Quote>> {
    const result: Record<string, Quote> = {};

    // Fetch quotes for each symbol in parallel through backend
    await Promise.all(
      symbols.map(async (symbol) => {
        try {
          result[symbol] = await BackendAPI.market.getQuote(symbol);
        } catch (error) {
          console.error(`Error fetching quote for ${symbol}:`, error);
          // Return empty quote on error
          result[symbol] = {
            ax: "", ap: 0, as: 0,
            bx: "", bp: 0, bs: 0,
            t: new Date().toISOString(),
            c: [], z: ""
          };
        }
      }),
    );

    return result;
  }

  // ==================== BARS (CANDLES) ====================

  /**
   * Get historical bars for a symbol through backend API
   * Note: Currently limited - backend should implement full historical endpoint
   */
  async getBars(
    symbol: string,
    params: {
      start?: string | Date;
      end?: string | Date;
      timeframe?:
        | "1Min"
        | "5Min"
        | "15Min"
        | "30Min"
        | "1Hour"
        | "1Day"
        | "1Week"
        | "1Month";
      limit?: number;
      adjustment?: "raw" | "split" | "dividend" | "all";
      feed?: "iex" | "sip";
    },
  ): Promise<Bar[]> {
    try {
      // Use backend API to fetch current quote and construct a bar
      // TODO: Backend should implement /api/market/{symbol}/bars endpoint
      const quote = await BackendAPI.market.getQuote(symbol);

      const bar: Bar = {
        t: new Date().toISOString(),
        o: quote.ap || 0,
        h: quote.ap || 0,
        l: quote.bp || 0,
        c: quote.ap || 0,
        v: 0,
        n: 1,
        vw: quote.ap || 0,
      };

      return [bar];
    } catch (error) {
      console.error("Error fetching bars:", error);
      return [];
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
      timeframe?:
        | "1Min"
        | "5Min"
        | "15Min"
        | "30Min"
        | "1Hour"
        | "1Day"
        | "1Week"
        | "1Month";
      limit?: number;
      adjustment?: "raw" | "split" | "dividend" | "all";
      feed?: "iex" | "sip";
    },
  ): Promise<Record<string, Bar[]>> {
    const result: Record<string, Bar[]> = {};

    await Promise.all(
      symbols.map(async (symbol) => {
        try {
          result[symbol] = await this.getBars(symbol, params);
        } catch (error) {
          result[symbol] = [];
        }
      }),
    );

    return result;
  }

  /**
   * Get latest bar for a symbol
   */
  async getLatestBar(symbol: string): Promise<Bar> {
    const bars = await this.getBars(symbol, { limit: 1 });
    return bars[0] || {
      t: new Date().toISOString(),
      o: 0, h: 0, l: 0, c: 0, v: 0, n: 0, vw: 0
    };
  }

  // ==================== TRADES ====================

  /**
   * Get latest trade for a symbol
   * Uses quote data as proxy since backend doesn't have separate trade endpoint
   */
  async getLatestTrade(symbol: string): Promise<Trade> {
    const quote = await BackendAPI.market.getQuote(symbol);

    return {
      t: quote.t,
      x: quote.ax,
      p: quote.ap,
      s: quote.as,
      c: quote.c,
      i: 0,
      z: quote.z,
    };
  }

  /**
   * Get trades for multiple symbols
   */
  async getLatestTrades(symbols: string[]): Promise<Record<string, Trade>> {
    const result: Record<string, Trade> = {};

    await Promise.all(
      symbols.map(async (symbol) => {
        try {
          result[symbol] = await this.getLatestTrade(symbol);
        } catch (error) {
          console.error(`Error fetching trade for ${symbol}:`, error);
        }
      }),
    );

    return result;
  }

  // ==================== SNAPSHOTS ====================

  /**
   * Get snapshot for a symbol (comprehensive current data)
   * Constructs snapshot from available backend data
   */
  async getSnapshot(symbol: string): Promise<Snapshot> {
    const quote = await BackendAPI.market.getQuote(symbol);

    // Construct a basic snapshot from quote data
    return {
      latestTrade: {
        t: quote.t,
        x: quote.ax,
        p: quote.ap,
        s: quote.as,
        c: quote.c,
        i: 0,
        z: quote.z,
      },
      latestQuote: quote,
      minuteBar: {
        t: new Date().toISOString(),
        o: quote.ap, h: quote.ap, l: quote.bp, c: quote.ap,
        v: 0, n: 1, vw: quote.ap
      },
      dailyBar: {
        t: new Date().toISOString(),
        o: quote.o || quote.ap,
        h: quote.h || quote.ap,
        l: quote.l || quote.bp,
        c: quote.c || quote.ap,
        v: quote.v || 0,
        n: 1,
        vw: quote.ap
      },
      prevDailyBar: {
        t: new Date(Date.now() - 86400000).toISOString(),
        o: quote.o || quote.ap,
        h: quote.h || quote.ap,
        l: quote.l || quote.bp,
        c: quote.c || quote.ap,
        v: quote.v || 0,
        n: 1,
        vw: quote.ap
      },
    };
  }

  /**
   * Get snapshots for multiple symbols
   */
  async getSnapshots(symbols: string[]): Promise<Record<string, Snapshot>> {
    const result: Record<string, Snapshot> = {};

    await Promise.all(
      symbols.map(async (symbol) => {
        try {
          result[symbol] = await this.getSnapshot(symbol);
        } catch (error) {
          console.error(`Error fetching snapshot for ${symbol}:`, error);
        }
      }),
    );

    return result;
  }

  // ==================== NEWS ====================

  /**
   * Get news articles
   * TODO: Backend should implement news endpoint
   */
  async getNews(params?: {
    symbols?: string | string[];
    start?: string | Date;
    end?: string | Date;
    limit?: number;
    sort?: "asc" | "desc";
  }): Promise<News[]> {
    console.warn("News endpoint not yet implemented in backend");
    return [];
  }

  // ==================== ANALYSIS & UTILITIES ====================

  /**
   * Get current price for a symbol
   */
  async getCurrentPrice(symbol: string): Promise<number> {
    const quote = await BackendAPI.market.getQuote(symbol);
    return quote.ap || 0;
  }

  /**
   * Get current prices for multiple symbols
   */
  async getCurrentPrices(symbols: string[]): Promise<Record<string, number>> {
    const quotes = await this.getLatestQuotes(symbols);
    const prices: Record<string, number> = {};

    for (const [symbol, quote] of Object.entries(quotes)) {
      prices[symbol] = quote.ap || 0;
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
    const quote = await BackendAPI.market.getQuote(symbol);
    const spread = quote.ap - quote.bp;
    const spreadPercent = quote.bp > 0 ? (spread / quote.bp) * 100 : 0;

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
    const quote = await BackendAPI.market.getQuote(symbol);

    return {
      symbol,
      currentPrice: quote.ap || 0,
      dayHigh: quote.h || 0,
      dayLow: quote.l || 0,
      dayOpen: quote.o || 0,
      volume: quote.v || 0,
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
    const quote = await BackendAPI.market.getQuote(symbol);
    const currentPrice = quote.ap || 0;
    const previousClose = quote.c || currentPrice;
    const change = currentPrice - previousClose;
    const changePercent =
      previousClose > 0 ? (change / previousClose) * 100 : 0;

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
      const quote = await BackendAPI.market.getQuote(symbol);
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
  async getMarketMovers(
    symbols: string[],
    count: number = 10,
  ): Promise<{
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
      }),
    );

    const validChanges = changes.filter(
      (c): c is NonNullable<typeof c> => c !== null,
    );

    const sorted = [...validChanges].sort(
      (a, b) => b.changePercent - a.changePercent,
    );

    return {
      topGainers: sorted.slice(0, count).map((c) => ({
        symbol: c.symbol,
        changePercent: c.changePercent,
        price: c.currentPrice,
      })),
      topLosers: sorted
        .slice(-count)
        .reverse()
        .map((c) => ({
          symbol: c.symbol,
          changePercent: c.changePercent,
          price: c.currentPrice,
        })),
    };
  }
}

export default MarketDataService;
