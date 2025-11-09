import { useState, useEffect, useRef } from "react";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Chip } from "@heroui/chip";

interface AgentQuestion {
  question_id: string;
  agent_id: string;
  question_type: string;
  question: string;
  options?: string[];
  context?: string;
  urgency?: string;
}

interface AgentMessage {
  id: string;
  type: string;
  from: string;
  to: string;
  content: string;
  timestamp: string;
  confidence?: number;
  reasoning?: string;
  question?: AgentQuestion;
  consensus_level?: string;
  data?: any;
  importance?: string;
  message_type?: string;
  question_id?: string;
}

// Removed complex orchestrator status - using simple chat status

const AGENTS = [
  { id: "market", name: "Market Agent", emoji: "🔍", color: "bg-blue-500" },
  { id: "strategy", name: "Strategy Agent", emoji: "🧠", color: "bg-purple-500" },
  { id: "risk", name: "Risk Agent", emoji: "⚠️", color: "bg-red-500" },
  { id: "executor", name: "Executor Agent", emoji: "⚡", color: "bg-green-500" },
  { id: "explainer", name: "Explainer Agent", emoji: "💬", color: "bg-yellow-500" },
  { id: "user", name: "You", emoji: "👤", color: "bg-gray-500" },
  { id: "system", name: "System", emoji: "⚙️", color: "bg-gray-400" }
];

const API_BASE_URL = 'http://localhost:8000';

