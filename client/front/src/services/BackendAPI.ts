/**
 * Backend API Service
 * Handles all communication with the FastAPI backend server
 */

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Token storage keys
const ACCESS_TOKEN_KEY = 'apex_access_token';
const REFRESH_TOKEN_KEY = 'apex_refresh_token';

/**
 * Token management utilities
 */
export class TokenManager {
  static getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  static setAccessToken(token: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  static setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  }

  static clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  static isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
}

/**
 * HTTP client with automatic token injection and refresh
 */
class APIClient {
  private baseURL: string;
  private refreshing: Promise<string> | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  /**
   * Make an authenticated API request
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = TokenManager.getAccessToken();

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle token expiration
      if (response.status === 401 && token) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          // Retry with new token
          headers['Authorization'] = `Bearer ${refreshed}`;
          const retryResponse = await fetch(url, {
            ...options,
            headers,
          });
          return await this.handleResponse<T>(retryResponse);
        }
      }

      return await this.handleResponse<T>(response);
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new Error(error.detail || 'API request failed');
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }

    return (await response.text()) as unknown as T;
  }

  /**
   * Refresh access token using refresh token
   */
  private async refreshAccessToken(): Promise<string | null> {
    // Prevent multiple concurrent refresh attempts
    if (this.refreshing) {
      return this.refreshing;
    }

    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) {
      TokenManager.clearTokens();
      return null;
    }

    this.refreshing = (async () => {
      try {
        const response = await fetch(`${this.baseURL}/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
          throw new Error('Token refresh failed');
        }

        const data = await response.json();
        TokenManager.setAccessToken(data.access_token);
        return data.access_token;
      } catch (error) {
        console.error('Token refresh failed:', error);
        TokenManager.clearTokens();
        window.location.href = '/login';
        return null;
      } finally {
        this.refreshing = null;
      }
    })();

    return this.refreshing;
  }

  /**
   * HTTP method helpers
   */
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

const client = new APIClient(API_BASE_URL);

/**
 * Backend API Interface
 */
export const BackendAPI = {
  // Authentication
  auth: {
    login: async (username: string, password: string) => {
      const response = await client.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
      }>('/auth/login', { username, password });

      TokenManager.setAccessToken(response.access_token);
      TokenManager.setRefreshToken(response.refresh_token);

      return response;
    },

    logout: async () => {
      try {
        await client.post('/auth/logout');
      } finally {
        TokenManager.clearTokens();
      }
    },

    getCurrentUser: () => client.get<any>('/auth/me'),
  },

  // Portfolio
  portfolio: {
    get: () => client.get<any>('/api/portfolio'),
    getAccount: () => client.get<any>('/api/account'),
    getPositions: () => client.get<any>('/api/positions'),
    getOrders: () => client.get<any>('/api/orders'),
  },

  // Trading
  trading: {
    placeTrade: (trade: {
      symbol: string;
      qty: number;
      side: 'buy' | 'sell';
      type?: string;
      timeInForce?: string;
      limitPrice?: number;
    }) => client.post<any>('/api/trade', trade),

    cancelOrder: (orderId: string) =>
      client.delete(`/api/orders/${orderId}`),
  },

  // Goals
  goals: {
    list: () => client.get<any[]>('/api/goals'),
    get: (id: string) => client.get<any>(`/api/goals/${id}`),
    create: (goal: any) => client.post<any>('/api/goals', goal),
    update: (id: string, updates: any) =>
      client.put<any>(`/api/goals/${id}`, updates),
    delete: (id: string) => client.delete(`/api/goals/${id}`),
    updateProgress: (id: string, amount: number) =>
      client.post<any>(`/api/goals/${id}/progress`, { amount }),
  },

  // Finance (Personal Finance Dashboard)
  finance: {
    getAccounts: () => client.get<any[]>('/api/finance/accounts'),
    getTransactions: (days: number = 90) =>
      client.get<any[]>(`/api/finance/transactions?days=${days}`),
    getSubscriptions: () => client.get<any[]>('/api/finance/subscriptions'),
    getNetWorth: () => client.get<any>('/api/finance/net-worth'),
    getCashFlow: (days: number = 30) =>
      client.get<any>(`/api/finance/cash-flow?days=${days}`),
    getHealthScore: () => client.get<any>('/api/finance/health-score'),
  },

  // Plaid Integration
  plaid: {
    createLinkToken: () => client.post<{ link_token: string }>('/api/plaid/link-token'),
    exchangePublicToken: (publicToken: string) =>
      client.post<any>('/api/plaid/exchange-token', { public_token: publicToken }),
    getAccounts: () => client.get<any[]>('/api/plaid/accounts'),
    getTransactions: (days: number = 90) =>
      client.get<any[]>(`/api/plaid/transactions?days=${days}`),
  },

  // Voice Commands
  voice: {
    execute: (audioFile: Blob) => {
      const formData = new FormData();
      formData.append('audio', audioFile);
      return fetch(`${API_BASE_URL}/api/voice/execute`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${TokenManager.getAccessToken()}`,
        },
        body: formData,
      }).then((r) => r.json());
    },
    confirm: (commandId: string) =>
      client.post(`/api/voice/confirm/${commandId}`, {}),
  },

  // RAG System
  rag: {
    query: (query: string, userId?: string) =>
      client.post<any>('/api/rag/query', { query, user_id: userId }),
    uploadDocument: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return fetch(`${API_BASE_URL}/api/rag/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${TokenManager.getAccessToken()}`,
        },
        body: formData,
      }).then((r) => r.json());
    },
  },

  // War Room (WebSocket connection handled separately)
  warroom: {
    getStatus: () => client.get<any>('/api/warroom/status'),
    start: (config?: any) => client.post<any>('/api/warroom/start', { config }),
    stop: () => client.post<any>('/api/warroom/stop', {}),
    pause: () => client.post<any>('/api/warroom/pause', {}),
    resume: () => client.post<any>('/api/warroom/resume', {}),
  },

  // Market Data
  market: {
    getQuote: (symbol: string) => client.get<any>(`/api/market/quote/${symbol}`),
    getHistoricalData: (symbol: string, timeframe: string = '1D', limit: number = 100) =>
      client.get<any>(`/api/market/historical/${symbol}?timeframe=${timeframe}&limit=${limit}`),
  },
};

export default BackendAPI;
