import { Card, CardBody, CardHeader } from "@heroui/card";
import { Chip } from "@heroui/chip";
import ReactApexChart from 'react-apexcharts';
import { ApexOptions } from 'apexcharts';

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

export const StockChart = ({ data, symbol, currentPrice, priceChange, width = "100%" }: StockChartProps) => {
  const formatChange = (change?: number) => {
    if (change === undefined) return '';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  // Prepare data for ApexCharts candlestick format
  const candlestickData = data.map(d => ({
    x: new Date(d.date).getTime(),
    y: [d.open, d.high, d.low, d.close]
  }));

  const lineData = data.map(d => ({
    x: new Date(d.date).getTime(),
    y: d.close
  }));

  const volumeData = data.map(d => ({
    x: new Date(d.date).getTime(),
    y: d.volume || 0
  }));

  const chartOptions: ApexOptions = {
    chart: {
      type: 'candlestick',
      height: 350,
      background: 'transparent',
      toolbar: {
        show: false
      },
      zoom: {
        enabled: true
      }
    },
    theme: {
      mode: 'dark'
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#10b981',
          downward: '#ef4444'
        },
        wick: {
          useFillColor: true
        }
      },
      bar: {
        columnWidth: '95%'
      }
    },
    stroke: {
      width: [0, 2],
      curve: 'smooth'
    },
    xaxis: {
      type: 'datetime',
      labels: {
        style: {
          colors: '#9ca3af',
          fontSize: '10px'
        },
        datetimeFormatter: {
          year: 'yyyy',
          month: "MMM 'yy",
          day: 'dd MMM',
          hour: 'HH:mm'
        }
      },
      axisBorder: {
        color: '#374151'
      },
      axisTicks: {
        color: '#374151'
      }
    },
    yaxis: {
      tooltip: {
        enabled: true
      },
      labels: {
        style: {
          colors: '#9ca3af',
          fontSize: '10px'
        },
        formatter: (val) => `$${val.toFixed(2)}`
      }
    },
    grid: {
      borderColor: '#374151',
      strokeDashArray: 3,
      xaxis: {
        lines: {
          show: false
        }
      }
    },
    tooltip: {
      theme: 'dark',
      custom: function({ seriesIndex, dataPointIndex, w }) {
        const o = w.globals.seriesCandleO[seriesIndex][dataPointIndex];
        const h = w.globals.seriesCandleH[seriesIndex][dataPointIndex];
        const l = w.globals.seriesCandleL[seriesIndex][dataPointIndex];
        const c = w.globals.seriesCandleC[seriesIndex][dataPointIndex];
        const isGreen = c >= o;
        const change = ((c - o) / o * 100).toFixed(2);
        const date = new Date(w.globals.seriesX[seriesIndex][dataPointIndex]);
        
        return `
          <div class="bg-gray-900 border-2 border-purple-500 rounded-lg p-3 shadow-xl">
            <p class="text-xs text-gray-300 mb-2 font-semibold">${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</p>
            <div class="space-y-1 text-xs font-mono">
              <p class="text-white">Open: <span class="font-bold text-blue-400">$${o.toFixed(2)}</span></p>
              <p class="text-white">High: <span class="font-bold text-green-400">$${h.toFixed(2)}</span></p>
              <p class="text-white">Low: <span class="font-bold text-red-400">$${l.toFixed(2)}</span></p>
              <p class="text-white">Close: <span class="font-bold ${isGreen ? 'text-green-400' : 'text-red-400'}">$${c.toFixed(2)}</span></p>
              <p class="text-xs mt-2 ${isGreen ? 'text-green-400' : 'text-red-400'}">
                ${isGreen ? '▲' : '▼'} ${Math.abs(parseFloat(change))}%
              </p>
            </div>
          </div>
        `;
      }
    }
  };

  const volumeOptions: ApexOptions = {
    chart: {
      type: 'bar',
      height: 160,
      background: 'transparent',
      toolbar: {
        show: false
      }
    },
    theme: {
      mode: 'dark'
    },
    plotOptions: {
      bar: {
        colors: {
          ranges: [{
            from: 0,
            to: Number.MAX_VALUE,
            color: '#6366f1'
          }]
        },
        columnWidth: '80%',
      }
    },
    dataLabels: {
      enabled: false
    },
    xaxis: {
      type: 'datetime',
      labels: {
        show: false
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    yaxis: {
      labels: {
        style: {
          colors: '#9ca3af',
          fontSize: '9px'
        },
        formatter: (val) => (val / 1000000).toFixed(1) + 'M'
      }
    },
    grid: {
      show: false
    },
    tooltip: {
      theme: 'dark',
      x: {
        format: 'dd MMM yyyy'
      },
      y: {
        formatter: (val) => (val / 1000000).toFixed(2) + 'M shares'
      }
    }
  };

  const series = [{
    name: symbol,
    type: 'candlestick',
    data: candlestickData
  }, {
    name: 'Trend',
    type: 'line',
    data: lineData
  }];

  const volumeSeries = [{
    name: 'Volume',
    data: volumeData
  }];

  return (
    <Card className="shadow-lg border border-divider h-full flex flex-col bg-gradient-to-br from-gray-900 via-gray-900 to-black" style={{ width }}>
      <CardHeader className="px-6 pt-6 pb-3 flex-shrink-0 border-b border-gray-800">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-3">
            <Chip variant="flat" color="primary" size="sm" classNames={{ base: "font-mono font-bold", content: "text-xs" }}>{symbol}</Chip>
            {currentPrice && <span className="text-2xl font-bold text-white font-mono">${currentPrice.toFixed(2)}</span>}
          </div>
          {priceChange !== undefined && (
            <Chip variant="flat" color={priceChange >= 0 ? "success" : "danger"} size="sm" classNames={{ base: "font-mono", content: "text-xs font-semibold" }}>
              {formatChange(priceChange)}
            </Chip>
          )}
        </div>
      </CardHeader>
      <CardBody className="px-4 pb-4 flex-1 min-h-0">
        {data.length > 0 ? (
          <div className="h-full flex flex-col">
            <div className="flex-1">
              <ReactApexChart 
                options={chartOptions} 
                series={series} 
                type="candlestick" 
                height="100%" 
              />
            </div>
            {data.some(d => d.volume) && (
              <div className="h-32">
                <ReactApexChart 
                  options={volumeOptions} 
                  series={volumeSeries} 
                  type="bar" 
                  height="100%" 
                />
              </div>
            )}
          </div>
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
