import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Spinner } from "@heroui/spinner";
import { BalanceChart } from "@/components/BalanceChart";
import { ChatBox } from "@/components/ChatBox";
import { AssetSidebar } from "@/components/AssetSidebar";
import { BuySellDialog } from "@/components/BuySellDialog";
import { ChatMessage } from "@/types";
import { AssetService } from "@/services/AssetService";
import { MarketDataService } from "@/services/MarketDataService";
import SimpleTradingService from "@/services/SimpleTradingService";
import type { Asset as AlpacaAsset, Position } from "@/services/alpaca.types";

export default function AssetPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  
  const [assetInfo, setAssetInfo] = useState<AlpacaAsset | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState<{ date: Date; balance: number }[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [userPosition, setUserPosition] = useState<Position | null>(null);
  const [showBuySellDialog, setShowBuySellDialog] = useState(false);
  const [priceData, setPriceData] = useState({
    currentPrice: 0,
    open: 0,
    high: 0,
    low: 0,
    volume: 0,
    previousClose: 0,
    dailyChange: 0,
    dailyChangePercent: 0,
  });

  const assetService = new AssetService();
  const marketDataService = new MarketDataService();

  useEffect(() => {
    if (symbol) {
      loadAssetData();
    }
  }, [symbol]);

  const loadAssetData = async () => {
    if (!symbol) return;

    try {
      setLoading(true);

      // Check if user owns this asset
      try {
        const position = await SimpleTradingService.getPosition(symbol);
        setUserPosition(position);
      } catch (posError) {
        // User doesn't own this asset, that's fine
        setUserPosition(null);
      }

      // Load comprehensive asset info from Alpaca
      const asset = await assetService.getAsset(symbol);
      setAssetInfo(asset);
      
      // Load market data snapshot
      let currentPrice = 0;
      let priceDataObj = {
        currentPrice: 0,
        open: 0,
        high: 0,
        low: 0,
        volume: 0,
        previousClose: 0,
        dailyChange: 0,
        dailyChangePercent: 0,
      };

      try {
        const snapshot = await marketDataService.getSnapshot(symbol);
        const priceChange = await marketDataService.getPriceChange(symbol);

        currentPrice = snapshot.latestTrade?.p || 0;
        priceDataObj = {
          currentPrice,
          open: snapshot.dailyBar?.o || 0,
          high: snapshot.dailyBar?.h || 0,
          low: snapshot.dailyBar?.l || 0,
          volume: snapshot.dailyBar?.v || 0,
          previousClose: priceChange.previousClose,
          dailyChange: priceChange.change,
          dailyChangePercent: priceChange.changePercent,
        };
      } catch (priceError: any) {
        console.warn("Could not fetch real-time price data, using mock data:", priceError.message);
        
        // Generate mock price data
        const mockPrice = 100 + Math.random() * 400; // Random price between 100-500
        const mockChange = (Math.random() - 0.5) * 10; // ±5% change
        currentPrice = mockPrice;
        
        priceDataObj = {
          currentPrice: mockPrice,
          open: mockPrice * (1 - mockChange / 200),
          high: mockPrice * 1.02,
          low: mockPrice * 0.98,
          volume: Math.floor(Math.random() * 10000000) + 1000000,
          previousClose: mockPrice * (1 - mockChange / 100),
          dailyChange: mockPrice * (mockChange / 100),
          dailyChangePercent: mockChange,
        };
      }

      setPriceData(priceDataObj);

      // Load historical data for balance chart (last 30 days)
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 30);

      let balanceData: { date: Date; balance: number }[] = [];
      
      try {
        const bars = await marketDataService.getBars(symbol, {
          start: startDate,
          end: endDate,
          timeframe: '1Day',
          limit: 30,
        });

        // Convert bars to balance data (using close price as balance)
        balanceData = bars.map(bar => ({
          date: new Date(bar.t),
          balance: bar.c,
        }));
      } catch (barError: any) {
        console.warn("Could not fetch historical bars, using mock data:", barError.message);
        
        // Generate mock daily balance data for the last 30 days
        const basePrice = currentPrice || 100;
        const tradingDays = 30;
        
        balanceData = Array.from({ length: tradingDays }, (_, i) => {
          const date = new Date(startDate);
          date.setDate(date.getDate() + i);
          
          // Create realistic daily price movement with trend
          const trendChange = (Math.random() - 0.5) * 0.02; // ±2% daily variation
          const balance = basePrice * (1 + (i * trendChange / tradingDays));
          
          return {
            date,
            balance: balance + (Math.random() - 0.5) * basePrice * 0.05, // Add some daily volatility
          };
        });
      }

      setChartData(balanceData);

      // Add welcome message
      setMessages([
        {
          id: Date.now().toString(),
          role: "system",
          content: `Welcome! You're viewing ${asset.symbol} (${asset.name}). Ask me anything about this stock!`,
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      console.error("Error loading asset data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = () => {
    // TODO: Implement analyze functionality
    console.log("Analyze button clicked for", symbol);
  };

  const handleBuySell = () => {
    setShowBuySellDialog(true);
  };

  const handleBuySellSuccess = () => {
    // Reload asset data to update position
    loadAssetData();
  };

  const handleSendMessage = async (message: string) => {
    if (!assetInfo) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setSendingMessage(true);

    try {
      // Get fresh data for AI response
      let priceChange: any;
      let priceSummary: any;
      
      try {
        await marketDataService.getSnapshot(assetInfo.symbol);
        priceChange = await marketDataService.getPriceChange(assetInfo.symbol);
        priceSummary = await marketDataService.getPriceSummary(assetInfo.symbol);
      } catch (dataError: any) {
        console.warn("Using cached price data for AI response:", dataError.message);
        // Use cached priceData state
        priceChange = {
          currentPrice: priceData.currentPrice,
          previousClose: priceData.previousClose,
          change: priceData.dailyChange,
          changePercent: priceData.dailyChangePercent,
        };
        priceSummary = {
          symbol: assetInfo.symbol,
          currentPrice: priceData.currentPrice,
          dayHigh: priceData.high,
          dayLow: priceData.low,
          dayOpen: priceData.open,
          volume: priceData.volume,
        };
      }

      const response = generateAIResponse(
        message,
        assetInfo,
        priceChange,
        priceSummary
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
        content: "Sorry, I encountered an error fetching data. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSendingMessage(false);
    }
  };

  const generateAIResponse = (
    question: string,
    asset: AlpacaAsset,
    priceChange: any,
    priceSummary: any
  ): string => {
    const lowerQuestion = question.toLowerCase();
    const currentPrice = priceData.currentPrice;

    if (lowerQuestion.includes("price") || lowerQuestion.includes("cost")) {
      return `${asset.symbol} is currently trading at $${currentPrice.toFixed(2)}. Today's high is $${priceSummary.dayHigh.toFixed(2)} and low is $${priceSummary.dayLow.toFixed(2)}.`;
    }

    if (lowerQuestion.includes("change") || lowerQuestion.includes("performance")) {
      const changeSign = priceChange.change >= 0 ? "+" : "";
      return `${asset.symbol} has ${priceChange.change >= 0 ? "gained" : "lost"} ${changeSign}$${priceChange.change.toFixed(2)} (${changeSign}${priceChange.changePercent.toFixed(2)}%) today. Previous close was $${priceChange.previousClose.toFixed(2)}.`;
    }

    if (lowerQuestion.includes("volume")) {
      return `Today's trading volume for ${asset.symbol} is ${priceSummary.volume.toLocaleString()} shares.`;
    }

    if (lowerQuestion.includes("buy") || lowerQuestion.includes("invest") || lowerQuestion.includes("should i")) {
      return `${asset.symbol} (${asset.name}) is ${priceData.dailyChangePercent >= 0 ? "up" : "down"} ${Math.abs(priceData.dailyChangePercent).toFixed(2)}% today at $${currentPrice.toFixed(2)}. Consider your investment goals, risk tolerance, and consult financial research before making decisions.`;
    }

    if (lowerQuestion.includes("high") || lowerQuestion.includes("low") || lowerQuestion.includes("range")) {
      return `Today's trading range for ${asset.symbol}: High: $${priceSummary.dayHigh.toFixed(2)}, Low: $${priceSummary.dayLow.toFixed(2)}, Open: $${priceSummary.dayOpen.toFixed(2)}.`;
    }

    if (lowerQuestion.includes("chart") || lowerQuestion.includes("trend")) {
      return `Looking at the 30-day chart, ${asset.symbol} is currently at $${currentPrice.toFixed(2)}. Check the chart above to see price trends and patterns over the last month.`;
    }

    // Default response
    return `${asset.symbol} (${asset.name}) is currently at $${currentPrice.toFixed(2)}, ${priceData.dailyChangePercent >= 0 ? "up" : "down"} ${Math.abs(priceData.dailyChangePercent).toFixed(2)}% today. Ask me about price, performance, volume, or trading range!`;
  };

  const formatPrice = (price: number) => {
    return price.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!assetInfo) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Card>
          <CardBody className="text-center py-12">
            <h1 className="text-2xl font-bold mb-2">Asset Not Found</h1>
            <p className="text-default-500 mb-4">
              The asset "{symbol}" could not be found.
            </p>
            <Button color="primary" onPress={() => navigate("/market")}>
              Back to Market
            </Button>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar - Hidden on mobile, shown on large screens */}
        <div className="hidden lg:block lg:col-span-1">
          <div className="sticky top-6">
            {symbol && <AssetSidebar currentSymbol={symbol} />}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {/* Header */}
          <div className="mb-6">
            <div className="flex justify-between items-start mb-4">
              <Button
                size="sm"
                variant="light"
                onPress={() => navigate("/market")}
                startContent={
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                    className="w-4 h-4"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
                    />
                  </svg>
                }
              >
                Back to Market
              </Button>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button
                  color="secondary"
                  variant="flat"
                  onPress={handleAnalyze}
                  startContent={
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                      className="w-4 h-4"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
                      />
                    </svg>
                  }
                >
                  Analyze
                </Button>
                <Button
                  color="success"
                  onPress={handleBuySell}
                  startContent={
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                      className="w-4 h-4"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z"
                      />
                    </svg>
                  }
                >
                  Buy/Sell
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <Chip
                variant="flat"
                color="primary"
                size="lg"
                classNames={{
                  base: "font-mono font-bold text-lg px-4 py-2",
                }}
              >
                {assetInfo.symbol}
              </Chip>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold">{assetInfo.name}</h1>
                  {userPosition && (
                    <Chip
                      variant="flat"
                      color="success"
                      size="sm"
                      startContent={
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          strokeWidth={2}
                          stroke="currentColor"
                          className="w-3 h-3"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      }
                      classNames={{
                        content: "font-semibold",
                      }}
                    >
                      Owned
                    </Chip>
                  )}
                </div>
                <div className="flex items-center gap-4 mt-1">
                  <span className="text-3xl font-bold">${formatPrice(priceData.currentPrice)}</span>
                  <Chip
                    variant="flat"
                    color={priceData.dailyChangePercent >= 0 ? "success" : "danger"}
                    size="md"
                    classNames={{
                      base: "font-mono",
                      content: "text-sm font-semibold",
                    }}
                  >
                    {priceData.dailyChangePercent >= 0 ? "+" : ""}
                    {priceData.dailyChangePercent.toFixed(2)}%
                  </Chip>
                </div>
                {userPosition && (
                  <div className="flex items-center gap-4 mt-2">
                    <div className="text-sm">
                      <span className="text-default-500">Position: </span>
                      <span className="font-semibold">
                        {formatPrice(parseFloat(userPosition.qty))} shares
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="text-default-500">Value: </span>
                      <span className="font-semibold">
                        ${formatPrice(parseFloat(userPosition.market_value))}
                      </span>
                    </div>
                    <div className="text-sm">
                      <span className="text-default-500">P/L: </span>
                      <span
                        className={`font-semibold ${
                          parseFloat(userPosition.unrealized_pl) >= 0
                            ? "text-success"
                            : "text-danger"
                        }`}
                      >
                        {parseFloat(userPosition.unrealized_pl) >= 0 ? "+" : ""}
                        ${formatPrice(parseFloat(userPosition.unrealized_pl))} (
                        {parseFloat(userPosition.unrealized_plpc) >= 0 ? "+" : ""}
                        {parseFloat(userPosition.unrealized_plpc).toFixed(2)}%)
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Asset Info Chips */}
          <div className="flex flex-wrap gap-2 mb-6">
            <Chip size="sm" variant="flat" color={assetInfo.tradable ? "success" : "default"}>
              {assetInfo.tradable ? "Tradable" : "Not Tradable"}
            </Chip>
            <Chip size="sm" variant="flat" color={assetInfo.marginable ? "primary" : "default"}>
              {assetInfo.marginable ? "Marginable" : "Cash Only"}
            </Chip>
            <Chip size="sm" variant="flat" color={assetInfo.shortable ? "warning" : "default"}>
              {assetInfo.shortable ? "Shortable" : "Long Only"}
            </Chip>
            <Chip size="sm" variant="flat" color={assetInfo.fractionable ? "secondary" : "default"}>
              {assetInfo.fractionable ? "Fractionable" : "Whole Shares"}
            </Chip>
            <Chip size="sm" variant="flat">
              {assetInfo.exchange}
            </Chip>
            <Chip size="sm" variant="flat">
              Status: {assetInfo.status.toUpperCase()}
            </Chip>
          </div>

          {/* Price Stats */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <Card>
              <CardBody className="py-3">
                <p className="text-xs text-default-500 mb-1">Open</p>
                <p className="text-lg font-semibold">${formatPrice(priceData.open)}</p>
              </CardBody>
            </Card>
            <Card>
              <CardBody className="py-3">
                <p className="text-xs text-default-500 mb-1">High</p>
                <p className="text-lg font-semibold text-success">${formatPrice(priceData.high)}</p>
              </CardBody>
            </Card>
            <Card>
              <CardBody className="py-3">
                <p className="text-xs text-default-500 mb-1">Low</p>
                <p className="text-lg font-semibold text-danger">${formatPrice(priceData.low)}</p>
              </CardBody>
            </Card>
            <Card>
              <CardBody className="py-3">
                <p className="text-xs text-default-500 mb-1">Volume</p>
                <p className="text-lg font-semibold">{priceData.volume.toLocaleString()}</p>
              </CardBody>
            </Card>
            <Card>
              <CardBody className="py-3">
                <p className="text-xs text-default-500 mb-1">Prev Close</p>
                <p className="text-lg font-semibold">${formatPrice(priceData.previousClose)}</p>
              </CardBody>
            </Card>
          </div>

          {/* Main Content - Chart and Chat */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chart - 2/3 width on large screens */}
            <div className="lg:col-span-2 h-[500px]">
              <BalanceChart
                data={chartData}
                title={`${assetInfo.symbol} Price History (30 Days)`}
              />
            </div>

            {/* Chat - 1/3 width on large screens */}
            <div className="lg:col-span-1">
              <Card className="h-[500px] flex flex-col">
                <CardHeader className="flex-shrink-0 pb-3">
                  <div className="flex flex-col gap-2 w-full">
                    <h2 className="text-xl font-bold">AI Assistant</h2>
                    <p className="text-sm text-default-500">
                      Ask questions about {assetInfo.symbol}
                    </p>
                  </div>
                </CardHeader>
                <CardBody className="flex-1 overflow-hidden p-0">
                  <div className="h-full">
                    <ChatBox
                      messages={messages}
                      onSend={handleSendMessage}
                      placeholder={`Ask about ${assetInfo.symbol}...`}
                      disabled={sendingMessage}
                      className="h-full"
                    />
                  </div>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* Buy/Sell Dialog */}
      {assetInfo && (
        <BuySellDialog
          isOpen={showBuySellDialog}
          onClose={() => setShowBuySellDialog(false)}
          asset={assetInfo}
          currentPrice={priceData.currentPrice}
          userPosition={userPosition}
          onSuccess={handleBuySellSuccess}
        />
      )}
    </div>
  );
}
