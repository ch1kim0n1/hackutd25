/**
 * Test setup file for Vitest
 * Configures testing environment and global mocks
 */

import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

global.localStorage = localStorageMock as any;

// Mock fetch API
global.fetch = vi.fn();

// Mock WebSocket
class WebSocketMock {
  onopen: any;
  onmessage: any;
  onerror: any;
  onclose: any;
  readyState = 0;

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = 1;
      this.onopen?.();
    }, 0);
  }

  send(data: any) {
    // Mock send
  }

  close() {
    this.readyState = 3;
    this.onclose?.();
  }
}

global.WebSocket = WebSocketMock as any;

// Mock environment variables
vi.mock('import.meta', () => ({
  env: {
    VITE_BACKEND_URL: 'http://localhost:8000',
    VITE_BACKEND_WS_URL: 'ws://localhost:8000',
  },
}));
