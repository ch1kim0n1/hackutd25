/**
 * Custom React Hooks for Alpaca Services
 * Easy-to-use hooks for React components
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  AlpacaService,
  Account,
  Position,
  Order,
  Asset,
  Clock,
  Bar,
} from './index';

// ==================== Main Alpaca Hook ====================

export function useAlpaca() {
  const alpacaRef = useRef<AlpacaService | null>(null);

  if (!alpacaRef.current) {
    alpacaRef.current = new AlpacaService();
  }

  return alpacaRef.current;
}

// ==================== Account Hooks ====================

export function useAccount() {
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await alpaca.account.getAccount();
      setAccount(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch account');
    } finally {
      setLoading(false);
    }
  }, [alpaca]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { account, loading, error, refresh };
}

export function useAccountMetrics() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await alpaca.account.getAccountMetrics();
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  }, [alpaca]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { metrics, loading, error, refresh };
}

// ==================== Trading Hooks ====================

export function usePositions() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await alpaca.trading.getPositions();
      setPositions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch positions');
    } finally {
      setLoading(false);
    }
  }, [alpaca]);

  const closePosition = useCallback(async (symbol: string) => {
    try {
      await alpaca.trading.closePosition(symbol);
      await refresh();
    } catch (err: any) {
      throw new Error(err.message || 'Failed to close position');
    }
  }, [alpaca, refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { positions, loading, error, refresh, closePosition };
}

export function useOrders(status: 'all' | 'open' | 'closed' = 'open') {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await alpaca.trading.getOrders({ status });
      setOrders(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  }, [alpaca, status]);

  const cancelOrder = useCallback(async (orderId: string) => {
    try {
      await alpaca.trading.cancelOrder(orderId);
      await refresh();
    } catch (err: any) {
      throw new Error(err.message || 'Failed to cancel order');
    }
  }, [alpaca, refresh]);

  const placeOrder = useCallback(async (symbol: string, qty: number, side: 'buy' | 'sell') => {
    try {
      const order = await alpaca.trading.marketOrder(symbol, qty, side);
      await refresh();
      return order;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to place order');
    }
  }, [alpaca, refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { orders, loading, error, refresh, cancelOrder, placeOrder };
}

// ==================== Market Data Hooks ====================

export function useStockPrice(symbol: string, interval: number = 5000) {
  const [price, setPrice] = useState<number | null>(null);
  const [change, setChange] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [currentPrice, priceChange] = await Promise.all([
        alpaca.marketData.getCurrentPrice(symbol),
        alpaca.marketData.getPriceChange(symbol),
      ]);
      setPrice(currentPrice);
      setChange(priceChange);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch price');
    } finally {
      setLoading(false);
    }
  }, [alpaca, symbol]);

  useEffect(() => {
    refresh();
    const intervalId = setInterval(refresh, interval);
    return () => clearInterval(intervalId);
  }, [refresh, interval]);

  return { price, change, loading, error, refresh };
}

export function useStockBars(
  symbol: string,
  timeframe: '1Min' | '5Min' | '15Min' | '1Hour' | '1Day' = '1Day',
  days: number = 30
) {
  const [bars, setBars] = useState<Bar[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (timeframe === '1Day') {
        const data = await alpaca.marketData.getDailyBars(symbol, days);
        setBars(data);
      } else {
        const data = await alpaca.marketData.getIntradayBars(symbol, timeframe);
        setBars(data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch bars');
    } finally {
      setLoading(false);
    }
  }, [alpaca, symbol, timeframe, days]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { bars, loading, error, refresh };
}

export function useMarketOverview(symbols: string[]) {
  const [overview, setOverview] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await alpaca.marketData.getMarketOverview(symbols);
      setOverview(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch market overview');
    } finally {
      setLoading(false);
    }
  }, [alpaca, symbols]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { overview, loading, error, refresh };
}

// ==================== Asset Hooks ====================

export function useAssetSearch(query: string) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  useEffect(() => {
    if (!query || query.length < 1) {
      setAssets([]);
      return;
    }

    const search = async () => {
      try {
        setLoading(true);
        setError(null);
        const results = await alpaca.assets.searchAssets(query, 20);
        setAssets(results);
      } catch (err: any) {
        setError(err.message || 'Search failed');
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(search, 300);
    return () => clearTimeout(debounce);
  }, [alpaca, query]);

  return { assets, loading, error };
}

// ==================== Clock Hooks ====================

export function useMarketStatus() {
  const [status, setStatus] = useState<Clock | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await alpaca.clock.getClock();
      setStatus(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch market status');
    } finally {
      setLoading(false);
    }
  }, [alpaca]);

  useEffect(() => {
    refresh();
    // Refresh every minute
    const intervalId = setInterval(refresh, 60000);
    return () => clearInterval(intervalId);
  }, [refresh]);

  return { status, isOpen: status?.is_open || false, loading, error, refresh };
}

// ==================== Dashboard Hook ====================

export function useDashboard() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await alpaca.getDashboardData();
      setDashboard(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, [alpaca]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { dashboard, loading, error, refresh };
}

// ==================== Trading Actions Hook ====================

export function useTrading() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const alpaca = useAlpaca();

  const buy = useCallback(async (symbol: string, qty: number) => {
    try {
      setLoading(true);
      setError(null);
      const order = await alpaca.quickBuy(symbol, qty);
      return order;
    } catch (err: any) {
      setError(err.message || 'Buy order failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [alpaca]);

  const sell = useCallback(async (symbol: string, qty: number) => {
    try {
      setLoading(true);
      setError(null);
      const order = await alpaca.quickSell(symbol, qty);
      return order;
    } catch (err: any) {
      setError(err.message || 'Sell order failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [alpaca]);

  const limitOrder = useCallback(async (
    symbol: string,
    qty: number,
    side: 'buy' | 'sell',
    limitPrice: number
  ) => {
    try {
      setLoading(true);
      setError(null);
      const order = await alpaca.trading.limitOrder(symbol, qty, side, limitPrice);
      return order;
    } catch (err: any) {
      setError(err.message || 'Limit order failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [alpaca]);

  return { buy, sell, limitOrder, loading, error };
}
