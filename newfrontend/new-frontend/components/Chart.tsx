
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart, ReferenceLine, ReferenceDot } from 'recharts';

interface ChartProps {
  data: {
    x_axis: string;
    y_axis: number;
  }[];
  metricName?: string;
  holidays?: {
    date: string;
    name: string;
    icon: string;
    impact: string;
  }[];
  anomalies?: number[];
}

const Chart: React.FC<ChartProps> = ({ data, metricName, holidays, anomalies }) => {
  // Format Y-axis values (abbreviate large numbers)
  const formatYAxis = (value: number) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(0);
  };

  // Custom tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ 
          backgroundColor: '#1F2937', 
          border: '1px solid #6366F1',
          borderRadius: '8px',
          color: '#E5E7EB',
          padding: '12px'
        }}>
          <p style={{ marginBottom: '4px', color: '#E5E7EB' }}>{label}</p>
          <p style={{ color: '#A5B4FC', fontWeight: 'bold' }}>
            {metricName || 'Value'}: {payload[0].value.toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-80 bg-gray-900/30 p-4 rounded-lg">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{
            top: 10,
            right: 30,
            left: 0,
            bottom: 5,
          }}
        >
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#818CF8" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#818CF8" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
          <XAxis 
            dataKey="x_axis"
            label={{ value: 'Period', position: 'insideBottom', offset: -5, style: { fill: '#9CA3AF', fontSize: 12 } }}
            stroke="#9CA3AF" 
            tick={{ fontSize: 11, fill: '#9CA3AF' }}
            tickLine={{ stroke: '#4B5563' }}
          />
          <YAxis 
            label={{ value: metricName || 'Value', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF', fontSize: 12 } }}
            stroke="#9CA3AF" 
            tick={{ fontSize: 11, fill: '#9CA3AF' }}
            tickLine={{ stroke: '#4B5563' }}
            tickFormatter={formatYAxis}
          />
          <Tooltip 
            content={<CustomTooltip />}
            cursor={{fill: 'rgba(129, 140, 248, 0.1)'}}
          />
          <Legend 
            wrapperStyle={{ fontSize: '13px', color: '#9CA3AF', paddingTop: '16px' }}
            iconType="line"
          />
          <Area 
            type="monotone" 
            dataKey="y_axis" 
            fill="url(#colorValue)" 
            stroke="none"
          />
          
          <Line 
            type="monotone" 
            dataKey="y_axis" 
            name={metricName || "Value"}
            stroke="#818CF8" 
            strokeWidth={3} 
            dot={(props: any) => {
              const { cx, cy, index } = props;
              const isAnomaly = anomalies && anomalies.includes(index);
              
              if (isAnomaly) {
                return (
                  <g>
                    <circle cx={cx} cy={cy} r={8} fill="#EF4444" stroke="#FEE2E2" strokeWidth={2} />
                    <circle cx={cx} cy={cy} r={3} fill="#FEE2E2" />
                  </g>
                );
              }
              
              return <circle cx={cx} cy={cy} r={5} fill="#818CF8" stroke="#1F2937" strokeWidth={2} />;
            }}
            activeDot={{ r: 7, fill: '#6366F1', stroke: '#A5B4FC', strokeWidth: 2 }} 
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Chart;
