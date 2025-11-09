import React from 'react';

/**
 * Agent color scheme for War Room
 */
const AGENT_COLORS = {
  market: {
    bg: 'bg-blue-50',
    border: 'border-blue-500',
    text: 'text-blue-900',
    badge: 'bg-blue-500',
    icon: '🔍'
  },
  strategy: {
    bg: 'bg-green-50',
    border: 'border-green-500',
    text: 'text-green-900',
    badge: 'bg-green-500',
    icon: '🧠'
  },
  risk: {
    bg: 'bg-red-50',
    border: 'border-red-500',
    text: 'text-red-900',
    badge: 'bg-red-500',
    icon: '⚠️'
  },
  executor: {
    bg: 'bg-purple-50',
    border: 'border-purple-500',
    text: 'text-purple-900',
    badge: 'bg-purple-500',
    icon: '⚡'
  },
  explainer: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-500',
    text: 'text-yellow-900',
    badge: 'bg-yellow-500',
    icon: '💬'
  },
  user: {
    bg: 'bg-indigo-50',
    border: 'border-indigo-500',
    text: 'text-indigo-900',
    badge: 'bg-indigo-500',
    icon: '👤'
  },
  system: {
    bg: 'bg-gray-50',
    border: 'border-gray-400',
    text: 'text-gray-900',
    badge: 'bg-gray-500',
    icon: '🤖'
  }
};

/**
 * Individual message component in the War Room
 */
const AgentMessage = ({ message }) => {
  const agent = message.from?.toLowerCase() || 'system';
  const colors = AGENT_COLORS[agent] || AGENT_COLORS.system;
  
  const timestamp = new Date(message.timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  return (
    <div className={`p-4 rounded-lg border-l-4 ${colors.border} ${colors.bg} mb-3 animate-fade-in`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{colors.icon}</span>
          <span className={`font-bold ${colors.text} capitalize`}>
            {message.from || 'System'}
          </span>
          {message.to && message.to !== 'all' && (
            <span className="text-gray-500 text-sm">
              → {message.to}
            </span>
          )}
        </div>
        <span className="text-xs text-gray-500">{timestamp}</span>
      </div>
      
      <div className={`${colors.text} whitespace-pre-wrap`}>
        {message.content}
      </div>

      {/* Show metadata if available */}
      {message.data && Object.keys(message.data).length > 0 && (
        <details className="mt-2">
          <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800">
            View Details
          </summary>
          <pre className="text-xs bg-white p-2 rounded mt-1 overflow-x-auto">
            {JSON.stringify(message.data, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};

/**
 * Message list component for War Room
 * Displays real-time agent conversations with auto-scroll
 */
const MessageList = ({ messages, isConnected }) => {
  const messagesEndRef = React.useRef(null);

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <div className="text-6xl mb-4">🤖</div>
        <p className="text-lg font-medium">
          {isConnected ? 'Waiting for agent activity...' : 'Connecting to War Room...'}
        </p>
        <p className="text-sm mt-2">
          {isConnected 
            ? 'Start the orchestrator to see agent conversations' 
            : 'Establishing WebSocket connection...'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {messages.map((message) => (
        <AgentMessage key={message.id} message={message} />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
