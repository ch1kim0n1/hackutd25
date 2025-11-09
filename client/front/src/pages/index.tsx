import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { BalanceChart } from "@/components/BalanceChart";
import { Asset } from "@/types";
import { AlpacaService } from "@/services";
import type { Position, Account } from "@/services/alpaca.types";

interface PortfolioAsset extends Asset {
  shares: number;
  totalValue: number;
  purchasePrice: number;
  profitLoss: number;
  profitLossPercent: number;
}

export const IndexPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [portfolioAssets, setPortfolioAssets] = useState<PortfolioAsset[]>([]);
  const [account, setAccount] = useState<Account | null>(null);
  const [balanceData, setBalanceData] = useState<{ date: Date; balance: number }[]>([]);

  // Initialize Alpaca service
  const alpaca = new AlpacaService();

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const loadPortfolioData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch account and positions from Alpaca
      const [accountData, positions, portfolioHistory] = await Promise.all([
        alpaca.account.getAccount(),
        alpaca.trading.getPositions(),
        alpaca.account.getPortfolioHistory({
          period: '1M',
          timeframe: '1D',
        }),
      ]);

      setAccount(accountData);

      // Convert positions to portfolio assets with current prices
      const assets = await Promise.all(
        positions.map(async (position: Position) => {
          const currentPrice = parseFloat(position.current_price);
          const avgEntryPrice = parseFloat(position.avg_entry_price);
          const qty = parseFloat(position.qty);
          const marketValue = parseFloat(position.market_value);
          const unrealizedPL = parseFloat(position.unrealized_pl);
          const unrealizedPLPC = parseFloat(position.unrealized_plpc);

          // Get price change for the day
          let dailyChange = 0;
          try {
            const priceChange = await alpaca.marketData.getPriceChange(position.symbol);
            dailyChange = priceChange.changePercent;
          } catch (err) {
            console.warn(`Could not fetch price change for ${position.symbol}`);
          }

          return {
            symbol: position.symbol,
            name: position.symbol, // You can fetch full name from asset service if needed
            price: currentPrice,
            dailyChange: dailyChange,
            shares: qty,
            purchasePrice: avgEntryPrice,
            totalValue: marketValue,
            profitLoss: unrealizedPL,
            profitLossPercent: unrealizedPLPC,
          } as PortfolioAsset;
        })
      );

      setPortfolioAssets(assets);

      // Convert portfolio history to balance data
      if (portfolioHistory.equity && portfolioHistory.timestamp) {
        const chartData = portfolioHistory.timestamp.map((timestamp, index) => ({
          date: new Date(timestamp * 1000),
          balance: portfolioHistory.equity[index],
        }));
        setBalanceData(chartData);
      }
    } catch (err: any) {
      console.error('Error loading portfolio data:', err);
      setError(err.message || 'Failed to load portfolio data');
    } finally {
      setLoading(false);
    }
  };

  // Calculate portfolio totals from Alpaca account data
  const totalValue = account ? parseFloat(account.portfolio_value) : 0;
  const totalInvested = portfolioAssets.reduce(
    (sum, asset) => sum + asset.shares * asset.purchasePrice,
    0
  );
  const totalProfitLoss = account ? parseFloat(account.equity) - parseFloat(account.last_equity) : 0;
  const totalProfitLossPercent = totalInvested > 0 ? (totalProfitLoss / totalInvested) * 100 : 0;
  const todayChange = account 
    ? parseFloat(account.equity) - parseFloat(account.last_equity)
    : 0;
  const todayChangePercent = account && parseFloat(account.last_equity) > 0
    ? (todayChange / parseFloat(account.last_equity)) * 100
    : 0;

  const handleAssetClick = (asset: PortfolioAsset) => {
    navigate(`/asset/${asset.symbol}`);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Card className="shadow-lg">
          <CardBody className="p-12 text-center">
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              <p className="text-lg text-default-500">Loading portfolio data...</p>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Card className="shadow-lg border-danger">
          <CardBody className="p-8 text-center">
            <div className="flex flex-col items-center gap-4">
              <div className="text-danger text-4xl">⚠️</div>
              <h3 className="text-xl font-bold text-danger">Error Loading Portfolio</h3>
              <p className="text-default-500">{error}</p>
              <Button color="primary" onPress={loadPortfolioData}>
                Retry
              </Button>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header with Refresh Button */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-foreground">Portfolio Dashboard</h1>
        <Button
          color="default"
          variant="flat"
          onPress={loadPortfolioData}
          isDisabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh Data"}
        </Button>
      </div>

      {/* Portfolio Summary Header */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="shadow-lg">
          <CardBody className="p-6">
            <p className="text-sm text-default-500 mb-1">Total Portfolio Value</p>
            <h2 className="text-3xl font-bold text-foreground">{formatCurrency(totalValue)}</h2>
            <div className="flex items-center gap-2 mt-2">
              <Chip
                size="sm"
                variant="flat"
                color={todayChange >= 0 ? "success" : "danger"}
              >
                {formatCurrency(todayChange)}
              </Chip>
              <span
                className={`text-sm font-medium ${
                  todayChange >= 0 ? "text-success" : "text-danger"
                }`}
              >
                {formatPercent(todayChangePercent)} today
              </span>
            </div>
          </CardBody>
        </Card>

        <Card className="shadow-lg">
          <CardBody className="p-6">
            <p className="text-sm text-default-500 mb-1">Total Invested</p>
            <h2 className="text-3xl font-bold text-foreground">
              {formatCurrency(totalInvested)}
            </h2>
            <p className="text-sm text-default-500 mt-2">
              {portfolioAssets.length} assets
            </p>
          </CardBody>
        </Card>

        <Card className="shadow-lg">
          <CardBody className="p-6">
            <p className="text-sm text-default-500 mb-1">Total Profit/Loss</p>
            <h2
              className={`text-3xl font-bold ${
                totalProfitLoss >= 0 ? "text-success" : "text-danger"
              }`}
            >
              {formatCurrency(totalProfitLoss)}
            </h2>
            <Chip
              size="sm"
              variant="flat"
              color={totalProfitLoss >= 0 ? "success" : "danger"}
              className="mt-2"
            >
              {formatPercent(totalProfitLossPercent)}
            </Chip>
          </CardBody>
        </Card>

        <Card className="shadow-lg">
          <CardBody className="p-6 flex flex-col gap-2">
            <Button
              color="primary"
              size="lg"
              className="w-full font-semibold"
              onPress={() => navigate("/market")}
            >
              Go to Market
            </Button>
            <Button
              color="secondary"
              variant="flat"
              size="lg"
              className="w-full font-semibold"
              onPress={() => console.log("Analyze Portfolio clicked")}
            >
              Analyze Portfolio
            </Button>
          </CardBody>
        </Card>
      </div>

      {/* Balance Chart */}
      {balanceData.length > 0 && (
        <BalanceChart data={balanceData} title="Portfolio Value (30 Days)" />
      )}

      {/* Assets List */}
      <Card className="shadow-lg">
        <CardHeader className="px-6 py-4 border-b border-divider">
          <h3 className="text-2xl font-bold text-foreground">Your Assets</h3>
        </CardHeader>
        <CardBody className="p-0">
          {/* Table Header */}
          <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-divider bg-default-50">
            <div className="col-span-3 text-sm font-semibold text-default-700">Asset</div>
            <div className="col-span-2 text-sm font-semibold text-default-700 text-right">
              Price
            </div>
            <div className="col-span-2 text-sm font-semibold text-default-700 text-right">
              Shares
            </div>
            <div className="col-span-2 text-sm font-semibold text-default-700 text-right">
              Total Value
            </div>
            <div className="col-span-3 text-sm font-semibold text-default-700 text-right">
              Profit/Loss
            </div>
          </div>

          {/* Asset Rows */}
          {portfolioAssets.map((asset) => (
            <div
              key={asset.symbol}
              className="grid grid-cols-12 gap-4 px-6 py-4 border-b border-divider hover:bg-default-50 cursor-pointer transition-colors"
              onClick={() => handleAssetClick(asset)}
            >
              {/* Asset Info */}
              <div className="col-span-3 flex flex-col">
                <div className="flex items-center gap-2">
                  <Chip size="sm" color="primary" variant="flat">
                    {asset.symbol}
                  </Chip>
                  <Chip
                    size="sm"
                    variant="flat"
                    color={asset.dailyChange >= 0 ? "success" : "danger"}
                  >
                    {formatPercent(asset.dailyChange)}
                  </Chip>
                </div>
                <span className="text-sm text-default-500 mt-1">{asset.name}</span>
              </div>

              {/* Current Price */}
              <div className="col-span-2 flex items-center justify-end">
                <span className="text-base font-semibold text-foreground font-mono">
                  {formatCurrency(asset.price)}
                </span>
              </div>

              {/* Shares */}
              <div className="col-span-2 flex items-center justify-end">
                <span className="text-base text-foreground">{asset.shares}</span>
              </div>

              {/* Total Value */}
              <div className="col-span-2 flex items-center justify-end">
                <span className="text-base font-semibold text-foreground">
                  {formatCurrency(asset.totalValue)}
                </span>
              </div>

              {/* Profit/Loss */}
              <div className="col-span-3 flex flex-col items-end justify-center">
                <span
                  className={`text-base font-bold ${
                    asset.profitLoss >= 0 ? "text-success" : "text-danger"
                  }`}
                >
                  {formatCurrency(asset.profitLoss)}
                </span>
                <Chip
                  size="sm"
                  variant="flat"
                  color={asset.profitLoss >= 0 ? "success" : "danger"}
                  className="mt-1"
                >
                  {formatPercent(asset.profitLossPercent)}
                </Chip>
              </div>
            </div>
          ))}

          {/* Empty State */}
          {portfolioAssets.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-xl text-default-400 mb-2">No assets in your portfolio yet</p>
              <p className="text-sm text-default-500 mb-6">
                Start investing to see your portfolio here
              </p>
              <Button color="primary" size="lg" onPress={() => navigate("/market")}>
                Go to Market
              </Button>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
};
