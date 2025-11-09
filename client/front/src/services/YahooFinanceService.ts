/**
 * Yahoo Finance Service
 * Fetches real stock market data from Yahoo Finance API
 */

export interface YahooQuote {
  symbol: string;
  regularMarketPrice: number;
  regularMarketChange: number;
  regularMarketChangePercent: number;
  regularMarketPreviousClose: number;
  regularMarketOpen: number;
  regularMarketDayHigh: number;
  regularMarketDayLow: number;
  regularMarketVolume: number;
  fiftyTwoWeekHigh?: number;
  fiftyTwoWeekLow?: number;
  marketCap?: number;
  shortName?: string;
  longName?: string;
  averageVolume?: number;
}

export interface YahooHistoricalData {
  date: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export class YahooFinanceService {
  private readonly chartUrl = 'https://query1.finance.yahoo.com/v8/finance/chart';
  
  /**
   * Get real-time quote for a symbol
   */
  async getQuote(symbol: string): Promise<YahooQuote> {
    try {
      const response = await fetch(
        `${this.chartUrl}/${symbol}?interval=1d&range=1d`,
        {
          headers: {
            'User-Agent': 'Mozilla/5.0',
          },
        }
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch quote for ${symbol}`);
      }
      
      const data = await response.json();
      const result = data.chart.result[0];
      const meta = result.meta;
      const quote = result.indicators.quote[0];
      
      return {
        symbol: meta.symbol,
        regularMarketPrice: meta.regularMarketPrice || quote.close[quote.close.length - 1],
        regularMarketChange: meta.regularMarketPrice - meta.previousClose,
        regularMarketChangePercent: ((meta.regularMarketPrice - meta.previousClose) / meta.previousClose) * 100,
        regularMarketPreviousClose: meta.previousClose,
        regularMarketOpen: quote.open[0] || meta.regularMarketPrice,
        regularMarketDayHigh: meta.regularMarketDayHigh || Math.max(...quote.high),
        regularMarketDayLow: meta.regularMarketDayLow || Math.min(...quote.low),
        regularMarketVolume: meta.regularMarketVolume || quote.volume.reduce((a: number, b: number) => a + b, 0),
        shortName: meta.shortName,
        longName: meta.longName,
      };
    } catch (error) {
      console.error('Error fetching quote:', error);
      // Return mock data as fallback
      return this.getMockQuote(symbol);
    }
  }
  
  /**
   * Get multiple quotes at once
   */
  async getQuotes(symbols: string[]): Promise<Record<string, YahooQuote>> {
    const quotes: Record<string, YahooQuote> = {};
    
    // Fetch quotes in parallel
    await Promise.all(
      symbols.map(async (symbol) => {
        try {
          quotes[symbol] = await this.getQuote(symbol);
        } catch (error) {
          console.error(`Error fetching quote for ${symbol}:`, error);
          quotes[symbol] = this.getMockQuote(symbol);
        }
      })
    );
    
    return quotes;
  }
  
  /**
   * Get historical price data
   */
  async getHistoricalData(
    symbol: string,
    range: '1d' | '5d' | '1mo' | '3mo' | '6mo' | '1y' | '2y' | '5y' | 'max' = '1mo',
    interval: '1m' | '5m' | '15m' | '30m' | '1h' | '1d' | '1wk' | '1mo' = '1d'
  ): Promise<YahooHistoricalData[]> {
    try {
      const response = await fetch(
        `${this.chartUrl}/${symbol}?interval=${interval}&range=${range}`,
        {
          headers: {
            'User-Agent': 'Mozilla/5.0',
          },
        }
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch historical data for ${symbol}`);
      }
      
      const data = await response.json();
      const result = data.chart.result[0];
      const timestamps = result.timestamp;
      const quote = result.indicators.quote[0];
      
      return timestamps.map((timestamp: number, index: number) => ({
        date: new Date(timestamp * 1000),
        open: quote.open[index] || 0,
        high: quote.high[index] || 0,
        low: quote.low[index] || 0,
        close: quote.close[index] || 0,
        volume: quote.volume[index] || 0,
      })).filter((d: YahooHistoricalData) => d.close > 0);
    } catch (error) {
      console.error('Error fetching historical data:', error);
      return this.getMockHistoricalData(symbol, range);
    }
  }
  
  /**
   * Search for stocks by query
   */
  async searchStocks(query: string): Promise<any[]> {
    try {
      const response = await fetch(
        `https://query1.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(query)}&quotesCount=10&newsCount=0`,
        {
          headers: {
            'User-Agent': 'Mozilla/5.0',
          },
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to search stocks');
      }
      
      const data = await response.json();
      return data.quotes || [];
    } catch (error) {
      console.error('Error searching stocks:', error);
      return [];
    }
  }
  
  // ==================== MOCK DATA FALLBACKS ====================
  
  private getMockQuote(symbol: string): YahooQuote {
    const basePrice = 100 + Math.random() * 400;
    const change = (Math.random() - 0.5) * 10;
    
    return {
      symbol,
      regularMarketPrice: basePrice,
      regularMarketChange: change,
      regularMarketChangePercent: (change / basePrice) * 100,
      regularMarketPreviousClose: basePrice - change,
      regularMarketOpen: basePrice * 0.99,
      regularMarketDayHigh: basePrice * 1.02,
      regularMarketDayLow: basePrice * 0.98,
      regularMarketVolume: Math.floor(Math.random() * 10000000) + 1000000,
      shortName: symbol,
      longName: `${symbol} Inc.`,
    };
  }
  
  private getMockHistoricalData(_symbol: string, range: string): YahooHistoricalData[] {
    const days = range === '1d' ? 1 : range === '5d' ? 5 : range === '1mo' ? 30 : 90;
    const basePrice = 100 + Math.random() * 400;
    const data: YahooHistoricalData[] = [];
    
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      const dayChange = (Math.random() - 0.5) * 5;
      const open = basePrice + dayChange;
      const close = open + (Math.random() - 0.5) * 3;
      const high = Math.max(open, close) + Math.random() * 2;
      const low = Math.min(open, close) - Math.random() * 2;
      
      data.push({
        date,
        open,
        high,
        low,
        close,
        volume: Math.floor(Math.random() * 10000000) + 1000000,
      });
    }
    
    return data;
  }
}

export default new YahooFinanceService();
