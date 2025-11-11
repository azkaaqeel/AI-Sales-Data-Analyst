
import React, { useState } from 'react';
import { CleaningPlan, CleaningStep, ColumnCleaningPlan, GlobalStep } from '../types';
import { AnalyzeIcon } from './icons';

interface CleaningPlanViewProps {
  cleaningPlan: CleaningPlan;
  onApply: (selectedStepIds: string[]) => void;
}

const CleaningPlanView: React.FC<CleaningPlanViewProps> = ({ cleaningPlan, onApply }) => {
  // Safety check - ensure columns and global_steps exist
  if (!cleaningPlan.columns) {
    console.error('Invalid cleaning plan structure:', cleaningPlan);
    return (
      <div className="w-full max-w-4xl text-center p-8 bg-gray-800 border border-red-700 rounded-2xl shadow-lg">
        <h2 className="text-2xl font-bold text-red-400 mb-4">Error Loading Cleaning Plan</h2>
        <p className="text-gray-300 mb-4">
          The backend returned an invalid cleaning plan structure.
        </p>
        <pre className="text-left text-xs bg-gray-900 p-4 rounded overflow-auto max-h-60">
          {JSON.stringify(cleaningPlan, null, 2)}
        </pre>
      </div>
    );
  }

  // Initialize with all recommended steps selected
  const initialSelection = new Set<string>();
  (cleaningPlan.columns || []).forEach(col => {
    col.steps.forEach(step => {
      if (step.recommended) initialSelection.add(step.id);
    });
  });
  (cleaningPlan.global_steps || []).forEach(step => {
    if (step.recommended) initialSelection.add(step.id);
  });

  const [selectedSteps, setSelectedSteps] = useState<Set<string>>(initialSelection);

  const handleToggleStep = (stepId: string) => {
    const newSelection = new Set(selectedSteps);
    if (newSelection.has(stepId)) {
      newSelection.delete(stepId);
    } else {
      newSelection.add(stepId);
    }
    setSelectedSteps(newSelection);
  };

  const handleSubmit = () => {
    onApply(Array.from(selectedSteps));
  };

  const getStepIcon = (action: string) => {
    switch (action) {
      case 'parse_date':
        return '📅';
      case 'standardize_text':
        return '📝';
      case 'remove_duplicates':
        return '🔄';
      case 'fix_negative':
        return '➕';
      case 'handle_outliers':
        return '📊';
      case 'fill_missing':
        return '🔢';
      default:
        return '✨';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'date':
        return '📆';
      case 'revenue':
        return '💰';
      case 'quantity':
        return '🔢';
      case 'categorical':
        return '🏷️';
      case 'product':
        return '📦';
      case 'identifier':
        return '🔑';
      default:
        return '📊';
    }
  };

  const totalSteps = (cleaningPlan.columns || []).reduce((sum, col) => sum + col.steps.length, 0) + 
                     (cleaningPlan.global_steps || []).length;

  return (
    <div className="w-full max-w-5xl text-center p-8 bg-gray-800 border border-gray-700 rounded-2xl shadow-lg animate-fade-in">
      <h2 className="text-3xl font-bold text-white mb-2">Review Data Cleaning Plan</h2>
      <p className="text-gray-400 mb-2">
        We've analyzed {cleaningPlan.summary?.total_columns || cleaningPlan.columns?.length || 0} columns and identified {totalSteps} potential cleaning steps.
      </p>
      <p className="text-sm text-gray-500 mb-6">
        Select which steps you want to apply. Recommended steps are pre-selected.
      </p>

      {/* Summary Cards */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
          <div className="text-2xl font-bold text-white">{cleaningPlan.original_shape[0]}</div>
          <div className="text-xs text-gray-400 mt-1">Total Rows</div>
        </div>
        <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
          <div className="text-2xl font-bold text-white">{cleaningPlan.summary?.columns_needing_cleaning || cleaningPlan.columns?.length || 0}</div>
          <div className="text-xs text-gray-400 mt-1">Columns Need Cleaning</div>
        </div>
        <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
          <div className="text-2xl font-bold text-indigo-400">{selectedSteps.size}</div>
          <div className="text-xs text-gray-400 mt-1">Steps Selected</div>
        </div>
      </div>

      {/* Column-wise Cleaning Steps */}
      <div className="space-y-4 text-left mb-6 max-h-[500px] overflow-y-auto pr-2">
        {cleaningPlan.columns.map((columnPlan) => (
          <div
            key={columnPlan.column}
            className="p-4 bg-gray-900/50 rounded-lg border border-gray-700"
          >
            {/* Column Header */}
            <div className="flex items-center gap-3 mb-3 pb-2 border-b border-gray-700">
              <span className="text-2xl">{getTypeIcon(columnPlan.type)}</span>
              <div className="flex-grow">
                <h3 className="font-bold text-white text-lg">{columnPlan.column}</h3>
                <p className="text-xs text-gray-400">
                  Type: <span className="text-indigo-400">{columnPlan.type}</span>
                  {columnPlan.missing_count > 0 && (
                    <span className="ml-3 text-yellow-400">
                      ⚠️ {columnPlan.missing_count} missing values
                    </span>
                  )}
                </p>
              </div>
              <div className="text-xs text-gray-500">
                {columnPlan.steps.filter(s => selectedSteps.has(s.id)).length}/{columnPlan.steps.length} selected
              </div>
            </div>

            {/* Column Steps */}
            <div className="space-y-2">
              {columnPlan.steps.map((step) => (
                <label
                  key={step.id}
                  htmlFor={step.id}
                  className={`flex items-start p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedSteps.has(step.id)
                      ? 'bg-indigo-900/30 border-indigo-500'
                      : 'bg-gray-800/50 border-gray-600 hover:bg-gray-700/50'
                  }`}
                >
                  <input
                    type="checkbox"
                    id={step.id}
                    checked={selectedSteps.has(step.id)}
                    onChange={() => handleToggleStep(step.id)}
                    className="mt-0.5 h-4 w-4 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500 flex-shrink-0"
                  />
                  <div className="ml-3 flex-grow">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getStepIcon(step.action)}</span>
                      <span className="text-sm text-white">{step.reason}</span>
                      {step.recommended && (
                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">
                          Recommended
                        </span>
                      )}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        ))}

        {/* Global Steps (if any) */}
        {cleaningPlan.global_steps.length > 0 && (
          <div className="p-4 bg-gray-900/50 rounded-lg border border-yellow-700">
            <div className="flex items-center gap-3 mb-3 pb-2 border-b border-gray-700">
              <span className="text-2xl">🌐</span>
              <div className="flex-grow">
                <h3 className="font-bold text-white text-lg">Global Operations</h3>
                <p className="text-xs text-gray-400">Applied to entire dataset</p>
              </div>
            </div>

            <div className="space-y-2">
              {cleaningPlan.global_steps.map((step) => (
                <label
                  key={step.id}
                  htmlFor={step.id}
                  className={`flex items-start p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedSteps.has(step.id)
                      ? 'bg-indigo-900/30 border-indigo-500'
                      : 'bg-gray-800/50 border-gray-600 hover:bg-gray-700/50'
                  }`}
                >
                  <input
                    type="checkbox"
                    id={step.id}
                    checked={selectedSteps.has(step.id)}
                    onChange={() => handleToggleStep(step.id)}
                    className="mt-0.5 h-4 w-4 rounded border-gray-600 bg-gray-700 text-indigo-600 focus:ring-indigo-500 flex-shrink-0"
                  />
                  <div className="ml-3 flex-grow">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getStepIcon(step.action)}</span>
                      <span className="text-sm text-white">{step.reason}</span>
                      {step.recommended && (
                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">
                          Recommended
                        </span>
                      )}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Apply Button */}
      <button
        onClick={handleSubmit}
        disabled={selectedSteps.size === 0}
        className="w-full mt-4 flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-indigo-700 disabled:bg-gray-500 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:scale-100"
      >
        <AnalyzeIcon />
        Apply {selectedSteps.size} Selected Steps & Detect KPIs
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

export default CleaningPlanView;

