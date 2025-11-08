import React from 'react';
import DashboardPage from './pages/DashboardPage';
import { AgentProvider } from './contexts/AgentContext';
import './styles/globals.css';

function App() {
  return (
    <AgentProvider>
      <div className="App">
        {/* Basic router could be added here to switch between pages */}
        <DashboardPage />
      </div>
    </AgentProvider>
  );
}

export default App;
