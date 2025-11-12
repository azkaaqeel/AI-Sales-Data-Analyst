"""Seasonal analysis and holiday detection utilities."""
from datetime import datetime, date
from typing import List, Dict, Tuple
import pandas as pd

# Major holidays and shopping events
HOLIDAYS = {
    # US Holidays
    'new_years': {'month': 1, 'day': 1, 'name': 'New Year\'s Day', 'icon': '🎊', 'impact': 'neutral'},
    'valentines': {'month': 2, 'day': 14, 'name': 'Valentine\'s Day', 'icon': '💝', 'impact': 'positive'},
    'easter': {'month': 4, 'day': 17, 'name': 'Easter', 'icon': '🐰', 'impact': 'positive'},  # Approximate
    'mothers_day': {'month': 5, 'day': 14, 'name': 'Mother\'s Day', 'icon': '👩', 'impact': 'positive'},
    'memorial_day': {'month': 5, 'day': 29, 'name': 'Memorial Day', 'icon': '🇺🇸', 'impact': 'positive'},
    'fathers_day': {'month': 6, 'day': 18, 'name': 'Father\'s Day', 'icon': '👨', 'impact': 'positive'},
    'independence_day': {'month': 7, 'day': 4, 'name': 'Independence Day', 'icon': '🎆', 'impact': 'positive'},
    'labor_day': {'month': 9, 'day': 4, 'name': 'Labor Day', 'icon': '⚒️', 'impact': 'positive'},
    'halloween': {'month': 10, 'day': 31, 'name': 'Halloween', 'icon': '🎃', 'impact': 'positive'},
    'thanksgiving': {'month': 11, 'day': 23, 'name': 'Thanksgiving', 'icon': '🦃', 'impact': 'positive'},
    'black_friday': {'month': 11, 'day': 24, 'name': 'Black Friday', 'icon': '🛍️', 'impact': 'very_positive'},
    'cyber_monday': {'month': 11, 'day': 27, 'name': 'Cyber Monday', 'icon': '💻', 'impact': 'very_positive'},
    'christmas': {'month': 12, 'day': 25, 'name': 'Christmas', 'icon': '🎄', 'impact': 'very_positive'},
    'boxing_day': {'month': 12, 'day': 26, 'name': 'Boxing Day', 'icon': '📦', 'impact': 'positive'},
    'new_years_eve': {'month': 12, 'day': 31, 'name': 'New Year\'s Eve', 'icon': '🎉', 'impact': 'neutral'},
}

# Seasonal baselines (typical % change MoM)
SEASONAL_BASELINES = {
    1: -15,   # January (post-holiday slump)
    2: -5,    # February
    3: 0,     # March
    4: 5,     # April (spring)
    5: 8,     # May (Mother's Day)
    6: 3,     # June (Father's Day)
    7: 2,     # July (summer)
    8: -3,    # August (back-to-school prep)
    9: 5,     # September (back-to-school)
    10: 10,   # October (Halloween prep)
    11: 25,   # November (Black Friday, Thanksgiving)
    12: -8,   # December (post-Black Friday dip, then Christmas)
}

def get_holidays_in_period(start_date: date, end_date: date) -> List[Dict]:
    """
    Get all holidays that fall within a date range.
    
    Args:
        start_date: Start of period
        end_date: End of period
        
    Returns:
        List of holiday dicts with date, name, icon, impact
    """
    holidays_in_period = []
    
    for year in range(start_date.year, end_date.year + 1):
        for holiday_key, holiday_info in HOLIDAYS.items():
            try:
                holiday_date = date(year, holiday_info['month'], holiday_info['day'])
                if start_date <= holiday_date <= end_date:
                    holidays_in_period.append({
                        'date': holiday_date.isoformat(),
                        'name': holiday_info['name'],
                        'icon': holiday_info['icon'],
                        'impact': holiday_info['impact']
                    })
            except ValueError:
                # Invalid date (e.g., Feb 30)
                continue
    
    return sorted(holidays_in_period, key=lambda x: x['date'])

def get_seasonal_baseline(month: int) -> float:
    """
    Get the expected MoM % change for a given month based on seasonal patterns.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Expected % change MoM
    """
    return SEASONAL_BASELINES.get(month, 0)

def analyze_seasonal_performance(current_value: float, previous_value: float, 
                                 current_month: int) -> Dict:
    """
    Compare actual performance to seasonal baseline.
    
    Args:
        current_value: Current period value
        previous_value: Previous period value
        current_month: Current month (1-12)
        
    Returns:
        Dict with actual_change, expected_change, variance, assessment
    """
    if previous_value == 0:
        return {
            'actual_change': 0,
            'expected_change': 0,
            'variance': 0,
            'assessment': 'insufficient_data'
        }
    
    actual_change = ((current_value - previous_value) / previous_value) * 100
    expected_change = get_seasonal_baseline(current_month)
    variance = actual_change - expected_change
    
    # Assess performance
    if variance > 5:
        assessment = 'outperforming'
    elif variance < -5:
        assessment = 'underperforming'
    else:
        assessment = 'on_track'
    
    return {
        'actual_change': round(actual_change, 1),
        'expected_change': expected_change,
        'variance': round(variance, 1),
        'assessment': assessment
    }

def get_yoy_comparison(current_period_df: pd.DataFrame, 
                       historical_df: pd.DataFrame,
                       value_column: str) -> Dict:
    """
    Calculate year-over-year comparison.
    
    Args:
        current_period_df: DataFrame for current period
        historical_df: DataFrame with historical data
        value_column: Column name to compare
        
    Returns:
        Dict with current, last_year, yoy_change, yoy_pct
    """
    try:
        current_total = current_period_df[value_column].sum()
        
        # Try to find same period last year
        current_year = pd.to_datetime(current_period_df.iloc[0]['Date']).year if 'Date' in current_period_df.columns else datetime.now().year
        last_year = current_year - 1
        
        last_year_data = historical_df[pd.to_datetime(historical_df['Date']).dt.year == last_year] if 'Date' in historical_df.columns else historical_df
        last_year_total = last_year_data[value_column].sum() if not last_year_data.empty else 0
        
        if last_year_total > 0:
            yoy_change = current_total - last_year_total
            yoy_pct = (yoy_change / last_year_total) * 100
            
            return {
                'current': current_total,
                'last_year': last_year_total,
                'yoy_change': yoy_change,
                'yoy_pct': round(yoy_pct, 1),
                'available': True
            }
    except Exception:
        pass
    
    return {'available': False}

def detect_anomalies(values: List[float], threshold: float = 2.0) -> List[int]:
    """
    Detect anomalies in a time series using standard deviation.
    
    Args:
        values: List of values
        threshold: Number of standard deviations to consider anomaly
        
    Returns:
        List of indices where anomalies occur
    """
    if len(values) < 3:
        return []
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    
    if std_dev == 0:
        return []
    
    anomalies = []
    for i, value in enumerate(values):
        z_score = abs((value - mean) / std_dev)
        if z_score > threshold:
            anomalies.append(i)
    
    return anomalies

