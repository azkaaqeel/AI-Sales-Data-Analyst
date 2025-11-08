from modules.KPI_Module.KPI_Engine import build_dependency_graph, calculate_kpis_temporal


def KPI_Calculation(df, kpi_status, selected_kpis):
    """
    Perform KPI calculation only on user-selected KPIs.
    """
    # Filter KPIs based on user selection
    filtered_kpis = {
        name: data for name, data in kpi_status.items()
        if name in selected_kpis
    }

    # Build dependency graph for selected KPIs only
    dependency_graph = build_dependency_graph(filtered_kpis)

    calculated_kpis = calculate_kpis_temporal(df, filtered_kpis, dependency_graph)

    return {
        "status": "calculation_complete",
        "calculated_kpis": calculated_kpis
    }