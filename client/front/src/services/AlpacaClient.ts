/**
 * Base Alpaca Client
 * Core client for making authenticated requests to Alpaca API
 * Uses fetch API for browser compatibility (no Node.js dependencies)
 *
 * ⚠️ SECURITY WARNING - PLANNED FOR REFACTOR:
 * This client makes direct API calls from the browser to Alpaca, which exposes
 * API credentials in the frontend bundle. This is acceptable for demo/development
 * but MUST be replaced with backend proxy endpoints for production.
 *
 * REFACTOR PLAN (Phase 3.2):
 * - All Alpaca calls should route through backend API at /api/v1/alpaca/*
 * - Frontend will use typed API client instead of this direct client
 * - API keys will be stored server-side only
 */

import { getAlpacaConfig, type AlpacaConfig } from './alpaca.config';
import type { AlpacaError } from './alpaca.types';

export class AlpacaClient {
  protected config: AlpacaConfig;

  constructor(config?: Partial<AlpacaConfig>) {
    this.config = { ...getAlpacaConfig(), ...config };
    
    if (!this.config.keyId || !this.config.secretKey) {
      throw new Error('Alpaca API credentials are required. Please set VITE_ALPACA_API_KEY and VITE_ALPACA_SECRET_KEY');
    }
  }

  /**
   * Get the current configuration
   */
  getConfig(): AlpacaConfig {
    return this.config;
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
