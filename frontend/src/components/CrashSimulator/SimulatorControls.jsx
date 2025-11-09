import React, { useState, useEffect, useCallback } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const SimulatorControls = ({ onStart, onStop, onLoadScenario, isRunning, scenarios }) => {
  const [selectedScenario, setSelectedScenario] = useState('2008_crisis');
  const [speed, setSpeed] = useState(100);
  const [riskTolerance, setRiskTolerance] = useState('moderate');

  const handleStart = () => {
    onStart({
      scenario: selectedScenario,
      speed_multiplier: speed,
      risk_tolerance: riskTolerance,
    });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm space-y-4">
      <h3 className="font-bold text-lg">🎮 Crash Simulator Controls</h3>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Historical Scenario
        </label>
        <select
          value={selectedScenario}
          onChange={(e) => {
            setSelectedScenario(e.target.value);
            onLoadScenario(e.target.value);
          }}
          disabled={isRunning}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {Object.entries(scenarios).map(([key, value]) => (
            <option key={key} value={key}>
              {value.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Simulation Speed: {speed}x
        </label>
        <input
          type="range"
          min="1"
          max="200"
          value={speed}
          onChange={(e) => setSpeed(parseInt(e.target.value))}
          disabled={isRunning}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>1x</span>
          <span>50x</span>
          <span>100x</span>
          <span>200x</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Risk Tolerance
        </label>
        <select
          value={riskTolerance}
          onChange={(e) => setRiskTolerance(e.target.value)}
          disabled={isRunning}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="conservative">Conservative</option>
          <option value="moderate">Moderate</option>
          <option value="aggressive">Aggressive</option>
        </select>
      </div>

      <div className="flex gap-2">
        {!isRunning ? (
          <button
            onClick={handleStart}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded transition-colors"
          >
            ▶️ Start Simulation
          </button>
        ) : (
          <button
            onClick={onStop}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded transition-colors"
          >
            ⏹️ Stop
          </button>
        )}
      </div>
    </div>
  );
};

export default SimulatorControls;
