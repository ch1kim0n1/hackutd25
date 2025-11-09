import React, { useState, useEffect } from 'react';
import Header from '../components/layout/Header';
import Card from '../components/ui/Card';
import NetWorthCard from '../components/Finance/NetWorthCard';
import CashFlowCard from '../components/Finance/CashFlowCard';
import HealthScoreCard from '../components/Finance/HealthScoreCard';
import SubscriptionsCard from '../components/Finance/SubscriptionsCard';
import NewsFeed from '../components/News/NewsFeed';

const DashboardPage = () => {
  const [accounts, setAccounts] = useState([]);
  const [netWorth, setNetWorth] = useState(null);
  const [cashFlow, setCashFlow] = useState(null);
  const [healthScore, setHealthScore] = useState(null);
  const [subscriptions, setSubscriptions] = useState(null);
  const [news, setNews] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);

        const [accountsRes, netWorthRes, cashFlowRes, healthScoreRes, subscriptionsRes, newsRes] = await Promise.all([
          fetch('http://localhost:8000/api/finance/accounts'),
          fetch('http://localhost:8000/api/finance/net-worth'),
          fetch('http://localhost:8000/api/finance/cash-flow'),
          fetch('http://localhost:8000/api/finance/health-score'),
          fetch('http://localhost:8000/api/finance/subscriptions'),
          fetch('http://localhost:8000/api/news?limit=10'),
        ]);

        const [accountsData, netWorthData, cashFlowData, healthScoreData, subscriptionsData, newsData] = await Promise.all([
          accountsRes.json(),
          netWorthRes.json(),
          cashFlowRes.json(),
          healthScoreRes.json(),
          subscriptionsRes.json(),
          newsRes.json(),
        ]);

        setAccounts(accountsData.accounts || []);
        setNetWorth(netWorthData);
        setCashFlow(cashFlowData);
        setHealthScore(healthScoreData);
        setSubscriptions(subscriptionsData);
        setNews(newsData.news || []);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatCurrency = (value) => {
    return '$' + parseFloat(value || 0).toLocaleString('en-US', { 
      minimumFractionDigits: 0, 
      maximumFractionDigits: 0 
    });
  };

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <main className="flex-1 p-6 bg-gray-100 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">💰 Personal Finance Dashboard</h2>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors"
          >
            🔄 Refresh
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-gray-600">Loading your financial data...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <NetWorthCard netWorthData={netWorth} />
              <CashFlowCard cashFlowData={cashFlow} />
              <HealthScoreCard healthScore={healthScore} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="font-bold text-lg mb-4">🏦 Accounts</h3>
                <div className="space-y-3">
                  {accounts.map((account, idx) => (
                    <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">{account.name}</p>
                        <p className="text-xs text-gray-600">{account.institution} • {account.subtype}</p>
                      </div>
                      <div className="text-right">
                        <p className={`font-bold ${account.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(account.balance)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              <SubscriptionsCard subscriptions={subscriptions} />
            </div>

            <NewsFeed news={news} />
          </div>
        )}
      </main>
    </div>
  );
};

export default DashboardPage;
