import React from 'react';

const PortfolioSummary = ({ account, portfolio }) => {
  if (!account) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-50 p-4 rounded-lg border border-gray-200 animate-pulse">
            <p className="text-xs text-gray-500 mb-1">Loading...</p>
            <p className="text-2xl font-bold text-gray-300">--</p>
          </div>
        ))}
      </div>
    );
  }

  const formatCurrency = (value) => {
    return '$' + parseFloat(value || 0).toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
  };

  const portfolioValue = parseFloat(account.portfolio_value || 0);
  const equity = parseFloat(account.equity || 0);
  const cash = parseFloat(account.cash || 0);
  const buyingPower = parseFloat(account.buying_power || 0);
  const dayReturn = parseFloat(portfolio?.day_return || 0);
  const totalReturn = parseFloat(portfolio?.total_return || 0);

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
        <p className="text-xs text-blue-700 font-medium mb-1">Portfolio Value</p>
        <p className="text-2xl font-bold text-blue-900">{formatCurrency(portfolioValue)}</p>
        <p className={`text-xs font-medium mt-1 ${dayReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {dayReturn >= 0 ? '+' : ''}{dayReturn.toFixed(2)}% today
        </p>
      </div>

      <div className="bg-green-50 p-4 rounded-lg border-2 border-green-200">
        <p className="text-xs text-green-700 font-medium mb-1">Cash</p>
        <p className="text-2xl font-bold text-green-900">{formatCurrency(cash)}</p>
        <p className="text-xs text-green-600 mt-1">Available</p>
      </div>

      <div className="bg-purple-50 p-4 rounded-lg border-2 border-purple-200">
        <p className="text-xs text-purple-700 font-medium mb-1">Buying Power</p>
        <p className="text-2xl font-bold text-purple-900">{formatCurrency(buyingPower)}</p>
        <p className="text-xs text-purple-600 mt-1">4x leverage</p>
      </div>

      <div className={`p-4 rounded-lg border-2 ${totalReturn >= 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
        <p className={`text-xs font-medium mb-1 ${totalReturn >= 0 ? 'text-green-700' : 'text-red-700'}`}>
          Total Return
        </p>
        <p className={`text-2xl font-bold ${totalReturn >= 0 ? 'text-green-900' : 'text-red-900'}`}>
          {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
        </p>
        <p className={`text-xs font-medium mt-1 ${totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {formatCurrency((portfolioValue - equity) * (totalReturn / 100))}
        </p>
      </div>
    </div>
  );
};

export default PortfolioSummary;
