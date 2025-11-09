import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Card, CardBody, CardFooter } from "@heroui/card";
import { Button } from "@heroui/button";
import { Textarea } from "@heroui/input";
import clsx from "clsx";

import { ChatMessage } from "@/types";
import { Response } from "@/components/ui/shadcn-io/ai/response";

interface ChatBoxProps {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  width?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export const ChatBox = ({
  messages,
  onSend,
  width = "100%",
  placeholder = "Type your message...",
  disabled = false,
  className = "",
}: ChatBoxProps) => {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (date?: Date) => {
    if (!date) return "";

    return new Intl.DateTimeFormat("en-US", {
      hour: "numeric",
      minute: "2-digit",
    }).format(date);
  };

  return (
    <div className={`${className}`}>
      <Card className="shadow-lg h-full flex flex-col" style={{ width }}>
        {/* Messages display area */}
        <CardBody className="p-4 flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full min-h-[200px]">
              <p className="text-default-400 text-sm">
                No messages yet. Start the conversation!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={clsx(
                    "flex flex-col gap-1",
                    message.role === "user" ? "items-end" : "items-start",
                  )}
                >
                  {/* Message bubble */}
                  <div
                    className={clsx(
                      "px-4 py-2 rounded-2xl max-w-[80%]",
                      message.role === "user"
                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                        : message.role === "assistant"
                          ? "bg-content2 text-foreground rounded-tl-sm"
                          : "bg-warning-100 text-warning-900 rounded-sm",
                    )}
                  >
                    <Response className="text-sm whitespace-pre-wrap break-words">
                      {message.content}
                    </Response>
                  </div>

                  {/* Timestamp */}
                  {message.timestamp && (
                    <span className="text-xs text-default-400 px-2">
                      {formatTime(message.timestamp)}
                    </span>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </CardBody>

        {/* Input area */}
        <CardFooter className="p-4 border-t border-divider">
          <div className="flex gap-2 w-full">
            <Textarea
              classNames={{
                base: "flex-1",
                input: "resize-none",
              }}
              disabled={disabled}
              maxRows={6}
              minRows={1}
              placeholder={placeholder}
              value={input}
              variant="bordered"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <Button
              isIconOnly
              className="self-end"
              color="primary"
              isDisabled={!input.trim() || disabled}
              size="lg"
              variant="shadow"
              onPress={handleSend}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ChatBox;
