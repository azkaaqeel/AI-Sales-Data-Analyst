
import React from 'react';
import { KPI } from '../types';

interface KPICardProps {
  kpi: KPI;
}

const KPICard: React.FC<KPICardProps> = ({ kpi }) => {
  return (
    <div className="bg-gray-900/50 p-5 rounded-xl border border-gray-700 transition-all duration-300 hover:border-indigo-500 hover:shadow-lg hover:shadow-indigo-500/10">
      <p className="text-sm font-medium text-gray-400 mb-1">{kpi.name}</p>
      <h4 className="text-2xl font-bold text-white mb-2">{kpi.value}</h4>
      <p className="text-xs text-gray-500">{kpi.description}</p>
    </div>
  );
};

export default KPICard;
