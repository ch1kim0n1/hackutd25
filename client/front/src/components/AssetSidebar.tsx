import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardBody } from "@heroui/card";
import { Button } from "@heroui/button";
import { Chip } from "@heroui/chip";
import { Spinner } from "@heroui/spinner";
import SimpleTradingService from "@/services/SimpleTradingService";
import type { Position } from "@/services/alpaca.types";

interface AssetSidebarProps {
  currentSymbol: string;
}

export function AssetSidebar({ currentSymbol }: AssetSidebarProps) {
  const navigate = useNavigate();
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPositions();
  }, []);

  const loadPositions = async () => {
    try {
      setLoading(true);
      const userPositions = await SimpleTradingService.getPositions();
      setPositions(userPositions);
    } catch (error) {
      console.error("Error loading positions:", error);
      setPositions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAssetClick = (symbol: string) => {
    navigate(`/asset/${symbol}`);
  };

  const handleGoToMarket = () => {
    navigate("/market");
  };

  const isCurrentlyOwned = positions.some(
    (pos) => pos.symbol === currentSymbol
  );

  const formatPrice = (value: string | number) => {
    return parseFloat(value.toString()).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const formatQty = (value: string | number) => {
    return parseFloat(value.toString()).toLocaleString("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 4,
    });
  };

  return (
    <Card className="h-full">
      <CardBody className="p-4">
        <div className="flex flex-col gap-4 h-full">
          {/* Header */}
          <div className="flex flex-col gap-2">
            <h3 className="text-lg font-bold">Assets</h3>
            <Button
              size="sm"
              color="primary"
              variant="flat"
              onPress={handleGoToMarket}
              className="w-full"
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
                    d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6"
                  />
                </svg>
              }
            >
              Go to Market
            </Button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Spinner size="md" />
            </div>
          ) : (
            <div className="flex flex-col gap-3 overflow-y-auto flex-1">
              {/* Current Asset if not owned */}
              {!isCurrentlyOwned && (
                <>
                  <div className="border-b border-default-200 pb-3">
                    <div
                      className="p-3 rounded-lg bg-default-100 border-2 border-primary cursor-pointer hover:bg-default-200 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-sm text-primary">
                          {currentSymbol}
                        </span>
                        <Chip size="sm" variant="flat" color="default">
                          Viewing
                        </Chip>
                      </div>
                      <p className="text-xs text-default-500">
                        Currently viewing
                      </p>
                    </div>
                  </div>
                  <div className="border-b border-default-300 -mt-1 mb-1"></div>
                </>
              )}

              {/* Owned Assets */}
              {positions.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-default-500 mb-2">
                    No positions yet
                  </p>
                  <p className="text-xs text-default-400">
                    Start trading to see your assets here
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-default-500 font-semibold">
                      YOUR POSITIONS ({positions.length})
                    </span>
                  </div>
                  {positions.map((position) => {
                    const isCurrentAsset = position.symbol === currentSymbol;
                    const unrealizedPLPercent = parseFloat(position.unrealized_plpc);
                    const isPositive = unrealizedPLPercent >= 0;

                    return (
                      <div
                        key={position.symbol}
                        className={`p-3 rounded-lg cursor-pointer transition-all ${
                          isCurrentAsset
                            ? "bg-primary-50 dark:bg-primary-900/20 border-2 border-primary shadow-md"
                            : "bg-default-50 border border-default-200 hover:bg-default-100 hover:border-default-300"
                        }`}
                        onClick={() => handleAssetClick(position.symbol)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className={`font-bold text-sm ${isCurrentAsset ? "text-primary" : ""}`}>
                              {position.symbol}
                            </span>
                            {isCurrentAsset && (
                              <Chip size="sm" variant="flat" color="primary">
                                Current
                              </Chip>
                            )}
                          </div>
                          <Chip
                            size="sm"
                            variant="flat"
                            color={isPositive ? "success" : "danger"}
                            classNames={{
                              content: "text-xs font-semibold",
                            }}
                          >
                            {isPositive ? "+" : ""}
                            {unrealizedPLPercent.toFixed(2)}%
                          </Chip>
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="text-default-500">Qty:</span>
                            <span className="font-medium">
                              {formatQty(position.qty)}
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-default-500">Value:</span>
                            <span className="font-medium">
                              ${formatPrice(position.market_value)}
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-default-500">P/L:</span>
                            <span
                              className={`font-semibold ${
                                isPositive ? "text-success" : "text-danger"
                              }`}
                            >
                              {isPositive ? "+" : ""}$
                              {formatPrice(position.unrealized_pl)}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </>
              )}
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
