/**
 * Backend API Service
 * Replaces geminiService with direct backend integration
 */

import { CleaningPlan } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface UploadResponse {
    file_id: string;
    cleaning_plan: CleaningPlan;
    success: boolean;
}

export interface DetectedKPI {
    name: string;
    description: string;
    matched_columns: Record<string, string>;
    formula?: string;
}

export interface CleanDetectResponse {
    detected_kpis: DetectedKPI[];
    cleaning_logs: string[];
    cleaned_shape: [number, number];
    success: boolean;
}

export interface CustomKPI {
    name: string;
    formula: string;
    description: string;
}

export interface TrendChart {
    title: string;
    description: string;
    chartData: Array<{
        x_axis: string;
        y_axis: number;
    }>;
}

export interface ReportResponse {
    report: {
        reportTitle: string;
        summary: string;
        kpis: Array<{
            name: string;
            value: string;
            description: string;
        }>;
        trends: TrendChart[];
        insights: string[];
        recommendations: string[];
    };
    calculated_kpis: Record<string, any>;
    trends: Array<{
        type: string;
        data: string;  // base64
        size_bytes: number;
    }>;
    insights: string;
    logs: string[];
    success: boolean;
}

/**
 * Phase 1: Upload CSV and get cleaning plan
 */
export const uploadAndPropose = async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(error.detail || 'Failed to upload file');
    }
    
    return response.json();
};

/**
 * Phase 2: Apply selected cleaning steps and detect KPIs
 */
export const cleanAndDetectKPIs = async (
    fileId: string,
    selectedStepIds: string[]
): Promise<CleanDetectResponse> => {
    const formData = new FormData();
    formData.append('file_id', fileId);
    formData.append('selected_steps', JSON.stringify(selectedStepIds));
    
    const response = await fetch(`${API_BASE_URL}/api/clean_and_detect_kpis`, {
        method: 'POST',
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Cleaning failed' }));
        throw new Error(error.detail || 'Failed to clean data and detect KPIs');
    }
    
    return response.json();
};

/**
 * Phase 3 & 4: Generate full report with selected + custom KPIs
 */
export const generateReport = async (
    fileId: string,
    selectedKPIs: string[],
    customKPIs: CustomKPI[] = []
): Promise<ReportResponse> => {
    const formData = new FormData();
    formData.append('file_id', fileId);
    formData.append('selected_kpis', JSON.stringify(selectedKPIs));
    formData.append('custom_kpis', JSON.stringify(customKPIs));
    
    const response = await fetch(`${API_BASE_URL}/api/generate_report`, {
        method: 'POST',
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Report generation failed' }));
        throw new Error(error.detail || 'Failed to generate report');
    }
    
    return response.json();
};

/**
 * Health check
 */
export const checkHealth = async (): Promise<boolean> => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) return false;
        const data = await response.json();
        return data.status === 'ok';
    } catch {
        return false;
    }
};

