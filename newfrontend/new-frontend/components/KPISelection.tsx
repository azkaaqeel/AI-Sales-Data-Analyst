
import React, { useState } from 'react';
import { KPI } from '../types';
import { AnalyzeIcon } from './icons';

interface KPISelectionProps {
  kpis: KPI[];
  onGenerateReport: (selectedKpis: string[]) => void;
}

const KPISelection: React.FC<KPISelectionProps> = ({ kpis, onGenerateReport }) => {
  const [selectedKpis, setSelectedKpis] = useState<Set<string>>(new Set(kpis.map(k => k.name)));

  const handleToggleKpi = (kpiName: string) => {
    const newSelection = new Set(selectedKpis);
    if (newSelection.has(kpiName)) {
      newSelection.delete(kpiName);
    } else {
      newSelection.add(kpiName);
    }
    setSelectedKpis(newSelection);
  };

  const handleSubmit = () => {
    onGenerateReport(Array.from(selectedKpis));
  };

  return (
    <div className="w-full max-w-3xl text-center p-8 bg-gray-800 border border-gray-700 rounded-2xl shadow-lg animate-fade-in">
      <h2 className="text-3xl font-bold text-white mb-2">Select KPIs for Your Report</h2>
      <p className="text-gray-400 mb-8">Our AI has identified these potential KPIs from your data. Choose which ones to include in the analysis.</p>
      
      <div className="space-y-4 text-left mb-8">
        {kpis.map((kpi) => (
          <label 
            key={kpi.name} 
            htmlFor={kpi.name}
            className="flex items-start p-4 bg-gray-900/50 rounded-lg border border-gray-700 cursor-pointer hover:bg-gray-700/50 transition-colors"
          >
            <input
              type="checkbox"
              id={kpi.name}
              checked={selectedKpis.has(kpi.name)}
              onChange={() => handleToggleKpi(kpi.name)}
              className="mt-1 h-5 w-5 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500"
            />
            <div className="ml-4">
              <span className="font-semibold text-white">{kpi.name}</span>
              <p className="text-sm text-gray-400">{kpi.description}</p>
            </div>
          </label>
        ))}
      </div>

      <button
        onClick={handleSubmit}
        disabled={selectedKpis.size === 0}
        className="w-full mt-4 flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-indigo-700 disabled:bg-gray-500 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:scale-100"
      >
        <AnalyzeIcon />
        Generate Report ({selectedKpis.size} KPIs)
      </button>
       <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default KPISelection;
