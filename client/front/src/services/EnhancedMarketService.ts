/**
 * Enhanced Market Service
 * Fetches real market data using Yahoo Finance API with infinite pagination
 */

import YahooFinanceService from './YahooFinanceService';
import type { Asset } from '@/types';

// Popular stock symbols categorized
const POPULAR_STOCKS = {
  tech: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'NFLX', 'ADBE', 'CRM', 'ORCL', 'CSCO', 'AVGO', 'QCOM', 'TXN', 'AMAT', 'MU', 'LRCX'],
  finance: ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT'],
  healthcare: ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'ABT', 'DHR', 'LLY', 'BMY', 'AMGN', 'GILD', 'CVS', 'CI', 'HUM'],
  consumer: ['WMT', 'HD', 'PG', 'KO', 'PEP', 'COST', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW', 'DIS', 'CMCSA', 'VZ', 'T'],
  energy: ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL', 'KMI', 'WMB', 'PXD', 'DVN', 'HES'],
  industrial: ['BA', 'HON', 'UPS', 'CAT', 'GE', 'MMM', 'LMT', 'RTX', 'DE', 'UNP', 'FDX', 'NSC', 'CSX', 'EMR', 'ETN'],
  crypto: ['BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'SOL-USD', 'DOGE-USD', 'DOT-USD', 'MATIC-USD', 'AVAX-USD'],
};

// Get all symbols in a flat array
const ALL_SYMBOLS = Object.values(POPULAR_STOCKS).flat();

export interface MarketDataOptions {
  pageSize?: number;
  category?: keyof typeof POPULAR_STOCKS | 'all';
  sortBy?: 'symbol' | 'price' | 'change' | 'volume';
  sortOrder?: 'asc' | 'desc';
  searchQuery?: string;
}

export interface PaginatedMarketData {
  assets: Asset[];
  hasMore: boolean;
  nextPage: number;
  total: number;
}

export class EnhancedMarketService {
  private cache: Map<string, { data: Asset; timestamp: number }> = new Map();
  private readonly CACHE_DURATION = 60000; // 1 minute cache

  /**
   * Get symbols based on category
   */
  private getSymbolsByCategory(category: keyof typeof POPULAR_STOCKS | 'all'): string[] {
    if (category === 'all') {
      return ALL_SYMBOLS;
    }
    return POPULAR_STOCKS[category] || [];
  }

  /**
   * Fetch asset data with Yahoo Finance API
   */
  private async fetchAssetData(symbol: string): Promise<Asset | null> {
    try {
      // Check cache first
      const cached = this.cache.get(symbol);
      if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
        return cached.data;
      }

      // Fetch fresh data
      const quote = await YahooFinanceService.getQuote(symbol);
      
      const asset: Asset = {
        symbol: quote.symbol,
        name: quote.shortName || quote.longName || quote.symbol,
        price: quote.regularMarketPrice,
        dailyChange: quote.regularMarketChangePercent,
        volume: quote.regularMarketVolume,
        marketCap: quote.marketCap || 0,
      };

      // Cache the result
      this.cache.set(symbol, { data: asset, timestamp: Date.now() });

      return asset;
    } catch (error) {
      console.error(`Failed to fetch data for ${symbol}:`, error);
      return null;
    }
  }

  /**
   * Get paginated market data with real Yahoo Finance data
   */
  async getMarketData(
    page: number = 1,
    options: MarketDataOptions = {}
  ): Promise<PaginatedMarketData> {
    const {
      pageSize = 20,
      category = 'all',
      sortBy = 'symbol',
      sortOrder = 'asc',
      searchQuery = '',
    } = options;

    // Get symbols to fetch
    let symbols = this.getSymbolsByCategory(category);

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      symbols = symbols.filter(symbol => 
        symbol.toLowerCase().includes(query)
      );
    }

    const total = symbols.length;
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    
    // Get symbols for current page
    const pageSymbols = symbols.slice(startIndex, endIndex);

    // Fetch data for all symbols in parallel (with rate limiting)
    const BATCH_SIZE = 5; // Fetch 5 at a time to avoid rate limits
    const assets: Asset[] = [];

    for (let i = 0; i < pageSymbols.length; i += BATCH_SIZE) {
      const batch = pageSymbols.slice(i, i + BATCH_SIZE);
      const batchResults = await Promise.all(
        batch.map(symbol => this.fetchAssetData(symbol))
      );
      
      assets.push(...batchResults.filter((asset): asset is Asset => asset !== null));
      
      // Small delay between batches to avoid rate limiting
      if (i + BATCH_SIZE < pageSymbols.length) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    // Apply sorting
    this.sortAssets(assets, sortBy, sortOrder);

    return {
      assets,
      hasMore: endIndex < total,
      nextPage: page + 1,
      total,
    };
  }

  /**
   * Search stocks with Yahoo Finance search API
   */
  async searchStocks(query: string, limit: number = 20): Promise<Asset[]> {
    try {
      const results = await YahooFinanceService.searchStocks(query);
      
      const assets: Asset[] = [];
      const symbols = results
        .filter((r: any) => r.quoteType === 'EQUITY' || r.quoteType === 'CRYPTOCURRENCY')
        .slice(0, limit)
        .map((r: any) => r.symbol);

      // Fetch detailed data for each symbol
      for (const symbol of symbols) {
        const asset = await this.fetchAssetData(symbol);
        if (asset) {
          assets.push(asset);
        }
      }

      return assets;
    } catch (error) {
      console.error('Search failed:', error);
      return [];
    }
  }

  /**
   * Get market movers (gainers and losers)
   */
  async getMarketMovers(): Promise<{
    gainers: Asset[];
    losers: Asset[];
  }> {
    // Fetch all popular stocks
    const allAssets: Asset[] = [];
    
    for (let i = 0; i < ALL_SYMBOLS.length; i += 10) {
      const batch = ALL_SYMBOLS.slice(i, i + 10);
      const batchResults = await Promise.all(
        batch.map(symbol => this.fetchAssetData(symbol))
      );
      
      allAssets.push(...batchResults.filter((asset): asset is Asset => asset !== null));
      
      // Rate limiting
      if (i + 10 < ALL_SYMBOLS.length) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    // Sort by daily change
    const sorted = [...allAssets].sort((a, b) => b.dailyChange - a.dailyChange);

    return {
      gainers: sorted.slice(0, 10),
      losers: sorted.slice(-10).reverse(),
    };
  }

  /**
   * Get stocks by category
   */
  async getStocksByCategory(
    category: keyof typeof POPULAR_STOCKS,
    limit?: number
  ): Promise<Asset[]> {
    const symbols = POPULAR_STOCKS[category];
    const assetsToFetch = limit ? symbols.slice(0, limit) : symbols;
    
    const assets: Asset[] = [];
    
    for (let i = 0; i < assetsToFetch.length; i += 5) {
      const batch = assetsToFetch.slice(i, i + 5);
      const batchResults = await Promise.all(
        batch.map(symbol => this.fetchAssetData(symbol))
      );
      
      assets.push(...batchResults.filter((asset): asset is Asset => asset !== null));
      
      if (i + 5 < assetsToFetch.length) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    return assets;
  }

  /**
   * Get multiple quotes at once (optimized)
   */
  async getMultipleQuotes(symbols: string[]): Promise<Record<string, Asset>> {
    const result: Record<string, Asset> = {};
    
    for (let i = 0; i < symbols.length; i += 5) {
      const batch = symbols.slice(i, i + 5);
      const batchResults = await Promise.all(
        batch.map(async symbol => {
          const asset = await this.fetchAssetData(symbol);
          return { symbol, asset };
        })
      );
      
      batchResults.forEach(({ symbol, asset }) => {
        if (asset) {
          result[symbol] = asset;
        }
      });
      
      if (i + 5 < symbols.length) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    return result;
  }

  /**
   * Sort assets
   */
  private sortAssets(
    assets: Asset[],
    sortBy: 'symbol' | 'price' | 'change' | 'volume',
    sortOrder: 'asc' | 'desc'
  ): void {
    assets.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'symbol':
          comparison = a.symbol.localeCompare(b.symbol);
          break;
        case 'price':
          comparison = a.price - b.price;
          break;
        case 'change':
          comparison = a.dailyChange - b.dailyChange;
          break;
        case 'volume':
          comparison = (a.volume || 0) - (b.volume || 0);
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }

  /**
   * Clear cache (useful for forcing refresh)
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Get available categories
   */
  getCategories(): (keyof typeof POPULAR_STOCKS)[] {
    return Object.keys(POPULAR_STOCKS) as (keyof typeof POPULAR_STOCKS)[];
  }
}

export default new EnhancedMarketService();
