import React from 'react';
import Card from '../ui/Card';

const HealthScoreCard = ({ healthScore }) => {
  if (!healthScore) return null;

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score) => {
    if (score >= 80) return 'bg-green-100 border-green-300';
    if (score >= 60) return 'bg-blue-100 border-blue-300';
    if (score >= 40) return 'bg-yellow-100 border-yellow-300';
    return 'bg-red-100 border-red-300';
  };

  return (
    <Card className="p-6">
      <h3 className="font-bold text-lg mb-4">❤️ Financial Health Score</h3>
      
      <div className={`text-center p-6 rounded-lg border-2 mb-4 ${getScoreBgColor(healthScore.score)}`}>
        <div className={`text-6xl font-bold mb-2 ${getScoreColor(healthScore.score)}`}>
          {healthScore.score}
        </div>
        <div className={`text-xl font-medium ${getScoreColor(healthScore.score)}`}>
          {healthScore.rating}
        </div>
      </div>

      <div className="space-y-3">
        {healthScore.factors.map((factor, idx) => (
          <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-100">
            <div>
              <p className="font-medium text-gray-900">{factor.factor}</p>
              <p className="text-xs text-gray-600">{factor.status}</p>
            </div>
            <span className={`font-bold ${getScoreColor(factor.score)}`}>
              {factor.score}/30
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Emergency Fund</span>
          <span className="font-medium">{healthScore.emergency_fund_months.toFixed(1)} months</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Debt to Income</span>
          <span className="font-medium">{healthScore.debt_to_income_ratio.toFixed(1)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Savings Rate</span>
          <span className="font-medium">{healthScore.savings_rate.toFixed(1)}%</span>
        </div>
      </div>
    </Card>
  );
};

export default HealthScoreCard;
