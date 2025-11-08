import React from 'react';
import Header from '../components/layout/Header';
import Sidebar from '../components/layout/Sidebar';
import Card from '../components/ui/Card';

const DashboardPage = () => {
  return (
    <div className="flex">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen">
        <Header />
        <main className="flex-1 p-6 bg-gray-100">
          <h2 className="text-2xl font-bold mb-6">Personal Finance Dashboard</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <h3 className="font-bold">Net Worth</h3>
              <p className="text-2xl">$123,456.78</p>
            </Card>
            <Card>
              <h3 className="font-bold">Cash Flow</h3>
              <p className="text-2xl text-green-500">+$2,000.00</p>
            </Card>
            <Card>
              <h3 className="font-bold">AI Health Score</h3>
              <p className="text-2xl">85/100</p>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardPage;
