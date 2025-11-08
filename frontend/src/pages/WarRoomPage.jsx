import React from 'react';
import Header from '../components/layout/Header';
import Sidebar from '../components/layout/Sidebar';
import Card from '../components/ui/Card';

const WarRoomPage = () => {
  return (
    <div className="flex">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen">
        <Header />
        <main className="flex-1 p-6 bg-gray-100">
          <h2 className="text-2xl font-bold mb-6">Agent War Room</h2>
          <Card className="h-full">
            {/* Live agent conversation display will go here */}
            <p>Agent conversations will appear here...</p>
          </Card>
        </main>
      </div>
    </div>
  );
};

export default WarRoomPage;
