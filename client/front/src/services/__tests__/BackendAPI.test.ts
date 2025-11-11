/**
 * Unit tests for BackendAPI service
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BackendAPI, TokenManager } from '../BackendAPI';

describe('TokenManager', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should store and retrieve access token', () => {
    const token = 'test-access-token';
    TokenManager.setAccessToken(token);
    expect(TokenManager.getAccessToken()).toBe(token);
  });

  it('should store and retrieve refresh token', () => {
    const token = 'test-refresh-token';
    TokenManager.setRefreshToken(token);
    expect(TokenManager.getRefreshToken()).toBe(token);
  });

  it('should clear all tokens', () => {
    TokenManager.setAccessToken('access');
    TokenManager.setRefreshToken('refresh');
    TokenManager.clearTokens();

    expect(TokenManager.getAccessToken()).toBeNull();
    expect(TokenManager.getRefreshToken()).toBeNull();
  });

  it('should check authentication status', () => {
    expect(TokenManager.isAuthenticated()).toBe(false);

    TokenManager.setAccessToken('token');
    expect(TokenManager.isAuthenticated()).toBe(true);
  });
});

describe('BackendAPI', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    (global.fetch as any).mockReset();
  });

  describe('Authentication', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await BackendAPI.auth.login('testuser', 'password');

      expect(result).toEqual(mockResponse);
      expect(TokenManager.getAccessToken()).toBe('mock-access-token');
      expect(TokenManager.getRefreshToken()).toBe('mock-refresh-token');
    });

    it('should handle login failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' }),
      });

      await expect(
        BackendAPI.auth.login('testuser', 'wrongpassword')
      ).rejects.toThrow();
    });

    it('should logout successfully', async () => {
      TokenManager.setAccessToken('token');
      TokenManager.setRefreshToken('refresh');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Logged out' }),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      await BackendAPI.auth.logout();

      expect(TokenManager.getAccessToken()).toBeNull();
      expect(TokenManager.getRefreshToken()).toBeNull();
    });
  });

  describe('Portfolio', () => {
    it('should get portfolio data', async () => {
      const mockPortfolio = {
        total_value: 100000,
        day_return: 2.5,
        total_return: 10.0,
      };

      TokenManager.setAccessToken('mock-token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPortfolio,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await BackendAPI.portfolio.get();

      expect(result).toEqual(mockPortfolio);
    });

    it('should include authorization header', async () => {
      TokenManager.setAccessToken('mock-token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      await BackendAPI.portfolio.get();

      const fetchCall = (global.fetch as any).mock.calls[0];
      expect(fetchCall[1].headers.Authorization).toBe('Bearer mock-token');
    });
  });

  describe('Trading', () => {
    it('should place a trade', async () => {
      const mockTrade = {
        symbol: 'AAPL',
        qty: 10,
        side: 'buy',
      };

      const mockResponse = {
        id: 'order-123',
        status: 'pending',
        ...mockTrade,
      };

      TokenManager.setAccessToken('mock-token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await BackendAPI.trading.placeTrade(mockTrade as any);

      expect(result).toEqual(mockResponse);
    });
  });

  describe('Goals', () => {
    it('should list all goals', async () => {
      const mockGoals = [
        { id: '1', title: 'Goal 1', target_amount: 10000 },
        { id: '2', title: 'Goal 2', target_amount: 20000 },
      ];

      TokenManager.setAccessToken('mock-token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockGoals,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await BackendAPI.goals.list();

      expect(result).toEqual(mockGoals);
      expect(result).toHaveLength(2);
    });

    it('should create a goal', async () => {
      const newGoal = {
        title: 'New Goal',
        target_amount: 50000,
        description: 'Test goal',
      };

      const mockResponse = {
        id: 'goal-123',
        ...newGoal,
        created_at: new Date().toISOString(),
      };

      TokenManager.setAccessToken('mock-token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
        headers: new Headers({ 'content-type': 'application/json' }),
      });

      const result = await BackendAPI.goals.create(newGoal);

      expect(result).toEqual(mockResponse);
    });
  });
});
