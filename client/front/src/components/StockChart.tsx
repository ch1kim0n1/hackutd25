import { ChartComponent, SeriesCollectionDirective, SeriesDirective, Inject, DateTime, CandleSeries, Tooltip, Crosshair, Zoom, LineSeries } from '@syncfusion/ej2-react-charts';
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Chip } from "@heroui/chip";

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

export const StockChart = ({ 
  data, 
  symbol,
  currentPrice,
  priceChange,
  width = "100%" 
}: StockChartProps) => {
  const primaryxAxis: any = {
    valueType: 'DateTime',
    labelFormat: 'MMM dd',
    majorGridLines: { width: 0 },
    crosshairTooltip: { enable: true },
    labelStyle: { color: '#94a3b8' }
  };

  const primaryyAxis: any = {
    title: 'Price (USD)',
    labelFormat: '${value}',
    lineStyle: { width: 0 },
    majorTickLines: { width: 0 },
    rangePadding: 'None',
    labelStyle: { color: '#94a3b8' }
  };

  const chartArea = {
    border: { width: 0 }
  };

  const tooltip = {
    enable: true,
    shared: true,
    format: '<b>${point.x}</b><br/>Open: <b>${point.open}</b><br/>High: <b>${point.high}</b><br/>Low: <b>${point.low}</b><br/>Close: <b>${point.close}</b>'
  };

  const crosshair: any = {
    enable: true,
    lineType: 'Vertical',
    line: { color: '#7c3aed', width: 1 }
  };

  const zoomSettings: any = {
    enableSelectionZooming: true,
    enablePinchZooming: true,
    enableMouseWheelZooming: true,
    mode: 'X'
  };

  const formatChange = (change?: number) => {
    if (change === undefined) return '';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  return (
    <div className="bg-background p-6 rounded-xl" style={{ width }}>
      <Card className="shadow-lg border border-divider">
        <CardHeader className="px-6 pt-6 pb-2 flex flex-col gap-2">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <Chip
                variant="flat"
                color="primary"
                size="sm"
                classNames={{
                  base: "font-mono font-bold",
                  content: "text-xs"
                }}
              >
                {symbol}
              </Chip>
              {currentPrice && (
                <span className="text-2xl font-bold text-foreground font-mono">
                  ${currentPrice.toFixed(2)}
                </span>
              )}
            </div>
            {priceChange !== undefined && (
              <Chip
                variant="flat"
                color={priceChange >= 0 ? "success" : "danger"}
                size="sm"
                classNames={{
                  base: "font-mono",
                  content: "text-xs font-semibold"
                }}
              >
                {formatChange(priceChange)}
              </Chip>
            )}
          </div>
        </CardHeader>
        <CardBody className="px-6 pb-6">
          <ChartComponent
            id={`stock-chart-${symbol}`}
            primaryXAxis={primaryxAxis}
            primaryYAxis={primaryyAxis}
            tooltip={tooltip}
            crosshair={crosshair}
            zoomSettings={zoomSettings}
            chartArea={chartArea}
            background="transparent"
            height="400px"
          >
            <Inject services={[CandleSeries, DateTime, Tooltip, Crosshair, Zoom, LineSeries]} />
            <SeriesCollectionDirective>
              <SeriesDirective
                dataSource={data}
                xName="date"
                high="high"
                low="low"
                open="open"
                close="close"
                type="Candle"
                bearFillColor="#ef4444"
                bullFillColor="#22c55e"
                enableSolidCandles={true}
                width={1.5}
                name={symbol}
              />
            </SeriesCollectionDirective>
          </ChartComponent>
        </CardBody>
      </Card>
    </div>
  );
};

export default StockChart;
