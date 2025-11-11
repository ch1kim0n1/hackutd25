/**
 * Example component showing how to use BackendAPI for trading operations
 *
 * Replace direct Alpaca API calls with BackendAPI service
 */

import React, { useState, useEffect } from 'react';
import BackendAPI from '@/services/BackendAPI';

export function TradingExample() {
  const [symbol, setSymbol] = useState('AAPL');
  const [quantity, setQuantity] = useState(10);
  const [positions, setPositions] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch positions on mount
  useEffect(() => {
    fetchPositions();
    fetchOrders();
  }, []);

  const fetchPositions = async () => {
    try {
      const data = await BackendAPI.portfolio.getPositions();
      setPositions(data);
    } catch (err) {
      console.error('Error fetching positions:', err);
    }
  };

  const fetchOrders = async () => {
    try {
      const data = await BackendAPI.portfolio.getOrders();
      setOrders(data);
    } catch (err) {
      console.error('Error fetching orders:', err);
    }
  };

  const handleBuy = async () => {
    setLoading(true);
    try {
      const result = await BackendAPI.trading.placeTrade({
        symbol,
        qty: quantity,
        side: 'buy',
        type: 'market',
      });

      console.log('Buy order placed:', result);
      alert(`Buy order placed for ${quantity} shares of ${symbol}`);

      // Refresh data
      await fetchPositions();
      await fetchOrders();
    } catch (err) {
      console.error('Error placing buy order:', err);
      alert('Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  const handleSell = async () => {
    setLoading(true);
    try {
      const result = await BackendAPI.trading.placeTrade({
        symbol,
        qty: quantity,
        side: 'sell',
        type: 'market',
      });

      console.log('Sell order placed:', result);
      alert(`Sell order placed for ${quantity} shares of ${symbol}`);

      // Refresh data
      await fetchPositions();
      await fetchOrders();
    } catch (err) {
      console.error('Error placing sell order:', err);
      alert('Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Trading Example</h2>

      {/* Trade Form */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Place Order</h3>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 border rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Quantity</label>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value))}
              min="1"
              className="w-full px-3 py-2 border rounded"
            />
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={handleBuy}
            disabled={loading}
            className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Buy'}
          </button>

          <button
            onClick={handleSell}
            disabled={loading}
            className="flex-1 bg-red-600 text-white py-2 rounded hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Sell'}
          </button>
        </div>
      </div>

      {/* Current Positions */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Current Positions</h3>

        {positions.length === 0 ? (
          <p className="text-gray-500">No positions</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Symbol</th>
                  <th className="text-right py-2">Quantity</th>
                  <th className="text-right py-2">Avg Price</th>
                  <th className="text-right py-2">Current Price</th>
                  <th className="text-right py-2">P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="py-2">{pos.symbol}</td>
                    <td className="text-right">{pos.qty}</td>
                    <td className="text-right">${pos.avg_entry_price}</td>
                    <td className="text-right">${pos.current_price}</td>
                    <td className={`text-right ${pos.unrealized_pl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${pos.unrealized_pl}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Orders */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Orders</h3>

        {orders.length === 0 ? (
          <p className="text-gray-500">No orders</p>
        ) : (
          <div className="space-y-2">
            {orders.slice(0, 5).map((order, idx) => (
              <div key={idx} className="border rounded p-3">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-semibold">{order.symbol}</span>
                    <span className="ml-2 text-sm text-gray-600">
                      {order.side} {order.qty} @ {order.type}
                    </span>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded ${
                    order.status === 'filled' ? 'bg-green-100 text-green-800' :
                    order.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {order.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded text-sm">
        <p className="font-semibold mb-2">Migration from Direct Alpaca:</p>
        <div className="space-y-1">
          <p><strong>Before:</strong> <code>alpacaClient.buy(symbol, qty)</code></p>
          <p><strong>After:</strong> <code>BackendAPI.trading.placeTrade({'{'}symbol, qty, side: 'buy'{'}'})</code></p>
          <p className="mt-2 text-xs text-gray-600">
            All trading now goes through the backend for better security, logging, and agent integration.
          </p>
        </div>
      </div>
    </div>
  );
}

export default TradingExample;
