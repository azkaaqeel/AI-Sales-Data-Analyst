"""Profile performance of the data processing pipeline."""
import sys
import time
from pathlib import Path
import pandas as pd

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def time_function(func_name, func, *args, **kwargs):
    """Time a function and print results."""
    print(f"\n⏱️  {func_name}...")
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    print(f"   ✅ Done in {elapsed:.2f}s")
    return result, elapsed

def profile_pipeline(csv_path: str):
    """Profile each step of the pipeline."""
    print("=" * 70)
    print("🔍 PERFORMANCE PROFILING")
    print("=" * 70)
    
    timings = {}
    
    # Step 1: Load CSV
    print(f"\n📂 Testing with: {Path(csv_path).name}")
    df, timings['load_csv'] = time_function(
        "Loading CSV",
        pd.read_csv,
        csv_path
    )
    print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    
    # Step 2: Dataset Classification
    from modules.Ingestion_Module.dataset_classification import classify_dataset
    metadata = {'column_types': {col: str(df[col].dtype) for col in df.columns}}
    
    _, timings['classify'] = time_function(
        "Dataset Classification (LLM call)",
        classify_dataset,
        df, metadata
    )
    
    # Step 3: Cleaning Plan Generation
    from agent.business_analyst_agent import run_proposal_phase
    
    result, timings['cleaning_plan'] = time_function(
        "Cleaning Plan Generation (LLM call)",
        run_proposal_phase,
        df
    )
    
    # Step 4: Apply Cleaning
    cleaned_df = result.get('cleaned_df', df)
    print(f"\n⏱️  Applying Cleaning (simulated - selecting all steps)...")
    start = time.time()
    # In real scenario, statistical_cleaner.clean() is called
    timings['apply_cleaning'] = time.time() - start
    print(f"   ✅ Done in {timings['apply_cleaning']:.2f}s")
    
    # Step 5: KPI Detection
    from modules.KPI_Module.hybrid_kpi_detection import detect_kpis_hybrid
    
    _, timings['kpi_detection'] = time_function(
        "KPI Detection (Hybrid: YAML + LLM)",
        detect_kpis_hybrid,
        cleaned_df
    )
    
    # Step 6: Period Detection & KPI Calculation
    from utils.time_period_detection import determine_period_type, add_period_column
    from modules.KPI_Module.kpi_calculation import calculate_kpis_over_time
    
    period_type, timings['period_detection'] = time_function(
        "Period Type Detection",
        determine_period_type,
        cleaned_df
    )
    
    df_with_period, timings['add_period'] = time_function(
        "Adding Period Column",
        add_period_column,
        cleaned_df, period_type
    )
    
    # Get sample KPIs
    sample_kpis = [
        {'name': 'Total Revenue', 'formula': "df['Selling Price (INR)'].sum()"},
        {'name': 'Average Purchase', 'formula': "df['Selling Price (INR)'].mean()"},
    ]
    
    _, timings['kpi_calculation'] = time_function(
        "KPI Calculation Over Time",
        calculate_kpis_over_time,
        df_with_period, sample_kpis, period_type
    )
    
    # Step 7: Trend Forecasting
    from modules.Forecast_Module.forecast_trends import forecast_trends
    
    _, timings['forecasting'] = time_function(
        "Prophet Forecasting",
        forecast_trends,
        df_with_period, 'Selling Price (INR)', period_type
    )
    
    # Step 8: Insights Generation (simulated - no images)
    print(f"\n⏱️  Insights Generation (LLM call - skipped in test)...")
    timings['insights'] = 0.0  # Would be ~3-5s with LLM
    print(f"   ⏭️  Skipped (would take ~3-5s)")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 70)
    
    total_time = sum(timings.values())
    
    # Sort by time taken
    sorted_timings = sorted(timings.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Step':<30} {'Time':<10} {'% of Total':<12}")
    print("-" * 70)
    
    for step, duration in sorted_timings:
        if duration > 0:
            percentage = (duration / total_time) * 100
            print(f"{step:<30} {duration:>6.2f}s    {percentage:>5.1f}%")
    
    print("-" * 70)
    print(f"{'TOTAL':<30} {total_time:>6.2f}s")
    
    # Identify bottlenecks
    print("\n🐌 BOTTLENECKS (Steps > 2 seconds):")
    bottlenecks = [(step, dur) for step, dur in sorted_timings if dur > 2.0]
    
    if bottlenecks:
        for step, duration in bottlenecks:
            print(f"   • {step}: {duration:.2f}s")
            
            # Suggest optimizations
            if 'kpi_detection' in step.lower() or 'cleaning_plan' in step.lower():
                print(f"     💡 Optimization: Cache LLM results or use smaller model")
            elif 'forecasting' in step.lower():
                print(f"     💡 Optimization: Reduce forecast periods or use simpler model")
            elif 'classify' in step.lower():
                print(f"     💡 Optimization: Skip for known datasets or use heuristics only")
    else:
        print("   ✅ No significant bottlenecks!")
    
    print("\n" + "=" * 70)
    
    return timings

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    
    # Load env
    load_dotenv()
    
    # Test with Fashion Retail dataset
    csv_path = Path(__file__).parent / "Fashion_Retail_Sales.csv"
    
    if not csv_path.exists():
        print(f"❌ Dataset not found: {csv_path}")
        print(f"   Please place Fashion_Retail_Sales.csv in {Path(__file__).parent}")
        sys.exit(1)
    
    try:
        timings = profile_pipeline(str(csv_path))
    except Exception as e:
        print(f"\n❌ Error during profiling: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

