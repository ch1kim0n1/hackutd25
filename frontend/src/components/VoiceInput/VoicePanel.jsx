import React, { useCallback } from 'react';
import useVoiceRecognition from '../../hooks/useVoiceRecognition';
import VoiceButton from './VoiceButton';
import TranscriptDisplay from './TranscriptDisplay';

const VoicePanel = ({ onVoiceInput, isConnected }) => {
  const {
    isListening,
    transcript,
    interimTranscript,
    isPaused,
    error,
    isSupported,
    startListening,
    stopListening,
    clearTranscript,
    resumeAfterHoldOn,
  } = useVoiceRecognition();

  const handleSendTranscript = useCallback(async () => {
    if (!transcript.trim()) return;

    const userMessage = {
      type: 'user_voice',
      content: transcript.trim(),
      timestamp: new Date().toISOString(),
      pausedAgents: isPaused,
    };

    onVoiceInput(userMessage);
    
    clearTranscript();
    resumeAfterHoldOn();
    
    if (isListening) {
      stopListening();
    }
  }, [transcript, isPaused, onVoiceInput, clearTranscript, resumeAfterHoldOn, isListening, stopListening]);

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <h3 className="font-bold text-lg mb-4">🎤 Voice Input</h3>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">Error: {error}</p>
          </div>
        )}

        <div className="flex flex-col items-center">
          <VoiceButton
            isListening={isListening}
            isPaused={isPaused}
            onStart={startListening}
            onStop={stopListening}
            isSupported={isSupported}
          />
        </div>

        {!isConnected && isSupported && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-700">
              ⚠️ WebSocket not connected. Voice input will queue until connected.
            </p>
          </div>
        )}
      </div>

      {isSupported && (
        <TranscriptDisplay
          transcript={transcript}
          interimTranscript={interimTranscript}
          isPaused={isPaused}
          onSend={handleSendTranscript}
          onClear={clearTranscript}
        />
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800 font-medium mb-1">💡 Pro Tip:</p>
        <p className="text-xs text-blue-700">
          Say "hold on" to pause agents and add more context. They'll wait for your complete thought!
        </p>
      </div>
    </div>
  );
};

export default VoicePanel;
