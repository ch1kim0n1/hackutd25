import { Card, CardBody, CardHeader } from "@heroui/card";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

interface BalanceDataPoint {
  date: Date;
  balance: number;
}

interface BalanceChartProps {
  data: BalanceDataPoint[];
  title?: string;
  width?: string;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload[0]) {
    const data = payload[0].payload;

    return (
      <div className="bg-gray-900 border-2 border-purple-500 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-300 mb-2 font-semibold">
          {new Date(data.date).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
        </p>
        <p className="text-sm font-mono font-bold text-white">
          <span className="text-green-400">
            $
            {data.balance.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        </p>
      </div>
    );
  }

  return null;
};

export const BalanceChart = ({
  data,
  title = "Net Worth Over Time",
  width = "100%",
}: BalanceChartProps) => {
  const chartData = data.map((d) => ({
    ...d,
    timestamp: new Date(d.date).getTime(),
  }));
  const values = data.map((d) => d.balance);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const padding = (maxValue - minValue) * 0.1;

  return (
    <div className="bg-background p-6 rounded-xl" style={{ width }}>
      <Card className="shadow-lg border border-divider">
        <CardHeader className="px-6 pt-6 pb-2">
          <h3 className="text-xl font-semibold text-foreground">{title}</h3>
        </CardHeader>
        <CardBody className="px-6 pb-6">
          <ResponsiveContainer height={350} width="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorBalance" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid
                opacity={0.5}
                stroke="#475569"
                strokeDasharray="3 3"
              />
              <XAxis
                dataKey="timestamp"
                stroke="#e2e8f0"
                style={{ fontSize: "12px", fontWeight: "500" }}
                tickFormatter={(ts) =>
                  new Date(ts).toLocaleDateString("en-US", {
                    month: "short",
                    year: "numeric",
                  })
                }
              />
              <YAxis
                domain={[minValue - padding, maxValue + padding]}
                stroke="#e2e8f0"
                style={{ fontSize: "12px", fontWeight: "500" }}
                tickFormatter={(val) =>
                  val >= 1000
                    ? `$${(val / 1000).toFixed(1)}K`
                    : `$${val.toFixed(0)}`
                }
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                activeDot={{
                  r: 7,
                  fill: "#a855f7",
                  stroke: "#ffffff",
                  strokeWidth: 3,
                }}
                dataKey="balance"
                dot={{
                  fill: "#a855f7",
                  strokeWidth: 2,
                  r: 5,
                  stroke: "#ffffff",
                }}
                fill="url(#colorBalance)"
                stroke="#a855f7"
                strokeWidth={3}
                type="monotone"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>
    </div>
  );
};

export default BalanceChart;
