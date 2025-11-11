def extract_kpi_summary(calculated_kpis: dict) -> dict:
    """
    Extracts a minimal, clean KPI summary for LLM reasoning.
    Keeps only period, KPI name, and numeric/text value.
    """
    if not isinstance(calculated_kpis, dict):
        raise ValueError("'calculated_kpis' must be a dictionary.")

    data = {k: v for k, v in calculated_kpis.items() if k != "meta"}
    summary = {}

    for period, kpis in data.items():
        if not isinstance(kpis, dict):
            continue
        clean_kpis = {
            name: details.get("value") if isinstance(details, dict) else details
            for name, details in kpis.items()
        }
        summary[period] = clean_kpis

    return summary
