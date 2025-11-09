import type { Asset as AlpacaAsset } from "@/services/alpaca.types";

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Spinner } from "@heroui/spinner";

import { StockChart } from "@/components/StockChart";
import { ChatBox } from "@/components/ChatBox";
import { LoadingAI } from "@/components/LoadingAI";
import { ChatMessage, StockDataPoint } from "@/types";
import { AssetService } from "@/services/AssetService";
import { MarketDataService } from "@/services/MarketDataService";
import { aiService } from "@/services/AIService";

interface AIMessage {
  aiId: number;
  message: string;
  timestamp: number;
}

export default function AssetPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();

  const [assetInfo, setAssetInfo] = useState<AlpacaAsset | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState<StockDataPoint[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [aiMessages, setAiMessages] = useState<AIMessage[]>([]);
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
        console.warn(
          "Could not fetch real-time price data, using mock data:",
          priceError.message,
        );

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

      // Load historical data for chart (last 30 days)
      const endDate = new Date();
      const startDate = new Date();

      startDate.setDate(startDate.getDate() - 30);

      let stockData: StockDataPoint[] = [];

      try {
        const bars = await marketDataService.getBars(symbol, {
          start: startDate,
          end: endDate,
          timeframe: "1Day",
          limit: 30,
        });

        stockData = bars.map((bar) => ({
          date: new Date(bar.t),
          open: bar.o,
          high: bar.h,
          low: bar.l,
          close: bar.c,
          volume: bar.v,
        }));
      } catch (barError: any) {
        console.warn(
          "Could not fetch historical bars, using mock data:",
          barError.message,
        );

        // Generate mock data for the last 30 days
        const basePrice = currentPrice || 100;

        stockData = Array.from({ length: 30 }, (_, i) => {
          const date = new Date(startDate);

          date.setDate(date.getDate() + i);

          // Create some realistic price variation
          const randomChange = (Math.random() - 0.5) * 0.05; // ±5%
          const dayPrice = basePrice * (1 + randomChange);
          const variance = dayPrice * 0.02; // 2% intraday range

          return {
            date,
            open: dayPrice - variance * Math.random(),
            high: dayPrice + variance,
            low: dayPrice - variance,
            close: dayPrice,
            volume: Math.floor(Math.random() * 10000000) + 1000000,
          };
        });
      }

      setChartData(stockData);

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

  const handleAnalyze = async () => {
    if (!assetInfo || !symbol) return;

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
    setAiMessages([]);

    // Add system message
    const systemMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "system",
      content: `🤖 Analyzing ${symbol}...`,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, systemMessage]);

    // Simulate AI communication logs
    const communicationInterval = setInterval(() => {
      const aiId = Math.floor(Math.random() * 5) + 1;
      const messages = [
        `Fetching ${symbol} market data...`,
        "Analyzing price movements...",
        "Evaluating technical indicators...",
        "Assessing market sentiment...",
        "Computing risk metrics...",
        "Generating recommendation...",
      ];

      const newMessage: AIMessage = {
        aiId,
        message: messages[Math.floor(Math.random() * messages.length)],
        timestamp: Date.now(),
      };

      setAiMessages((prev) => [...prev, newMessage]);
    }, 700);

    try {
      // Prepare asset data for AI analysis
      const assetAnalysisData = {
        symbol: assetInfo.symbol,
        name: assetInfo.name,
        currentPrice: priceData.currentPrice,
        dailyChange: priceData.dailyChange,
        dailyChangePercent: priceData.dailyChangePercent,
        open: priceData.open,
        high: priceData.high,
        low: priceData.low,
        volume: priceData.volume,
        previousClose: priceData.previousClose,
        historicalData: chartData.map((d) => ({
          date: d.date,
          close: d.close,
          volume: d.volume || 0,
        })),
      };

      // Call AI service for analysis
      const analysis = await aiService.analyzeAsset(assetAnalysisData);

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

  const handleBuySell = () => {
    // TODO: Open buy/sell dialog
    alert(`Buy/Sell dialog for ${symbol} - Coming soon!`);
  };

  const handleSendMessage = async (message: string) => {
    if (!assetInfo) return;

    if (!aiService.isConfigured()) {
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "assistant",
        content:
          "⚠️ OpenAI API key not configured. Using fallback responses. Add VITE_OPENAI_API_KEY to your .env file for AI-powered insights.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);

      // Fall back to local responses
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "user",
        content: message,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);

      const response = generateAIResponse(
        message,
        assetInfo,
        {
          currentPrice: priceData.currentPrice,
          previousClose: priceData.previousClose,
          change: priceData.dailyChange,
          changePercent: priceData.dailyChangePercent,
        },
        {
          symbol: assetInfo.symbol,
          currentPrice: priceData.currentPrice,
          dayHigh: priceData.high,
          dayLow: priceData.low,
          dayOpen: priceData.open,
          volume: priceData.volume,
        },
      );

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);

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
      // Prepare context for AI
      const context = {
        conversationHistory: messages.slice(-6).map((msg) => ({
          role: msg.role as "user" | "assistant",
          content: msg.content,
        })),
        currentAsset: {
          symbol: assetInfo.symbol,
          name: assetInfo.name,
          currentPrice: priceData.currentPrice,
          dailyChange: priceData.dailyChange,
          dailyChangePercent: priceData.dailyChangePercent,
          open: priceData.open,
          high: priceData.high,
          low: priceData.low,
          volume: priceData.volume,
          previousClose: priceData.previousClose,
        },
      };

      // Get AI response
      const response = await aiService.getChatResponse(message, context);

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
        content: "Sorry, I encountered an error. Please try again.",
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
    priceSummary: any,
  ): string => {
    const lowerQuestion = question.toLowerCase();
    const currentPrice = priceData.currentPrice;

    if (lowerQuestion.includes("price") || lowerQuestion.includes("cost")) {
      return `${asset.symbol} is currently trading at $${currentPrice.toFixed(2)}. Today's high is $${priceSummary.dayHigh.toFixed(2)} and low is $${priceSummary.dayLow.toFixed(2)}.`;
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

    if (
      lowerQuestion.includes("buy") ||
      lowerQuestion.includes("invest") ||
      lowerQuestion.includes("should i")
    ) {
      return `${asset.symbol} (${asset.name}) is ${priceData.dailyChangePercent >= 0 ? "up" : "down"} ${Math.abs(priceData.dailyChangePercent).toFixed(2)}% today at $${currentPrice.toFixed(2)}. Consider your investment goals, risk tolerance, and consult financial research before making decisions.`;
    }

    if (
      lowerQuestion.includes("high") ||
      lowerQuestion.includes("low") ||
      lowerQuestion.includes("range")
    ) {
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
              The asset  could not be found.
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
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <Button
            size="sm"
            startContent={
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            }
            variant="light"
            onPress={() => navigate("/market")}
          >
            Back to Market
          </Button>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button
              color="secondary"
              startContent={
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              }
              variant="flat"
              onPress={handleAnalyze}
            >
              Analyze
            </Button>
            <Button
              color="success"
              startContent={
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              }
              onPress={handleBuySell}
            >
              Buy/Sell
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Chip
            classNames={{
              base: "font-mono font-bold text-lg px-4 py-2",
            }}
            color="primary"
            size="lg"
            variant="flat"
          >
            {assetInfo.symbol}
          </Chip>
          <div className="flex-1">
            <h1 className="text-2xl font-bold">{assetInfo.name}</h1>
            <div className="flex items-center gap-4 mt-1">
              <span className="text-3xl font-bold">
                ${formatPrice(priceData.currentPrice)}
              </span>
              <Chip
                classNames={{
                  base: "font-mono",
                  content: "text-sm font-semibold",
                }}
                color={priceData.dailyChangePercent >= 0 ? "success" : "danger"}
                size="md"
                variant="flat"
              >
                {priceData.dailyChangePercent >= 0 ? "+" : ""}
                {priceData.dailyChangePercent.toFixed(2)}%
              </Chip>
            </div>
          </div>
        </div>
      </div>

      {/* Asset Info Chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        <Chip
          color={assetInfo.tradable ? "success" : "default"}
          size="sm"
          variant="flat"
        >
          {assetInfo.tradable ? "Tradable" : "Not Tradable"}
        </Chip>
        <Chip
          color={assetInfo.marginable ? "primary" : "default"}
          size="sm"
          variant="flat"
        >
          {assetInfo.marginable ? "Marginable" : "Cash Only"}
        </Chip>
        <Chip
          color={assetInfo.shortable ? "warning" : "default"}
          size="sm"
          variant="flat"
        >
          {assetInfo.shortable ? "Shortable" : "Long Only"}
        </Chip>
        <Chip
          color={assetInfo.fractionable ? "secondary" : "default"}
          size="sm"
          variant="flat"
        >
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

      {/* AI Loading Component - Show when analyzing */}
      {isAnalyzing && (
        <div className="mb-6 animate-in fade-in slide-in-from-top-4 duration-500">
          <LoadingAI messages={aiMessages} showLogs={true} />
        </div>
      )}

      {/* Main Content - Chart and Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart - 2/3 width on large screens */}
        <div className="lg:col-span-2 h-[500px]">
          <StockChart data={chartData} symbol={assetInfo.symbol} />
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
                  className="h-full"
                  disabled={sendingMessage || isAnalyzing}
                  messages={messages}
                  placeholder={`Ask about ${assetInfo.symbol}...`}
                  onSend={handleSendMessage}
                />
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
