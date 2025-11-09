import React, { useState } from 'react';

const TradeModal = ({ isOpen, onClose, onConfirm }) => {
  const [symbol, setSymbol] = useState('');
  const [side, setSide] = useState('buy');
  const [quantity, setQuantity] = useState('');
  const [orderType, setOrderType] = useState('market');
  const [limitPrice, setLimitPrice] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const orderData = {
        symbol: symbol.toUpperCase(),
        side,
        qty: parseFloat(quantity),
        type: orderType,
        time_in_force: 'day',
      };

      if (orderType === 'limit' && limitPrice) {
        orderData.limit_price = parseFloat(limitPrice);
      }

      await onConfirm(orderData);
      
      setSymbol('');
      setQuantity('');
      setLimitPrice('');
      onClose();
    } catch (err) {
      console.error('Order submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Place Order</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="AAPL"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Side</label>
              <select
                value={side}
                onChange={(e) => setSide(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="100"
                min="1"
                step="1"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Order Type</label>
            <select
              value={orderType}
              onChange={(e) => setOrderType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="market">Market</option>
              <option value="limit">Limit</option>
            </select>
          </div>

          {orderType === 'limit' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Limit Price</label>
              <input
                type="number"
                value={limitPrice}
                onChange={(e) => setLimitPrice(e.target.value)}
                placeholder="150.00"
                step="0.01"
                min="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          )}

          <div className="bg-gray-50 p-4 rounded-md">
            <h3 className="font-medium text-sm text-gray-700 mb-2">Order Summary</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Action:</span>
                <span className={`font-medium ${side === 'buy' ? 'text-green-600' : 'text-red-600'}`}>
                  {side === 'buy' ? 'BUY' : 'SELL'} {quantity || '0'} shares
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Symbol:</span>
                <span className="font-medium text-gray-900">{symbol || '--'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium text-gray-900">{orderType.toUpperCase()}</span>
              </div>
              {orderType === 'limit' && limitPrice && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Limit Price:</span>
                  <span className="font-medium text-gray-900">${limitPrice}</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`flex-1 px-4 py-2 rounded-md text-white font-medium transition-colors disabled:opacity-50 ${
                side === 'buy' 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              {isSubmitting ? 'Submitting...' : 'Confirm Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TradeModal;
