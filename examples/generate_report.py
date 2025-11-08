"""Example usage of PDF report generation."""
from pathlib import Path
from modules.Insights_Generator.generate_insights import generate_insights
from utils.generate_pdf_reports import generate_pdf_from_insights
import pandas as pd

def generate_sample_report(
    data_path: str | Path,
    output_dir: str | Path = None,
    filename: str = None
) -> Path:
    """
    Generate a sample PDF report from sales data.
    
    Args:
        data_path: Path to CSV file with sales data
        output_dir: Where to save the PDF (default: current directory)
        filename: Optional PDF filename
        
    Returns:
        Path to the generated PDF
    """
    # Load and process data
    df = pd.read_csv(data_path)
    
    # Generate insights (this will call Prophet and compute KPIs)
    insights_result, trend_images = generate_insights(df)
    
    # Create PDF report
    pdf_path = generate_pdf_from_insights(
        insights_result=insights_result,
        trend_images=trend_images,
        output_dir=output_dir,
        filename=filename
    )
    
    return pdf_path

if __name__ == '__main__':
    # Example usage
    data_file = Path('path/to/your/sales_data.csv')
    output_dir = Path('reports')
    
    try:
        pdf_path = generate_sample_report(
            data_path=data_file,
            output_dir=output_dir
        )
        print(f"PDF report generated successfully at: {pdf_path}")
        
    except Exception as e:
        print(f"Error generating report: {e}")