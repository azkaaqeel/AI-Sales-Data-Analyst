import React from 'react';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  fillColor?: string;
}

const Sparkline: React.FC<SparklineProps> = ({ 
  data, 
  width = 100, 
  height = 30,
  color = '#818CF8',
  fillColor = 'rgba(129, 140, 248, 0.1)'
}) => {
  if (!data || data.length < 2) {
    return null;
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1; // Avoid division by zero

  // Calculate points for the line
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  // Create area path (for fill)
  const areaPath = `M 0,${height} L ${points} L ${width},${height} Z`;
  
  // Create line path
  const linePath = `M ${points}`;

  return (
    <svg 
      width={width} 
      height={height} 
      className="inline-block"
      style={{ overflow: 'visible' }}
    >
      {/* Fill area */}
      <path
        d={areaPath}
        fill={fillColor}
      />
      
      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      
      {/* Last point dot */}
      {data.length > 0 && (
        <circle
          cx={(data.length - 1) / (data.length - 1) * width}
          cy={height - ((data[data.length - 1] - min) / range) * height}
          r="2.5"
          fill={color}
        />
      )}
    </svg>
  );
};

export default Sparkline;

