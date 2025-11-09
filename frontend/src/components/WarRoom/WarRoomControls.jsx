import React, { useState } from 'react';
import Button from '../ui/Button';

/**
 * Control panel for War Room
 * Allows users to trigger orchestrator and control agents
 */
const WarRoomControls = ({ onStartOrchestrator, onStopOrchestrator, isRunning, isConnected }) => {
  const [marketCondition, setMarketCondition] = useState('normal');

  const handleStart = () => {
    onStartOrchestrator({
      marketCondition,
      timestamp: new Date().toISOString()
    });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <h3 className="font-bold text-lg mb-4">Orchestrator Controls</h3>
      
      <div className="space-y-4">
        {/* Market Condition Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Market Condition
          </label>
          <select
            value={marketCondition}
            onChange={(e) => setMarketCondition(e.target.value)}
            disabled={isRunning}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="normal">Normal Market</option>
            <option value="volatile">High Volatility</option>
            <option value="bullish">Bullish Trend</option>
            <option value="bearish">Bearish Trend</option>
            <option value="crisis">Crisis Mode</option>
          </select>
        </div>

        {/* Start/Stop Button */}
        <div className="flex gap-2">
          {!isRunning ? (
            <Button
              onClick={handleStart}
              disabled={!isConnected}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white"
            >
              🚀 Start Agent Discussion
            </Button>
          ) : (
            <Button
              onClick={onStopOrchestrator}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white"
            >
              ⏹️ Stop Orchestrator
            </Button>
          )}
        </div>

        {/* Status Info */}
        <div className="text-sm text-gray-600">
          {!isConnected && (
            <p className="text-yellow-600">⚠️ Waiting for WebSocket connection...</p>
          )}
          {isConnected && !isRunning && (
            <p className="text-green-600">✅ Ready to start agent discussions</p>
          )}
          {isRunning && (
            <p className="text-blue-600">🔄 Agents are actively debating...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default WarRoomControls;
