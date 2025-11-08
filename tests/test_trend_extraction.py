import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.Trend_Extractor.Trend_Extraction import (
    find_sales_column,
    detect_time_column,
    detect_trends,
    sales_synonyms
)
from io import BytesIO

@pytest.fixture
def sample_sales_df():
    # Create sample data with 90 days (covers 3 months)
    dates = [datetime(2025, 1, 1) + timedelta(days=x) for x in range(90)]
    sales = [100 + x + np.random.normal(0, 10) for x in range(90)]  # Trending up with noise
    orders = np.random.randint(5, 15, 90)  # Make orders same length as other arrays
    
    return pd.DataFrame({
        'Order Date': dates,
        'Total Sales': sales,
        'Orders': orders
    })

@pytest.fixture
def sample_sales_df_variants():
    # Test different column name variants
    dates = [datetime(2025, 1, 1) + timedelta(days=x) for x in range(10)]
    return pd.DataFrame({
        'timestamp': dates,
        'Revenue': np.random.normal(100, 10, 10),
        'Purchase Value': np.random.normal(100, 10, 10),
        'Random Column': np.random.normal(0, 1, 10)
    })

def test_find_sales_column_exact():
    df = pd.DataFrame({'Total Sales': [100, 200], 'Orders': [1, 2]})
    assert find_sales_column(df) == 'Total Sales'

def test_find_sales_column_fuzzy():
    df = pd.DataFrame({'Total Revenue': [100, 200], 'Orders': [1, 2]})
    assert find_sales_column(df) == 'Total Revenue'

def test_find_sales_column_multiple():
    # Should pick the best match when multiple sales-like columns exist
    df = pd.DataFrame({
        'Revenue': [100, 200],
        'Total Sales': [100, 200],
        'Orders': [1, 2]
    })
    result = find_sales_column(df)
    assert result in ['Revenue', 'Total Sales']

def test_find_sales_column_no_match():
    df = pd.DataFrame({'Random': [100, 200], 'Orders': [1, 2]})
    assert find_sales_column(df) is None

def test_detect_time_column_named(sample_sales_df):
    assert detect_time_column(sample_sales_df) == 'Order Date'

def test_detect_time_column_datetime():
    # Test detection by dtype
    df = pd.DataFrame({
        'event_time': pd.date_range('2025-01-01', periods=5),
        'value': range(5)
    })
    assert detect_time_column(df) == 'event_time'

def test_detect_time_column_multiple_options(sample_sales_df_variants):
    # Should find a datetime column even with multiple options
    result = detect_time_column(sample_sales_df_variants)
    assert result == 'timestamp'

def test_detect_time_column_no_time():
    df = pd.DataFrame({
        'col1': range(5),
        'col2': ['a', 'b', 'c', 'd', 'e']
    })
    assert detect_time_column(df) is None

def test_detect_trends_daily(sample_sales_df):
    # Test daily trend detection
    result = detect_trends(sample_sales_df, 'daily')
    assert len(result) == 2  # Should return two BytesIO objects
    assert all(isinstance(buf, BytesIO) for buf in result)
    
    # Verify both buffers contain PNG data
    for buf in result:
        buf.seek(0)
        assert buf.read(8).startswith(b'\x89PNG')  # PNG magic number

def test_detect_trends_weekly(sample_sales_df):
    # Test weekly aggregation
    result = detect_trends(sample_sales_df, 'WoW')
    assert len(result) == 2
    assert all(isinstance(buf, BytesIO) for buf in result)

def test_detect_trends_monthly(sample_sales_df):
    # Test monthly aggregation
    result = detect_trends(sample_sales_df, 'MoM')
    assert len(result) == 2
    assert all(isinstance(buf, BytesIO) for buf in result)

def test_detect_trends_handles_missing_data():
    # Test handling of missing data
    df = pd.DataFrame({
        'Order Date': [datetime(2025, 1, 1) + timedelta(days=x) for x in range(5)],
        'Total Sales': [100, np.nan, 300, np.nan, 500]
    })
    result = detect_trends(df, 'daily')
    assert len(result) == 2
    assert all(isinstance(buf, BytesIO) for buf in result)

def test_detect_trends_input_validation():
    # Test with invalid data
    with pytest.raises(Exception):
        df = pd.DataFrame({
            'Order Date': ['invalid_date'] * 5,
            'Total Sales': range(5)
        })
        detect_trends(df, 'daily')

def test_sales_synonyms_coverage():
    # Verify all sales synonyms are properly normalized and unique
    normalized_synonyms = [s.lower() for s in sales_synonyms]
    assert len(normalized_synonyms) == len(set(normalized_synonyms))  # No duplicates
    assert all(isinstance(s, str) for s in sales_synonyms)  # All strings
    assert all(len(s) > 0 for s in sales_synonyms)  # No empty strings