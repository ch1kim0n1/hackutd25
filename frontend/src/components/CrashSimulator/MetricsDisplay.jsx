import React from 'react';

const MetricsDisplay = ({ metrics, isRunning }) => {
  if (!metrics) {
    return (
      <div className="grid grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-500 mb-1">Loading...</p>
            <p className="text-2xl font-bold text-gray-300">--</p>
          </div>
        ))}
      </div>
    );
  }

  const formatCurrency = (value) => {
    return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  };

  const formatPercent = (value) => {
    return (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className={`p-4 rounded-lg border-2 ${isRunning ? 'border-green-500 bg-green-50' : 'border-green-200 bg-green-50'}`}>
        <p className="text-xs text-green-700 font-medium mb-1">APEX Portfolio</p>
        <p className="text-2xl font-bold text-green-900">{formatCurrency(metrics.apex_value || 100000)}</p>
        <p className={`text-sm font-medium ${(metrics.apex_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {formatPercent(metrics.apex_return || 0)}
        </p>
      </div>

      <div className={`p-4 rounded-lg border-2 ${isRunning ? 'border-red-500 bg-red-50' : 'border-red-200 bg-red-50'}`}>
        <p className="text-xs text-red-700 font-medium mb-1">Buy & Hold SPY</p>
        <p className="text-2xl font-bold text-red-900">{formatCurrency(metrics.buy_hold_value || 100000)}</p>
        <p className={`text-sm font-medium ${(metrics.buy_hold_return || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {formatPercent(metrics.buy_hold_return || 0)}
        </p>
      </div>

      <div className="col-span-2 p-4 rounded-lg border-2 border-blue-200 bg-blue-50">
        <p className="text-xs text-blue-700 font-medium mb-1">APEX Outperformance</p>
        <p className={`text-3xl font-bold ${((metrics.apex_value || 100000) - (metrics.buy_hold_value || 100000)) >= 0 ? 'text-blue-900' : 'text-red-900'}`}>
          {formatPercent(((metrics.apex_value || 100000) / (metrics.buy_hold_value || 100000) - 1) * 100)}
        </p>
        <p className="text-sm text-blue-700 mt-1">
          {formatCurrency(Math.abs((metrics.apex_value || 100000) - (metrics.buy_hold_value || 100000)))} 
          {((metrics.apex_value || 100000) - (metrics.buy_hold_value || 100000)) >= 0 ? ' gained' : ' lost'}
        </p>
      </div>

      {metrics.day !== undefined && (
        <div className="col-span-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Simulation Day:</span>
            <span className="text-sm font-bold text-gray-900">{metrics.day}</span>
          </div>
          {metrics.date && (
            <div className="flex justify-between items-center mt-1">
              <span className="text-sm text-gray-600">Date:</span>
              <span className="text-sm font-medium text-gray-700">{metrics.date}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MetricsDisplay;
