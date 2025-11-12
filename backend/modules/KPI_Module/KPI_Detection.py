from modules.KPI_Module.KPI_Engine import match_column, normalize_column_name, match_kpis, calculate_semantic_similarity
from modules.KPI_Module.llm_kpi_generator import llm_generate_kpis, merge_kpis

def KPI_Detection(df, combined_kpis, use_llm_generation=True):
    """
    Hybrid KPI Detection:
    1. Try matching YAML KPIs with column mapping
    2. Generate additional KPIs using LLM based on available columns
    3. Merge both for maximum coverage
    
    Args:
        df: DataFrame to analyze
        combined_kpis: KPIs from YAML files
        use_llm_generation: Whether to use LLM for additional KPIs
    
    Returns:
        Dict with detected KPIs and status
    """
    # Normalize column names
    original_columns = df.columns.tolist()
    df.columns = [normalize_column_name(col) for col in df.columns]
    df_columns = df.columns.tolist()
    
    # Phase 1: Match YAML KPIs (with LLM mapping, no need for semantic embeddings)
    print("\n📋 Phase 1: Matching YAML KPIs...")
    kpi_status = match_kpis(df_columns, combined_kpis=combined_kpis, df=df, semantic_match_fn=None)
    
    # Count how many YAML KPIs matched
    yaml_matched_count = sum(1 for data in kpi_status.values() if data.get("calculable", False))
    print(f"   ✅ Matched {yaml_matched_count}/{len(combined_kpis)} YAML KPIs")
    
    # Phase 2: LLM Generate Additional KPIs (if enabled and low match rate)
    final_kpi_status = kpi_status.copy()
    
    if use_llm_generation:
        match_rate = yaml_matched_count / len(combined_kpis) if combined_kpis else 0
        
        # Only use LLM generation for very low match rates (< 30%) to improve latency
        if match_rate < 0.3:  # If less than 30% matched, use LLM
            print(f"\n🤖 Phase 2: LLM KPI Generation (match rate: {match_rate:.1%})...")
            
            # Prepare sample data for LLM
            sample_data = {}
            for col in original_columns[:10]:  # First 10 columns only
                sample_data[col] = df[normalize_column_name(col)].dropna().head(3).tolist()
            
            # Generate KPIs
            llm_kpis = llm_generate_kpis(original_columns, sample_data)
            
            if llm_kpis:
                # Match LLM KPIs (they should all match since they're generated from available columns)
                llm_status = match_kpis(df_columns, combined_kpis=llm_kpis, df=df, semantic_match_fn=None)
                
                # Merge: Add LLM KPIs that aren't already present
                for name, data in llm_status.items():
                    if name not in final_kpi_status:
                        final_kpi_status[name] = data
                
                llm_matched = sum(1 for data in llm_status.values() if data.get("calculable", False))
                print(f"   ✅ Added {llm_matched} LLM-generated KPIs")
        else:
            print(f"\n✅ Skipping LLM generation (good match rate: {match_rate:.1%})")

    # Extract minimal info for UI
    detected_kpis = [
        {
            "name": name,
            "description": data["kpi_info"].get("description", ""),
        }
        for name, data in final_kpi_status.items()
        if data.get("calculable", False)
    ]
    
    total_calculable = len(detected_kpis)
    print(f"\n🎯 Total Calculable KPIs: {total_calculable}")

    # Return all info so backend can continue later
    return {
        "status": "awaiting_user_selection",
        "kpi_status": final_kpi_status,
        "detected_kpis": detected_kpis
    }