import React from 'react';

/**
 * Connection status indicator for War Room
 */
const ConnectionStatus = ({ isConnected, error }) => {
  if (error) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-red-100 border border-red-300 rounded-md">
        <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
        <span className="text-sm text-red-800 font-medium">Error: {error}</span>
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-green-100 border border-green-300 rounded-md">
        <span className="w-3 h-3 bg-green-500 rounded-full"></span>
        <span className="text-sm text-green-800 font-medium">Connected to War Room</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-yellow-100 border border-yellow-300 rounded-md">
      <span className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></span>
      <span className="text-sm text-yellow-800 font-medium">Connecting...</span>
    </div>
  );
};

export default ConnectionStatus;
