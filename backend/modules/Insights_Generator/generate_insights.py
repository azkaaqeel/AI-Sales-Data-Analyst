# services/insight_generator.py
from __future__ import annotations
import json
from io import BytesIO
from typing import List, Dict, Optional

from utils.errors import InsightGenerationError, InsightInputError
from models.base import InsightLLM
from utils.extract_kpi_summary import extract_kpi_summary

PROMPT_TEMPLATE = """
You are an experienced business analyst creating an executive-level sales performance report.

**DATA PROVIDED:**
{clean_kpis}

**YOUR TASK:**
Analyze the KPI data and trend charts to create a comprehensive, data-driven report with SPECIFIC NUMBERS and ACTIONABLE RECOMMENDATIONS.

**OUTPUT FORMAT (use these EXACT markdown headings):**

# Executive Summary
[2-3 sentences highlighting the MOST IMPORTANT finding with specific numbers and % changes. Focus on business impact.]

# KPI Analysis

## Financial Performance
[Analyze revenue, pricing, and financial metrics with specific % changes between periods]

## Customer Metrics  
[Analyze customer count, transaction volume, and purchase behavior with specific numbers]

## Product Performance
[For categorical KPIs like "Revenue by Item", identify top performers and their contribution %]

## Quality & Satisfaction
[Analyze ratings, reviews, or satisfaction metrics with trends]

# Key Insights
[3-5 bullet points, each starting with a specific finding]
- **[Metric name] shows [specific % change]**: Explain WHY this happened and business impact
- **[Pattern observed]**: Connect multiple KPIs to explain the root cause

# Recommendations
[3-5 specific, actionable recommendations tied to the data]
1. **[Action verb] [specific action]**: Explain expected impact with numbers if possible
2. **Investigate [specific issue]**: Reference the KPI that triggered this recommendation

**CRITICAL RULES:**
✅ USE ACTUAL NUMBERS from the KPI data (e.g., "$20,261" not "revenue declined")
✅ CALCULATE % CHANGES between periods (e.g., "-11.8%" not "decreased")
✅ REFERENCE SPECIFIC TIME PERIODS (e.g., "Dec 2023 vs Nov 2023")
✅ TIE INSIGHTS TO BUSINESS IMPACT (revenue, profit, customer retention)
✅ MAKE RECOMMENDATIONS MEASURABLE (e.g., "increase by 15%" not "improve")

❌ DON'T invent data not in the KPI list
❌ DON'T use vague terms like "significant" without numbers
❌ DON'T generic advice like "monitor trends" - be specific
❌ DON'T reference "Image 1" or charts - focus on KPI data

**EXAMPLE OF GOOD INSIGHT:**
"Total Revenue declined 11.8% from $22,961 (Nov) to $20,261 (Dec) despite a 6.3% increase in customers (111 → 118). This indicates Average Purchase Value dropped 16.7% to $104, likely due to seasonal discounting or shift to lower-priced products."

**EXAMPLE OF BAD INSIGHT:**
"Revenue showed a downward trend. Customer numbers increased. This requires monitoring."
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
