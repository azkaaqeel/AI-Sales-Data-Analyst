import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from rapidfuzz import fuzz, process
import warnings
warnings.filterwarnings('ignore')
from prophet import Prophet
from modules.KPI_Module.KPI_Engine import match_column_with_score, normalize_column_name
from io import BytesIO

sales_synonyms = [
    "Sales", "Revenue", "Turnover", "Total Amount", "Amount",
    "Order Value", "Payment", "Price", "Invoice", "Purchase Value"
]

# Find sales column for prophet detection
def find_sales_column(df):
    df.columns = [normalize_column_name(col) for col in df.columns]

    best_match = None
    best_score = 0

    for synonym in sales_synonyms:
        match, score = match_column_with_score(synonym, df.columns, threshold=80)
        if match:
            if score > best_score:
                best_match, best_score = match, score

    return best_match

# Check if the column name hints it's about time
def detect_time_column(df):
    for col in df.columns:

        if any(word in col.lower() for word in ['date', 'time', 'timestamp']):
            return col
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None

def detect_trends(df, period_type):
    sales_col = find_sales_column(df)
    time_col = detect_time_column(df)
    df = df.rename(columns={time_col: 'ds', sales_col: 'y'})
    df['ds'] = pd.to_datetime(df['ds'], errors='coerce')
    df = df.dropna(subset=['ds', 'y'])

    weekly_seasonality = False 
    model = Prophet(daily_seasonality=False)

    if period_type == 'WoW':
        weekly_seasonality = True  
    elif period_type == 'Monthly':
        # Add custom monthly seasonality (approx. 30.5 days for a month)
        model.add_seasonality(name='monthly', period=30.5, fourier_order=4)

    # Apply weekly seasonality if necessary
    model = Prophet(daily_seasonality=False, weekly_seasonality=weekly_seasonality)
    model.add_country_holidays(country_name='PK')
    model.fit(df)

    forecast = model.predict(df)
    trend = forecast[['ds', 'trend']]

    # --- Trend plot ---
    fig1, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['ds'], df['y'], label='Actual', marker='o')
    ax.set_title(f"Sales Trend ({period_type})")
    ax.legend()
    ax.set_title('Trend Detection')
    ax.set_xlabel('Date')
    ax.set_ylabel('Value')

    trend_buf = BytesIO()
    fig1.savefig(trend_buf, format='png', bbox_inches='tight')
    trend_buf.seek(0)
    plt.close(fig1)

    # --- Components plot ---
    fig2 = model.plot_components(forecast)
    comp_buf = BytesIO()
    fig2.savefig(comp_buf, format='png', bbox_inches='tight')
    comp_buf.seek(0)
    plt.close(fig2)

    return [trend_buf, comp_buf]
