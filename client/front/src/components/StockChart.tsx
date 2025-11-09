import { Card, CardBody, CardHeader } from "@heroui/card";
import { Chip } from "@heroui/chip";
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";

interface StockDataPoint {
  date: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface StockChartProps {
  data: StockDataPoint[];
  symbol: string;
  currentPrice?: number;
  priceChange?: number;
  width?: string;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload[0]) {
    const data = payload[0].payload;
    const isGreen = data.close >= data.open;

    return (
      <div className="bg-gray-900 border-2 border-purple-500 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-300 mb-2 font-semibold">
          {new Date(data.date).toLocaleDateString()}
        </p>
        <div className="space-y-1 text-xs font-mono">
          <p className="text-white">
            Open:{" "}
            <span className="font-bold text-blue-400">
              ${data.open.toFixed(2)}
            </span>
          </p>
          <p className="text-white">
            High:{" "}
            <span className="font-bold text-green-400">
              ${data.high.toFixed(2)}
            </span>
          </p>
          <p className="text-white">
            Low:{" "}
            <span className="font-bold text-red-400">
              ${data.low.toFixed(2)}
            </span>
          </p>
          <p className="text-white">
            Close:{" "}
            <span
              className={`font-bold ${isGreen ? "text-green-400" : "text-red-400"}`}
            >
              ${data.close.toFixed(2)}
            </span>
          </p>
          {data.volume && (
            <p className="text-white">
              Volume:{" "}
              <span className="font-bold text-purple-400">
                {(data.volume / 1000000).toFixed(2)}M
              </span>
            </p>
          )}
          <p
            className={`text-xs mt-2 ${isGreen ? "text-green-400" : "text-red-400"}`}
          >
            {isGreen ? "▲" : "▼"}{" "}
            {Math.abs(((data.close - data.open) / data.open) * 100).toFixed(2)}%
          </p>
        </div>
      </div>
    );
  }

  return null;
};

// Custom candlestick renderer
const CandlestickBar = (props: any) => {
  const { x, y, width, height, payload } = props;

  if (!payload || !payload.open || !payload.close) return null;

  const isGreen = payload.close >= payload.open;
  const color = isGreen ? "#10b981" : "#ef4444";

  // Calculate body dimensions
  const bodyTop = Math.min(payload.open, payload.close);
  const bodyHeight = Math.abs(payload.close - payload.open);

  // Calculate wick dimensions
  const wickTop = payload.high;

  // Chart scale (this is approximate, Recharts handles actual scaling)
  const priceRange = payload.high - payload.low;
  const wickX = x + width / 2;

  return (
    <g>
      {/* High-Low Wick */}
      <line
        stroke={color}
        strokeWidth={1.5}
        x1={wickX}
        x2={wickX}
        y1={y}
        y2={y + height}
      />
      {/* Candle Body */}
      <rect
        fill={color}
        height={Math.max(height * (bodyHeight / priceRange), 1)}
        rx={1}
        stroke={color}
        strokeWidth={1}
        width={width * 0.6}
        x={x + width * 0.2}
        y={y + height * ((wickTop - bodyTop) / priceRange)}
      />
    </g>
  );
};

export const StockChart = ({
  data,
  symbol,
  currentPrice,
  priceChange,
  width = "100%",
}: StockChartProps) => {
  const formatChange = (change?: number) => {
    if (change === undefined) return "";
    const sign = change >= 0 ? "+" : "";

    return `${sign}${change.toFixed(2)}%`;
  };

  // Prepare chart data
  const chartData = data.map((d) => ({
    ...d,
    timestamp: new Date(d.date).getTime(),
    range: [d.low, d.high],
    isGreen: d.close >= d.open,
  }));

  return (
    <Card
      className="shadow-lg border border-divider h-full flex flex-col bg-gradient-to-br from-gray-900 via-gray-900 to-black"
      style={{ width }}
    >
      <CardHeader className="px-6 pt-6 pb-3 flex-shrink-0 border-b border-gray-800">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-3">
            <Chip
              classNames={{ base: "font-mono font-bold", content: "text-xs" }}
              color="primary"
              size="sm"
              variant="flat"
            >
              {symbol}
            </Chip>
            {currentPrice && (
              <span className="text-2xl font-bold text-white font-mono">
                ${currentPrice.toFixed(2)}
              </span>
            )}
          </div>
          {priceChange !== undefined && (
            <Chip
              classNames={{
                base: "font-mono",
                content: "text-xs font-semibold",
              }}
              color={priceChange >= 0 ? "success" : "danger"}
              size="sm"
              variant="flat"
            >
              {formatChange(priceChange)}
            </Chip>
          )}
        </div>
      </CardHeader>
      <CardBody className="px-4 pb-4 flex-1 min-h-0">
        {data.length > 0 ? (
          <ResponsiveContainer height="100%" width="100%">
            <ComposedChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="volumeGradient" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.05} />
                </linearGradient>
              </defs>

              <CartesianGrid
                opacity={0.2}
                stroke="#374151"
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                axisLine={{ stroke: "#374151" }}
                dataKey="timestamp"
                stroke="#6b7280"
                style={{ fontSize: "10px", fontWeight: "400" }}
                tick={{ fill: "#9ca3af" }}
                tickFormatter={(ts) =>
                  new Date(ts).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                  })
                }
              />

              <YAxis
                axisLine={{ stroke: "#374151" }}
                domain={["dataMin - 2", "dataMax + 2"]}
                orientation="right"
                stroke="#6b7280"
                style={{ fontSize: "10px", fontWeight: "400" }}
                tick={{ fill: "#9ca3af" }}
                tickFormatter={(val) => `$${val.toFixed(0)}`}
              />

              <Tooltip
                content={<CustomTooltip />}
                cursor={{
                  stroke: "#6366f1",
                  strokeWidth: 1,
                  strokeDasharray: "3 3",
                }}
              />

              {/* Price bars (candlesticks) */}
              <Bar
                dataKey="high"
                isAnimationActive={false}
                shape={<CandlestickBar />}
              >
                {chartData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} />
                ))}
              </Bar>

              {/* Volume bars at bottom - 20% of chart height */}
              <Bar dataKey="volume" maxBarSize={4} yAxisId="volume">
                {chartData.map((entry, index) => (
                  <Cell
                    key={`vol-${index}`}
                    fill={entry.isGreen ? "#10b98180" : "#ef444480"}
                  />
                ))}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">No chart data available</p>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default StockChart;
