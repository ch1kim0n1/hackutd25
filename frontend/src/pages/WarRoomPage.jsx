import React, { useState, useCallback } from 'react';
import Header from '../components/layout/Header';
import Sidebar from '../components/layout/Sidebar';
import Card from '../components/ui/Card';
import useWebSocket from '../hooks/useWebSocket';
import MessageList from '../components/WarRoom/MessageList';
import ConnectionStatus from '../components/WarRoom/ConnectionStatus';
import WarRoomControls from '../components/WarRoom/WarRoomControls';

const WarRoomPage = () => {
  const { messages, isConnected, error, sendMessage, clearMessages } = useWebSocket();
  const [isOrchestratorRunning, setIsOrchestratorRunning] = useState(false);

  // Start orchestrator via API
  const handleStartOrchestrator = useCallback(async (config) => {
    try {
      const response = await fetch('http://localhost:8000/orchestrator/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config }),
      });

      if (response.ok) {
        setIsOrchestratorRunning(true);
        console.log('✅ Orchestrator started');
      } else {
        console.error('❌ Failed to start orchestrator');
        alert('Failed to start orchestrator. Check backend logs.');
      }
    } catch (err) {
      console.error('Error starting orchestrator:', err);
      alert('Error connecting to backend. Is the server running?');
    }
  }, []);

  // Stop orchestrator
  const handleStopOrchestrator = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/orchestrator/stop', {
        method: 'POST',
      });

      if (response.ok) {
        setIsOrchestratorRunning(false);
        console.log('⏹️ Orchestrator stopped');
      }
    } catch (err) {
      console.error('Error stopping orchestrator:', err);
    }
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen">
        <Header />
        <main className="flex-1 p-6 bg-gray-100 overflow-hidden">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">🎭 Agent War Room</h2>
            <ConnectionStatus isConnected={isConnected} error={error} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-180px)]">
            {/* Main War Room Display (75%) */}
            <div className="lg:col-span-3 h-full">
              <Card className="h-full flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-lg">Live Agent Conversations</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={clearMessages}
                      className="text-sm text-gray-600 hover:text-gray-800 px-3 py-1 rounded border border-gray-300"
                    >
                      🗑️ Clear
                    </button>
                    <span className="text-sm text-gray-500 px-3 py-1">
                      {messages.length} messages
                    </span>
                  </div>
                </div>
                
                <div className="flex-1 overflow-y-auto pr-2">
                  <MessageList messages={messages} isConnected={isConnected} />
                </div>
              </Card>
            </div>

            {/* Controls Panel (25%) */}
            <div className="lg:col-span-1 h-full">
              <WarRoomControls
                onStartOrchestrator={handleStartOrchestrator}
                onStopOrchestrator={handleStopOrchestrator}
                isRunning={isOrchestratorRunning}
                isConnected={isConnected}
              />

              {/* Agent Legend */}
              <Card className="mt-4 p-4">
                <h4 className="font-bold text-sm mb-3">Agent Legend</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span>🔍</span>
                    <span className="text-blue-600">Market Agent</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>🧠</span>
                    <span className="text-green-600">Strategy Agent</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>⚠️</span>
                    <span className="text-red-600">Risk Agent</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>⚡</span>
                    <span className="text-purple-600">Executor Agent</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>💬</span>
                    <span className="text-yellow-600">Explainer Agent</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>👤</span>
                    <span className="text-indigo-600">You</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default WarRoomPage;
