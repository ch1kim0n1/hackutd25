import React from 'react';

const TranscriptDisplay = ({ transcript, interimTranscript, isPaused, onSend, onClear }) => {
  const fullText = transcript + (interimTranscript ? ' ' + interimTranscript : '');

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-sm text-gray-700">Live Transcription</h3>
        {transcript && (
          <button
            onClick={onClear}
            className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded border border-gray-300"
          >
            Clear
          </button>
        )}
      </div>

      <div className="min-h-[100px] max-h-[200px] overflow-y-auto p-3 bg-gray-50 rounded border border-gray-200">
        {fullText ? (
          <p className="text-sm text-gray-800">
            <span className="font-medium">{transcript}</span>
            {interimTranscript && (
              <span className="text-gray-500 italic"> {interimTranscript}</span>
            )}
          </p>
        ) : (
          <p className="text-sm text-gray-400 italic">
            Start speaking to see your words appear here...
          </p>
        )}
      </div>

      {isPaused && (
        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-300 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-yellow-600 font-bold">⏸️ Hold On Detected!</span>
          </div>
          <p className="text-xs text-yellow-700 mb-3">
            Agents paused. Continue speaking to add more context, then send.
          </p>
          <button
            onClick={onSend}
            disabled={!transcript}
            className="w-full bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded transition-colors"
          >
            Send to Agents
          </button>
        </div>
      )}

      {transcript && !isPaused && (
        <button
          onClick={onSend}
          className="w-full mt-3 bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded transition-colors"
        >
          Send to Agents
        </button>
      )}
    </div>
  );
};

export default TranscriptDisplay;
