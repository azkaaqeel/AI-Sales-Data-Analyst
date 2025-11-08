"""Test CSV ingestion functionality."""
import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO
from datetime import datetime, timedelta
from modules.Ingestion_Module.ingest_csv import ingest_csv, CSVValidationError

def create_test_csv():
    """Create a sample CSV file for testing."""
    # Generate sample data
    dates = [datetime.now() - timedelta(days=x) for x in range(30)]
    dates.reverse()
    
    data = {
        'Date': dates,
        'Total Sales': np.random.uniform(1000, 5000, 30),
        'Orders': np.random.randint(20, 100, 30),
        'Category': np.random.choice(['A', 'B', 'C'], 30),
        'Region': 'North',  # Categorical with single value
    }
    
    df = pd.DataFrame(data)
    
    # Save to CSV
    test_file = Path('test_data.csv')
    df.to_csv(test_file, index=False)
    return test_file

def test_csv_ingestion():
    """Run basic tests for CSV ingestion."""
    # Create test file
    test_file = create_test_csv()
    
    try:
        print("Testing CSV ingestion...")
        
        # Test basic ingestion
        df, metadata = ingest_csv(test_file)
        print("\n1. Basic ingestion successful:")
        print(f"- Rows: {metadata['row_count']}")
        print(f"- Columns: {metadata['column_count']}")
        print(f"- Column types: {metadata['column_types']}")
        print(f"- Date column: {metadata['date_column']}")
        
        # Test date handling
        print("\n2. Date handling:")
        if metadata['date_column']:
            print(f"- Date range: {metadata['date_range']['start']} to {metadata['date_range']['end']}")
        
        # Test with expected columns
        print("\n3. Testing column validation...")
        df, _ = ingest_csv(
            test_file,
            expected_columns=['Date', 'Total Sales', 'Orders']
        )
        print("- Column validation passed")
        
        # Test numerical validation
        print("\n4. Testing numerical validation...")
        df, _ = ingest_csv(test_file, validate_numeric=True)
        print("- Numerical validation passed")
        
        print("\nAll tests passed successfully!")
        
    except CSVValidationError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Cleanup
        test_file.unlink()

if __name__ == '__main__':
    test_csv_ingestion()