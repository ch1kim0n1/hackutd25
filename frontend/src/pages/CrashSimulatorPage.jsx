import React, { useState, useEffect, useCallback } from 'react';
import Header from '../components/layout/Header';
import Card from '../components/ui/Card';
import useWebSocket from '../hooks/useWebSocket';
import MessageList from '../components/WarRoom/MessageList';
import ConnectionStatus from '../components/WarRoom/ConnectionStatus';
import SimulatorControls from '../components/CrashSimulator/SimulatorControls';
import ComparisonChart from '../components/CrashSimulator/ComparisonChart';
import MetricsDisplay from '../components/CrashSimulator/MetricsDisplay';

const CrashSimulatorPage = () => {
  const { messages, isConnected, error, sendMessage } = useWebSocket();
  const [isSimulating, setIsSimulating] = useState(false);
  const [scenarios, setScenarios] = useState({
    '2008_crisis': { name: '2008 Financial Crisis' },
    '2020_covid': { name: '2020 COVID Crash' },
    '2022_bear': { name: '2022 Bear Market' },
  });
  const [comparisonData, setComparisonData] = useState(null);
  const [currentMetrics, setCurrentMetrics] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/crash-simulator/scenarios')
      .then(res => res.json())
      .then(data => {
        if (data.details) {
          setScenarios(data.details);
        }
      })
      .catch(err => console.error('Failed to load scenarios:', err));
  }, []);

  useEffect(() => {
    const latestMessage = messages[messages.length - 1];
    if (latestMessage && latestMessage.data) {
      if (latestMessage.data.apex_value !== undefined) {
        setCurrentMetrics(latestMessage.data);
      }
    }
  }, [messages]);

  const handleLoadScenario = useCallback(async (scenarioName) => {
    try {
      await fetch(`http://localhost:8000/crash-simulator/load/${scenarioName}`, {
        method: 'POST',
      });

      const compData = await fetch('http://localhost:8000/crash-simulator/comparison');
      const comparison = await compData.json();
      setComparisonData(comparison);
    } catch (err) {
      console.error('Error loading scenario:', err);
    }
  }, []);

  const handleStartSimulation = useCallback(async (config) => {
    try {
      await handleLoadScenario(config.scenario);

      const response = await fetch('http://localhost:8000/crash-simulator/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        setIsSimulating(true);
      }
    } catch (err) {
      console.error('Error starting simulation:', err);
    }
  }, [handleLoadScenario]);

  const handleStopSimulation = useCallback(async () => {
    try {
      await fetch('http://localhost:8000/crash-simulator/stop', {
        method: 'POST',
      });
      setIsSimulating(false);
    } catch (err) {
      console.error('Error stopping simulation:', err);
    }
  }, []);

  useEffect(() => {
    handleLoadScenario('2008_crisis');
  }, [handleLoadScenario]);

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <main className="flex-1 p-6 bg-gray-100 overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">📊 Market Crash Simulator</h2>
          <ConnectionStatus isConnected={isConnected} error={error} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-180px)]">
          <div className="lg:col-span-2 space-y-4 overflow-y-auto">
            <Card className="p-4">
              <h3 className="font-bold text-lg mb-4">Performance Comparison</h3>
              <ComparisonChart comparisonData={comparisonData} />
            </Card>

            <Card className="p-4">
              <MetricsDisplay metrics={currentMetrics} isRunning={isSimulating} />
            </Card>

            <Card className="p-4">
              <h3 className="font-bold text-lg mb-4">Agent Activity</h3>
              <div className="max-h-[300px] overflow-y-auto">
                <MessageList messages={messages} isConnected={isConnected} />
              </div>
            </Card>
          </div>

          <div className="lg:col-span-1 space-y-4">
            <SimulatorControls
              onStart={handleStartSimulation}
              onStop={handleStopSimulation}
              onLoadScenario={handleLoadScenario}
              isRunning={isSimulating}
              scenarios={scenarios}
            />

            <Card className="p-4">
              <h4 className="font-bold text-sm mb-3">📖 How It Works</h4>
              <div className="space-y-2 text-xs text-gray-700">
                <p>🔍 <strong>Market Agent</strong> monitors volatility</p>
                <p>🧠 <strong>Strategy Agent</strong> adjusts allocation</p>
                <p>⚠️ <strong>Risk Agent</strong> validates moves</p>
                <p>⚡ <strong>Executor Agent</strong> rebalances portfolio</p>
                <p className="mt-3 pt-3 border-t border-gray-200">
                  Watch how APEX adapts to crashes in real-time vs passive buy-and-hold!
                </p>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default CrashSimulatorPage;
