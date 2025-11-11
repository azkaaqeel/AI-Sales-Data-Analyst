# services/insight_generator.py
from __future__ import annotations
import json
from io import BytesIO
from typing import List, Dict, Optional

from utils.errors import InsightGenerationError, InsightInputError
from models.base import InsightLLM
from utils.extract_kpi_summary import extract_kpi_summary

PROMPT_TEMPLATE = """
You are an experienced business analyst preparing a structured retail performance report
based on Prophet-generated sales trends and KPI data.

**Objective:**
Deliver a clear, data-driven analysis that leadership can use for decision-making.

**Your tasks:**
1. Interpret each image (describe overall trend, peaks, troughs, and anomalies).
2. Connect visual patterns with the KPI table — explain *why* KPI values changed in relation to trends.
3. Identify underlying causes and patterns (discount effects, category shifts, pricing, etc.).
4. Provide specific, actionable recommendations tied directly to the insights.

**Output Format (use Markdown headings exactly):**
- Executive Summary
- Table with all KPIs
- KPI Insights
- Recommendations

**Tone & Style:**
- Use impactful, and executive-level language.
- Be analytical, not descriptive — explain the *why*, not just the *what*.
- Avoid repetition, filler words, or generic advice.
- Use short paragraphs and bullet points for readability.

**Reasoning expectations:**
- Compare KPI changes across time periods quantitatively (e.g., +20%, –35%).
- Link insights to business levers: pricing, discounting, category performance, seasonality.
- Highlight anomalies or sudden shifts that may indicate operational or market issues.

**KPI data:**
{clean_kpis}

**Important:**
Follow the section structure *exactly*.
All numbers, categories, and insights should be grounded in the provided data.
Never invent extra data or trends.
""".strip()


def build_prompt(clean_kpis: Dict) -> str:
    try:
        return PROMPT_TEMPLATE.format(clean_kpis=json.dumps(clean_kpis, indent=2))
    except Exception as exc:
        raise InsightGenerationError(f"Failed to format KPI data into prompt: {exc}") from exc


def generate_insights(
    trend_imgs: List[BytesIO],
    kpi_data: Dict,
    llm: InsightLLM,
    temperature: float = 0.6,
) -> Optional[str]:
    """
    Provider-agnostic insight generation that depends on InsightLLM.
    """
    # Input validation
    if not isinstance(trend_imgs, list) or not all(isinstance(x, BytesIO) for x in trend_imgs):
        raise InsightInputError("'trend_imgs' must be a list of BytesIO objects.")
    if not isinstance(kpi_data, dict) or "calculated_kpis" not in kpi_data:
        raise InsightInputError("'kpi_data' must be a dict containing 'calculated_kpis'.")

    # KPI summary
    try:
        clean_kpis = extract_kpi_summary(kpi_data["calculated_kpis"])
    except Exception as exc:
        raise InsightGenerationError(f"Failed to extract KPI summary: {exc}") from exc

    # Prompt
    prompt = build_prompt(clean_kpis)

    # Prepare images as bytes
    image_bytes: List[bytes] = []
    try:
        for img in trend_imgs:
            data = img.getvalue()
            if data:
                image_bytes.append(data)
    except Exception as exc:
        raise InsightGenerationError(f"Failed to read image buffers: {exc}") from exc

    if not image_bytes:
        raise InsightInputError("No valid images provided for analysis.")

    # Call LLM
    return llm.generate(prompt=prompt, images=image_bytes, temperature=temperature)
