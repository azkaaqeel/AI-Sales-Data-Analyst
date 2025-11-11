import React, { useRef, useState } from 'react';
import { Report } from '../types';
import KPICard from './KPICard';
import Chart from './Chart';
import { InsightIcon, RecommendationIcon, DownloadIcon, ResetIcon } from './icons';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface ReportViewProps {
  report: Report;
  onReset: () => void;
}

const ReportView: React.FC<ReportViewProps> = ({ report, onReset }) => {
  const reportRef = useRef<HTMLDivElement>(null);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    if (!reportRef.current || isExporting) return;

    setIsExporting(true);
    const reportElement = reportRef.current;
    
    const buttonsContainer = reportElement.querySelector<HTMLElement>('#report-actions');
    if (buttonsContainer) {
      buttonsContainer.style.visibility = 'hidden';
    }

    try {
      const canvas = await html2canvas(reportElement, {
        scale: 2,
        backgroundColor: '#1f2937', // bg-gray-800
        useCORS: true,
      });
      
      if (buttonsContainer) {
        buttonsContainer.style.visibility = 'visible';
      }

      const imgData = canvas.toDataURL('image/png');
      
      const pdf = new jsPDF({
        orientation: 'p',
        unit: 'mm',
        format: 'a4',
        putOnlyUsedFonts: true,
        compress: true,
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const canvasWidth = canvas.width;
      const canvasHeight = canvas.height;
      const ratio = canvasWidth / canvasHeight;
      const imgHeight = pdfWidth / ratio;
      
      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
      heightLeft -= pdfHeight;

      while (heightLeft > 0) {
        position -= pdfHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, imgHeight);
        heightLeft -= pdfHeight;
      }
      
      pdf.save(`${report.reportTitle.replace(/\s+/g, '_')}_Report.pdf`);

    } catch (error) {
      console.error("Error exporting to PDF:", error);
      if (buttonsContainer) {
        buttonsContainer.style.visibility = 'visible';
      }
    } finally {
      setIsExporting(false);
    }
  };
  
  return (
    <div ref={reportRef} className="bg-gray-800 p-6 md:p-8 rounded-2xl border border-gray-700 w-full animate-fade-in">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
            <h2 className="text-3xl font-bold text-white mb-2 sm:mb-0">{report.reportTitle}</h2>
            <div id="report-actions" className="flex gap-2">
                 <button onClick={handleExport} disabled={isExporting} className="flex items-center gap-2 bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/40 font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-wait">
                    <DownloadIcon /> {isExporting ? 'Exporting...' : 'Export PDF'}
                 </button>
                 <button onClick={onReset} className="flex items-center gap-2 bg-gray-600/40 text-gray-300 hover:bg-gray-600/60 font-medium py-2 px-4 rounded-lg transition-colors">
                    <ResetIcon /> New Report
                 </button>
            </div>
        </div>
        <p className="text-gray-400 mb-8">{report.summary}</p>

      <section className="mb-10">
        <h3 className="text-2xl font-semibold text-white mb-4">Key Performance Indicators</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {report.kpis.map((kpi, index) => (
            <KPICard key={index} kpi={kpi} />
          ))}
        </div>
      </section>

      <section className="mb-10">
        <h3 className="text-2xl font-semibold text-white mb-4">Trends Analysis</h3>
        <div className="space-y-8">
          {report.trends.map((trend, index) => (
            <div key={index} className="bg-gray-900/50 p-6 rounded-xl border border-gray-700">
              <h4 className="text-xl font-semibold text-indigo-300 mb-2">{trend.title}</h4>
              <p className="text-gray-400 mb-4">{trend.description}</p>
              <Chart data={trend.chartData} />
            </div>
          ))}
        </div>
      </section>
      
      <div className="grid md:grid-cols-2 gap-8">
        <section>
          <h3 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2"><InsightIcon /> Actionable Insights</h3>
          <ul className="space-y-3 list-inside">
            {report.insights.map((insight, index) => (
              <li key={index} className="flex items-start p-3 bg-gray-900/50 rounded-lg">
                <span className="text-indigo-400 font-bold mr-3">{index + 1}.</span>
                <span className="text-gray-300">{insight}</span>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h3 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2"><RecommendationIcon /> Recommendations</h3>
          <ul className="space-y-3 list-inside">
            {report.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start p-3 bg-gray-900/50 rounded-lg">
                <span className="text-indigo-400 font-bold mr-3">{index + 1}.</span>
                <span className="text-gray-300">{rec}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
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

export default ReportView;