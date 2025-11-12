import React, { useRef, useState } from 'react';
import { Report } from '../types';
import KPICard from './KPICard';
import Chart from './Chart';
import { InsightIcon, RecommendationIcon, DownloadIcon, ResetIcon } from './icons';
import { exportPDF } from '../services/backendService';

interface ReportViewProps {
  report: Report;
  onReset: () => void;
  fileId?: string;
  rawReportData?: {
    insights: string;
    trends: any[];
  };
}

// Helper to parse markdown text to React elements
const parseMarkdown = (text: string) => {
  // Remove bold markers and return clean text
  let cleaned = text.replace(/\*\*(.+?)\*\*/g, '$1'); // Bold
  cleaned = cleaned.replace(/\*(.+?)\*/g, '$1'); // Italic
  cleaned = cleaned.replace(/^#{1,6}\s+/gm, ''); // Headers
  return cleaned;
};

const ReportView: React.FC<ReportViewProps> = ({ report, onReset, fileId, rawReportData }) => {
  const reportRef = useRef<HTMLDivElement>(null);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    if (isExporting) return;

    // Use backend PDF generator if data is available
    if (fileId && rawReportData && report) {
      setIsExporting(true);
      try {
        // Create formatted markdown from the report structure
        let formattedInsights = `# ${report.reportTitle}\n\n`;
        formattedInsights += `**Generated on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}**\n\n`;
        formattedInsights += `## Executive Summary\n\n${report.summary}\n\n`;
        
        // KPIs Section
        formattedInsights += `## Key Performance Indicators\n\n`;
        formattedInsights += `| Metric | Value | Period Comparison |\n`;
        formattedInsights += `|--------|-------|-------------------|\n`;
        report.kpis.forEach(kpi => {
          formattedInsights += `| ${kpi.name} | ${kpi.value} | ${kpi.description} |\n`;
        });
        formattedInsights += `\n`;
        
        // KPI Explanations Section
        if (report.kpiExplanations && report.kpiExplanations.length > 0) {
          formattedInsights += `## What This Means For Your Business\n\n`;
          formattedInsights += `The metrics above show your business performance over time. Here's how to read them:\n\n`;
          report.kpiExplanations.forEach(explanation => {
            formattedInsights += `### ${explanation.icon} ${explanation.title}\n\n`;
            formattedInsights += `${explanation.description}\n\n`;
          });
          formattedInsights += `**Reading the Graphs:** Charts show trends over time. An upward trend means growth, a downward trend means decline. Red circles mark unusual spikes or drops that need investigation.\n\n`;
        }
        
        // Trends Analysis Section
        if (report.trends && report.trends.length > 0) {
          formattedInsights += `## Trends Analysis\n\n`;
          report.trends.forEach((trend, idx) => {
            formattedInsights += `### ${trend.title}\n\n`;
            formattedInsights += `${trend.description}\n\n`;
            
            // Add chart insights if available
            if (trend.insights) {
              formattedInsights += `**Analysis:**\n\n`;
              formattedInsights += `- Overall Trend: ${trend.insights.trend.charAt(0).toUpperCase() + trend.insights.trend.slice(1)} (${trend.insights.change})\n`;
              formattedInsights += `- Volatility: ${trend.insights.volatility.charAt(0).toUpperCase() + trend.insights.volatility.slice(1)}\n`;
              formattedInsights += `- Peak Value: ${trend.insights.peak}\n`;
              formattedInsights += `- Lowest Value: ${trend.insights.low}\n`;
              formattedInsights += `- Average: ${trend.insights.average}\n`;
              if (trend.insights.anomalies_count > 0) {
                formattedInsights += `- Anomalies Detected: ${trend.insights.anomalies_count}\n`;
              }
              formattedInsights += `\n`;
            }
            
            formattedInsights += `*[See Chart ${idx + 1} in the PDF]*\n\n`;
          });
        }
        
        // Insights Section
        formattedInsights += `## Actionable Insights\n\n`;
        report.insights.forEach((insight, idx) => {
          formattedInsights += `${idx + 1}. ${insight}\n\n`;
        });
        
        // Recommendations Section
        formattedInsights += `## Recommendations\n\n`;
        report.recommendations.forEach((rec, idx) => {
          formattedInsights += `${idx + 1}. ${rec}\n\n`;
        });
        
        // Send full report structure for new text-based PDF
        const structuredReport = {
          reportTitle: report.reportTitle,
          summary: report.summary,
          kpis: report.kpis.map(kpi => ({
            name: kpi.name,
            value: kpi.value,
            description: kpi.description // Already has comparison text like "↑ +15%"
          })),
          kpiExplanations: report.kpiExplanations || [],
          categoricalBreakdowns: report.categoricalBreakdowns || [],  // NEW: Include category data in PDF
          trends: report.trends?.map(trend => ({
            title: trend.title,
            description: trend.description,
            insights: trend.insights ? {
              trend: trend.insights.trend,
              change: trend.insights.change,
              volatility: trend.insights.volatility,
              peak: trend.insights.peak,
              low: trend.insights.low,
              average: trend.insights.average,
              anomalies_count: trend.insights.anomalies_count || 0
            } : null
          })) || [],
          insights: report.insights || [],
          recommendations: report.recommendations || []
        };
        
        // Call backend PDF generator with structured data
        const response = await exportPDF(fileId, structuredReport);
        
        // Download the PDF
        const linkSource = `data:application/pdf;base64,${response.pdf_base64}`;
        const downloadLink = document.createElement('a');
        downloadLink.href = linkSource;
        downloadLink.download = response.filename;
        downloadLink.click();
        
      } catch (error) {
        console.error("Error generating PDF from backend:", error);
        alert('Failed to generate PDF. Please try again.');
      } finally {
        setIsExporting(false);
      }
    } else {
      // Fallback: Show message that PDF export requires proper data
      alert('PDF export is not available. Please regenerate the report.');
    }
  };
  
  return (
    <div ref={reportRef} className="bg-gradient-to-br from-gray-800 to-gray-900 p-8 md:p-10 rounded-2xl border border-gray-700 shadow-2xl w-full animate-fade-in">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 pb-6 border-b border-gray-700">
            <div>
              <h2 className="text-4xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent mb-2">
                {report.reportTitle}
              </h2>
              <p className="text-sm text-gray-500">Generated on {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
            </div>
            <div id="report-actions" className="flex gap-2 mt-4 sm:mt-0">
                 <button onClick={handleExport} disabled={isExporting} className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 font-semibold py-2.5 px-5 rounded-lg transition-all shadow-lg hover:shadow-indigo-500/50 disabled:opacity-50 disabled:cursor-wait">
                    <DownloadIcon /> {isExporting ? 'Exporting...' : 'Export PDF'}
                 </button>
                 <button onClick={onReset} className="flex items-center gap-2 bg-gray-700 text-gray-200 hover:bg-gray-600 font-semibold py-2.5 px-5 rounded-lg transition-all">
                    <ResetIcon /> New Report
                 </button>
            </div>
        </div>

        {/* Executive Summary */}
        <div className="mb-10 p-6 bg-gradient-to-r from-indigo-900/30 to-purple-900/30 rounded-xl border border-indigo-700/50">
          <h3 className="text-lg font-bold text-indigo-300 mb-3 uppercase tracking-wide">Executive Summary</h3>
          <p className="text-gray-300 leading-relaxed text-base">{parseMarkdown(report.summary)}</p>
        </div>

        {/* KPI Section */}
        <section className="mb-12">
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <span className="w-1 h-8 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></span>
            Key Performance Indicators
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {report.kpis.map((kpi, index) => (
              <KPICard key={index} kpi={kpi} />
            ))}
          </div>
        </section>

        {/* What This Means For Your Business */}
        {report.kpiExplanations && report.kpiExplanations.length > 0 && (
          <section className="mb-12 p-8 bg-gradient-to-br from-indigo-900/20 to-purple-900/20 rounded-2xl border border-indigo-700/30">
            <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <span className="text-2xl">💡</span>
              What This Means For Your Business
            </h3>
            <div className="space-y-4 text-gray-300 leading-relaxed">
              <p className="text-base">
                <strong className="text-indigo-300">Understanding Your Numbers:</strong> The metrics above show your business performance over time. 
                Here's how to read them:
              </p>
              
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                {report.kpiExplanations.map((explanation, index) => (
                  <div key={index} className="p-4 bg-gray-900/40 rounded-lg border border-gray-700">
                    <h4 className="font-semibold text-indigo-300 mb-2 flex items-center gap-2">
                      <span>{explanation.icon}</span> {explanation.title}
                    </h4>
                    <p className="text-sm text-gray-400">
                      {explanation.description}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-indigo-900/20 rounded-lg border border-indigo-600/30">
                <p className="text-sm">
                  <strong className="text-indigo-300">📈 Reading the Graphs Below:</strong> The charts show trends over time. 
                  An <span className="text-green-400">upward trend ↗</span> means growth, a <span className="text-red-400">downward trend ↘</span> means decline. 
                  Red circles (🔴) mark unusual spikes or drops that need investigation. The "Analysis" section under each graph explains what the data means.
                </p>
              </div>
            </div>
          </section>
        )}

        {/* Category Breakdowns (Safe - won't crash if missing) */}
        {report.categoricalBreakdowns && report.categoricalBreakdowns.length > 0 && (
          <section className="mb-12">
            <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="w-1 h-8 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></span>
              Category Breakdowns
            </h3>
            <p className="text-sm text-gray-400 mb-6">Top performing categories and products</p>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {report.categoricalBreakdowns.map((breakdown, index) => (
                <div key={index} className="bg-gradient-to-br from-gray-900/80 to-gray-800/80 p-6 rounded-xl border border-gray-700 hover:border-purple-500/50 transition-all">
                  <h4 className="text-lg font-bold text-purple-300 mb-4">{breakdown.title}</h4>
                  <div className="space-y-3">
                    {breakdown.items.map((item, idx) => {
                      // Calculate percentage of max for visual bar
                      const maxValue = breakdown.items[0]?.raw_value || 1;
                      const percentage = (item.raw_value / maxValue) * 100;
                      
                      return (
                        <div key={idx} className="relative">
                          <div className="flex justify-between items-center mb-1 relative z-10">
                            <span className="text-sm font-medium text-gray-300 truncate mr-2">
                              {idx + 1}. {item.name}
                            </span>
                            <span className="text-sm font-bold text-white whitespace-nowrap">
                              {item.value}
                            </span>
                          </div>
                          {/* Visual bar */}
                          <div className="h-2 bg-gray-700/30 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full transition-all ${
                                idx === 0 ? 'bg-gradient-to-r from-purple-500 to-pink-500' :
                                idx === 1 ? 'bg-gradient-to-r from-blue-500 to-purple-500' :
                                idx === 2 ? 'bg-gradient-to-r from-cyan-500 to-blue-500' :
                                'bg-gradient-to-r from-gray-500 to-gray-600'
                              }`}
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  {breakdown.total_categories > breakdown.items.length && (
                    <p className="text-xs text-gray-500 mt-4 text-center">
                      +{breakdown.total_categories - breakdown.items.length} more categories
                    </p>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Trends Section */}
        {report.trends && report.trends.length > 0 && (
          <section className="mb-12">
            <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="w-1 h-8 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></span>
              Trends Analysis
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {report.trends.map((trend, index) => (
                <div key={index} className="bg-gradient-to-br from-gray-900/80 to-gray-800/80 p-6 rounded-xl border border-gray-700 hover:border-indigo-500/50 transition-all">
                  <h4 className="text-lg font-bold text-indigo-300 mb-2">{trend.title}</h4>
                  <p className="text-gray-400 text-sm mb-4">{trend.description}</p>
                  <Chart 
                    data={trend.chartData}
                    metricName={trend.title.replace(' Over Time', '')}
                    holidays={trend.holidays}
                    anomalies={trend.anomalies}
                  />
                  
                  {/* Chart Insights */}
                  {trend.insights && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                      <h5 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Analysis</h5>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="flex flex-col">
                          <span className="text-gray-500 text-xs">Overall Trend</span>
                          <span className={`font-semibold ${trend.insights.trend === 'upward' ? 'text-green-400' : trend.insights.trend === 'downward' ? 'text-red-400' : 'text-gray-400'}`}>
                            {trend.insights.trend === 'upward' ? '↗' : trend.insights.trend === 'downward' ? '↘' : '→'} {trend.insights.trend.charAt(0).toUpperCase() + trend.insights.trend.slice(1)} ({trend.insights.change})
                          </span>
                        </div>
                        
                        <div className="flex flex-col">
                          <span className="text-gray-500 text-xs">Volatility</span>
                          <span className={`font-semibold ${trend.insights.volatility === 'high' ? 'text-orange-400' : trend.insights.volatility === 'moderate' ? 'text-yellow-400' : 'text-green-400'}`}>
                            {trend.insights.volatility.charAt(0).toUpperCase() + trend.insights.volatility.slice(1)}
                          </span>
                        </div>
                        
                        <div className="flex flex-col">
                          <span className="text-gray-500 text-xs">Peak Value</span>
                          <span className="font-semibold text-white">{trend.insights.peak}</span>
                        </div>
                        
                        <div className="flex flex-col">
                          <span className="text-gray-500 text-xs">Lowest Value</span>
                          <span className="font-semibold text-white">{trend.insights.low}</span>
                        </div>
                        
                        <div className="flex flex-col">
                          <span className="text-gray-500 text-xs">Average</span>
                          <span className="font-semibold text-white">{trend.insights.average}</span>
                        </div>
                        
                        {trend.insights.anomalies_count > 0 && (
                          <div className="flex flex-col">
                            <span className="text-gray-500 text-xs">Anomalies</span>
                            <span className="font-semibold text-red-400">{trend.insights.anomalies_count} detected</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}
      
        {/* Insights & Recommendations */}
        <div className="grid md:grid-cols-2 gap-8">
          <section>
            <h3 className="text-2xl font-bold text-white mb-5 flex items-center gap-2">
              <InsightIcon /> Actionable Insights
            </h3>
            <div className="space-y-4">
              {report.insights.map((insight, index) => {
                // Parse markdown and split for readability
                const cleanedInsight = parseMarkdown(insight);
                const parts = cleanedInsight.split(/:\s+/);
                const title = parts.length > 1 ? parts[0] : null;
                const content = parts.length > 1 ? parts.slice(1).join(': ') : cleanedInsight;
                
                return (
                  <div key={index} className="flex items-start p-5 bg-gradient-to-r from-indigo-900/20 to-purple-900/20 rounded-lg border border-indigo-700/30 hover:border-indigo-500/60 transition-all">
                    <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-indigo-600 text-white font-bold rounded-full mr-4 text-sm">
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      {title && (
                        <div className="font-semibold text-indigo-300 mb-2 text-sm leading-relaxed">
                          {title}
                        </div>
                      )}
                      <p className="text-gray-300 leading-relaxed text-sm whitespace-pre-line">
                        {content}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section>
            <h3 className="text-2xl font-bold text-white mb-5 flex items-center gap-2">
              <RecommendationIcon /> Recommendations
            </h3>
            <div className="space-y-4">
              {report.recommendations.map((rec, index) => {
                // Parse markdown and split for better formatting
                const cleanedRec = parseMarkdown(rec);
                const parts = cleanedRec.split(/:\s+/);
                const title = parts.length > 1 ? parts[0] : null;
                const content = parts.length > 1 ? parts.slice(1).join(': ') : cleanedRec;
                
                return (
                  <div key={index} className="flex items-start p-5 bg-gradient-to-r from-green-900/20 to-emerald-900/20 rounded-lg border border-green-700/30 hover:border-green-500/60 transition-all">
                    <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-green-600 text-white font-bold rounded-full mr-4 text-sm">
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      {title && (
                        <div className="font-semibold text-green-300 mb-2 text-sm leading-relaxed">
                          {title}
                        </div>
                      )}
                      <p className="text-gray-300 leading-relaxed text-sm whitespace-pre-line">
                        {content}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
        
        <style>{`
          @keyframes fade-in {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }
          .animate-fade-in {
            animation: fade-in 0.6s ease-out forwards;
          }
        `}</style>
    </div>
  );
};

export default ReportView;