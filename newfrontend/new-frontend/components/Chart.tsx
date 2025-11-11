
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartProps {
  data: {
    x_axis: string;
    y_axis: number;
  }[];
}

const Chart: React.FC<ChartProps> = ({ data }) => {
  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{
            top: 5,
            right: 20,
            left: -10,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
          <XAxis dataKey="x_axis" stroke="#9CA3AF" tick={{ fontSize: 12 }} />
          <YAxis stroke="#9CA3AF" tick={{ fontSize: 12 }} />
          <Tooltip 
            contentStyle={{ 
                backgroundColor: '#1F2937', 
                borderColor: '#4B5563', 
                color: '#E5E7EB' 
            }}
            itemStyle={{ color: '#E5E7EB' }}
            cursor={{fill: 'rgba(129, 140, 248, 0.1)'}}
          />
          <Legend wrapperStyle={{ fontSize: '14px' }} />
          <Line type="monotone" dataKey="y_axis" name="Value" stroke="#818CF8" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 8 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Chart;
