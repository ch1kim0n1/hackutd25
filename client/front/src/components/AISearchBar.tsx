import { Input } from "@heroui/input";
import { Button } from "@heroui/button";
import { Card, CardBody } from "@heroui/card";
import React, { useState } from "react";

interface AISearchBarProps {
  onSearch: (query: string) => void;
  isSearching?: boolean;
  placeholder?: string;
  className?: string;
}

export const AISearchBar: React.FC<AISearchBarProps> = ({
  onSearch,
  isSearching = false,
  placeholder = "Ask AI to find stocks, analyze trends, or get insights...",
  className = "",
}) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query);
      setQuery("");
      setSuggestions([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleInputChange = (value: string) => {
    setQuery(value);

    // Mock AI suggestions - in real app, this would call an AI service
    if (value.length > 2) {
      const mockSuggestions = [
        "Find stocks with high growth potential",
        "Show me undervalued tech stocks",
        "Analyze my portfolio risk",
        "What stocks are trending today?",
        "Find dividend stocks with >3% yield",
      ].filter((s) => s.toLowerCase().includes(value.toLowerCase()));

      setSuggestions(mockSuggestions.slice(0, 3));
    } else {
      setSuggestions([]);
    }
  };

  return (
    <div className={`relative w-full ${className}`}>
      <div className="flex gap-2 items-center">
        <Input
          classNames={{
            input: "text-base",
            inputWrapper:
              "border-default-200 hover:border-primary focus-within:border-primary data-[hover=true]:border-primary",
          }}
          endContent={
            isSearching && (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
            )
          }
          placeholder={placeholder}
          size="lg"
          startContent={
            <svg
              className="w-5 h-5 text-default-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
              />
            </svg>
          }
          value={query}
          variant="bordered"
          onKeyDown={handleKeyDown}
          onValueChange={handleInputChange}
        />
        <Button
          className="px-6 font-semibold"
          color="primary"
          isDisabled={!query.trim()}
          isLoading={isSearching}
          size="lg"
          variant="shadow"
          onPress={handleSearch}
        >
          Search
        </Button>
      </div>

      {/* AI Suggestions Dropdown */}
      {suggestions.length > 0 && (
        <Card className="absolute top-full left-0 right-16 mt-2 z-50 shadow-xl">
          <CardBody className="p-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="w-full text-left px-4 py-3 rounded-lg hover:bg-default-100 transition-colors"
                onClick={() => {
                  setQuery(suggestion);
                  setSuggestions([]);
                }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-primary text-sm font-medium">AI:</span>
                  <span className="text-sm text-default-700">{suggestion}</span>
                </div>
              </button>
            ))}
          </CardBody>
        </Card>
      )}
    </div>
  );
};
