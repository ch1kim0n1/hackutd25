import { useState, useEffect } from "react";
import { Card, CardBody } from "@heroui/card";

import { cn } from "@/lib/utils";

interface AIMessage {
  aiId: number;
  message: string;
  timestamp: number;
}

interface LoadingAIProps {
  messages?: AIMessage[];
  width?: string;
  showLogs?: boolean;
}

export const LoadingAI = ({
  messages = [],
  width = "100%",
  showLogs = true,
}: LoadingAIProps) => {
  const [activeAI, setActiveAI] = useState<number>(0);
  const [activeConnection, setActiveConnection] = useState<
    [number, number] | null
  >(null);
  const [displayedMessages, setDisplayedMessages] = useState<AIMessage[]>([]);

  // AI positions in a pentagon formation
  const aiPositions = [
    { x: 150, y: 30, label: "AI 1" }, // Top
    { x: 260, y: 110, label: "AI 2" }, // Top right
    { x: 220, y: 220, label: "AI 3" }, // Bottom right
    { x: 80, y: 220, label: "AI 4" }, // Bottom left
    { x: 40, y: 110, label: "AI 5" }, // Top left
  ];

  // All connections between AIs (complete graph)
  const connections = [
    [0, 1],
    [0, 2],
    [0, 3],
    [0, 4],
    [1, 2],
    [1, 3],
    [1, 4],
    [2, 3],
    [2, 4],
    [3, 4],
  ];

  // Animate through AIs and connections
  useEffect(() => {
    const aiInterval = setInterval(() => {
      setActiveAI((prev) => (prev + 1) % 5);
    }, 1500);

    const connectionInterval = setInterval(() => {
      const randomConnection =
        connections[Math.floor(Math.random() * connections.length)];

      setActiveConnection(randomConnection as [number, number]);
      setTimeout(() => setActiveConnection(null), 800);
    }, 1000);

    return () => {
      clearInterval(aiInterval);
      clearInterval(connectionInterval);
    };
  }, []);

  // Update displayed messages
  useEffect(() => {
    if (messages.length > 0) {
      setDisplayedMessages(messages);
    }
  }, [messages]);

  const isConnectionActive = (start: number, end: number) => {
    if (!activeConnection) return false;

    return (
      (activeConnection[0] === start && activeConnection[1] === end) ||
      (activeConnection[0] === end && activeConnection[1] === start)
    );
  };

  return (
    <div className="bg-background p-6 rounded-xl" style={{ width }}>
      <Card className="shadow-lg border border-divider">
        <CardBody className="p-6">
          <div className="flex flex-col gap-6">
            {/* SVG Visualization */}
            <div className="flex justify-center">
              <svg className="overflow-visible" height="260" width="300">
                {/* Draw all connection lines */}
                {connections.map(([start, end], idx) => {
                  const startPos = aiPositions[start];
                  const endPos = aiPositions[end];
                  const isActive = isConnectionActive(start, end);

                  return (
                    <g key={`connection-${idx}`}>
                      <line
                        className="transition-all duration-300"
                        opacity={isActive ? "1" : "0.3"}
                        stroke={isActive ? "#7c3aed" : "#334155"}
                        strokeWidth={isActive ? "3" : "1"}
                        x1={startPos.x}
                        x2={endPos.x}
                        y1={startPos.y}
                        y2={endPos.y}
                      />
                      {isActive && (
                        <>
                          {/* Animated pulse effect */}
                          <circle fill="#7c3aed" opacity="0.6" r="4">
                            <animateMotion
                              dur="0.8s"
                              path={`M ${startPos.x},${startPos.y} L ${endPos.x},${endPos.y}`}
                              repeatCount="1"
                            />
                          </circle>
                        </>
                      )}
                    </g>
                  );
                })}

                {/* Draw AI nodes */}
                {aiPositions.map((pos, idx) => {
                  const isActive = activeAI === idx;
                  const hasMessage = displayedMessages.some(
                    (m) => m.aiId === idx + 1,
                  );

                  return (
                    <g key={`ai-${idx}`}>
                      {/* Outer glow ring when active */}
                      {isActive && (
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          fill="none"
                          opacity="0.4"
                          r="20"
                          stroke="#7c3aed"
                          strokeWidth="2"
                        >
                          <animate
                            attributeName="r"
                            dur="1.5s"
                            from="12"
                            repeatCount="indefinite"
                            to="24"
                          />
                          <animate
                            attributeName="opacity"
                            dur="1.5s"
                            from="0.6"
                            repeatCount="indefinite"
                            to="0"
                          />
                        </circle>
                      )}

                      {/* Main AI node */}
                      <circle
                        className="transition-all duration-300"
                        cx={pos.x}
                        cy={pos.y}
                        fill={
                          isActive
                            ? "#7c3aed"
                            : hasMessage
                              ? "#22c55e"
                              : "#475569"
                        }
                        r={isActive ? "12" : "10"}
                      />

                      {/* AI label */}
                      <text
                        className="text-xs font-mono fill-slate-400"
                        textAnchor="middle"
                        x={pos.x}
                        y={pos.y + 30}
                      >
                        {pos.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Message logs */}
            {showLogs && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-foreground">
                  AI Communication Logs
                </h3>
                <div className="max-h-48 overflow-y-auto space-y-2 bg-default-50 dark:bg-default-100 rounded-lg p-3">
                  {displayedMessages.length === 0 ? (
                    <p className="text-xs text-default-400 text-center py-4">
                      Waiting for AI communications...
                    </p>
                  ) : (
                    displayedMessages
                      .slice(-10)
                      .reverse()
                      .map((msg, idx) => (
                        <div
                          key={`msg-${msg.timestamp}-${idx}`}
                          className="text-xs space-y-1 p-2 bg-background rounded border border-divider animate-in fade-in slide-in-from-bottom-2 duration-300"
                        >
                          <div className="flex items-center gap-2">
                            <span
                              className={cn(
                                "w-2 h-2 rounded-full",
                                msg.aiId === 1 && "bg-violet-500",
                                msg.aiId === 2 && "bg-primary",
                                msg.aiId === 3 && "bg-green-500",
                                msg.aiId === 4 && "bg-yellow-500",
                                msg.aiId === 5 && "bg-pink-500",
                              )}
                            />
                            <span className="font-mono font-semibold text-primary">
                              AI {msg.aiId}
                            </span>
                            <span className="text-default-400">
                              {new Date(msg.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="text-default-700 dark:text-default-300 pl-4">
                            {msg.message}
                          </p>
                        </div>
                      ))
                  )}
                </div>
              </div>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default LoadingAI;
