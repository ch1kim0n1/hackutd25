/**
 * Local Storage Service
 * Manages portfolio data in browser's local storage
 */

import type { Account, Position, Order } from './alpaca.types';

const STORAGE_KEYS = {
  ACCOUNT: 'portfolio_account',
  POSITIONS: 'portfolio_positions',
  ORDERS: 'portfolio_orders',
  WATCHLISTS: 'portfolio_watchlists',
};

export class LocalStorageService {
  // ==================== ACCOUNT ====================
  
  getAccount(): Account {
    const stored = localStorage.getItem(STORAGE_KEYS.ACCOUNT);
    if (stored) {
      return JSON.parse(stored);
    }
    
    // Initialize default account
    const defaultAccount: Account = {
      id: 'local-account-001',
      account_number: 'PA1234567890',
      status: 'ACTIVE',
      currency: 'USD',
      buying_power: '100000.00',
      regt_buying_power: '100000.00',
      daytrading_buying_power: '100000.00',
      non_marginable_buying_power: '100000.00',
      cash: '100000.00',
      accrued_fees: '0.00',
      pending_transfer_out: '0.00',
      pending_transfer_in: '0.00',
      portfolio_value: '100000.00',
      pattern_day_trader: false,
      trading_blocked: false,
      transfers_blocked: false,
      account_blocked: false,
      created_at: new Date().toISOString(),
      trade_suspended_by_user: false,
      multiplier: '4',
      shorting_enabled: true,
      equity: '100000.00',
      last_equity: '100000.00',
      long_market_value: '0.00',
      short_market_value: '0.00',
      initial_margin: '0.00',
      maintenance_margin: '0.00',
      last_maintenance_margin: '0.00',
      sma: '0.00',
      daytrade_count: 0,
    };
    
    this.saveAccount(defaultAccount);
    return defaultAccount;
  }
  
  saveAccount(account: Account): void {
    localStorage.setItem(STORAGE_KEYS.ACCOUNT, JSON.stringify(account));
  }
  
  updateAccount(updates: Partial<Account>): Account {
    const account = this.getAccount();
    const updatedAccount = { ...account, ...updates };
    this.saveAccount(updatedAccount);
    return updatedAccount;
  }
  
  // ==================== POSITIONS ====================
  
  getPositions(): Position[] {
    const stored = localStorage.getItem(STORAGE_KEYS.POSITIONS);
    return stored ? JSON.parse(stored) : [];
  }
  
  getPosition(symbol: string): Position | null {
    const positions = this.getPositions();
    return positions.find(p => p.symbol === symbol) || null;
  }
  
  savePositions(positions: Position[]): void {
    localStorage.setItem(STORAGE_KEYS.POSITIONS, JSON.stringify(positions));
  }
  
  addOrUpdatePosition(position: Position): void {
    const positions = this.getPositions();
    const index = positions.findIndex(p => p.symbol === position.symbol);
    
    if (index >= 0) {
      positions[index] = position;
    } else {
      positions.push(position);
    }
    
    this.savePositions(positions);
    this.recalculateAccountValues();
  }
  
  removePosition(symbol: string): void {
    const positions = this.getPositions().filter(p => p.symbol !== symbol);
    this.savePositions(positions);
    this.recalculateAccountValues();
  }
  
  // ==================== ORDERS ====================
  
  getOrders(): Order[] {
    const stored = localStorage.getItem(STORAGE_KEYS.ORDERS);
    return stored ? JSON.parse(stored) : [];
  }
  
  saveOrders(orders: Order[]): void {
    localStorage.setItem(STORAGE_KEYS.ORDERS, JSON.stringify(orders));
  }
  
  addOrder(order: Order): void {
    const orders = this.getOrders();
    orders.push(order);
    this.saveOrders(orders);
  }
  
  updateOrder(orderId: string, updates: Partial<Order>): Order | null {
    const orders = this.getOrders();
    const index = orders.findIndex(o => o.id === orderId);
    
    if (index >= 0) {
      orders[index] = { ...orders[index], ...updates };
      this.saveOrders(orders);
      return orders[index];
    }
    
    return null;
  }
  
  // ==================== WATCHLISTS ====================
  
  getWatchlists(): any[] {
    const stored = localStorage.getItem(STORAGE_KEYS.WATCHLISTS);
    return stored ? JSON.parse(stored) : [];
  }
  
  saveWatchlists(watchlists: any[]): void {
    localStorage.setItem(STORAGE_KEYS.WATCHLISTS, JSON.stringify(watchlists));
  }
  
  // ==================== UTILITIES ====================
  
  recalculateAccountValues(): void {
    const account = this.getAccount();
    const positions = this.getPositions();
    
    // Calculate total market value of positions
    const longMarketValue = positions
      .filter(p => p.side === 'long')
      .reduce((sum, p) => sum + parseFloat(p.market_value), 0);
    
    const shortMarketValue = positions
      .filter(p => p.side === 'short')
      .reduce((sum, p) => sum + parseFloat(p.market_value), 0);
    
    // Calculate equity
    const equity = parseFloat(account.cash) + longMarketValue - shortMarketValue;
    
    // Calculate portfolio value
    const portfolioValue = equity;
    
    // Update account
    this.updateAccount({
      long_market_value: longMarketValue.toFixed(2),
      short_market_value: shortMarketValue.toFixed(2),
      equity: equity.toFixed(2),
      portfolio_value: portfolioValue.toFixed(2),
      buying_power: equity.toFixed(2), // Simplified buying power calculation
    });
  }
  
  clearAllData(): void {
    localStorage.removeItem(STORAGE_KEYS.ACCOUNT);
    localStorage.removeItem(STORAGE_KEYS.POSITIONS);
    localStorage.removeItem(STORAGE_KEYS.ORDERS);
    localStorage.removeItem(STORAGE_KEYS.WATCHLISTS);
  }
  
  resetToDefaults(): void {
    this.clearAllData();
    this.getAccount(); // This will create default account
  }
}

export default new LocalStorageService();
