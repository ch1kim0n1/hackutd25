import { useState, useEffect } from "react";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import SimpleTradingService from "@/services/SimpleTradingService";
import LocalStorageService from "@/services/LocalStorageService";
import type { Asset, Position } from "@/services/alpaca.types";

interface BuySellDialogProps {
  isOpen: boolean;
  onClose: () => void;
  asset: Asset;
  currentPrice: number;
  userPosition?: Position | null;
  onSuccess?: () => void;
}

type OrderMode = "buy" | "sell";

export function BuySellDialog({
  isOpen,
  onClose,
  asset,
  currentPrice,
  userPosition,
  onSuccess,
}: BuySellDialogProps) {
  const [mode, setMode] = useState<OrderMode>("buy");
  const [quantity, setQuantity] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [cash, setCash] = useState(0);

  useEffect(() => {
    if (isOpen) {
      loadAccountInfo();
    }
  }, [isOpen]);

  const loadAccountInfo = () => {
    try {
      const account = LocalStorageService.getAccount();
      setCash(parseFloat(account.cash));
    } catch (err) {
      console.error("Error loading account info:", err);
    }
  };

  const calculateEstimate = () => {
    const qty = parseFloat(quantity) || 0;
    return qty * currentPrice;
  };

  const calculateMaxShares = () => {
    if (mode === "sell" && userPosition) {
      return parseFloat(userPosition.qty);
    }
    if (mode === "buy") {
      return Math.floor(cash / currentPrice);
    }
    return 0;
  };

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);

    try {
      const qty = parseFloat(quantity);
      if (!qty || qty <= 0) {
        throw new Error("Please enter a valid quantity");
      }

      if (mode === "sell" && userPosition && qty > parseFloat(userPosition.qty)) {
        throw new Error("Cannot sell more shares than you own");
      }

      if (mode === "buy" && calculateEstimate() > cash) {
        throw new Error("Insufficient cash");
      }

      // Simple buy or sell
      if (mode === "buy") {
        await SimpleTradingService.buy(asset.symbol, qty);
      } else {
        await SimpleTradingService.sell(asset.symbol, qty);
      }

      setSuccess(true);
      
      setTimeout(() => {
        handleClose();
        onSuccess?.();
      }, 1500);
    } catch (err: any) {
      console.error("Error placing order:", err);
      setError(err.message || "Failed to place order");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setMode("buy");
    setQuantity("");
    setError(null);
    setSuccess(false);
    onClose();
  };

  const handleSetMaxQuantity = () => {
    const max = calculateMaxShares();
    setQuantity(max.toString());
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <Card className="w-full">
          <CardHeader className="flex justify-between items-center pb-4">
            <div>
              <h2 className="text-2xl font-bold">Trade {asset.symbol}</h2>
              <p className="text-sm text-default-500">{asset.name}</p>
            </div>
            <Button
              isIconOnly
              variant="light"
              onPress={handleClose}
              size="sm"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
                className="w-5 h-5"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </Button>
          </CardHeader>

          <CardBody className="gap-6">
            {success ? (
              <div className="text-center py-8">
                <div className="flex justify-center mb-4">
                  <div className="rounded-full bg-success/20 p-4">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                      className="w-12 h-12 text-success"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                </div>
                <h3 className="text-xl font-bold text-success mb-2">Order Placed Successfully!</h3>
                <p className="text-default-500">Your order has been submitted.</p>
              </div>
            ) : (
              <>
                {/* Current Price & Cash */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col p-4 bg-default-100 rounded-lg">
                    <span className="text-sm text-default-500">Current Price</span>
                    <span className="text-2xl font-bold">${currentPrice.toFixed(2)}</span>
                  </div>
                  <div className="flex flex-col p-4 bg-default-100 rounded-lg">
                    <span className="text-sm text-default-500">Available Cash</span>
                    <span className="text-2xl font-bold">${cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                  </div>
                </div>

                {/* User Position */}
                {userPosition && (
                  <div className="flex items-center justify-between p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg border border-primary">
                    <div>
                      <p className="text-xs text-default-500">Your Position</p>
                      <p className="font-semibold">
                        {parseFloat(userPosition.qty).toLocaleString()} shares
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-default-500">Market Value</p>
                      <p className="font-semibold">
                        ${parseFloat(userPosition.market_value).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </p>
                    </div>
                  </div>
                )}

                {/* Buy/Sell Toggle */}
                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    color={mode === "buy" ? "success" : "default"}
                    variant={mode === "buy" ? "solid" : "flat"}
                    onPress={() => setMode("buy")}
                    size="lg"
                  >
                    Buy
                  </Button>
                  <Button
                    className="flex-1"
                    color={mode === "sell" ? "danger" : "default"}
                    variant={mode === "sell" ? "solid" : "flat"}
                    onPress={() => setMode("sell")}
                    size="lg"
                    isDisabled={!userPosition || parseFloat(userPosition.qty) <= 0}
                  >
                    Sell
                  </Button>
                </div>

                {/* Quantity */}
                <div className="relative">
                  <Input
                    label="Number of Shares"
                    placeholder="0"
                    type="number"
                    value={quantity}
                    onValueChange={setQuantity}
                    description={`Max: ${calculateMaxShares().toLocaleString()} shares`}
                    endContent={
                      <Button
                        size="sm"
                        variant="flat"
                        color="primary"
                        onPress={handleSetMaxQuantity}
                        className="text-xs"
                      >
                        Max
                      </Button>
                    }
                  />
                </div>

                {/* Order Summary */}
                {quantity && parseFloat(quantity) > 0 && (
                  <div className="p-4 bg-default-100 rounded-lg space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-default-500">Total {mode === "buy" ? "Cost" : "Proceeds"}</span>
                      <span className="font-semibold">${calculateEstimate().toFixed(2)}</span>
                    </div>
                    {mode === "buy" && (
                      <div className="flex justify-between">
                        <span className="text-sm text-default-500">Cash After</span>
                        <span className="font-semibold">
                          ${(cash - calculateEstimate()).toFixed(2)}
                        </span>
                      </div>
                    )}
                    {mode === "sell" && (
                      <div className="flex justify-between">
                        <span className="text-sm text-default-500">Cash After</span>
                        <span className="font-semibold">
                          ${(cash + calculateEstimate()).toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Error Message */}
                {error && (
                  <div className="p-3 bg-danger/10 border border-danger rounded-lg">
                    <p className="text-sm text-danger">{error}</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  <Button
                    className="flex-1"
                    variant="flat"
                    onPress={handleClose}
                    isDisabled={loading}
                  >
                    Cancel
                  </Button>
                  <Button
                    className="flex-1"
                    color={mode === "buy" ? "success" : "danger"}
                    onPress={handleSubmit}
                    isLoading={loading}
                    isDisabled={loading || !quantity || parseFloat(quantity) <= 0}
                  >
                    {mode === "buy" ? "Buy Shares" : "Sell Shares"}
                  </Button>
                </div>
              </>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
