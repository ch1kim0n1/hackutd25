import { ChartComponent, SeriesCollectionDirective, SeriesDirective, Inject, DateTime, Tooltip, Legend, SplineAreaSeries } from '@syncfusion/ej2-react-charts';
import { Card, CardBody, CardHeader } from "@heroui/card";

interface BalanceDataPoint {
  date: Date;
  balance: number;
}

interface BalanceChartProps {
  data: BalanceDataPoint[];
  title?: string;
  width?: string;
}

export const BalanceChart = ({ 
  data, 
  title = "Net Worth Over Time",
  width = "100%" 
}: BalanceChartProps) => {
  const primaryxAxis: any = {
    valueType: 'DateTime',
    labelFormat: 'MMM yyyy',
    majorGridLines: { width: 0 },
    edgeLabelPlacement: 'Shift',
    labelStyle: { color: '#94a3b8' }
  };

  const primaryyAxis: any = {
    labelFormat: '${value}',
    lineStyle: { width: 0 },
    majorTickLines: { width: 0 },
    minorTickLines: { width: 0 },
    labelStyle: { color: '#94a3b8' }
  };

  const chartArea = {
    border: { width: 0 }
  };

  const marker = {
    visible: true,
    width: 8,
    height: 8,
    fill: '#7c3aed',
    border: { width: 2, color: '#ffffff' }
  };

  const tooltip = {
    enable: true,
    format: '${point.x} : <b>${point.y}</b>',
    shared: false
  };

  return (
    <div className="bg-background p-6 rounded-xl" style={{ width }}>
      <Card className="shadow-lg border border-divider">
        <CardHeader className="px-6 pt-6 pb-2">
          <h3 className="text-xl font-semibold text-foreground">{title}</h3>
        </CardHeader>
        <CardBody className="px-6 pb-6">
          <ChartComponent
            id="balance-chart"
            primaryXAxis={primaryxAxis}
            primaryYAxis={primaryyAxis}
            tooltip={tooltip}
            chartArea={chartArea}
            background="transparent"
            height="350px"
          >
            <Inject services={[SplineAreaSeries, DateTime, Tooltip, Legend]} />
            <SeriesCollectionDirective>
              <SeriesDirective
                dataSource={data}
                xName="date"
                yName="balance"
                name="Balance"
                type="SplineArea"
                fill="#7c3aed"
                opacity={0.3}
                border={{ width: 3, color: '#7c3aed' }}
                marker={marker}
              />
            </SeriesCollectionDirective>
          </ChartComponent>
        </CardBody>
      </Card>
    </div>
  );
};

export default BalanceChart;
