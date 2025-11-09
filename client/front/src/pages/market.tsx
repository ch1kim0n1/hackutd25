import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Chip } from "@heroui/chip";
import { Spinner } from "@heroui/spinner";

import { ChatBox } from "@/components/ChatBox";
import { Asset, ChatMessage } from "@/types";
import { AssetService } from "@/services/AssetService";
import { MarketDataService } from "@/services/MarketDataService";

const ITEMS_PER_PAGE = 20;

export default function MarketPage() {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [filteredAssets, setFilteredAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sendingMessage, setSendingMessage] = useState(false);

  // Services
  const assetService = new AssetService();
  const marketDataService = new MarketDataService();

  // Load assets on mount
  useEffect(() => {
    loadAssets();
  }, []);

  // Filter assets when search changes
  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredAssets(assets);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = assets.filter(
        (asset) =>
          asset.symbol.toLowerCase().includes(query) ||
          asset.name.toLowerCase().includes(query),
      );

      setFilteredAssets(filtered);
    }
    setCurrentPage(1); // Reset to first page on search
  }, [searchQuery, assets]);

  const loadAssets = async () => {
    try {
      setLoading(true);

      // Get tradable US equities
      const rawAssets = await assetService.getTradableAssets("us_equity");

      // Get top 100 by popularity/market cap (you can adjust this)
      const popularSymbols = rawAssets
        .filter((a) => a.tradable && a.status === "active")
        .slice(0, 100)
        .map((a) => a.symbol);

      let assetsWithPrices: Asset[] = [];

      try {
        // Try to fetch market data for these assets
        const snapshots = await marketDataService.getSnapshots(popularSymbols);

        // Combine asset info with market data
        assetsWithPrices = popularSymbols
          .map((symbol) => {
            const assetInfo = rawAssets.find((a) => a.symbol === symbol);
            const snapshot = snapshots[symbol];

            if (!assetInfo || !snapshot?.latestTrade) return null;

            const currentPrice = snapshot.latestTrade.p;
            const previousClose = snapshot.prevDailyBar?.c || currentPrice;
            const dailyChange =
              previousClose > 0
                ? ((currentPrice - previousClose) / previousClose) * 100
                : 0;

            return {
              symbol: assetInfo.symbol,
              name: assetInfo.name,
              price: currentPrice,
              dailyChange,
              volume: snapshot.dailyBar?.v || 0,
              marketCap: 0,
            } as Asset;
          })
          .filter((asset): asset is Asset => asset !== null);
      } catch (marketDataError: any) {
        console.warn(
          "Could not fetch market data, using mock prices:",
          marketDataError.message,
        );

        // Fallback: Use mock data for top 20 assets
        assetsWithPrices = popularSymbols
          .slice(0, 20)
          .map((symbol) => {
            const assetInfo = rawAssets.find((a) => a.symbol === symbol);

            if (!assetInfo) return null;

            const mockPrice = 50 + Math.random() * 450; // Random price between 50-500
            const mockChange = (Math.random() - 0.5) * 10; // ±5% change

            return {
              symbol: assetInfo.symbol,
              name: assetInfo.name,
              price: mockPrice,
              dailyChange: mockChange,
              volume: Math.floor(Math.random() * 10000000) + 1000000,
              marketCap: 0,
            } as Asset;
          })
          .filter((asset): asset is Asset => asset !== null);
      }

      setAssets(assetsWithPrices);
      setFilteredAssets(assetsWithPrices);
    } catch (error) {
      console.error("Error loading assets:", error);
      setAssets([]);
      setFilteredAssets([]);
    } finally {
      setLoading(false);
    }
  };

  // Pagination
  const totalPages = Math.ceil(filteredAssets.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentAssets = filteredAssets.slice(startIndex, endIndex);

  // Handle asset click - navigate to detail page
  const handleAssetClick = (asset: Asset) => {
    setSelectedAsset(asset);
    // Add welcome message for this asset
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
      // Get relevant data about the selected asset
      let snapshot: any;
      let priceChange: any;
      let priceSummary: any;

      try {
        snapshot = await marketDataService.getSnapshot(selectedAsset.symbol);
        priceChange = await marketDataService.getPriceChange(
          selectedAsset.symbol,
        );
        priceSummary = await marketDataService.getPriceSummary(
          selectedAsset.symbol,
        );
      } catch (dataError: any) {
        console.warn(
          "Using asset list data for AI response:",
          dataError.message,
        );
        // Use data from the asset list
        snapshot = { latestTrade: { p: selectedAsset.price } };
        priceChange = {
          currentPrice: selectedAsset.price,
          previousClose:
            selectedAsset.price / (1 + selectedAsset.dailyChange / 100),
          change: selectedAsset.price * (selectedAsset.dailyChange / 100),
          changePercent: selectedAsset.dailyChange,
        };
        priceSummary = {
          symbol: selectedAsset.symbol,
          currentPrice: selectedAsset.price,
          dayHigh: selectedAsset.price * 1.02,
          dayLow: selectedAsset.price * 0.98,
          dayOpen: selectedAsset.price * (1 - selectedAsset.dailyChange / 200),
          volume: selectedAsset.volume || 0,
        };
      }

      // Generate AI response based on the question and data
      const response = generateAIResponse(
        message,
        selectedAsset,
        snapshot,
        priceChange,
        priceSummary,
      );

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
        content:
          "Sorry, I encountered an error fetching data for this stock. Please try again.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSendingMessage(false);
    }
  };

  // Simple AI response generator (you can replace with actual AI API)
  const generateAIResponse = (
    question: string,
    asset: Asset,
    _snapshot: any,
    priceChange: any,
    priceSummary: any,
  ): string => {
    const lowerQuestion = question.toLowerCase();

    if (lowerQuestion.includes("price") || lowerQuestion.includes("cost")) {
      return `${asset.symbol} is currently trading at $${asset.price.toFixed(2)}. Today's high is $${priceSummary.dayHigh.toFixed(2)} and low is $${priceSummary.dayLow.toFixed(2)}.`;
    }

    if (
      lowerQuestion.includes("change") ||
      lowerQuestion.includes("performance")
    ) {
      const changeSign = priceChange.change >= 0 ? "+" : "";

      return `${asset.symbol} has ${priceChange.change >= 0 ? "gained" : "lost"} ${changeSign}$${priceChange.change.toFixed(2)} (${changeSign}${priceChange.changePercent.toFixed(2)}%) today. Previous close was $${priceChange.previousClose.toFixed(2)}.`;
    }

    if (lowerQuestion.includes("volume")) {
      return `Today's trading volume for ${asset.symbol} is ${priceSummary.volume.toLocaleString()} shares.`;
    }

    if (lowerQuestion.includes("buy") || lowerQuestion.includes("invest")) {
      return `${asset.symbol} (${asset.name}) is ${asset.dailyChange >= 0 ? "up" : "down"} ${Math.abs(asset.dailyChange).toFixed(2)}% today. Current price is $${asset.price.toFixed(2)}. Consider reviewing the company's fundamentals and your investment strategy before making a decision.`;
    }

    if (lowerQuestion.includes("high") || lowerQuestion.includes("low")) {
      return `Today's trading range for ${asset.symbol}: High: $${priceSummary.dayHigh.toFixed(2)}, Low: $${priceSummary.dayLow.toFixed(2)}, Open: $${priceSummary.dayOpen.toFixed(2)}.`;
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
            Browse tradable assets and get AI insights
          </p>
        </div>

        {/* Main Content - Horizontal Layout */}
        <div className="flex-1 flex gap-4 min-h-0">
          {/* Left Side - Stock List (2/3) */}
          <div className="flex-[2] flex flex-col min-w-0">
            <Card className="flex-1 flex flex-col">
              <CardHeader className="flex-shrink-0 pb-3">
                <div className="flex flex-col gap-3 w-full">
                  {/* Search Bar */}
                  <Input
                    isClearable
                    placeholder="Search by symbol or name..."
                    startContent={
                      <svg
                        className="w-5 h-5 text-default-400"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={2}
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    }
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onClear={() => setSearchQuery("")}
                  />

                  {/* Stats */}
                  <div className="flex gap-2 items-center">
                    <Chip size="sm" variant="flat">
                      {filteredAssets.length} Assets
                    </Chip>
                    {searchQuery && (
                      <Chip color="primary" size="sm" variant="flat">
                        Filtered: {filteredAssets.length} / {assets.length}
                      </Chip>
                    )}
                  </div>
                </div>
              </CardHeader>

              <CardBody className="flex-1 overflow-hidden flex flex-col p-0">
                {loading ? (
                  <div className="flex items-center justify-center h-full">
                    <Spinner size="lg" />
                  </div>
                ) : (
                  <>
                    {/* Table Header */}
                    <div className="flex-shrink-0 px-4 py-3 border-b border-divider">
                      <div className="grid grid-cols-12 gap-4 text-sm font-medium text-default-500">
                        <div className="col-span-2">Symbol</div>
                        <div className="col-span-4">Name</div>
                        <div className="col-span-2 text-right">Price</div>
                        <div className="col-span-2 text-right">24h Change</div>
                        <div className="col-span-2 text-right">Actions</div>
                      </div>
                    </div>

                    {/* Asset List - Scrollable */}
                    <div className="flex-1 overflow-y-auto px-4 py-2">
                      {currentAssets.length === 0 ? (
                        <div className="flex items-center justify-center h-full">
                          <p className="text-default-400">
                            {searchQuery
                              ? "No assets match your search"
                              : "No assets available"}
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {currentAssets.map((asset) => (
                            <Card
                              key={asset.symbol}
                              isPressable
                              className="hover:bg-default-100 transition-colors"
                              shadow="sm"
                            >
                              <CardBody className="py-3">
                                <div className="grid grid-cols-12 gap-4 items-center">
                                  {/* Symbol */}
                                  <div className="col-span-2">
                                    <Chip
                                      classNames={{
                                        base: "font-mono font-bold",
                                        content: "text-xs",
                                      }}
                                      color="primary"
                                      size="sm"
                                      variant="flat"
                                    >
                                      {asset.symbol}
                                    </Chip>
                                  </div>

                                  {/* Name */}
                                  <div className="col-span-4">
                                    <span className="text-sm font-medium text-foreground truncate block">
                                      {asset.name}
                                    </span>
                                  </div>

                                  {/* Price */}
                                  <div className="col-span-2 text-right">
                                    <span className="text-sm font-semibold text-foreground font-mono">
                                      ${formatPrice(asset.price)}
                                    </span>
                                  </div>

                                  {/* Daily change */}
                                  <div className="col-span-2 text-right">
                                    <Chip
                                      classNames={{
                                        base: "font-mono",
                                        content: "text-xs font-semibold",
                                      }}
                                      color={
                                        asset.dailyChange >= 0
                                          ? "success"
                                          : "danger"
                                      }
                                      size="sm"
                                      variant="flat"
                                    >
                                      {formatChange(asset.dailyChange)}
                                    </Chip>
                                  </div>

                                  {/* Actions */}
                                  <div className="col-span-2 flex gap-1 justify-end">
                                    <Button
                                      color="secondary"
                                      size="sm"
                                      variant="flat"
                                      onPress={() => handleAssetClick(asset)}
                                    >
                                      Ask AI
                                    </Button>
                                    <Button
                                      color="primary"
                                      size="sm"
                                      variant="flat"
                                      onPress={() =>
                                        handleNavigateToAsset(asset.symbol)
                                      }
                                    >
                                      View
                                    </Button>
                                  </div>
                                </div>
                              </CardBody>
                            </Card>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex-shrink-0 flex justify-center py-4 border-t border-divider">
                        <div className="flex items-center gap-2">
                          <Button
                            isDisabled={currentPage === 1}
                            size="sm"
                            variant="flat"
                            onPress={() => setCurrentPage(currentPage - 1)}
                          >
                            Previous
                          </Button>
                          <Chip variant="flat">
                            Page {currentPage} of {totalPages}
                          </Chip>
                          <Button
                            isDisabled={currentPage === totalPages}
                            size="sm"
                            variant="flat"
                            onPress={() => setCurrentPage(currentPage + 1)}
                          >
                            Next
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </CardBody>
            </Card>
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
                        classNames={{
                          base: "font-mono font-bold",
                        }}
                        color="secondary"
                        size="sm"
                        variant="flat"
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
                    className="h-full"
                    disabled={!selectedAsset || sendingMessage}
                    messages={messages}
                    placeholder={
                      selectedAsset
                        ? `Ask about ${selectedAsset.symbol}...`
                        : "Select a stock first..."
                    }
                    onSend={handleSendMessage}
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
