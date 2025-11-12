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
import re
from typing import Optional, List, Dict, Any
import os
import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4

from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.getenv("DATAMIND_ENV_FILE", "../.env"))

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import backend modules
from agent.business_analyst_agent import run_proposal_phase, run_full_pipeline
from modules.Ingestion_Module.dataset_classification import classify_dataset
from utils.time_period_detection import determine_period_type, add_period_column
from utils.generate_pdf_reports import create_pdf_report
from utils.generate_pdf_reports_v2 import create_text_pdf_report
from utils.errors import InsightGenerationError, InsightInputError, InsightModelError
from utils.seasonal_analysis import get_holidays_in_period, analyze_seasonal_performance, detect_anomalies

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
        
        # Create metadata for dataset classification
        metadata = {
            'column_types': {col: str(df[col].dtype) for col in df.columns}
        }
        
        # Validate dataset is sales-related
        is_sales, reason = classify_dataset(df, metadata)
        
        if not is_sales:
            raise HTTPException(
                status_code=400, 
                detail=f"Dataset validation failed: {reason}. Please upload sales-related data (transactions, orders, revenue records)."
            )
        
        print(f"✅ Dataset validated as sales data: {reason}")
        
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
            print(f"🔍 DEBUG: Received {len(selected_kpi_list)} selected KPIs: {selected_kpi_list}")
            print(f"🔍 DEBUG: Received {len(custom_kpi_list)} custom KPIs: {custom_kpi_list}")
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
        # Combine selected KPIs + custom KPIs for display
        all_kpis_to_display = selected_kpi_list.copy()
        for custom_kpi in custom_kpi_list:
            if custom_kpi.get('name') and custom_kpi['name'] not in all_kpis_to_display:
                all_kpis_to_display.append(custom_kpi['name'])
        
        print(f"🔍 DEBUG: Final KPIs to display: {all_kpis_to_display}")
        
        response['report'] = transform_to_frontend_report(
            result.get('calculated_kpis', {}),
            response['trends'],
            result.get('insights', ''),
            all_kpis_to_display  # Include custom KPIs in display
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
        previous_period = periods_sorted[-2] if len(periods_sorted) >= 2 else None
        
        latest_values = calculated_kpis.get(latest_period, {})
        previous_values = calculated_kpis.get(previous_period, {}) if previous_period else {}
        
        def extract_kpi_value(kpi_result):
            """Extract numeric value from KPI result (handles dict or direct value)."""
            if isinstance(kpi_result, dict):
                if kpi_result.get('success') is False:
                    return None
                return kpi_result.get('value')
            return kpi_result
        
        for kpi_name in selected_kpis:
            print(f"  🔍 Processing KPI: {kpi_name}, exists in data: {kpi_name in latest_values}")
            if kpi_name in latest_values:
                kpi_result = latest_values[kpi_name]
                value = extract_kpi_value(kpi_result)
                
                # Get previous value for comparison
                prev_value = None
                if previous_period and kpi_name in previous_values:
                    prev_value = extract_kpi_value(previous_values[kpi_name])
                
                # Format value and calculate change
                if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
                    value_str = "N/A"
                    description = "Calculation failed or no data available"
                    
                elif isinstance(value, dict):
                    # Categorical KPIs - skip from main KPI cards, but save for separate breakdown section
                    print(f"  Found categorical KPI: {kpi_name} (dict with {len(value)} items)")
                    continue  # Don't add to kpi_cards, will be handled separately
                        
                elif isinstance(value, (int, float)):
                    # Format numbers nicely
                    is_currency = 'revenue' in kpi_name.lower() or 'amount' in kpi_name.lower() or 'price' in kpi_name.lower()
                    is_percentage = 'percent' in kpi_name.lower() or 'rate' in kpi_name.lower()
                    is_rating = 'rating' in kpi_name.lower() or 'score' in kpi_name.lower()
                    
                    if is_currency:
                        value_str = f"${value:,.2f}"
                    elif is_percentage:
                        value_str = f"{value:.1f}%"
                    elif is_rating:
                        value_str = f"{value:.2f} / 5.0"
                    else:
                        value_str = f"{value:,.0f}"
                    
                    # Calculate period-over-period change
                    if prev_value and isinstance(prev_value, (int, float)):
                        change = value - prev_value
                        if prev_value != 0:
                            change_pct = (change / abs(prev_value)) * 100
                            trend = "↑" if change_pct > 2 else "↓" if change_pct < -2 else "→"
                            
                            if is_currency:
                                description = f"{trend} {change_pct:+.1f}% vs {str(previous_period)[:7]} (was ${prev_value:,.2f})"
                            elif is_percentage or is_rating:
                                description = f"{trend} {change:+.2f} points vs {str(previous_period)[:7]} (was {prev_value:.2f})"
                            else:
                                description = f"{trend} {change_pct:+.1f}% vs {str(previous_period)[:7]} (was {prev_value:,.0f})"
                        else:
                            description = f"Period: {str(latest_period)[:7]}"
                    else:
                        description = f"Period: {str(latest_period)[:7]}"
                else:
                    value_str = str(value)
                    description = f"Latest value for {kpi_name}"
                
                # Generate sparkline data (last 10 periods for this KPI)
                sparkline_data = []
                for period in periods_sorted[-10:]:  # Last 10 periods
                    if kpi_name in calculated_kpis.get(period, {}):
                        period_value = extract_kpi_value(calculated_kpis[period][kpi_name])
                        if period_value and isinstance(period_value, (int, float)):
                            sparkline_data.append(float(period_value))
                
                # Add seasonal analysis if we have month data
                seasonal_info = None
                if latest_period and previous_period:
                    try:
                        latest_month = int(str(latest_period).split('-')[1])
                        if value and prev_value and isinstance(value, (int, float)) and isinstance(prev_value, (int, float)):
                            seasonal_info = analyze_seasonal_performance(value, prev_value, latest_month)
                    except:
                        pass
                
                # Check if this is a custom KPI (has formula description)
                formula_description = None
                if isinstance(kpi_result, dict) and 'description' in kpi_result:
                    formula_description = kpi_result.get('description')
                
                kpi_cards.append({
                    'name': kpi_name,
                    'value': value_str,
                    'description': description,  # Period comparison
                    'formula_description': formula_description,  # Custom KPI formula explanation
                    'sparkline': sparkline_data,
                    'seasonal': seasonal_info
                })
    
    # Create trend charts from time series data (only for numeric KPIs)
    trend_charts = []
    for kpi_name in selected_kpis[:6]:  # Limit to 6 trends
        chart_data = []
        for period in sorted(periods):
            if kpi_name in calculated_kpis.get(period, {}):
                kpi_result = calculated_kpis[period][kpi_name]
                
                # Extract value from dict if needed
                if isinstance(kpi_result, dict):
                    if kpi_result.get('success') is False:
                        continue  # Skip failed calculations
                    value = kpi_result.get('value')
                else:
                    value = kpi_result
                
                # Only add numeric values to charts (skip dicts/categorical KPIs)
                if value is not None and not isinstance(value, dict):
                    if not (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
                        try:
                            chart_data.append({
                                'x_axis': str(period)[:10],  # Date string (YYYY-MM-DD)
                                'y_axis': float(value)
                            })
                        except (ValueError, TypeError):
                            continue  # Skip invalid values
        
        if len(chart_data) >= 2:  # Only create chart if we have at least 2 data points
            # Get date range for holiday detection (only major shopping holidays)
            try:
                from datetime import datetime, timedelta
                start_date = datetime.strptime(chart_data[0]['x_axis'], '%Y-%m-%d').date()
                end_date = datetime.strptime(chart_data[-1]['x_axis'], '%Y-%m-%d').date()
                all_holidays = get_holidays_in_period(start_date, end_date)
                
                # Only include holidays within 7 days of actual data points
                data_dates = [datetime.strptime(d['x_axis'], '%Y-%m-%d').date() for d in chart_data]
                holidays = []
                for holiday in all_holidays:
                    holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
                    # Check if holiday is within 7 days of any data point
                    if any(abs((holiday_date - data_date).days) <= 7 for data_date in data_dates):
                        holidays.append(holiday)
                
                # Limit to max 5 holidays per chart
                holidays = holidays[:5]
            except:
                holidays = []
            
            # Detect anomalies in the data
            values = [point['y_axis'] for point in chart_data]
            anomaly_indices = detect_anomalies(values)
            
            # Calculate trend insights
            if len(values) >= 2:
                first_val = values[0]
                last_val = values[-1]
                max_val = max(values)
                min_val = min(values)
                avg_val = sum(values) / len(values)
                
                # Overall trend direction
                if last_val > first_val * 1.1:
                    trend_direction = "upward"
                    trend_pct = ((last_val - first_val) / first_val) * 100
                elif last_val < first_val * 0.9:
                    trend_direction = "downward"
                    trend_pct = ((last_val - first_val) / first_val) * 100
                else:
                    trend_direction = "stable"
                    trend_pct = 0
                
                # Volatility
                std_dev = (sum((v - avg_val) ** 2 for v in values) / len(values)) ** 0.5
                volatility = "high" if std_dev > avg_val * 0.3 else "moderate" if std_dev > avg_val * 0.1 else "low"
                
                insights_text = {
                    'trend': trend_direction,
                    'change': f"{trend_pct:+.1f}%" if trend_pct != 0 else "minimal change",
                    'peak': f"{max_val:,.0f}",
                    'low': f"{min_val:,.0f}",
                    'average': f"{avg_val:,.0f}",
                    'volatility': volatility,
                    'anomalies_count': len(anomaly_indices)
                }
            else:
                insights_text = {}
            
            trend_charts.append({
                'title': f'{kpi_name} Over Time',
                'description': f'Historical trend showing {kpi_name.lower()} across time periods',
                'chartData': chart_data,
                'holidays': holidays,
                'anomalies': anomaly_indices,
                'insights': insights_text
            })
    
    # Generate dynamic KPI explanations based on detected KPIs
    kpi_explanations = []
    for kpi in kpi_cards:
        kpi_name = kpi['name'].lower()
        explanation = {}
        
        # Check if this is a custom KPI (skip from explanations section)
        if kpi.get('formula_description'):
            # Custom KPI - skip from "What This Means" section
            # The formula description is already shown in the KPI card
            continue
        
        # Revenue-related KPIs
        if any(keyword in kpi_name for keyword in ['revenue', 'sales', 'income', 'profit']):
            explanation = {
                'icon': '📊',
                'title': 'Revenue & Sales',
                'description': f"Your {kpi['name']} shows how much money your business is bringing in. The percentage change (↑ or ↓) compares this period to the previous one. A negative number means sales are down, which needs attention. Look at which products or services are performing well and which aren't."
            }
        # Customer-related KPIs
        elif any(keyword in kpi_name for keyword in ['customer', 'buyer', 'client', 'user']):
            explanation = {
                'icon': '👥',
                'title': 'Customer Growth',
                'description': f"The {kpi['name']} shows if you're attracting and retaining buyers. Growing customers but falling revenue? People are buying cheaper items. Steady customers but rising revenue? Your marketing and retention strategies are working!"
            }
        # Transaction/Order KPIs
        elif any(keyword in kpi_name for keyword in ['transaction', 'order', 'purchase']):
            explanation = {
                'icon': '🛒',
                'title': 'Transaction Volume',
                'description': f"This metric ({kpi['name']}) tracks the total number of transactions. More transactions with steady revenue means smaller average orders. Fewer transactions with rising revenue means customers are buying more per order."
            }
        # Average value KPIs
        elif any(keyword in kpi_name for keyword in ['average', 'avg', 'mean']) and any(word in kpi_name for word in ['price', 'value', 'amount']):
            explanation = {
                'icon': '💰',
                'title': 'Average Purchase Value',
                'description': f"The {kpi['name']} shows how much each customer spends on average. If this drops, customers are buying less expensive items or fewer items per order. Consider bundling products or offering upsells to increase this number."
            }
        # Rating/Review KPIs
        elif any(keyword in kpi_name for keyword in ['rating', 'review', 'satisfaction', 'score']):
            explanation = {
                'icon': '⭐',
                'title': 'Customer Satisfaction',
                'description': f"Your {kpi['name']} reflects product quality and customer service. Ratings below 3.5 signal problems. Read negative reviews to identify issues, and work on improving product quality, delivery speed, or customer support."
            }
        # Product/Item KPIs
        elif any(keyword in kpi_name for keyword in ['product', 'item', 'sku', 'category']):
            explanation = {
                'icon': '📦',
                'title': 'Product Performance',
                'description': f"The {kpi['name']} helps you understand which products drive your business. Focus on promoting and stocking your best sellers, and consider discontinuing or discounting underperforming items."
            }
        # Payment method KPIs
        elif any(keyword in kpi_name for keyword in ['payment', 'method', 'card', 'cash']):
            explanation = {
                'icon': '💳',
                'title': 'Payment Preferences',
                'description': f"This shows {kpi['name']} breakdown. Understanding payment preferences helps you optimize checkout, reduce cart abandonment, and potentially negotiate better payment processing fees."
            }
        # Generic KPI
        else:
            explanation = {
                'icon': '📈',
                'title': kpi['name'],
                'description': f"This metric ({kpi['name']}) tracks {kpi.get('description', 'a key business indicator')}. Monitor the trend and percentage change to identify patterns and take action when performance deviates from expectations."
            }
        
        # Only add unique explanations (avoid duplicates)
        if explanation and not any(e['title'] == explanation['title'] for e in kpi_explanations):
            kpi_explanations.append(explanation)
    
    # Parse insights markdown into sections
    insights_list = []
    recommendations_list = []
    summary = ""
    
    if insights:
        lines = insights.split('\n')
        current_section = None
        numbered_pattern = re.compile(r'^\d+\.\s+\*\*')  # Match "1. **"
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if '## Executive Summary' in line or '## Summary' in line or '# Executive Summary' in line:
                current_section = 'summary'
                continue
            elif '## Recommendations' in line or '## Recommendation' in line or '# Recommendations' in line:
                current_section = 'recommendations'
                continue
            elif '## Insights' in line or '## Key Insights' in line or '# Key Insights' in line:
                current_section = 'insights'
                continue
            elif '##' in line:
                current_section = None  # Unknown section
                continue
            
            # Extract content
            if line:
                # Handle numbered lists (1. **Action:** ...)
                if numbered_pattern.match(line):
                    # Extract action text (remove ** markers)
                    content = re.sub(r'\*\*([^*]+)\*\*:\s*', r'\1: ', line)
                    content = re.sub(r'^\d+\.\s+', '', content)  # Remove numbering
                    if current_section == 'recommendations':
                        recommendations_list.append(content)
                    elif current_section == 'insights':
                        insights_list.append(content)
                # Handle bullet points
                elif line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                    bullet = line[2:].strip()
                    if current_section == 'insights':
                        insights_list.append(bullet)
                    elif current_section == 'recommendations':
                        recommendations_list.append(bullet)
                # Regular paragraphs
                elif not line.startswith('#') and current_section == 'summary':
                    summary += line + " "
    
    # Ensure we have at least some content
    if not summary and insights:
        # Try to extract first paragraph as summary
        paragraphs = [p.strip() for p in insights.split('\n\n') if p.strip() and not p.startswith('#')]
        if paragraphs:
            summary = paragraphs[0]
    
    if not summary:
        summary = "Analysis complete. Key performance indicators have been calculated and trends identified across time periods."
    
    if not insights_list and not recommendations_list:
        # If parsing failed, try to extract any meaningful content
        sentences = re.split(r'[.!?]\s+', insights)
        for sentence in sentences[:5]:
            if len(sentence) > 30 and not sentence.startswith('#'):
                insights_list.append(sentence.strip() + '.')
        
        if not insights_list:
            insights_list = [
                "Sales data has been analyzed across all time periods",
                "Key performance indicators show measurable trends",
                "Historical patterns provide insights for future planning"
            ]
    
    # Extract categorical breakdowns (safely, won't crash if missing)
    categorical_breakdowns = []
    try:
        if periods and latest_period:
            latest_values = calculated_kpis.get(latest_period, {})
            
            for kpi_name, kpi_result in latest_values.items():
                # Extract value from result dict
                value = kpi_result.get('value') if isinstance(kpi_result, dict) else kpi_result
                
                # Only process categorical (dict) KPIs
                if isinstance(value, dict) and len(value) > 0:
                    # Determine if it's currency-based
                    is_currency = 'revenue' in kpi_name.lower() or 'sales' in kpi_name.lower() or 'amount' in kpi_name.lower()
                    
                    # Sort and get top 10 items
                    sorted_items = sorted(value.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)[:10]
                    
                    # Format items for display
                    items = []
                    for category, val in sorted_items:
                        if isinstance(val, (int, float)):
                            formatted_val = f"${val:,.2f}" if is_currency else f"{val:,.0f}"
                            items.append({
                                'name': str(category),
                                'value': formatted_val,
                                'raw_value': float(val)
                            })
                    
                    if items:  # Only add if we have valid items
                        categorical_breakdowns.append({
                            'title': kpi_name,
                            'items': items,
                            'total_categories': len(value),
                            'is_currency': is_currency
                        })
    except Exception as e:
        print(f"Warning: Error extracting categorical breakdowns: {e}")
        # Don't crash, just continue without breakdowns
        categorical_breakdowns = []
    
    return {
        'reportTitle': 'Sales Analysis Report',
        'summary': summary.strip(),
        'kpis': kpi_cards,
        'kpiExplanations': kpi_explanations,
        'categoricalBreakdowns': categorical_breakdowns,  # NEW: Safe categorical data
        'trends': trend_charts,
        'insights': insights_list[:3],  # Limit to 3
        'recommendations': recommendations_list[:3]  # Limit to 3
    }


@app.post("/api/generate_pdf")
async def generate_pdf_report(
    file_id: str = Form(...),
    report_data: str = Form(...)  # JSON string of full report structure
):
    """
    Generate a professional, text-based PDF report.
    
    Args:
    - file_id: File identifier  
    - report_data: JSON string containing complete report structure
    
    Returns:
    - PDF file as base64 encoded string
    """
    import traceback
    print(f"\n=== PDF Generation Request ===")
    print(f"File ID: {file_id}")
    
    try:
        # Parse report data
        try:
            report = json.loads(report_data)
            print(f"Report data keys: {report.keys()}")
        except Exception as parse_error:
            print(f"JSON parse error: {parse_error}")
            raise HTTPException(status_code=400, detail=f"Invalid report data JSON: {str(parse_error)}")
        
        # For backward compatibility, check if it's the old format (insights + trend_images)
        # or new format (full report structure)
        if 'insights' in report and isinstance(report.get('insights'), str):
            # Old format - use legacy PDF generator
            print("Using legacy PDF format (markdown + images)")
            insights = report.get('insights', '')
            trend_images_b64 = report.get('trend_images', [])
            
            # Decode trend images
            trend_images = []
            for idx, img_b64 in enumerate(trend_images_b64):
                try:
                    if img_b64.startswith('data:image'):
                        img_b64 = img_b64.split(',')[1]
                    img_data = base64.b64decode(img_b64)
                    if len(img_data) > 0:
                        trend_images.append(io.BytesIO(img_data))
                except:
                    continue
            
            output = io.BytesIO()
            create_pdf_report(
                markdown_text=insights,
                trend_images=trend_images,
                output_path=output,
                title="Sales Analysis Report",
                page_size=A4
            )
        else:
            # New format - use text-based PDF generator
            print("Using new text-based PDF format")
            output = io.BytesIO()
            create_text_pdf_report(
                report_data=report,
                output_path=output,
                title=report.get('reportTitle', 'Sales Analysis Report')
            )
        
        # Encode PDF to base64
        output.seek(0)
        pdf_data = output.read()
        print(f"PDF generated successfully ({len(pdf_data)} bytes)")
        
        pdf_b64 = base64.b64encode(pdf_data).decode('utf-8')
        
        return JSONResponse({
            'success': True,
            'pdf_base64': pdf_b64,
            'filename': f'report_{file_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
        })
    
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR /api/generate_pdf:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.get("/api/custom_kpi/columns/{file_id}")
async def get_available_columns(file_id: str):
    """Get available columns for custom KPI creation."""
    try:
        # Get the cleaned dataframe from storage
        if file_id not in _file_storage:
            raise HTTPException(status_code=404, detail="File not found. Please re-upload.")
        
        df = _file_storage[file_id]
        
        from modules.custom_kpi_calculator import CustomKPICalculator
        calculator = CustomKPICalculator(df)
        columns = calculator.get_available_columns()
        templates = calculator.get_formula_templates()
        
        return JSONResponse({
            'columns': columns,
            'templates': templates
        })
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR /api/custom_kpi/columns:\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/custom_kpi/calculate/{file_id}")
async def calculate_custom_kpi(
    file_id: str,
    kpi_name: str = Form(...),
    formula: str = Form(...)
):
    """Calculate a custom KPI using the provided formula."""
    try:
        # Get the cleaned dataframe from storage
        if file_id not in _file_storage:
            raise HTTPException(status_code=404, detail="File not found. Please re-upload.")
        
        df = _file_storage[file_id]
        
        from modules.custom_kpi_calculator import CustomKPICalculator
        calculator = CustomKPICalculator(df)
        
        # Validate formula first
        validation = calculator.validate_formula(formula)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['error'])
        
        # Calculate KPI
        result = calculator.calculate_kpi(formula, kpi_name)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return JSONResponse({
            'success': True,
            'kpi': {
                'name': kpi_name,
                'value': result['value'],
                'formula': result['formula'],
                'description': result['description']
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR /api/custom_kpi/calculate:\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)

