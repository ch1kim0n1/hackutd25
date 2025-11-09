import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Chip } from "@heroui/chip";
import { Spinner } from "@heroui/spinner";
import { ChatBox } from "@/components/ChatBox";
import InfiniteStockList from "@/components/InfiniteStockList";
import { Asset, ChatMessage } from "@/types";
import EnhancedMarketService from "@/services/EnhancedMarketService";
import YahooFinanceService from "@/services/YahooFinanceService";
import { navbar } from "@heroui/theme";

export default function MarketPage() {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [category, setCategory] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("change");

  const categories = ['all', ...EnhancedMarketService.getCategories()];

  // Load assets on mount and when filters change
  useEffect(() => {
    loadInitialAssets();
  }, [category, sortBy]);

  // Handle search with debounce
  useEffect(() => {
    if (!searchQuery.trim()) {
      loadInitialAssets();
      return;
    }

    const timeoutId = setTimeout(() => {
      handleSearch();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const loadInitialAssets = async () => {
    try {
      setInitialLoading(true);
      setAssets([]);
      setCurrentPage(1);
      
      const result = await EnhancedMarketService.getMarketData(1, {
        pageSize: 20,
        category: category as any,
        sortBy: sortBy as any,
        sortOrder: 'desc',
      });

      setAssets(result.assets);
      setHasMore(result.hasMore);
      setCurrentPage(2);
    } catch (error) {
      console.error("Error loading assets:", error);
      setAssets([]);
      setHasMore(false);
    } finally {
      setInitialLoading(false);
    }
  };

  const loadMoreAssets = async () => {
    if (loading || !hasMore) return;

    try {
      setLoading(true);
      
      const result = await EnhancedMarketService.getMarketData(currentPage, {
        pageSize: 20,
        category: category as any,
        sortBy: sortBy as any,
        sortOrder: 'desc',
        searchQuery: searchQuery || undefined,
      });

      setAssets(prev => [...prev, ...result.assets]);
      setHasMore(result.hasMore);
      setCurrentPage(prev => prev + 1);
    } catch (error) {
      console.error("Error loading more assets:", error);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      setInitialLoading(true);
      setAssets([]);
      setHasMore(false);
      
      if (!searchQuery.trim()) {
        await loadInitialAssets();
        return;
      }

      const results = await YahooFinanceService.searchStocks(searchQuery);
      
      // Convert search results to Asset format
      const searchAssets = (await Promise.all(
        results.slice(0, 20).map(async (result: any) => {
          try {
            const quote = await YahooFinanceService.getQuote(result.symbol);
            return {
              symbol: quote.symbol,
              name: quote.shortName || quote.longName || result.symbol,
              price: quote.regularMarketPrice,
              dailyChange: quote.regularMarketChangePercent,
              volume: quote.regularMarketVolume,
              marketCap: quote.marketCap || 0,
            } as Asset;
          } catch (err) {
            return null;
          }
        })
      )).filter((a): a is Asset => a !== null);

      setAssets(searchAssets);
    } catch (error) {
      console.error("Search error:", error);
      setAssets([]);
    } finally {
      setInitialLoading(false);
    }
  };

  // Handle asset click - open chat
  const handleAssetClick = (asset: Asset) => {
    setSelectedAsset(asset);
    setMessages([
      {
        id: Date.now().toString(),
        role: "system",
        content: `You selected ${asset.symbol}. Ask me anything about this stock!`,
        timestamp: new Date(),
      },
    ]);
  };

  const handleNavigateToAsset = (symbol: string) => {
    navigate(`/asset/${symbol}`);
  };

  // Handle chat message
  const handleSendMessage = async (message: string) => {
    if (!selectedAsset) {
      return;
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setSendingMessage(true);

    try {
      // Fetch fresh data
      const quote = await YahooFinanceService.getQuote(selectedAsset.symbol);
      
      const response = generateAIResponse(message, selectedAsset, quote);

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error generating response:", error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error fetching data for this stock. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSendingMessage(false);
    }
  };

  // Simple AI response generator
  const generateAIResponse = (
    question: string,
    asset: Asset,
    quote: any
  ): string => {
    const lowerQuestion = question.toLowerCase();

    if (lowerQuestion.includes("price") || lowerQuestion.includes("cost")) {
      return `${asset.symbol} is currently trading at $${quote.regularMarketPrice.toFixed(2)}. Today's high is $${quote.regularMarketDayHigh.toFixed(2)} and low is $${quote.regularMarketDayLow.toFixed(2)}.`;
    }

    if (lowerQuestion.includes("change") || lowerQuestion.includes("performance")) {
      const changeSign = quote.regularMarketChange >= 0 ? "+" : "";
      return `${asset.symbol} has ${quote.regularMarketChange >= 0 ? "gained" : "lost"} ${changeSign}$${quote.regularMarketChange.toFixed(2)} (${changeSign}${quote.regularMarketChangePercent.toFixed(2)}%) today. Previous close was $${quote.regularMarketPreviousClose.toFixed(2)}.`;
    }

    if (lowerQuestion.includes("volume")) {
      return `Today's trading volume for ${asset.symbol} is ${quote.regularMarketVolume.toLocaleString()} shares.`;
    }

    if (lowerQuestion.includes("buy") || lowerQuestion.includes("invest")) {
      return `${asset.symbol} (${asset.name}) is ${asset.dailyChange >= 0 ? "up" : "down"} ${Math.abs(asset.dailyChange).toFixed(2)}% today. Current price is $${asset.price.toFixed(2)}. Consider reviewing the company's fundamentals and your investment strategy before making a decision.`;
    }

    if (lowerQuestion.includes("high") || lowerQuestion.includes("low")) {
      return `Today's trading range for ${asset.symbol}: High: $${quote.regularMarketDayHigh.toFixed(2)}, Low: $${quote.regularMarketDayLow.toFixed(2)}, Open: $${quote.regularMarketOpen.toFixed(2)}.`;
    }

    // Default response
    return `${asset.symbol} (${asset.name}) is currently at $${asset.price.toFixed(2)}, ${asset.dailyChange >= 0 ? "up" : "down"} ${Math.abs(asset.dailyChange).toFixed(2)}% today. Ask me about its price, performance, volume, or trading range!`;
  };

  const formatPrice = (price: number) => {
    return price >= 1
      ? price.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : price.toFixed(6);
  };

  const formatChange = (change: number) => {
    const sign = change >= 0 ? "+" : "";
    return `${sign}${change.toFixed(2)}%`;
  };

  return (
    <div className="container mx-auto px-4 py-6 h-[calc(100vh-64px)]">
      <div className="flex flex-col h-full gap-4">
        {/* Header */}
        <div className="flex-shrink-0">
          <h1 className="text-3xl font-bold mb-2">Market</h1>
          <p className="text-default-500">
            Browse tradable assets with real-time data from Yahoo Finance
          </p>
        </div>

        {/* Filters */}
        <div className="flex-shrink-0 flex gap-4 items-center">
          <Input
            placeholder="Search stocks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            startContent={
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
                className="w-5 h-5 text-default-400"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                />
              </svg>
            }
            isClearable
            onClear={() => setSearchQuery("")}
            className="flex-1"
          />
          
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={category === "all" ? "solid" : "flat"}
              color="primary"
              onPress={() => setCategory("all")}
            >
              All
            </Button>
            <Button
              size="sm"
              variant={category === "tech" ? "solid" : "flat"}
              color="primary"
              onPress={() => setCategory("tech")}
            >
              Tech
            </Button>
            <Button
              size="sm"
              variant={category === "crypto" ? "solid" : "flat"}
              color="primary"
              onPress={() => setCategory("crypto")}
            >
              Crypto
            </Button>
          </div>

          <div className="flex gap-2">
            <Chip size="sm" variant="flat">
              Sort by:
            </Chip>
            <Button
              size="sm"
              variant={sortBy === "change" ? "solid" : "flat"}
              color="secondary"
              onPress={() => setSortBy("change")}
            >
              % Change
            </Button>
            <Button
              size="sm"
              variant={sortBy === "price" ? "solid" : "flat"}
              color="secondary"
              onPress={() => setSortBy("price")}
            >
              Price
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="flex-shrink-0">
          <Chip size="sm" variant="flat" color="primary">
            {assets.length} Assets Loaded
          </Chip>
        </div>

        {/* Main Content - Horizontal Layout */}
        <div className="flex-1 flex gap-4 min-h-0">
          {/* Left Side - Stock List (2/3) */}
          <div className="flex-[2] flex flex-col min-w-0">
            {initialLoading ? (
              <Card className="flex-1 flex items-center justify-center">
                <CardBody>
                  <div className="flex flex-col items-center gap-4">
                    <Spinner size="lg" />
                    <p className="text-default-500">Loading market data...</p>
                  </div>
                </CardBody>
              </Card>
            ) : (
              <InfiniteStockList
                assets={assets}
                loading={loading}
                hasMore={hasMore}
                onLoadMore={loadMoreAssets}
                onAssetClick={(asset) => {
                  navigate(`/asset/${asset.symbol}`);
                }}
              />
            )}
          </div>

          {/* Right Side - Chat Box (1/3) */}
          <div className="flex-[1] flex flex-col min-w-0">
            <Card className="flex-1 flex flex-col">
              <CardHeader className="flex-shrink-0 pb-3">
                <div className="flex flex-col gap-2 w-full">
                  <h2 className="text-xl font-bold">AI Assistant</h2>
                  {selectedAsset ? (
                    <div className="flex items-center gap-2">
                      <Chip
                        variant="flat"
                        color="secondary"
                        size="sm"
                        classNames={{
                          base: "font-mono font-bold",
                        }}
                      >
                        {selectedAsset.symbol}
                      </Chip>
                      <span className="text-sm text-default-500 truncate">
                        {selectedAsset.name}
                      </span>
                    </div>
                  ) : (
                    <p className="text-sm text-default-500">
                      Select a stock to start chatting
                    </p>
                  )}
                </div>
              </CardHeader>

              <CardBody className="flex-1 overflow-hidden p-0">
                <div className="h-full">
                  <ChatBox
                    messages={messages}
                    onSend={handleSendMessage}
                    placeholder={
                      selectedAsset
                        ? `Ask about ${selectedAsset.symbol}...`
                        : "Select a stock first..."
                    }
                    disabled={!selectedAsset || sendingMessage}
                    className="h-full"
                  />
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
