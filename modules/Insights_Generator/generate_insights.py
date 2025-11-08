import json
import traceback
from io import BytesIO
from typing import List, Dict, Optional
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
from utils.extract_kpi_summary import extract_kpi_summary
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class InsightGenerationError(Exception):
    """Base exception for insight generation errors."""
    pass

class InsightInputError(InsightGenerationError):
    """Raised when invalid input is provided."""
    pass

class InsightModelError(InsightGenerationError):
    """Raised when Gemini model initialization or inference fails."""
    pass


def generate_insights(
    trend_imgs: List[BytesIO],
    kpi_data: Dict,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.6,
) -> Optional[str]:
    """
    Uses Google's Gemini SDK to analyze multiple trend images and KPI results together.

    Args:
        trend_imgs: List of BytesIO image buffers (PNG format).
        kpi_data: KPI calculation result dictionary containing 'calculated_kpis'.
        model_name: Gemini model name ('gemini-1.5-flash' or 'gemini-1.5-pro').
        temperature: Controls creativity level in model response.

    Returns:
        Markdown text output from Gemini, or None if generation failed.

    Raises:
        InsightInputError: If inputs are missing or invalid.
        InsightModelError: For Gemini model or API-related issues.
        InsightGenerationError: For any unexpected internal errors.
    """

    # === Input Validation ===
    if not isinstance(trend_imgs, list) or not all(isinstance(img, BytesIO) for img in trend_imgs):
        raise InsightInputError("'trend_imgs' must be a list of BytesIO objects.")
    if not isinstance(kpi_data, dict) or "calculated_kpis" not in kpi_data:
        raise InsightInputError("'kpi_data' must be a dictionary containing 'calculated_kpis'.")

    # === Extract KPI summary ===
    try:
        clean_kpis = extract_kpi_summary(kpi_data["calculated_kpis"])
    except Exception as exc:
        raise InsightGenerationError(f"Failed to extract KPI summary: {exc}") from exc

    # === Initialize Gemini Model ===
    try:
        model = genai.GenerativeModel(model_name)
    except Exception as exc:
        raise InsightModelError(f"Failed to initialize Gemini model '{model_name}': {exc}") from exc

    # === Build Prompt ===
    try:
       prompt = f"""
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
{json.dumps(clean_kpis, indent=2)}

**Important:**
Follow the section structure *exactly*.
All numbers, categories, and insights should be grounded in the provided data.
Never invent extra data or trends.
"""

    except Exception as exc:
        raise InsightGenerationError(f"Failed to serialize or format KPI data: {exc}") from exc

    # === Prepare Multimodal Parts ===
    try:
        parts = [{"text": prompt}]
        for img in trend_imgs:
            data = img.getvalue()
            if not data:
                continue
            parts.append({"mime_type": "image/png", "data": data})

        if len(parts) == 1:
            raise InsightInputError("No valid images provided for analysis.")
    except Exception as exc:
        raise InsightGenerationError(f"Error preparing image data: {exc}") from exc

    # === Generate Content via Gemini ===
    try:
        response = model.generate_content(
            parts,
            generation_config={"temperature": temperature},
        )

        text_output = getattr(response, "text", None)
        if not text_output or not text_output.strip():
            raise InsightModelError("Gemini returned no text output.")

        return text_output.strip()

    except GoogleAPIError as exc:
        raise InsightModelError(f"Gemini API error: {exc}") from exc
    except Exception as exc:
        trace = traceback.format_exc()
        raise InsightGenerationError(
            f"Unexpected Gemini API error: {exc}\nTraceback:\n{trace}"
        ) from exc
