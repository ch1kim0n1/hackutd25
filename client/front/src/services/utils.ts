/**
 * Alpaca Utility Functions
 * Helper functions for common trading operations
 */

import type { Order, Position, Bar } from './alpaca.types';

// ==================== Formatting Utilities ====================

/**
 * Format currency value
 */
export function formatCurrency(value: number | string, decimals: number = 2): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

/**
 * Format percentage
 */
export function formatPercent(value: number | string, decimals: number = 2): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return `${num >= 0 ? '+' : ''}${num.toFixed(decimals)}%`;
}

/**
 * Format large numbers with K, M, B suffixes
 */
export function formatNumber(value: number): string {
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
  return value.toFixed(2);
}

/**
 * Format date/time
 */
export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format time only
 */
export function formatTime(date: string | Date): string {
  return new Date(date).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ==================== Calculation Utilities ====================

/**
 * Calculate profit/loss
 */
export function calculateProfitLoss(
  entryPrice: number,
  currentPrice: number,
  quantity: number
): { pl: number; plPercent: number } {
  const pl = (currentPrice - entryPrice) * quantity;
  const plPercent = entryPrice > 0 ? ((currentPrice - entryPrice) / entryPrice) * 100 : 0;
  return { pl, plPercent };
}

/**
 * Calculate position value
 */
export function calculatePositionValue(price: number, quantity: number): number {
  return price * quantity;
}

/**
 * Calculate total portfolio value
 */
export function calculatePortfolioValue(positions: Position[]): number {
  return positions.reduce((total, pos) => total + parseFloat(pos.market_value), 0);
}

/**
 * Calculate total portfolio P/L
 */
export function calculateTotalProfitLoss(positions: Position[]): {
  totalPL: number;
  totalPLPercent: number;
} {
  const totalPL = positions.reduce((sum, pos) => sum + parseFloat(pos.unrealized_pl), 0);
  const totalCost = positions.reduce((sum, pos) => sum + parseFloat(pos.cost_basis), 0);
  const totalPLPercent = totalCost > 0 ? (totalPL / totalCost) * 100 : 0;
  
  return { totalPL, totalPLPercent };
}

/**
 * Calculate average entry price for multiple fills
 */
export function calculateAveragePrice(orders: Order[]): number {
  const filled = orders.filter(o => o.filled_qty && parseFloat(o.filled_qty) > 0);
  
  if (filled.length === 0) return 0;
  
  let totalValue = 0;
  let totalQty = 0;
  
  filled.forEach(order => {
    const qty = parseFloat(order.filled_qty);
    const price = parseFloat(order.filled_avg_price || '0');
    totalValue += qty * price;
    totalQty += qty;
  });
  
  return totalQty > 0 ? totalValue / totalQty : 0;
}

/**
 * Calculate simple moving average from bars
 */
export function calculateSMA(bars: Bar[], period: number): number[] {
  const sma: number[] = [];
  
  for (let i = period - 1; i < bars.length; i++) {
    const sum = bars.slice(i - period + 1, i + 1).reduce((acc, bar) => acc + bar.c, 0);
    sma.push(sum / period);
  }
  
  return sma;
}

/**
 * Calculate exponential moving average
 */
export function calculateEMA(bars: Bar[], period: number): number[] {
  const ema: number[] = [];
  const multiplier = 2 / (period + 1);
  
  // Start with SMA for first value
  const firstSMA = bars.slice(0, period).reduce((acc, bar) => acc + bar.c, 0) / period;
  ema.push(firstSMA);
  
  // Calculate EMA for remaining values
  for (let i = period; i < bars.length; i++) {
    const value = (bars[i].c - ema[ema.length - 1]) * multiplier + ema[ema.length - 1];
    ema.push(value);
  }
  
  return ema;
}

/**
 * Calculate RSI (Relative Strength Index)
 */
export function calculateRSI(bars: Bar[], period: number = 14): number[] {
  const rsi: number[] = [];
  const changes: number[] = [];
  
  // Calculate price changes
  for (let i = 1; i < bars.length; i++) {
    changes.push(bars[i].c - bars[i - 1].c);
  }
  
  // Calculate RSI
  for (let i = period - 1; i < changes.length; i++) {
    const recentChanges = changes.slice(i - period + 1, i + 1);
    const gains = recentChanges.filter(c => c > 0).reduce((sum, c) => sum + c, 0);
    const losses = Math.abs(recentChanges.filter(c => c < 0).reduce((sum, c) => sum + c, 0));
    
    const avgGain = gains / period;
    const avgLoss = losses / period;
    
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    const rsiValue = 100 - (100 / (1 + rs));
    
    rsi.push(rsiValue);
  }
  
  return rsi;
}

/**
 * Calculate MACD (Moving Average Convergence Divergence)
 */
export function calculateMACD(bars: Bar[]): {
  macd: number[];
  signal: number[];
  histogram: number[];
} {
  const ema12 = calculateEMA(bars, 12);
  const ema26 = calculateEMA(bars, 26);
  
  // Calculate MACD line
  const macd: number[] = [];
  for (let i = 0; i < ema12.length && i < ema26.length; i++) {
    macd.push(ema12[i] - ema26[i]);
  }
  
  // Calculate signal line (9-day EMA of MACD)
  const macdBars: Bar[] = macd.map((value, i) => ({
    t: bars[i + 26].t,
    o: value,
    h: value,
    l: value,
    c: value,
    v: 0,
  }));
  const signal = calculateEMA(macdBars, 9);
  
  // Calculate histogram
  const histogram: number[] = [];
  for (let i = 0; i < macd.length && i < signal.length; i++) {
    histogram.push(macd[i] - signal[i]);
  }
  
  return { macd, signal, histogram };
}

// ==================== Validation Utilities ====================

/**
 * Validate order quantity
 */
export function validateQuantity(qty: number): { valid: boolean; error?: string } {
  if (!Number.isInteger(qty)) {
    return { valid: false, error: 'Quantity must be a whole number' };
  }
  if (qty <= 0) {
    return { valid: false, error: 'Quantity must be greater than 0' };
  }
  return { valid: true };
}

/**
 * Validate price
 */
export function validatePrice(price: number): { valid: boolean; error?: string } {
  if (price <= 0) {
    return { valid: false, error: 'Price must be greater than 0' };
  }
  if (!Number.isFinite(price)) {
    return { valid: false, error: 'Price must be a valid number' };
  }
  return { valid: true };
}

/**
 * Validate symbol format
 */
export function validateSymbol(symbol: string): { valid: boolean; error?: string } {
  if (!symbol || symbol.trim() === '') {
    return { valid: false, error: 'Symbol cannot be empty' };
  }
  if (!/^[A-Z]{1,5}$/.test(symbol.toUpperCase())) {
    return { valid: false, error: 'Symbol must be 1-5 letters' };
  }
  return { valid: true };
}

// ==================== Risk Management Utilities ====================

/**
 * Calculate position size based on risk
 */
export function calculatePositionSize(
  accountValue: number,
  riskPercent: number,
  entryPrice: number,
  stopLoss: number
): number {
  const riskAmount = accountValue * (riskPercent / 100);
  const riskPerShare = Math.abs(entryPrice - stopLoss);
  return Math.floor(riskAmount / riskPerShare);
}

/**
 * Calculate stop loss price
 */
export function calculateStopLoss(
  entryPrice: number,
  stopLossPercent: number,
  side: 'buy' | 'sell'
): number {
  if (side === 'buy') {
    return entryPrice * (1 - stopLossPercent / 100);
  } else {
    return entryPrice * (1 + stopLossPercent / 100);
  }
}

/**
 * Calculate take profit price
 */
export function calculateTakeProfit(
  entryPrice: number,
  takeProfitPercent: number,
  side: 'buy' | 'sell'
): number {
  if (side === 'buy') {
    return entryPrice * (1 + takeProfitPercent / 100);
  } else {
    return entryPrice * (1 - takeProfitPercent / 100);
  }
}

/**
 * Calculate risk/reward ratio
 */
export function calculateRiskRewardRatio(
  entryPrice: number,
  stopLoss: number,
  takeProfit: number
): number {
  const risk = Math.abs(entryPrice - stopLoss);
  const reward = Math.abs(takeProfit - entryPrice);
  return risk > 0 ? reward / risk : 0;
}

// ==================== Time Utilities ====================

/**
 * Check if market is likely open (US Eastern Time)
 */
export function isLikelyMarketHours(): boolean {
  const now = new Date();
  const et = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
  const day = et.getDay();
  const hours = et.getHours();
  const minutes = et.getMinutes();
  
  // Monday-Friday
  if (day === 0 || day === 6) return false;
  
  // 9:30 AM - 4:00 PM ET
  const currentTime = hours * 60 + minutes;
  const marketOpen = 9 * 60 + 30; // 9:30 AM
  const marketClose = 16 * 60; // 4:00 PM
  
  return currentTime >= marketOpen && currentTime < marketClose;
}

/**
 * Get trading day range
 */
export function getTradingDayRange(days: number): { start: Date; end: Date } {
  const end = new Date();
  const start = new Date();
  
  // Add extra days to account for weekends
  const calendarDays = Math.ceil(days * 1.5);
  start.setDate(start.getDate() - calendarDays);
  
  return { start, end };
}

// ==================== Array/Data Utilities ====================

/**
 * Group positions by asset class
 */
export function groupPositionsByClass(positions: Position[]): Record<string, Position[]> {
  return positions.reduce((acc, pos) => {
    const key = pos.asset_class;
    if (!acc[key]) acc[key] = [];
    acc[key].push(pos);
    return acc;
  }, {} as Record<string, Position[]>);
}

/**
 * Sort positions by value
 */
export function sortPositionsByValue(positions: Position[], descending: boolean = true): Position[] {
  return [...positions].sort((a, b) => {
    const aValue = parseFloat(a.market_value);
    const bValue = parseFloat(b.market_value);
    return descending ? bValue - aValue : aValue - bValue;
  });
}

/**
 * Sort positions by profit/loss
 */
export function sortPositionsByProfitLoss(positions: Position[], descending: boolean = true): Position[] {
  return [...positions].sort((a, b) => {
    const aPL = parseFloat(a.unrealized_pl);
    const bPL = parseFloat(b.unrealized_pl);
    return descending ? bPL - aPL : aPL - bPL;
  });
}

// ==================== Export All ====================

export const AlpacaUtils = {
  // Formatting
  formatCurrency,
  formatPercent,
  formatNumber,
  formatDateTime,
  formatTime,
  
  // Calculations
  calculateProfitLoss,
  calculatePositionValue,
  calculatePortfolioValue,
  calculateTotalProfitLoss,
  calculateAveragePrice,
  calculateSMA,
  calculateEMA,
  calculateRSI,
  calculateMACD,
  
  // Validation
  validateQuantity,
  validatePrice,
  validateSymbol,
  
  // Risk Management
  calculatePositionSize,
  calculateStopLoss,
  calculateTakeProfit,
  calculateRiskRewardRatio,
  
  // Time
  isLikelyMarketHours,
  getTradingDayRange,
  
  // Data manipulation
  groupPositionsByClass,
  sortPositionsByValue,
  sortPositionsByProfitLoss,
};

export default AlpacaUtils;
