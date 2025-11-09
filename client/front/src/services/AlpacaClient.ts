/**
 * Base Alpaca Client
 * Core client for making authenticated requests to Alpaca API
 */

import Alpaca from '@alpacahq/alpaca-trade-api';
import { getAlpacaConfig, type AlpacaConfig } from './alpaca.config';
import type { AlpacaError } from './alpaca.types';

export class AlpacaClient {
  protected client: Alpaca;
  protected config: AlpacaConfig;

  constructor(config?: Partial<AlpacaConfig>) {
    this.config = { ...getAlpacaConfig(), ...config };
    
    if (!this.config.keyId || !this.config.secretKey) {
      throw new Error('Alpaca API credentials are required. Please set VITE_ALPACA_API_KEY and VITE_ALPACA_SECRET_KEY');
    }

    this.client = new Alpaca({
      keyId: this.config.keyId,
      secretKey: this.config.secretKey,
      paper: this.config.paper,
      baseUrl: this.config.baseUrl,
      dataBaseUrl: this.config.dataBaseUrl,
    });
  }

  /**
   * Get the underlying Alpaca client instance
   */
  getClient(): Alpaca {
    return this.client;
  }

  /**
   * Check if using paper trading
   */
  isPaperTrading(): boolean {
    return this.config.paper;
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
   * Make a generic API request
   */
  protected async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    endpoint: string,
    data?: any
  ): Promise<T> {
    try {
      const baseUrl = this.config.paper 
        ? 'https://paper-api.alpaca.markets'
        : 'https://api.alpaca.markets';
      
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method,
        headers: {
          'APCA-API-KEY-ID': this.config.keyId,
          'APCA-API-SECRET-KEY': this.config.secretKey,
          'Content-Type': 'application/json',
        },
        body: data ? JSON.stringify(data) : undefined,
      });

      if (!response.ok) {
        const error = await response.json();
        throw {
          response: {
            status: response.status,
            data: error,
          },
          message: error.message || 'API request failed',
        };
      }

      return await response.json();
    } catch (error) {
      return this.handleError(error);
    }
  }
}

export default AlpacaClient;
