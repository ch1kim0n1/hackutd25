import { useState, useEffect, useCallback } from 'react';
import useWebSocket from './useWebSocket';

const usePortfolio = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [positions, setPositions] = useState([]);
  const [account, setAccount] = useState(null);
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const { messages } = useWebSocket();

  const fetchPortfolio = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:8000/api/portfolio');
      if (!response.ok) throw new Error('Failed to fetch portfolio');
      const data = await response.json();
      setPortfolio(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchPositions = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/positions');
      if (!response.ok) throw new Error('Failed to fetch positions');
      const data = await response.json();
      setPositions(data);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const fetchAccount = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/account');
      if (!response.ok) throw new Error('Failed to fetch account');
      const data = await response.json();
      setAccount(data);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const fetchOrders = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/orders');
      if (!response.ok) throw new Error('Failed to fetch orders');
      const data = await response.json();
      setOrders(data);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const placeOrder = useCallback(async (orderData) => {
    try {
      const response = await fetch('http://localhost:8000/api/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData),
      });
      if (!response.ok) throw new Error('Failed to place order');
      const data = await response.json();
      await fetchOrders();
      await fetchPositions();
      await fetchAccount();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchOrders, fetchPositions, fetchAccount]);

  useEffect(() => {
    fetchPortfolio();
    fetchPositions();
    fetchAccount();
    fetchOrders();
  }, [fetchPortfolio, fetchPositions, fetchAccount, fetchOrders]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchPositions();
      fetchAccount();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchPositions, fetchAccount]);

  useEffect(() => {
    const latestMessage = messages[messages.length - 1];
    if (latestMessage && latestMessage.type === 'executor') {
      if (latestMessage.data && latestMessage.data.order) {
        fetchOrders();
        fetchPositions();
      }
    }
  }, [messages, fetchOrders, fetchPositions]);

  return {
    portfolio,
    positions,
    account,
    orders,
    isLoading,
    error,
    placeOrder,
    refresh: () => {
      fetchPortfolio();
      fetchPositions();
      fetchAccount();
      fetchOrders();
    },
  };
};

export default usePortfolio;
