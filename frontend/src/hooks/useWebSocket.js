import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * WebSocket hook for real-time War Room communication
 * Handles connection, reconnection, and message streaming
 */
export const useWebSocket = (url = 'ws://localhost:8000/ws/warroom') => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 3000; // 3 seconds

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      console.log('🔌 Connecting to WebSocket:', url);
      
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 Received message:', message);
          
          setMessages((prev) => [...prev, {
            ...message,
            id: `${message.timestamp}-${Math.random()}`, // Ensure unique ID
            receivedAt: new Date().toISOString()
          }]);
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;
          console.log(`🔄 Reconnecting... (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY);
        } else {
          setError('Max reconnection attempts reached');
        }
      };

    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError(err.message);
    }
  }, [url]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  // Send message through WebSocket
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      console.log('📤 Sent message:', message);
      return true;
    } else {
      console.warn('Cannot send message: WebSocket not connected');
      return false;
    }
  }, []);

  // Clear all messages
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    messages,
    isConnected,
    error,
    sendMessage,
    clearMessages,
    reconnect: connect,
  };
};

export default useWebSocket;