const WarRoom = () => {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [userInput, setUserInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [pendingQuestions, setPendingQuestions] = useState<{[key: string]: AgentQuestion}>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // HTTP polling system for chat messages
  const [lastPolledId, setLastPolledId] = useState(-1);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [sessionStarted, setSessionStarted] = useState(false);
  const [currentMode, setCurrentMode] = useState<'introduction' | 'response'>('introduction');
  const [introductionsComplete, setIntroductionsComplete] = useState(false);

  // MANUAL POLLING ONLY - No automatic polling to prevent any automatic agent responses
  const manualPoll = async () => {
    try {
      console.log('🔍 Manual poll requested by user');
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/poll?since_id=${lastPolledId}`, {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache'
        }
      });
      if (!response.ok) {
        console.error('❌ Poll request failed:', response.status);
        return;
      }

      const data = await response.json();
      console.log('🔍 Poll response:', data);

      if (data.has_new && data.messages.length > 0) {
        console.log('📥 New messages received:', data.messages.length, data.messages);

        // Filter out any messages that look like test messages
        const validMessages = data.messages.filter((msg: any) => {
          return msg.type === 'agent_message' ||
                 msg.type === 'user_input' ||
                 msg.type === 'user_response';
        });

        if (validMessages.length > 0) {
          // Add new messages to the UI
          setMessages(prev => [...prev, ...validMessages.map((msg: any) => ({
            ...msg,
            id: `${msg.id}_${msg.from}_${msg.timestamp}_${Math.random().toString(36).substring(2, 15)}`
          }))]);

          // Update last polled ID
          setLastPolledId(data.latest_id);

          // Handle questions in new messages
          validMessages.forEach((message: AgentMessage) => {
            if (message.question) {
              console.log('❓ New question received:', message.question);
              setPendingQuestions(prev => {
                // Only add if not already present
                if (!prev[message.question!.question_id]) {
                  console.log('➕ Adding new question to pending list:', message.question!.question_id);
                  return {
                    ...prev,
                    [message.question!.question_id]: message.question!
                  };
                } else {
                  console.log('⚠️ Question already in pending list:', message.question!.question_id);
                  return prev;
                }
              });

              // Check if this is an introduction question (all agents have introduced)
              setPendingQuestions(prev => {
                const agentCount = Object.keys(prev).length + (prev[message.question!.question_id] ? 0 : 1);
                if (agentCount >= 4 && currentMode === 'introduction') {
                  console.log('🎯 All 4 agents have introduced themselves');
                  setIntroductionsComplete(true);
                  // All introductions done, ready for response mode
                  console.log('🔄 Ready to switch to response mode on next user message');
                }
                console.log('📊 Current pending questions count:', agentCount);
                return prev;
              });
            }

            // Show typing indicator for agent messages
            if (message.type === 'agent_message' || message.type === 'agent_consensus') {
              setIsTyping(true);
              setTimeout(() => setIsTyping(false), 1000);
            }

            // Detect mode changes based on message content
            if (message.content && message.content.includes('consensus') && currentMode === 'introduction') {
              console.log('🔄 Switching to response mode based on consensus message');
              setCurrentMode('response');
              setIntroductionsComplete(true);
            }
          });
        }
      }
    } catch (error) {
      console.error('❌ Polling error:', error);
    }
  };

  // DISABLED: No automatic polling - only manual polling when user requests it
  const startPolling = () => {
    console.log('🚫 Automatic polling DISABLED - only manual polling allowed');
    setIsConnected(true); // Mark as connected but don't start polling
  };

  // Stop polling
  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
    setIsConnected(false);
  };

  // Start chat session
  const startChatSession = async () => {
    try {
      console.log('🚀 Starting chat session...');
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        console.error('❌ Failed to start session:', response.status);
        return;
      }

      const data = await response.json();
      console.log('✅ Session started:', data);

      // Add initial messages to UI
      if (data.initial_messages) {
        setMessages(data.initial_messages.map((msg: any) => ({
          ...msg,
          id: `${msg.id}_${msg.from}_${msg.timestamp}_${Math.random().toString(36).substring(2, 15)}` // Truly unique composite key
        })));
        setLastPolledId(data.initial_messages[data.initial_messages.length - 1]?.id || -1);
      }

      setSessionStarted(true);
      startPolling();

    } catch (error) {
      console.error('❌ Error starting session:', error);
    }
  };

  // Initialize on component mount
  useEffect(() => {
    if (!sessionStarted) {
      startChatSession();
    }

    return () => {
      stopPolling();
    };
  }, []);

  // Load message history
  const loadMessageHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/messages?limit=20`);
      if (response.ok) {
        const data = await response.json();
        // Convert the simple message format to our expected format
        const formattedMessages = data.messages.map((msg: any) => ({
          ...msg,
          id: `${msg.id}_${msg.from}_${msg.timestamp}_${Math.random().toString(36).substring(2, 15)}`, // Truly unique composite key
          from_agent: msg.from,
          to_agent: msg.to,
          message: msg.content,
          message_type: msg.type,
          importance: msg.importance || 'medium'
        }));
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Error loading message history:', error);
    }
  };

  // Reset chat function
  const resetChat = async () => {
    try {
      console.log('🔄 Resetting chat...');
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/reset`, {
        method: 'POST'
      });

      if (!response.ok) {
        console.error('❌ Failed to reset chat:', response.status);
        return;
      }

      // Clear local state
      setMessages([]);
      setLastPolledId(-1);
      setPendingQuestions({});
      setUserInput('');
      setSessionStarted(false);
      setCurrentMode('introduction');
      setIntroductionsComplete(false);

      // Restart session
      await startChatSession();

      console.log('✅ Chat reset successfully');
    } catch (error) {
      console.error('❌ Error resetting chat:', error);
    }
  };

  // Load initial message history
  useEffect(() => {
    loadMessageHistory();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load chat status

  const getAgentInfo = (agentId: string) => {
    return AGENTS.find(agent => agent.id === agentId) || AGENTS[5]; // Default to user
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case "high": return "border-red-500 bg-red-50 dark:bg-red-900/20";
      case "medium": return "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20";
      case "low": return "border-gray-500 bg-gray-50 dark:bg-gray-900/20";
      default: return "border-gray-300";
    }
  };

  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case "analysis": return "text-blue-600";
      case "strategy": return "text-purple-600";
      case "risk_assessment": return "text-red-600";
      case "execution": return "text-green-600";
      case "explanation": return "text-yellow-600";
      case "user_input": return "text-gray-600";
      default: return "text-gray-600";
    }
  };

  const handleSendMessage = async () => {
    if (!userInput.trim()) {
      console.log('⚠️ Cannot send empty message');
      return;
    }

    const messageContent = userInput.trim();
    console.log('📤 User manually sending message:', messageContent);

    // Clear input immediately to prevent double-sending
    const contentToSend = messageContent;
    setUserInput("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content: contentToSend
        })
      });

      if (!response.ok) {
        console.error('❌ Failed to send message:', response.status);
        // Restore the input if sending failed
        setUserInput(contentToSend);
        return;
      }

      const data = await response.json();
      console.log('✅ Message sent successfully:', data);

      // Add to local messages for immediate display
      const userMessage: AgentMessage = {
        id: `${data.message_id}_${data.timestamp}_${Math.random().toString(36).substring(2, 15)}`, // Truly unique composite key
        type: "user_input",
        from: "user",
        to: "all",
        content: contentToSend,
        timestamp: data.timestamp,
        message_type: "user_input",
        importance: "high"
      };

      setMessages(prev => [...prev, userMessage]);
      setUserInput("");
      setIsTyping(true);

      // Auto-poll once to show immediate response
      setTimeout(() => manualPoll(), 500);

    } catch (error) {
      console.error('❌ Error sending message:', error);
      // Restore the input if there was an error
      setUserInput(contentToSend);
    }
  };

  const handleQuestionResponse = async (questionId: string, answer: string) => {
    try {
      console.log('📤 Sending question response via HTTP:', { questionId, answer });

      // Check if question still exists in pending questions
      const questionExists = Object.keys(pendingQuestions).includes(questionId);
      if (!questionExists) {
        console.log('⚠️ Question already answered or expired:', questionId);
        return;
      }

      // Send answer as query parameter (not JSON body)
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/respond/${questionId}?answer=${encodeURIComponent(answer)}`, {
        method: 'POST'
      });

      if (!response.ok) {
        console.error('❌ Failed to send question response:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('❌ Error details:', errorText);

        // If question not found, remove it from UI anyway
        if (response.status === 404 && errorText.includes('Question not found')) {
          console.log('🧹 Removing stale question from UI:', questionId);
          setPendingQuestions(prev => {
            const updated = { ...prev };
            delete updated[questionId];
            return updated;
          });
        }
        return;
      }

      const data = await response.json();
      console.log('✅ Question response sent:', data);

      // Remove question from pending list immediately
      setPendingQuestions(prev => {
        const updated = { ...prev };
        delete updated[questionId];
        console.log('🗑️ Removed question from pending list:', questionId, 'Remaining questions:', Object.keys(updated).length);
        return updated;
      });

      // Clear typing state and enable user input
      setIsTyping(false);
      console.log('✅ Question answered, UI should be responsive now');

      // Auto-poll once to show next agent response
      setTimeout(() => {
        console.log('🔄 Auto-polling for next agent response...');
        manualPoll();
      }, 500);

    } catch (error) {
      console.error('❌ Error sending question response:', error);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-white">APEX Agent War Room</h1>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
              <span className="text-sm text-gray-300">
                {isConnected ? (
                  Object.keys(pendingQuestions).length > 0
                    ? `Please answer the ${Object.keys(pendingQuestions).length} pending question${Object.keys(pendingQuestions).length > 1 ? 's' : ''} below`
                    : currentMode === 'introduction'
                    ? `Introduction Mode${introductionsComplete ? ' - Complete!' : ''} - Click "Check for Messages"`
                    : 'Response Mode - Click "Check for Messages"'
                ) : 'Initializing...'}
              </span>
            </div>
            <Chip size="sm" color="primary" variant="flat">
              Live Session
            </Chip>
          </div>

          <div className="flex items-center gap-4">
            {/* Agent Status */}
            <div className="flex gap-2">
              {AGENTS.slice(0, 4).map(agent => (
                <div key={agent.id} className="flex items-center gap-1">
                  <span className="text-sm">{agent.emoji}</span>
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                </div>
              ))}
            </div>

            <Button
              size="sm"
              variant="bordered"
              className="border-slate-600 text-slate-300"
              onPress={() => window.history.back()}
            >
              ← Exit War Room
            </Button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-6xl mx-auto space-y-4">
          {messages.map((message) => {
            const agent = getAgentInfo(message.from);
            const isUserMessage = message.from === 'user';
            const isAgentToAgent = message.to !== 'user' && message.to !== 'all' && !isUserMessage;
            const isToUser = message.to === 'user';

            return (
              <Card
                key={message.id}
                className={`max-w-4xl ${isUserMessage ? 'ml-auto' : ''} ${getImportanceColor(message.importance || 'medium')} ${
                  isAgentToAgent ? 'border-l-4 border-l-blue-500 bg-blue-50/50 dark:bg-blue-900/20' : ''
                }`}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center text-white text-sm`}>
                        {agent.emoji}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {agent.name}
                          {isAgentToAgent && (
                            <span className="text-xs text-blue-600 dark:text-blue-400 ml-2">
                              → {getAgentInfo(message.to).name}
                            </span>
                          )}
                          {isToUser && !isUserMessage && (
                            <span className="text-xs text-purple-600 dark:text-purple-400 ml-2">
                              → You
                            </span>
                          )}
                        </h3>
                        <p className="text-xs text-gray-500">
                          {formatTimestamp(message.timestamp)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Chip size="sm" variant="flat" className={getMessageTypeColor(message.type)}>
                        {message.type.replace('_', ' ')}
                      </Chip>
                      {isAgentToAgent && (
                        <Chip size="sm" color="primary" variant="flat">
                          Agent Discussion
                        </Chip>
                      )}
                      {message.importance && message.importance !== 'medium' && (
                        <Chip size="sm" color="warning" variant="flat">
                          {message.importance}
                        </Chip>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardBody className="pt-0">
                  {/* Confidence Level */}
                  {message.confidence !== undefined && (
                    <div className="mb-3 flex items-center gap-2">
                      <div className="text-xs text-gray-500">Confidence:</div>
                      <div className="flex items-center gap-1">
                        <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              message.confidence > 0.8 ? 'bg-green-500' :
                              message.confidence > 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${message.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className={`text-xs font-medium ${
                          message.confidence > 0.8 ? 'text-green-400' :
                          message.confidence > 0.6 ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {(message.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      {message.consensus_level && (
                        <Chip size="sm" color={
                          message.consensus_level === 'HIGH' ? 'success' :
                          message.consensus_level === 'MODERATE' ? 'warning' : 'danger'
                        } variant="flat">
                          {message.consensus_level} CONSENSUS
                        </Chip>
                      )}
                    </div>
                  )}

                  {/* Message Content */}
                  <div className="mb-3">
                    <p className={`text-gray-800 dark:text-gray-200 leading-relaxed ${
                      isAgentToAgent ? 'text-blue-900 dark:text-blue-100' : ''
                    }`}>
                      {message.content}
                    </p>
                  </div>

                  {/* Reasoning */}
                  {message.reasoning && (
                    <div className="mb-3 p-2 bg-slate-700/50 rounded border-l-2 border-slate-500">
                      <div className="text-xs text-gray-400 mb-1">Reasoning:</div>
                      <p className="text-xs text-gray-300">{message.reasoning}</p>
                    </div>
                  )}

                  {/* Question with Options */}
                  {message.question && (
                    <div className="mt-3 p-3 bg-blue-900/20 border border-blue-700 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                        <span className="text-sm font-medium text-blue-400">
                          {message.question.question_type === 'confirmation' ? 'Confirmation Request' :
                           message.question.question_type === 'opinion' ? 'Opinion Request' :
                           message.question.question_type === 'decision' ? 'Decision Needed' :
                           'Question'}
                        </span>
                        {message.question.urgency === 'high' && (
                          <Chip size="sm" color="danger" variant="flat">High Priority</Chip>
                        )}
                      </div>
                      <p className="text-blue-200 mb-3">{message.question.question}</p>

                      {message.question.context && (
                        <div className="text-xs text-blue-300/70 mb-3 italic">
                          Context: {message.question.context}
                        </div>
                      )}

                      {message.question.options && (
                        <div className="flex flex-wrap gap-2">
                          {message.question.options.map((option, index) => (
                            <Button
                              key={index}
                              size="sm"
                              variant="flat"
                              color="primary"
                              onPress={() => handleQuestionResponse(message.question!.question_id, option)}
                              className="text-xs"
                            >
                              {option}
                            </Button>
                          ))}
                        </div>
                      )}

                      {!message.question.options && (
                        <div className="text-xs text-blue-300/70">
                          Please respond to this question in the chat input below.
                        </div>
                      )}
                    </div>
                  )}
                </CardBody>
              </Card>
            );
          })}

          {isTyping && (
            <Card className="max-w-4xl bg-slate-800/50 border-slate-700">
              <CardBody className="p-4">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-gray-400 text-sm">Agents are thinking...</span>
                </div>
              </CardBody>
            </Card>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-slate-800 border-t border-slate-700 p-4">
        <div className="max-w-6xl mx-auto">
          {isTyping && (
            <div className="mb-3 p-3 bg-blue-900/20 border border-blue-700 rounded-lg">
              <div className="flex items-center gap-2 text-blue-400">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm">Agents are actively discussing...</span>
              </div>
            </div>
          )}

          {/* Pending Questions */}
          {Object.keys(pendingQuestions).length > 0 && (
            <div className="mb-4 p-3 bg-amber-900/20 border border-amber-700 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-amber-400">
                  Pending Agent Questions ({Object.keys(pendingQuestions).length})
                </span>
              </div>
              <div className="space-y-2">
                {Object.values(pendingQuestions).map((question) => (
                  <div key={question.question_id} className="p-2 bg-amber-900/30 rounded border-l-2 border-amber-500">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-amber-300 font-medium">
                        {getAgentInfo(question.agent_id).name}:
                      </span>
                      <Chip size="sm" color="warning" variant="flat">
                        {question.question_type}
                      </Chip>
                    </div>
                    <p className="text-amber-200 text-sm mt-1">{question.question}</p>
                    {question.options && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {question.options.map((option, index) => (
                          <Button
                            key={index}
                            size="sm"
                            variant="flat"
                            color="warning"
                            onPress={() => handleQuestionResponse(question.question_id, option)}
                            className="text-xs"
                          >
                            {option}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-4">
            <Input
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder={
                isTyping ? "Agents are actively discussing... please wait" :
                currentMode === 'introduction'
                  ? "Please respond to the agent's introduction question..."
                  : "Now you can ask questions and get collaborative agent responses..."
              }
              className="flex-1"
              onKeyPress={(e) => e.key === 'Enter' && !isTyping && handleSendMessage()}
              disabled={isTyping}
            />
            <Button
              color="primary"
              onPress={handleSendMessage}
              disabled={!userInput.trim() || isTyping}
              className="px-8"
            >
              {isTyping ? "Agents Discussing..." : "Send to Agents"}
            </Button>
            {Object.keys(pendingQuestions).length === 0 && (
              <Button
                color="secondary"
                variant="light"
                onPress={manualPoll}
                className="px-4"
                size="sm"
              >
                Check for Messages
              </Button>
            )}
            <Button
              color="danger"
              variant="light"
              onPress={resetChat}
              className="px-4"
              size="sm"
            >
              Reset Chat
            </Button>
          </div>

          <div className="text-xs text-gray-400 mt-2 space-y-1">
            {currentMode === 'introduction' ? (
              <>
                <p>
                  🎭 <strong>Introduction Phase:</strong> Each agent is introducing themselves and asking about your preferences
                </p>
                <p>
                  💬 <strong>Current:</strong> Please respond to the agent's question to continue the introductions
                </p>
                <p>
                  🔄 <strong>Next:</strong> Once all 4 agents have introduced themselves, you'll enter collaborative response mode
                </p>
              </>
            ) : (
              <>
                <p>
                  💡 <strong>Try asking about:</strong> "volatility concerns" • "tech sector outlook" • "risk assessment" • "market conditions"
                </p>
                <p>
                  🎯 <strong>Interactive features:</strong> Answer agent questions • Share opinions • Confirm decisions • Override strategies
                </p>
                <p>
                  🤝 <strong>Agent collaboration:</strong> Confidence levels • Question/response flow • Consensus building • Transparent reasoning
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WarRoom;
