
export enum AppState {
    IDLE,                     // Upload screen
    UPLOADING,                // Uploading file...
    PLAN_REVIEW,              // Review cleaning plan with toggle buttons
    CLEANING,                 // Applying selected cleaning steps...
    KPI_SELECTION,            // Select/add KPIs
    GENERATING_REPORT,        // Generating report...
    REPORT_READY,             // Show final report
    ERROR                     // Error state
}

export interface CleaningStep {
    id: string;
    action: string;
    reason: string;
    recommended: boolean;
}

export interface ColumnCleaningPlan {
    column: string;
    type: string;
    steps: CleaningStep[];
    missing_count: number;
    total_rows: number;
}

export interface GlobalStep {
    id: string;
    action: string;
    reason: string;
    recommended: boolean;
    count?: number;
}

export interface CleaningPlan {
    columns: ColumnCleaningPlan[];
    global_steps: GlobalStep[];
    column_types: Record<string, string>;
    original_shape: [number, number];
    data_preview?: any[];
    summary: {
        total_columns: number;
        columns_needing_cleaning: number;
        total_cleaning_steps: number;
    };
}

export interface DetectedKPI {
    name: string;
    description: string;
    matched_columns?: Record<string, string>;
    formula?: string;
    value?: string;  // For display in cards
}

export interface CustomKPI {
    name: string;
    formula: string;
    description: string;
}

export interface Trend {
    title: string;
    description: string;
    chartData: {
        x_axis: string;
        y_axis: number;
    }[];
}

export interface Report {
    reportTitle: string;
    summary: string;
    kpis: DetectedKPI[];
    trends: Trend[];
    insights: string[];
    recommendations: string[];
}

export interface ChatMessage {
    sender: 'user' | 'ai';
    text: string;
}
