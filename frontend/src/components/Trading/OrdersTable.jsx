import React from 'react';

const OrdersTable = ({ orders }) => {
  if (!orders || orders.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p className="text-lg mb-2">No recent orders</p>
        <p className="text-sm">Your order history will appear here</p>
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'filled':
        return 'bg-green-100 text-green-800';
      case 'partially_filled':
        return 'bg-blue-100 text-blue-800';
      case 'pending_new':
      case 'accepted':
        return 'bg-yellow-100 text-yellow-800';
      case 'canceled':
      case 'expired':
        return 'bg-gray-100 text-gray-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatCurrency = (value) => {
    return '$' + parseFloat(value || 0).toFixed(2);
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Time</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Symbol</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Side</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Qty</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Type</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Price</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {orders.map((order, idx) => (
            <tr key={idx} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-sm text-gray-700">
                {formatDate(order.created_at || order.submitted_at)}
              </td>
              <td className="px-4 py-3">
                <span className="font-bold text-gray-900">{order.symbol}</span>
              </td>
              <td className="px-4 py-3">
                <span className={`text-xs font-medium px-2 py-1 rounded ${
                  order.side === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {order.side.toUpperCase()}
                </span>
              </td>
              <td className="px-4 py-3 text-right text-sm font-medium text-gray-900">
                {order.filled_qty || 0} / {order.qty}
              </td>
              <td className="px-4 py-3 text-sm text-gray-700 uppercase">{order.type}</td>
              <td className="px-4 py-3 text-right text-sm text-gray-900">
                {order.filled_avg_price ? formatCurrency(order.filled_avg_price) : 
                 order.limit_price ? formatCurrency(order.limit_price) : 'Market'}
              </td>
              <td className="px-4 py-3">
                <span className={`text-xs font-medium px-2 py-1 rounded ${getStatusColor(order.status)}`}>
                  {order.status.replace('_', ' ').toUpperCase()}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default OrdersTable;
