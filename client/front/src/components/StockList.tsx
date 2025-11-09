import React, { useRef, useEffect } from "react";
import { Chip } from "@heroui/chip";
import { Card, CardBody } from "@heroui/card";
import { Button } from "@heroui/button";
import { Asset } from "@/types";

interface StockListProps {
  assets: Asset[];
  onAssetClick?: (asset: Asset) => void;
  className?: string;
  highlightedSymbols?: string[]; // Symbols to highlight
  scrollToSymbol?: string | null; // Symbol to scroll to
  onHighlightDismiss?: () => void; // Callback when user dismisses highlight
}

export const StockList: React.FC<StockListProps> = ({ 
  assets, 
  onAssetClick,
  highlightedSymbols = [],
  scrollToSymbol = null,
  onHighlightDismiss
}) => {
  const assetRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Scroll to highlighted symbol
  useEffect(() => {
    if (scrollToSymbol && assetRefs.current[scrollToSymbol]) {
      assetRefs.current[scrollToSymbol]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }
  }, [scrollToSymbol]);

  const formatPrice = (price: number) => {
    return price >= 1 
      ? price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : price.toFixed(6);
  };

  const formatChange = (change: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  return (
    <Card
      className="shadow-lg h-full flex flex-col"
    >
      <CardBody className="p-4 flex flex-col h-full overflow-hidden">
        <div className="flex-shrink-0">
          {/* Header row */}
          <div className="grid grid-cols-12 gap-4 px-4 py-2 text-sm font-medium text-default-500">
            <div className="col-span-3">Asset</div>
            <div className="col-span-3 text-left">Name</div>
            <div className="col-span-3 text-right">Price</div>
            <div className="col-span-3 text-right">24h Change</div>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto space-y-2 mt-2">
          {/* Asset rows */}
          {assets.map((asset) => {
            const isHighlighted = highlightedSymbols.includes(asset.symbol);
            
            return (
              <div 
                key={asset.symbol}
                ref={(el) => assetRefs.current[asset.symbol] = el}
              >
                <Card
                  isPressable={!!onAssetClick}
                  className={`
                    hover:bg-default-100 
                    transition-all duration-300 w-full
                    ${isHighlighted ? 'ring-2 ring-secondary shadow-lg shadow-secondary/20' : ''}
                  `}
                  onPress={() => onAssetClick?.(asset)}
                >
                  <CardBody className="px-4 py-3">
                    <div className="grid grid-cols-12 gap-4 items-center">
                      {/* Symbol badge */}
                      <div className="col-span-3">
                        <Chip
                          variant="flat"
                          color={isHighlighted ? "secondary" : "primary"}
                          size="sm"
                          classNames={{
                            base: "font-mono font-bold",
                            content: "text-xs"
                          }}
                        >
                          {asset.symbol}
                        </Chip>
                      </div>

                      {/* Name */}
                      <div className="col-span-3 text-left">
                        <span className="text-sm font-medium text-foreground">
                          {asset.name}
                        </span>
                      </div>

                      {/* Price */}
                      <div className="col-span-3 text-right">
                        <span className="text-sm font-semibold text-foreground font-mono">
                          ${formatPrice(asset.price)}
                        </span>
                      </div>

                      {/* Daily change */}
                      <div className="col-span-3 text-right">
                        <Chip
                          variant="flat"
                          color={asset.dailyChange >= 0 ? "success" : "danger"}
                          size="sm"
                          classNames={{
                            base: "font-mono",
                            content: "text-xs font-semibold"
                          }}
                        >
                          {formatChange(asset.dailyChange)}
                        </Chip>
                      </div>
                    </div>
                  </CardBody>
                </Card>
                
                {/* AI Highlight Notice */}
                {isHighlighted && (
                  <div className="mt-2 p-3 bg-secondary/10 border border-secondary rounded-lg flex items-center justify-between">
                    <span className="text-sm text-secondary font-medium">
                      AI recommends reviewing this asset
                    </span>
                    <Button
                      size="sm"
                      variant="flat"
                      color="default"
                      onPress={() => {
                        onHighlightDismiss?.();
                      }}
                    >
                      Dismiss
                    </Button>
                  </div>
                )}
              </div>
            );
          })}

          {/* Empty state */}
          {assets.length === 0 && (
            <Card>
              <CardBody className="py-8">
                <p className="text-center text-default-400">No assets to display</p>
              </CardBody>
            </Card>
          )}
        </div>
        {/* End of scrollable content */}
      </CardBody>
    </Card>
  );
};

export default StockList;
