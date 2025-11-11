def kpi_summary_to_markdown(summary: dict) -> str:
    md = "### KPI Summary by Period\n\n"
    for period, kpis in summary.items():
        md += f"**Period:** {period}\n"
        for name, value in kpis.items():
            md += f"- {name}: {value}\n"
        md += "\n"
    return md
