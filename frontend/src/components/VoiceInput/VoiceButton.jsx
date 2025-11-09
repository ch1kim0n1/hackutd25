import React from 'react';

const VoiceButton = ({ isListening, isPaused, onStart, onStop, isSupported }) => {
  if (!isSupported) {
    return (
      <div className="flex items-center justify-center p-4 bg-red-100 border border-red-300 rounded-lg">
        <span className="text-red-800 text-sm">
          ❌ Voice input not supported in this browser. Use Chrome or Edge.
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onClick={isListening ? onStop : onStart}
        className={`
          relative w-20 h-20 rounded-full border-4 transition-all duration-300 transform
          ${isListening 
            ? 'bg-red-500 border-red-600 scale-110 shadow-lg shadow-red-500/50' 
            : 'bg-blue-500 border-blue-600 hover:scale-105 shadow-md'
          }
          ${isPaused ? 'animate-pulse' : ''}
        `}
      >
        <div className="flex items-center justify-center h-full">
          {isListening ? (
            <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
              <rect x="6" y="4" width="3" height="12" rx="1"/>
              <rect x="11" y="4" width="3" height="12" rx="1"/>
            </svg>
          ) : (
            <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clipRule="evenodd"/>
            </svg>
          )}
        </div>
        
        {isListening && (
          <div className="absolute -inset-2 rounded-full border-4 border-red-500 animate-ping opacity-75"></div>
        )}
      </button>

      <div className="text-center">
        <p className="text-sm font-medium text-gray-700">
          {isListening ? (isPaused ? '⏸️ Paused - Say more' : '🎤 Listening...') : 'Push to Talk'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {isListening ? 'Click to stop' : 'Click to start'}
        </p>
      </div>
    </div>
  );
};

export default VoiceButton;
