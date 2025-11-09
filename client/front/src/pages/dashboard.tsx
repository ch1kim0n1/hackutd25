import { useState } from "react";
import { Button } from "@heroui/button";

import { StockList } from "@/components/StockList";
import { ChatBox } from "@/components/ChatBox";
import { AISearchBar } from "@/components/AISearchBar";
import { LoadingAI } from "@/components/LoadingAI";
import { Asset, ChatMessage } from "@/types";
import { aiService } from "@/services/AIService";

interface AIMessage {
  aiId: number;
  message: string;
  timestamp: number;
}

export default function Dashboard() {
  // Sample data
  const [assets] = useState<Asset[]>([
    { symbol: "BTC", name: "Bitcoin", price: 67234.5, dailyChange: 2.45 },
    { symbol: "ETH", name: "Ethereum", price: 3456.78, dailyChange: -1.23 },
    { symbol: "AAPL", name: "Apple Inc.", price: 178.23, dailyChange: 0.89 },
    {
      symbol: "GOOGL",
      name: "Alphabet Inc.",
      price: 141.52,
      dailyChange: 1.34,
    },
    {
      symbol: "MSFT",
      name: "Microsoft Corp",
      price: 378.91,
      dailyChange: -0.56,
    },
    { symbol: "TSLA", name: "Tesla Inc.", price: 242.84, dailyChange: 3.21 },
    { symbol: "NVDA", name: "NVIDIA Corp", price: 498.75, dailyChange: 5.67 },
    {
      symbol: "AMD",
      name: "Advanced Micro Devices",
      price: 123.45,
      dailyChange: 2.13,
    },
    {
      symbol: "AMZN",
      name: "Amazon.com Inc.",
      price: 145.67,
      dailyChange: -0.98,
    },
    {
      symbol: "META",
      name: "Meta Platforms",
      price: 334.21,
      dailyChange: 1.76,
    },
  ]);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your AI trading assistant. I can help you analyze stocks, find opportunities, and manage your portfolio. Try asking me to analyze specific stocks or search for investment opportunities!",
      timestamp: new Date(),
    },
  ]);

  const [highlightedSymbols, setHighlightedSymbols] = useState<string[]>([]);
  const [scrollToSymbol, setScrollToSymbol] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [aiMessages, setAiMessages] = useState<AIMessage[]>([]);

  const handleSearch = async (query: string) => {
    setIsSearching(true);

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    // Simulate AI response with stock highlighting
    setTimeout(() => {
      let aiResponse = "";
      let highlightedStocks: string[] = [];

      // Simple mock logic - in real app, this would call your AI service
      if (
        query.toLowerCase().includes("nvidia") ||
        query.toLowerCase().includes("nvda")
      ) {
        aiResponse =
          "I've highlighted NVIDIA (NVDA) for you. It shows strong growth with +5.67% today. The stock has been performing exceptionally well due to AI chip demand.";
        highlightedStocks = ["NVDA"];
      } else if (query.toLowerCase().includes("tech")) {
        aiResponse =
          "I've found several tech stocks worth reviewing: NVDA is up 5.67%, AAPL up 0.89%, and GOOGL up 1.34%. I recommend taking a closer look at NVIDIA and Apple.";
        highlightedStocks = ["NVDA", "AAPL"];
      } else if (
        query.toLowerCase().includes("bitcoin") ||
        query.toLowerCase().includes("btc")
      ) {
        aiResponse =
          "Bitcoin (BTC) is currently at $67,234.50, up 2.45% today. The crypto market is showing positive momentum.";
        highlightedStocks = ["BTC"];
      } else {
        aiResponse = `I've analyzed your query: "${query}". Based on current market conditions, I recommend reviewing NVDA and TSLA which are showing strong performance today.`;
        highlightedStocks = ["NVDA", "TSLA"];
      }

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: aiResponse,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);

      if (highlightedStocks.length > 0) {
        setHighlightedSymbols(highlightedStocks);
        setScrollToSymbol(highlightedStocks[0]);
      }

      setIsSearching(false);
    }, 1500);
  };

  const handleAnalyze = async () => {
    if (!aiService.isConfigured()) {
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "assistant",
        content:
          "⚠️ OpenAI API key not configured. Please add VITE_OPENAI_API_KEY to your .env file to enable AI analysis.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);

      return;
    }

    setIsAnalyzing(true);
    setAiMessages([]); // Clear previous AI messages

    // Add system message
    const systemMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "system",
      content: "🤖 AI Analysis in progress...",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, systemMessage]);

    // Simulate AI communication logs
    const communicationInterval = setInterval(() => {
      const aiId = Math.floor(Math.random() * 5) + 1;
      const messages = [
        "Analyzing market trends...",
        "Evaluating risk factors...",
        "Computing portfolio metrics...",
        "Reviewing historical data...",
        "Generating recommendations...",
        "Assessing diversification...",
        "Checking sector allocation...",
        "Analyzing price momentum...",
      ];

      const newMessage: AIMessage = {
        aiId,
        message: messages[Math.floor(Math.random() * messages.length)],
        timestamp: Date.now(),
      };

      setAiMessages((prev) => [...prev, newMessage]);
    }, 800);

    try {
      // Prepare portfolio data for AI analysis
      const portfolioData = {
        assets: assets.map((asset) => ({
          symbol: asset.symbol,
          name: asset.name,
          price: asset.price,
          dailyChange: asset.dailyChange,
        })),
        totalValue: assets.reduce((sum, asset) => sum + asset.price, 0),
      };

      // Call AI service for analysis
      const analysis = await aiService.analyzePortfolio(portfolioData);

      clearInterval(communicationInterval);

      // Add final AI communication
      setAiMessages((prev) => [
        ...prev,
        {
          aiId: 1,
          message: "Analysis complete! Generating report...",
          timestamp: Date.now(),
        },
      ]);

      // Wait a moment before showing results
      setTimeout(() => {
        const analysisMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: analysis.analysis,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, analysisMessage]);

        // Highlight recommended assets
        const highlightSymbols = analysis.suggestedActions
          .filter(
            (action) => action.action === "buy" || action.action === "sell",
          )
          .map((action) => action.symbol)
          .slice(0, 3);

        if (highlightSymbols.length > 0) {
          setHighlightedSymbols(highlightSymbols);
          setScrollToSymbol(highlightSymbols[0]);
        }

        setIsAnalyzing(false);
      }, 1000);
    } catch (error) {
      clearInterval(communicationInterval);
      console.error("AI Analysis Error:", error);

      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "❌ Analysis failed. Please check your OpenAI API key configuration and try again.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      setIsAnalyzing(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!aiService.isConfigured()) {
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "assistant",
        content:
          "⚠️ OpenAI API key not configured. Please add VITE_OPENAI_API_KEY to your .env file.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);

      return;
    }

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      // Prepare context for AI
      const context = {
        conversationHistory: messages.slice(-6).map((msg) => ({
          role: msg.role as "user" | "assistant",
          content: msg.content,
        })),
        portfolio: {
          assets: assets.map((asset) => ({
            symbol: asset.symbol,
            name: asset.name,
            price: asset.price,
            dailyChange: asset.dailyChange,
          })),
        },
      };

      // Get AI response
      const response = await aiService.getChatResponse(content, context);

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);

      // Check if response mentions specific stocks to highlight
      const mentionedSymbols = assets
        .filter(
          (asset) =>
            response.toLowerCase().includes(asset.symbol.toLowerCase()) ||
            response.toLowerCase().includes(asset.name.toLowerCase()),
        )
        .map((asset) => asset.symbol)
        .slice(0, 3);

      if (mentionedSymbols.length > 0) {
        setHighlightedSymbols(mentionedSymbols);
        setScrollToSymbol(mentionedSymbols[0]);
      }
    } catch (error) {
      console.error("Chat Error:", error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I encountered an error. Please try again.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleHighlightDismiss = () => {
    setHighlightedSymbols([]);
    setScrollToSymbol(null);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Main Content */}
      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Search Bar and Analyze Button */}
        <div className="flex gap-4 items-center">
          <div className="flex-1">
            <AISearchBar isSearching={isSearching} onSearch={handleSearch} />
          </div>
          <Button
            className="font-semibold px-8"
            color="primary"
            isLoading={isAnalyzing}
            size="lg"
            startContent={
              !isAnalyzing ? (
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : undefined
            }
            variant="shadow"
            onPress={handleAnalyze}
          >
            {isAnalyzing ? "Analyzing..." : "Analyze Portfolio"}
          </Button>
        </div>

        {/* AI Loading Component - Show when analyzing */}
        {isAnalyzing && (
          <div className="animate-in fade-in slide-in-from-top-4 duration-500">
            <LoadingAI messages={aiMessages} showLogs={true} />
          </div>
        )}

        {/* Dashboard Grid - Stock List and Chat Box */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Stock List - Left Side */}
          <div className="h-[calc(100vh-280px)]">
            <StockList
              assets={assets}
              highlightedSymbols={highlightedSymbols}
              scrollToSymbol={scrollToSymbol}
              onAssetClick={(asset) => {
                // Add message about clicked asset
                const assetMessage: ChatMessage = {
                  id: Date.now().toString(),
                  role: "user",
                  content: `Tell me more about ${asset.name} (${asset.symbol})`,
                  timestamp: new Date(),
                };

                setMessages((prev) => [...prev, assetMessage]);

                // Simulate AI response
                setTimeout(() => {
                  const response: ChatMessage = {
                    id: (Date.now() + 1).toString(),
                    role: "assistant",
                    content: `${asset.name} (${asset.symbol}) is currently trading at $${asset.price.toFixed(2)} with a ${asset.dailyChange >= 0 ? "gain" : "loss"} of ${Math.abs(asset.dailyChange)}% today. Would you like me to provide a detailed analysis?`,
                    timestamp: new Date(),
                  };

                  setMessages((prev) => [...prev, response]);
                }, 800);
              }}
              onHighlightDismiss={handleHighlightDismiss}
            />
          </div>

          {/* Chat Box - Right Side */}
          <div className="h-[calc(100vh-280px)]">
            <ChatBox
              className="h-full"
              messages={messages}
              onSend={handleSendMessage}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
