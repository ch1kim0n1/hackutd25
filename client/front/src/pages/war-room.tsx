import { useState, useEffect, useRef } from "react";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Chip } from "@heroui/chip";

interface AgentMessage {
  id: string;
  from_agent: string;
  to_agent: string;
  message: string;
  timestamp: string;
  message_type: string;
  importance: string;
  metadata?: any;
  thread_id?: string;
  parent_message_id?: string;
  tags?: string[];
}

const AGENTS = [
  { id: "market", name: "Market Agent", emoji: "🔍", color: "bg-blue-500" },
  { id: "strategy", name: "Strategy Agent", emoji: "🧠", color: "bg-purple-500" },
  { id: "risk", name: "Risk Agent", emoji: "⚠️", color: "bg-red-500" },
  { id: "executor", name: "Executor Agent", emoji: "⚡", color: "bg-green-500" },
  { id: "explainer", name: "Explainer Agent", emoji: "💬", color: "bg-yellow-500" },
  { id: "user", name: "You", emoji: "👤", color: "bg-gray-500" }
];

const WarRoom = () => {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [userInput, setUserInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Simulate initial conversation
  useEffect(() => {
    const initialMessages: AgentMessage[] = [
      {
        id: "1",
        from_agent: "market",
        to_agent: "all",
        message: "Market analysis complete. VIX at 18.2, down 0.8% today. S&P 500 showing bullish momentum with tech leading.",
        timestamp: new Date(Date.now() - 300000).toISOString(),
        message_type: "analysis",
        importance: "medium"
      },
      {
        id: "2",
        from_agent: "strategy",
        to_agent: "all",
        message: "Current portfolio allocation: 60% equities, 30% bonds, 10% cash. Risk-adjusted return target: 8-10% annually.",
        timestamp: new Date(Date.now() - 240000).toISOString(),
        message_type: "strategy",
        importance: "high"
      },
      {
        id: "3",
        from_agent: "risk",
        to_agent: "strategy",
        message: "Portfolio volatility at 12.4%, within acceptable range. Stress test shows 15% max drawdown in worst case.",
        timestamp: new Date(Date.now() - 180000).toISOString(),
        message_type: "risk_assessment",
        importance: "medium"
      },
      {
        id: "4",
        from_agent: "explainer",
        to_agent: "user",
        message: "Welcome to APEX! I'm here to help explain what's happening. The agents are analyzing market conditions and your portfolio. You can ask questions or provide input at any time.",
        timestamp: new Date(Date.now() - 120000).toISOString(),
        message_type: "welcome",
        importance: "low"
      }
    ];

    // Add messages with delay to simulate real-time
    let index = 0;
    const interval = setInterval(() => {
      if (index < initialMessages.length) {
        setMessages(prev => [...prev, initialMessages[index]]);
        index++;
      } else {
        clearInterval(interval);
        setIsConnected(true);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

  const handleSendMessage = () => {
    if (!userInput.trim()) return;

    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      from_agent: "user",
      to_agent: "all",
      message: userInput,
      timestamp: new Date().toISOString(),
      message_type: "user_input",
      importance: "high"
    };

    setMessages(prev => [...prev, userMessage]);
    setUserInput("");
    setIsTyping(true);

    // Simulate agent responses
    setTimeout(() => {
      const responses = [
        {
          from_agent: "explainer",
          message: `Thanks for your input! "${userInput}" is a great point. Let me break this down for you...`,
          type: "explanation",
          importance: "medium"
        },
        {
          from_agent: "strategy",
          message: "Considering user feedback... Adjusting strategy parameters accordingly.",
          type: "strategy",
          importance: "high"
        },
        {
          from_agent: "risk",
          message: "Re-evaluating risk parameters based on user input.",
          type: "risk_assessment",
          importance: "medium"
        }
      ];

      responses.forEach((response, index) => {
        setTimeout(() => {
          const agentMessage: AgentMessage = {
            id: (Date.now() + index + 1).toString(),
            from_agent: response.from_agent,
            to_agent: "all",
            message: response.message,
            timestamp: new Date().toISOString(),
            message_type: response.type,
            importance: response.importance
          };
          setMessages(prev => [...prev, agentMessage]);
        }, (index + 1) * 2000);
      });

      setIsTyping(false);
    }, 2000);
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
            <h1 className="text-2xl font-bold text-white">APEX War Room</h1>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
              <span className="text-sm text-gray-300">
                {isConnected ? 'Live Session' : 'Connecting...'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Agent Status */}
            <div className="flex gap-2">
              {AGENTS.slice(0, 5).map(agent => (
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
            const agent = getAgentInfo(message.from_agent);
            return (
              <Card
                key={message.id}
                className={`max-w-4xl ${message.from_agent === 'user' ? 'ml-auto' : ''} ${getImportanceColor(message.importance)}`}
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
                        </h3>
                        <p className="text-xs text-gray-500">
                          {formatTimestamp(message.timestamp)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Chip size="sm" variant="flat" className={getMessageTypeColor(message.message_type)}>
                        {message.message_type.replace('_', ' ')}
                      </Chip>
                      {message.importance !== 'low' && (
                        <Chip size="sm" color="warning" variant="flat">
                          {message.importance}
                        </Chip>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardBody className="pt-0">
                  <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                    {message.message}
                  </p>
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
          <div className="flex gap-4">
            <Input
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Type your thoughts, questions, or override instructions..."
              className="flex-1"
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            <Button
              color="primary"
              onPress={handleSendMessage}
              disabled={!userInput.trim() || isTyping}
              className="px-8"
            >
              Send to Agents
            </Button>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            💡 Try saying things like: "I'm concerned about volatility" or "Let's be more conservative" or "I want to invest in tech stocks"
          </p>
        </div>
      </div>
    </div>
  );
};

export default WarRoom;
