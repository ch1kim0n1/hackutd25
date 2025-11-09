import React from 'react';
import Card from '../ui/Card';

const NetWorthCard = ({ netWorthData }) => {
  if (!netWorthData) return null;

  const formatCurrency = (value) => {
    return '$' + parseFloat(value || 0).toLocaleString('en-US', { 
      minimumFractionDigits: 0, 
      maximumFractionDigits: 0 
    });
  };

  return (
    <Card className="p-6">
      <h3 className="font-bold text-lg mb-4">💰 Net Worth</h3>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-1">Assets</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(netWorthData.assets)}</p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-1">Liabilities</p>
          <p className="text-2xl font-bold text-red-600">{formatCurrency(netWorthData.liabilities)}</p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-1">Net Worth</p>
          <p className="text-2xl font-bold text-blue-600">{formatCurrency(netWorthData.net_worth)}</p>
        </div>
      </div>
    </Card>
  );
};

export default NetWorthCard;
