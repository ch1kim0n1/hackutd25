import React from 'react';
import Card from '../ui/Card';

const SubscriptionsCard = ({ subscriptions }) => {
  if (!subscriptions) return null;

  const formatCurrency = (value) => {
    return '$' + parseFloat(value || 0).toFixed(2);
  };

  const sortedSubscriptions = [...subscriptions.subscriptions].sort((a, b) => b.annual_cost - a.annual_cost);

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-lg">💳 Subscriptions</h3>
        <div className="text-right">
          <p className="text-xs text-gray-600">Total Annual</p>
          <p className="text-lg font-bold text-red-600">{formatCurrency(subscriptions.total_annual)}</p>
        </div>
      </div>

      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {sortedSubscriptions.map((sub, idx) => (
          <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors">
            <div>
              <p className="font-medium text-gray-900">{sub.merchant}</p>
              <p className="text-xs text-gray-600">{sub.category}</p>
            </div>
            <div className="text-right">
              <p className="font-bold text-gray-900">{formatCurrency(Math.abs(sub.amount))}/mo</p>
              <p className="text-xs text-gray-600">{formatCurrency(sub.annual_cost)}/yr</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Monthly Total</span>
          <span className="text-lg font-bold text-red-600">{formatCurrency(subscriptions.total_monthly)}</span>
        </div>
      </div>
    </Card>
  );
};

export default SubscriptionsCard;
