import React from 'react';
import Card from '../ui/Card';

const CashFlowCard = ({ cashFlowData }) => {
  if (!cashFlowData) return null;

  const formatCurrency = (value) => {
    return '$' + parseFloat(value || 0).toLocaleString('en-US', { 
      minimumFractionDigits: 0, 
      maximumFractionDigits: 0 
    });
  };

  return (
    <Card className="p-6">
      <h3 className="font-bold text-lg mb-4">📈 Cash Flow (Last 30 Days)</h3>
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Income</span>
          <span className="text-lg font-bold text-green-600">{formatCurrency(cashFlowData.income)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Expenses</span>
          <span className="text-lg font-bold text-red-600">-{formatCurrency(cashFlowData.expenses)}</span>
        </div>
        <div className="border-t pt-3 flex justify-between items-center">
          <span className="font-medium text-gray-900">Net Cash Flow</span>
          <span className={`text-xl font-bold ${cashFlowData.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {cashFlowData.net_cash_flow >= 0 ? '+' : ''}{formatCurrency(cashFlowData.net_cash_flow)}
          </span>
        </div>
        <div className="bg-blue-50 p-3 rounded-md">
          <div className="flex justify-between items-center">
            <span className="text-sm text-blue-800">Savings Rate</span>
            <span className="text-lg font-bold text-blue-900">{cashFlowData.savings_rate.toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default CashFlowCard;
