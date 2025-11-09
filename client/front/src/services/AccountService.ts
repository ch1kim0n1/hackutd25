/**
 * Account Service
 * Manages account information, portfolio, and account activities
 */

import { AlpacaClient } from './AlpacaClient';
import type { 
  Account, 
  PortfolioHistory, 
  Activity, 
  ActivityType 
} from './alpaca.types';

export class AccountService extends AlpacaClient {
  /**
   * Get account information
   */
  async getAccount(): Promise<Account> {
    return this.request<Account>('GET', '/v2/account');
  }

  /**
   * Get account configurations
   */
  async getAccountConfigurations(): Promise<any> {
    return this.request<any>('GET', '/v2/account/configurations');
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
    return this.request<any>('PATCH', '/v2/account/configurations', config);
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
    const queryParams = new URLSearchParams(params as any).toString();
    const endpoint = `/v2/account/portfolio/history${queryParams ? `?${queryParams}` : ''}`;
    return this.request<PortfolioHistory>('GET', endpoint);
  }

  /**
   * Get account activities
   */
  async getActivities(params?: {
    activity_types?: ActivityType | ActivityType[];
    date?: string;
    until?: string;
    after?: string;
    direction?: 'asc' | 'desc';
    page_size?: number;
    page_token?: string;
  }): Promise<Activity[]> {
    const queryParams = new URLSearchParams(params as any).toString();
    const endpoint = `/v2/account/activities${queryParams ? `?${queryParams}` : ''}`;
    return this.request<Activity[]>('GET', endpoint);
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
      return this.handleError(error);
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
      return this.handleError(error);
    }
  }

  /**
   * Get account buying power for a specific asset
   */
  async getBuyingPowerForSymbol(symbol: string, price: number): Promise<{
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
      return this.handleError(error);
    }
  }
}

export default AccountService;
