
import React from 'react';

interface ProcessingViewProps {
  title: string;
  steps: string[];
}

const ProcessingView: React.FC<ProcessingViewProps> = ({ title, steps }) => {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8">
      <div className="relative w-24 h-24 mb-6">
        <div className="absolute inset-0 border-4 border-indigo-500 rounded-full animate-ping opacity-75"></div>
        <div className="absolute inset-0 border-4 border-indigo-400 rounded-full"></div>
      </div>
      <h2 className="text-3xl font-bold text-white mb-4">{title}</h2>
      <p className="text-gray-400 mb-8">Our AI is hard at work. This may take a moment.</p>
      
      <div className="w-full max-w-md space-y-2">
        {steps.map((step, index) => (
          <div key={step} className="flex items-center text-gray-300 animate-fade-in" style={{ animationDelay: `${index * 500}ms`}}>
             <svg className="w-5 h-5 text-indigo-400 mr-3 animate-spin" style={{ animationDelay: `${index * 500}ms`, animationDuration: '2s' }} fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
            <span>{step}</span>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
          opacity: 0;
        }
      `}</style>
    </div>
  );
};

export default ProcessingView;
