import React, { useState } from 'react';
import Header from '../components/layout/Header';
import Card from '../components/ui/Card';
import usePortfolio from '../hooks/usePortfolio';
import PortfolioSummary from '../components/Trading/PortfolioSummary';
import PositionsTable from '../components/Trading/PositionsTable';
import OrdersTable from '../components/Trading/OrdersTable';
import TradeModal from '../components/Trading/TradeModal';

const TradingPage = () => {
  const { portfolio, positions, account, orders, isLoading, error, placeOrder, refresh } = usePortfolio();
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('positions');

  const handlePlaceOrder = async (orderData) => {
    try {
      await placeOrder(orderData);
      alert('Order placed successfully!');
    } catch (err) {
      alert('Failed to place order: ' + err.message);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <main className="flex-1 p-6 bg-gray-100 overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">💼 Live Trading</h2>
          <div className="flex gap-3">
            <button
              onClick={refresh}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              🔄 Refresh
            </button>
            <button
              onClick={() => setIsTradeModalOpen(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors"
            >
              + New Order
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
            <p className="font-medium">Error: {error}</p>
            <p className="text-sm mt-1">Make sure the backend is running and Alpaca credentials are configured.</p>
          </div>
        )}

        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="font-bold text-lg mb-4">Account Summary</h3>
            <PortfolioSummary account={account} portfolio={portfolio} />
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex gap-4">
                <button
                  onClick={() => setActiveTab('positions')}
                  className={`px-4 py-2 font-medium rounded-md transition-colors ${
                    activeTab === 'positions'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📊 Positions ({positions?.length || 0})
                </button>
                <button
                  onClick={() => setActiveTab('orders')}
                  className={`px-4 py-2 font-medium rounded-md transition-colors ${
                    activeTab === 'orders'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📋 Orders ({orders?.length || 0})
                </button>
              </div>

              {account && (
                <div className="text-sm text-gray-600">
                  <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                    account.status === 'ACTIVE' ? 'bg-green-500' : 'bg-red-500'
                  }`}></span>
                  {account.status || 'Paper Trading'}
                </div>
              )}
            </div>

            {isLoading ? (
              <div className="text-center py-8 text-gray-500">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                <p>Loading {activeTab}...</p>
              </div>
            ) : activeTab === 'positions' ? (
              <PositionsTable positions={positions} />
            ) : (
              <OrdersTable orders={orders} />
            )}
          </Card>

          <Card className="p-4 bg-blue-50 border-2 border-blue-200">
            <div className="flex items-start gap-3">
              <span className="text-2xl">💡</span>
              <div>
                <h4 className="font-bold text-blue-900 mb-1">Multi-Agent Trading</h4>
                <p className="text-sm text-blue-800">
                  Orders placed here are executed directly. For AI-driven trading, use the War Room to let the
                  Strategy Agent, Risk Agent, and Executor Agent collaborate on trade decisions.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </main>

      <TradeModal
        isOpen={isTradeModalOpen}
        onClose={() => setIsTradeModalOpen(false)}
        onConfirm={handlePlaceOrder}
      />
    </div>
  );
};

export default TradingPage;
