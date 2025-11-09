/**
 * Watchlist Service
 * Manages watchlists and symbol tracking
 */

import { AlpacaClient } from './AlpacaClient';
import type { Watchlist, CreateWatchlistRequest, Asset } from './alpaca.types';

export class WatchlistService extends AlpacaClient {
  /**
   * Get all watchlists
   */
  async getWatchlists(): Promise<Watchlist[]> {
    return this.request<Watchlist[]>('GET', '/v2/watchlists');
  }

  /**
   * Get a specific watchlist by ID
   */
  async getWatchlist(watchlistId: string): Promise<Watchlist> {
    return this.request<Watchlist>('GET', `/v2/watchlists/${watchlistId}`);
  }

  /**
   * Create a new watchlist
   */
  async createWatchlist(request: CreateWatchlistRequest): Promise<Watchlist> {
    return this.request<Watchlist>('POST', '/v2/watchlists', request);
  }

  /**
   * Update a watchlist
   */
  async updateWatchlist(
    watchlistId: string,
    updates: {
      name?: string;
      symbols?: string[];
    }
  ): Promise<Watchlist> {
    return this.request<Watchlist>('PUT', `/v2/watchlists/${watchlistId}`, updates);
  }

  /**
   * Add a symbol to a watchlist
   */
  async addSymbolToWatchlist(watchlistId: string, symbol: string): Promise<Watchlist> {
    return this.request<Watchlist>('POST', `/v2/watchlists/${watchlistId}`, { symbol });
  }

  /**
   * Add multiple symbols to a watchlist
   */
  async addSymbolsToWatchlist(watchlistId: string, symbols: string[]): Promise<Watchlist> {
    try {
      let watchlist = await this.getWatchlist(watchlistId);
      
      for (const symbol of symbols) {
        watchlist = await this.addSymbolToWatchlist(watchlistId, symbol);
      }
      
      return watchlist;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Remove a symbol from a watchlist
   */
  async removeSymbolFromWatchlist(watchlistId: string, symbol: string): Promise<void> {
    await this.request<void>('DELETE', `/v2/watchlists/${watchlistId}/${symbol}`);
  }

  /**
   * Remove multiple symbols from a watchlist
   */
  async removeSymbolsFromWatchlist(watchlistId: string, symbols: string[]): Promise<void> {
    try {
      for (const symbol of symbols) {
        await this.removeSymbolFromWatchlist(watchlistId, symbol);
      }
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Delete a watchlist
   */
  async deleteWatchlist(watchlistId: string): Promise<void> {
    await this.request<void>('DELETE', `/v2/watchlists/${watchlistId}`);
  }

  /**
   * Find a watchlist by name
   */
  async findWatchlistByName(name: string): Promise<Watchlist | null> {
    try {
      const watchlists = await this.getWatchlists();
      return watchlists.find(w => w.name.toLowerCase() === name.toLowerCase()) || null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if a symbol is in any watchlist
   */
  async isSymbolInWatchlists(symbol: string): Promise<{
    inWatchlist: boolean;
    watchlists: Array<{ id: string; name: string }>;
  }> {
    try {
      const watchlists = await this.getWatchlists();
      const foundIn: Array<{ id: string; name: string }> = [];

      for (const watchlist of watchlists) {
        const hasSymbol = watchlist.assets.some(
          asset => asset.symbol.toLowerCase() === symbol.toLowerCase()
        );
        if (hasSymbol) {
          foundIn.push({ id: watchlist.id, name: watchlist.name });
        }
      }

      return {
        inWatchlist: foundIn.length > 0,
        watchlists: foundIn,
      };
    } catch (error) {
      return { inWatchlist: false, watchlists: [] };
    }
  }

  /**
   * Get or create a watchlist by name
   */
  async getOrCreateWatchlist(name: string, symbols: string[] = []): Promise<Watchlist> {
    try {
      const existing = await this.findWatchlistByName(name);
      if (existing) {
        return existing;
      }
      return await this.createWatchlist({ name, symbols });
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Clone a watchlist
   */
  async cloneWatchlist(watchlistId: string, newName: string): Promise<Watchlist> {
    try {
      const original = await this.getWatchlist(watchlistId);
      const symbols = original.assets.map(asset => asset.symbol);
      return await this.createWatchlist({ name: newName, symbols });
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get watchlist symbols only (no full asset data)
   */
  async getWatchlistSymbols(watchlistId: string): Promise<string[]> {
    try {
      const watchlist = await this.getWatchlist(watchlistId);
      return watchlist.assets.map(asset => asset.symbol);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Merge multiple watchlists into one
   */
  async mergeWatchlists(
    watchlistIds: string[],
    newName: string,
    deleteOriginals: boolean = false
  ): Promise<Watchlist> {
    try {
      const allSymbols = new Set<string>();

      for (const id of watchlistIds) {
        const symbols = await this.getWatchlistSymbols(id);
        symbols.forEach(symbol => allSymbols.add(symbol));
      }

      const merged = await this.createWatchlist({
        name: newName,
        symbols: Array.from(allSymbols),
      });

      if (deleteOriginals) {
        for (const id of watchlistIds) {
          await this.deleteWatchlist(id);
        }
      }

      return merged;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get watchlist statistics
   */
  async getWatchlistStats(watchlistId: string): Promise<{
    totalSymbols: number;
    tradableSymbols: number;
    marginableSymbols: number;
    shortableSymbols: number;
    exchanges: Record<string, number>;
  }> {
    try {
      const watchlist = await this.getWatchlist(watchlistId);
      
      const exchanges: Record<string, number> = {};
      watchlist.assets.forEach(asset => {
        exchanges[asset.exchange] = (exchanges[asset.exchange] || 0) + 1;
      });

      return {
        totalSymbols: watchlist.assets.length,
        tradableSymbols: watchlist.assets.filter(a => a.tradable).length,
        marginableSymbols: watchlist.assets.filter(a => a.marginable).length,
        shortableSymbols: watchlist.assets.filter(a => a.shortable).length,
        exchanges,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }
}

export default WatchlistService;
