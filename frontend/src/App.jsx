import React, { useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import WarRoomPage from './pages/WarRoomPage';
import CrashSimulatorPage from './pages/CrashSimulatorPage';
import TradingPage from './pages/TradingPage';
import Sidebar from './components/layout/Sidebar';
import { AgentProvider } from './contexts/AgentContext';
import './styles/globals.css';

function App() {
  const [currentPage, setCurrentPage] = useState('warroom');
  
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'warroom':
        return <WarRoomPage />;
      case 'crashsim':
        return <CrashSimulatorPage />;
      case 'trading':
        return <TradingPage />;
      default:
        return <WarRoomPage />;
    }
  };

  return (
    <AgentProvider>
      <div className="App flex">
        <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
        <div className="flex-1">
          {renderPage()}
        </div>
      </div>
    </AgentProvider>
  );
}

export default App;
