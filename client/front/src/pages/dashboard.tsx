import { useState } from "react";
import { StockList } from "@/components/StockList";
import { ChatBox } from "@/components/ChatBox";
import { AISearchBar } from "@/components/AISearchBar";
import { AnalyzeButton } from "@/components/AnalyzeButton";
import { Asset, ChatMessage } from "@/types";

export default function Dashboard() {
  // Sample data
  const [assets] = useState<Asset[]>([
    { symbol: "BTC", name: "Bitcoin", price: 67234.50, dailyChange: 2.45 },
    { symbol: "ETH", name: "Ethereum", price: 3456.78, dailyChange: -1.23 },
    { symbol: "AAPL", name: "Apple Inc.", price: 178.23, dailyChange: 0.89 },
    { symbol: "GOOGL", name: "Alphabet Inc.", price: 141.52, dailyChange: 1.34 },
    { symbol: "MSFT", name: "Microsoft Corp", price: 378.91, dailyChange: -0.56 },
    { symbol: "TSLA", name: "Tesla Inc.", price: 242.84, dailyChange: 3.21 },
    { symbol: "NVDA", name: "NVIDIA Corp", price: 498.75, dailyChange: 5.67 },
    { symbol: "AMD", name: "Advanced Micro Devices", price: 123.45, dailyChange: 2.13 },
    { symbol: "AMZN", name: "Amazon.com Inc.", price: 145.67, dailyChange: -0.98 },
    { symbol: "META", name: "Meta Platforms", price: 334.21, dailyChange: 1.76 },
  ]);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm your AI trading assistant. I can help you analyze stocks, find opportunities, and manage your portfolio. Try asking me to analyze specific stocks or search for investment opportunities!",
      timestamp: new Date(),
    },
  ]);

  const [highlightedSymbols, setHighlightedSymbols] = useState<string[]>([]);
  const [scrollToSymbol, setScrollToSymbol] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleSearch = async (query: string) => {
    setIsSearching(true);
    
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Simulate AI response with stock highlighting
    setTimeout(() => {
      let aiResponse = "";
      let highlightedStocks: string[] = [];

      // Simple mock logic - in real app, this would call your AI service
      if (query.toLowerCase().includes("nvidia") || query.toLowerCase().includes("nvda")) {
        aiResponse = "I've highlighted NVIDIA (NVDA) for you. It shows strong growth with +5.67% today. The stock has been performing exceptionally well due to AI chip demand.";
        highlightedStocks = ["NVDA"];
      } else if (query.toLowerCase().includes("tech")) {
        aiResponse = "I've found several tech stocks worth reviewing: NVDA is up 5.67%, AAPL up 0.89%, and GOOGL up 1.34%. I recommend taking a closer look at NVIDIA and Apple.";
        highlightedStocks = ["NVDA", "AAPL"];
      } else if (query.toLowerCase().includes("bitcoin") || query.toLowerCase().includes("btc")) {
        aiResponse = "Bitcoin (BTC) is currently at $67,234.50, up 2.45% today. The crypto market is showing positive momentum.";
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
      
      setMessages(prev => [...prev, aiMessage]);
      
      if (highlightedStocks.length > 0) {
        setHighlightedSymbols(highlightedStocks);
        setScrollToSymbol(highlightedStocks[0]);
      }
      
      setIsSearching(false);
    }, 1500);
  };

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    
    // Add system message
    const systemMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "system",
      content: "AI Analysis in progress...",
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, systemMessage]);

    // Simulate AI analysis
    setTimeout(() => {
      const analysisMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `**Portfolio Analysis Complete**\n\n**Key Findings:**\n• Your portfolio is well-diversified across crypto and tech stocks\n• Top performers: NVDA (+5.67%), TSLA (+3.21%), BTC (+2.45%)\n• Minor losses: ETH (-1.23%), MSFT (-0.56%), AMZN (-0.98%)\n• Overall portfolio change: +2.34%\n\n**Recommendations:**\n• Consider increasing exposure to AI/semiconductor stocks (NVDA, AMD)\n• TSLA showing strong momentum - potential buying opportunity\n• ETH experiencing a dip - could be a good entry point for long-term holders\n\nWould you like me to dive deeper into any specific asset?`,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, analysisMessage]);
      setHighlightedSymbols(["NVDA", "TSLA", "ETH"]);
      setScrollToSymbol("NVDA");
      setIsAnalyzing(false);
    }, 3000);
  };

  const handleSendMessage = (content: string) => {
    handleSearch(content);
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
            <AISearchBar 
              onSearch={handleSearch}
              isSearching={isSearching}
            />
          </div>
          <AnalyzeButton 
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />
        </div>

        {/* Dashboard Grid - Stock List and Chat Box */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Stock List - Left Side */}
          <div className="h-[calc(100vh-280px)]">
            <StockList
              assets={assets}
              highlightedSymbols={highlightedSymbols}
              scrollToSymbol={scrollToSymbol}
              onHighlightDismiss={handleHighlightDismiss}
              onAssetClick={(asset) => {
                // Add message about clicked asset
                const assetMessage: ChatMessage = {
                  id: Date.now().toString(),
                  role: "user",
                  content: `Tell me more about ${asset.name} (${asset.symbol})`,
                  timestamp: new Date(),
                };
                setMessages(prev => [...prev, assetMessage]);

                // Simulate AI response
                setTimeout(() => {
                  const response: ChatMessage = {
                    id: (Date.now() + 1).toString(),
                    role: "assistant",
                    content: `${asset.name} (${asset.symbol}) is currently trading at $${asset.price.toFixed(2)} with a ${asset.dailyChange >= 0 ? 'gain' : 'loss'} of ${Math.abs(asset.dailyChange)}% today. Would you like me to provide a detailed analysis?`,
                    timestamp: new Date(),
                  };
                  setMessages(prev => [...prev, response]);
                }, 800);
              }}
            />
          </div>

          {/* Chat Box - Right Side */}
          <div className="h-[calc(100vh-280px)]">
            <ChatBox
              messages={messages}
              onSend={handleSendMessage}
              className="h-full"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
