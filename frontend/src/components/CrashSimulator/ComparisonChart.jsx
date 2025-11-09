import React from 'react';
import { Line } from 'react-chartjs-2';

const ComparisonChart = ({ comparisonData }) => {
  if (!comparisonData || !comparisonData.dates) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">Load a scenario to see comparison chart</p>
      </div>
    );
  }

  const data = {
    labels: comparisonData.dates,
    datasets: [
      {
        label: 'APEX Multi-Agent',
        data: comparisonData.apex_values,
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.1,
      },
      {
        label: 'Buy & Hold SPY',
        data: comparisonData.buy_hold_values,
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Portfolio Value Comparison',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            label += '$' + context.parsed.y.toLocaleString('en-US', {
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            });
            return label;
          }
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: function(value) {
            return '$' + (value / 1000).toFixed(0) + 'k';
          }
        }
      },
      x: {
        ticks: {
          maxTicksLimit: 10,
        }
      }
    },
  };

  return (
    <div className="h-[400px]">
      <Line data={data} options={options} />
    </div>
  );
};

export default ComparisonChart;
