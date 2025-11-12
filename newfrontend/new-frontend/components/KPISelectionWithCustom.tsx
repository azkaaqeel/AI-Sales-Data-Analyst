
import React, { useState } from 'react';
import { DetectedKPI, CustomKPI } from '../types';
import { AnalyzeIcon } from './icons';
import CustomKPIModal from './CustomKPIModal';

interface KPISelectionWithCustomProps {
  detectedKpis: DetectedKPI[];
  fileId: string;
  onGenerateReport: (selectedKpis: string[], customKpis: CustomKPI[]) => void;
}

const KPISelectionWithCustom: React.FC<KPISelectionWithCustomProps> = ({ 
  detectedKpis,
  fileId,
  onGenerateReport 
}) => {
  const [selectedKpis, setSelectedKpis] = useState<Set<string>>(
    new Set(detectedKpis.map(k => k.name))
  );
  
  const [customKpis, setCustomKpis] = useState<CustomKPI[]>([]);
  const [showCustomModal, setShowCustomModal] = useState(false);

  const handleToggleKpi = (kpiName: string) => {
    const newSelection = new Set(selectedKpis);
    if (newSelection.has(kpiName)) {
      newSelection.delete(kpiName);
    } else {
      newSelection.add(kpiName);
    }
    setSelectedKpis(newSelection);
  };

  const handleAddCustomKpi = (kpi: any) => {
    const customKpi: CustomKPI = {
      name: kpi.name,
      formula: kpi.formula,
      description: kpi.description
    };
    
    setCustomKpis([...customKpis, customKpi]);
    setSelectedKpis(new Set([...selectedKpis, kpi.name]));
  };

  const handleRemoveCustomKpi = (kpiName: string) => {
    setCustomKpis(customKpis.filter(k => k.name !== kpiName));
    const newSelection = new Set(selectedKpis);
    newSelection.delete(kpiName);
    setSelectedKpis(newSelection);
  };

  const handleSubmit = () => {
    onGenerateReport(Array.from(selectedKpis), customKpis);
  };

  const totalSelected = selectedKpis.size;

  return (
    <div className="w-full max-w-4xl text-center p-8 bg-gray-800 border border-gray-700 rounded-2xl shadow-lg animate-fade-in">
      <h2 className="text-3xl font-bold text-white mb-2">Select & Customize KPIs</h2>
      <p className="text-gray-400 mb-8">
        Choose from detected KPIs and add your own custom calculations.
      </p>

      {/* Detected KPIs */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold text-white text-left mb-4">
          📊 Detected KPIs ({detectedKpis.length})
        </h3>
        <div className="space-y-3 text-left max-h-64 overflow-y-auto">
          {detectedKpis.map((kpi) => (
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
                <p className="text-sm text-gray-400 mt-1">{kpi.description}</p>
                {kpi.formula && (
                  <p className="text-xs text-gray-500 mt-1 font-mono bg-gray-800 px-2 py-1 rounded">
                    {kpi.formula}
                  </p>
                )}
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Custom KPIs */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white text-left">
            ✨ Custom KPIs ({customKpis.length})
          </h3>
          <button
            onClick={() => setShowCustomModal(true)}
            className="text-sm bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
          >
            <span className="text-lg">🧮</span>
            + Create Custom KPI
          </button>
        </div>

        {/* Custom KPI Modal */}
        {showCustomModal && (
          <CustomKPIModal
            fileId={fileId}
            onAdd={handleAddCustomKpi}
            onClose={() => setShowCustomModal(false)}
          />
        )}

        {/* Custom KPI List */}
        {customKpis.length > 0 && (
          <div className="space-y-2 text-left">
            {customKpis.map((kpi) => (
              <div
                key={kpi.name}
                className="flex items-start justify-between p-3 bg-indigo-900/20 rounded-lg border border-indigo-700"
              >
                <div className="flex-grow">
                  <span className="font-semibold text-white">{kpi.name}</span>
                  <p className="text-xs text-gray-400 mt-0.5 font-mono bg-gray-800 px-2 py-1 rounded inline-block">
                    {kpi.formula}
                  </p>
                  {kpi.description && (
                    <p className="text-sm text-gray-400 mt-1">{kpi.description}</p>
                  )}
                </div>
                <button
                  onClick={() => handleRemoveCustomKpi(kpi.name)}
                  className="ml-3 text-red-400 hover:text-red-300 text-sm"
                  title="Remove"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Summary & Submit */}
      <div className="mb-6 p-3 bg-indigo-900/20 rounded-lg border border-indigo-700">
        <p className="text-sm text-indigo-200">
          <span className="font-semibold">{totalSelected}</span> KPI(s) selected
          {customKpis.length > 0 && (
            <span className="ml-2">
              (including <span className="font-semibold">{customKpis.length}</span> custom)
            </span>
          )}
        </p>
      </div>

      <button
        onClick={handleSubmit}
        disabled={totalSelected === 0}
        className="w-full mt-4 flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-indigo-700 disabled:bg-gray-500 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:scale-100"
      >
        <AnalyzeIcon />
        Generate Report ({totalSelected} KPI{totalSelected !== 1 ? 's' : ''})
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

export default KPISelectionWithCustom;

