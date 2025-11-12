
import React, { useState, useCallback } from 'react';
import { AppState, Report, ChatMessage, CleaningPlan, DetectedKPI, CustomKPI } from './types';
import { uploadAndPropose, cleanAndDetectKPIs, generateReport } from './services/backendService';
import FileUpload from './components/FileUpload';
import CleaningPlanView from './components/CleaningPlanView';
import ProcessingView from './components/ProcessingView';
import ReportView from './components/ReportView';
import Chatbot from './components/Chatbot';
import KPISelectionWithCustom from './components/KPISelectionWithCustom';
import { LogoIcon } from './components/icons';

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>(AppState.IDLE);
  const [file, setFile] = useState<File | null>(null);
  const [fileId, setFileId] = useState<string>('');
  
  // Phase 1: Cleaning Plan
  const [cleaningPlan, setCleaningPlan] = useState<CleaningPlan | null>(null);
  
  // Phase 2: Detected KPIs
  const [detectedKpis, setDetectedKpis] = useState<DetectedKPI[]>([]);
  
  // Phase 3: Report
  const [report, setReport] = useState<Report | null>(null);
  const [reportRawData, setReportRawData] = useState<{ insights: string; trends: any[] } | null>(null);
  
  // Chatbot
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isChatbotLoading, setIsChatbotLoading] = useState<boolean>(false);
  
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
  };

  // PHASE 1: Upload and get cleaning plan
  const handleUploadAndPropose = useCallback(async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setAppState(AppState.UPLOADING);
    setError(null);
    setCleaningPlan(null);
    setDetectedKpis([]);
    setReport(null);
    setChatHistory([]);

    try {
      const response = await uploadAndPropose(file);
      setFileId(response.file_id);
      setCleaningPlan(response.cleaning_plan);
      setAppState(AppState.PLAN_REVIEW);
    } catch (err) {
      console.error(err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
      setError(`Failed to upload and analyze file. ${errorMessage}`);
      setAppState(AppState.ERROR);
    }
  }, [file]);

  // PHASE 2: Apply selected cleaning steps and detect KPIs
  const handleApplyCleaningAndDetectKPIs = useCallback(async (selectedStepIds: string[]) => {
    if (!fileId) {
      setError('Session expired. Please upload the file again.');
      setAppState(AppState.ERROR);
      return;
    }

    setAppState(AppState.CLEANING);
    try {
      const response = await cleanAndDetectKPIs(fileId, selectedStepIds);
      setDetectedKpis(response.detected_kpis);
      setAppState(AppState.KPI_SELECTION);
    } catch (err) {
      console.error(err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
      setError(`Failed to clean data and detect KPIs. ${errorMessage}`);
      setAppState(AppState.ERROR);
    }
  }, [fileId]);

  // PHASE 3 & 4: Generate report with selected + custom KPIs
  const handleGenerateReport = useCallback(async (selectedKpis: string[], customKpis: CustomKPI[]) => {
    if (!fileId || selectedKpis.length === 0) {
      setError('Please select at least one KPI.');
      return;
    }

    console.log('🔍 FRONTEND: Generating report with:');
    console.log('  - Selected KPIs:', selectedKpis);
    console.log('  - Custom KPIs:', customKpis);

    setAppState(AppState.GENERATING_REPORT);
    try {
      const response = await generateReport(fileId, selectedKpis, customKpis);
      console.log('🔍 FRONTEND: Got response, report KPIs:', response.report?.kpis?.map(k => k.name));
      setReport(response.report);
      
      // Store raw data for PDF generation
      setReportRawData({
        insights: response.insights || '',
        trends: response.trends || []
      });
      
      const welcomeMessage: ChatMessage = {
        sender: 'ai',
        text: 'Hello! I am your sales assistant. Feel free to ask me any questions about the generated report.',
      };
      setChatHistory([welcomeMessage]);
      setAppState(AppState.REPORT_READY);

    } catch (err) {
      console.error(err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
      setError(`Failed to generate the report. ${errorMessage}`);
      setAppState(AppState.ERROR);
    }
  }, [fileId]);
  
  // Chatbot (can use Gemini or keep responses simple)
  const handleSendMessage = useCallback(async (message: string) => {
      if (!report) return;

      const userMessage: ChatMessage = { sender: 'user', text: message };
      setChatHistory(prev => [...prev, userMessage]);
      setIsChatbotLoading(true);

      try {
        // Simple response for now (can integrate Gemini later)
        const aiResponse = generateChatResponse(message, report);
        const aiMessage: ChatMessage = { sender: 'ai', text: aiResponse };
        setChatHistory(prev => [...prev, aiMessage]);
      } catch (err) {
        console.error(err);
        const errorMessage: ChatMessage = { sender: 'ai', text: 'Sorry, I encountered an error. Please try again.' };
        setChatHistory(prev => [...prev, errorMessage]);
      } finally {
        setIsChatbotLoading(false);
      }
  }, [report]);

  const handleReset = () => {
    setFile(null);
    setFileId('');
    setCleaningPlan(null);
    setDetectedKpis([]);
    setReport(null);
    setReportRawData(null);
    setChatHistory([]);
    setError(null);
    setAppState(AppState.IDLE);
  };

  const renderContent = () => {
    switch (appState) {
      case AppState.UPLOADING:
        return <ProcessingView title="Analyzing Your Data..." steps={["Uploading file...", "Detecting data types...", "Identifying issues...", "Preparing cleaning plan..."]} />;
      
      case AppState.PLAN_REVIEW:
        if (cleaningPlan) {
          return <CleaningPlanView cleaningPlan={cleaningPlan} onApply={handleApplyCleaningAndDetectKPIs} />;
        }
        break;
      
      case AppState.CLEANING:
        return <ProcessingView title="Cleaning Your Data..." steps={["Applying selected steps...", "Standardizing formats...", "Handling missing values...", "Detecting KPIs..."]} />;
      
      case AppState.KPI_SELECTION:
        return <KPISelectionWithCustom detectedKpis={detectedKpis} fileId={fileId} onGenerateReport={handleGenerateReport} />;
      
      case AppState.GENERATING_REPORT:
        return <ProcessingView title="Generating Your Report..." steps={["Calculating KPIs...", "Analyzing trends...", "Generating forecasts...", "Compiling insights...", "Finalizing report..."]} />;
      
      case AppState.REPORT_READY:
        if (report && reportRawData) {
          return (
            <div className="w-full max-w-screen-2xl mx-auto p-4 md:p-8">
              <ReportView 
                report={report} 
                onReset={handleReset}
                fileId={fileId}
                rawReportData={reportRawData}
              />
            </div>
          );
        }
        break;
      
      case AppState.ERROR:
        return (
          <div className="text-center p-8">
            <h2 className="text-xl text-red-400 mb-4">{error || 'An unexpected error occurred.'}</h2>
            <button onClick={handleReset} className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg transition-colors">
              Try Again
            </button>
          </div>
        );
      
      case AppState.IDLE:
      default:
        return (
          <FileUpload onFileSelect={handleFileSelect} onAnalyze={handleUploadAndPropose} file={file} />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200 font-sans flex flex-col items-center p-4">
      <header className="w-full max-w-screen-2xl mx-auto py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <LogoIcon />
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            AI Sales Data Analyst
          </h1>
        </div>
      </header>
      <main className="w-full flex-grow flex items-center justify-center">
        {renderContent()}
      </main>
    </div>
  );
};

// Simple chatbot response generator (can be replaced with Gemini)
function generateChatResponse(message: string, report: Report): string {
  const lowerMessage = message.toLowerCase();
  
  // Check for KPI questions
  if (lowerMessage.includes('kpi') || lowerMessage.includes('metric')) {
    const kpiNames = report.kpis.map(k => k.name).join(', ');
    return `The report includes ${report.kpis.length} KPIs: ${kpiNames}. Each KPI provides insights into your sales performance.`;
  }
  
  // Check for trend questions
  if (lowerMessage.includes('trend') || lowerMessage.includes('pattern')) {
    return `I've identified ${report.trends.length} key trends in your data. ${report.insights[0] || 'The data shows interesting patterns.'}`;
  }
  
  // Check for recommendation questions
  if (lowerMessage.includes('recommend') || lowerMessage.includes('should') || lowerMessage.includes('what')) {
    return report.recommendations[0] || 'Based on the analysis, I recommend reviewing the key metrics regularly.';
  }
  
  // Default response
  return `Based on the report, ${report.summary}`;
}

export default App;
