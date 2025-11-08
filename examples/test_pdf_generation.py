"""Test script for PDF report generation with sample data."""
import os
import sys
from io import BytesIO

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def create_sample_data(n_days=90):
    """Create sample sales data CSV."""
    np.random.seed(42)  # For reproducibility
    
    # Generate dates
    dates = [datetime.now() - timedelta(days=x) for x in range(n_days)]
    dates.reverse()
    
    # Generate sales with trend and noise
    base_sales = np.linspace(1000, 1500, n_days)  # Upward trend
    noise = np.random.normal(0, 50, n_days)
    sales = base_sales + noise
    
    # Add weekly seasonality
    weekly_pattern = np.tile([1.2, 1.1, 1.0, 0.9, 1.1, 1.3, 0.8], (n_days // 7) + 1)[:n_days]
    sales = sales * weekly_pattern
    
    # Generate orders (correlated with sales)
    avg_order_value = 50
    orders = np.round(sales / avg_order_value + np.random.normal(0, 2, n_days))
    
    # Create DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Total Sales': sales,
        'Orders': orders,
        'Average Order Value': sales / orders
    })
    
    return df

def create_sample_trend_images() -> list[BytesIO]:
    """Create sample trend images for testing."""
    # Create two sample plots
    images = []
    
    # Sample trend plot
    plt.figure(figsize=(10, 6))
    x = np.linspace(0, 10, 100)
    y = np.sin(x) * x + x
    plt.plot(x, y)
    plt.title('Sample Sales Trend')
    plt.xlabel('Time')
    plt.ylabel('Sales')
    plt.grid(True)
    
    # Save to BytesIO
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    images.append(img_buf)
    plt.close()
    
    # Sample components plot
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    
    # Trend
    axes[0].plot(x, x)
    axes[0].set_title('Trend')
    
    # Seasonal
    axes[1].plot(x, np.sin(x))
    axes[1].set_title('Seasonal')
    
    # Residual
    axes[2].plot(x, np.random.normal(0, 0.1, 100))
    axes[2].set_title('Residual')
    
    plt.tight_layout()
    
    # Save to BytesIO
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    images.append(img_buf)
    plt.close()
    
    return images

def create_sample_insights() -> str:
    """Create sample markdown insights for testing."""
    return """# Executive Summary
Sales show strong growth with 15% YoY increase. Weekly patterns indicate weekend peaks.

# Table with all KPIs
| KPI | Current value | Change vs previous period (%) | On-target? (Y/N) |
|---|---:|---:|:--:|
| Total Sales | 12,345 | +20.4% | Y |
| Orders | 234 | +15.2% | Y |
| Average Order Value | 52.75 | +4.5% | N |

# KPI Insights
Total Sales increased significantly, driven by both higher order volume and larger basket sizes.
- Weekly Pattern: Strongest on Saturdays (+30% vs. weekday average)
- Growth Trend: Consistent upward movement since Q3

# Recommendations
- Expand weekend staffing to support peak sales periods
- Investigate lower Average Order Value vs target
- Launch targeted promotions during weekday evenings

# Next investigations
- Deep dive into product category mix
- Customer cohort analysis for repeat purchase patterns"""

def test_pdf_generation():
    """Test PDF report generation with various styles and configurations."""
    # Create test directory
    test_dir = Path('test_reports')
    test_dir.mkdir(exist_ok=True)
    
    # Get sample content
    trend_images = create_sample_trend_images()
    insights = create_sample_insights()
    
    # Import here to avoid circular imports
    from utils.generate_pdf_reports import generate_pdf_from_insights
    
    # Test 1: Default style
    print("Generating default style PDF...")
    pdf_path = generate_pdf_from_insights(
        insights_result=insights,
        trend_images=trend_images,
        output_dir=test_dir,
        filename='report_default.pdf'
    )
    print(f"Default PDF created at: {pdf_path}")
    
    # Test 2: Modern dark style
    print("\nGenerating dark style PDF...")
    dark_styles = {
        'title_color': '#1A237E',
        'header_color': '#303F9F',
        'table_header_color': '#3949AB',
        'table_header_text_color': '#FFFFFF',
        'body_font': 'Helvetica',
        'title_font': 'Helvetica-Bold',
        'header_font': 'Helvetica-Bold',
        'title_size': 28,
        'header_size': 20,
        'body_size': 12,
        'table_size': 11,
    }
    
    dark_layout = {
        'margins': 54,  # Smaller margins
        'spacing': 0.3,
        'section_spacing': 0.6,
        'table_style': 'modern',
    }
    
    pdf_path = generate_pdf_from_insights(
        insights_result=insights,
        trend_images=trend_images,
        output_dir=test_dir,
        filename='report_dark.pdf',
        styles_config=dark_styles,
        layout_config=dark_layout
    )
    print(f"Dark style PDF created at: {pdf_path}")
    
    # Test 3: Minimal style
    print("\nGenerating minimal style PDF...")
    minimal_styles = {
        'title_color': '#000000',
        'header_color': '#333333',
        'table_header_color': '#EEEEEE',
        'table_header_text_color': '#000000',
        'body_font': 'Helvetica',
        'title_size': 20,
        'header_size': 16,
        'body_size': 10,
        'table_size': 9,
    }
    
    minimal_layout = {
        'margins': 72,
        'spacing': 0.2,
        'section_spacing': 0.4,
        'table_style': 'minimal',
    }
    
    pdf_path = generate_pdf_from_insights(
        insights_result=insights,
        trend_images=trend_images,
        output_dir=test_dir,
        filename='report_minimal.pdf',
        styles_config=minimal_styles,
        layout_config=minimal_layout
    )
    print(f"Minimal style PDF created at: {pdf_path}")
    
    print("\nAll test PDFs generated successfully!")

if __name__ == '__main__':
    # Test PDF generation with sample data
    test_pdf_generation()
    
    # Optional: Also test with real data
    try:
        print("\nTesting with real data...")
        # Create sample CSV
        df = create_sample_data()
        csv_path = Path('test_data.csv')
        df.to_csv(csv_path, index=False)
        
        # Import the example report generator
        from generate_report import generate_sample_report
        
        pdf_path = generate_sample_report(
            data_path=csv_path,
            output_dir='test_reports',
            filename='real_data_report.pdf'
        )
        print(f"Real data report generated at: {pdf_path}")
        
        # Cleanup
        csv_path.unlink()  # Remove test CSV
        
    except Exception as e:
        print(f"Error testing with real data: {e}")