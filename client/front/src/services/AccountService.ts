/**
 * Account Service
 * Manages account information, portfolio, and account activities using local storage
 */

import LocalStorageService from './LocalStorageService';
import type { 
  Account, 
  PortfolioHistory, 
  Activity, 
  ActivityType 
} from './alpaca.types';

export class AccountService {
  /**
   * Get account information
   */
  async getAccount(): Promise<Account> {
    return LocalStorageService.getAccount();
  }

  /**
   * Get account configurations
   */
  async getAccountConfigurations(): Promise<any> {
    // Return mock configurations
    return {
      dtbp_check: 'entry',
      no_shorting: false,
      suspend_trade: false,
      trade_confirm_email: 'none',
    };
  }

  /**
   * Update account configurations
   */
  async updateAccountConfigurations(config: {
    dtbp_check?: 'entry' | 'exit' | 'both';
    no_shorting?: boolean;
    suspend_trade?: boolean;
    trade_confirm_email?: 'all' | 'none';
  }): Promise<any> {
    // Store in localStorage if needed
    return config;
  }

  /**
   * Get portfolio history
   */
  async getPortfolioHistory(params?: {
    period?: '1D' | '1W' | '1M' | '3M' | '1A' | 'all';
    timeframe?: '1Min' | '5Min' | '15Min' | '1H' | '1D';
    date_end?: string;
    extended_hours?: boolean;
  }): Promise<PortfolioHistory> {
    // Generate mock portfolio history
    const days = params?.period === '1D' ? 1 : params?.period === '1W' ? 7 : params?.period === '1M' ? 30 : 90;
    const account = LocalStorageService.getAccount();
    const baseValue = parseFloat(account.portfolio_value);
    
    const timestamps: number[] = [];
    const equity: number[] = [];
    const profit_loss: number[] = [];
    const profit_loss_pct: number[] = [];
    
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      timestamps.push(date.getTime() / 1000);
      
      const variance = (Math.random() - 0.5) * 0.05; // ±2.5% daily variance
      const value = baseValue * (1 + variance);
      equity.push(value);
      profit_loss.push(value - baseValue);
      profit_loss_pct.push(((value - baseValue) / baseValue) * 100);
    }
    
    return {
      timestamp: timestamps,
      equity,
      profit_loss,
      profit_loss_pct,
      base_value: baseValue,
      timeframe: params?.timeframe || '1D',
    };
  }

  /**
   * Get account activities
   */
  async getActivities(_params?: {
    activity_types?: ActivityType | ActivityType[];
    date?: string;
    until?: string;
    after?: string;
    direction?: 'asc' | 'desc';
    page_size?: number;
    page_token?: string;
  }): Promise<Activity[]> {
    // Return empty activities for now
    // You can enhance this to store activities in localStorage
    return [];
  }

  /**
   * Get account activity by type
   */
  async getActivityByType(activityType: ActivityType): Promise<Activity[]> {
    return this.getActivities({ activity_types: activityType });
  }

  /**
   * Calculate account metrics
   */
  async getAccountMetrics(): Promise<{
    totalValue: number;
    cashBalance: number;
    equityValue: number;
    buyingPower: number;
    profitLoss: number;
    profitLossPercent: number;
    dayTradeCount: number;
    isPatternDayTrader: boolean;
  }> {
    try {
      const account = await this.getAccount();
      const portfolioValue = parseFloat(account.portfolio_value);
      const lastEquity = parseFloat(account.last_equity);
      const profitLoss = portfolioValue - lastEquity;
      const profitLossPercent = lastEquity > 0 ? (profitLoss / lastEquity) * 100 : 0;

      return {
        totalValue: portfolioValue,
        cashBalance: parseFloat(account.cash),
        equityValue: parseFloat(account.equity),
        buyingPower: parseFloat(account.buying_power),
        profitLoss,
        profitLossPercent,
        dayTradeCount: account.daytrade_count,
        isPatternDayTrader: account.pattern_day_trader,
      };
    } catch (error) {
      console.error('Error getting account metrics:', error);
      throw error;
    }
  }

  /**
   * Check if account can trade
   */
  async canTrade(): Promise<{
    canTrade: boolean;
    reasons: string[];
  }> {
    try {
      const account = await this.getAccount();
      const reasons: string[] = [];

      if (account.trading_blocked) {
        reasons.push('Trading is blocked on this account');
      }
      if (account.account_blocked) {
        reasons.push('Account is blocked');
      }
      if (account.trade_suspended_by_user) {
        reasons.push('Trading is suspended by user');
      }
      if (account.status !== 'ACTIVE') {
        reasons.push(`Account status is ${account.status}`);
      }

      return {
        canTrade: reasons.length === 0,
        reasons,
      };
    } catch (error) {
      console.error('Error checking if can trade:', error);
      return {
        canTrade: false,
        reasons: ['Error checking account status'],
      };
    }
  }

  /**
   * Get account buying power for a specific asset
   */
  async getBuyingPowerForSymbol(_symbol: string, price: number): Promise<{
    maxShares: number;
    maxNotional: number;
    buyingPower: number;
  }> {
    try {
      const account = await this.getAccount();
      const buyingPower = parseFloat(account.buying_power);
      const maxShares = Math.floor(buyingPower / price);
      const maxNotional = buyingPower;

      return {
        maxShares,
        maxNotional,
        buyingPower,
      };
    } catch (error) {
      console.error('Error getting buying power:', error);
      throw error;
    }
  }
}

export default AccountService;
