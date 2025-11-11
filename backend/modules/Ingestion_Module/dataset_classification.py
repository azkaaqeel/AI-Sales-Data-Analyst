# TO BE TESTED
import pandas as pd
import json
import re
import os
from modules.KPI_Module.KPI_Engine import normalize_column_name

# Strong indicators of sales data
STRONG_SALES_TERMS = {
    'Sales', 'Invoice', 'Transaction', 'Order Id', 'Purchase', 'Customer Id',
    'Sale Amount', 'Order Number', 'Payment', 'Receipt'
}

# Ambiguous terms that might indicate sales
AMBIGUOUS_TERMS = {
    'Revenue', 'Profit', 'Roi', 'Spend', 'Cost', 'Price', 'Amount', 
    'Quantity', 'Units', 'Customer', 'Product'
}


def check_column_matches(columns, term_set):
    """Count how many columns match terms in the given set."""
    normalized_cols = [normalize_column_name(col) for col in columns]
    matches = []
    
    for col in normalized_cols:
        for term in term_set:
            if term in col:
                matches.append(col)
                break
    
    return matches

def classify_dataset(df, metadata):
    """
    Determine if a dataset is sales-related using a two-pass approach:
    1. Quick heuristic check based on column names
    2. LLM analysis for ambiguous cases
    
    Args:
        df: pandas DataFrame to analyze
        metadata: Dict containing dataset metadata from ingest_csv
    
    Returns:
        Tuple[bool, str]: (is_sales_related, reason)
    """
    # First pass: Check for strong sales indicators
    strong_matches = check_column_matches(df.columns, STRONG_SALES_TERMS)
    columns_len = len(df.columns)
    if len(strong_matches) >= columns_len / 2:
        return True, f"Found strong sales indicators: {', '.join(strong_matches)}"
    
    # Check for ambiguous terms
    ambiguous_matches = check_column_matches(df.columns, AMBIGUOUS_TERMS)
    if not strong_matches and not ambiguous_matches:
        return False, "No sales-related columns found"
        
    # If we have ambiguous matches or just one strong match, use LLM
    if strong_matches or ambiguous_matches:
        PROMPT_TEMPLATE = """
        Determine if this dataset represents *sales* data — meaning customer purchase transactions, orders, or revenue directly from product sales.
        Do not classify datasets as sales-related if they are about marketing (ROI, ad spend, impressions), finance (budgets, costs), or inventory tracking without transaction details.

        Columns and their types:
        {column_info}

        Sample Data:
        {sample_data}

        Respond in JSON format:
        {{
            "is_sales_related": true/false,
            "reason": "one line explanation of why or why not"
        }}
        
        DO NOT RESPOND WITH ANYTHING ELSE.
        """

        # Format column information
        column_info = []
        for col, col_type in metadata['column_types'].items():
            sample_values = df[col].head(2).tolist()
            column_info.append(f"- {col} ({col_type}): {sample_values}")

        # Prepare the prompt
        prompt = PROMPT_TEMPLATE.format(
            column_info="\n".join(column_info),
            sample_data=df.head(3).to_string()
        )

        try:
            # Try to use Gemini for classification if API key is available
            api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if api_key:
                from models.gemini import GeminiClient
                client = GeminiClient(model_name="gemini-2.5-flash", api_key=api_key)
                response = client.generate(prompt=prompt, images=[], temperature=0.3)
                
                # Extract JSON from response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start == -1 or end == 0:
                    # Fallback to heuristic if LLM response is invalid
                    return len(strong_matches) > 0, f"Found sales indicators: {', '.join(strong_matches)}"
                
                classification = json.loads(response[start:end])
                
                return (
                    classification.get('is_sales_related', False),
                    classification.get('reason', 'No reason provided')
                )
            else:
                # Fallback to heuristic if no API key
                return len(strong_matches) > 0, f"Found sales indicators: {', '.join(strong_matches)}"

        except Exception as e:
            # Fallback to heuristic on any error
            return len(strong_matches) > 0, f"Classification fallback: {', '.join(strong_matches) if strong_matches else 'No strong indicators'}"
