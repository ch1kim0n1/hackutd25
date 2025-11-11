/**
 * Base Alpaca Client
 * Proxies requests through the backend API for security
 * All Alpaca credentials are managed server-side
 */

import type { AlpacaError } from "./alpaca.types";
import { BackendAPI } from "./BackendAPI";

export class AlpacaClient {
  /**
   * Get the current configuration
   * Note: Configuration is now managed server-side
   */
  getConfig(): { paper: boolean } {
    // Return minimal config - actual credentials are server-side
    return { paper: true }; // Assume paper trading by default
  }

  /**
   * Check if using paper trading
   * Note: This is now determined server-side
   */
  isPaperTrading(): boolean {
    return true; // Server-side determines actual mode
  }

  /**
   * Handle API errors consistently
   */
  protected handleError(error: any): never {
    if (error.response) {
      const alpacaError: AlpacaError = {
        code: error.response.status,
        message: error.response.data?.message || error.message,
      };

      throw alpacaError;
    }
    throw error;
  }

  /**
   * Make a generic API request through the backend
   * All requests are proxied through /api/trade endpoint
   */
  protected async request<T>(
    method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
    endpoint: string,
    data?: any,
  ): Promise<T> {
    try {
      // For trading operations, use the backend API
      if (method === "POST" && endpoint.includes("/orders")) {
        // This is a trade order - use the backend trade endpoint
        return await BackendAPI.trading.placeTrade(data) as T;
      } else if (method === "GET" && endpoint.includes("/account")) {
        // Get account info
        return await BackendAPI.account.get() as T;
      } else if (method === "GET" && endpoint.includes("/positions")) {
        // Get positions
        return await BackendAPI.portfolio.getPositions() as T;
      } else if (method === "GET" && endpoint.includes("/orders")) {
        // Get orders/trades
        return await BackendAPI.trading.getTrades() as T;
      }

      // Fallback: generic request (will need backend endpoint)
      throw new Error(
        `Unsupported Alpaca operation: ${method} ${endpoint}. Please use BackendAPI directly.`
      );
    } catch (error) {
      return this.handleError(error);
    }
  }
}

export default AlpacaClient;
