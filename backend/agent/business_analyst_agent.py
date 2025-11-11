"""
LangGraph-based agentic workflow for DataMind.
Pipeline: CSV Upload → Auto-Clean → KPI Detection → Calculation → Insights

State flows through these nodes:
1. ingest_node: Load and analyze CSV
2. auto_clean_node: Automated statistical cleaning (rule-based)
3. load_kpis_node: Load KPI definitions
4. detect_kpis_node: Match columns to KPIs (fuzzy + semantic)
5. calculate_kpis_node: Compute KPIs per time period
6. extract_trends_node: Generate Prophet visualizations
7. generate_insights_node: Use Gemini for business insights
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any
import pandas as pd
from io import BytesIO
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try alternative path
    load_dotenv()

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import modules
from modules.Ingestion_Module.ingest_csv import ingest_csv
from modules.Ingestion_Module.dataset_classification import classify_dataset
from modules.KPI_Module.KPI_Engine import (
    export_kpis,
    match_kpis,
    build_dependency_graph,
    calculate_kpis,
    calculate_kpis_temporal,
    normalize_column_name,
)
from modules.KPI_Module.KPI_Detection import KPI_Detection
from modules.Trend_Extractor.Trend_Extraction import detect_trends
from modules.Insights_Generator.generate_insights import generate_insights
from utils.extract_kpi_summary import extract_kpi_summary
from models.gemini import GeminiClient
from modules.Cleaning_Module.statistical_cleaner import clean_retail_data


class AnalysisState(TypedDict):
    """Shared state across all workflow nodes."""
    
    # Input
    csv_data: pd.DataFrame
    csv_filename: str
    
    # Cleaning phase
    cleaning_plan: Dict[str, Any]
    user_choices: Dict[str, bool]
    cleaned_data: Optional[pd.DataFrame]
    cleaning_logs: List[str]
    
    # KPI phase
    kpi_definitions: Dict[str, Any]
    detected_kpis: Dict[str, Any]
    calculated_kpis: Dict[str, Any]
    kpi_summary: Dict[str, Any]
    
    # Trend phase
    trend_images: List[BytesIO]
    
    # Insights phase
    insights: str
    
    # Metadata
    agent_reasoning: str
    error: Optional[str]
    current_step: str


def create_agent() -> Any:
    """Build and return the compiled LangGraph workflow."""
    
    workflow = StateGraph(AnalysisState)
    
    # ========================================================================
    # NODE 1: INGEST & ANALYZE
    # ========================================================================
    def ingest_node(state: AnalysisState) -> AnalysisState:
        """Load and analyze the CSV dataset."""
        try:
            state['current_step'] = 'ingest'
            
            # Basic validation
            if state['csv_data'].empty:
                raise ValueError("CSV is empty")
            
            state['cleaning_logs'].append(
                f"✅ Ingested {len(state['csv_data'])} rows, {len(state['csv_data'].columns)} columns"
            )
            state['agent_reasoning'] = (
                f"Analyzed CSV: {len(state['csv_data'])} rows, {len(state['csv_data'].columns)} columns. "
                f"Columns: {list(state['csv_data'].columns)}"
            )
            
        except Exception as e:
            state['error'] = f"Ingestion failed: {str(e)}"
            state['current_step'] = 'error'
        
        return state
    
    # ========================================================================
    # NODE 2: PROPOSE CLEANING PLAN (Using Statistical Cleaner)
    # ========================================================================
    def propose_cleaning_node(state: AnalysisState) -> AnalysisState:
        """Propose cleaning plan using statistical analysis."""
        try:
            state['current_step'] = 'propose_cleaning'
            
            df = state['csv_data']
            
            # Import the cleaner to analyze data
            from modules.Cleaning_Module.statistical_cleaner import StatisticalCleaner
            cleaner = StatisticalCleaner()
            
            # Profile the data to detect issues
            cleaner._profile_columns(df)
            
            # Build cleaning plan with individual steps
            plan = {
                'steps': [],
                'column_types': cleaner.column_profiles,
                'original_shape': df.shape,
            }
            
            # Step 1: Date parsing
            date_cols = [col for col, profile in cleaner.column_profiles.items() 
                        if profile['semantic_type'] == 'date']
            if date_cols:
                plan['steps'].append({
                    'id': 'parse_dates',
                    'action': 'parse_dates',
                    'columns': date_cols,
                    'reason': f'Standardize date formats in {len(date_cols)} column(s)'
                })
            
            # Step 2: Text standardization
            cat_cols = [col for col, profile in cleaner.column_profiles.items() 
                       if profile['semantic_type'] in ['categorical', 'product', 'payment_method']]
            if cat_cols:
                plan['steps'].append({
                    'id': 'standardize_text',
                    'action': 'standardize_text',
                    'columns': cat_cols,
                    'reason': f'Normalize text in {len(cat_cols)} categorical column(s)'
                })
            
            # Step 3: Remove duplicates
            dup_count = df.duplicated().sum()
            if dup_count > 0:
                plan['steps'].append({
                    'id': 'remove_duplicates',
                    'action': 'remove_duplicates',
                    'count': int(dup_count),
                    'reason': f'Remove {dup_count} duplicate row(s)'
                })
            
            # Step 4: Handle negative values in revenue columns
            revenue_cols = [col for col, profile in cleaner.column_profiles.items() 
                          if profile['semantic_type'] == 'revenue']
            for col in revenue_cols:
                if col in df.columns and (df[col] < 0).any():
                    neg_count = (df[col] < 0).sum()
                    plan['steps'].append({
                        'id': f'fix_negative_{col}',
                        'action': 'fix_negative_values',
                        'column': col,
                        'count': int(neg_count),
                        'reason': f'Convert {neg_count} negative value(s) to absolute in {col}'
                    })
            
            # Step 5: Handle outliers
            numeric_cols = [col for col, profile in cleaner.column_profiles.items() 
                          if profile['semantic_type'] in ['revenue', 'quantity']]
            if numeric_cols:
                plan['steps'].append({
                    'id': 'handle_outliers',
                    'action': 'handle_outliers',
                    'columns': numeric_cols,
                    'reason': f'Detect and clip outliers in {len(numeric_cols)} numeric column(s)'
                })
            
            # Step 6: Handle missing values
            missing_info = []
            for col in df.columns:
                missing = df[col].isnull().sum()
                if missing > 0:
                    missing_info.append({'column': col, 'count': int(missing)})
            
            if missing_info:
                plan['steps'].append({
                    'id': 'fill_missing',
                    'action': 'fill_missing',
                    'missing_info': missing_info,
                    'reason': f'Impute missing values in {len(missing_info)} column(s)'
                })
            
            state['cleaning_plan'] = plan
            state['cleaning_logs'].append(f"📋 Proposed {len(plan['steps'])} cleaning steps")
            state['agent_reasoning'] = f"Analyzed data and proposed {len(plan['steps'])} cleaning steps"
            
        except Exception as e:
            state['error'] = f"Cleaning proposal failed: {str(e)}"
            state['current_step'] = 'error'
        
        return state
    
    # ========================================================================
    # NODE 3: APPLY SELECTED CLEANING STEPS
    # ========================================================================
    def apply_cleaning_node(state: AnalysisState) -> AnalysisState:
        """Execute only user-selected cleaning steps using statistical cleaner."""
        try:
            state['current_step'] = 'apply_cleaning'
            
            df = state['csv_data'].copy()
            user_choices = state.get('user_choices', {})
            plan = state.get('cleaning_plan', {})
            
            # If no user choices provided, assume all steps approved
            if not user_choices:
                user_choices = {step['id']: True for step in plan.get('steps', [])}
            
            # Apply each selected step
            from modules.Cleaning_Module.statistical_cleaner import StatisticalCleaner
            cleaner = StatisticalCleaner()
            cleaner._profile_columns(df)
            
            applied_count = 0
            for step in plan.get('steps', []):
                step_id = step['id']
                
                # Skip if user didn't select this step
                if not user_choices.get(step_id, False):
                    state['cleaning_logs'].append(f"⏭️  Skipped: {step['reason']}")
                    continue
                
                action = step['action']
                
                try:
                    if action == 'parse_dates':
                        for col in step.get('columns', []):
                            df[col] = cleaner._parse_dates(df[col], col)
                        state['cleaning_logs'].append(f"✅ {step['reason']}")
                        applied_count += 1
                    
                    elif action == 'standardize_text':
                        for col in step.get('columns', []):
                            df[col] = cleaner._standardize_text(df[col], col)
                        state['cleaning_logs'].append(f"✅ {step['reason']}")
                        applied_count += 1
                    
                    elif action == 'remove_duplicates':
                        before = len(df)
                        df = df.drop_duplicates()
                        after = len(df)
                        state['cleaning_logs'].append(f"✅ Removed {before - after} duplicates")
                        applied_count += 1
                    
                    elif action == 'fix_negative_values':
                        col = step['column']
                        df.loc[df[col] < 0, col] = df.loc[df[col] < 0, col].abs()
                        state['cleaning_logs'].append(f"✅ {step['reason']}")
                        applied_count += 1
                    
                    elif action == 'handle_outliers':
                        product_col = None
                        for col, profile in cleaner.column_profiles.items():
                            if profile['semantic_type'] == 'product':
                                product_col = col
                                break
                        
                        for col in step.get('columns', []):
                            if product_col and product_col in df.columns:
                                df = cleaner._detect_outliers_by_group(df, col, product_col)
                            else:
                                df = cleaner._detect_outliers_global(df, col)
                        state['cleaning_logs'].append(f"✅ {step['reason']}")
                        applied_count += 1
                    
                    elif action == 'fill_missing':
                        # Find product column for group-wise imputation
                        product_col = None
                        for col, profile in cleaner.column_profiles.items():
                            if profile['semantic_type'] == 'product':
                                product_col = col
                                break
                        
                        for info in step.get('missing_info', []):
                            col = info['column']
                            if col not in df.columns:
                                continue
                            
                            profile = cleaner.column_profiles.get(col, {})
                            semantic_type = profile.get('semantic_type', 'categorical')
                            
                            if semantic_type == 'revenue' and product_col:
                                df = cleaner._impute_by_group(df, col, product_col, method='median')
                            elif semantic_type in ['revenue', 'quantity']:
                                df[col].fillna(df[col].median(), inplace=True)
                            elif semantic_type == 'rating':
                                mode_val = df[col].mode()
                                if len(mode_val) > 0:
                                    df[col].fillna(mode_val[0], inplace=True)
                            elif semantic_type == 'date':
                                df[col].fillna(method='ffill', inplace=True)
                                df[col].fillna(method='bfill', inplace=True)
                            else:  # categorical
                                mode_val = df[col].mode()
                                if len(mode_val) > 0:
                                    df[col].fillna(mode_val[0], inplace=True)
                        
                        state['cleaning_logs'].append(f"✅ {step['reason']}")
                        applied_count += 1
                
                except Exception as step_error:
                    state['cleaning_logs'].append(f"⚠️  Error in {step['reason']}: {str(step_error)}")
            
            state['cleaned_data'] = df
            state['cleaning_logs'].append(f"📊 Applied {applied_count}/{len(plan.get('steps', []))} cleaning steps")
            state['agent_reasoning'] = f"Applied {applied_count} cleaning steps"
            
            # Calculate quality score
            completeness = (1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100 if df.shape[0] * df.shape[1] > 0 else 100
            state['cleaning_logs'].append(f"📊 Data Quality Score: {completeness:.1f}/100")
            
        except Exception as e:
            state['error'] = f"Cleaning execution failed: {str(e)}"
            state['current_step'] = 'error'
            # Fallback: use original data
            state['cleaned_data'] = state['csv_data']
        
        return state
    
    # ========================================================================
    # NODE 4: LOAD KPI DEFINITIONS
    # ========================================================================
    def load_kpis_node(state: AnalysisState) -> AnalysisState:
        """Load KPI definitions from YAML."""
        try:
            state['current_step'] = 'load_kpis'
            
            kpis = export_kpis()
            state['kpi_definitions'] = kpis
            state['cleaning_logs'].append(f"📊 Loaded {len(kpis)} KPI definitions")
            state['agent_reasoning'] = f"Loaded {len(kpis)} KPIs"
            
        except Exception as e:
            state['error'] = f"KPI loading failed: {str(e)}"
            state['current_step'] = 'error'
        
        return state
    
    # ========================================================================
    # NODE 5: DETECT KPIs (Fuzzy + Semantic Matching)
    # ========================================================================
    def detect_kpis_node(state: AnalysisState) -> AnalysisState:
        """Hybrid KPI Detection: YAML matching + LLM generation."""
        try:
            state['current_step'] = 'detect_kpis'
            
            df = state['cleaned_data'] if state['cleaned_data'] is not None else state['csv_data']
            kpis = state['kpi_definitions']
            
            # Use hybrid detection (YAML + LLM generation)
            detection_result = KPI_Detection(df, kpis, use_llm_generation=True)
            
            state['detected_kpis'] = detection_result['kpi_status']
            matched_count = len(detection_result['detected_kpis'])
            
            state['cleaning_logs'].append(f"🎯 Detected {matched_count} calculable KPIs")
            state['agent_reasoning'] = f"Detected {matched_count} KPIs via hybrid YAML + LLM generation"
            
        except Exception as e:
            import traceback
            print(f"KPI detection error:\n{traceback.format_exc()}")
            state['error'] = f"KPI detection failed: {str(e)}"
            state['current_step'] = 'error'
        
        return state
    
    # ========================================================================
    # NODE 6: CALCULATE KPIs
    # ========================================================================
    def calculate_kpis_node(state: AnalysisState) -> AnalysisState:
        """Calculate KPIs per time period."""
        try:
            state['current_step'] = 'calculate_kpis'
            
            df = state['cleaned_data'] if state['cleaned_data'] is not None else state['csv_data']
            detected_kpis = state['detected_kpis']
            
            # Filter calculable KPIs
            selected_kpis = {
                name: config
                for name, config in detected_kpis.items()
                if config.get('calculable')
            }
            
            if not selected_kpis:
                state['cleaning_logs'].append("⚠️  No calculable KPIs")
                state['calculated_kpis'] = {}
            else:
                # Build dependency order
                try:
                    dependency_order = build_dependency_graph(selected_kpis)
                except:
                    dependency_order = list(selected_kpis.keys())
                
                # Try temporal calculation
                try:
                    calc_result = calculate_kpis_temporal(df, selected_kpis, dependency_order)
                    state['calculated_kpis'] = calc_result
                    state['cleaning_logs'].append(f"📈 Calculated {len(selected_kpis)} KPIs (temporal)")
                except:
                    # Fallback to non-temporal
                    calc_result = calculate_kpis(df, selected_kpis, dependency_order)
                    state['calculated_kpis'] = calc_result
                    state['cleaning_logs'].append(f"📈 Calculated {len(selected_kpis)} KPIs")
            
            state['agent_reasoning'] = f"Calculated KPIs"
            
        except Exception as e:
            state['error'] = f"KPI calculation failed: {str(e)}"
            state['current_step'] = 'error'
        
        return state
    
    # ========================================================================
    # NODE 7: EXTRACT TRENDS
    # ========================================================================
    def extract_trends_node(state: AnalysisState) -> AnalysisState:
        """Generate trend visualizations using Prophet."""
        try:
            state['current_step'] = 'extract_trends'
            
            df = state['cleaned_data'] if state['cleaned_data'] is not None else state['csv_data']
            
            trend_images = detect_trends(df, period_type='Monthly')
            state['trend_images'] = trend_images
            state['cleaning_logs'].append(f"📉 Generated {len(trend_images)} trend charts")
            state['agent_reasoning'] = f"Extracted {len(trend_images)} visualizations"
            
        except Exception as e:
            state['error'] = f"Trend extraction failed: {str(e)}"
            state['current_step'] = 'error'
            state['trend_images'] = []  # Continue without trends
        
        return state
    
    # ========================================================================
    # NODE 8: GENERATE INSIGHTS (Gemini)
    # ========================================================================
    def generate_insights_node(state: AnalysisState) -> AnalysisState:
        """Generate AI insights using Gemini."""
        try:
            state['current_step'] = 'generate_insights'
            
            api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if not api_key:
                state['insights'] = "Gemini API key not configured"
                state['cleaning_logs'].append("ℹ️  Gemini insights skipped (no API key)")
            elif not state.get('trend_images') or len(state['trend_images']) == 0:
                state['insights'] = "No trend images available for insights generation"
                state['cleaning_logs'].append("ℹ️  Gemini insights skipped (no trend images)")
            else:
                try:
                    # Initialize Gemini client
                    llm_client = GeminiClient(
                        model_name="gemini-2.5-flash",
                        api_key=api_key
                    )
                    
                    kpi_data = {'calculated_kpis': state['calculated_kpis']}
                    
                    insights = generate_insights(
                        state['trend_images'],
                        kpi_data,
                        llm=llm_client,
                        temperature=0.6
                    )
                    
                    state['insights'] = insights or "Insights generation skipped"
                    state['cleaning_logs'].append("🧠 Generated Gemini insights")
                    state['agent_reasoning'] = "Generated insights"
                except Exception as e:
                    state['insights'] = f"Insights generation error: {str(e)}"
                    state['cleaning_logs'].append(f"⚠️  Gemini insights failed: {str(e)}")
                    # Don't set error state, continue with pipeline
            
        except Exception as e:
            state['error'] = f"Insights generation failed: {str(e)}"
            state['current_step'] = 'error'
            state['insights'] = f"Error: {str(e)}"
        
        return state
    
    # ========================================================================
    # BUILD GRAPH
    # ========================================================================
    
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("propose_cleaning", propose_cleaning_node)
    workflow.add_node("apply_cleaning", apply_cleaning_node)
    workflow.add_node("load_kpis", load_kpis_node)
    workflow.add_node("detect_kpis", detect_kpis_node)
    workflow.add_node("calculate_kpis", calculate_kpis_node)
    workflow.add_node("extract_trends", extract_trends_node)
    workflow.add_node("generate_insights", generate_insights_node)
    
    # Define edges
    workflow.add_edge("ingest", "propose_cleaning")
    workflow.add_edge("propose_cleaning", "apply_cleaning")
    workflow.add_edge("apply_cleaning", "load_kpis")
    workflow.add_edge("load_kpis", "detect_kpis")
    workflow.add_edge("detect_kpis", "calculate_kpis")
    workflow.add_edge("calculate_kpis", "extract_trends")
    workflow.add_edge("extract_trends", "generate_insights")
    workflow.add_edge("generate_insights", END)
    
    workflow.set_entry_point("ingest")
    
    return workflow.compile()


def run_proposal_phase(
    csv_data: pd.DataFrame,
    csv_filename: str
) -> Dict[str, Any]:
    """
    Phase 1: Analyze data and propose cleaning plan.
    
    Args:
        csv_data: Loaded DataFrame
        csv_filename: Original filename
    
    Returns:
        Dictionary with cleaning plan and column types
    """
    from modules.Cleaning_Module.statistical_cleaner import StatisticalCleaner
    
    try:
        cleaner = StatisticalCleaner()
        cleaner._profile_columns(csv_data)
        
        # Build cleaning plan with individual steps
        import math
        
        # Clean column profiles - remove NaN/inf values for JSON serialization
        clean_profiles = {}
        for col, profile in cleaner.column_profiles.items():
            clean_profile = {}
            for key, value in profile.items():
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        clean_profile[key] = None
                    else:
                        clean_profile[key] = value
                else:
                    clean_profile[key] = value
            clean_profiles[col] = clean_profile
        
        # Clean data preview - replace NaN with None for JSON
        preview_df = csv_data.head(5).fillna('')
        
        # Build column-wise cleaning plan
        columns_plan = []
        global_steps = []
        
        for col in csv_data.columns:
            profile = clean_profiles.get(col, {})
            col_steps = []
            
            semantic_type = profile.get('semantic_type', 'unknown')
            missing_count = int(csv_data[col].isnull().sum())
            
            # Date parsing
            if semantic_type == 'date':
                col_steps.append({
                    'id': f'{col}_parse_date',
                    'action': 'parse_date',
                    'reason': 'Convert to standardized datetime format',
                    'recommended': True
                })
            
            # Text standardization for categorical columns
            if semantic_type in ['categorical', 'product', 'payment_method']:
                col_steps.append({
                    'id': f'{col}_standardize_text',
                    'action': 'standardize_text',
                    'reason': 'Normalize text (trim, lowercase, remove special chars)',
                    'recommended': True
                })
            
            # Fix negative values in revenue/quantity columns
            if semantic_type in ['revenue', 'quantity']:
                try:
                    neg_count = int((csv_data[col] < 0).sum())
                    if neg_count > 0:
                        col_steps.append({
                            'id': f'{col}_fix_negative',
                            'action': 'fix_negative',
                            'reason': f'Convert {neg_count} negative value(s) to absolute',
                            'recommended': True
                        })
                except:
                    pass
            
            # Handle outliers for numeric columns
            if semantic_type in ['revenue', 'quantity']:
                col_steps.append({
                    'id': f'{col}_handle_outliers',
                    'action': 'handle_outliers',
                    'reason': 'Detect and clip statistical outliers using IQR method',
                    'recommended': False  # Optional - can be aggressive
                })
            
            # Missing value imputation
            if missing_count > 0:
                imputation_method = 'median' if semantic_type in ['revenue', 'quantity'] else 'mode'
                col_steps.append({
                    'id': f'{col}_fill_missing',
                    'action': 'fill_missing',
                    'reason': f'Impute {missing_count} missing value(s) using {imputation_method}',
                    'recommended': True
                })
            
            # Only add column to plan if it has cleaning steps
            if col_steps:
                columns_plan.append({
                    'column': col,
                    'type': semantic_type,
                    'steps': col_steps,
                    'missing_count': missing_count,
                    'total_rows': len(csv_data)
                })
        
        # Global steps (affect entire dataset, not column-specific)
        dup_count = int(csv_data.duplicated().sum())
        if dup_count > 0:
            global_steps.append({
                'id': 'remove_duplicates',
                'action': 'remove_duplicates',
                'reason': f'Remove {dup_count} duplicate row(s) across all columns',
                'recommended': True,
                'count': dup_count
            })
        
        plan = {
            'columns': columns_plan,
            'global_steps': global_steps,
            'column_types': {col: profile['semantic_type'] 
                           for col, profile in clean_profiles.items()},
            'original_shape': list(csv_data.shape),
            'data_preview': preview_df.to_dict('records'),
            'summary': {
                'total_columns': len(csv_data.columns),
                'columns_needing_cleaning': len(columns_plan),
                'total_cleaning_steps': sum(len(c['steps']) for c in columns_plan) + len(global_steps)
            }
        }
        
        return plan
        
    except Exception as e:
        import traceback
        print(f"ERROR in run_proposal_phase:\n{traceback.format_exc()}")
        return {
            'error': str(e),
            'columns': [],
            'global_steps': [],
            'column_types': {},
            'original_shape': list(csv_data.shape),
            'summary': {
                'total_columns': 0,
                'columns_needing_cleaning': 0,
                'total_cleaning_steps': 0
            }
        }


def run_full_pipeline(
    csv_data: pd.DataFrame,
    csv_filename: str,
    user_choices: Dict[str, bool],
    custom_kpis: Optional[List[Dict[str, str]]] = None
) -> AnalysisState:
    """
    Run the complete analysis pipeline.
    
    Args:
        csv_data: Loaded DataFrame
        csv_filename: Original filename
        user_choices: User approval for cleaning steps {step_id: approved_bool}
        custom_kpis: Optional list of custom KPI definitions
    
    Returns:
        Final analysis state with all results
    """
    
    agent = create_agent()
    
    initial_state = AnalysisState(
        csv_data=csv_data,
        csv_filename=csv_filename,
        cleaning_plan={},
        user_choices=user_choices,
        cleaned_data=None,
        cleaning_logs=[],
        kpi_definitions={},
        detected_kpis={},
        calculated_kpis={},
        kpi_summary={},
        trend_images=[],
        insights="",
        agent_reasoning="",
        error=None,
        current_step="start"
    )
    
    # Store custom KPIs in state (we'll use them in KPI detection)
    if custom_kpis:
        initial_state['custom_kpis'] = custom_kpis
    
    result = agent.invoke(initial_state)
    return result
