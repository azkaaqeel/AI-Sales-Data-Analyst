
import React from 'react';
import { DetectedKPI } from '../types';
import Sparkline from './Sparkline';

interface KPICardProps {
  kpi: DetectedKPI;
}

const KPICard: React.FC<KPICardProps> = ({ kpi }) => {
  // Determine if value is long (for truncation)
  const isLongValue = (kpi.value?.length || 0) > 50;
  
  // Build description - prioritize formula description for custom KPIs
  const getFullDescription = () => {
    // If it's a custom KPI with formula description, show that
    if (kpi.formula_description) {
      return `🧮 ${kpi.formula_description}`;
    }
    // Otherwise use the period comparison description
    return kpi.description;
  };
  
  return (
    <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 p-6 rounded-xl border border-gray-700 transition-all duration-300 hover:border-indigo-500 hover:shadow-lg hover:shadow-indigo-500/20 hover:scale-[1.02]">
      <div className="flex items-start justify-between mb-2">
        <p className="text-sm font-semibold text-indigo-400 uppercase tracking-wide">{kpi.name}</p>
      </div>
      
      <div className="flex items-end justify-between mb-3">
        <h4 className={`text-3xl font-bold text-white ${isLongValue ? 'text-lg' : ''}`} title={kpi.value}>
          {isLongValue ? `${kpi.value?.substring(0, 50)}...` : kpi.value}
        </h4>
        
        {kpi.sparkline && kpi.sparkline.length > 1 && (
          <div className="ml-4">
            <Sparkline data={kpi.sparkline} width={80} height={24} />
          </div>
        )}
      </div>
      
      <p className="text-xs text-gray-400 leading-relaxed">{getFullDescription()}</p>
    </div>
  );
};

export default KPICard;
