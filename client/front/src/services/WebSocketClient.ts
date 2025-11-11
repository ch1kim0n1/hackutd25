/**
 * WebSocket Client for War Room
 * Handles real-time updates from the backend orchestrator
 */

import { TokenManager } from './BackendAPI';

const WS_BASE_URL = import.meta.env.VITE_BACKEND_WS_URL || 'ws://localhost:8000';

export interface WarRoomMessage {
  type: string;
  data: any;
  timestamp?: string;
}

export type MessageHandler = (message: WarRoomMessage) => void;
export type ErrorHandler = (error: Event) => void;
export type CloseHandler = (event: CloseEvent) => void;

export class WarRoomWebSocket {
  private ws: WebSocket | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Set<MessageHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();
  private closeHandlers: Set<CloseHandler> = new Set();
  private isIntentionallyClosed = false;

  constructor(private userId?: string) {}

  /**
   * Connect to the War Room WebSocket
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.isIntentionallyClosed = false;
    const token = TokenManager.getAccessToken();
    const url = `${WS_BASE_URL}/ws/warroom${this.userId ? `?user_id=${this.userId}` : ''}${token ? `&token=${token}` : ''}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('War Room WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WarRoomMessage = JSON.parse(event.data);
          this.messageHandlers.forEach((handler) => handler(message));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.errorHandlers.forEach((handler) => handler(error));
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        this.closeHandlers.forEach((handler) => handler(event));

        // Attempt reconnection if not intentionally closed
        if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

          this.reconnectTimeout = setTimeout(() => {
            this.connect();
          }, delay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }

  /**
   * Send a message to the server
   */
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(typeof message === 'string' ? message : JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  /**
   * Close the WebSocket connection
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Add a message handler
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Add an error handler
   */
  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  /**
   * Add a close handler
   */
  onClose(handler: CloseHandler): () => void {
    this.closeHandlers.add(handler);
    return () => this.closeHandlers.delete(handler);
  }

  /**
   * Get connection state
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get ready state
   */
  getReadyState(): number | undefined {
    return this.ws?.readyState;
  }
}

/**
 * React hook for using War Room WebSocket
 */
export function useWarRoomWebSocket(userId?: string) {
  const wsRef = React.useRef<WarRoomWebSocket | null>(null);
  const [isConnected, setIsConnected] = React.useState(false);
  const [messages, setMessages] = React.useState<WarRoomMessage[]>([]);

  React.useEffect(() => {
    // Create WebSocket instance
    wsRef.current = new WarRoomWebSocket(userId);

    // Set up handlers
    const removeMessageHandler = wsRef.current.onMessage((message) => {
      setMessages((prev) => [...prev, message]);
    });

    const removeCloseHandler = wsRef.current.onClose(() => {
      setIsConnected(false);
    });

    // Connect
    wsRef.current.connect();
    setIsConnected(true);

    // Cleanup
    return () => {
      removeMessageHandler();
      removeCloseHandler();
      wsRef.current?.disconnect();
    };
  }, [userId]);

  const sendMessage = React.useCallback((message: any) => {
    wsRef.current?.send(message);
  }, []);

  const clearMessages = React.useCallback(() => {
    setMessages([]);
  }, []);

  return {
    isConnected,
    messages,
    sendMessage,
    clearMessages,
  };
}

// Add React import (this will be available in the frontend environment)
declare const React: any;

export default WarRoomWebSocket;
