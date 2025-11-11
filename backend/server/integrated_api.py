"""
FastAPI backend with 4-phase integration for frontend.

Phases:
1. Upload & Propose: Returns cleaning plan
2. Clean & Detect KPIs: Returns detected KPIs  
3. Add Custom KPIs: User can add custom KPIs
4. Generate Report: Returns full report with trends and insights
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import json
import math
import base64
from typing import Optional, List, Dict, Any
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.getenv("DATAMIND_ENV_FILE", "../.env"))

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import backend modules
from agent.business_analyst_agent import run_proposal_phase, run_full_pipeline

app = FastAPI(title="Datamind Integrated API", version="2.0")

# CORS - Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for uploaded files (use Redis/DB in production)
_file_storage: Dict[str, pd.DataFrame] = {}


def _load_csv(contents: bytes) -> pd.DataFrame:
    """Load CSV with fallback encoding."""
    try:
        return pd.read_csv(io.BytesIO(contents))
    except Exception:
        return pd.read_csv(io.BytesIO(contents), encoding='latin1')


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({'status': 'ok', 'service': 'Datamind Integrated API', 'version': '2.0'})


@app.post("/api/upload")
async def upload_and_propose(file: UploadFile = File(...)):
    """
    Phase 1: Upload CSV and get cleaning plan proposal.
    
    Returns:
    - file_id: Unique identifier for this upload session
    - cleaning_plan: Proposed cleaning steps with toggle options
    - column_types: Detected column types
    - data_preview: First 5 rows
    - original_shape: [rows, columns]
    """
    try:
        contents = await file.read()
        df = _load_csv(contents)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Generate unique file ID
        file_id = f"{file.filename}_{hash(contents)}"
        
        # Store dataframe for later phases
        _file_storage[file_id] = df
        
        # Get cleaning proposal
        plan = run_proposal_phase(df, file.filename or "uploaded.csv")
        
        # Clean the response for JSON serialization
        cleaned_response = clean_for_json({
            'file_id': file_id,
            'cleaning_plan': plan,
            'success': True
        })
        
        return JSONResponse(cleaned_response)
    
    except Exception as e:
        import traceback
        print(f"ERROR /api/upload:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clean_and_detect_kpis")
async def clean_and_detect_kpis(
    file_id: str = Form(...),
    selected_steps: str = Form(...)  # JSON string of selected step IDs
):
    """
    Phase 2: Apply selected cleaning steps and detect KPIs.
    
    Args:
    - file_id: File identifier from upload phase
    - selected_steps: JSON array of step IDs to apply
    
    Returns:
    - detected_kpis: List of KPIs that can be calculated
    - cleaning_logs: Actions taken during cleaning
    - cleaned_shape: Shape after cleaning
    """
    try:
        # Retrieve dataframe
        if file_id not in _file_storage:
            raise HTTPException(status_code=404, detail="File not found. Please upload again.")
        
        df = _file_storage[file_id]
        
        # Parse selected steps
        try:
            selected_step_ids = json.loads(selected_steps)
        except:
            selected_step_ids = []
        
        # Build user_choices dict
        user_choices = {step_id: True for step_id in selected_step_ids}
        
        # Run pipeline up to KPI detection
        result = run_full_pipeline(df, file_id, user_choices)
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Extract detected KPIs
        detected_kpis_dict = result.get('detected_kpis', {})
        detected_kpis = []
        
        print(f"\n🔍 KPI DETECTION DEBUG:")
        print(f"   Total KPIs checked: {len(detected_kpis_dict)}")
        
        for kpi_name, kpi_data in detected_kpis_dict.items():
            calculable = kpi_data.get('calculable', False)
            matched_cols = kpi_data.get('matched_columns', {})
            print(f"   {kpi_name}: calculable={calculable}, matched={matched_cols}")
            
            if calculable:
                kpi_info = kpi_data.get('kpi_info', {})
                detected_kpis.append({
                    'name': kpi_name,
                    'description': kpi_info.get('description', ''),
                    'matched_columns': matched_cols,
                    'formula': kpi_info.get('formula', '')
                })
        
        print(f"   ✅ Detected {len(detected_kpis)} calculable KPIs\n")
        
        # Update stored dataframe with cleaned version
        if result.get('cleaned_data') is not None:
            _file_storage[file_id] = result['cleaned_data']
        
        response_data = {
            'detected_kpis': detected_kpis,
            'cleaning_logs': result.get('cleaning_logs', []),
            'cleaned_shape': list(result.get('cleaned_data', df).shape) if result.get('cleaned_data') is not None else list(df.shape),
            'success': True
        }
        return JSONResponse(clean_for_json(response_data))
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR /api/clean_and_detect_kpis:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate_report")
async def generate_report(
    file_id: str = Form(...),
    selected_kpis: str = Form(...),  # JSON array of KPI names
    custom_kpis: str = Form(default="[]")  # JSON array of custom KPI definitions
):
    """
    Phase 3 & 4: Calculate selected KPIs (including custom) and generate full report.
    
    Args:
    - file_id: File identifier
    - selected_kpis: JSON array of KPI names to calculate
    - custom_kpis: JSON array of custom KPI objects [{name, formula, description}]
    
    Returns:
    - report: Complete report with KPIs, trends, insights
    - calculated_kpis: KPI values by time period
    - trends: Trend images (base64)
    - insights: Markdown insights from Gemini
    """
    try:
        # Retrieve cleaned dataframe
        if file_id not in _file_storage:
            raise HTTPException(status_code=404, detail="File not found. Please re-upload and clean data.")
        
        df = _file_storage[file_id]
        
        # Parse inputs
        try:
            selected_kpi_list = json.loads(selected_kpis)
            custom_kpi_list = json.loads(custom_kpis) if custom_kpis else []
        except:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        # Run full pipeline (KPI calculation + trends + insights)
        # user_choices is empty since cleaning is already done
        result = run_full_pipeline(
            df, 
            file_id, 
            user_choices={},  # Already cleaned
            custom_kpis=custom_kpi_list
        )
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Transform response for frontend
        response = {
            'calculated_kpis': result.get('calculated_kpis', {}),
            'insights': result.get('insights', ''),
            'logs': result.get('cleaning_logs', []),
            'success': True
        }
        
        # Add trend images as base64
        if result.get('trend_images'):
            encoded_trends = []
            for img in result['trend_images']:
                img_data = img.getvalue()
                encoded_trends.append({
                    'type': 'image/png',
                    'data': base64.b64encode(img_data).decode('ascii'),
                    'size_bytes': len(img_data)
                })
            response['trends'] = encoded_trends
        else:
            response['trends'] = []
        
        # Transform report for frontend format
        response['report'] = transform_to_frontend_report(
            result.get('calculated_kpis', {}),
            response['trends'],
            result.get('insights', ''),
            selected_kpi_list
        )
        
        return JSONResponse(clean_for_json(response))
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR /api/generate_report:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


def clean_for_json(obj):
    """Recursively clean NaN/Inf values and convert non-serializable types."""
    import math
    import numpy as np
    import pandas as pd
    from datetime import datetime, date
    
    if isinstance(obj, dict):
        # Convert keys to strings if they're not JSON-serializable
        cleaned_dict = {}
        for k, v in obj.items():
            # Convert Period, Timestamp, datetime, date keys to strings
            if isinstance(k, (pd.Period, pd.Timestamp, datetime, date)):
                key = str(k)
            elif isinstance(k, (str, int, float, bool, type(None))):
                key = k
            else:
                key = str(k)  # Convert any other non-serializable keys to string
            cleaned_dict[key] = clean_for_json(v)
        return cleaned_dict
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, (pd.Period, pd.Timestamp)):
        return str(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    return obj


def transform_to_frontend_report(
    calculated_kpis: Dict[str, Any],
    trends: List[Dict[str, Any]],
    insights: str,
    selected_kpis: List[str]
) -> Dict[str, Any]:
    """
    Transform backend response to frontend Report format.
    
    Frontend expects:
    {
        reportTitle: string,
        summary: string,
        kpis: [{name, value, description}],
        trends: [{title, description, chartData: [{x_axis, y_axis}]}],
        insights: string[],
        recommendations: string[]
    }
    """
    # Extract KPI values (use most recent period)
    kpi_cards = []
    periods = [k for k in calculated_kpis.keys() if k != 'meta']
    
    if periods:
        # Sort periods
        periods_sorted = sorted(periods)
        latest_period = periods_sorted[-1]
        latest_values = calculated_kpis.get(latest_period, {})
        
        for kpi_name in selected_kpis:
            if kpi_name in latest_values:
                value = latest_values[kpi_name]
                # Handle NaN, None, and invalid values
                if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
                    value_str = "N/A"
                elif isinstance(value, (int, float)):
                    value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                
                kpi_cards.append({
                    'name': kpi_name,
                    'value': value_str,
                    'description': f"Current value for {kpi_name}"
                })
    
    # Create trend charts from time series data
    trend_charts = []
    for kpi_name in selected_kpis[:4]:  # Limit to 4 trends
        chart_data = []
        for period in sorted(periods):
            if kpi_name in calculated_kpis.get(period, {}):
                value = calculated_kpis[period][kpi_name]
                # Skip NaN, None, and invalid values
                if value is not None and not (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
                    try:
                        chart_data.append({
                            'x_axis': str(period)[:10],  # Date string
                            'y_axis': float(value)
                        })
                    except (ValueError, TypeError):
                        continue  # Skip invalid values
        
        if chart_data:
            trend_charts.append({
                'title': f'{kpi_name} Over Time',
                'description': f'Trend analysis of {kpi_name}',
                'chartData': chart_data
            })
    
    # Parse insights markdown into sections
    insights_list = []
    recommendations_list = []
    summary = ""
    
    if insights:
        lines = insights.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if '## Executive Summary' in line or '## Summary' in line:
                current_section = 'summary'
            elif '## Recommendations' in line or 'Recommendation' in line:
                current_section = 'recommendations'
            elif '## Insights' in line or '## Key Insights' in line:
                current_section = 'insights'
            elif line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                bullet = line[2:].strip()
                if current_section == 'insights':
                    insights_list.append(bullet)
                elif current_section == 'recommendations':
                    recommendations_list.append(bullet)
            elif line and not line.startswith('#'):
                if current_section == 'summary':
                    summary += line + " "
    
    # Ensure we have at least some content
    if not summary:
        summary = "Analysis of sales data showing key performance indicators and trends."
    if not insights_list:
        insights_list = ["Data has been analyzed successfully", "Key metrics have been calculated", "Trends have been identified"]
    if not recommendations_list:
        recommendations_list = ["Review the KPI values regularly", "Monitor trend changes", "Take action on insights"]
    
    return {
        'reportTitle': 'Sales Analysis Report',
        'summary': summary.strip(),
        'kpis': kpi_cards,
        'trends': trend_charts,
        'insights': insights_list[:3],  # Limit to 3
        'recommendations': recommendations_list[:3]  # Limit to 3
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)

