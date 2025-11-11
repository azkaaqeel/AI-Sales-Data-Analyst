
import React, { useRef } from 'react';
import { UploadIcon, AnalyzeIcon } from './icons';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onAnalyze: () => void;
  file: File | null;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, onAnalyze, file }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      onFileSelect(event.target.files[0]);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
  };

  const handleDrop = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      onFileSelect(event.dataTransfer.files[0]);
      event.dataTransfer.clearData();
    }
  };

  return (
    <div className="w-full max-w-2xl text-center p-8 bg-gray-800 border border-gray-700 rounded-2xl shadow-lg">
      <h2 className="text-3xl font-bold text-white mb-2">Upload Your Sales Data</h2>
      <p className="text-gray-400 mb-6">Upload a CSV file to get started.</p>
      
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".csv"
      />
      
      <label
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-gray-600 rounded-xl cursor-pointer bg-gray-800/50 hover:bg-gray-700/50 transition-colors"
      >
        <div className="flex flex-col items-center justify-center pt-5 pb-6">
          <UploadIcon />
          <p className="mb-2 text-sm text-gray-400">
            <span className="font-semibold">Click to upload</span> or drag and drop
          </p>
          <p className="text-xs text-gray-500">CSV files only</p>
          {file && (
            <p className="mt-4 text-sm font-medium text-indigo-400">{file.name}</p>
          )}
        </div>
      </label>

      <button
        onClick={onAnalyze}
        disabled={!file}
        className="w-full mt-8 flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-indigo-700 disabled:bg-gray-500 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:scale-100"
      >
        <AnalyzeIcon />
        Analyze Data
      </button>
    </div>
  );
};

export default FileUpload;
