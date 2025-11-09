import React from 'react';

const PositionsTable = ({ positions }) => {
  if (!positions || positions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p className="text-lg mb-2">No positions</p>
        <p className="text-sm">Start trading to see your positions here</p>
      </div>
    );
  }

  const formatCurrency = (value) => {
    return '$' + parseFloat(value || 0).toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
  };

  const formatPercent = (value) => {
    const num = parseFloat(value || 0);
    return (num >= 0 ? '+' : '') + num.toFixed(2) + '%';
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Symbol</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Quantity</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Avg Cost</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Current Price</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Market Value</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">P&L</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Return</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {positions.map((position, idx) => {
            const qty = parseFloat(position.qty || 0);
            const avgCost = parseFloat(position.avg_entry_price || 0);
            const currentPrice = parseFloat(position.current_price || 0);
            const marketValue = parseFloat(position.market_value || 0);
            const unrealizedPL = parseFloat(position.unrealized_pl || 0);
            const unrealizedPLPercent = parseFloat(position.unrealized_plpc || 0) * 100;

            return (
              <tr key={idx} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center">
                    <span className="font-bold text-gray-900">{position.symbol}</span>
                    <span className={`ml-2 text-xs px-2 py-0.5 rounded ${
                      position.side === 'long' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {position.side === 'long' ? 'LONG' : 'SHORT'}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-medium text-gray-900">{qty}</td>
                <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(avgCost)}</td>
                <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(currentPrice)}</td>
                <td className="px-4 py-3 text-right font-bold text-gray-900">{formatCurrency(marketValue)}</td>
                <td className={`px-4 py-3 text-right font-bold ${unrealizedPL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {unrealizedPL >= 0 ? '+' : ''}{formatCurrency(unrealizedPL)}
                </td>
                <td className={`px-4 py-3 text-right font-bold ${unrealizedPLPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(unrealizedPLPercent)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default PositionsTable;
