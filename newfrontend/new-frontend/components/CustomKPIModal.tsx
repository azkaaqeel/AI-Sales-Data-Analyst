import React, { useState, useEffect } from 'react';
import { getCustomKPIColumns, calculateCustomKPI } from '../services/backendService';

interface CustomKPIModalProps {
  fileId: string;
  onAdd: (kpi: any) => void;
  onClose: () => void;
}

interface Template {
  name: string;
  formula: string;
  description: string;
  requires: string[];
}

const CustomKPIModal: React.FC<CustomKPIModalProps> = ({ fileId, onAdd, onClose }) => {
  const [columns, setColumns] = useState<{ numeric: string[], countable: string[], all: string[] }>({ numeric: [], countable: [], all: [] });
  const [templates, setTemplates] = useState<Template[]>([]);
  const [kpiName, setKpiName] = useState('');
  const [formula, setFormula] = useState('');
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadColumnsAndTemplates();
  }, [fileId]);

  const loadColumnsAndTemplates = async () => {
    try {
      setLoading(true);
      const data = await getCustomKPIColumns(fileId);
      setColumns(data.columns);
      setTemplates(data.templates);
    } catch (err: any) {
      setError(err.message || 'Failed to load columns');
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = (template: Template) => {
    setKpiName(template.name);
    setFormula(template.formula);
    setError('');
  };

  // Insert operations/aggregations/columns by clicking
  const insertToken = (token: string) => {
    setFormula(formula + token);
  };

  const clearFormula = () => {
    setFormula('');
  };

  const deleteLastChar = () => {
    setFormula(formula.slice(0, -1));
  };

  const handleCalculate = async () => {
    if (!kpiName.trim() || !formula.trim()) {
      setError('Please provide both KPI name and build a formula');
      return;
    }

    try {
      setCalculating(true);
      setError('');
      const result = await calculateCustomKPI(fileId, kpiName, formula);
      
      if (result.success) {
        onAdd(result.kpi);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to calculate KPI');
    } finally {
      setCalculating(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-gray-900 p-8 rounded-2xl border border-gray-700 max-w-2xl w-full mx-4">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            <span className="ml-3 text-gray-300">Loading columns...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-8 rounded-2xl border border-gray-700 max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="text-3xl">🧮</span>
            Build Custom KPI
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* KPI Name Input */}
        <div className="mb-4">
          <label className="block text-sm font-semibold text-gray-300 mb-2">
            KPI Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={kpiName}
            onChange={(e) => setKpiName(e.target.value)}
            placeholder="e.g., Profit Margin"
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* Formula Display */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-semibold text-gray-300">
              Formula <span className="text-red-400">*</span>
            </label>
            <div className="flex gap-2">
              <button
                onClick={deleteLastChar}
                className="px-3 py-1 text-xs bg-red-600/20 hover:bg-red-600/40 border border-red-500/50 rounded text-red-300 transition-all"
                title="Delete last character"
              >
                ← Delete
              </button>
              <button
                onClick={clearFormula}
                className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded text-gray-300 transition-all"
              >
                Clear All
              </button>
            </div>
          </div>
          <div className="w-full min-h-[80px] px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white font-mono text-sm break-all">
            {formula || <span className="text-gray-500">Click buttons below to build your formula...</span>}
          </div>
        </div>

        {/* Formula Builder - Clickable Buttons */}
        <div className="mb-6 space-y-4">
          {/* Numeric Columns */}
          {columns.numeric && columns.numeric.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                💰 Numeric Columns (for sum, avg, min, max)
              </h4>
              <div className="flex flex-wrap gap-2">
                {columns.numeric.map((col, idx) => (
                  <button
                    key={idx}
                    onClick={() => insertToken(`"${col}"`)}
                    className="px-3 py-2 bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/50 rounded text-sm text-blue-300 transition-all font-mono"
                  >
                    {col}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Countable Columns (IDs, Categories) */}
          {columns.countable && columns.countable.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                🏷️ All Columns (for count operations)
              </h4>
              <div className="flex flex-wrap gap-2">
                {columns.countable.filter(col => !columns.numeric.includes(col)).map((col, idx) => (
                  <button
                    key={idx}
                    onClick={() => insertToken(`"${col}"`)}
                    className="px-3 py-2 bg-cyan-600/20 hover:bg-cyan-600/40 border border-cyan-500/50 rounded text-sm text-cyan-300 transition-all font-mono"
                  >
                    {col}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Aggregations */}
          <div>
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
              🔢 Aggregations
            </h4>
            
            {/* Numeric Aggregations */}
            <div className="mb-3">
              <p className="text-[10px] text-blue-400 mb-1.5">For Numeric Columns Only:</p>
              <div className="flex flex-wrap gap-2">
                {['sum', 'avg', 'min', 'max', 'median'].map((agg, idx) => (
                  <button
                    key={idx}
                    onClick={() => insertToken(`${agg}(`)}
                    className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/50 rounded text-sm text-blue-300 transition-all font-semibold"
                    title={`${agg.charAt(0).toUpperCase() + agg.slice(1)} - numeric columns only`}
                  >
                    {agg}()
                  </button>
                ))}
              </div>
            </div>
            
            {/* Universal Aggregations */}
            <div>
              <p className="text-[10px] text-purple-400 mb-1.5">For Any Column:</p>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => insertToken(`count(`)}
                  className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/50 rounded text-sm text-purple-300 transition-all font-semibold"
                  title="Count of all non-null rows"
                >
                  count()
                </button>
                <button
                  onClick={() => insertToken(`nunique(`)}
                  className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/40 border border-purple-500/50 rounded text-sm text-purple-300 transition-all font-semibold"
                  title="Count of unique/distinct values"
                >
                  nunique()
                </button>
              </div>
            </div>
          </div>

          {/* Operations */}
          <div>
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
              ➕ Operations
            </h4>
            <div className="flex flex-wrap gap-2">
              {[
                { label: '+', token: ' + ' },
                { label: '−', token: ' - ' },
                { label: '×', token: ' * ' },
                { label: '÷', token: ' / ' },
                { label: '(', token: '(' },
                { label: ')', token: ')' },
                { label: '*100', token: ' * 100' },
              ].map((op, idx) => (
                <button
                  key={idx}
                  onClick={() => insertToken(op.token)}
                  className="px-4 py-2 bg-green-600/20 hover:bg-green-600/40 border border-green-500/50 rounded text-sm text-green-300 transition-all font-bold"
                >
                  {op.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
            <p className="text-sm text-red-400">⚠️ {error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleCalculate}
            disabled={calculating || !kpiName.trim() || !formula.trim()}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {calculating ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Calculating...
              </span>
            ) : (
              'Calculate & Add KPI'
            )}
          </button>
          <button
            onClick={onClose}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition-all"
          >
            Cancel
          </button>
        </div>

        {/* Help Text */}
        <div className="mt-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">💡 How It Works</h4>
          <ul className="text-xs text-gray-400 space-y-1">
            <li>• <strong className="text-blue-300">sum(), avg(), min(), max(), median()</strong> - Only work on numeric columns (Revenue, Quantity, Price)</li>
            <li>• <strong className="text-purple-300">count()</strong> - Counts all rows with non-null values (works on any column)</li>
            <li>• <strong className="text-purple-300">nunique()</strong> - Counts unique/distinct values (use for Category, Product, Customer ID)</li>
            <li>• Date columns excluded - they're used for time periods, not calculations</li>
            <li>• <strong className="text-red-400">Validation</strong>: System will reject invalid operations (e.g., sum on text columns)</li>
          </ul>
          <div className="mt-3 pt-3 border-t border-gray-700">
            <p className="text-xs font-semibold text-gray-300 mb-1">✅ Valid Examples:</p>
            <ul className="text-xs text-gray-400 space-y-1 font-mono">
              <li>• sum("Revenue") / count("Order Id") → Avg order value</li>
              <li>• nunique("Category") → Count unique categories</li>
              <li>• (sum("Revenue") / sum("Cost")) * 100 → Profit margin %</li>
            </ul>
            <p className="text-xs font-semibold text-red-300 mt-2 mb-1">❌ Invalid Examples:</p>
            <ul className="text-xs text-gray-400 space-y-1 font-mono">
              <li>• sum("Category") → Error: Category is text, not numeric</li>
              <li>• avg("Product Name") → Error: Cannot average text</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomKPIModal;
